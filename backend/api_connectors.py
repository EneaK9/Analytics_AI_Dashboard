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
        """Fetch ALL orders from Shopify with pagination"""
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
                            
                            # Transform to standard format
                            page_orders = []
                            for order in orders:
                                page_orders.append({
                                    'order_id': order.get('id'),
                                    'order_number': order.get('order_number'),
                                    'created_at': order.get('created_at'),
                                    'updated_at': order.get('updated_at'),
                                    'total_price': float(order.get('total_price', 0)),
                                    'subtotal_price': float(order.get('subtotal_price', 0)),
                                    'total_tax': float(order.get('total_tax', 0)),
                                    'currency': order.get('currency'),
                                    'financial_status': order.get('financial_status'),
                                    'fulfillment_status': order.get('fulfillment_status'),
                                    'customer_email': order.get('email'),
                                    'customer_id': order.get('customer', {}).get('id'),
                                    'line_items_count': len(order.get('line_items', [])),
                                    'shipping_address': order.get('shipping_address'),
                                    'billing_address': order.get('billing_address'),
                                    'gateway': order.get('gateway'),
                                    'source_name': order.get('source_name'),
                                    'tags': order.get('tags'),
                                    'discount_codes': order.get('discount_codes', []),
                                    'platform': 'shopify'
                                })
                            
                            all_orders.extend(page_orders)
                            logger.info(f" Fetched page with {len(page_orders)} orders (Total: {len(all_orders)})")
                            
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
                
                logger.info(f" Fetched ALL {len(all_orders)} Shopify orders")
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
                            
                            # Transform to standard format
                            page_products = []
                            for product in products:
                                # Process variants
                                variants = []
                                for variant in product.get('variants', []):
                                    variants.append({
                                        'variant_id': variant.get('id'),
                                        'title': variant.get('title'),
                                        'price': float(variant.get('price', 0)),
                                        'sku': variant.get('sku'),
                                        'inventory_quantity': variant.get('inventory_quantity', 0),
                                        'weight': variant.get('weight'),
                                        'requires_shipping': variant.get('requires_shipping')
                                    })
                                
                                page_products.append({
                                    'product_id': product.get('id'),
                                    'title': product.get('title'),
                                    'handle': product.get('handle'),
                                    'product_type': product.get('product_type'),
                                    'vendor': product.get('vendor'),
                                    'created_at': product.get('created_at'),
                                    'updated_at': product.get('updated_at'),
                                    'published_at': product.get('published_at'),
                                    'status': product.get('status'),
                                    'tags': product.get('tags'),
                                    'variants': variants,
                                    'variants_count': len(variants),
                                    'images_count': len(product.get('images', [])),
                                    'platform': 'shopify'
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
        """Fetch ALL orders from Amazon SP-API with pagination"""
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
                            
                            # Transform to standard format
                            page_orders = []
                            for order in orders:
                                # Amazon order structure
                                order_total = order.get('OrderTotal', {})
                                
                                page_orders.append({
                                    'order_id': order.get('AmazonOrderId'),
                                    'order_number': order.get('AmazonOrderId'),
                                    'created_at': order.get('PurchaseDate'),
                                    'updated_at': order.get('LastUpdateDate'),
                                    'total_price': float(order_total.get('Amount', 0)),
                                    'currency': order_total.get('CurrencyCode', 'USD'),
                                    'order_status': order.get('OrderStatus'),
                                    'fulfillment_channel': order.get('FulfillmentChannel'),
                                    'sales_channel': order.get('SalesChannel'),
                                    'marketplace_id': order.get('MarketplaceId'),
                                    'number_of_items_shipped': order.get('NumberOfItemsShipped', 0),
                                    'number_of_items_unshipped': order.get('NumberOfItemsUnshipped', 0),
                                    'payment_method': order.get('PaymentMethod'),
                                    'is_business_order': order.get('IsBusinessOrder', False),
                                    'is_premium_order': order.get('IsPremiumOrder', False),
                                    'platform': 'amazon'
                                })
                            
                            all_orders.extend(page_orders)
                            logger.info(f" Fetched page with {len(page_orders)} Amazon orders (Total: {len(all_orders)})")
                            
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
                
                logger.info(f" Fetched ALL {len(all_orders)} Amazon orders")
                return all_orders
                        
        except Exception as e:
            logger.error(f" Failed to fetch Amazon orders: {e}")
            raise APIConnectorError(f"Amazon orders fetch failed: {str(e)}")

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
        """Fetch all available data from a platform"""
        try:
            connector = APIConnectorFactory.create_connector(platform_type, credentials)
            
            all_data = {}
            
            # Fetch different data types based on platform capabilities
            if hasattr(connector, 'fetch_orders'):
                try:
                    orders = await connector.fetch_orders()  # No limit parameters - fetch ALL
                    all_data['orders'] = orders
                    logger.info(f" Fetched {len(orders)} orders from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch orders from {platform_type}: {e}")
                    all_data['orders'] = []
            
            if hasattr(connector, 'fetch_products'):
                try:
                    products = await connector.fetch_products()  # No limit parameters - fetch ALL
                    all_data['products'] = products
                    logger.info(f"️ Fetched {len(products)} products from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch products from {platform_type}: {e}")
                    all_data['products'] = []
            
            if hasattr(connector, 'fetch_customers'):
                try:
                    customers = await connector.fetch_customers()
                    all_data['customers'] = customers
                    logger.info(f" Fetched {len(customers)} customers from {platform_type}")
                except Exception as e:
                    logger.warning(f" Failed to fetch customers from {platform_type}: {e}")
                    all_data['customers'] = []
            
            return all_data
            
        except Exception as e:
            logger.error(f" Failed to fetch data from {platform_type}: {e}")
            raise APIConnectorError(f"Data fetch failed: {str(e)}")

# Create global instance
api_data_fetcher = APIDataFetcher() 