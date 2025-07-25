import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin
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
                        logger.info(f"✅ Shopify connection successful: {shop_name}")
                        return True, f"Connected to {shop_name}"
                    elif response.status == 401:
                        return False, "Invalid access token"
                    elif response.status == 403:
                        return False, "Insufficient permissions"
                    else:
                        return False, f"Connection failed: HTTP {response.status}"
        except Exception as e:
            logger.error(f"❌ Shopify connection test failed: {e}")
            return False, f"Connection error: {str(e)}"
    
    async def fetch_orders(self, limit: int = 250, days_back: int = 30) -> List[Dict]:
        """Fetch recent orders from Shopify"""
        try:
            since_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "limit": min(limit, 250),  # Shopify max is 250
                    "status": "any",
                    "created_at_min": since_date,
                    "financial_status": "any"
                }
                
                async with session.get(
                    f"{self.base_url}/orders.json",
                    headers=self.headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        orders = data.get('orders', [])
                        
                        # Transform to standard format
                        standardized_orders = []
                        for order in orders:
                            standardized_orders.append({
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
                        
                        logger.info(f"✅ Fetched {len(standardized_orders)} Shopify orders")
                        return standardized_orders
                    
                    elif response.status == 429:
                        # Rate limited
                        raise APIConnectorError("Rate limited by Shopify. Please try again later.")
                    else:
                        raise APIConnectorError(f"Failed to fetch orders: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to fetch Shopify orders: {e}")
            raise APIConnectorError(f"Shopify orders fetch failed: {str(e)}")
    
    async def fetch_products(self, limit: int = 250) -> List[Dict]:
        """Fetch products from Shopify"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "limit": min(limit, 250),
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
                        standardized_products = []
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
                            
                            standardized_products.append({
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
                        
                        logger.info(f"✅ Fetched {len(standardized_products)} Shopify products")
                        return standardized_products
                    else:
                        raise APIConnectorError(f"Failed to fetch products: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to fetch Shopify products: {e}")
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
                        logger.info("✅ Amazon SP-API token refreshed")
                        return self.access_token
                    else:
                        raise APIConnectorError(f"Failed to get Amazon access token: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to get Amazon access token: {e}")
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
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/sellers/v1/marketplaceParticipations",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        marketplaces = data.get('payload', [])
                        marketplace_names = [mp.get('marketplace', {}).get('name', 'Unknown') for mp in marketplaces]
                        logger.info(f"✅ Amazon SP-API connection successful: {', '.join(marketplace_names)}")
                        return True, f"Connected to marketplaces: {', '.join(marketplace_names[:3])}"
                    elif response.status == 401:
                        return False, "Invalid credentials or expired token"
                    else:
                        return False, f"Connection failed: HTTP {response.status}"
                        
        except Exception as e:
            logger.error(f"❌ Amazon connection test failed: {e}")
            return False, f"Connection error: {str(e)}"
    
    async def fetch_orders(self, limit: int = 100, days_back: int = 30) -> List[Dict]:
        """Fetch recent orders from Amazon SP-API"""
        try:
            access_token = await self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'x-amz-access-token': access_token,
                'Content-Type': 'application/json'
            }
            
            # Amazon date format
            created_after = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            params = {
                'CreatedAfter': created_after,
                'MarketplaceIds': ','.join(self.credentials.marketplace_ids),
                'MaxResultsPerPage': min(limit, 100)  # Amazon max is 100
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/orders/v0/orders",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        orders = data.get('payload', {}).get('Orders', [])
                        
                        # Transform to standard format
                        standardized_orders = []
                        for order in orders:
                            # Amazon order structure
                            order_total = order.get('OrderTotal', {})
                            
                            standardized_orders.append({
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
                        
                        logger.info(f"✅ Fetched {len(standardized_orders)} Amazon orders")
                        return standardized_orders
                    
                    elif response.status == 429:
                        raise APIConnectorError("Rate limited by Amazon. Please try again later.")
                    else:
                        raise APIConnectorError(f"Failed to fetch orders: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to fetch Amazon orders: {e}")
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
            logger.error(f"❌ WooCommerce connection test failed: {e}")
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
            logger.error(f"❌ Connection test failed for {platform_type}: {e}")
            return False, f"Connection test failed: {str(e)}"
    
    async def fetch_all_data(self, platform_type: PlatformType, credentials: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Fetch all available data from a platform"""
        try:
            connector = APIConnectorFactory.create_connector(platform_type, credentials)
            
            all_data = {}
            
            # Fetch different data types based on platform capabilities
            if hasattr(connector, 'fetch_orders'):
                try:
                    orders = await connector.fetch_orders()
                    all_data['orders'] = orders
                    logger.info(f"📦 Fetched {len(orders)} orders from {platform_type}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch orders from {platform_type}: {e}")
                    all_data['orders'] = []
            
            if hasattr(connector, 'fetch_products'):
                try:
                    products = await connector.fetch_products()
                    all_data['products'] = products
                    logger.info(f"🛍️ Fetched {len(products)} products from {platform_type}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch products from {platform_type}: {e}")
                    all_data['products'] = []
            
            if hasattr(connector, 'fetch_customers'):
                try:
                    customers = await connector.fetch_customers()
                    all_data['customers'] = customers
                    logger.info(f"👥 Fetched {len(customers)} customers from {platform_type}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch customers from {platform_type}: {e}")
                    all_data['customers'] = []
            
            return all_data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch data from {platform_type}: {e}")
            raise APIConnectorError(f"Data fetch failed: {str(e)}")

# Create global instance
api_data_fetcher = APIDataFetcher() 