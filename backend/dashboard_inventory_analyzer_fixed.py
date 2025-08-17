"""
Dashboard-Focused Inventory Analytics Module
Provides specific SKU lists, KPIs, trends, and alerts for dashboard consumption
All data retrieved via direct SQL queries from organized client tables
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from database import get_admin_client

logger = logging.getLogger(__name__)

class DashboardInventoryAnalyzer:
    """Dashboard-focused inventory analyzer with specific KPIs and data structures"""
    
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

    async def get_dashboard_inventory_analytics(self, client_id: str, platform: str = "shopify") -> Dict[str, Any]:
        """Get complete dashboard inventory analytics"""
        try:
            # Ensure database client is available
            self._ensure_client()
            
            logger.info(f"📊 Getting dashboard inventory analytics for client {client_id} (platform: {platform})")
            
            # Get data sources based on platform selection
            if platform.lower() == "shopify":
                shopify_data = await self._get_shopify_data(client_id)
                amazon_data = {"products": [], "orders": []}  # Empty Amazon data
            elif platform.lower() == "amazon":
                amazon_data = await self._get_amazon_data(client_id)
                shopify_data = {"products": [], "orders": []}  # Empty Shopify data
            else:
                # For backward compatibility, get both if platform is invalid
                shopify_data = await self._get_shopify_data(client_id)
                amazon_data = await self._get_amazon_data(client_id)
            
            # Calculate dashboard components using platform-specific data
            analytics = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,

                "sales_kpis": await self._get_kpi_charts(client_id, shopify_data, amazon_data),
                "trend_analysis": await self._get_trend_visualizations(client_id, shopify_data, amazon_data),
                "alerts_summary": await self._get_alerts_summary(client_id, shopify_data, amazon_data),
                "data_summary": {
                    "total_records": len(shopify_data.get('products', [])) + len(amazon_data.get('products', [])),
                    "shopify_products": len(shopify_data.get('products', [])),
                    "shopify_orders": len(shopify_data.get('orders', [])),
                    "amazon_products": len(amazon_data.get('products', [])),
                    "amazon_orders": len(amazon_data.get('orders', [])),
                    "analysis_period": "Last 90 days",
                    "data_completeness": 1.0
                },
                "recommendations": [
                    "Monitor low stock alerts regularly",
                    "Use /api/dashboard/sku-inventory for detailed SKU data with pagination",
                    "SKU data separated for optimal performance with large datasets",
                    "Enable caching for faster subsequent requests"
                ]
            }
            
            logger.info(f"✅ Dashboard inventory analytics completed for client {client_id}")
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard inventory analytics: {e}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "error": str(e),
                "sales_kpis": {},
                "trend_analysis": {},
                "alerts_summary": {"summary_counts": {"total_alerts": 0}},
                "data_summary": {"total_records": 0},
                "recommendations": []
            }
    
    async def _get_shopify_data(self, client_id: str) -> Dict[str, Any]:
        """Get Shopify data from organized tables with optimized queries"""
        try:
            # Ensure database client is available
            admin_client = self._ensure_client()
            
            products_table = f"{client_id.replace('-', '_')}_shopify_products"
            orders_table = f"{client_id.replace('-', '_')}_shopify_orders"
            
            # Get only necessary product fields for performance
            try:
                products_response = admin_client.table(products_table).select(
                    "sku,title,variant_title,inventory_quantity,price,option1,option2,variant_id"
                ).execute()
                products = products_response.data if products_response.data else []
                logger.info(f"📦 Found {len(products)} Shopify product variants")
            except Exception as e:
                logger.info(f"ℹ️ Shopify products table not found or empty: {e}")
                products = []
            
            # Get only necessary order fields for performance
            try:
                orders_response = admin_client.table(orders_table).select(
                    "order_id,total_price,created_at,line_items_count,financial_status,fulfillment_status,order_number"
                ).execute()
                orders = orders_response.data if orders_response.data else []
                logger.info(f"📦 Found {len(orders)} Shopify orders")
            except Exception as e:
                logger.info(f"ℹ️ Shopify orders table not found or empty: {e}")
                orders = []
            
            return {"products": products, "orders": orders}
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get Shopify data: {e}")
            return {"products": [], "orders": []}
    
    async def _get_amazon_data(self, client_id: str) -> Dict[str, Any]:
        """Get Amazon data from organized tables with optimized queries"""
        try:
            # Ensure database client is available
            admin_client = self._ensure_client()
            
            orders_table = f"{client_id.replace('-', '_')}_amazon_orders"
            products_table = f"{client_id.replace('-', '_')}_amazon_products"
            
            # Get only necessary Amazon order fields for performance
            try:
                orders_response = admin_client.table(orders_table).select(
                    "order_id,total_price,created_at,number_of_items_shipped,order_status,order_number"
                ).execute()
                orders = orders_response.data if orders_response.data else []
                logger.info(f"📦 Found {len(orders)} Amazon orders")
            except Exception as e:
                logger.info(f"ℹ️ Amazon orders table not found or empty: {e}")
                orders = []
            
            # Get only necessary Amazon product fields for performance
            try:
                products_response = admin_client.table(products_table).select(
                    "sku,asin,title,quantity,price,brand,status"
                ).execute()
                products = products_response.data if products_response.data else []
                logger.info(f"📦 Found {len(products)} Amazon products")
            except Exception as e:
                logger.info(f"ℹ️ Amazon products table not found or empty: {e}")
                products = []
            
            return {"products": products, "orders": orders}
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get Amazon data: {e}")
            return {"products": [], "orders": []}

    async def _get_sku_list(self, client_id: str, shopify_data: Dict, amazon_data: Dict, 
                           page: int = 1, page_size: int = 50, use_cache: bool = True, 
                           platform: str = "shopify") -> Dict[str, Any]:
        """Get optimized SKU list with fast calculations and caching support"""
        try:
            # Import cache manager
            from sku_cache_manager import get_sku_cache_manager
            cache_manager = get_sku_cache_manager(self.admin_client)
            
            # Create a unique cache key that includes platform
            cache_key = f"dashboard_sku_list_{client_id}_{platform}"
            
            # Try to get cached data first
            if use_cache:
                cached_result = await cache_manager.get_cached_skus(cache_key)
                if cached_result.get('success'):
                    logger.info(f"📦 Using cached SKU data for client {client_id} (platform: {platform})")
                    # Apply pagination to cached data
                    cached_skus = cached_result['skus']
                    total_count = len(cached_skus)
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    paginated_skus = cached_skus[start_idx:end_idx]
                    
                    return {
                        "success": True,
                        "skus": paginated_skus,
                        "pagination": {
                            "current_page": page,
                            "page_size": page_size,
                            "total_count": total_count,
                            "total_pages": (total_count + page_size - 1) // page_size,
                            "has_next": end_idx < total_count,
                            "has_previous": page > 1
                        },
                        "cached": True
                    }
                    
            logger.info(f"🔄 Generating fresh SKU list for client {client_id} (platform: {platform})")
            
            sku_list = []
            
            # Process products based on platform selection
            if platform.lower() == "shopify":
                # Process Shopify products only
                shopify_products = shopify_data.get('products', [])
                
                for product in shopify_products:
                    sku = product.get('sku')
                    if not sku:
                        continue
                    
                    on_hand = product.get('inventory_quantity', 0) or 0
                    incoming = 0  # TODO: Implement purchase order tracking
                    outgoing = self._calculate_outgoing_for_sku(sku, shopify_data.get('orders', []))
                    current_availability = max(0, on_hand + incoming - outgoing)
                    unit_price = product.get('price', 0) or 0
                    
                    sku_list.append({
                        "platform": "shopify",
                        "item_name": product.get('title', 'Unknown Product'),
                        "sku_code": sku,
                        "variant_title": product.get('variant_title', ''),
                        "on_hand_inventory": on_hand,
                        "incoming_inventory": incoming,
                        "outgoing_inventory": outgoing,
                        "current_availability": current_availability,
                        "unit_price": unit_price,
                        "total_value": current_availability * unit_price,
                        "option1": product.get('option1'),
                        "option2": product.get('option2')
                    })
            
            elif platform.lower() == "amazon":
                # Process Amazon products only
                amazon_products = amazon_data.get('products', [])
                
                for product in amazon_products:
                    sku = product.get('sku')
                    asin = product.get('asin')
                    
                    if not sku and not asin:
                        continue
                    
                    on_hand = product.get('quantity', 0) or 0
                    incoming = 0  # TODO: Implement purchase order tracking  
                    outgoing = self._calculate_outgoing_for_asin(asin or sku, amazon_data.get('orders', []))
                    current_availability = max(0, on_hand + incoming - outgoing)
                    unit_price = product.get('price', 0) or 0
                    
                    sku_list.append({
                        "platform": "amazon",
                        "item_name": product.get('title', 'Unknown Product'),
                        "sku_code": sku or asin,
                        "asin": asin,
                        "on_hand_inventory": on_hand,
                        "incoming_inventory": incoming,
                        "outgoing_inventory": outgoing,
                        "current_availability": current_availability,
                        "unit_price": unit_price,
                        "total_value": current_availability * unit_price,
                        "brand": product.get('brand')
                    })
            
            else:
                # For backward compatibility, process both platforms
                # Process Shopify products (simplified for speed)
                shopify_products = shopify_data.get('products', [])
                
                for product in shopify_products:
                    sku = product.get('sku')
                    if not sku:
                        continue
                    
                    on_hand = product.get('inventory_quantity', 0) or 0
                    incoming = 0  # TODO: Implement purchase order tracking
                    outgoing = self._calculate_outgoing_for_sku(sku, shopify_data.get('orders', []))
                    current_availability = max(0, on_hand + incoming - outgoing)
                    unit_price = product.get('price', 0) or 0
                    
                    sku_list.append({
                        "platform": "shopify",
                        "item_name": product.get('title', 'Unknown Product'),
                        "sku_code": sku,
                        "variant_title": product.get('variant_title', ''),
                        "on_hand_inventory": on_hand,
                        "incoming_inventory": incoming,
                        "outgoing_inventory": outgoing,
                        "current_availability": current_availability,
                        "unit_price": unit_price,
                        "total_value": current_availability * unit_price,
                        "option1": product.get('option1'),
                        "option2": product.get('option2')
                    })
                
                # Process Amazon products (simplified for speed)
                amazon_products = amazon_data.get('products', [])
                
                for product in amazon_products:
                    sku = product.get('sku')
                    asin = product.get('asin')
                    
                    if not sku and not asin:
                        continue
                    
                    on_hand = product.get('quantity', 0) or 0
                    incoming = 0  # TODO: Implement purchase order tracking  
                    outgoing = self._calculate_outgoing_for_asin(asin or sku, amazon_data.get('orders', []))
                    current_availability = max(0, on_hand + incoming - outgoing)
                    unit_price = product.get('price', 0) or 0
                    
                    sku_list.append({
                        "platform": "amazon",
                        "item_name": product.get('title', 'Unknown Product'),
                        "sku_code": sku or asin,
                        "asin": asin,
                        "on_hand_inventory": on_hand,
                        "incoming_inventory": incoming,
                        "outgoing_inventory": outgoing,
                        "current_availability": current_availability,
                        "unit_price": unit_price,
                        "total_value": current_availability * unit_price,
                        "brand": product.get('brand')
                    })
                
                # Sort by current availability (lowest first for attention)
                sku_list.sort(key=lambda x: x['current_availability'])
                
                logger.info(f"📦 Generated SKU list with {len(sku_list)} items in fast mode")
            
            # Cache the full result for future requests
            if use_cache and sku_list:
                await cache_manager.cache_skus(cache_key, sku_list)
            
            # Apply pagination to the fresh data
            total_count = len(sku_list)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_skus = sku_list[start_idx:end_idx]
            
            return {
                "success": True,
                "skus": paginated_skus,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": end_idx < total_count,
                    "has_previous": page > 1
                },
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting SKU list: {e}")
            return {
                "success": False,
                "error": str(e),
                "skus": [],
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False
                },
                "cached": False
            }
    
    def _calculate_outgoing_for_sku(self, sku: str, orders: List[Dict]) -> int:
        """Calculate outgoing inventory for a specific SKU"""
        try:
            outgoing = 0
            for order in orders:
                # Check if order contains this SKU
                if str(sku).lower() in str(order).lower():
                    outgoing += 1  # Simplified calculation
            return outgoing
        except Exception:
            return 0
    
    def _calculate_outgoing_for_asin(self, asin: str, orders: List[Dict]) -> int:
        """Calculate outgoing inventory for a specific ASIN"""
        try:
            outgoing = 0
            for order in orders:
                # Check if order contains this ASIN
                if str(asin).lower() in str(order).lower():
                    outgoing += 1  # Simplified calculation
            return outgoing
        except Exception:
            return 0

    async def _get_kpi_charts(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Generate KPI charts with proper time-based calculations"""
        try:
            logger.info(f"📊 Generating KPI charts for client {client_id}")
            
            # Get all orders from both platforms
            all_orders = shopify_data.get('orders', []) + amazon_data.get('orders', [])
            
            # Calculate time periods
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            ninety_days_ago = now - timedelta(days=90)
            
            # Calculate sales for different periods
            sales_7_days = self._calculate_sales_for_period(all_orders, seven_days_ago, now)
            sales_30_days = self._calculate_sales_for_period(all_orders, thirty_days_ago, now)
            sales_90_days = self._calculate_sales_for_period(all_orders, ninety_days_ago, now)
            
            # Calculate inventory metrics
            total_inventory = sum(p.get('inventory_quantity', 0) or 0 for p in shopify_data.get('products', []))
            total_inventory += sum(p.get('quantity', 0) or 0 for p in amazon_data.get('products', []))
            
            # Calculate turnover and days of stock
            if total_inventory > 0 and sales_30_days['units'] > 0:
                turnover_rate = (sales_30_days['units'] * 12) / total_inventory  # Annualized
                avg_daily_sales = sales_30_days['units'] / 30
                days_stock_remaining = total_inventory / avg_daily_sales if avg_daily_sales > 0 else 999
            else:
                turnover_rate = 0
                avg_daily_sales = 0
                days_stock_remaining = 999
            
            return {
                "total_sales_7_days": {
                    "revenue": round(sales_7_days['revenue'], 2),
                    "units": sales_7_days['units'],
                    "orders": sales_7_days['orders']
                },
                "total_sales_30_days": {
                    "revenue": round(sales_30_days['revenue'], 2),
                    "units": sales_30_days['units'], 
                    "orders": sales_30_days['orders']
                },
                "total_sales_90_days": {
                    "revenue": round(sales_90_days['revenue'], 2),
                    "units": sales_90_days['units'],
                    "orders": sales_90_days['orders']
                },
                "inventory_turnover_rate": round(turnover_rate, 2),
                "days_stock_remaining": round(min(days_stock_remaining, 999), 1),
                "avg_daily_sales": round(avg_daily_sales, 1),
                "total_inventory_units": total_inventory
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating KPI charts: {e}")
            return {"error": str(e)}

    def _calculate_sales_for_period(self, orders: List[Dict], start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate sales metrics for a specific time period with proper date handling"""
        revenue = 0
        units = 0
        order_count = 0
        
        logger.debug(f"🔍 Calculating sales from {start_date} to {end_date} for {len(orders)} orders")
        
        for order in orders:
            try:
                # Handle different date formats
                order_date_str = order.get('created_at') or order.get('order_date', '')
                if not order_date_str:
                    continue
                    
                # Parse date (handle different formats)
                try:
                    if 'T' in order_date_str:
                        order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00'))
                    else:
                        order_date = datetime.strptime(order_date_str, '%Y-%m-%d')
                except:
                    continue
                
                # Check if order is in the time period
                if start_date <= order_date <= end_date:
                    order_count += 1
                    
                    # Add revenue
                    order_total = order.get('total_price', 0)
                    if isinstance(order_total, str):
                        try:
                            order_total = float(order_total.replace('$', '').replace(',', ''))
                        except:
                            order_total = 0
                    revenue += order_total or 0
                    
                    # Add units (simplified)
                    units += order.get('line_items_count', 1) or order.get('number_of_items_shipped', 1) or 1
                    
            except Exception as e:
                logger.debug(f"Error processing order: {e}")
                continue
        
        logger.debug(f"📈 Period results: {order_count} orders, ${revenue:.2f} revenue, {units} units")
        
        return {
            "revenue": revenue,
            "units": units,
            "orders": order_count
        }

    async def _get_trend_visualizations(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Generate trend visualization data with simplified calculations"""
        try:
            logger.info(f"📈 Generating trend visualizations for client {client_id}")
            
            all_orders = shopify_data.get('orders', []) + amazon_data.get('orders', [])
            
            # Generate simple trend data for the last 30 days
            trends = []
            now = datetime.now()
            
            for i in range(30):
                date = now - timedelta(days=29-i)
                day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                day_sales = self._calculate_sales_for_period(all_orders, day_start, day_end)
                
                trends.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "revenue": day_sales['revenue'],
                    "orders": day_sales['orders'],
                    "units": day_sales['units']
                })
            
            # Calculate simple growth metrics
            recent_week = trends[-7:]
            previous_week = trends[-14:-7]
            
            recent_revenue = sum(day['revenue'] for day in recent_week)
            previous_revenue = sum(day['revenue'] for day in previous_week)
            
            growth_rate = 0
            if previous_revenue > 0:
                growth_rate = ((recent_revenue - previous_revenue) / previous_revenue) * 100
            
            return {
                "daily_sales_trends": trends,
                "weekly_comparison": {
                    "current_week_revenue": round(recent_revenue, 2),
                    "previous_week_revenue": round(previous_revenue, 2),
                    "growth_rate": round(growth_rate, 1)
                },
                "trend_summary": {
                    "direction": "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable",
                    "growth_rate": round(growth_rate, 1),
                    "volatility": "low"  # Simplified
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating trend visualizations: {e}")
            return {"error": str(e)}

    async def _get_alerts_summary(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get comprehensive alerts summary with proper calculations"""
        try:
            logger.info(f"🚨 Generating alerts for client {client_id}")
            
            # Initialize counters
            low_stock_count = 0
            overstock_count = 0
            low_stock_details = []
            overstock_details = []
            
            # Process Shopify products for stock alerts
            for product in shopify_data.get('products', []):
                inventory = product.get('inventory_quantity', 0) or 0
                sku = product.get('sku', '')
                title = product.get('title', 'Unknown Product')
                
                if inventory <= 5 and inventory > 0:  # Low stock threshold
                    low_stock_count += 1
                    low_stock_details.append({
                        "sku": sku,
                        "item_name": title,
                        "current_inventory": inventory,
                        "platform": "shopify",
                        "severity": "high" if inventory <= 2 else "medium"
                    })
                elif inventory == 0:  # Out of stock
                    low_stock_count += 1
                    low_stock_details.append({
                        "sku": sku,
                        "item_name": title,
                        "current_inventory": inventory,
                        "platform": "shopify",
                        "severity": "critical"
                    })
                elif inventory > 100:  # Overstock threshold
                    overstock_count += 1
                    overstock_details.append({
                        "sku": sku,
                        "item_name": title,
                        "current_inventory": inventory,
                        "platform": "shopify",
                        "severity": "medium"
                    })
            
            # Process Amazon products for stock alerts
            for product in amazon_data.get('products', []):
                inventory = product.get('quantity', 0) or 0
                sku = product.get('sku', product.get('asin', ''))
                title = product.get('title', 'Unknown Product')
                
                if inventory <= 5 and inventory > 0:  # Low stock threshold
                    low_stock_count += 1
                    low_stock_details.append({
                        "sku": sku,
                        "item_name": title,
                        "current_inventory": inventory,
                        "platform": "amazon",
                        "severity": "high" if inventory <= 2 else "medium"
                    })
                elif inventory == 0:  # Out of stock
                    low_stock_count += 1
                    low_stock_details.append({
                        "sku": sku,
                        "item_name": title,
                        "current_inventory": inventory,
                        "platform": "amazon",
                        "severity": "critical"
                    })
                elif inventory > 100:  # Overstock threshold
                    overstock_count += 1
                    overstock_details.append({
                        "sku": sku,
                        "item_name": title,
                        "current_inventory": inventory,
                        "platform": "amazon",
                        "severity": "medium"
                    })
            
            # Simple sales trend analysis for alerts
            all_orders = shopify_data.get('orders', []) + amazon_data.get('orders', [])
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            fourteen_days_ago = now - timedelta(days=14)
            
            recent_week_sales = self._calculate_sales_for_period(all_orders, seven_days_ago, now)
            previous_week_sales = self._calculate_sales_for_period(all_orders, fourteen_days_ago, seven_days_ago)
            
            sales_spike_count = 0
            sales_slowdown_count = 0
            sales_spike_details = []
            sales_slowdown_details = []
            
            # Check for significant changes
            if previous_week_sales['revenue'] > 0:
                change_percent = ((recent_week_sales['revenue'] - previous_week_sales['revenue']) / previous_week_sales['revenue']) * 100
                
                if change_percent > 50:  # Sales spike
                    sales_spike_count = 1
                    sales_spike_details.append({
                        "type": "sales_spike",
                        "change_percent": round(change_percent, 1),
                        "current_sales": recent_week_sales['revenue'],
                        "previous_sales": previous_week_sales['revenue'],
                        "severity": "medium"
                    })
                elif change_percent < -30:  # Sales slowdown
                    sales_slowdown_count = 1
                    sales_slowdown_details.append({
                        "type": "sales_slowdown", 
                        "change_percent": round(change_percent, 1),
                        "current_sales": recent_week_sales['revenue'],
                        "previous_sales": previous_week_sales['revenue'],
                        "severity": "high"
                    })
            
            total_alerts = low_stock_count + overstock_count + sales_spike_count + sales_slowdown_count
            
            logger.info(f"🚨 Alerts calculated - Low stock: {low_stock_count}, Overstock: {overstock_count}, Spikes: {sales_spike_count}, Slowdowns: {sales_slowdown_count}")
            
            return {
                "summary_counts": {
                    "low_stock_alerts": low_stock_count,
                    "overstock_alerts": overstock_count,
                    "sales_spike_alerts": sales_spike_count,
                    "sales_slowdown_alerts": sales_slowdown_count,
                    "total_alerts": total_alerts
                },
                "detailed_alerts": {
                    "low_stock_alerts": low_stock_details,
                    "overstock_alerts": overstock_details,
                    "sales_spike_alerts": sales_spike_details,
                    "sales_slowdown_alerts": sales_slowdown_details
                },
                "quick_links": {
                    "view_low_stock": f"/dashboard/alerts/low-stock?client_id={client_id}",
                    "view_overstock": f"/dashboard/alerts/overstock?client_id={client_id}",
                    "view_sales_alerts": f"/dashboard/alerts/sales?client_id={client_id}"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating alerts summary: {e}")
            return {"error": str(e)}

# Global instance
dashboard_inventory_analyzer = DashboardInventoryAnalyzer()
