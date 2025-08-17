"""
Organized Inventory Analytics Module
Analyzes organized client tables to extract inventory metrics, sales KPIs, trends, and alerts
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from database import get_admin_client

logger = logging.getLogger(__name__)

class OrganizedInventoryAnalyzer:
    """Analyzer that works with organized client tables for inventory analytics"""
    
    def __init__(self):
        self.admin_client = None
        self._client_initialized = False
    
    def _ensure_client(self):
        """Lazy initialization of database client"""
        if not self._client_initialized:
            self.admin_client = get_admin_client()
            self._client_initialized = True
            if not self.admin_client:
                raise Exception("❌ No admin database client available")
        return self.admin_client

    async def analyze_client_inventory(self, client_id: str) -> Dict[str, Any]:
        """Main analysis function for organized client tables"""
        try:
            # Ensure database client is available
            self._ensure_client()
            
            logger.info(f"🔍 Starting organized inventory analysis for client {client_id}")
            
            # Get data from organized tables
            shopify_data = await self._get_shopify_data(client_id)
            amazon_data = await self._get_amazon_data(client_id)
            
            # Perform comprehensive analysis
            analytics = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "data_sources": {
                    "shopify_products": len(shopify_data.get('products', [])),
                    "shopify_orders": len(shopify_data.get('orders', [])),
                    "amazon_orders": len(amazon_data.get('orders', [])),
                    "amazon_products": len(amazon_data.get('products', []))
                },
                "inventory_kpis": await self._calculate_inventory_kpis(client_id, shopify_data, amazon_data),
                "sales_kpis": await self._calculate_sales_kpis(client_id, shopify_data, amazon_data),
                "trend_analysis": await self._analyze_trends(client_id, shopify_data, amazon_data),
                "alerts": await self._generate_alerts(client_id, shopify_data, amazon_data),
                "top_products": await self._get_top_products(client_id, shopify_data, amazon_data),
                "low_stock_alerts": await self._get_low_stock_alerts(client_id, shopify_data, amazon_data)
            }
            
            logger.info(f"✅ Organized inventory analysis completed successfully")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error in organized inventory analysis: {str(e)}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "message": f"Analysis failed: {str(e)}",
                "error": str(e)
            }
    
    async def _get_shopify_data(self, client_id: str) -> Dict[str, Any]:
        """Get Shopify data from organized tables"""
        try:
            products_table = f"{client_id.replace('-', '_')}_shopify_products"
            orders_table = f"{client_id.replace('-', '_')}_shopify_orders"
            
            # Get all Shopify products/variants
            try:
                products_response = self._ensure_client().table(products_table).select("*").execute()
                products = products_response.data if products_response.data else []
            except Exception:
                products = []
            
            # Get all Shopify orders
            try:
                orders_response = self._ensure_client().table(orders_table).select("*").execute()
                orders = orders_response.data if orders_response.data else []
            except Exception:
                orders = []
            
            logger.info(f"📦 Found {len(products)} Shopify product variants, {len(orders)} Shopify orders")
            
            return {"products": products, "orders": orders}
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get Shopify data: {e}")
            return {"products": [], "orders": []}
    
    async def _get_amazon_data(self, client_id: str) -> Dict[str, Any]:
        """Get Amazon data from organized tables"""
        try:
            orders_table = f"{client_id.replace('-', '_')}_amazon_orders"
            products_table = f"{client_id.replace('-', '_')}_amazon_products"
            
            # Get Amazon orders
            try:
                orders_response = self._ensure_client().table(orders_table).select("*").execute()
                orders = orders_response.data if orders_response.data else []
            except Exception:
                orders = []
            
            # Get Amazon products
            try:
                products_response = self._ensure_client().table(products_table).select("*").execute()
                products = products_response.data if products_response.data else []
            except Exception:
                products = []
            
            logger.info(f"📦 Found {len(orders)} Amazon orders, {len(products)} Amazon products")
            
            return {"orders": orders, "products": products}
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get Amazon data: {e}")
            return {"orders": [], "products": []}
    
    async def _calculate_inventory_kpis(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Calculate inventory KPIs from organized data"""
        try:
            shopify_products = shopify_data.get('products', [])
            amazon_products = amazon_data.get('products', [])
            
            # Shopify inventory metrics
            shopify_total_inventory = sum(p.get('inventory_quantity', 0) or 0 for p in shopify_products)
            shopify_total_value = sum((p.get('price', 0) or 0) * (p.get('inventory_quantity', 0) or 0) for p in shopify_products)
            shopify_unique_skus = len(set(p.get('sku') for p in shopify_products if p.get('sku')))
            shopify_low_stock = len([p for p in shopify_products if (p.get('inventory_quantity', 0) or 0) < 10])
            
            # Amazon inventory metrics
            amazon_total_inventory = sum(p.get('quantity', 0) or 0 for p in amazon_products)
            amazon_total_value = sum((p.get('price', 0) or 0) * (p.get('quantity', 0) or 0) for p in amazon_products)
            amazon_unique_skus = len(set(p.get('sku') for p in amazon_products if p.get('sku')))
            amazon_low_stock = len([p for p in amazon_products if (p.get('quantity', 0) or 0) < 10])
            
            # Combined metrics
            total_inventory = shopify_total_inventory + amazon_total_inventory
            total_value = shopify_total_value + amazon_total_value
            total_skus = shopify_unique_skus + amazon_unique_skus
            total_low_stock = shopify_low_stock + amazon_low_stock
            
            # Average prices
            shopify_avg_price = sum(p.get('price', 0) or 0 for p in shopify_products) / len(shopify_products) if shopify_products else 0
            amazon_avg_price = sum(p.get('price', 0) or 0 for p in amazon_products) / len(amazon_products) if amazon_products else 0
            
            return {
                "total_inventory_units": total_inventory,
                "total_inventory_value": round(total_value, 2),
                "total_unique_skus": total_skus,
                "low_stock_count": total_low_stock,
                "shopify": {
                    "total_units": shopify_total_inventory,
                    "total_value": round(shopify_total_value, 2),
                    "unique_skus": shopify_unique_skus,
                    "low_stock": shopify_low_stock,
                    "avg_price": round(shopify_avg_price, 2),
                    "total_variants": len(shopify_products)
                },
                "amazon": {
                    "total_units": amazon_total_inventory,
                    "total_value": round(amazon_total_value, 2),
                    "unique_skus": amazon_unique_skus,
                    "low_stock": amazon_low_stock,
                    "avg_price": round(amazon_avg_price, 2),
                    "total_products": len(amazon_products)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating inventory KPIs: {e}")
            return {"error": str(e)}
    
    async def _calculate_sales_kpis(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Calculate sales KPIs from organized data"""
        try:
            shopify_orders = shopify_data.get('orders', [])
            amazon_orders = amazon_data.get('orders', [])
            
            # Shopify sales metrics
            shopify_total_orders = len(shopify_orders)
            shopify_total_revenue = sum(order.get('total_price', 0) or 0 for order in shopify_orders)
            shopify_avg_order_value = shopify_total_revenue / shopify_total_orders if shopify_total_orders > 0 else 0
            
            # Shopify orders by status
            shopify_status_counts = {}
            for order in shopify_orders:
                status = order.get('financial_status', 'Unknown')
                shopify_status_counts[status] = shopify_status_counts.get(status, 0) + 1
            
            # Amazon sales metrics
            amazon_total_orders = len(amazon_orders)
            amazon_total_revenue = sum(order.get('total_price', 0) or 0 for order in amazon_orders)
            amazon_avg_order_value = amazon_total_revenue / amazon_total_orders if amazon_total_orders > 0 else 0
            
            # Amazon orders by status
            amazon_status_counts = {}
            for order in amazon_orders:
                status = order.get('order_status', 'Unknown')
                amazon_status_counts[status] = amazon_status_counts.get(status, 0) + 1
            
            # Amazon premium orders
            premium_orders = len([o for o in amazon_orders if o.get('is_premium_order', False)])
            premium_ratio = premium_orders / amazon_total_orders if amazon_total_orders > 0 else 0
            
            # Combined metrics
            total_orders = shopify_total_orders + amazon_total_orders
            total_revenue = shopify_total_revenue + amazon_total_revenue
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Recent orders (last 30 days) - combined
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_shopify_orders = []
            recent_amazon_orders = []
            
            # Get recent Shopify orders
            for order in shopify_orders:
                try:
                    created_at = order.get('created_at')
                    if created_at:
                        order_date = pd.to_datetime(created_at)
                        if order_date >= thirty_days_ago:
                            recent_shopify_orders.append(order)
                except:
                    continue
            
            # Get recent Amazon orders
            for order in amazon_orders:
                try:
                    created_at = order.get('created_at')
                    if created_at:
                        order_date = pd.to_datetime(created_at)
                        if order_date >= thirty_days_ago:
                            recent_amazon_orders.append(order)
                except:
                    continue
            
            recent_shopify_revenue = sum(order.get('total_price', 0) or 0 for order in recent_shopify_orders)
            recent_amazon_revenue = sum(order.get('total_price', 0) or 0 for order in recent_amazon_orders)
            recent_total_orders = len(recent_shopify_orders) + len(recent_amazon_orders)
            recent_total_revenue = recent_shopify_revenue + recent_amazon_revenue
            
            return {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "avg_order_value": round(avg_order_value, 2),
                "shopify": {
                    "orders": shopify_total_orders,
                    "revenue": round(shopify_total_revenue, 2),
                    "avg_order_value": round(shopify_avg_order_value, 2),
                    "orders_by_status": shopify_status_counts
                },
                "amazon": {
                    "orders": amazon_total_orders,
                    "revenue": round(amazon_total_revenue, 2),
                    "avg_order_value": round(amazon_avg_order_value, 2),
                    "orders_by_status": amazon_status_counts,
                    "premium_orders_ratio": round(premium_ratio * 100, 1)
                },
                "recent_30_days": {
                    "total_orders": recent_total_orders,
                    "total_revenue": round(recent_total_revenue, 2),
                    "shopify_orders": len(recent_shopify_orders),
                    "shopify_revenue": round(recent_shopify_revenue, 2),
                    "amazon_orders": len(recent_amazon_orders),
                    "amazon_revenue": round(recent_amazon_revenue, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating sales KPIs: {e}")
            return {"error": str(e)}
    
    async def _analyze_trends(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Analyze trends from organized data"""
        try:
            shopify_orders = shopify_data.get('orders', [])
            amazon_orders = amazon_data.get('orders', [])
            all_orders = shopify_orders + amazon_orders
            
            if not all_orders:
                return {"message": "No order data available for trend analysis"}
            
            # Group orders by month (combined Shopify + Amazon)
            monthly_data = {}
            shopify_monthly_data = {}
            amazon_monthly_data = {}
            
            # Process Shopify orders
            for order in shopify_orders:
                try:
                    created_at = order.get('created_at')
                    if created_at:
                        order_date = pd.to_datetime(created_at)
                        month_key = order_date.strftime('%Y-%m')
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {'orders': 0, 'revenue': 0, 'shopify_orders': 0, 'shopify_revenue': 0, 'amazon_orders': 0, 'amazon_revenue': 0}
                        if month_key not in shopify_monthly_data:
                            shopify_monthly_data[month_key] = {'orders': 0, 'revenue': 0}
                        
                        revenue = order.get('total_price', 0) or 0
                        monthly_data[month_key]['orders'] += 1
                        monthly_data[month_key]['revenue'] += revenue
                        monthly_data[month_key]['shopify_orders'] += 1
                        monthly_data[month_key]['shopify_revenue'] += revenue
                        shopify_monthly_data[month_key]['orders'] += 1
                        shopify_monthly_data[month_key]['revenue'] += revenue
                except:
                    continue
            
            # Process Amazon orders
            for order in amazon_orders:
                try:
                    created_at = order.get('created_at')
                    if created_at:
                        order_date = pd.to_datetime(created_at)
                        month_key = order_date.strftime('%Y-%m')
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {'orders': 0, 'revenue': 0, 'shopify_orders': 0, 'shopify_revenue': 0, 'amazon_orders': 0, 'amazon_revenue': 0}
                        if month_key not in amazon_monthly_data:
                            amazon_monthly_data[month_key] = {'orders': 0, 'revenue': 0}
                        
                        revenue = order.get('total_price', 0) or 0
                        monthly_data[month_key]['orders'] += 1
                        monthly_data[month_key]['revenue'] += revenue
                        monthly_data[month_key]['amazon_orders'] += 1
                        monthly_data[month_key]['amazon_revenue'] += revenue
                        amazon_monthly_data[month_key]['orders'] += 1
                        amazon_monthly_data[month_key]['revenue'] += revenue
                except:
                    continue
            
            # Sort by month
            sorted_months = sorted(monthly_data.keys())
            
            # Calculate growth rates
            trends = []
            for i, month in enumerate(sorted_months):
                month_data = monthly_data[month]
                
                growth_rate = 0
                if i > 0:
                    prev_month = sorted_months[i-1]
                    prev_revenue = monthly_data[prev_month]['revenue']
                    if prev_revenue > 0:
                        growth_rate = ((month_data['revenue'] - prev_revenue) / prev_revenue) * 100
                
                trends.append({
                    "month": month,
                    "total_orders": month_data['orders'],
                    "total_revenue": round(month_data['revenue'], 2),
                    "shopify_orders": month_data['shopify_orders'],
                    "shopify_revenue": round(month_data['shopify_revenue'], 2),
                    "amazon_orders": month_data['amazon_orders'],
                    "amazon_revenue": round(month_data['amazon_revenue'], 2),
                    "growth_rate": round(growth_rate, 1)
                })
            
            return {
                "monthly_trends": trends,
                "total_months": len(sorted_months),
                "latest_month": sorted_months[-1] if sorted_months else None,
                "platforms": {
                    "shopify_months": len(shopify_monthly_data),
                    "amazon_months": len(amazon_monthly_data)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing trends: {e}")
            return {"error": str(e)}
    
    async def _generate_alerts(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> List[Dict[str, Any]]:
        """Generate alerts from organized data"""
        try:
            alerts = []
            
            # Low stock alerts for Shopify
            shopify_products = shopify_data.get('products', [])
            for product in shopify_products:
                inventory = product.get('inventory_quantity', 0) or 0
                if inventory < 5:
                    alerts.append({
                        "type": "low_stock",
                        "platform": "shopify",
                        "severity": "high" if inventory == 0 else "medium",
                        "title": f"Low Stock: {product.get('title', 'Unknown Product')}",
                        "message": f"SKU {product.get('sku', 'N/A')} has only {inventory} units left",
                        "sku": product.get('sku'),
                        "current_stock": inventory
                    })
            
            # Low stock alerts for Amazon
            amazon_products = amazon_data.get('products', [])
            for product in amazon_products:
                quantity = product.get('quantity', 0) or 0
                if quantity < 5:
                    alerts.append({
                        "type": "low_stock", 
                        "platform": "amazon",
                        "severity": "high" if quantity == 0 else "medium",
                        "title": f"Low Stock: {product.get('title', 'Unknown Product')}",
                        "message": f"ASIN {product.get('asin', 'N/A')} has only {quantity} units left",
                        "asin": product.get('asin'),
                        "sku": product.get('sku'),
                        "current_stock": quantity
                    })
            
            # High value inventory alerts
            shopify_high_value = [p for p in shopify_products if (p.get('price', 0) or 0) > 100]
            if shopify_high_value:
                total_value = sum((p.get('price', 0) or 0) * (p.get('inventory_quantity', 0) or 0) for p in shopify_high_value)
                alerts.append({
                    "type": "high_value_inventory",
                    "platform": "shopify",
                    "severity": "info",
                    "title": "High Value Inventory",
                    "message": f"${total_value:,.2f} in high-value products (${len(shopify_high_value)} items over $100)",
                    "value": total_value,
                    "count": len(shopify_high_value)
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error generating alerts: {e}")
            return [{"type": "error", "message": f"Error generating alerts: {str(e)}"}]
    
    async def _get_top_products(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get top products by various metrics"""
        try:
            # Top Shopify products by inventory value
            shopify_products = shopify_data.get('products', [])
            shopify_by_value = []
            for product in shopify_products:
                value = (product.get('price', 0) or 0) * (product.get('inventory_quantity', 0) or 0)
                if value > 0:
                    shopify_by_value.append({
                        "title": product.get('title'),
                        "sku": product.get('sku'),
                        "price": product.get('price', 0),
                        "inventory": product.get('inventory_quantity', 0),
                        "total_value": round(value, 2),
                        "option1": product.get('option1'),
                        "option2": product.get('option2')
                    })
            
            shopify_by_value.sort(key=lambda x: x['total_value'], reverse=True)
            
            # Top Amazon products by price
            amazon_products = amazon_data.get('products', [])
            amazon_by_price = []
            for product in amazon_products:
                price = product.get('price', 0) or 0
                if price > 0:
                    amazon_by_price.append({
                        "title": product.get('title'),
                        "asin": product.get('asin'),
                        "sku": product.get('sku'),
                        "price": price,
                        "quantity": product.get('quantity', 0),
                        "brand": product.get('brand')
                    })
            
            amazon_by_price.sort(key=lambda x: x['price'], reverse=True)
            
            return {
                "shopify_top_by_value": shopify_by_value[:10],
                "amazon_top_by_price": amazon_by_price[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting top products: {e}")
            return {"error": str(e)}
    
    async def _get_low_stock_alerts(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> List[Dict[str, Any]]:
        """Get detailed low stock alerts"""
        try:
            low_stock = []
            
            # Shopify low stock
            shopify_products = shopify_data.get('products', [])
            for product in shopify_products:
                inventory = product.get('inventory_quantity', 0) or 0
                if inventory < 10:
                    low_stock.append({
                        "platform": "shopify",
                        "title": product.get('title'),
                        "sku": product.get('sku'),
                        "current_stock": inventory,
                        "price": product.get('price'),
                        "variant": f"{product.get('option1', '')} {product.get('option2', '')}".strip(),
                        "urgency": "critical" if inventory == 0 else "high" if inventory < 3 else "medium"
                    })
            
            # Amazon low stock
            amazon_products = amazon_data.get('products', [])
            for product in amazon_products:
                quantity = product.get('quantity', 0) or 0
                if quantity < 10:
                    low_stock.append({
                        "platform": "amazon",
                        "title": product.get('title'),
                        "asin": product.get('asin'),
                        "sku": product.get('sku'),
                        "current_stock": quantity,
                        "price": product.get('price'),
                        "brand": product.get('brand'),
                        "urgency": "critical" if quantity == 0 else "high" if quantity < 3 else "medium"
                    })
            
            # Sort by urgency and stock level
            urgency_order = {"critical": 0, "high": 1, "medium": 2}
            low_stock.sort(key=lambda x: (urgency_order.get(x['urgency'], 3), x['current_stock']))
            
            return low_stock
            
        except Exception as e:
            logger.error(f"❌ Error getting low stock alerts: {e}")
            return []

# Global instance
organized_inventory_analyzer = OrganizedInventoryAnalyzer()
