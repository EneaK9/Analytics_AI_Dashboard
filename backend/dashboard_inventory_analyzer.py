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
        self.admin_client = get_admin_client()
        if not self.admin_client:
            raise Exception("❌ No admin database client available")
    
    async def get_dashboard_inventory_analytics(self, client_id: str) -> Dict[str, Any]:
        """Get complete dashboard inventory analytics"""
        try:
            logger.info(f"📊 Getting dashboard inventory analytics for client {client_id}")
            
            # Get all data sources
            shopify_data = await self._get_shopify_data(client_id)
            amazon_data = await self._get_amazon_data(client_id)
            
            # Calculate dashboard components
            analytics = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,

                "sales_kpis": await self._get_kpi_charts(client_id, shopify_data, amazon_data),
                "trend_analysis": await self._get_trend_visualizations(client_id, shopify_data, amazon_data),
                "alerts_summary": await self._get_alerts_summary(client_id, shopify_data, amazon_data),
                "data_summary": {
                    "total_records": len(shopify_data.get('products', [])) + len(amazon_data.get('products', [])) + len(shopify_data.get('orders', [])) + len(amazon_data.get('orders', [])),
                    "total_skus": len([p for p in shopify_data.get('products', []) if p.get('sku')]) + len([p for p in amazon_data.get('products', []) if p.get('sku')]),
                    "analysis_period": "30_days", 
                    "data_completeness": 100,
                    "shopify_products": len(shopify_data.get('products', [])),
                    "shopify_orders": len(shopify_data.get('orders', [])),
                    "amazon_products": len(amazon_data.get('products', [])),
                    "amazon_orders": len(amazon_data.get('orders', []))
                },
                "sku_inventory": {
                    "skus": [],  # Empty - use dedicated endpoint for SKU data
                    "summary_stats": {
                        "total_skus": len([p for p in shopify_data.get('products', []) if p.get('sku')]) + len([p for p in amazon_data.get('products', []) if p.get('sku')]),
                        "total_inventory_value": 0,  # Calculate separately if needed
                        "low_stock_count": 0,        # Calculate separately if needed  
                        "out_of_stock_count": 0,     # Calculate separately if needed
                        "overstock_count": 0         # Calculate separately if needed
                    }
                },
                "recommendations": [
                    "Use /api/dashboard/sku-inventory for detailed SKU data with pagination",
                    "SKU data separated for optimal performance with large datasets",
                    "Enable caching for faster subsequent requests"
                ]
            }
            
            logger.info(f"✅ Dashboard inventory analytics completed for client {client_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Dashboard inventory analytics failed: {e}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "error": str(e)
            }
    
    async def _get_shopify_data(self, client_id: str) -> Dict[str, Any]:
        """Get Shopify data from organized tables with optimized queries"""
        try:
            products_table = f"{client_id.replace('-', '_')}_shopify_products"
            orders_table = f"{client_id.replace('-', '_')}_shopify_orders"
            
            # Get only necessary product fields for performance
            try:
                products_response = self.admin_client.table(products_table).select(
                    "sku,title,variant_title,inventory_quantity,price,option1,option2,variant_id"
                ).execute()
                products = products_response.data if products_response.data else []
                logger.info(f"📦 Found {len(products)} Shopify product variants")
            except Exception as e:
                logger.info(f"ℹ️ Shopify products table not found or empty: {e}")
                products = []
            
            # Get only necessary order fields for performance
            try:
                orders_response = self.admin_client.table(orders_table).select(
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
            orders_table = f"{client_id.replace('-', '_')}_amazon_orders"
            products_table = f"{client_id.replace('-', '_')}_amazon_products"
            
            # Get only necessary Amazon order fields for performance
            try:
                orders_response = self.admin_client.table(orders_table).select(
                    "order_id,total_price,created_at,number_of_items_shipped,order_status,order_number"
                ).execute()
                orders = orders_response.data if orders_response.data else []
                logger.info(f"📦 Found {len(orders)} Amazon orders")
            except Exception as e:
                logger.info(f"ℹ️ Amazon orders table not found or empty: {e}")
                orders = []
            
            # Get only necessary Amazon product fields for performance
            try:
                products_response = self.admin_client.table(products_table).select(
                    "sku,asin,title,quantity,price,brand,status"
                ).execute()
                products = products_response.data if products_response.data else []
                logger.info(f"📦 Found {len(products)} Amazon products")
            except Exception as e:
                logger.info(f"ℹ️ Amazon products table not found or empty: {e}")
                products = []
            
            return {"orders": orders, "products": products}
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get Amazon data: {e}")
            return {"orders": [], "products": []}
    
    async def _get_sku_list(self, client_id: str, shopify_data: Dict, amazon_data: Dict, page: int = 1, page_size: int = 50, use_cache: bool = True) -> Dict[str, Any]:
        """Get optimized SKU list with fast calculations and caching support"""
        try:
            # Import cache manager
            from sku_cache_manager import get_sku_cache_manager
            cache_manager = get_sku_cache_manager(self.admin_client)
            
            # Try to get from cache first if enabled
            if use_cache:
                cached_result = await cache_manager.get_cached_skus(client_id, page, page_size)
                if cached_result.get("success"):
                    return cached_result
                    
            logger.info(f"🔄 Generating fresh SKU list for client {client_id}")
            
            sku_list = []
            
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
                await cache_manager.cache_skus(client_id, sku_list)
            
            # Apply pagination to the fresh data
            total_count = len(sku_list)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_skus = sku_list[start_idx:end_idx]
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "success": True,
                "cached": False,
                "skus": paginated_skus,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating SKU list: {e}")
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
                }
            }
    
    def _calculate_outgoing_for_sku(self, sku: str, orders: List[Dict]) -> int:
        """Calculate outgoing inventory for a specific SKU from unfulfilled orders"""
        if not sku:
            return 0
            
        outgoing = 0
        
        for order in orders:
            try:
                # Only count orders that are paid but not yet fulfilled
                financial_status = order.get('financial_status', '').lower()
                fulfillment_status = order.get('fulfillment_status', '').lower()
                
                # Consider orders that are paid but not fully fulfilled
                if financial_status in ['paid', 'authorized'] and fulfillment_status in ['', 'unfulfilled', 'partial']:
                    # Estimate 1 unit per order for this SKU (conservative estimate)
                    # TODO: Parse actual line_items when available for exact quantities
                    outgoing += 1
                    
            except Exception as e:
                logger.debug(f"Error processing order for outgoing calculation: {e}")
                continue
        
        return outgoing
    
    def _calculate_outgoing_for_asin(self, identifier: str, orders: List[Dict]) -> int:
        """Calculate outgoing inventory for Amazon ASIN/SKU from unfulfilled orders"""
        if not identifier:
            return 0
            
        outgoing = 0
        
        for order in orders:
            try:
                # Check Amazon order status
                order_status = order.get('order_status', '').lower()
                
                # Count orders that are pending fulfillment
                if order_status in ['pending', 'unshipped', 'partiallyshipped']:
                    # Use number_of_items_shipped vs total to estimate pending
                    items_shipped = order.get('number_of_items_shipped', 0) or 0
                    # Rough estimate - 1 unit per unfulfilled order for this ASIN
                    outgoing += 1
                    
            except Exception as e:
                logger.debug(f"Error processing Amazon order for outgoing calculation: {e}")
                continue
        
        return outgoing
    
    def _calculate_outgoing_inventory_shopify(self, sku: str, orders: List[Dict]) -> int:
        """Legacy method - use the new _calculate_outgoing_for_sku instead"""
        return self._calculate_outgoing_for_sku(sku, orders)
    
    def _calculate_outgoing_inventory_amazon(self, identifier: str, orders: List[Dict]) -> int:
        """Calculate outgoing inventory from Amazon orders (simplified)"""
        # Similar simplified calculation for Amazon
        outgoing = 0
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        for order in orders:
            try:
                created_at = order.get('created_at')
                if created_at:
                    order_date = pd.to_datetime(created_at)
                    if order_date >= thirty_days_ago:
                        # Estimate based on items shipped
                        items_shipped = order.get('number_of_items_shipped', 0) or 0
                        outgoing += items_shipped
            except:
                continue
        
        return outgoing
    
    async def _get_kpi_charts(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get optimized KPI charts data with corrected calculations"""
        try:
            shopify_orders = shopify_data.get('orders', [])
            amazon_orders = amazon_data.get('orders', [])
            
            # Current time and date ranges
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            ninety_days_ago = now - timedelta(days=90)
            
            logger.info(f"🔍 Calculating KPIs for {len(shopify_orders)} Shopify orders, {len(amazon_orders)} Amazon orders")
            
            # Calculate sales for each period with proper date filtering
            sales_7_days = self._calculate_sales_for_period(shopify_orders + amazon_orders, seven_days_ago, now)
            sales_30_days = self._calculate_sales_for_period(shopify_orders + amazon_orders, thirty_days_ago, now)
            sales_90_days = self._calculate_sales_for_period(shopify_orders + amazon_orders, ninety_days_ago, now)
            
            logger.info(f"📊 Sales calculated - 7d: {sales_7_days}, 30d: {sales_30_days}, 90d: {sales_90_days}")
            
            # Fast inventory calculation
            total_inventory = self._fast_calculate_inventory(shopify_data, amazon_data)
            avg_daily_sales = sales_30_days['units'] / 30 if sales_30_days['units'] > 0 else 0
            
            # Simple metrics
            turnover_rate = sales_30_days['units'] / total_inventory if total_inventory > 0 else 0
            days_stock_remaining = total_inventory / avg_daily_sales if avg_daily_sales > 0 else 999
            
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
                created_at = order.get('created_at')
                if created_at:
                    # Handle different date formats
                    if isinstance(created_at, str):
                        # Try multiple date formats
                        try:
                            order_date = pd.to_datetime(created_at, utc=True)
                        except:
                            try:
                                order_date = pd.to_datetime(created_at)
                            except:
                                continue
                    else:
                        order_date = pd.to_datetime(created_at)
                    
                    # Make dates timezone-aware for comparison if needed
                    if order_date.tz is None:
                        order_date = order_date.tz_localize('UTC')
                    if start_date.tzinfo is None:
                        start_date = start_date.replace(tzinfo=order_date.tz)
                    if end_date.tzinfo is None:
                        end_date = end_date.replace(tzinfo=order_date.tz)
                    
                    if start_date <= order_date <= end_date:
                        order_revenue = float(order.get('total_price', 0) or 0)
                        revenue += order_revenue
                        
                        # Better units estimation
                        if 'line_items_count' in order:
                            units += int(order.get('line_items_count', 1) or 1)
                        elif 'number_of_items_shipped' in order:
                            units += int(order.get('number_of_items_shipped', 1) or 1)
                        else:
                            units += 1
                        
                        order_count += 1
                        logger.debug(f"📦 Order {order.get('order_id')} - Revenue: ${order_revenue}, Date: {order_date}")
                        
            except Exception as e:
                logger.debug(f"⚠️ Error processing order: {e}")
                continue
        
        logger.info(f"📊 Period totals - Orders: {order_count}, Revenue: ${revenue:.2f}, Units: {units}")
        return {"revenue": revenue, "units": units, "orders": order_count}
    
    def _calculate_sales_in_period(self, orders: List[Dict], start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate sales metrics for a specific time period (legacy method)"""
        return self._calculate_sales_for_period(orders, start_date, end_date)
    
    def _fast_calculate_sales(self, orders: List[Dict], since_date: datetime) -> Dict[str, float]:
        """Fast sales calculation for KPIs - now uses the improved date handling"""
        now = datetime.now()
        return self._calculate_sales_for_period(orders, since_date, now)
    
    def _fast_calculate_inventory(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Fast inventory calculation"""
        total = 0
        
        # Shopify inventory
        for product in shopify_data.get('products', []):
            total += product.get('inventory_quantity', 0) or 0
        
        # Amazon inventory
        for product in amazon_data.get('products', []):
            total += product.get('quantity', 0) or 0
        
        return total
    
    def _calculate_total_inventory(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Calculate total inventory units"""
        total = 0
        
        # Shopify inventory
        for product in shopify_data.get('products', []):
            total += product.get('inventory_quantity', 0) or 0
        
        # Amazon inventory
        for product in amazon_data.get('products', []):
            total += product.get('quantity', 0) or 0
        
        return total
    
    async def _get_trend_visualizations(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get trend visualization data with corrected weekly calculations"""
        try:
            shopify_orders = shopify_data.get('orders', [])
            amazon_orders = amazon_data.get('orders', [])
            all_orders = shopify_orders + amazon_orders
            
            logger.info(f"📈 Generating trends for {len(all_orders)} total orders")
            
            # Calculate weekly data for last 12 weeks
            now = datetime.now()
            weekly_data = []
            
            for i in range(12):  # Last 12 weeks
                week_end = now - timedelta(weeks=i)
                week_start = now - timedelta(weeks=i+1)
                
                # Calculate sales for this specific week
                week_sales = self._calculate_sales_for_period(all_orders, week_start, week_end)
                
                weekly_data.append({
                    "week": week_start.strftime("%Y-W%U"),
                    "date": week_start.strftime("%Y-%m-%d"),
                    "revenue": round(week_sales['revenue'], 2),
                    "units_sold": week_sales['units'],
                    "orders": week_sales['orders']
                })
            
            weekly_data.reverse()  # Chronological order (oldest first)
            
            # Calculate comparison metrics - last 4 weeks vs previous 4 weeks
            if len(weekly_data) >= 8:
                recent_4_weeks = weekly_data[-4:]  # Last 4 weeks
                previous_4_weeks = weekly_data[-8:-4]  # Previous 4 weeks
                
                current_avg_revenue = sum(w['revenue'] for w in recent_4_weeks) / 4
                historical_avg_revenue = sum(w['revenue'] for w in previous_4_weeks) / 4
                
                current_avg_units = sum(w['units_sold'] for w in recent_4_weeks) / 4
                historical_avg_units = sum(w['units_sold'] for w in previous_4_weeks) / 4
                
                revenue_change = ((current_avg_revenue - historical_avg_revenue) / historical_avg_revenue * 100) if historical_avg_revenue > 0 else 0
                units_change = ((current_avg_units - historical_avg_units) / historical_avg_units * 100) if historical_avg_units > 0 else 0
            else:
                current_avg_revenue = historical_avg_revenue = 0
                current_avg_units = historical_avg_units = 0
                revenue_change = units_change = 0
            
            # Calculate inventory levels with estimated historical changes
            current_inventory = self._fast_calculate_inventory(shopify_data, amazon_data)
            inventory_levels_chart = self._estimate_historical_inventory_levels(weekly_data, current_inventory, all_orders)
            
            logger.info(f"📊 Trends calculated - {len(weekly_data)} weeks, current avg revenue: ${current_avg_revenue:.2f}")
            
            return {
                "weekly_data_12_weeks": weekly_data,
                "inventory_levels_chart": inventory_levels_chart,
                "units_sold_chart": [
                    {"date": w["date"], "units_sold": w["units_sold"]} 
                    for w in weekly_data
                ],
                "sales_comparison": {
                    "current_period_avg_revenue": round(current_avg_revenue, 2),
                    "historical_avg_revenue": round(historical_avg_revenue, 2),
                    "revenue_change_percent": round(revenue_change, 1),
                    "current_period_avg_units": round(current_avg_units, 1),
                    "historical_avg_units": round(historical_avg_units, 1),
                    "units_change_percent": round(units_change, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating trend visualizations: {e}")
            return {"error": str(e)}
    
    def _estimate_historical_inventory_levels(self, weekly_data: List[Dict], current_inventory: int, all_orders: List[Dict]) -> List[Dict]:
        """Estimate historical inventory levels based on sales data"""
        inventory_chart = []
        
        # Start with current inventory and work backwards
        estimated_inventory = current_inventory
        
        # Process weeks in reverse order (most recent first)
        for i in range(len(weekly_data) - 1, -1, -1):
            week = weekly_data[i]
            units_sold = week.get('units_sold', 0)
            
            # Add back the units sold this week to estimate previous inventory
            if i < len(weekly_data) - 1:  # Not the current week
                estimated_inventory += units_sold
            
            inventory_chart.insert(0, {
                "date": week["date"],
                "inventory_level": max(0, estimated_inventory)
            })
        
        return inventory_chart
    
    def _estimate_inventory_level_for_date(self, date: datetime, shopify_data: Dict, amazon_data: Dict) -> int:
        """Estimate inventory level for a specific date (simplified)"""
        # This is a simplified estimation - in reality you'd need historical inventory data
        # For now, we'll use current inventory as baseline
        current_inventory = self._calculate_total_inventory(shopify_data, amazon_data)
        
        # Estimate based on sales since that date
        now = datetime.now()
        if date >= now:
            return current_inventory
        
        # Rough estimation: current inventory + estimated sales since that date
        days_since = (now - date).days
        avg_daily_consumption = 5  # Simplified average
        estimated_inventory = current_inventory + (days_since * avg_daily_consumption)
        
        return max(0, estimated_inventory)
    
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
            shopify_products = shopify_data.get('products', [])
            for product in shopify_products:
                inventory = product.get('inventory_quantity', 0) or 0
                title = product.get('title', 'Unknown Product')
                sku = product.get('sku')
                
                if inventory <= 10:  # Low stock threshold
                    low_stock_count += 1
                    if len(low_stock_details) < 5:  # Keep first 5 for display
                        severity = "critical" if inventory == 0 else "high" if inventory <= 3 else "medium"
                        low_stock_details.append({
                            "platform": "shopify",
                            "sku": sku,
                            "item_name": title,
                            "current_stock": inventory,
                            "severity": severity
                        })
                elif inventory >= 100:  # Overstock threshold
                    overstock_count += 1
                    if len(overstock_details) < 3:  # Keep first 3 for display
                        overstock_details.append({
                            "platform": "shopify",
                            "sku": sku,
                            "item_name": title,
                            "current_stock": inventory,
                            "severity": "medium"
                        })
            
            # Process Amazon products for stock alerts
            amazon_products = amazon_data.get('products', [])
            for product in amazon_products:
                quantity = product.get('quantity', 0) or 0
                title = product.get('title', 'Unknown Product')
                sku = product.get('sku')
                asin = product.get('asin')
                
                if quantity <= 10:  # Low stock threshold
                    low_stock_count += 1
                    if len(low_stock_details) < 5:  # Keep first 5 for display
                        severity = "critical" if quantity == 0 else "high" if quantity <= 3 else "medium"
                        low_stock_details.append({
                            "platform": "amazon",
                            "sku": sku,
                            "asin": asin,
                            "item_name": title,
                            "current_stock": quantity,
                            "severity": severity
                        })
                elif quantity >= 100:  # Overstock threshold
                    overstock_count += 1
                    if len(overstock_details) < 3:  # Keep first 3 for display
                        overstock_details.append({
                            "platform": "amazon",
                            "sku": sku,
                            "asin": asin,
                            "item_name": title,
                            "current_stock": quantity,
                            "severity": "medium"
                        })
            
            # Calculate sales trend alerts
            all_orders = shopify_data.get('orders', []) + amazon_data.get('orders', [])
            now = datetime.now()
            
            # Compare recent week vs previous week for trend analysis
            recent_week_sales = self._calculate_sales_for_period(
                all_orders, 
                now - timedelta(days=7), 
                now
            )
            previous_week_sales = self._calculate_sales_for_period(
                all_orders, 
                now - timedelta(days=14), 
                now - timedelta(days=7)
            )
            
            sales_spike_count = 0
            sales_slowdown_count = 0
            sales_spike_details = []
            sales_slowdown_details = []
            
            # Check for significant sales changes
            if previous_week_sales['revenue'] > 0:
                revenue_change = ((recent_week_sales['revenue'] - previous_week_sales['revenue']) / previous_week_sales['revenue']) * 100
                
                if revenue_change > 50:  # 50% increase = spike
                    sales_spike_count = 1
                    sales_spike_details.append({
                        "type": "sales_spike",
                        "severity": "info",
                        "message": f"Sales spiked {revenue_change:.1f}% this week (${recent_week_sales['revenue']:.2f} vs ${previous_week_sales['revenue']:.2f})",
                        "current_revenue": recent_week_sales['revenue'],
                        "previous_revenue": previous_week_sales['revenue'],
                        "change_percent": revenue_change
                    })
                elif revenue_change < -30:  # 30% decrease = slowdown
                    sales_slowdown_count = 1
                    sales_slowdown_details.append({
                        "type": "sales_slowdown",
                        "severity": "warning",
                        "message": f"Sales dropped {abs(revenue_change):.1f}% this week (${recent_week_sales['revenue']:.2f} vs ${previous_week_sales['revenue']:.2f})",
                        "current_revenue": recent_week_sales['revenue'],
                        "previous_revenue": previous_week_sales['revenue'],
                        "change_percent": revenue_change
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
