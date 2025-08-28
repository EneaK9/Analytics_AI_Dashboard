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
        self.base_url = f"https://{credentials.shop_domain}/admin/api/2023-10"
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

    async def fetch_inventory_levels(self, inventory_item_ids: List[str] = None) -> List[Dict]:
        """Fetch inventory levels (actual stock on hand) by location and inventory item IDs
        
        Shopify requires either inventory_item_ids OR location_ids parameter - can't fetch all without filter.
        Enhanced to always include SKU data by cross-referencing with products.
        """
        try:
            # First, get inventory item ID to SKU mapping from products
            logger.info("📦 Getting SKU mapping from products for inventory levels...")
            sku_mapping = await self._get_inventory_item_sku_mapping()
            
            all_inventory = []
            
            async with aiohttp.ClientSession() as session:
                if inventory_item_ids:
                    # Method 1: Fetch by specific inventory item IDs
                    logger.info(f"📦 Fetching inventory levels for {len(inventory_item_ids)} specific items...")
                    
                    # Shopify allows up to 50 inventory_item_ids per request
                    batch_size = 50
                    for i in range(0, len(inventory_item_ids), batch_size):
                        batch_ids = inventory_item_ids[i:i+batch_size]
                        
                        params = {
                            "inventory_item_ids": ",".join(map(str, batch_ids)),
                            "limit": 50  # Safer limit for inventory API
                        }
                        
                        async with session.get(
                            f"{self.base_url}/inventory_levels.json",
                            headers=self.headers,
                            params=params
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                inventory_levels = data.get('inventory_levels', [])
                                
                                for level in inventory_levels:
                                    inventory_item_id = str(level.get('inventory_item_id'))
                                    sku_info = sku_mapping.get(inventory_item_id, {})
                                    
                                    all_inventory.append({
                                        'inventory_item_id': level.get('inventory_item_id'),
                                        'location_id': level.get('location_id'),
                                        'available': level.get('available', 0),
                                        'updated_at': level.get('updated_at'),
                                        'inventory_level_id': f"{level.get('inventory_item_id')}_{level.get('location_id')}",
                                        'sku': sku_info.get('sku'),  # ⭐ SKU from products mapping
                                        'product_title': sku_info.get('product_title'),  # ⭐ Product name
                                        'variant_title': sku_info.get('variant_title'),  # ⭐ Variant name
                                        'price': sku_info.get('price'),  # ⭐ Current price
                                        'barcode': sku_info.get('barcode'),  # ⭐ Barcode
                                        'platform': 'shopify',
                                        'data_source': 'inventory_api_enhanced',
                                        'raw_data': level
                                    })
                                
                                logger.info(f"📦 Fetched {len(inventory_levels)} inventory levels for batch {i//batch_size + 1}")
                            
                            elif response.status == 422:
                                error_text = await response.text()
                                logger.warning(f"📦 422 Error with inventory_item_ids: {error_text[:200]}")
                                logger.info("📦 Falling back to location-based method...")
                                return await self._fetch_inventory_via_locations_enhanced(sku_mapping)
                            
                            elif response.status == 429:
                                logger.warning("📦 Rate limited, waiting 1 second...")
                                await asyncio.sleep(1)
                                continue
                            else:
                                error_text = await response.text()
                                logger.warning(f"📦 API error {response.status}: {error_text[:200]}")
                                break
                    
                    logger.info(f"📦 ✅ Fetched {len(all_inventory)} inventory levels via inventory_item_ids with SKU data")
                    return all_inventory
                
                else:
                    # Method 2: Since no specific inventory items requested, fetch by locations
                    # This is the CORRECT way - Shopify requires either inventory_item_ids OR location_ids
                    logger.info("📦 No specific inventory items requested, fetching by locations...")
                    return await self._fetch_inventory_via_locations_enhanced(sku_mapping)
                        
        except Exception as e:
            logger.error(f"📦 Failed to fetch Shopify inventory levels: {e}")
            # Fallback to location-based method
            logger.info("📦 Trying location-based fallback...")
            sku_mapping = await self._get_inventory_item_sku_mapping()
            return await self._fetch_inventory_via_locations_enhanced(sku_mapping)

    async def _get_inventory_item_sku_mapping(self) -> Dict[str, Dict]:
        """Create a mapping of inventory_item_id to SKU and product info"""
        try:
            logger.info("📦 Building inventory_item_id → SKU mapping...")
            products = await self.fetch_products()
            
            mapping = {}
            for product in products:
                product_title = product.get('title')
                for variant in product.get('variants', []):
                    inventory_item_id = str(variant.get('inventory_item_id'))
                    if inventory_item_id and inventory_item_id != 'None':
                        mapping[inventory_item_id] = {
                            'sku': variant.get('sku'),
                            'product_title': product_title,
                            'variant_title': variant.get('title'),
                            'price': variant.get('price'),
                            'barcode': variant.get('barcode'),
                            'variant_id': variant.get('variant_id'),
                            'product_id': product.get('product_id')
                        }
            
            logger.info(f"📦 Created mapping for {len(mapping)} inventory items")
            return mapping
            
        except Exception as e:
            logger.warning(f"📦 Failed to create SKU mapping: {e}")
            return {}

    async def _fetch_inventory_via_locations(self) -> List[Dict]:
        """Alternative method: Get inventory by fetching locations first, then inventory per location"""
        # Get SKU mapping first
        sku_mapping = await self._get_inventory_item_sku_mapping()
        return await self._fetch_inventory_via_locations_enhanced(sku_mapping)

    async def _fetch_inventory_via_locations_enhanced(self, sku_mapping: Dict[str, Dict]) -> List[Dict]:
        """Enhanced method: Get inventory by locations with SKU data included"""
        try:
            all_inventory = []
            
            async with aiohttp.ClientSession() as session:
                # First get all locations
                async with session.get(
                    f"{self.base_url}/locations.json",
                    headers=self.headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        locations = data.get('locations', [])
                        
                        logger.info(f"📦 Found {len(locations)} locations, getting inventory for each...")
                        
                        # For each location, try to get inventory levels
                        for location in locations:
                            location_id = location.get('id')
                            location_name = location.get('name', 'Unknown')
                            
                            try:
                                # Try to get inventory levels for this location
                                # Note: Use location_ids (plural) with correct limit
                                params = {
                                    "location_ids": str(location_id),  # Shopify expects location_ids parameter
                                    "limit": 50  # Use safer limit for inventory API
                                }
                                
                                async with session.get(
                                    f"{self.base_url}/inventory_levels.json",
                                    headers=self.headers,
                                    params=params
                                ) as inv_response:
                                    
                                    if inv_response.status == 200:
                                        inv_data = await inv_response.json()
                                        inventory_levels = inv_data.get('inventory_levels', [])
                                        
                                        for level in inventory_levels:
                                            inventory_item_id = str(level.get('inventory_item_id'))
                                            sku_info = sku_mapping.get(inventory_item_id, {})
                                            
                                            all_inventory.append({
                                                'inventory_item_id': level.get('inventory_item_id'),
                                                'location_id': location_id,
                                                'location_name': location_name,
                                                'available': level.get('available', 0),
                                                'updated_at': level.get('updated_at'),
                                                'inventory_level_id': f"{level.get('inventory_item_id')}_{location_id}",
                                                'sku': sku_info.get('sku'),  # ⭐ SKU from products mapping
                                                'product_title': sku_info.get('product_title'),  # ⭐ Product name
                                                'variant_title': sku_info.get('variant_title'),  # ⭐ Variant name
                                                'price': sku_info.get('price'),  # ⭐ Current price
                                                'barcode': sku_info.get('barcode'),  # ⭐ Barcode
                                                'platform': 'shopify',
                                                'data_source': 'locations_api_enhanced',
                                                'raw_data': level
                                            })
                                        
                                        logger.info(f"📦 Found {len(inventory_levels)} items at location '{location_name}' with SKU data")
                                    
                                    elif inv_response.status == 422:
                                        # Get detailed error message for debugging
                                        error_text = await inv_response.text()
                                        logger.warning(f"📦 422 Error for location '{location_name}' (ID: {location_id}): {error_text[:200]}")
                                        logger.info(f"📦 Parameters used: {params}")
                                        continue
                                    else:
                                        error_text = await inv_response.text()
                                        logger.warning(f"📦 Failed to get inventory for location '{location_name}': {error_text[:100]}")
                                
                            except Exception as loc_e:
                                logger.warning(f"📦 Error getting inventory for location '{location_name}': {loc_e}")
                                continue
                    
                    else:
                        # If we can't even get locations, try to extract from product variants
                        logger.warning("📦 Cannot access locations API, extracting inventory from product variants...")
                        return await self._extract_inventory_from_products_enhanced(sku_mapping)
                
                if all_inventory:
                    logger.info(f"📦 ✅ Enhanced method found {len(all_inventory)} inventory records with SKU data")
                else:
                    logger.warning("📦 No inventory data found via locations, trying product variants...")
                    return await self._extract_inventory_from_products_enhanced(sku_mapping)
                
                return all_inventory
                        
        except Exception as e:
            logger.warning(f"📦 Enhanced inventory method failed: {e}")
            return await self._extract_inventory_from_products_enhanced(sku_mapping)

    async def _extract_inventory_from_products(self) -> List[Dict]:
        """Last resort: Extract inventory quantities from product variants"""
        # Get SKU mapping (though it's redundant here since we're getting from products)
        sku_mapping = await self._get_inventory_item_sku_mapping()
        return await self._extract_inventory_from_products_enhanced(sku_mapping)

    async def _extract_inventory_from_products_enhanced(self, sku_mapping: Dict[str, Dict]) -> List[Dict]:
        """Enhanced: Extract inventory quantities from product variants with full data"""
        try:
            logger.info("📦 Extracting inventory from product variants as fallback (enhanced)...")
            
            products = await self.fetch_products()
            inventory_data = []
            
            for product in products:
                product_title = product.get('title')
                for variant in product.get('variants', []):
                    if variant.get('inventory_quantity') is not None and variant.get('inventory_item_id'):
                        inventory_data.append({
                            'inventory_item_id': variant.get('inventory_item_id'),
                            'location_id': 'default',  # Default location since we don't have specific location data
                            'location_name': 'Default Location',
                            'available': variant.get('inventory_quantity', 0),
                            'updated_at': variant.get('updated_at'),
                            'inventory_level_id': f"{variant.get('inventory_item_id')}_default",
                            'sku': variant.get('sku'),  # ⭐ SKU directly from variant
                            'product_title': product_title,  # ⭐ Product name
                            'variant_title': variant.get('title'),  # ⭐ Variant name
                            'price': variant.get('price'),  # ⭐ Current price
                            'barcode': variant.get('barcode'),  # ⭐ Barcode
                            'platform': 'shopify',
                            'data_source': 'product_variant_enhanced',  # Mark the data source
                            'raw_data': variant
                        })
            
            logger.info(f"📦 ✅ Extracted {len(inventory_data)} inventory records from product variants with full SKU data")
            return inventory_data
            
        except Exception as e:
            logger.error(f"📦 Failed to extract inventory from products: {e}")
            return []

    async def fetch_inventory_items(self, inventory_item_ids: List[str] = None) -> List[Dict]:
        """Fetch inventory items metadata (cost, country of origin, tracking status)"""
        try:
            all_items = []
            
            async with aiohttp.ClientSession() as session:
                if inventory_item_ids:
                    # Fetch specific inventory items by ID
                    for item_id in inventory_item_ids:
                        async with session.get(
                            f"{self.base_url}/inventory_items/{item_id}.json",
                            headers=self.headers
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                item = data.get('inventory_item', {})
                                
                                all_items.append({
                                    'inventory_item_id': item.get('id'),
                                    'sku': item.get('sku'),
                                    'created_at': item.get('created_at'),
                                    'updated_at': item.get('updated_at'),
                                    'requires_shipping': item.get('requires_shipping'),
                                    'cost': float(item.get('cost', 0)) if item.get('cost') else None,
                                    'country_code_of_origin': item.get('country_code_of_origin'),
                                    'province_code_of_origin': item.get('province_code_of_origin'),
                                    'harmonized_system_code': item.get('harmonized_system_code'),
                                    'tracked': item.get('tracked', False),  # Critical tracking flag
                                    'country_harmonized_system_codes': item.get('country_harmonized_system_codes', []),
                                    'platform': 'shopify',
                                    'raw_data': item
                                })
                                
                                logger.info(f"🏷️ Fetched inventory item {item_id}")
                            
                            elif response.status == 429:
                                logger.warning("🏷️ Rate limited by Shopify Inventory Items API, waiting 1 second...")
                                await asyncio.sleep(1)
                                continue
                            else:
                                error_text = await response.text()
                                logger.warning(f"🏷️ Shopify Inventory Item API error {response.status} for item {item_id}: {error_text[:200]}")
                
                else:
                    # If no specific IDs provided, we need to get inventory items from products first
                    logger.info("🏷️ No specific inventory item IDs provided, fetching from product variants...")
                    products = await self.fetch_products()
                    inventory_item_ids_from_products = []
                    
                    for product in products:
                        for variant in product.get('variants', []):
                            if variant.get('inventory_item_id'):
                                inventory_item_ids_from_products.append(str(variant['inventory_item_id']))
                    
                    # Remove duplicates and fetch inventory items
                    unique_ids = list(set(inventory_item_ids_from_products))
                    logger.info(f"🏷️ Found {len(unique_ids)} unique inventory item IDs from products")
                    
                    return await self.fetch_inventory_items(unique_ids)
                
                logger.info(f"🏷️ ✅ Fetched ALL {len(all_items)} Shopify inventory items")
                return all_items
                        
        except Exception as e:
            logger.error(f"🏷️ Failed to fetch Shopify inventory items: {e}")
            raise APIConnectorError(f"Shopify inventory items fetch failed: {str(e)}")

    async def fetch_fulfillment_orders(self, status: str = None) -> List[Dict]:
        """Fetch fulfillment orders to track work in progress and incoming stock"""
        try:
            all_fulfillment_orders = []
            page_info = None
            
            async with aiohttp.ClientSession() as session:
                while True:
                    params = {"limit": 50}  # Shopify default for fulfillment orders
                    
                    if page_info:
                        params["page_info"] = page_info
                    
                    if status:
                        params["status"] = status  # e.g., 'open', 'in_progress', 'cancelled', 'incomplete', 'closed'
                    
                    async with session.get(
                        f"{self.base_url}/fulfillment_orders.json",
                        headers=self.headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            fulfillment_orders = data.get('fulfillment_orders', [])
                            
                            page_fulfillments = []
                            for fulfillment_order in fulfillment_orders:
                                # Process line items in fulfillment order
                                line_items = []
                                for item in fulfillment_order.get('line_items', []):
                                    line_items.append({
                                        'line_item_id': item.get('id'),
                                        'variant_id': item.get('variant_id'),
                                        'product_id': item.get('product_id'),
                                        'inventory_item_id': item.get('inventory_item_id'),
                                        'quantity': item.get('quantity', 0),
                                        'fulfillable_quantity': item.get('fulfillable_quantity', 0),
                                        'sku': item.get('sku'),
                                        'title': item.get('title'),
                                        'vendor': item.get('vendor'),
                                        'properties': item.get('properties', [])
                                    })
                                
                                page_fulfillments.append({
                                    'fulfillment_order_id': fulfillment_order.get('id'),
                                    'shop_id': fulfillment_order.get('shop_id'),
                                    'order_id': fulfillment_order.get('order_id'),
                                    'assigned_location_id': fulfillment_order.get('assigned_location_id'),
                                    'request_status': fulfillment_order.get('request_status'),
                                    'status': fulfillment_order.get('status'),
                                    'supported_actions': fulfillment_order.get('supported_actions', []),
                                    'destination': fulfillment_order.get('destination', {}),
                                    'origin': fulfillment_order.get('origin', {}),
                                    'line_items': line_items,
                                    'outgoing_requests': fulfillment_order.get('outgoing_requests', []),
                                    'fulfillment_holds': fulfillment_order.get('fulfillment_holds', []),
                                    'created_at': fulfillment_order.get('created_at'),
                                    'updated_at': fulfillment_order.get('updated_at'),
                                    'fulfill_at': fulfillment_order.get('fulfill_at'),
                                    'fulfill_by': fulfillment_order.get('fulfill_by'),
                                    'international_duties': fulfillment_order.get('international_duties'),
                                    'delivery_method': fulfillment_order.get('delivery_method'),
                                    'platform': 'shopify',
                                    'raw_data': fulfillment_order
                                })
                            
                            all_fulfillment_orders.extend(page_fulfillments)
                            logger.info(f"🚚 Fetched page with {len(page_fulfillments)} fulfillment orders (Total: {len(all_fulfillment_orders)})")
                            
                            # Check if there are more pages
                            link_header = response.headers.get('Link', '')
                            if 'rel="next"' in link_header:
                                next_match = re.search(r'<[^>]*[?&]page_info=([^&>]+)[^>]*>;\s*rel="next"', link_header)
                                if next_match:
                                    page_info = unquote(next_match.group(1))
                                    logger.info(f"🚚 Next page_info: {page_info[:50]}...")
                                else:
                                    break
                            else:
                                break
                        
                        elif response.status == 429:
                            logger.warning("🚚 Rate limited by Shopify Fulfillment Orders API, waiting 1 second...")
                            await asyncio.sleep(1)
                            continue
                        elif response.status == 404:
                            # Fulfillment Orders API not available (common on basic Shopify plans)
                            logger.info("🚚 Fulfillment Orders API not available (requires Shopify Plus or specific fulfillment setup)")
                            return []
                        else:
                            error_text = await response.text()
                            logger.warning(f"🚚 Shopify Fulfillment Orders API error {response.status}: {error_text[:200]}")
                            break
                
                logger.info(f"🚚 ✅ Fetched ALL {len(all_fulfillment_orders)} Shopify fulfillment orders")
                return all_fulfillment_orders
                        
        except Exception as e:
            logger.error(f"🚚 Failed to fetch Shopify fulfillment orders: {e}")
            # Return empty list instead of raising error to keep other endpoints working
            return []

    async def fetch_incoming_inventory(self, inventory_item_ids: List[str] = None) -> List[Dict]:
        """Fetch incoming inventory (stock en route) via Shopify GraphQL API
        
        Incoming inventory = stock en route from transfers, purchase orders, or apps.
        This is only available via GraphQL API, not REST API.
        """
        try:
            all_incoming = []
            
            # If no specific inventory item IDs provided, get them from products
            if not inventory_item_ids:
                logger.info("🚛 Getting inventory item IDs from products for incoming inventory query...")
                products = await self.fetch_products()
                inventory_item_ids = []
                
                for product in products:
                    for variant in product.get('variants', []):
                        if variant.get('inventory_item_id'):
                            inventory_item_ids.append(str(variant['inventory_item_id']))
                
                # Remove duplicates
                inventory_item_ids = list(set(inventory_item_ids))
                logger.info(f"🚛 Found {len(inventory_item_ids)} unique inventory items to check for incoming stock")
            
            if not inventory_item_ids:
                logger.warning("🚛 No inventory item IDs available for incoming inventory query")
                return []
            
            # GraphQL endpoint (different from REST)
            graphql_url = f"https://{self.credentials.shop_domain}/admin/api/2023-10/graphql.json"
            
            # GraphQL headers
            graphql_headers = {
                "X-Shopify-Access-Token": self.credentials.access_token,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Process in batches to avoid query limits
                batch_size = 20  # GraphQL can handle multiple items per query
                
                for i in range(0, len(inventory_item_ids), batch_size):
                    batch_ids = inventory_item_ids[i:i+batch_size]
                    
                    # Build GraphQL query for multiple inventory items
                    query_parts = []
                    for idx, item_id in enumerate(batch_ids):
                        query_parts.append(f'''
                        item{idx}: inventoryItem(id: "gid://shopify/InventoryItem/{item_id}") {{
                            id
                            sku
                            createdAt
                            updatedAt
                            inventoryLevels(first: 10) {{
                                edges {{
                                    node {{
                                        id
                                        createdAt
                                        updatedAt
                                        location {{
                                            id
                                            name
                                        }}
                                        quantities(names: ["incoming", "available", "committed", "on_hand"]) {{
                                            name
                                            quantity
                                            updatedAt
                                        }}
                                    }}
                                }}
                            }}
                        }}''')
                    
                    # Complete GraphQL query
                    graphql_query = {
                        "query": f'''
                        query GetIncomingInventory {{
                            {chr(10).join(query_parts)}
                        }}
                        '''
                    }
                    
                    try:
                        async with session.post(
                            graphql_url,
                            headers=graphql_headers,
                            json=graphql_query
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                
                                if 'errors' in data:
                                    logger.warning(f"🚛 GraphQL errors: {data['errors']}")
                                    continue
                                
                                # Process the response
                                query_data = data.get('data', {})
                                batch_incoming = []
                                
                                for idx, item_id in enumerate(batch_ids):
                                    item_key = f"item{idx}"
                                    item_data = query_data.get(item_key)
                                    
                                    if not item_data:
                                        continue
                                    
                                    sku = item_data.get('sku')
                                    item_created_at = item_data.get('createdAt')
                                    item_updated_at = item_data.get('updatedAt')
                                    inventory_levels = item_data.get('inventoryLevels', {}).get('edges', [])
                                    
                                    for level_edge in inventory_levels:
                                        level = level_edge.get('node', {})
                                        location = level.get('location', {})
                                        quantities = level.get('quantities', [])
                                        level_created_at = level.get('createdAt')
                                        level_updated_at = level.get('updatedAt')
                                        
                                        # Collect all inventory states for this location
                                        inventory_states = {}
                                        latest_update = None
                                        
                                        for quantity_info in quantities:
                                            state_name = quantity_info.get('name')
                                            state_qty = quantity_info.get('quantity', 0)
                                            state_updated = quantity_info.get('updatedAt')
                                            
                                            inventory_states[state_name] = {
                                                'quantity': state_qty,
                                                'updated_at': state_updated
                                            }
                                            
                                            # Track the most recent update
                                            if state_updated and (not latest_update or state_updated > latest_update):
                                                latest_update = state_updated
                                        
                                        # Only include if there's incoming inventory
                                        incoming_info = inventory_states.get('incoming', {})
                                        incoming_qty = incoming_info.get('quantity', 0)
                                        
                                        if incoming_qty > 0:  # Only include items with incoming stock
                                            batch_incoming.append({
                                                'inventory_item_id': item_id,
                                                'sku': sku,
                                                'location_id': location.get('id', '').replace('gid://shopify/Location/', ''),
                                                'location_name': location.get('name'),
                                                'incoming_quantity': incoming_qty,
                                                'incoming_updated_at': incoming_info.get('updated_at'),  # When incoming was last updated
                                                'available_quantity': inventory_states.get('available', {}).get('quantity', 0),
                                                'committed_quantity': inventory_states.get('committed', {}).get('quantity', 0),
                                                'on_hand_quantity': inventory_states.get('on_hand', {}).get('quantity', 0),
                                                'inventory_level_id': level.get('id'),
                                                'level_created_at': level_created_at,    # ⭐ When inventory level was created
                                                'level_updated_at': level_updated_at,    # ⭐ When inventory level was last updated
                                                'item_created_at': item_created_at,      # ⭐ When inventory item was created
                                                'item_updated_at': item_updated_at,      # ⭐ When inventory item was last updated
                                                'latest_activity': latest_update,        # ⭐ Most recent activity timestamp
                                                'platform': 'shopify',
                                                'data_source': 'graphql_incoming_enhanced',
                                                'all_inventory_states': inventory_states,  # Complete inventory breakdown
                                                'raw_data': level
                                            })
                                
                                all_incoming.extend(batch_incoming)
                                logger.info(f"🚛 Batch {i//batch_size + 1}: Found {len(batch_incoming)} items with incoming inventory")
                            
                            elif response.status == 429:
                                logger.warning("🚛 Rate limited by Shopify GraphQL API, waiting 2 seconds...")
                                await asyncio.sleep(2)
                                continue
                            
                            else:
                                error_text = await response.text()
                                logger.warning(f"🚛 GraphQL API error {response.status}: {error_text[:200]}")
                                break
                    
                    except Exception as batch_e:
                        logger.warning(f"🚛 Error processing batch {i//batch_size + 1}: {batch_e}")
                        continue
                    
                    # Small delay between batches to respect rate limits
                    if i + batch_size < len(inventory_item_ids):
                        await asyncio.sleep(0.5)
                
                logger.info(f"🚛 ✅ Found {len(all_incoming)} items with incoming inventory across all locations")
                return all_incoming
                        
        except Exception as e:
            logger.error(f"🚛 Failed to fetch Shopify incoming inventory: {e}")
            return []

class AmazonConnector:
    """Amazon SP-API Connector - Real-time marketplace data fetching"""
    
    def __init__(self, credentials: AmazonCredentials):
        self.credentials = credentials
        self.base_url = "https://sellingpartnerapi-na.amazon.com"  # North America endpoint
        self.access_token = None
        self.token_expires_at = None
    
    async def _get_access_token(self) -> str:
        """Get or refresh Amazon SP-API access token"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            logger.info(f"[CACHED_TOKEN] Using cached token (expires: {self.token_expires_at})")
            return self.access_token
        elif self.access_token and self.token_expires_at:
            logger.info(f"[EXPIRED_TOKEN] Cached token expired at {self.token_expires_at}, refreshing...")
        else:
            logger.info("[NEW_TOKEN] No cached token, requesting new one...")
        
        try:
            # Amazon SP-API OAuth token exchange
            token_url = "https://api.amazon.com/auth/o2/token"
            
            # ✅ DEBUG: Log token request details (without sensitive data)
            logger.info(f"[TOKEN_REQUEST] Requesting new Amazon token...")
            logger.info(f"[TOKEN_REQUEST] URL: {token_url}")
            logger.info(f"[TOKEN_REQUEST] Client ID: {self.credentials.access_key_id}")
            logger.info(f"[TOKEN_REQUEST] Refresh token length: {len(self.credentials.refresh_token)}")
            
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
                        # ✅ DEBUG: Get detailed error info
                        error_text = await response.text()
                        logger.error(f"[TOKEN_ERROR] Amazon token request failed:")
                        logger.error(f"[TOKEN_ERROR] Status: {response.status}")
                        logger.error(f"[TOKEN_ERROR] Response: {error_text}")
                        logger.error(f"[TOKEN_ERROR] URL: {token_url}")
                        logger.error(f"[TOKEN_ERROR] Client ID: {self.credentials.access_key_id}")
                        raise APIConnectorError(f"Failed to get Amazon access token: HTTP {response.status} - {error_text}")
                        
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
    
    def _safe_get(self, data: dict, key: str, default=None, convert_type=None):
        """Safely get value from dictionary with optional type conversion"""
        try:
            value = data.get(key, default)
            if convert_type and value is not None:
                return convert_type(value)
            return value
        except (ValueError, TypeError):
            return default
    
    def _safe_nested_get(self, data: dict, keys: list, default=None):
        """Safely get nested value from dictionary"""
        try:
            current = data
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    async def fetch_inventory(self) -> List[Dict]:
        """Fetch FBA inventory summaries from Amazon SP-API - Legacy method redirects to fetch_fba_inventory"""
        return await self.fetch_fba_inventory()
    
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
                # ✅ ARTICLE PATTERN: Add iteration counter and safety limit
                iteration = 0
                max_iterations = 20  # Safety limit to prevent infinite loops
                
                while iteration < max_iterations:
                    logger.info(f"📦 API Call #{iteration + 1}")
                    
                    # ✅ ENHANCED: Add details=true to get reserved quantities and detailed breakdown
                    params = {
                        'granularityType': 'Marketplace',
                        'granularityId': self.credentials.marketplace_ids[0],  # Use first marketplace
                        'marketplaceIds': ','.join(self.credentials.marketplace_ids),
                        'details': 'true'  # ✅ This should give us reserved quantities and detailed breakdown
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
                            
                            # ✅ DEBUG: Log the raw API response structure
                            logger.info(f"📦 RAW API RESPONSE SAMPLE:")
                            if inventory_summaries:
                                sample = inventory_summaries[0]
                                logger.info(f"📦 Sample inventory item structure: {json.dumps(sample, indent=2)}")
                                
                                # Check what fields actually exist
                                logger.info(f"📦 Available fields in summary: {list(sample.keys())}")
                                if 'inventoryDetails' in sample:
                                    logger.info(f"📦 Available fields in inventoryDetails: {list(sample['inventoryDetails'].keys())}")
                                else:
                                    logger.warning("📦 No 'inventoryDetails' field found in response!")
                            
                            # Transform to standard format with ALL FBA inventory details
                            page_inventory = []
                            for summary in inventory_summaries:
                                # ✅ FIXED: Extract from the correct nested structure (inventoryDetails)
                                total_qty = self._safe_get(summary, 'totalQuantity', 0, int)
                                inventory_details = summary.get('inventoryDetails', {})
                                
                                # ✅ CORRECT: Get from inventoryDetails (details=true provides this)
                                fulfillable_qty = self._safe_get(inventory_details, 'fulfillableQuantity', 0, int)
                                
                                # ✅ CORRECT: Inbound quantities from inventoryDetails
                                inbound_working_qty = self._safe_get(inventory_details, 'inboundWorkingQuantity', 0, int)
                                inbound_shipped_qty = self._safe_get(inventory_details, 'inboundShippedQuantity', 0, int)
                                inbound_receiving_qty = self._safe_get(inventory_details, 'inboundReceivingQuantity', 0, int)
                                
                                # ✅ CORRECT: Reserved quantities from nested structure
                                reserved_qty_obj = inventory_details.get('reservedQuantity', {})
                                reserved_total = self._safe_get(reserved_qty_obj, 'totalReservedQuantity', 0, int)
                                pending_customer_orders = self._safe_get(reserved_qty_obj, 'pendingCustomerOrderQuantity', 0, int)
                                pending_transfers = self._safe_get(reserved_qty_obj, 'pendingTransshipmentQuantity', 0, int)
                                fc_processing = self._safe_get(reserved_qty_obj, 'fcProcessingQuantity', 0, int)
                                
                                # ✅ CORRECT: Unfulfillable from nested structure
                                unfulfillable_qty_obj = inventory_details.get('unfulfillableQuantity', {})
                                unfulfillable_qty = self._safe_get(unfulfillable_qty_obj, 'totalUnfulfillableQuantity', 0, int)
                                
                                # ✅ CORRECT: Researching from nested structure  
                                researching_qty_obj = inventory_details.get('researchingQuantity', {})
                                researching_qty = self._safe_get(researching_qty_obj, 'totalResearchingQuantity', 0, int)
                                
                                page_inventory.append({
                                    'sku': self._safe_get(summary, 'sellerSku'),
                                    'seller_sku': self._safe_get(summary, 'sellerSku'),  # For compatibility
                                    'asin': self._safe_get(summary, 'asin'),
                                    'fnsku': self._safe_get(summary, 'fnSku'),
                                    'condition': self._safe_get(summary, 'condition'),
                                    'marketplace_id': self._safe_get(summary, 'marketplaceId'),
                                    
                                    # ✅ SAFE: Available inventory (ready to ship)
                                    'fulfillable_quantity': fulfillable_qty,
                                    'available_quantity': fulfillable_qty,  # Alias
                                    
                                    # ✅ ENHANCED: Working/Inbound inventory (incoming to warehouses)
                                    'inbound_working_quantity': inbound_working_qty,
                                    'inbound_shipped_quantity': inbound_shipped_qty,
                                    'inbound_receiving_quantity': inbound_receiving_qty,
                                    'total_inbound_quantity': inbound_working_qty + inbound_shipped_qty + inbound_receiving_qty,
                                    
                                    # ✅ ENHANCED: Reserved inventory (detailed breakdown)
                                    'reserved_total': reserved_total,
                                    'total_reserved_quantity': reserved_total,  # Alias
                                    'pending_customer_order_quantity': pending_customer_orders,  # Reserved for orders
                                    'pending_transshipment_quantity': pending_transfers,         # Being transferred
                                    'fc_processing_quantity': fc_processing,                     # Being processed
                                    'reserved_breakdown': {
                                        'customer_orders': pending_customer_orders,
                                        'transfers': pending_transfers,
                                        'fc_processing': fc_processing,
                                        'total': reserved_total
                                    },
                                    
                                    # ✅ SAFE: Unfulfillable inventory
                                    'unfulfillable_quantity': unfulfillable_qty,
                                    'unsellable_quantity': unfulfillable_qty,  # Alias
                                    
                                    # ✅ SAFE: Research quantity
                                    'researching_quantity': researching_qty,
                                    
                                    # ✅ SAFE: Total quantity calculations
                                    'total_quantity': total_qty,  # Use the actual totalQuantity from Amazon
                                    
                                    # Timestamps
                                    'last_updated_time': self._safe_get(summary, 'lastUpdatedTime'),
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'inventory_type': 'fba_onhand',
                                    'raw_data': summary  # ✅ ALWAYS keep raw data for debugging
                                })
                            
                            all_inventory.extend(page_inventory)
                            logger.info(f"📦 Fetched page with {len(page_inventory)} FBA inventory SKUs (Total: {len(all_inventory)})")
                            
                            # ✅ FIXED: Check for next page exactly like the article
                            if 'pagination' in data and 'nextToken' in data['pagination']:
                                next_token = data['pagination']['nextToken']
                                logger.info(f"📦 ✅ NextToken found: {next_token[:50]}...")
                            else:
                                next_token = None
                                logger.info("📦 No nextToken found - reached end of inventory")
                            
                            # ✅ DEBUG: Log pagination details
                            pagination = data.get('pagination', {})
                            logger.info(f"📦 Pagination object: {pagination}")
                            logger.info(f"📦 Total items fetched so far: {len(all_inventory)}")
                            
                            if not next_token:
                                break
                                
                            # ✅ ARTICLE PATTERN: Increment iteration and add delay
                            iteration += 1
                            await asyncio.sleep(1)  # Match article's 1 second delay
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry (don't increment iteration for retries)
                            logger.warning("📦 Rate limited by Amazon FBA Inventory API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"📦 Amazon FBA Inventory API error {response.status}: {error_text[:200]}")
                            # Inventory API might not be accessible for all sellers
                            logger.info("📦 FBA Inventory API might not be available for this seller account")
                            break
                
                # ✅ SAFETY: Check if we hit max iterations
                if iteration >= max_iterations:
                    logger.warning(f"📦 Reached maximum iterations ({max_iterations}) - stopping pagination")
                
                logger.info(f"📦 ✅ Fetched {len(all_inventory)} FBA inventory items with quantities")
                
                # ✅ IMPORTANT: Explain why only 50 SKUs and zero quantities
                if len(all_inventory) == 50:
                    logger.warning("⚠️  EXACTLY 50 SKUs FOUND - This suggests pagination may have stopped early")
                    logger.info("📦 Common reasons for limited SKUs:")
                    logger.info("   1. Amazon FBA API pagination not returning nextToken")
                    logger.info("   2. You have exactly 50 FBA-enrolled products")
                    logger.info("   3. Some products might be FBM (Fulfilled by Merchant) not FBA")
                    logger.info("   4. Products not yet enrolled in FBA program")
                
                zero_qty_count = sum(1 for item in all_inventory if item.get('fulfillable_quantity', 0) == 0)
                total_units = sum(item.get('fulfillable_quantity', 0) for item in all_inventory)
                
                if zero_qty_count == len(all_inventory):
                    logger.warning("⚠️  ALL INVENTORY QUANTITIES ARE ZERO")
                    logger.info("📦 This means no physical inventory has been shipped to Amazon FBA warehouses")
                else:
                    logger.info(f"✅ SUCCESS: Found {total_units} total units across {len(all_inventory) - zero_qty_count} SKUs with inventory!")
                    logger.info(f"📦 {zero_qty_count} SKUs have zero inventory (normal for new/out-of-stock products)")
                
                return all_inventory
                        
        except Exception as e:
            logger.warning(f"📦 Failed to fetch FBA inventory (this is normal if FBA not enabled): {e}")
            return []  # Return empty list instead of failing
    
    async def discover_all_skus_from_orders(self, days_back: int = 365) -> set:
        """Discover ALL your SKUs by analyzing order history (reveals more than just FBA inventory)"""
        try:
            logger.info(f"🔍 Discovering ALL your SKUs from order history (last {days_back} days)...")
            
            # Fetch recent orders to find ALL SKUs you've sold
            orders = await self.fetch_orders(days_back=days_back)
            
            all_skus = set()
            all_asins = set()
            
            for order in orders:
                for item in order.get('line_items', []):
                    sku = item.get('sku') or item.get('seller_sku')
                    asin = item.get('asin')
                    
                    if sku:
                        all_skus.add(sku)
                    if asin:
                        all_asins.add(asin)
            
            logger.info(f"🔍 Found {len(all_skus)} unique SKUs and {len(all_asins)} unique ASINs in order history")
            logger.info(f"🔍 Sample SKUs from orders: {list(all_skus)[:10]}")
            
            return all_skus
            
        except Exception as e:
            logger.warning(f"🔍 Failed to discover SKUs from orders: {e}")
            return set()
    
    async def fetch_inbound_shipments(self) -> List[Dict]:
        """Fetch inbound shipments (inventory coming to Amazon warehouses)"""
        try:
            logger.info("📦 Fetching inbound shipments (inventory coming to warehouses)...")
            
            access_token = await self._get_access_token()
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            all_shipments = []
            
            async with aiohttp.ClientSession() as session:
                # First get list of shipments
                params = {
                    'queryType': 'DATE_RANGE',
                    'marketplaceId': self.credentials.marketplace_ids[0],
                    'lastUpdatedAfter': (datetime.now() - timedelta(days=90)).isoformat(),  # Last 90 days
                    'lastUpdatedBefore': datetime.now().isoformat()
                }
                
                async with session.get(
                    f"{self.base_url}/fba/inbound/v0/shipments",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        payload = data.get('payload', {})
                        shipment_data = payload.get('ShipmentData', [])
                        
                        logger.info(f"📦 Found {len(shipment_data)} inbound shipments")
                        
                        # Get details for each shipment
                        for shipment in shipment_data:
                            shipment_id = shipment.get('ShipmentId')
                            if shipment_id:
                                try:
                                    # Get detailed shipment info
                                    detail_params = {'skuQuantities': 'SHOW'}
                                    async with session.get(
                                        f"{self.base_url}/fba/inbound/v0/shipments/{shipment_id}",
                                        headers=headers,
                                        params=detail_params
                                    ) as detail_response:
                                        
                                        if detail_response.status == 200:
                                            detail_data = await detail_response.json()
                                            shipment_detail = detail_data.get('payload', {})
                                            
                                            # Extract SKU quantities
                                            items = shipment_detail.get('Items', [])
                                            
                                            shipment_info = {
                                                'shipment_id': shipment_id,
                                                'shipment_name': shipment.get('ShipmentName'),
                                                'destination_fulfillment_center': shipment.get('DestinationFulfillmentCenterId'),
                                                'shipment_status': shipment.get('ShipmentStatus'),
                                                'label_prep_preference': shipment.get('LabelPrepPreference'),
                                                'are_cases_required': shipment.get('AreCasesRequired'),
                                                'created_date': shipment.get('CreatedDate'),
                                                'last_updated_date': shipment.get('LastUpdatedDate'),
                                                'items': []
                                            }
                                            
                                            for item in items:
                                                item_info = {
                                                    'sku': item.get('SellerSKU'),
                                                    'fnsku': item.get('FulfillmentNetworkSKU'),
                                                    'quantity_shipped': item.get('QuantityShipped', 0),
                                                    'quantity_received': item.get('QuantityReceived', 0),
                                                    'quantity_in_case': item.get('QuantityInCase', 0),
                                                    'prep_instructions': item.get('PrepDetailsList', [])
                                                }
                                                shipment_info['items'].append(item_info)
                                            
                                            all_shipments.append(shipment_info)
                                            
                                        await asyncio.sleep(0.5)  # Rate limiting
                                        
                                except Exception as e:
                                    logger.warning(f"Failed to get details for shipment {shipment_id}: {e}")
                                    continue
                        
                        logger.info(f"📦 ✅ Fetched details for {len(all_shipments)} inbound shipments")
                        return all_shipments
                        
                    else:
                        logger.warning(f"📦 Failed to fetch inbound shipments: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.warning(f"📦 Failed to fetch inbound shipments: {e}")
            return []
    
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
                            
                            # ✅ ARTICLE PATTERN: Process orders with progress tracking
                            logger.info(f"🛒 Processing {len(orders)} orders to fetch SKU details...")
                            
                            # Transform to standard format INCLUDING ALL AMAZON ORDER FIELDS
                            page_orders = []
                            for order_index, order in enumerate(orders):
                                # ✅ Show progress every 10 orders
                                if order_index > 0 and order_index % 10 == 0:
                                    logger.info(f"🛒 Processed {order_index}/{len(orders)} orders in this batch...")
                                    # ✅ Add extra delay every 10 orders to be extra safe
                                    await asyncio.sleep(2.0)
                                # Amazon order structure
                                order_total = order.get('OrderTotal', {})
                                order_id = order.get('AmazonOrderId')
                                
                                # ✅ ARTICLE PATTERN: Add delay BEFORE fetching order items
                                await asyncio.sleep(0.5)  # Half second delay before each order items call
                                
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
                                
                            # ✅ ARTICLE PATTERN: Much more conservative delays for orders
                            await asyncio.sleep(1.0)  # 1 request per second (much safer)
                        
                        elif response.status == 429:
                            # Rate limited - wait much longer like article suggests
                            logger.warning(" Rate limited by Amazon Orders API, waiting 30 seconds...")
                            await asyncio.sleep(30)  # Longer wait for orders API
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
                    # ✅ ARTICLE PATTERN: Much longer wait for order items rate limiting
                    logger.warning(f" Rate limited when fetching order items for {order_id}, waiting 15 seconds...")
                    await asyncio.sleep(15)  # Much longer wait like article suggests
                    return await self._fetch_order_items(session, headers, order_id)  # Retry
                else:
                    logger.warning(f" Failed to fetch order items for {order_id}: HTTP {response.status}")
                    return []  # Return empty list if can't fetch items
                    
        except Exception as e:
            logger.warning(f" Failed to fetch order items for {order_id}: {e}")
            return []  # Return empty list on error
    
    async def fetch_products(self) -> List[Dict]:
        """Fetch YOUR seller products using FBA inventory as the source (contains YOUR actual SKUs)"""
        try:
            # ✅ SOLUTION: Use FBA inventory as the source of YOUR products
            logger.info("📦 Fetching YOUR seller products from FBA inventory...")
            inventory_data = await self.fetch_inventory()
            
            if not inventory_data:
                logger.warning("📦 No FBA inventory found - cannot build product list")
                return []
            
            logger.info(f"📦 Converting {len(inventory_data)} FBA inventory items to product list")
            
            # Convert FBA inventory items to product format
            all_products = []
            
            for inventory_item in inventory_data:
                asin = inventory_item.get('asin')
                seller_sku = inventory_item.get('seller_sku') or inventory_item.get('sku')
                
                if not seller_sku:
                    continue
                    
                # Create product data from inventory item
                product_data = {
                    'asin': asin,
                    'seller_sku': seller_sku,
                    'sku': seller_sku,  # ✅ PRIMARY SKU FIELD
                    'fnsku': inventory_item.get('fnsku'),
                    'title': f"Product {seller_sku}",  # Basic title, can be enhanced later
                    'brand': 'Unknown',
                    'condition': inventory_item.get('condition', 'NewItem'),
                    'marketplace_id': inventory_item.get('marketplace_id'),
                    
                    # ✅ INVENTORY QUANTITIES FROM FBA DATA
                    'quantity': inventory_item.get('fulfillable_quantity', 0),
                    'fulfillable_quantity': inventory_item.get('fulfillable_quantity', 0),
                    'total_quantity': inventory_item.get('total_quantity', 0),
                    'inbound_quantity': inventory_item.get('inbound_working_quantity', 0),
                    'reserved_quantity': inventory_item.get('reserved_total', 0),
                    'unfulfillable_quantity': inventory_item.get('unfulfillable_quantity', 0),
                                    
                                    # METADATA
                    'status': 'Active',
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                    'last_updated': inventory_item.get('last_updated_time'),
                    
                    # Raw inventory data for reference
                    'raw_inventory_data': inventory_item
                }
                
                all_products.append(product_data)
            
            logger.info(f"📦 ✅ Built {len(all_products)} products from YOUR FBA inventory")
            return all_products
                        
        except Exception as e:
            logger.error(f" Failed to fetch Amazon products: {e}")
            raise APIConnectorError(f"Amazon products fetch failed: {str(e)}")

    async def fetch_product_details_from_catalog(self, asins: List[str]) -> List[Dict]:
        """
        Fetch detailed product information from Amazon Catalog API
        Gets color, size, style, long sleeves, and all product attributes
        """
        logger.info(f"📋 Fetching detailed product info for {len(asins)} ASINs from Catalog API...")
        
        try:
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            all_catalog_data = []
            
            async with aiohttp.ClientSession() as session:
                # Process ASINs in batches (Catalog API supports multiple ASINs)
                batch_size = 20
                for i in range(0, len(asins), batch_size):
                    batch_asins = asins[i:i + batch_size]
                    
                    params = {
                        'identifiers': ','.join(batch_asins),
                        'identifiersType': 'ASIN',
                        'marketplaceIds': ','.join(self.credentials.marketplace_ids),
                        'includedData': 'attributes,dimensions,identifiers,images,productTypes,relationships,salesRanks,summaries'
                    }
                    
                    try:
                        async with session.get(
                            f"{self.base_url}/catalog/2022-04-01/items",
                            headers=headers,
                            params=params
                        ) as response:
                            
                            logger.info(f"📋 Catalog API response: {response.status}")
                            
                            if response.status == 200:
                                data = await response.json()
                                items = data.get('items', [])
                                
                                logger.info(f"📋 Received {len(items)} catalog items")
                                
                                for item in items:
                                    # Extract detailed product information
                                    asin = item.get('asin')
                                    attributes = item.get('attributes', {})
                                    summaries = item.get('summaries', [])
                                    images = item.get('images', [])
                                    
                                    # Parse attributes for color, size, style, etc.
                                    catalog_details = {
                                        'asin': asin,
                                        'platform': 'amazon',
                                        'catalog_data': item,
                                        
                                        # Basic product info
                                        'title': summaries[0].get('itemName') if summaries else None,
                                        'brand': summaries[0].get('brand') if summaries else None,
                                        'manufacturer': summaries[0].get('manufacturer') if summaries else None,
                                        
                                        # Product attributes (color, size, style, etc.)
                                        'color': self._extract_attribute(attributes, ['color', 'Color', 'colour']),
                                        'size': self._extract_attribute(attributes, ['size', 'Size', 'item_size']),
                                        'style': self._extract_attribute(attributes, ['style', 'Style', 'item_style']),
                                        'material': self._extract_attribute(attributes, ['material', 'Material', 'fabric_type']),
                                        'sleeve_type': self._extract_attribute(attributes, ['sleeve_type', 'SleeveType', 'sleeve_length']),
                                        'pattern': self._extract_attribute(attributes, ['pattern', 'Pattern', 'pattern_type']),
                                        'fit_type': self._extract_attribute(attributes, ['fit_type', 'FitType', 'fit']),
                                        'gender': self._extract_attribute(attributes, ['target_gender', 'Gender', 'gender']),
                                        'age_group': self._extract_attribute(attributes, ['target_audience', 'AgeGroup', 'age_group']),
                                        
                                        # Physical characteristics
                                        'item_weight': self._extract_attribute(attributes, ['item_weight', 'Weight', 'package_weight']),
                                        'item_dimensions': self._extract_attribute(attributes, ['item_dimensions', 'Dimensions', 'package_dimensions']),
                                        
                                        # Product type and category
                                        'product_type': item.get('productTypes', [{}])[0].get('displayName') if item.get('productTypes') else None,
                                        'category': self._extract_attribute(attributes, ['item_type_name', 'Category', 'product_category']),
                                        
                                        # Images
                                        'main_image_url': images[0].get('link') if images else None,
                                        'all_images': [img.get('link') for img in images if img.get('link')],
                                        'image_count': len(images),
                                        
                                        # Sales and ranking info
                                        'sales_ranks': item.get('salesRanks', []),
                                        'best_sellers_rank': self._get_best_rank(item.get('salesRanks', [])),
                                        
                                        # All raw attributes for custom analysis
                                        'all_attributes': attributes,
                                        'attribute_keys': list(attributes.keys()) if attributes else [],
                                        
                                        'created_at': datetime.now().isoformat(),
                                        'last_updated': datetime.now().isoformat()
                                    }
                                    
                                    all_catalog_data.append(catalog_details)
                                    
                            elif response.status == 429:
                                logger.warning("📋 Rate limited by Catalog API, waiting...")
                                await asyncio.sleep(5)
                                continue
                            else:
                                error_text = await response.text()
                                logger.warning(f"📋 Catalog API error {response.status}: {error_text[:200]}")
                                
                    except Exception as e:
                        logger.error(f"📋 Error fetching catalog batch: {e}")
                        continue
                    
                    # Small delay between batches
                    await asyncio.sleep(1)
            
            logger.info(f"📋 ✅ Fetched detailed catalog data for {len(all_catalog_data)} products")
            return all_catalog_data
            
        except Exception as e:
            logger.error(f"📋 Failed to fetch catalog details: {e}")
            return []
    
    def _extract_attribute(self, attributes: Dict, possible_keys: List[str]) -> str:
        """Extract attribute value by trying multiple possible key names"""
        for key in possible_keys:
            if key in attributes:
                value = attributes[key]
                if isinstance(value, list) and value:
                    return str(value[0].get('value', '')) if isinstance(value[0], dict) else str(value[0])
                elif isinstance(value, dict):
                    return str(value.get('value', ''))
                else:
                    return str(value)
        return None
    
    def _get_best_rank(self, sales_ranks: List[Dict]) -> int:
        """Get the best (lowest) sales rank across all categories"""
        if not sales_ranks:
            return None
        
        ranks = []
        for rank_data in sales_ranks:
            rank = rank_data.get('rank')
            if rank and isinstance(rank, int):
                ranks.append(rank)
        
        return min(ranks) if ranks else None
    
    async def fetch_incoming_inventory(self) -> List[Dict]:
        """Fetch incoming inventory from Amazon FBA"""
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
                        'marketplaceIds': ','.join(self.credentials.marketplace_ids),
                        'maxResultsPerPage': 50  # FBA Inventory API max
                    }
                    
                    if next_token:
                        params['nextToken'] = next_token
                    
                    async with session.get(
                        f"{self.base_url}/fba/inbound/v0/shipments",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            payload = data.get('payload', {})
                            shipments = payload.get('ShipmentData', [])
                            
                            # Transform to standard format with shipment items
                            page_inventory = []
                            for shipment in shipments:
                                shipment_id = shipment.get('ShipmentId')
                                
                                # Fetch shipment items for this specific shipment
                                shipment_items = await self._fetch_shipment_items(session, headers, shipment_id)
                                
                                # Create record with shipment items
                                shipment_record = {
                                    'shipment_id': shipment_id,
                                    'shipment_name': shipment.get('ShipmentName'),
                                    'shipment_status': shipment.get('ShipmentStatus'),
                                    'destination_fulfillment_center_id': shipment.get('DestinationFulfillmentCenterId'),
                                    'label_prep_preference': shipment.get('LabelPrepPreference'),
                                    'are_cases_required': shipment.get('AreCasesRequired'),
                                    'confirmed_need_by_date': shipment.get('ConfirmedNeedByDate'),  # ⭐ EXPECTED DATE
                                    'box_contents_source': shipment.get('BoxContentsSource'),
                                    'estimated_box_contents_fee': shipment.get('EstimatedBoxContentsFee'),
                                    'shipment_items': shipment_items,  # ⭐ ITEMS WITH SKUs AND DATES
                                    'created_at': datetime.now().isoformat(),
                                    'platform': 'amazon',
                                    'raw_data': shipment
                                }
                                
                                page_inventory.append(shipment_record)
                            
                            all_inventory.extend(page_inventory)
                            logger.info(f" Fetched page with {len(page_inventory)} Amazon FBA shipments (Total: {len(all_inventory)})")
                            
                            # Check for next page
                            next_token = payload.get('NextToken')
                            if not next_token:
                                break
                                
                            # Add delay to respect rate limits
                            await asyncio.sleep(1)  # Be conservative with FBA API
                        
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning(" Rate limited by Amazon FBA API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f" Amazon FBA API error {response.status}: {error_text[:200]}")
                            # FBA API might not be accessible for all sellers, so don't fail completely
                            logger.info(" FBA Inbound API might not be available for this seller account")
                            break
                
                logger.info(f" ✅ Fetched {len(all_inventory)} Amazon FBA incoming inventory items")
                return all_inventory
                        
        except Exception as e:
            logger.warning(f" Failed to fetch Amazon incoming inventory (this is normal if FBA not enabled): {e}")
            return []  # Return empty list instead of failing
    
    async def _fetch_shipment_items(self, session, headers, shipment_id):
        """Fetch items for a specific Amazon inbound shipment"""
        try:
            params = {
                'MarketplaceId': self.credentials.marketplace_ids[0]
            }
            
            async with session.get(
                f"{self.base_url}/fba/inbound/v0/shipments/{shipment_id}/items",
                headers=headers,
                params=params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    payload = data.get('payload', {})
                    items = payload.get('ItemData', [])
                    
                    # Transform items to include expected dates and SKUs
                    shipment_items = []
                    for item in items:
                        shipment_items.append({
                            'seller_sku': item.get('SellerSKU'),           # ⭐ YOUR SKU
                            'sku': item.get('SellerSKU'),                  # ⭐ UNIFIED SKU FIELD
                            'fulfillment_network_sku': item.get('FulfillmentNetworkSKU'),
                            'quantity_shipped': int(item.get('QuantityShipped', 0)),    # ⭐ QUANTITY INCOMING
                            'quantity_received': int(item.get('QuantityReceived', 0)),
                            'quantity_in_case': int(item.get('QuantityInCase', 0)),
                            'release_date': item.get('ReleaseDate'),       # ⭐ EXPECTED ARRIVAL DATE
                            'prep_details_list': item.get('PrepDetailsList', []),
                            'raw_data': item
                        })
                    
                    return shipment_items
                    
                elif response.status == 404:
                    logger.info(f"📦 No items found for shipment {shipment_id}")
                    return []
                    
                else:
                    response_text = await response.text()
                    logger.warning(f"📦 Failed to fetch shipment items for {shipment_id}: HTTP {response.status} - {response_text[:100]}")
                    return []
                    
        except Exception as e:
            logger.warning(f"📦 Error fetching shipment items for {shipment_id}: {e}")
            return []

    async def fetch_fba_inbound_shipments(self) -> List[Dict]:
        """Fetch detailed FBA inbound shipments with SKU-level item data - Enhanced version"""
        return await self.fetch_incoming_inventory()  # Redirect to existing method for now

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

    async def extract_sku_pricing_from_orders(self, orders_data: List[Dict], days_back: int = 30) -> List[Dict]:
        """Extract pricing data per SKU from order line items - Better than Listings API!"""
        try:
            from collections import defaultdict
            import statistics
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            sku_pricing = defaultdict(list)
            
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

    async def fetch_product_prices(self, asins: List[str] = None) -> List[Dict]:
        """
        Fetch product prices using Amazon Product Pricing API
        Following the exact pattern from the article
        """
        logger.info("Starting Amazon Product Pricing API fetch...")
        
        # If no ASINs provided, get them from inventory
        if not asins:
            logger.info("Getting ASINs from inventory data...")
            inventory_data = await self.fetch_fba_inventory()
            asins = [item.get('asin') for item in inventory_data if item.get('asin')]
            asins = list(set(asins))  # Remove duplicates
            
        logger.info(f"Found {len(asins)} unique ASINs to get prices for")
        
        if not asins:
            logger.warning("No ASINs found to fetch prices for")
            return []

        # ✅ FIXED: Use same SP-API token as inventory (works!)
        try:
            access_token = await self._get_access_token()
            logger.info("[SUCCESS] SP-API access token obtained successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to get SP-API access token: {str(e)}")
            return []

        # ✅ FIXED: Use SAME headers as working inventory API
        headers = {
            'Authorization': f'Bearer {access_token}',  # ← This was missing!
            'x-amz-access-token': access_token,
            'Content-Type': 'application/json'
        }

        all_prices = []

        # ✅ ARTICLE PATTERN: Function to separate ASIN list to chunks with 20 ASINs
        def chunk_list(data, chunk_size=20):
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]

        async with aiohttp.ClientSession() as session:
            chunk_count = 0
            
            for chunk in chunk_list(asins):
                chunk_count += 1
                logger.info(f"[PRICING] Processing chunk #{chunk_count} with {len(chunk)} ASINs")
                logger.info(f"[PRICING] ASINs: {chunk[:3]}{'...' if len(chunk) > 3 else ''}")

                # ✅ ARTICLE PATTERN: Define params exactly like the article
                request_params = {
                    "MarketplaceId": self.credentials.marketplace_ids[0],  # Use first marketplace
                    "ItemType": "Asin",
                    "Asins": ','.join(chunk)  # ✅ Comma-separated ASINs, max 20
                }

                try:
                    # ✅ FIXED: Use self.base_url like all other working APIs
                    url = f"{self.base_url}/products/pricing/v0/price"
                    
                    async with session.get(
                        url,
                        params=request_params,
                        headers=headers
                    ) as response:
                        
                        logger.info(f"[PRICING] Response code: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            # ✅ ARTICLE PATTERN: Process payload
                            payload = data.get('payload', [])
                            loaded_qty = len(payload)
                            logger.info(f"[PRICING] Loaded {loaded_qty} price records")
                            
                            # ✅ DEBUG: Show sample price data structure
                            if payload:
                                sample_price = payload[0]
                                logger.info(f"[PRICING] Sample price data: {json.dumps(sample_price, indent=2)[:500]}...")
                            
                            # Process each price item
                            for item in payload:
                                asin = item.get('ASIN')
                                status = item.get('status')
                                
                                price_data = {
                                    'asin': asin,
                                    'status': status,
                                    'sku': None,  # Will try to match with inventory
                                    'platform': 'amazon',
                                    'currency': 'USD',
                                    'pricing_data': item,
                                    'created_at': datetime.now().isoformat(),
                                    'raw_data': item
                                }
                                
                                # Extract price information from complex structure
                                if status == 'Success':
                                    product = item.get('Product', {})
                                    identifiers = product.get('Identifiers', {})
                                    offers = product.get('Offers', [])
                                    
                                    if offers:
                                        # Get the first offer (usually the main seller offer)
                                        main_offer = offers[0]
                                        listing_price = main_offer.get('ListingPrice', {})
                                        shipping = main_offer.get('Shipping', {})
                                        
                                        price_data.update({
                                            'listing_price': listing_price.get('Amount'),
                                            'listing_currency': listing_price.get('CurrencyCode'),
                                            'shipping_price': shipping.get('Amount'),
                                            'shipping_currency': shipping.get('CurrencyCode'),
                                            'seller_id': main_offer.get('SellerId'),
                                            'condition': main_offer.get('ItemCondition'),
                                            'fulfillment_channel': main_offer.get('FulfillmentChannel'),
                                            'offer_count': len(offers)
                                        })
                                
                                all_prices.append(price_data)
                            
                        elif response.status == 429:
                            # Rate limited - wait and retry
                            logger.warning("[PRICING] Rate limited by Amazon Pricing API, waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue
                            
                        else:
                            error_text = await response.text()
                            logger.warning(f"[PRICING] Amazon Pricing API error {response.status}: {error_text[:200]}")
                            # Continue with next chunk
                            continue

                except Exception as e:
                    logger.error(f"[PRICING] Error fetching prices for chunk {chunk_count}: {str(e)}")
                    continue

                # ✅ ARTICLE PATTERN: Add delay between requests (article uses time.sleep(2))
                await asyncio.sleep(2)

        logger.info(f"[PRICING] Fetched prices for {len(all_prices)} products")
        return all_prices


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
            
            # NEW: Fetch incoming inventory (Amazon FBA / Shopify GraphQL)
            if hasattr(connector, 'fetch_incoming_inventory'):
                try:
                    incoming_inventory = await connector.fetch_incoming_inventory()
                    all_data['incoming_inventory'] = incoming_inventory
                    if platform_type.value == 'shopify':
                        logger.info(f"🚛 ✅ Fetched {len(incoming_inventory)} incoming inventory items via GraphQL from {platform_type}")
                    else:
                        logger.info(f" ✅ Fetched {len(incoming_inventory)} incoming inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch incoming inventory from {platform_type}: {e}")
                    all_data['incoming_inventory'] = []
            
            # NEW: Fetch inventory levels (Shopify)
            if hasattr(connector, 'fetch_inventory_levels'):
                try:
                    inventory_levels = await connector.fetch_inventory_levels()
                    all_data['inventory_levels'] = inventory_levels
                    logger.info(f"📦 ✅ Fetched {len(inventory_levels)} inventory levels from {platform_type}")
                except Exception as e:
                    logger.warning(f"📦 Failed to fetch inventory levels from {platform_type}: {e}")
                    all_data['inventory_levels'] = []
            
            # NEW: Fetch inventory (Amazon FBA)
            if hasattr(connector, 'fetch_inventory'):
                try:
                    inventory = await connector.fetch_inventory()
                    all_data['inventory'] = inventory
                    logger.info(f"📦 ✅ Fetched {len(inventory)} inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f"📦 Failed to fetch inventory from {platform_type}: {e}")
                    all_data['inventory'] = []
            
            # NEW: Fetch enhanced FBA inventory (Amazon)
            if hasattr(connector, 'fetch_fba_inventory'):
                try:
                    fba_inventory = await connector.fetch_fba_inventory()
                    all_data['fba_inventory'] = fba_inventory
                    logger.info(f"📦 ✅ Fetched {len(fba_inventory)} FBA inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f"📦 Failed to fetch FBA inventory from {platform_type}: {e}")
                    all_data['fba_inventory'] = []
            
            # NEW: Fetch listings pricing (Amazon)
            if hasattr(connector, 'fetch_listings_pricing'):
                try:
                    listings = await connector.fetch_listings_pricing()
                    all_data['listings_pricing'] = listings
                    logger.info(f"💰 ✅ Fetched {len(listings)} product listings with pricing from {platform_type}")
                except Exception as e:
                    logger.warning(f"💰 Failed to fetch listings pricing from {platform_type}: {e}")
                    all_data['listings_pricing'] = []
            
            # NEW: Fetch inventory items metadata (Shopify)
            if hasattr(connector, 'fetch_inventory_items'):
                try:
                    inventory_items = await connector.fetch_inventory_items()
                    all_data['inventory_items'] = inventory_items
                    logger.info(f"🏷️ ✅ Fetched {len(inventory_items)} inventory items from {platform_type}")
                except Exception as e:
                    logger.warning(f"🏷️ Failed to fetch inventory items from {platform_type}: {e}")
                    all_data['inventory_items'] = []
            
            # NEW: Fetch fulfillment orders (Shopify)
            if hasattr(connector, 'fetch_fulfillment_orders'):
                try:
                    fulfillment_orders = await connector.fetch_fulfillment_orders()
                    all_data['fulfillment_orders'] = fulfillment_orders
                    logger.info(f"🚚 ✅ Fetched {len(fulfillment_orders)} fulfillment orders from {platform_type}")
                except Exception as e:
                    logger.warning(f"🚚 Failed to fetch fulfillment orders from {platform_type}: {e}")
                    all_data['fulfillment_orders'] = []
            
            if hasattr(connector, 'fetch_customers'):
                try:
                    customers = await connector.fetch_customers()
                    all_data['customers'] = customers
                    logger.info(f" Fetched {len(customers)} customers from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch customers from {platform_type}: {e}")
                    all_data['customers'] = []
            
            # Log summary of what was fetched
            summary = []
            for data_type, data_list in all_data.items():
                if data_list:
                    if data_type == 'orders':
                        total_line_items = sum(len(order.get('line_items', [])) for order in data_list)
                        summary.append(f"{len(data_list)} {data_type} ({total_line_items} line items)")
                    else:
                        summary.append(f"{len(data_list)} {data_type}")
            
            logger.info(f" 🎉 ENHANCED API FETCH COMPLETE for {platform_type}: {', '.join(summary)}")
            
            return all_data
            
        except Exception as e:
            logger.error(f" Failed to fetch data from {platform_type}: {e}")
            raise APIConnectorError(f"Data fetch failed: {str(e)}")

# Create global instance
api_data_fetcher = APIDataFetcher() 