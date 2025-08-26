import asyncio
import aiohttp
import json
import logging
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, unquote
import hashlib
import hmac
import base64
from models import (
    PlatformType, ShopifyCredentials, AmazonCredentials, WooCommerceCredentials,
    APIConnectionStatus, APIDataSyncResult
)

logger = logging.getLogger(__name__)

class APIConnectorError(Exception):
    """Custom exception for API connector errors"""
    pass

class ShopifyConnector:
    """Shopify Admin API Connector - Real-time e-commerce data fetching"""
    
    def __init__(self, credentials: ShopifyCredentials):
        self.credentials = credentials
        self.base_url = f"https://{credentials.shop_domain}/admin/api/2024-01"
        self.headers = {
            "X-Shopify-Access-Token": credentials.access_token,
            "Content-Type": "application/json"
        }
        self.rate_limit_remaining = 40  # Shopify allows 40 requests per second
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test Shopify connection and validate credentials"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        shop_data = await response.json()
                        shop_name = shop_data.get('shop', {}).get('name', 'Unknown Shop')
                        logger.info(f" Shopify connection successful: {shop_name}")
                        return True, f"Connected to {shop_name}"
                    elif response.status == 401:
                        return False, "Invalid access token"
                    elif response.status == 403:
                        return False, "Insufficient permissions"
                    else:
                        return False, f"Connection failed: HTTP {response.status}"
        except Exception as e:
            logger.error(f" Shopify connection test failed: {e}")
            return False, f"Connection error: {str(e)}"
    
    async def fetch_orders(self, days_back: int = None) -> List[Dict]:
        """Fetch ALL orders from Shopify with pagination INCLUDING LINE ITEMS (SKUs, quantities)"""
        try:
            all_orders = []
            page_info = None
            
            # If days_back is None, fetch all orders ever created
            since_date = None
            if days_back is not None:
                since_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            async with aiohttp.ClientSession() as session:
                while True:
                    if page_info:
                        # When using page_info, only include limit and page_info
                        params = {
                            "limit": 250,
                            "page_info": page_info
                        }
                    else:
                        # First request - include all filters
                        params = {
                            "limit": 250,  # Use max limit per request for efficiency
                            "status": "any",
                            "financial_status": "any"
                        }
                        
                        if since_date:
                            params["created_at_min"] = since_date
                
                    async with session.get(
                        f"{self.base_url}/orders.json",
                        headers=self.headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            orders = data.get('orders', [])
                            
                            # Transform to standard format INCLUDING ALL POSSIBLE FIELDS
                            page_orders = []
                            for order in orders:
                                # Process line items to extract ALL SKU and product data
                                line_items = []
                                for item in order.get('line_items', []):
                                    line_items.append({
                                        'line_item_id': item.get('id'),
                                        'product_id': item.get('product_id'),
                                        'variant_id': item.get('variant_id'),
                                        'title': item.get('title'),
                                        'name': item.get('name'),
                                        'sku': item.get('sku'),
                                        'quantity': item.get('quantity', 0),
                                        'price': float(item.get('price', 0)),
                                        'total_discount': float(item.get('total_discount', 0)),
                                        'fulfillment_status': item.get('fulfillment_status'),
                                        'fulfillable_quantity': item.get('fulfillable_quantity', 0),
                                        'fulfillment_service': item.get('fulfillment_service'),
                                        'grams': item.get('grams', 0),
                                        'vendor': item.get('vendor'),
                                        'product_exists': item.get('product_exists'),
                                        'requires_shipping': item.get('requires_shipping'),
                                        'taxable': item.get('taxable'),
                                        'gift_card': item.get('gift_card'),
                                        'properties': item.get('properties', []),
                                        'variant_title': item.get('variant_title'),
                                        'variant_inventory_management': item.get('variant_inventory_management'),
                                        'pre_tax_price': float(item.get('pre_tax_price', 0)),
                                        'duties': item.get('duties', []),
                                        'discount_allocations': item.get('discount_allocations', []),
                                        'tax_lines': item.get('tax_lines', [])
                                    })
                                
                                # Process fulfillments
                                fulfillments = []
                                for fulfillment in order.get('fulfillments', []):
                                    fulfillments.append({
                                        'fulfillment_id': fulfillment.get('id'),
                                        'status': fulfillment.get('status'),
                                        'created_at': fulfillment.get('created_at'),
                                        'service': fulfillment.get('service'),
                                        'tracking_company': fulfillment.get('tracking_company'),
                                        'tracking_number': fulfillment.get('tracking_number'),
                                        'tracking_numbers': fulfillment.get('tracking_numbers', []),
                                        'tracking_urls': fulfillment.get('tracking_urls', []),
                                        'receipt': fulfillment.get('receipt', {}),
                                        'line_items': fulfillment.get('line_items', [])
                                    })
                                
                                # Process refunds
                                refunds = []
                                for refund in order.get('refunds', []):
                                    refunds.append({
                                        'refund_id': refund.get('id'),
                                        'created_at': refund.get('created_at'),
                                        'note': refund.get('note'),
                                        'restock': refund.get('restock'),
                                        'refund_line_items': refund.get('refund_line_items', []),
                                        'transactions': refund.get('transactions', [])
                                    })
                                
                                # Process transactions
                                transactions = []
                                for transaction in order.get('transactions', []):
                                    transactions.append({
                                        'transaction_id': transaction.get('id'),
                                        'kind': transaction.get('kind'),
                                        'gateway': transaction.get('gateway'),
                                        'status': transaction.get('status'),
                                        'message': transaction.get('message'),
                                        'created_at': transaction.get('created_at'),
                                        'amount': float(transaction.get('amount', 0)),
                                        'currency': transaction.get('currency'),
                                        'authorization': transaction.get('authorization'),
                                        'test': transaction.get('test'),
                                        'parent_id': transaction.get('parent_id')
                                    })
                                
                                # Process shipping lines
                                shipping_lines = []
                                for shipping in order.get('shipping_lines', []):
                                    shipping_lines.append({
                                        'shipping_line_id': shipping.get('id'),
                                        'title': shipping.get('title'),
                                        'price': float(shipping.get('price', 0)),
                                        'code': shipping.get('code'),
                                        'source': shipping.get('source'),
                                        'carrier_identifier': shipping.get('carrier_identifier'),
                                        'requested_fulfillment_service_id': shipping.get('requested_fulfillment_service_id'),
                                        'tax_lines': shipping.get('tax_lines', []),
                                        'discount_allocations': shipping.get('discount_allocations', [])
                                    })
                                
                                # Process customer data
                                customer = order.get('customer', {})
                                customer_data = {
                                    'customer_id': customer.get('id'),
                                    'email': customer.get('email'),
                                    'accepts_marketing': customer.get('accepts_marketing'),
                                    'created_at': customer.get('created_at'),
                                    'updated_at': customer.get('updated_at'),
                                    'first_name': customer.get('first_name'),
                                    'last_name': customer.get('last_name'),
                                    'orders_count': customer.get('orders_count', 0),
                                    'state': customer.get('state'),
                                    'total_spent': float(customer.get('total_spent', 0)),
                                    'last_order_id': customer.get('last_order_id'),
                                    'note': customer.get('note'),
                                    'verified_email': customer.get('verified_email'),
                                    'multipass_identifier': customer.get('multipass_identifier'),
                                    'tax_exempt': customer.get('tax_exempt'),
                                    'phone': customer.get('phone'),
                                    'tags': customer.get('tags'),
                                    'currency': customer.get('currency'),
                                    'default_address': customer.get('default_address', {})
                                }
                                
                                # Calculate total items quantity
                                total_items_quantity = sum(item.get('quantity', 0) for item in order.get('line_items', []))
                                
                                page_orders.append({
                                    'order_id': order.get('id'),
                                    'order_number': order.get('order_number'),
                                    'name': order.get('name'),  # Order name like "#1001"
                                    'created_at': order.get('created_at'),
                                    'updated_at': order.get('updated_at'),
                                    'closed_at': order.get('closed_at'),
                                    'cancelled_at': order.get('cancelled_at'),
                                    'cancel_reason': order.get('cancel_reason'),
                                    'total_price': float(order.get('total_price', 0)),
                                    'subtotal_price': float(order.get('subtotal_price', 0)),
                                    'total_weight': order.get('total_weight', 0),
                                    'total_tax': float(order.get('total_tax', 0)),
                                    'total_discounts': float(order.get('total_discounts', 0)),
                                    'total_line_items_price': float(order.get('total_line_items_price', 0)),
                                    'taxes_included': order.get('taxes_included'),
                                    'currency': order.get('currency'),
                                    'financial_status': order.get('financial_status'),
                                    'confirmed': order.get('confirmed'),
                                    'total_price_usd': float(order.get('total_price_usd', 0)),
                                    'checkout_id': order.get('checkout_id'),
                                    'reference': order.get('reference'),
                                    'user_id': order.get('user_id'),
                                    'location_id': order.get('location_id'),
                                    'source_identifier': order.get('source_identifier'),
                                    'source_url': order.get('source_url'),
                                    'processed_at': order.get('processed_at'),
                                    'device_id': order.get('device_id'),
                                    'phone': order.get('phone'),
                                    'customer_locale': order.get('customer_locale'),
                                    'app_id': order.get('app_id'),
                                    'browser_ip': order.get('browser_ip'),
                                    'landing_site': order.get('landing_site'),
                                    'referring_site': order.get('referring_site'),
                                    'order_status_url': order.get('order_status_url'),
                                    'fulfillment_status': order.get('fulfillment_status'),
                                    'customer_email': order.get('email'),
                                    'customer_data': customer_data,
                                    'line_items_count': len(order.get('line_items', [])),
                                    'total_items_quantity': total_items_quantity,
                                    'line_items': line_items,  # ✅ COMPLETE LINE ITEMS
                                    'fulfillments': fulfillments,  # ✅ ALL FULFILLMENT DATA
                                    'refunds': refunds,  # ✅ ALL REFUND DATA  
                                    'transactions': transactions,  # ✅ ALL TRANSACTION DATA
                                    'shipping_lines': shipping_lines,  # ✅ ALL SHIPPING DATA
                                    'shipping_address': order.get('shipping_address'),
                                    'billing_address': order.get('billing_address'),
                                    'gateway': order.get('gateway'),
                                    'source_name': order.get('source_name'),
                                    'tags': order.get('tags'),
                                    'discount_codes': order.get('discount_codes', []),
                                    'discount_applications': order.get('discount_applications', []),
                                    'note': order.get('note'),
                                    'note_attributes': order.get('note_attributes', []),
                                    'processing_method': order.get('processing_method'),
                                    'checkout_token': order.get('checkout_token'),
                                    'token': order.get('token'),
                                    'cart_token': order.get('cart_token'),
                                    'tax_lines': order.get('tax_lines', []),
                                    'order_adjustments': order.get('order_adjustments', []),
                                    'client_details': order.get('client_details', {}),
                                    'payment_gateway_names': order.get('payment_gateway_names', []),
                                    'payment_details': order.get('payment_details', {}),
                                    'platform': 'shopify',
                                    'raw_data': order  # Keep full raw data for reference
                                })
                            
                            all_orders.extend(page_orders)
                            total_line_items = sum(len(order.get('line_items', [])) for order in page_orders)
                            logger.info(f" Fetched page with {len(page_orders)} orders, {total_line_items} line items (Total: {len(all_orders)} orders)")
                            
                            # Check if there are more pages
                            link_header = response.headers.get('Link', '')
                            if 'rel="next"' in link_header:
                                # Extract page_info from Link header
                                next_match = re.search(r'<[^>]*[?&]page_info=([^&>]+)[^>]*>;\s*rel="next"', link_header)
                                if next_match:
                                    # URL decode the page_info parameter
                                    page_info = unquote(next_match.group(1))
                                    logger.info(f" Next page_info: {page_info[:50]}...")
                                else:
                                    break
                            else:
                                break
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning(" Rate limited by Shopify, waiting 1 second...")
                            await asyncio.sleep(1)
                            continue
                        else:
                            # Get detailed error response
                            error_text = await response.text()
                            logger.error(f" Shopify orders API error {response.status}: {error_text[:200]}")
                            raise APIConnectorError(f"Failed to fetch orders: HTTP {response.status} - {error_text[:100]}")
                
                total_line_items_all = sum(len(order.get('line_items', [])) for order in all_orders)
                logger.info(f" ✅ Fetched ALL {len(all_orders)} Shopify orders with {total_line_items_all} total line items")
                return all_orders
                        
        except Exception as e:
            logger.error(f" Failed to fetch Shopify orders: {e}")
            raise APIConnectorError(f"Shopify orders fetch failed: {str(e)}")
    
    async def fetch_products(self) -> List[Dict]:
        """Fetch ALL products from Shopify with pagination"""
        try:
            all_products = []
            page_info = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    if page_info:
                        # When using page_info, only include limit and page_info
                        params = {
                            "limit": 250,
                            "page_info": page_info
                        }
                    else:
                        # First request - include all filters
                        params = {
                            "limit": 250,  # Use max limit per request for efficiency
                            "published_status": "any"
                        }
                
                    async with session.get(
                        f"{self.base_url}/products.json",
                        headers=self.headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            products = data.get('products', [])
                            
                            # Transform to standard format INCLUDING ALL PRODUCT DATA
                            page_products = []
                            for product in products:
                                # Process ALL variant data
                                variants = []
                                for variant in product.get('variants', []):
                                    variants.append({
                                        'variant_id': variant.get('id'),
                                        'product_id': variant.get('product_id'),
                                        'title': variant.get('title'),
                                        'price': float(variant.get('price', 0)),
                                        'sku': variant.get('sku'),
                                        'position': variant.get('position'),
                                        'inventory_policy': variant.get('inventory_policy'),
                                        'compare_at_price': float(variant.get('compare_at_price', 0)) if variant.get('compare_at_price') else None,
                                        'fulfillment_service': variant.get('fulfillment_service'),
                                        'inventory_management': variant.get('inventory_management'),
                                        'option1': variant.get('option1'),
                                        'option2': variant.get('option2'),
                                        'option3': variant.get('option3'),
                                        'created_at': variant.get('created_at'),
                                        'updated_at': variant.get('updated_at'),
                                        'taxable': variant.get('taxable'),
                                        'barcode': variant.get('barcode'),
                                        'grams': variant.get('grams', 0),
                                        'image_id': variant.get('image_id'),
                                        'weight': variant.get('weight'),
                                        'weight_unit': variant.get('weight_unit'),
                                        'inventory_item_id': variant.get('inventory_item_id'),
                                        'inventory_quantity': variant.get('inventory_quantity', 0),
                                        'old_inventory_quantity': variant.get('old_inventory_quantity', 0),
                                        'requires_shipping': variant.get('requires_shipping'),
                                        'admin_graphql_api_id': variant.get('admin_graphql_api_id')
                                    })
                                
                                # Process ALL image data
                                images = []
                                for image in product.get('images', []):
                                    images.append({
                                        'image_id': image.get('id'),
                                        'product_id': image.get('product_id'),
                                        'position': image.get('position'),
                                        'created_at': image.get('created_at'),
                                        'updated_at': image.get('updated_at'),
                                        'alt': image.get('alt'),
                                        'width': image.get('width'),
                                        'height': image.get('height'),
                                        'src': image.get('src'),
                                        'variant_ids': image.get('variant_ids', [])
                                    })
                                
                                # Process ALL option data
                                options = []
                                for option in product.get('options', []):
                                    options.append({
                                        'option_id': option.get('id'),
                                        'product_id': option.get('product_id'),
                                        'name': option.get('name'),
                                        'position': option.get('position'),
                                        'values': option.get('values', [])
                                    })
                                
                                page_products.append({
                                    'product_id': product.get('id'),
                                    'title': product.get('title'),
                                    'body_html': product.get('body_html'),
                                    'vendor': product.get('vendor'),
                                    'product_type': product.get('product_type'),
                                    'created_at': product.get('created_at'),
                                    'handle': product.get('handle'),
                                    'updated_at': product.get('updated_at'),
                                    'published_at': product.get('published_at'),
                                    'template_suffix': product.get('template_suffix'),
                                    'status': product.get('status'),
                                    'published_scope': product.get('published_scope'),
                                    'tags': product.get('tags'),
                                    'admin_graphql_api_id': product.get('admin_graphql_api_id'),
                                    'seo_title': product.get('seo_title'),
                                    'seo_description': product.get('seo_description'),
                                    'variants': variants,
                                    'options': options,
                                    'images': images,
                                    'image': product.get('image', {}),
                                    'variants_count': len(variants),
                                    'images_count': len(images),
                                    'options_count': len(options),
                                    'platform': 'shopify',
                                    'raw_data': product  # Keep full raw data
                                })
                            
                            all_products.extend(page_products)
                            logger.info(f"️ Fetched page with {len(page_products)} products (Total: {len(all_products)})")
                            
                            # Check if there are more pages
                            link_header = response.headers.get('Link', '')
                            if 'rel="next"' in link_header:
                                # Extract page_info from Link header

                                next_match = re.search(r'<[^>]*[?&]page_info=([^&>]+)[^>]*>;\s*rel="next"', link_header)
                                if next_match:
                                    # URL decode the page_info parameter
                                    page_info = unquote(next_match.group(1))
                                    logger.info(f" Next page_info: {page_info[:50]}...")
                                else:
                                    break
                            else:
                                break
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning(" Rate limited by Shopify, waiting 1 second...")
                            await asyncio.sleep(1)
                            continue
                        else:
                            raise APIConnectorError(f"Failed to fetch products: HTTP {response.status}")
                
                logger.info(f" Fetched ALL {len(all_products)} Shopify products")
                return all_products
                        
        except Exception as e:
            logger.error(f" Failed to fetch Shopify products: {e}")
            raise APIConnectorError(f"Shopify products fetch failed: {str(e)}")

class AmazonConnector:
    """Amazon SP-API Connector - Real-time marketplace data fetching"""
    
    def __init__(self, credentials: AmazonCredentials):
        self.credentials = credentials
        self.base_url = "https://sellingpartnerapi-na.amazon.com"  # North America endpoint
        self.access_token = None
        self.token_expires_at = None
    
    def _safe_get(self, data: dict, key: str, default=None, data_type=None):
        """Safely extract data with type conversion and error handling"""
        try:
            value = data.get(key, default)
            if data_type and value is not None:
                if data_type == float:
                    return float(value) if value != '' else 0.0
                elif data_type == int:
                    return int(value) if value != '' else 0
            return value
        except (ValueError, TypeError) as e:
            logger.warning(f"Error converting {key}={value} to {data_type}: {e}")
            return default if default is not None else (0.0 if data_type == float else 0 if data_type == int else None)
    
    def _safe_nested_get(self, data: dict, keys: list, default=None):
        """Safely get nested dictionary values"""
        try:
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key, {})
                else:
                    return default
            return current if current != {} else default
        except Exception as e:
            logger.warning(f"Error accessing nested path {keys}: {e}")
            return default
    
    async def _get_access_token(self) -> str:
        """Get or refresh Amazon SP-API access token"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        try:
            # Amazon SP-API OAuth token exchange
            token_url = "https://api.amazon.com/auth/o2/token"
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.credentials.refresh_token,
                'client_id': self.credentials.access_key_id,
                'client_secret': self.credentials.secret_access_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        self.token_expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
                        logger.info(" Amazon SP-API token refreshed")
                        return self.access_token
                    else:
                        raise APIConnectorError(f"Failed to get Amazon access token: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f" Failed to get Amazon access token: {e}")
            raise APIConnectorError(f"Amazon token refresh failed: {str(e)}")
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test Amazon SP-API connection"""
        try:
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            # Log detailed connection attempt
            logger.info(f" Testing SP-API connection to {self.base_url}")
            logger.info(f" Using seller_id: {self.credentials.seller_id}")
            logger.info(f" Marketplace IDs: {self.credentials.marketplace_ids}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/sellers/v1/marketplaceParticipations",
                    headers=headers
                ) as response:
                    
                    # Log response details for debugging
                    response_text = await response.text()
                    logger.info(f" SP-API Response Status: {response.status}")
                    logger.info(f" SP-API Response Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        data = await response.json()
                        marketplaces = data.get('payload', [])
                        marketplace_names = [mp.get('marketplace', {}).get('name', 'Unknown') for mp in marketplaces]
                        logger.info(f" Amazon SP-API connection successful: {', '.join(marketplace_names)}")
                        return True, f"Connected to marketplaces: {', '.join(marketplace_names[:3])}"
                    
                    elif response.status == 401:
                        logger.error(f" SP-API 401 Unauthorized: {response_text}")
                        return False, "Invalid credentials or expired token"
                    
                    elif response.status == 403:
                        logger.error(f" SP-API 403 Forbidden: {response_text}")
                        
                        # Parse error response for more details
                        try:
                            error_data = await response.json()
                            error_details = error_data.get('errors', [])
                            if error_details:
                                error_code = error_details[0].get('code', 'Unknown')
                                error_message = error_details[0].get('message', 'Unknown error')
                                logger.error(f" SP-API Error Details - Code: {error_code}, Message: {error_message}")
                                
                                # Provide specific guidance based on error
                                if 'unauthorized' in error_message.lower() or 'forbidden' in error_message.lower():
                                    return False, f"Access Forbidden: {error_message}. Check if your SP-API app is Published (not Draft) and has proper IAM permissions."
                                else:
                                    return False, f"SP-API Error [{error_code}]: {error_message}"
                            else:
                                return False, f"Access Forbidden (403). Possible causes: 1) SP-API app not Published, 2) Missing IAM permissions, 3) Invalid marketplace IDs, 4) Seller account suspended"
                        except:
                            return False, f"Access Forbidden (403). Raw response: {response_text[:200]}..."
                    
                    else:
                        logger.error(f" SP-API Unexpected Status {response.status}: {response_text}")
                        return False, f"Connection failed: HTTP {response.status} - {response_text[:100]}..."
                        
        except Exception as e:
            logger.error(f" Amazon connection test failed: {e}")
            return False, f"Connection error: {str(e)}"
    
    async def fetch_orders(self, days_back: int = None) -> List[Dict]:
        """Fetch ALL orders from Amazon SP-API with pagination INCLUDING ORDER ITEMS (SKUs, quantities)"""
        try:
            all_orders = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            # If days_back is None, fetch all orders ever created
            created_after = None
            if days_back is not None:
                created_after = (datetime.now() - timedelta(days=days_back)).isoformat()
            else:
                # Default to last 2 years if no limit specified to avoid extremely large datasets
                created_after = (datetime.now() - timedelta(days=730)).isoformat()
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        'CreatedAfter': created_after,
                        'MarketplaceIds': ','.join(self.credentials.marketplace_ids),
                        'MaxResultsPerPage': 100  # Amazon max is 100
                    }
                    
                    if next_token:
                        params['NextToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/orders/v0/orders",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            payload = data.get('payload', {})
                            orders = payload.get('Orders', [])
                            
                            # Transform to standard format INCLUDING ALL AMAZON ORDER FIELDS
                            page_orders = []
                            for order in orders:
                                # Amazon order structure
                                order_total = order.get('OrderTotal', {})
                                order_id = order.get('AmazonOrderId')
                                
                                # Fetch order items (SKUs and quantities) for this order
                                order_items = await self._fetch_order_items(session, headers, order_id)
                                
                                # Calculate total items quantity
                                total_items_quantity = sum(item.get('quantity', 0) for item in order_items)
                                
                                # Process shipping address
                                shipping_address = order.get('ShippingAddress', {})
                                shipping_address_data = {
                                    'name': shipping_address.get('Name'),
                                    'address_line1': shipping_address.get('AddressLine1'),
                                    'address_line2': shipping_address.get('AddressLine2'),
                                    'address_line3': shipping_address.get('AddressLine3'),
                                    'city': shipping_address.get('City'),
                                    'county': shipping_address.get('County'),
                                    'district': shipping_address.get('District'),
                                    'state_or_region': shipping_address.get('StateOrRegion'),
                                    'municipality': shipping_address.get('Municipality'),
                                    'postal_code': shipping_address.get('PostalCode'),
                                    'country_code': shipping_address.get('CountryCode'),
                                    'phone': shipping_address.get('Phone'),
                                    'address_type': shipping_address.get('AddressType')
                                }
                                
                                # Process buyer info
                                buyer_info = order.get('BuyerInfo', {})
                                buyer_data = {
                                    'buyer_email': buyer_info.get('BuyerEmail'),
                                    'buyer_name': buyer_info.get('BuyerName'),
                                    'buyer_county': buyer_info.get('BuyerCounty'),
                                    'buyer_tax_info': buyer_info.get('BuyerTaxInfo', {})
                                }
                                
                                # Process payment execution details
                                payment_execution_detail = order.get('PaymentExecutionDetail', [])
                                payment_details = []
                                for payment in payment_execution_detail:
                                    payment_details.append({
                                        'payment_method': payment.get('PaymentMethod'),
                                        'payment_method_details': payment.get('PaymentMethodDetails', [])
                                    })
                                
                                page_orders.append({
                                    'order_id': order_id,
                                    'order_number': order_id,
                                    'seller_order_id': order.get('SellerOrderId'),
                                    'purchase_date': order.get('PurchaseDate'),
                                    'created_at': order.get('PurchaseDate'),
                                    'last_update_date': order.get('LastUpdateDate'),
                                    'updated_at': order.get('LastUpdateDate'),
                                    'order_status': order.get('OrderStatus'),
                                    'fulfillment_channel': order.get('FulfillmentChannel'),
                                    'sales_channel': order.get('SalesChannel'),
                                    'order_channel': order.get('OrderChannel'),
                                    'url': order.get('Url'),
                                    'ship_service_level': order.get('ShipServiceLevel'),
                                    'total_price': float(order_total.get('Amount', 0)),
                                    'currency': order_total.get('CurrencyCode', 'USD'),
                                    'number_of_items_shipped': order.get('NumberOfItemsShipped', 0),
                                    'number_of_items_unshipped': order.get('NumberOfItemsUnshipped', 0),
                                    'total_items_quantity': total_items_quantity,
                                    'payment_execution_detail': payment_details,
                                    'payment_method': order.get('PaymentMethod'),
                                    'payment_method_details': order.get('PaymentMethodDetails', []),
                                    'marketplace_id': order.get('MarketplaceId'),
                                    'shipment_service_level_category': order.get('ShipmentServiceLevelCategory'),
                                    'cba_displayable_shipping_label': order.get('CbaDisplayableShippingLabel'),
                                    'order_type': order.get('OrderType'),
                                    'earliest_ship_date': order.get('EarliestShipDate'),
                                    'latest_ship_date': order.get('LatestShipDate'),
                                    'earliest_delivery_date': order.get('EarliestDeliveryDate'),
                                    'latest_delivery_date': order.get('LatestDeliveryDate'),
                                    'is_business_order': order.get('IsBusinessOrder', False),
                                    'is_prime': order.get('IsPrime', False),
                                    'is_premium_order': order.get('IsPremiumOrder', False),
                                    'is_global_express_enabled': order.get('IsGlobalExpressEnabled', False),
                                    'replaced_order_id': order.get('ReplacedOrderId'),
                                    'is_replacement_order': order.get('IsReplacementOrder', False),
                                    'promise_response_due_date': order.get('PromiseResponseDueDate'),
                                    'is_estimated_ship_date_set': order.get('IsEstimatedShipDateSet', False),
                                    'is_sold_by_ab': order.get('IsSoldByAB', False),
                                    'is_iba': order.get('IsIBA', False),
                                    'default_ship_from_location_address': order.get('DefaultShipFromLocationAddress', {}),
                                    'buyer_invoice_preference': order.get('BuyerInvoicePreference'),
                                    'buyer_tax_information': order.get('BuyerTaxInformation', {}),
                                    'fulfillment_instruction': order.get('FulfillmentInstruction', {}),
                                    'is_ispu': order.get('IsISPU', False),
                                    'is_access_point_order': order.get('IsAccessPointOrder', False),
                                    'marketplace_tax_info': order.get('MarketplaceTaxInfo', {}),
                                    'seller_display_name': order.get('SellerDisplayName'),
                                    'shipping_address': shipping_address_data,
                                    'buyer_info': buyer_data,
                                    'line_items': order_items,  # ✅ ALL ORDER ITEMS WITH SKUs
                                    'platform': 'amazon',
                                    'raw_data': order  # Keep full raw data for reference
                                })
                            
                            all_orders.extend(page_orders)
                            total_line_items = sum(len(order.get('line_items', [])) for order in page_orders)
                            logger.info(f" Fetched page with {len(page_orders)} Amazon orders, {total_line_items} line items (Total: {len(all_orders)} orders)")
                            
                            # Check for next page
                            next_token = payload.get('NextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(0.2)  # 5 requests per second max
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning(" Rate limited by Amazon SP-API, waiting 10 seconds...")
                            await asyncio.sleep(10)
                            continue
                        else:
                            raise APIConnectorError(f"Failed to fetch orders: HTTP {response.status}")
                
                total_line_items_all = sum(len(order.get('line_items', [])) for order in all_orders)
                logger.info(f" ✅ Fetched ALL {len(all_orders)} Amazon orders with {total_line_items_all} total line items")
                return all_orders
                        
        except Exception as e:
            logger.error(f" Failed to fetch Amazon orders: {e}")
            raise APIConnectorError(f"Amazon orders fetch failed: {str(e)}")
    
    async def _fetch_order_items(self, session, headers, order_id: str) -> List[Dict]:
        """Fetch order items (SKUs, quantities) for a specific Amazon order"""
        try:
            async with session.get(
                f"{self.base_url}/orders/v0/orders/{order_id}/orderItems",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    payload = data.get('payload', {})
                    order_items = payload.get('OrderItems', [])
                    
                    # Transform order items to standard format INCLUDING ALL ITEM FIELDS
                    line_items = []
                    for item in order_items:
                        # Handle complex pricing structures
                        item_price = item.get('ItemPrice', {})
                        shipping_price = item.get('ShippingPrice', {})
                        gift_wrap_price = item.get('GiftWrapPrice', {})
                        item_tax = item.get('ItemTax', {})
                        shipping_tax = item.get('ShippingTax', {})
                        shipping_discount = item.get('ShippingDiscount', {})
                        shipping_discount_tax = item.get('ShippingDiscountTax', {})
                        promotion_discount = item.get('PromotionDiscount', {})
                        promotion_discount_tax = item.get('PromotionDiscountTax', {})
                        cod_fee = item.get('CODFee', {})
                        cod_fee_discount = item.get('CODFeeDiscount', {})
                        
                        # Handle product info complex structure
                        product_info = item.get('ProductInfo', {})
                        
                        # Handle points granted
                        points_granted = item.get('PointsGranted', {})
                        
                        line_items.append({
                            'line_item_id': item.get('OrderItemId'),
                            'asin': item.get('ASIN'),
                            'seller_sku': item.get('SellerSKU'),
                            'sku': item.get('SellerSKU'),  # Use SellerSKU as primary SKU
                            'buyer_product_identifier': item.get('BuyerProductIdentifier'),
                            'title': item.get('Title'),
                            'quantity_ordered': int(item.get('QuantityOrdered', 0)),
                            'quantity_shipped': int(item.get('QuantityShipped', 0)),
                            'quantity': int(item.get('QuantityOrdered', 0)),  # Alias for consistency
                            'points_granted': {
                                'points_number': points_granted.get('PointsNumber', 0),
                                'points_monetary_value': points_granted.get('PointsMonetaryValue', {})
                            },
                            # Pricing information
                            'item_price': {
                                'amount': float(item_price.get('Amount', 0)),
                                'currency_code': item_price.get('CurrencyCode', 'USD')
                            },
                            'price': float(item_price.get('Amount', 0)),  # Simplified price
                            'currency': item_price.get('CurrencyCode', 'USD'),
                            'shipping_price': {
                                'amount': float(shipping_price.get('Amount', 0)),
                                'currency_code': shipping_price.get('CurrencyCode', 'USD')
                            },
                            'gift_wrap_price': {
                                'amount': float(gift_wrap_price.get('Amount', 0)),
                                'currency_code': gift_wrap_price.get('CurrencyCode', 'USD')
                            },
                            'item_tax': {
                                'amount': float(item_tax.get('Amount', 0)),
                                'currency_code': item_tax.get('CurrencyCode', 'USD')
                            },
                            'shipping_tax': {
                                'amount': float(shipping_tax.get('Amount', 0)),
                                'currency_code': shipping_tax.get('CurrencyCode', 'USD')
                            },
                            'shipping_discount': {
                                'amount': float(shipping_discount.get('Amount', 0)),
                                'currency_code': shipping_discount.get('CurrencyCode', 'USD')
                            },
                            'shipping_discount_tax': {
                                'amount': float(shipping_discount_tax.get('Amount', 0)),
                                'currency_code': shipping_discount_tax.get('CurrencyCode', 'USD')
                            },
                            'promotion_discount': {
                                'amount': float(promotion_discount.get('Amount', 0)),
                                'currency_code': promotion_discount.get('CurrencyCode', 'USD')
                            },
                            'promotion_discount_tax': {
                                'amount': float(promotion_discount_tax.get('Amount', 0)),
                                'currency_code': promotion_discount_tax.get('CurrencyCode', 'USD')
                            },
                            'cod_fee': {
                                'amount': float(cod_fee.get('Amount', 0)),
                                'currency_code': cod_fee.get('CurrencyCode', 'USD')
                            },
                            'cod_fee_discount': {
                                'amount': float(cod_fee_discount.get('Amount', 0)),
                                'currency_code': cod_fee_discount.get('CurrencyCode', 'USD')
                            },
                            # Product information
                            'product_info': {
                                'number_of_items': product_info.get('NumberOfItems', 1)
                            },
                            'condition_id': item.get('ConditionId'),
                            'condition_subtype_id': item.get('ConditionSubtypeId'),
                            'condition_note': item.get('ConditionNote'),
                            'scheduled_delivery_start_date': item.get('ScheduledDeliveryStartDate'),
                            'scheduled_delivery_end_date': item.get('ScheduledDeliveryEndDate'),
                            'price_designation': item.get('PriceDesignation'),
                            'tax_collection': item.get('TaxCollection', {}),
                            'serial_number_required': item.get('SerialNumberRequired', False),
                            'is_gift': item.get('IsGift', False),
                            'condition_note': item.get('ConditionNote'),
                            'condition_id': item.get('ConditionId'),
                            'condition_subtype_id': item.get('ConditionSubtypeId'),
                            'is_transparency': item.get('IsTransparency', False),
                            'buyer_requested_cancel': item.get('BuyerRequestedCancel', {}),
                            'substitution_preferences': item.get('SubstitutionPreferences', {}),
                            'measurement': item.get('Measurement', {})
                        })
                    
                    return line_items
                    
                elif response.status == 429:
                    # Rate limited - wait and retry
                    logger.warning(f" Rate limited when fetching order items for {order_id}, waiting 2 seconds...")
                    await asyncio.sleep(2)
                    return await self._fetch_order_items(session, headers, order_id)  # Retry
                else:
                    logger.warning(f" Failed to fetch order items for {order_id}: HTTP {response.status}")
                    return []  # Return empty list if can't fetch items
                    
        except Exception as e:
            logger.warning(f" Failed to fetch order items for {order_id}: {e}")
            return []  # Return empty list on error
    
    async def fetch_products(self) -> List[Dict]:
        """Fetch ALL products from Amazon SP-API Catalog"""
        try:
            all_products = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        'marketplaceIds': ','.join(self.credentials.marketplace_ids),
                        'includedData': 'attributes,images,productTypes,relationships,salesRanks',
                        'pageSize': 20  # Amazon catalog API max is 20
                    }
                    
                    if next_token:
                        params['pageToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/catalog/2022-04-01/items",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            items = data.get('items', [])
                            
                            # Transform to standard format
                            page_products = []
                            for item in items:
                                # Extract attributes
                                attributes = item.get('attributes', {})
                                
                                page_products.append({
                                    'asin': item.get('asin'),
                                    'title': attributes.get('item_name', [{}])[0].get('value', 'Unknown'),
                                    'brand': attributes.get('brand', [{}])[0].get('value', 'Unknown'),
                                    'manufacturer': attributes.get('manufacturer', [{}])[0].get('value', 'Unknown'),
                                    'product_type': ', '.join([pt.get('displayName', '') for pt in item.get('productTypes', [])]),
                                    'images': [img.get('link') for img in item.get('images', [])],
                                    'sales_rank': item.get('salesRanks', []),
                                    'relationships': item.get('relationships', []),
                                    'marketplace_ids': [mp_id for mp_id in self.credentials.marketplace_ids],
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'raw_data': item
                                })
                            
                            all_products.extend(page_products)
                            logger.info(f" Fetched page with {len(page_products)} Amazon catalog products (Total: {len(all_products)})")
                            
                            # Check for next page
                            pagination = data.get('pagination', {})
                            next_token = pagination.get('nextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(0.5)  # Be conservative with catalog API
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning(" Rate limited by Amazon Catalog API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.error(f" Amazon Catalog API error {response.status}: {error_text[:200]}")
                            raise APIConnectorError(f"Failed to fetch products: HTTP {response.status}")
                
                logger.info(f" ✅ Fetched ALL {len(all_products)} Amazon catalog products")
                return all_products
                        
        except Exception as e:
            logger.error(f" Failed to fetch Amazon products: {e}")
            raise APIConnectorError(f"Amazon products fetch failed: {str(e)}")
    
    async def fetch_fba_inventory(self) -> List[Dict]:
        """Fetch FBA on-hand inventory per SKU - Available, Reserved, Inbound quantities"""
        try:
            all_inventory = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        'granularityType': 'Marketplace',
                        'granularityId': self.credentials.marketplace_ids[0],  # Use first marketplace
                        'marketplaceIds': ','.join(self.credentials.marketplace_ids)
                    }
                    
                    if next_token:
                        params['nextToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/fba/inventory/v1/summaries",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            payload = data.get('payload', {})
                            inventory_summaries = payload.get('inventorySummaries', [])
                            
                            # Transform to standard format with ALL FBA inventory details
                            page_inventory = []
                            for summary in inventory_summaries:
                                # Get all inventory details for this SKU
                                inventory_details = summary.get('inventoryDetails', {})
                                
                                # ✅ SAFE DATA EXTRACTION with error handling
                                fulfillable_qty = self._safe_get(inventory_details, 'fulfillableQuantity', 0, int)
                                inbound_working_qty = self._safe_get(inventory_details, 'inboundWorkingQuantity', 0, int)
                                unfulfillable_qty = self._safe_get(inventory_details, 'unfulfillableQuantity', 0, int)
                                researching_qty = self._safe_get(inventory_details, 'researchingQuantity', 0, int)
                                
                                # Handle reserved quantity (structure may vary)
                                reserved_qty = inventory_details.get('reservedQuantity', {})
                                if isinstance(reserved_qty, dict):
                                    reserved_total = sum([
                                        self._safe_get(reserved_qty, 'fcTransfers', 0, int),
                                        self._safe_get(reserved_qty, 'fcProcessing', 0, int),
                                        self._safe_get(reserved_qty, 'customerOrders', 0, int)
                                    ])
                                else:
                                    reserved_total = self._safe_get({}, 'reservedQuantity', 0, int)
                                
                                page_inventory.append({
                                    'sku': self._safe_get(summary, 'sellerSku'),
                                    'asin': self._safe_get(summary, 'asin'),
                                    'fnsku': self._safe_get(summary, 'fnSku'),
                                    'condition': self._safe_get(summary, 'condition'),
                                    'marketplace_id': self._safe_get(summary, 'marketplaceId'),
                                    
                                    # ✅ SAFE: Available inventory (ready to ship)
                                    'fulfillable_quantity': fulfillable_qty,
                                    'available_quantity': fulfillable_qty,  # Alias
                                    
                                    # ✅ SAFE: Working inventory (being processed)
                                    'inbound_working_quantity': inbound_working_qty,
                                    'inbound_shipped_quantity': self._safe_get(inventory_details, 'inboundShippedQuantity', 0, int),
                                    'inbound_receiving_quantity': self._safe_get(inventory_details, 'inboundReceivingQuantity', 0, int),
                                    
                                    # ✅ SAFE: Reserved inventory (structure-agnostic)
                                    'reserved_quantity_total': reserved_total,
                                    'reserved_quantity_raw': reserved_qty,  # Keep raw for analysis
                                    
                                    # ✅ SAFE: Unfulfillable inventory
                                    'unfulfillable_quantity': unfulfillable_qty,
                                    'unsellable_quantity': unfulfillable_qty,  # Alias
                                    
                                    # ✅ SAFE: Research quantity
                                    'researching_quantity': researching_qty,
                                    
                                    # ✅ SAFE: Total quantity calculations
                                    'total_quantity': fulfillable_qty + inbound_working_qty + unfulfillable_qty + researching_qty,
                                    
                                    # Timestamps
                                    'last_updated_time': self._safe_get(summary, 'lastUpdatedTime'),
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'inventory_type': 'fba_onhand',
                                    'raw_data': summary  # ✅ ALWAYS keep raw data for debugging
                                })
                            
                            all_inventory.extend(page_inventory)
                            logger.info(f"📦 Fetched page with {len(page_inventory)} FBA inventory SKUs (Total: {len(all_inventory)})")
                            
                            # Check for next page
                            pagination = payload.get('pagination', {})
                            next_token = pagination.get('nextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(0.5)  # Be conservative with inventory API
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning("📦 Rate limited by Amazon FBA Inventory API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"📦 Amazon FBA Inventory API error {response.status}: {error_text[:200]}")
                            # Inventory API might not be accessible for all sellers
                            logger.info("📦 FBA Inventory API might not be available for this seller account")
                            break
                
                logger.info(f"📦 ✅ Fetched {len(all_inventory)} FBA inventory items with quantities")
                return all_inventory
                        
        except Exception as e:
            logger.warning(f"📦 Failed to fetch FBA inventory (this is normal if FBA not enabled): {e}")
            return []  # Return empty list instead of failing
    
    async def fetch_fba_inbound_shipments(self) -> List[Dict]:
        """Fetch detailed FBA inbound shipments with SKU-level item data"""
        try:
            all_shipments = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # First get list of shipments with required parameters
                while True:
                    params = {
                        'ShipmentStatusList': 'WORKING,SHIPPED,RECEIVING,CANCELLED,DELETED,CLOSED,ERROR'
                    }
                    if next_token:
                        params['NextToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/fba/inbound/v0/shipments",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            payload = data.get('payload', {})
                            shipments = payload.get('ShipmentData', [])
                            
                            # For each shipment, get detailed items
                            for shipment in shipments:
                                shipment_id = shipment.get('ShipmentId')
                                if shipment_id:
                                    shipment_items = await self._fetch_shipment_items(session, headers, shipment_id)
                                    
                                    all_shipments.append({
                                        'shipment_id': shipment_id,
                                        'shipment_name': shipment.get('ShipmentName'),
                                        'shipment_status': shipment.get('ShipmentStatus'),
                                        'destination_fulfillment_center_id': shipment.get('DestinationFulfillmentCenterId'),
                                        'label_prep_preference': shipment.get('LabelPrepPreference'),
                                        'are_cases_required': shipment.get('AreCasesRequired'),
                                        'confirmed_need_by_date': shipment.get('ConfirmedNeedByDate'),
                                        'box_contents_source': shipment.get('BoxContentsSource'),
                                        'estimated_box_contents_fee': shipment.get('EstimatedBoxContentsFee'),
                                        'ship_from_address': shipment.get('ShipFromAddress', {}),
                                        'items': shipment_items,  # ✅ SKU-level item data
                                        'items_count': len(shipment_items),
                                        'total_units': sum(item.get('quantity_shipped', 0) for item in shipment_items),
                                        'created_at': datetime.now().isoformat(),
                                        'platform': 'amazon',
                                        'inventory_type': 'fba_inbound',
                                        'raw_data': shipment
                                    })
                            
                            logger.info(f"🚚 Fetched page with {len(shipments)} FBA inbound shipments")
                            
                            # Check for next page
                            next_token = payload.get('NextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(1)
                        
                        elif response.status == 429:
                            logger.warning("🚚 Rate limited by Amazon FBA Inbound API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"🚚 Amazon FBA Inbound API error {response.status}: {error_text[:200]}")
                            break
                
                total_items = sum(len(shipment.get('items', [])) for shipment in all_shipments)
                logger.info(f"🚚 ✅ Fetched {len(all_shipments)} FBA inbound shipments with {total_items} items")
                return all_shipments
                        
        except Exception as e:
            logger.warning(f"🚚 Failed to fetch FBA inbound shipments: {e}")
            return []
    
    async def _fetch_shipment_items(self, session, headers, shipment_id: str) -> List[Dict]:
        """Fetch items for a specific FBA inbound shipment"""
        try:
            async with session.get(
                f"{self.base_url}/fba/inbound/v0/shipments/{shipment_id}/items",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    payload = data.get('payload', {})
                    items = payload.get('ItemData', [])
                    
                    # Transform items to standard format
                    shipment_items = []
                    for item in items:
                        shipment_items.append({
                            'sku': item.get('SellerSKU'),
                            'fnsku': item.get('FulfillmentNetworkSKU'),
                            'quantity_shipped': int(item.get('QuantityShipped', 0)),
                            'quantity_received': int(item.get('QuantityReceived', 0)),
                            'quantity_in_case': int(item.get('QuantityInCase', 0)),
                            'release_date': item.get('ReleaseDate'),
                            'prep_details_list': item.get('PrepDetailsList', []),
                            'raw_data': item
                        })
                    
                    return shipment_items
                    
                elif response.status == 429:
                    logger.warning(f"🚚 Rate limited when fetching shipment items for {shipment_id}")
                    await asyncio.sleep(2)
                    return await self._fetch_shipment_items(session, headers, shipment_id)  # Retry
                else:
                    logger.warning(f"🚚 Failed to fetch shipment items for {shipment_id}: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.warning(f"🚚 Failed to fetch shipment items for {shipment_id}: {e}")
            return []

    async def fetch_listings_pricing(self) -> List[Dict]:
        """Fetch product listings with pricing data per SKU"""
        try:
            all_listings = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        'sellerId': self.credentials.seller_id,
                        'marketplaceIds': ','.join(self.credentials.marketplace_ids),
                        'includedData': 'summaries,attributes,issues,offers,fulfillmentAvailability,procurement'
                    }
                    
                    if next_token:
                        params['pageToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/listings/2021-08-01/items",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            listings = data.get('listings', [])
                            
                            # Transform to standard format with pricing and listing details
                            page_listings = []
                            for listing in listings:
                                summaries = listing.get('summaries', [])
                                attributes = listing.get('attributes', {})
                                offers = listing.get('offers', [])
                                
                                # ✅ SAFE: Extract pricing from offers
                                pricing_info = {}
                                if offers:
                                    main_offer = offers[0]  # Use first offer as primary
                                    listing_price = main_offer.get('listingPrice', {})
                                    pricing_info = {
                                        'listing_price': self._safe_nested_get(listing_price, ['Amount'], 0.0),
                                        'listing_price_float': self._safe_get(listing_price, 'Amount', 0.0, float),
                                        'currency': self._safe_get(listing_price, 'CurrencyCode', 'USD'),
                                        'minimum_seller_allowed_price': self._safe_nested_get(main_offer, ['minimumSellerAllowedPrice', 'Amount'], 0.0),
                                        'maximum_seller_allowed_price': self._safe_nested_get(main_offer, ['maximumSellerAllowedPrice', 'Amount'], 0.0),
                                        'buyer_price': self._safe_nested_get(main_offer, ['buyerPrice', 'Amount'], 0.0),
                                        'regular_price': self._safe_nested_get(main_offer, ['regularPrice', 'Amount'], 0.0),
                                        'fulfillment_channel': self._safe_get(main_offer, 'fulfillmentChannel'),
                                        'merchant_shipping_group': self._safe_get(main_offer, 'merchantShippingGroup'),
                                        'points': main_offer.get('points', {}),
                                        'prime': main_offer.get('prime', {}),
                                        'pricing_raw': main_offer  # ✅ Keep raw pricing data
                                    }
                                
                                # Extract basic listing info from summaries
                                listing_info = {}
                                if summaries:
                                    main_summary = summaries[0]  # Use first summary as primary
                                    listing_info = {
                                        'marketplace_id': main_summary.get('marketplaceId'),
                                        'asin': main_summary.get('asin'),
                                        'product_type': main_summary.get('productType'),
                                        'condition_type': main_summary.get('conditionType'),
                                        'status': main_summary.get('status'),
                                        'fn_sku': main_summary.get('fnSku'),
                                        'item_name': main_summary.get('itemName'),
                                        'created_date': main_summary.get('createdDate'),
                                        'last_updated_date': main_summary.get('lastUpdatedDate'),
                                        'main_image': main_summary.get('mainImage', {}),
                                        'link': main_summary.get('link')
                                    }
                                
                                page_listings.append({
                                    'sku': listing.get('sku'),
                                    **listing_info,
                                    **pricing_info,
                                    'summaries': summaries,
                                    'attributes': attributes,
                                    'offers': offers,
                                    'fulfillment_availability': listing.get('fulfillmentAvailability', []),
                                    'procurement': listing.get('procurement', {}),
                                    'issues': listing.get('issues', []),
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'data_type': 'listings_pricing',
                                    'raw_data': listing
                                })
                            
                            all_listings.extend(page_listings)
                            logger.info(f"💰 Fetched page with {len(page_listings)} listing prices (Total: {len(all_listings)})")
                            
                            # Check for next page
                            pagination = data.get('pagination', {})
                            next_token = pagination.get('nextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(0.5)  # Be conservative with listings API
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning("💰 Rate limited by Amazon Listings API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"💰 Amazon Listings API error {response.status}: {error_text[:200]}")
                            # Listings API might not be accessible for all sellers
                            logger.info("💰 Listings API might not be available for this seller account")
                            break
                
                logger.info(f"💰 ✅ Fetched {len(all_listings)} product listings with pricing data")
                return all_listings
                        
        except Exception as e:
            logger.warning(f"💰 Failed to fetch listings pricing: {e}")
            return []  # Return empty list instead of failing
    
    async def fetch_awd_inventory(self) -> List[Dict]:
        """Fetch Amazon Warehousing and Distribution (AWD) inventory data"""
        try:
            all_awd_inventory = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        'maxResultsPerPage': 100
                    }
                    
                    if next_token:
                        params['nextToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/awd/2024-05-09/inventory",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            inventory_summaries = data.get('inventorySummaries', [])
                            
                            # Transform to standard format
                            page_inventory = []
                            for summary in inventory_summaries:
                                distribution_package = summary.get('distributionPackage', {})
                                
                                page_inventory.append({
                                    'sku': summary.get('sku'),
                                    'package_id': distribution_package.get('packageId'),
                                    'package_status': distribution_package.get('packageStatus'),
                                    'tracking_id': distribution_package.get('trackingId'),
                                    'quantity': summary.get('quantity', 0),
                                    'available_quantity': summary.get('availableQuantity', 0),
                                    'reserved_quantity': summary.get('reservedQuantity', 0),
                                    'product_title': summary.get('productTitle'),
                                    'measurement_unit': summary.get('measurementUnit'),
                                    'measurement_value': summary.get('measurementValue', 0),
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'inventory_type': 'awd',
                                    'raw_data': summary
                                })
                            
                            all_awd_inventory.extend(page_inventory)
                            logger.info(f"🏭 Fetched page with {len(page_inventory)} AWD inventory items (Total: {len(all_awd_inventory)})")
                            
                            # Check for next page
                            pagination = data.get('pagination', {})
                            next_token = pagination.get('nextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(1)  # Be conservative with AWD API
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning("🏭 Rate limited by Amazon AWD API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"🏭 Amazon AWD API error {response.status}: {error_text[:200]}")
                            # AWD API might not be accessible for all sellers
                            logger.info("🏭 AWD API might not be available for this seller account")
                            break
                
                logger.info(f"🏭 ✅ Fetched {len(all_awd_inventory)} AWD inventory items")
                return all_awd_inventory
                        
        except Exception as e:
            logger.warning(f"🏭 Failed to fetch AWD inventory: {e}")
            return []  # Return empty list instead of failing
    
    async def fetch_awd_inbound_shipments(self) -> List[Dict]:
        """Fetch AWD inbound shipments data"""
        try:
            all_awd_shipments = []
            next_token = None
            
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        'maxResultsPerPage': 100
                    }
                    
                    if next_token:
                        params['nextToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/awd/2024-05-09/inboundShipments",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            inbound_shipments = data.get('inboundShipments', [])
                            
                            # Transform to standard format
                            page_shipments = []
                            for shipment in inbound_shipments:
                                # Get shipment items if available
                                shipment_items = []
                                distribution_packages = shipment.get('distributionPackages', [])
                                for package in distribution_packages:
                                    shipment_items.append({
                                        'package_id': package.get('packageId'),
                                        'sku': package.get('sku'),
                                        'quantity': package.get('quantity', 0),
                                        'measurement_unit': package.get('measurementUnit'),
                                        'measurement_value': package.get('measurementValue', 0),
                                        'package_status': package.get('packageStatus'),
                                        'tracking_id': package.get('trackingId')
                                    })
                                
                                page_shipments.append({
                                    'shipment_id': shipment.get('shipmentId'),
                                    'shipment_name': shipment.get('shipmentName'),
                                    'shipment_status': shipment.get('shipmentStatus'),
                                    'created_date': shipment.get('createdDate'),
                                    'last_updated_date': shipment.get('lastUpdatedDate'),
                                    'origin': shipment.get('origin', {}),
                                    'destination': shipment.get('destination', {}),
                                    'transportation': shipment.get('transportation', {}),
                                    'distribution_packages': shipment_items,
                                    'packages_count': len(shipment_items),
                                    'total_units': sum(item.get('quantity', 0) for item in shipment_items),
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'inventory_type': 'awd_inbound',
                                    'raw_data': shipment
                                })
                            
                            all_awd_shipments.extend(page_shipments)
                            logger.info(f"🚛 Fetched page with {len(page_shipments)} AWD inbound shipments (Total: {len(all_awd_shipments)})")
                            
                            # Check for next page
                            pagination = data.get('pagination', {})
                            next_token = pagination.get('nextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(1)  # Be conservative with AWD API
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning("🚛 Rate limited by Amazon AWD Inbound API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"🚛 Amazon AWD Inbound API error {response.status}: {error_text[:200]}")
                            # AWD API might not be accessible for all sellers
                            logger.info("🚛 AWD Inbound API might not be available for this seller account")
                            break
                
                total_packages = sum(len(shipment.get('distribution_packages', [])) for shipment in all_awd_shipments)
                logger.info(f"🚛 ✅ Fetched {len(all_awd_shipments)} AWD inbound shipments with {total_packages} packages")
                return all_awd_shipments
                        
        except Exception as e:
            logger.warning(f"🚛 Failed to fetch AWD inbound shipments: {e}")
            return []  # Return empty list instead of failing

    async def extract_sku_pricing_from_orders(self, orders_data: List[Dict], days_back: int = 30) -> List[Dict]:
        """Extract pricing data per SKU from order line items - Better than Listings API!"""
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict
            import statistics
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            sku_pricing = defaultdict(list)
            sku_stats = {}
            
            logger.info(f"📊 Extracting SKU pricing from {len(orders_data)} orders (last {days_back} days)")
            
            # Collect all price data per SKU
            for order in orders_data:
                try:
                    order_date = datetime.fromisoformat(order.get('created_at', '').replace('Z', '+00:00'))
                    if order_date >= cutoff_date:
                        for item in order.get('line_items', []):
                            sku = item.get('sku')
                            price = item.get('price', 0)
                            quantity = item.get('quantity', 0)
                            
                            if sku and price > 0:
                                sku_pricing[sku].append({
                                    'price': float(price),
                                    'quantity': int(quantity),
                                    'order_date': order_date.isoformat(),
                                    'order_id': order.get('order_id'),
                                    'currency': item.get('currency', 'USD')
                                })
                except Exception as e:
                    logger.warning(f"Error processing order {order.get('order_id')}: {e}")
                    continue
            
            # Calculate pricing statistics per SKU
            pricing_results = []
            for sku, price_data in sku_pricing.items():
                if not price_data:
                    continue
                
                prices = [item['price'] for item in price_data]
                quantities = [item['quantity'] for item in price_data]
                total_quantity = sum(quantities)
                total_revenue = sum(item['price'] * item['quantity'] for item in price_data)
                
                # Calculate pricing metrics
                avg_price = statistics.mean(prices)
                median_price = statistics.median(prices)
                min_price = min(prices)
                max_price = max(prices)
                price_std = statistics.stdev(prices) if len(prices) > 1 else 0
                weighted_avg_price = total_revenue / total_quantity if total_quantity > 0 else 0
                
                # Most recent and oldest prices
                sorted_by_date = sorted(price_data, key=lambda x: x['order_date'])
                most_recent_price = sorted_by_date[-1]['price']
                oldest_price = sorted_by_date[0]['price']
                
                pricing_results.append({
                    'sku': sku,
                    'currency': price_data[0]['currency'],
                    
                    # 🎯 KEY PRICING METRICS
                    'average_price': round(avg_price, 2),
                    'weighted_average_price': round(weighted_avg_price, 2),  # Revenue-weighted
                    'median_price': round(median_price, 2),
                    'min_price': round(min_price, 2),
                    'max_price': round(max_price, 2),
                    'price_std_dev': round(price_std, 2),
                    'most_recent_price': round(most_recent_price, 2),
                    'oldest_price': round(oldest_price, 2),
                    
                    # 📊 SALES METRICS
                    'total_units_sold': total_quantity,
                    'total_revenue': round(total_revenue, 2),
                    'number_of_orders': len(price_data),
                    'date_range_days': days_back,
                    
                    # 📈 PRICE TRENDS
                    'price_change': round(most_recent_price - oldest_price, 2),
                    'price_change_percent': round(((most_recent_price - oldest_price) / oldest_price * 100), 2) if oldest_price > 0 else 0,
                    'price_volatility': 'HIGH' if price_std > avg_price * 0.1 else 'LOW',
                    
                    # 📅 TIME DATA
                    'first_sale_date': sorted_by_date[0]['order_date'],
                    'last_sale_date': sorted_by_date[-1]['order_date'],
                    
                    # 🎯 CALCULATED FIELDS FOR DASHBOARD
                    'revenue_per_unit': round(weighted_avg_price, 2),
                    'sales_frequency': round(len(price_data) / days_back, 3),  # Orders per day
                    
                    # 📋 RAW DATA
                    'pricing_raw_data': price_data,
                    'created_at': datetime.now().isoformat(),
                    'platform': 'amazon',
                    'data_type': 'sku_pricing_from_orders'
                })
            
            # Sort by total revenue (highest first)
            pricing_results.sort(key=lambda x: x['total_revenue'], reverse=True)
            
            logger.info(f"💰 ✅ Extracted pricing for {len(pricing_results)} SKUs from order data")
            return pricing_results
            
        except Exception as e:
            logger.error(f"💰 Failed to extract SKU pricing from orders: {e}")
            return []

    async def fetch_incoming_inventory(self) -> List[Dict]:
        """Legacy method - redirect to new enhanced inbound shipments"""
        return await self.fetch_fba_inbound_shipments()

class WooCommerceConnector:
    """WooCommerce REST API Connector"""
    
    def __init__(self, credentials: WooCommerceCredentials):
        self.credentials = credentials
        self.base_url = f"{credentials.site_url}/wp-json/{credentials.version}"
        
    async def test_connection(self) -> Tuple[bool, str]:
        """Test WooCommerce connection"""
        try:
            auth = aiohttp.BasicAuth(self.credentials.consumer_key, self.credentials.consumer_secret)
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(f"{self.base_url}/system_status") as response:
                    if response.status == 200:
                        data = await response.json()
                        site_title = data.get('settings', {}).get('title', 'WooCommerce Site')
                        return True, f"Connected to {site_title}"
                    elif response.status == 401:
                        return False, "Invalid consumer key/secret"
                    else:
                        return False, f"Connection failed: HTTP {response.status}"
                        
        except Exception as e:
            logger.error(f" WooCommerce connection test failed: {e}")
            return False, f"Connection error: {str(e)}"

class APIConnectorFactory:
    """Factory to create appropriate API connectors"""
    
    @staticmethod
    def create_connector(platform_type: PlatformType, credentials: Dict[str, Any]):
        """Create the appropriate API connector based on platform type"""
        
        if platform_type == PlatformType.SHOPIFY:
            shopify_creds = ShopifyCredentials(**credentials)
            return ShopifyConnector(shopify_creds)
        
        elif platform_type == PlatformType.AMAZON:
            amazon_creds = AmazonCredentials(**credentials)
            return AmazonConnector(amazon_creds)
        
        elif platform_type == PlatformType.WOOCOMMERCE:
            woo_creds = WooCommerceCredentials(**credentials)
            return WooCommerceConnector(woo_creds)
        
        else:
            raise APIConnectorError(f"Unsupported platform type: {platform_type}")

class APIDataFetcher:
    """High-level API data fetcher that orchestrates different connectors"""
    
    def __init__(self):
        self.connectors = {}
    
    async def test_connection(self, platform_type: PlatformType, credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """Test connection for any platform"""
        try:
            connector = APIConnectorFactory.create_connector(platform_type, credentials)
            return await connector.test_connection()
        except Exception as e:
            logger.error(f" Connection test failed for {platform_type}: {e}")
            return False, f"Connection test failed: {str(e)}"
    
    async def fetch_all_data(self, platform_type: PlatformType, credentials: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Fetch all available data from a platform INCLUDING ALL MISSING DATA"""
        try:
            connector = APIConnectorFactory.create_connector(platform_type, credentials)
            
            all_data = {}
            
            # Fetch different data types based on platform capabilities
            if hasattr(connector, 'fetch_orders'):
                try:
                    orders = await connector.fetch_orders()  # Now includes line items with SKUs/quantities
                    all_data['orders'] = orders
                    
                    # Count total line items for logging
                    total_line_items = sum(len(order.get('line_items', [])) for order in orders)
                    logger.info(f" ✅ Fetched {len(orders)} orders with {total_line_items} line items from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch orders from {platform_type}: {e}")
                    all_data['orders'] = []
            
            if hasattr(connector, 'fetch_products'):
                try:
                    products = await connector.fetch_products()  # Now enhanced for Amazon
                    all_data['products'] = products
                    logger.info(f"️ ✅ Fetched {len(products)} products from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch products from {platform_type}: {e}")
                    all_data['products'] = []
            
            # ✅ ENHANCED: Fetch ALL Amazon inventory and pricing data
            if hasattr(connector, 'fetch_fba_inventory'):
                try:
                    fba_inventory = await connector.fetch_fba_inventory()
                    all_data['fba_inventory'] = fba_inventory
                    logger.info(f"📦 ✅ Fetched {len(fba_inventory)} FBA inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f"📦 Failed to fetch FBA inventory from {platform_type}: {e}")
                    all_data['fba_inventory'] = []
            
            if hasattr(connector, 'fetch_fba_inbound_shipments'):
                try:
                    fba_inbound = await connector.fetch_fba_inbound_shipments()
                    all_data['fba_inbound_shipments'] = fba_inbound
                    total_inbound_items = sum(len(shipment.get('items', [])) for shipment in fba_inbound)
                    logger.info(f"🚚 ✅ Fetched {len(fba_inbound)} FBA inbound shipments ({total_inbound_items} items) from {platform_type}")
                except Exception as e:
                    logger.warning(f"🚚 Failed to fetch FBA inbound shipments from {platform_type}: {e}")
                    all_data['fba_inbound_shipments'] = []
            
            # ✅ ENHANCED: Extract pricing from orders (better than listings API!)
            if hasattr(connector, 'extract_sku_pricing_from_orders') and all_data.get('orders'):
                try:
                    sku_pricing = await connector.extract_sku_pricing_from_orders(all_data['orders'], days_back=30)
                    all_data['sku_pricing_from_orders'] = sku_pricing
                    if sku_pricing:
                        avg_price = sum(item.get('weighted_average_price', 0) for item in sku_pricing) / len(sku_pricing)
                        total_revenue = sum(item.get('total_revenue', 0) for item in sku_pricing)
                        logger.info(f"💰 ✅ Extracted pricing for {len(sku_pricing)} SKUs from orders (avg: ${avg_price:.2f}, total revenue: ${total_revenue:.2f}) from {platform_type}")
                    else:
                        logger.info(f"💰 No pricing data extracted from orders from {platform_type}")
                except Exception as e:
                    logger.warning(f"💰 Failed to extract pricing from orders from {platform_type}: {e}")
                    all_data['sku_pricing_from_orders'] = []
            
            # Legacy listings pricing (keep for fallback)
            if hasattr(connector, 'fetch_listings_pricing'):
                try:
                    listings_pricing = await connector.fetch_listings_pricing()
                    all_data['listings_pricing'] = listings_pricing
                    logger.info(f"💱 ✅ Fetched {len(listings_pricing)} product listings with pricing from {platform_type}")
                except Exception as e:
                    logger.warning(f"💱 Failed to fetch listings pricing from {platform_type}: {e}")
                    all_data['listings_pricing'] = []
            
            if hasattr(connector, 'fetch_awd_inventory'):
                try:
                    awd_inventory = await connector.fetch_awd_inventory()
                    all_data['awd_inventory'] = awd_inventory
                    logger.info(f"🏭 ✅ Fetched {len(awd_inventory)} AWD inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f"🏭 Failed to fetch AWD inventory from {platform_type}: {e}")
                    all_data['awd_inventory'] = []
            
            if hasattr(connector, 'fetch_awd_inbound_shipments'):
                try:
                    awd_inbound = await connector.fetch_awd_inbound_shipments()
                    all_data['awd_inbound_shipments'] = awd_inbound
                    total_awd_packages = sum(len(shipment.get('distribution_packages', [])) for shipment in awd_inbound)
                    logger.info(f"🚛 ✅ Fetched {len(awd_inbound)} AWD inbound shipments ({total_awd_packages} packages) from {platform_type}")
                except Exception as e:
                    logger.warning(f"🚛 Failed to fetch AWD inbound shipments from {platform_type}: {e}")
                    all_data['awd_inbound_shipments'] = []
            
            # Legacy incoming inventory (redirects to FBA inbound)
            if hasattr(connector, 'fetch_incoming_inventory'):
                try:
                    incoming_inventory = await connector.fetch_incoming_inventory()
                    all_data['incoming_inventory'] = incoming_inventory
                    logger.info(f"📋 ✅ Fetched {len(incoming_inventory)} incoming inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f"📋 Failed to fetch incoming inventory from {platform_type}: {e}")
                    all_data['incoming_inventory'] = []
            
            if hasattr(connector, 'fetch_customers'):
                try:
                    customers = await connector.fetch_customers()
                    all_data['customers'] = customers
                    logger.info(f" Fetched {len(customers)} customers from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch customers from {platform_type}: {e}")
                    all_data['customers'] = []
            
            # Log summary of what was fetched - ENHANCED with all new data types
            summary = []
            for data_type, data_list in all_data.items():
                if data_list:
                    if data_type == 'orders':
                        total_line_items = sum(len(order.get('line_items', [])) for order in data_list)
                        summary.append(f"{len(data_list)} {data_type} ({total_line_items} line items)")
                    elif data_type == 'fba_inbound_shipments':
                        total_items = sum(len(shipment.get('items', [])) for shipment in data_list)
                        summary.append(f"{len(data_list)} FBA inbound ({total_items} items)")
                    elif data_type == 'awd_inbound_shipments':
                        total_packages = sum(len(shipment.get('distribution_packages', [])) for shipment in data_list)
                        summary.append(f"{len(data_list)} AWD inbound ({total_packages} packages)")
                    elif data_type == 'fba_inventory':
                        total_units = sum(item.get('total_quantity', 0) for item in data_list)
                        summary.append(f"{len(data_list)} FBA inventory SKUs ({total_units} units)")
                    elif data_type == 'awd_inventory':
                        total_units = sum(item.get('quantity', 0) for item in data_list)
                        summary.append(f"{len(data_list)} AWD inventory SKUs ({total_units} units)")
                    elif data_type == 'sku_pricing_from_orders':
                        avg_price = sum(item.get('weighted_average_price', 0) for item in data_list) / len(data_list) if data_list else 0
                        total_revenue = sum(item.get('total_revenue', 0) for item in data_list)
                        summary.append(f"{len(data_list)} SKU prices from orders (avg ${avg_price:.2f}, revenue ${total_revenue:.2f})")
                    elif data_type == 'listings_pricing':
                        avg_price = sum(item.get('listing_price', 0) for item in data_list) / len(data_list) if data_list else 0
                        summary.append(f"{len(data_list)} listings (avg ${avg_price:.2f})")
                    else:
                        summary.append(f"{len(data_list)} {data_type}")
            
            logger.info(f" 🎉 ENHANCED API FETCH COMPLETE for {platform_type}: {', '.join(summary)}")
            
            return all_data
            
        except Exception as e:
            logger.error(f" Failed to fetch data from {platform_type}: {e}")
            raise APIConnectorError(f"Data fetch failed: {str(e)}")

# Create global instance
api_data_fetcher = APIDataFetcher() 