"""
Component-Specific Data Query Functions

This module provides functions to query database for specific component data
with date range and platform filtering. Each function handles a specific
component type and returns appropriately formatted data.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from database import get_admin_client

logger = logging.getLogger(__name__)


class ComponentDataManager:
    """Manages component-specific database queries for dashboard components"""
    
    def __init__(self):
        pass
    
    def _get_table_names(self, client_id: str) -> Dict[str, str]:
        """Get organized table names for a client"""
        safe_client_id = client_id.replace('-', '_')
        return {
            'shopify_products': f"{safe_client_id}_shopify_products",
            'shopify_orders': f"{safe_client_id}_shopify_orders",
            'amazon_products': f"{safe_client_id}_amazon_products",
            'amazon_orders': f"{safe_client_id}_amazon_orders"
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object (always returns timezone-aware datetime in UTC)"""
        if not date_str:
            return None
        try:
            # Try ISO format first (handles timezone-aware strings)
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # If it's timezone-naive, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            try:
                # Parse YYYY-MM-DD format and assume UTC
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None
    
    async def get_total_sales_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get total sales data for a specific platform and date range.
        Sums all order prices for the specified period.
        """
        logger.info(f"📊 Getting total sales data for {client_id} - {platform} ({start_date} to {end_date})")
        
        tables = self._get_table_names(client_id)
        result = {}
        
        try:
            if platform in ["shopify", "combined"]:
                shopify_data = await self._get_platform_sales_data(
                    tables['shopify_orders'], 'shopify', start_date, end_date
                )
                result['shopify'] = shopify_data
            
            if platform in ["amazon", "combined"]:
                amazon_data = await self._get_platform_sales_data(
                    tables['amazon_orders'], 'amazon', start_date, end_date
                )
                result['amazon'] = amazon_data
            
            # For combined platform, calculate totals
            if platform == "combined":
                shopify_sales = result.get('shopify', {})
                amazon_sales = result.get('amazon', {})
                
                # Calculate combined totals
                combined_revenue = (shopify_sales.get('total_sales_30_days', {}).get('revenue', 0) + 
                                  amazon_sales.get('total_sales_30_days', {}).get('revenue', 0))
                combined_orders = (shopify_sales.get('total_sales_30_days', {}).get('orders', 0) + 
                                 amazon_sales.get('total_sales_30_days', {}).get('orders', 0))
                combined_units = (shopify_sales.get('total_sales_30_days', {}).get('units', 0) + 
                                amazon_sales.get('total_sales_30_days', {}).get('units', 0))
                
                # Calculate combined sales comparison (within-period trend)
                shopify_comparison = shopify_sales.get('sales_comparison', {})
                amazon_comparison = amazon_sales.get('sales_comparison', {})
                
                # Combine first and second half revenues from both platforms
                combined_first_half = (shopify_comparison.get('first_half_avg_revenue', 0) + 
                                     amazon_comparison.get('first_half_avg_revenue', 0))
                combined_second_half = (shopify_comparison.get('second_half_avg_revenue', 0) + 
                                      amazon_comparison.get('second_half_avg_revenue', 0))
                
                # Calculate combined growth rate
                combined_growth_rate = ((combined_second_half - combined_first_half) / combined_first_half) * 100 if combined_first_half > 0 else 0
                
                result['combined'] = {
                    'total_revenue': combined_revenue,
                    'total_orders': combined_orders,
                    'total_units': combined_units,
                    'sales_comparison': {
                        'first_half_avg_revenue': combined_first_half,
                        'second_half_avg_revenue': combined_second_half,
                        'growth_rate': combined_growth_rate
                    }
                }
            
            logger.info(f"✅ Total sales data retrieved for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting total sales data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_platform_sales_data(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """Get sales data for a specific platform"""
        try:
            # Build query based on platform
            db_client = get_admin_client()
            query = db_client.table(table_name).select("*")
            
            # Add date filtering if provided
            if start_date:
                start_dt = self._parse_date(start_date)
                if start_dt:
                    if platform == "shopify":
                        query = query.gte("created_at", start_dt.isoformat())
                    elif platform == "amazon":
                        query = query.gte("created_at", start_dt.isoformat())
            
            if end_date:
                end_dt = self._parse_date(end_date)
                if end_dt:
                    if platform == "shopify":
                        query = query.lte("created_at", end_dt.isoformat())
                    elif platform == "amazon":
                        query = query.lte("created_at", end_dt.isoformat())
            
            response = query.execute()
            orders = response.data or []
            
            # Calculate sales metrics
            total_revenue = 0
            total_orders = len(orders)
            total_units = 0
            
            for order in orders:
                if platform == "shopify":
                    # For Shopify orders, sum the total_price
                    order_value = float(order.get('total_price', 0) or 0)
                    total_revenue += order_value
                    
                    # Count line items for units
                    line_items = order.get('line_items', [])
                    if isinstance(line_items, list):
                        for item in line_items:
                            total_units += int(item.get('quantity', 0) or 0)
                    
                elif platform == "amazon":
                    # For Amazon orders, sum the total_price
                    order_value = float(order.get('total_price', 0) or 0)
                    total_revenue += order_value
                    total_units += int(order.get('quantity', 0) or 0)
            
            # Calculate comparison metrics (within-period trend)
            period_days = 30  # default period
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                if start_dt and end_dt:
                    period_days = (end_dt - start_dt).days + 1  # Include both start and end dates
            
            # Get within-period growth rate (first half vs second half)
            first_half_revenue, second_half_revenue = await self._get_within_period_trend(
                table_name, platform, start_date, end_date, period_days
            )
            
            return {
                'total_sales_30_days': {
                    'revenue': total_revenue,
                    'orders': total_orders,
                    'units': total_units
                },
                'sales_comparison': {
                    'first_half_avg_revenue': first_half_revenue / max(period_days // 2, 1),
                    'second_half_avg_revenue': second_half_revenue / max(period_days // 2, 1),
                    'growth_rate': ((second_half_revenue - first_half_revenue) / first_half_revenue) * 100 if first_half_revenue > 0 else 0
                },
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': period_days
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting {platform} sales data: {str(e)}")
            return {
                'total_sales_30_days': {'revenue': 0, 'orders': 0, 'units': 0},
                'sales_comparison': {'first_half_avg_revenue': 0, 'second_half_avg_revenue': 0, 'growth_rate': 0},
                'error': str(e)
            }
    
    async def _get_within_period_trend(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str], period_days: int) -> tuple[float, float]:
        """Get revenue for first half and second half of the selected period to calculate within-period growth"""
        try:
            if not start_date or not end_date:
                return 0.0, 0.0
            
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)
            if not start_dt or not end_dt:
                return 0.0, 0.0
            
            # Calculate midpoint of the selected period
            midpoint_dt = start_dt + timedelta(days=period_days // 2)
            
            db_client = get_admin_client()
            
            # Get first half revenue (start to midpoint)
            first_half_query = db_client.table(table_name).select("*")
            if platform == "shopify":
                first_half_query = first_half_query.gte("created_at", start_dt.isoformat()).lt("created_at", midpoint_dt.isoformat())
            elif platform == "amazon":
                first_half_query = first_half_query.gte("created_at", start_dt.isoformat()).lt("created_at", midpoint_dt.isoformat())
            
            first_half_response = first_half_query.execute()
            first_half_orders = first_half_response.data or []
            
            # Get second half revenue (midpoint to end)
            second_half_query = db_client.table(table_name).select("*")
            if platform == "shopify":
                second_half_query = second_half_query.gte("created_at", midpoint_dt.isoformat()).lte("created_at", end_dt.isoformat())
            elif platform == "amazon":
                second_half_query = second_half_query.gte("created_at", midpoint_dt.isoformat()).lte("created_at", end_dt.isoformat())
            
            second_half_response = second_half_query.execute()
            second_half_orders = second_half_response.data or []
            
            # Calculate revenue for each half
            first_half_revenue = 0.0
            for order in first_half_orders:
                first_half_revenue += float(order.get('total_price', 0) or 0)
            
            second_half_revenue = 0.0
            for order in second_half_orders:
                second_half_revenue += float(order.get('total_price', 0) or 0)
            
            logger.debug(f"📊 Within-period trend for {platform}: First half: ${first_half_revenue}, Second half: ${second_half_revenue}")
            
            return first_half_revenue, second_half_revenue
            
        except Exception as e:
            logger.error(f"❌ Error getting within-period trend: {str(e)}")
            return 0.0, 0.0
    
    async def _get_platform_turnover_trend(self, client_id: str, platform: str, start_date: Optional[str], end_date: Optional[str], period_days: int) -> tuple[float, float]:
        """Get turnover rates for first half and second half of the selected period"""
        try:
            if not start_date or not end_date:
                return 0.0, 0.0
            
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)
            if not start_dt or not end_dt:
                return 0.0, 0.0
            
            # Calculate midpoint of the selected period
            midpoint_dt = start_dt + timedelta(days=period_days // 2)
            
            # Get revenue data for each half using the existing within-period trend method
            table_names = self._get_table_names(client_id)
            table_name = table_names.get(f"{platform}_orders")
            
            if not table_name:
                return 0.0, 0.0
                
            first_half_revenue, second_half_revenue = await self._get_within_period_trend(
                table_name, platform, start_date, end_date, period_days
            )
            
            # Get inventory data for the platform
            inventory_data = await self.get_inventory_levels_data(client_id, platform, start_date, end_date)
            
            # For trend calculation, we need to use a consistent inventory baseline
            # Since we don't have true historical inventory, we'll use current inventory as the baseline
            # This represents "turnover velocity" rather than absolute turnover ratio
            platform_inventory_data = inventory_data.get(platform, {})
            inventory_value = platform_inventory_data.get('current_total_inventory', 0)
            
            if inventory_value <= 0:
                logger.warning(f"⚠️ No inventory data available for {platform} trend calculation")
                return 0.0, 0.0
            
            # Calculate turnover rates for each half
            # Note: Using same inventory baseline to show revenue acceleration/deceleration
            first_half_turnover = first_half_revenue / inventory_value
            second_half_turnover = second_half_revenue / inventory_value
            
            logger.debug(f"📊 Turnover trend for {platform}: Revenue trend - First half: ${first_half_revenue:.2f}, Second half: ${second_half_revenue:.2f}")
            logger.debug(f"📊 Turnover rates - First half: {first_half_turnover:.2f}, Second half: {second_half_turnover:.2f}")
            
            return first_half_turnover, second_half_turnover
            
        except Exception as e:
            logger.error(f"❌ Error getting platform turnover trend: {str(e)}")
            return 0.0, 0.0
    
    async def _get_combined_turnover_trend(self, client_id: str, start_date: Optional[str], end_date: Optional[str], period_days: int) -> tuple[float, float]:
        """Get combined turnover rates for first half and second half of the selected period"""
        try:
            # Get revenue data for both platforms for each half
            table_names = self._get_table_names(client_id)
            
            # Get Shopify revenue data for each half
            shopify_table = table_names.get("shopify_orders")
            shopify_first_revenue, shopify_second_revenue = 0, 0
            if shopify_table:
                shopify_first_revenue, shopify_second_revenue = await self._get_within_period_trend(
                    shopify_table, "shopify", start_date, end_date, period_days
                )
            
            # Get Amazon revenue data for each half
            amazon_table = table_names.get("amazon_orders")
            amazon_first_revenue, amazon_second_revenue = 0, 0
            if amazon_table:
                amazon_first_revenue, amazon_second_revenue = await self._get_within_period_trend(
                    amazon_table, "amazon", start_date, end_date, period_days
                )
            
            # Calculate combined revenues for each half
            combined_first_revenue = shopify_first_revenue + amazon_first_revenue
            combined_second_revenue = shopify_second_revenue + amazon_second_revenue
            
            # Get combined inventory data
            inventory_data = await self.get_inventory_levels_data(client_id, "combined", start_date, end_date)
            combined_inventory = inventory_data.get('combined', {}).get('current_total_inventory', 0)
            
            if combined_inventory <= 0:
                logger.warning(f"⚠️ No combined inventory data available for trend calculation")
                return 0.0, 0.0
            
            # Calculate combined turnover rates for each half
            combined_first_half = combined_first_revenue / combined_inventory
            combined_second_half = combined_second_revenue / combined_inventory
            
            logger.debug(f"📊 Combined turnover trend: Revenue - First half: ${combined_first_revenue:.2f}, Second half: ${combined_second_revenue:.2f}")
            logger.debug(f"📊 Combined turnover rates - First half: {combined_first_half:.2f}, Second half: {combined_second_half:.2f}")
            
            return combined_first_half, combined_second_half
            
        except Exception as e:
            logger.error(f"❌ Error getting combined turnover trend: {str(e)}")
            return 0.0, 0.0
    
    async def get_inventory_levels_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get inventory levels data for timeline charts.
        Returns daily inventory data for the specified date range.
        """
        logger.info(f"📈 Getting inventory levels data for {client_id} - {platform} ({start_date} to {end_date})")
        
        tables = self._get_table_names(client_id)
        result = {}
        
        try:
            if platform in ["shopify", "combined"]:
                shopify_data = await self._get_platform_inventory_levels(
                    tables['shopify_products'], 'shopify', start_date, end_date
                )
                result['shopify'] = shopify_data
            
            if platform in ["amazon", "combined"]:
                amazon_data = await self._get_platform_inventory_levels(
                    tables['amazon_products'], 'amazon', start_date, end_date
                )
                result['amazon'] = amazon_data
            
            # For combined platform, merge timeline data
            if platform == "combined":
                result['combined'] = await self._combine_inventory_timelines(
                    result.get('shopify', {}), result.get('amazon', {})
                )
            
            logger.info(f"✅ Inventory levels data retrieved for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting inventory levels data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_platform_inventory_levels(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """Calculate inventory levels: inventory_at_start_date - cumulative units sold since start date"""
        try:
            db_client = get_admin_client()
            
            # Get current products
            products_response = db_client.table(table_name).select("*").execute()
            products = products_response.data or []
            
            # Get corresponding orders table
            if platform == "shopify":
                orders_table = table_name.replace('_shopify_products', '_shopify_orders')
            elif platform == "amazon":
                orders_table = table_name.replace('_amazon_products', '_amazon_orders')
            else:
                logger.error(f"❌ Unknown platform: {platform}")
                return {'inventory_levels_chart': [], 'current_total_inventory': 0, 'error': 'Unknown platform'}
            
            # Parse dates first
            if not start_date or not end_date:
                return {
                    'inventory_levels_chart': [],
                    'current_total_inventory': 0,
                    'error': 'Start date and end date are required'
                }
            
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)
            
            if not start_dt or not end_dt:
                return {
                    'inventory_levels_chart': [],
                    'current_total_inventory': 0,
                    'error': 'Invalid date format'
                }
            
            # Get ALL orders from start_date to NOW (to calculate inventory at start_date)
            now = datetime.now(timezone.utc)
            
            orders_query = db_client.table(orders_table).select("*")
            orders_query = orders_query.gte("created_at", start_dt.isoformat())
            orders_query = orders_query.lte("created_at", now.isoformat())
            
            orders_response = orders_query.execute()
            all_orders_since_start = orders_response.data or []
            
            logger.info(f"🔍 INVENTORY CALCULATION (NEW LOGIC):")
            logger.info(f"   📊 Products: {len(products)}, Orders since start: {len(all_orders_since_start)}")
            logger.info(f"   📊 Platform: {platform}, Date range: {start_date} to {end_date}")
            logger.info(f"   📊 Orders table: {orders_table}, Query: {start_date} to NOW")
            
            # Debug: Show sample orders if any exist
            if all_orders_since_start:
                logger.info(f"📋 Sample order data (first 3):")
                for i, order in enumerate(all_orders_since_start[:3]):
                    logger.info(f"   Order {i+1}: created_at={order.get('created_at')}")
                    logger.info(f"   Order {i+1}: available columns: {list(order.keys())}")
                    logger.info(f"   Order {i+1}: line_items_count={order.get('line_items_count')}")
                    logger.info(f"   Order {i+1}: lines_of_item={order.get('lines_of_item')}")
                    logger.info(f"   Order {i+1}: quantity={order.get('quantity')}")
                    logger.info(f"   Order {i+1}: raw_data_exists={bool(order.get('raw_data'))}")
                    
                    if order.get('raw_data'):
                        try:
                            raw_data = json.loads(order['raw_data']) if isinstance(order['raw_data'], str) else order['raw_data']
                            line_items = raw_data.get('line_items', [])
                            logger.info(f"   Order {i+1}: raw_data line_items_count={len(line_items)}")
                            if line_items and len(line_items) > 0:
                                first_item = line_items[0] if isinstance(line_items[0], dict) else {}
                                logger.info(f"   Order {i+1}: first_item_qty={first_item.get('quantity', 'N/A')}")
                        except Exception as e:
                            logger.info(f"   Order {i+1}: raw_data parse error: {e}")
                    logger.info("   " + "-" * 50)
            else:
                logger.warning(f"⚠️ NO ORDERS FOUND since {start_date}")
                logger.info(f"   Debug: Query was for table '{orders_table}' from {start_date} to NOW")
                
                # Debug: Check what orders actually exist in the database
                try:
                    all_orders_response = db_client.table(orders_table).select("*").limit(5).execute()
                    all_orders = all_orders_response.data or []
                    if all_orders:
                        logger.info(f"   📅 Sample order data from database:")
                        for i, order in enumerate(all_orders[:2]):
                            logger.info(f"   Order {i+1}: created_at={order.get('created_at', 'N/A')[:10]}")
                            logger.info(f"   Order {i+1}: columns: {list(order.keys())}")
                    else:
                        logger.warning(f"   ❌ NO ORDERS found in table '{orders_table}' at all!")
                except Exception as e:
                    logger.error(f"   ❌ Error checking order dates: {e}")
            
            # Step 1: Calculate current total inventory
            current_total_inventory = 0
            for product in products:
                if platform == "shopify":
                    raw_inventory = product.get('inventory_quantity')
                    if raw_inventory is None:
                        inventory = 0
                    elif isinstance(raw_inventory, str):
                        try:
                            inventory = int(float(raw_inventory)) if raw_inventory.strip() else 0
                        except (ValueError, AttributeError):
                            inventory = 0
                    else:
                        try:
                            inventory = int(float(raw_inventory))
                        except (ValueError, TypeError):
                            inventory = 0
                    inventory = max(0, inventory)
                elif platform == "amazon":
                    raw_quantity = product.get('quantity')
                    if raw_quantity is None:
                        inventory = 0
                    elif isinstance(raw_quantity, str):
                        try:
                            inventory = int(float(raw_quantity)) if raw_quantity.strip() else 0
                        except (ValueError, AttributeError):
                            inventory = 0
                    else:
                        try:
                            inventory = int(float(raw_quantity))
                        except (ValueError, TypeError):
                            inventory = 0
                    inventory = max(0, inventory)
                
                current_total_inventory += inventory
            
            logger.info(f"📦 Current total inventory: {current_total_inventory}")
            
            # Step 2: Calculate total units sold from start_date to NOW
            def extract_units_from_order(order):
                units_in_order = 0
                
                # Priority 1: Try lines_of_item column first (user suggestion)
                if order.get('lines_of_item') is not None:
                    try:
                        units_in_order = int(order.get('lines_of_item', 0))
                        if units_in_order > 0:
                            return units_in_order
                    except (ValueError, TypeError):
                        pass
                
                # Priority 2: Try line_items_count column
                if order.get('line_items_count') is not None:
                    try:
                        units_in_order = int(order.get('line_items_count', 0))
                        if units_in_order > 0:
                            return units_in_order
                    except (ValueError, TypeError):
                        pass
                
                # Priority 3: For Amazon, try quantity column
                if platform == "amazon" and order.get('quantity') is not None:
                    try:
                        units_in_order = int(order.get('quantity', 0))
                        if units_in_order > 0:
                            return units_in_order
                    except (ValueError, TypeError):
                        pass
                
                # Priority 4: Parse raw_data for Shopify
                if platform == "shopify":
                    raw_data = order.get('raw_data')
                    if raw_data:
                        try:
                            if isinstance(raw_data, str):
                                raw_order = json.loads(raw_data)
                            else:
                                raw_order = raw_data
                            
                            line_items = raw_order.get('line_items', [])
                            if isinstance(line_items, list):
                                for item in line_items:
                                    if isinstance(item, dict):
                                        quantity = int(item.get('quantity', 0) or 0)
                                        units_in_order += quantity
                                        
                            if units_in_order > 0:
                                return units_in_order
                        except Exception as e:
                            logger.debug(f"Error parsing raw_data: {e}")
                
                # Fallback: Default to 1 unit per order if nothing else works
                return 1
            
            # Calculate total units sold from start_date to NOW
            total_units_sold_since_start = 0
            units_extraction_debug = []
            
            for i, order in enumerate(all_orders_since_start):
                order_date = self._parse_date(order.get('created_at', ''))
                if order_date and order_date >= start_dt:
                    units = extract_units_from_order(order)
                    total_units_sold_since_start += units
                    
                    # Debug first 3 extractions
                    if i < 3:
                        units_extraction_debug.append({
                            'order_id': order.get('id', f'order_{i}'),
                            'date': order_date.strftime('%Y-%m-%d'),
                            'lines_of_item': order.get('lines_of_item'),
                            'line_items_count': order.get('line_items_count'),
                            'quantity': order.get('quantity'),
                            'extracted_units': units
                        })
            
            # Log extraction debugging
            if units_extraction_debug:
                logger.info(f"🔍 UNITS EXTRACTION DEBUG:")
                for debug_info in units_extraction_debug:
                    logger.info(f"   Order {debug_info['order_id']} ({debug_info['date']}):")
                    logger.info(f"     lines_of_item: {debug_info['lines_of_item']}")
                    logger.info(f"     line_items_count: {debug_info['line_items_count']}")
                    logger.info(f"     quantity: {debug_info['quantity']}")
                    logger.info(f"     ✅ EXTRACTED UNITS: {debug_info['extracted_units']}")
                    logger.info("     " + "-" * 30)
            
            # Step 3: Calculate inventory at start_date
            inventory_at_start_date = current_total_inventory + total_units_sold_since_start
            
            logger.info(f"🧮 CALCULATION BREAKDOWN:")
            logger.info(f"   📊 Current inventory: {current_total_inventory}")
            logger.info(f"   🛒 Units sold since {start_date}: {total_units_sold_since_start}")
            logger.info(f"   📦 Inventory at {start_date}: {inventory_at_start_date}")
            
            # Step 4: Calculate daily sales within the selected period
            daily_sales_in_period = {}
            period_orders_processed = 0
            
            for order in all_orders_since_start:
                order_date = self._parse_date(order.get('created_at', ''))
                if order_date and start_dt <= order_date <= end_dt:
                    date_key = order_date.strftime('%Y-%m-%d')
                    units = extract_units_from_order(order)
                    daily_sales_in_period[date_key] = daily_sales_in_period.get(date_key, 0) + units
                    period_orders_processed += 1
            
            logger.info(f"📊 PERIOD SALES SUMMARY:")
            logger.info(f"   - Orders in selected period: {period_orders_processed}")
            logger.info(f"   - Days with sales: {len(daily_sales_in_period)}")
            logger.info(f"   - Total period sales: {sum(daily_sales_in_period.values())}")
            if daily_sales_in_period:
                logger.info(f"   - Sample daily sales: {dict(list(daily_sales_in_period.items())[:3])}")
            else:
                logger.warning(f"   ⚠️ NO SALES found in period {start_date} to {end_date}")
            
            # Step 5: Create timeline with correct cumulative calculation
            timeline_data = []
            current_date = start_dt
            cumulative_units_sold_from_start = 0
            
            while current_date <= end_dt:
                date_key = current_date.strftime('%Y-%m-%d')
                units_sold_today = daily_sales_in_period.get(date_key, 0)
                
                # Add today's sales to cumulative total from start_date
                cumulative_units_sold_from_start += units_sold_today
                
                # Calculate inventory: inventory_at_start_date - cumulative_units_sold_from_start_date
                inventory_level_today = max(0, inventory_at_start_date - cumulative_units_sold_from_start)
                
                timeline_data.append({
                    'date': date_key,
                    'inventory_level': inventory_level_today,
                    'value': inventory_level_today
                })
                current_date += timedelta(days=1)
            
            logger.info(f"📊 Sample timeline calculations:")
            cumulative_debug = 0
            for i in range(min(5, len(timeline_data))):
                item = timeline_data[i]
                date = item['date']
                units_today = daily_sales_in_period.get(date, 0)
                cumulative_debug += units_today
                inventory = item['inventory_level']
                logger.info(f"   {date}: {inventory_at_start_date} - {cumulative_debug} = {inventory} (sold today: {units_today})")
            
            return {
                'inventory_levels_chart': timeline_data,
                'current_total_inventory': current_total_inventory,
                'inventory_at_start_date': inventory_at_start_date,
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'data_points': len(timeline_data),
                    'calculation_method': 'start_date_inventory_minus_cumulative_sales_from_start',
                    'total_units_sold_in_period': sum(daily_sales_in_period.values()),
                    'total_units_sold_since_start': total_units_sold_since_start,
                    'daily_sales_calculated': len(daily_sales_in_period)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting {platform} inventory levels: {str(e)}")
            return {
                'inventory_levels_chart': [],
                'current_total_inventory': 0,
                'error': str(e)
            }


    
    async def _combine_inventory_timelines(self, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Combine inventory timelines from both platforms"""
        try:
            shopify_timeline = shopify_data.get('inventory_levels_chart', [])
            amazon_timeline = amazon_data.get('inventory_levels_chart', [])
            
            # Create combined timeline by merging data by date
            combined_timeline = {}
            
            for item in shopify_timeline:
                date = item['date']
                combined_timeline[date] = combined_timeline.get(date, 0) + item['inventory_level']
            
            for item in amazon_timeline:
                date = item['date']
                combined_timeline[date] = combined_timeline.get(date, 0) + item['inventory_level']
            
            # Convert back to list format
            timeline_data = [
                {
                    'date': date,
                    'inventory_level': level,
                    'value': level
                }
                for date, level in sorted(combined_timeline.items())
            ]
            
            return {
                'inventory_levels_chart': timeline_data,
                'current_total_inventory': timeline_data[-1]['inventory_level'] if timeline_data else 0,
                'combined': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error combining inventory timelines: {str(e)}")
            return {
                'inventory_levels_chart': [],
                'current_total_inventory': 0,
                'error': str(e)
            }
    
    async def get_inventory_turnover_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get inventory turnover data for the specified period with within-period trend analysis"""
        logger.info(f"🔄 Getting inventory turnover data for {client_id} - {platform}")
        
        try:
            # Get sales and inventory data
            sales_data = await self.get_total_sales_data(client_id, platform, start_date, end_date)
            inventory_data = await self.get_inventory_levels_data(client_id, platform, start_date, end_date)
            
            # Calculate period days for trend analysis
            period_days = 30  # default period
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                if start_dt and end_dt:
                    period_days = (end_dt - start_dt).days + 1  # Include both start and end dates
            
            result = {}
            
            if platform == "combined":
                # Calculate combined turnover
                total_revenue = sales_data.get('combined', {}).get('total_revenue', 0)
                total_inventory = inventory_data.get('combined', {}).get('current_total_inventory', 0)
                
                turnover_rate = total_revenue / total_inventory if total_inventory > 0 else 0
                avg_days_to_sell = 365 / turnover_rate if turnover_rate > 0 else 999
                
                # Get within-period trend for combined platforms
                first_half_turnover, second_half_turnover = await self._get_combined_turnover_trend(
                    client_id, start_date, end_date, period_days
                )
                
                result = {
                    'inventory_turnover_ratio': round(turnover_rate, 2),
                    'avg_days_to_sell': round(avg_days_to_sell, 1),
                    'total_revenue': total_revenue,
                    'total_inventory_value': total_inventory,
                    'fast_moving_items': 0,  # TODO: Calculate based on individual SKU performance
                    'turnover_comparison': {
                        'first_half_turnover_rate': round(first_half_turnover, 2),
                        'second_half_turnover_rate': round(second_half_turnover, 2),
                        'growth_rate': ((second_half_turnover - first_half_turnover) / first_half_turnover) * 100 if first_half_turnover > 0 else 0
                    },
                    'period_info': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'days': period_days
                    }
                }
            else:
                # Calculate for specific platform
                platform_sales = sales_data.get(platform, {})
                platform_inventory = inventory_data.get(platform, {})
                
                revenue = platform_sales.get('total_sales_30_days', {}).get('revenue', 0)
                inventory = platform_inventory.get('current_total_inventory', 0)
                
                turnover_rate = revenue / inventory if inventory > 0 else 0
                avg_days_to_sell = 365 / turnover_rate if turnover_rate > 0 else 999
                
                # Get within-period turnover trend
                first_half_turnover, second_half_turnover = await self._get_platform_turnover_trend(
                    client_id, platform, start_date, end_date, period_days
                )
                
                result = {
                    'inventory_turnover_ratio': round(turnover_rate, 2),
                    'avg_days_to_sell': round(avg_days_to_sell, 1),
                    'total_revenue': revenue,
                    'total_inventory_value': inventory,
                    'fast_moving_items': 0,
                    'turnover_comparison': {
                        'first_half_turnover_rate': round(first_half_turnover, 2),
                        'second_half_turnover_rate': round(second_half_turnover, 2),
                        'growth_rate': ((second_half_turnover - first_half_turnover) / first_half_turnover) * 100 if first_half_turnover > 0 else 0
                    },
                    'period_info': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'days': period_days
                    }
                }
            
            logger.info(f"✅ Inventory turnover data calculated for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting inventory turnover data: {str(e)}")
            return {
                'inventory_turnover_ratio': 0,
                'avg_days_to_sell': 999,
                'total_revenue': 0,
                'total_inventory_value': 0,
                'fast_moving_items': 0,
                'turnover_comparison': {
                    'first_half_turnover_rate': 0,
                    'second_half_turnover_rate': 0,
                    'growth_rate': 0
                },
                'error': str(e)
            }
    
    async def get_days_of_stock_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get days of stock remaining data"""
        logger.info(f"📅 Getting days of stock data for {client_id} - {platform}")
        
        try:
            # Get sales velocity and current inventory
            sales_data = await self.get_total_sales_data(client_id, platform, start_date, end_date)
            inventory_data = await self.get_inventory_levels_data(client_id, platform, start_date, end_date)
            
            result = {}
            
            if platform == "combined":
                total_units_sold = (
                    sales_data.get('shopify', {}).get('total_sales_30_days', {}).get('units', 0) +
                    sales_data.get('amazon', {}).get('total_sales_30_days', {}).get('units', 0)
                )
                total_inventory = inventory_data.get('combined', {}).get('current_total_inventory', 0)
            else:
                total_units_sold = sales_data.get(platform, {}).get('total_sales_30_days', {}).get('units', 0)
                total_inventory = inventory_data.get(platform, {}).get('current_total_inventory', 0)
            
            # Calculate daily sales velocity
            period_days = 30  # default
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                if start_dt and end_dt:
                    period_days = max((end_dt - start_dt).days, 1)
            
            daily_sales_velocity = total_units_sold / period_days if period_days > 0 else 0
            days_of_stock = total_inventory / max(daily_sales_velocity, 1) if daily_sales_velocity > 0 else 999
            
            # Categorize stock levels
            low_stock_count = 1 if days_of_stock < 7 else 0
            out_of_stock_count = 1 if total_inventory == 0 else 0
            overstock_count = 1 if days_of_stock > 90 else 0
            
            result = {
                'avg_days_of_stock': round(days_of_stock, 1),
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'overstock_count': overstock_count,
                'daily_sales_velocity': round(daily_sales_velocity, 2),
                'current_inventory': total_inventory,
                'period_days': period_days
            }
            
            logger.info(f"✅ Days of stock data calculated for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting days of stock data: {str(e)}")
            return {"error": str(e)}

    async def get_units_sold_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get units sold data using real orders data with CONSISTENT date filtering"""
        logger.info(f"📊 UNITS SOLD REQUEST - Getting data for {client_id} - {platform} ({start_date} to {end_date})")
        
        tables = self._get_table_names(client_id)
        logger.info(f"📊 UNITS SOLD - Tables available: {tables}")
        result = {}
        
        try:
            if platform in ["shopify", "combined"]:
                shopify_data = await self._get_platform_units_sold(
                    tables['shopify_orders'], 'shopify', start_date, end_date
                )
                result['shopify'] = shopify_data
            
            if platform in ["amazon", "combined"]:
                amazon_data = await self._get_platform_units_sold(
                    tables['amazon_orders'], 'amazon', start_date, end_date
                )
                result['amazon'] = amazon_data
            
            # For combined platform, merge the data
            if platform == "combined":
                shopify_chart = result.get('shopify', {}).get('units_sold_chart', [])
                amazon_chart = result.get('amazon', {}).get('units_sold_chart', [])
                
                # Combine charts by date
                combined_data = {}
                for item in shopify_chart + amazon_chart:
                    date = item['date']
                    if date not in combined_data:
                        combined_data[date] = {'date': date, 'units_sold': 0, 'value': 0}
                    combined_data[date]['units_sold'] += item['units_sold']
                    combined_data[date]['value'] += item['value']
                
                combined_chart = sorted(combined_data.values(), key=lambda x: x['date'])
                result['combined'] = {
                    'units_sold_chart': combined_chart,
                    'total_units_sold': sum(item['units_sold'] for item in combined_chart)
                }
            
            # Log final summary
            logger.info(f"✅ UNITS SOLD FINAL RESULT for {platform}:")
            for platform_key, platform_result in result.items():
                if isinstance(platform_result, dict) and 'units_sold_chart' in platform_result:
                    chart_data = platform_result['units_sold_chart']
                    total_units = sum(item['units_sold'] for item in chart_data) if chart_data else 0
                    logger.info(f"   📊 {platform_key}: {len(chart_data)} data points, {total_units} total units")
                    if chart_data:
                        logger.info(f"      First: {chart_data[0]}")
                        logger.info(f"      Last: {chart_data[-1]}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting units sold data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_platform_units_sold(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """Get REAL units sold data using orders data with SAME date filtering as total sales"""
        try:
            db_client = get_admin_client()
            
            # Build query with date filtering (IDENTICAL to total sales function)
            query = db_client.table(table_name).select("*")
            
            # Add date filtering if provided (CONSISTENT with total sales)
            if start_date:
                start_dt = self._parse_date(start_date)
                if start_dt:
                    query = query.gte("created_at", start_dt.isoformat())
                    logger.info(f"📅 UNITS SOLD - Filtering orders >= {start_dt.isoformat()}")
            
            if end_date:
                end_dt = self._parse_date(end_date)
                if end_dt:
                    query = query.lte("created_at", end_dt.isoformat())
                    logger.info(f"📅 UNITS SOLD - Filtering orders <= {end_dt.isoformat()}")
            
            # Execute query with filters
            orders_response = query.execute()
            orders = orders_response.data or []
            
            logger.info(f"🔍 UNITS SOLD DEBUG - Platform: {platform}, Orders: {len(orders)}")
            
            # Sample a few orders to understand the data structure
            if orders:
                logger.info(f"📊 SAMPLE ORDER DATA STRUCTURE:")
                for i, order in enumerate(orders[:3]):  # Sample first 3 orders
                    logger.info(f"   Order {i+1}: {list(order.keys())}")
                    logger.info(f"   Order {i+1} sample values:")
                    logger.info(f"     - order_number: {order.get('order_number', 'N/A')}")
                    logger.info(f"     - created_at: {order.get('created_at', 'N/A')}")
                    logger.info(f"     - total_price: {order.get('total_price', 'N/A')}")
                    
                    if platform == "shopify":
                        logger.info(f"     - line_items_count: {order.get('line_items_count', 'N/A')}")
                        raw_data = order.get('raw_data')
                        if raw_data:
                            try:
    
                                if isinstance(raw_data, str):
                                    parsed = json.loads(raw_data)
                                else:
                                    parsed = raw_data
                                line_items = parsed.get('line_items', [])
                                logger.info(f"     - raw_data line_items count: {len(line_items)}")
                                if line_items and isinstance(line_items, list) and len(line_items) > 0:
                                    first_item = line_items[0]
                                    if isinstance(first_item, dict):
                                        logger.info(f"     - first line_item quantity: {first_item.get('quantity', 'N/A')}")
                                    else:
                                        logger.info(f"     - first line_item not a dict: {type(first_item)}")
                                else:
                                    logger.info(f"     - no valid line_items found")
                            except Exception as e:
                                logger.info(f"     - raw_data parsing error: {e}")
                        else:
                            logger.info(f"     - raw_data: None")
                    elif platform == "amazon":
                        logger.info(f"     - quantity: {order.get('quantity', 'N/A')}")
                    
                    if i >= 2:  # Only show first 3 orders
                        break
            else:
                logger.warning(f"⚠️ NO ORDERS FOUND in table {table_name} after date filtering!")
                logger.warning(f"⚠️ Check if orders exist in the date range {start_date} to {end_date}")
            
            timeline_data = []
            
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                
                logger.info(f"📅 PARSED DATE RANGE: {start_dt} to {end_dt}")
                
                # Check if dates are realistic
                from datetime import datetime
                current_year = datetime.now().year
                if start_dt and start_dt.year > current_year:
                    logger.warning(f"⚠️ FUTURE DATE DETECTED: {start_dt.year} > {current_year}")
                    logger.warning(f"⚠️ You selected dates in {start_dt.year} - check if you have orders in the future!")
                
                if start_dt and end_dt:
                    # Calculate daily sales from filtered orders
                    daily_sales = await self._calculate_daily_sales_from_orders(orders, platform, start_dt, end_dt)
                    
                    # Convert daily sales to chart format
                    current_date = start_dt
                    while current_date <= end_dt:
                        date_str = current_date.strftime('%Y-%m-%d')
                        units_sold = daily_sales.get(date_str, 0)
                        
                        timeline_data.append({
                            'date': date_str,
                            'units_sold': units_sold,
                            'value': units_sold
                        })
                        current_date += timedelta(days=1)
            
            return {
                'units_sold_chart': timeline_data,
                'total_units_sold': sum(item['units_sold'] for item in timeline_data),
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'data_points': len(timeline_data),
                    'calculation_method': 'real_orders_data'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting {platform} units sold: {str(e)}")
            return {
                'units_sold_chart': [],
                'total_units_sold': 0,
                'error': str(e)
            }

    async def _calculate_daily_sales_from_orders(self, orders: List[Dict], platform: str, start_dt: datetime, end_dt: datetime) -> Dict[str, int]:
        """Calculate daily sales quantities from ALREADY FILTERED orders data"""
        daily_sales = {}
        
        # Initialize all dates with 0 sales
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_sales[date_str] = 0
            current_date += timedelta(days=1)
        
        logger.info(f"🔍 Processing {len(orders)} FILTERED orders for daily sales calculation ({platform})")
        
        orders_processed = 0
        orders_with_units = 0
        total_units_extracted = 0
        
        # Since orders are already filtered by date at the database level, ALL orders should be in range
        for order in orders:
            orders_processed += 1
            try:
                # Parse order date
                created_at = order.get('created_at')
                if not created_at:
                    if orders_processed <= 5:  # Log first few
                        logger.info(f"📅 Order {orders_processed}: No created_at date")
                    continue
                    
                order_date = self._parse_date(created_at)
                if not order_date:
                    if orders_processed <= 5:  # Log first few
                        logger.info(f"📅 Order {orders_processed}: Could not parse date {created_at}")
                    continue
                
                date_str = order_date.strftime('%Y-%m-%d')
                units_sold = 0
                
                if orders_processed <= 5:  # Log first few orders for debugging
                    logger.info(f"📦 Processing Order {orders_processed}: {order.get('order_number', 'Unknown')} on {date_str}")
                
                if platform == "shopify":
                    # Extract line items from Shopify orders with comprehensive fallbacks
                    raw_data = order.get('raw_data')
                    if raw_data:
                        try:

                            if isinstance(raw_data, str):
                                raw_order = json.loads(raw_data)
                            else:
                                raw_order = raw_data
                            
                            line_items = raw_order.get('line_items', [])
                            if isinstance(line_items, list) and len(line_items) > 0:
                                for item in line_items:
                                    if isinstance(item, dict):
                                        quantity = int(item.get('quantity', 0) or 0)
                                        units_sold += quantity
                                        if orders_processed <= 5:
                                            logger.info(f"     🛍️ Line item quantity: {quantity}")
                            else:
                                # No line items in raw_data, use fallback
                                fallback_count = int(order.get('line_items_count', 1) or 1)
                                units_sold = fallback_count
                                if orders_processed <= 5:
                                    logger.info(f"     🛍️ Using fallback line_items_count: {fallback_count}")
                        except Exception as e:
                            logger.debug(f"Error parsing Shopify order {order.get('order_number')}: {e}")
                            # Fallback to line_items_count if available
                            fallback_count = int(order.get('line_items_count', 1) or 1)
                            units_sold = fallback_count
                            if orders_processed <= 5:
                                logger.info(f"     🛍️ Error fallback line_items_count: {fallback_count}")
                    else:
                        # No raw_data, try other fields
                        fallback_count = int(order.get('line_items_count', 1) or 1)
                        units_sold = fallback_count
                        if orders_processed <= 5:
                            logger.info(f"     🛍️ No raw_data, using line_items_count: {fallback_count}")
                    
                    # Alternative: Check if there's a direct units/quantity field
                    if units_sold == 0:
                        alt_quantity = order.get('quantity') or order.get('units') or order.get('total_quantity')
                        if alt_quantity:
                            units_sold = int(alt_quantity)
                            if orders_processed <= 5:
                                logger.info(f"     🛍️ Using alternative quantity field: {units_sold}")
                        
                elif platform == "amazon":
                    # Amazon orders have direct quantity field
                    units_sold = int(order.get('quantity', 1) or 1)
                    if orders_processed <= 5:
                        logger.info(f"     🛍️ Amazon quantity: {units_sold}")
                
                # Ensure we always count at least 1 unit per order (if we couldn't extract quantity)
                if units_sold == 0:
                    units_sold = 1
                    if orders_processed <= 5:
                        logger.info(f"     🛍️ Final fallback: counting as 1 unit")
                
                # Add to daily sales (since orders are pre-filtered, we know date is in range)
                if date_str in daily_sales:
                    daily_sales[date_str] += units_sold
                    total_units_extracted += units_sold
                    if units_sold > 0:
                        orders_with_units += 1
                        if orders_processed <= 5:  # Log first few
                            logger.info(f"   📊 Added {units_sold} units to {date_str} (total now: {daily_sales[date_str]})")
                else:
                    # This shouldn't happen since orders are pre-filtered, but log it
                    logger.warning(f"⚠️ Order date {date_str} not in expected range!")
                    
            except Exception as e:
                logger.debug(f"Error processing order for daily sales: {e}")
                continue
        
        # Log comprehensive summary
        non_zero_days = len([v for v in daily_sales.values() if v > 0])
        
        logger.info(f"📊 DAILY SALES CALCULATION SUMMARY:")
        logger.info(f"   📊 Total orders processed: {orders_processed}")
        logger.info(f"   📊 Orders with units: {orders_with_units}")
        logger.info(f"   📊 Total units extracted: {total_units_extracted}")
        logger.info(f"   📊 Active sales days: {non_zero_days}")
        
        if total_units_extracted == 0:
            logger.warning(f"⚠️ ZERO UNITS EXTRACTED! Possible issues:")
            logger.warning(f"   - Orders missing line_items or quantity data")
            logger.warning(f"   - Raw_data field malformed or empty")
            logger.warning(f"   - Quantity fields not where expected")
            
            if len(orders) > 0:
                logger.info(f"💡 DEBUGGING HINT:")
                logger.info(f"   You have {len(orders)} orders in the selected date range")
                logger.info(f"   But no units could be extracted from them")
                logger.info(f"   Check the order data structure and quantity fields")
        
        return daily_sales

    async def get_historical_comparison_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get historical comparison data with period-over-period analysis"""
        logger.info(f"📈 HISTORICAL COMPARISON REQUEST - Getting data for {client_id} - {platform} ({start_date} to {end_date})")
        
        tables = self._get_table_names(client_id)
        result = {}
        
        try:
            if platform in ["shopify", "combined"]:
                shopify_data = await self._get_platform_historical_comparison(
                    tables['shopify_orders'], 'shopify', start_date, end_date
                )
                result['shopify'] = shopify_data
            
            if platform in ["amazon", "combined"]:
                amazon_data = await self._get_platform_historical_comparison(
                    tables['amazon_orders'], 'amazon', start_date, end_date
                )
                result['amazon'] = amazon_data
            
            # For combined platform, merge the data
            if platform == "combined":
                shopify_chart = result.get('shopify', {}).get('comparison_chart', [])
                amazon_chart = result.get('amazon', {}).get('comparison_chart', [])
                
                # Combine charts by date
                combined_data = {}
                for item in shopify_chart + amazon_chart:
                    date = item['date']
                    if date not in combined_data:
                        combined_data[date] = {
                            'date': date, 
                            'current_period': 0, 
                            'previous_period': 0,
                            'value': 0
                        }
                    combined_data[date]['current_period'] += item['current_period']
                    combined_data[date]['previous_period'] += item['previous_period']
                    combined_data[date]['value'] = combined_data[date]['current_period']
                
                combined_chart = sorted(combined_data.values(), key=lambda x: x['date'])
                
                # Calculate combined totals
                total_current = sum(item['current_period'] for item in combined_chart)
                total_previous = sum(item['previous_period'] for item in combined_chart)
                growth_rate = ((total_current - total_previous) / total_previous) * 100 if total_previous > 0 else 0
                
                result['combined'] = {
                    'comparison_chart': combined_chart,
                    'total_current_period': total_current,
                    'total_previous_period': total_previous,
                    'growth_rate': round(growth_rate, 2)
                }
            
            logger.info(f"✅ HISTORICAL COMPARISON FINAL RESULT for {platform}:")
            for platform_key, platform_result in result.items():
                if isinstance(platform_result, dict) and 'comparison_chart' in platform_result:
                    chart_data = platform_result['comparison_chart']
                    current_total = platform_result.get('total_current_period', 0)
                    previous_total = platform_result.get('total_previous_period', 0)
                    logger.info(f"   📊 {platform_key}: {len(chart_data)} data points")
                    logger.info(f"      Current: ${current_total:.2f}, Previous: ${previous_total:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting historical comparison data: {str(e)}")
            return {"error": str(e)}

    async def _get_platform_historical_comparison(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """Get historical comparison data for a specific platform"""
        try:
            if not start_date or not end_date:
                logger.warning(f"❌ Historical comparison requires both start_date and end_date")
                return {'comparison_chart': [], 'total_current_period': 0, 'total_previous_period': 0, 'error': 'Missing date range'}
            
            db_client = get_admin_client()
            
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)
            
            if not start_dt or not end_dt:
                logger.warning(f"❌ Could not parse dates: {start_date}, {end_date}")
                return {'comparison_chart': [], 'total_current_period': 0, 'total_previous_period': 0, 'error': 'Invalid dates'}
            
            # Calculate period length
            period_length = (end_dt - start_dt).days + 1
            
            # Calculate previous period (same length, going backwards)
            previous_end_dt = start_dt - timedelta(days=1)
            previous_start_dt = previous_end_dt - timedelta(days=period_length - 1)
            
            logger.info(f"📅 HISTORICAL COMPARISON PERIODS:")
            logger.info(f"   Current: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')} ({period_length} days)")
            logger.info(f"   Previous: {previous_start_dt.strftime('%Y-%m-%d')} to {previous_end_dt.strftime('%Y-%m-%d')} ({period_length} days)")
            
            # Get current period orders
            current_query = db_client.table(table_name).select("*")
            current_query = current_query.gte("created_at", start_dt.isoformat()).lte("created_at", end_dt.isoformat())
            current_response = current_query.execute()
            current_orders = current_response.data or []
            
            # Get previous period orders
            previous_query = db_client.table(table_name).select("*")
            previous_query = previous_query.gte("created_at", previous_start_dt.isoformat()).lte("created_at", previous_end_dt.isoformat())
            previous_response = previous_query.execute()
            previous_orders = previous_response.data or []
            
            logger.info(f"📊 ORDERS FOUND:")
            logger.info(f"   Current period: {len(current_orders)} orders")
            logger.info(f"   Previous period: {len(previous_orders)} orders")
            
            # Calculate daily sales for both periods
            current_daily_sales = await self._calculate_daily_sales_from_orders(current_orders, platform, start_dt, end_dt)
            previous_daily_sales = await self._calculate_daily_sales_from_orders(previous_orders, platform, previous_start_dt, previous_end_dt)
            
            # Create comparison chart with aligned dates
            comparison_data = []
            current_date = start_dt
            previous_date = previous_start_dt
            
            while current_date <= end_dt:
                current_date_str = current_date.strftime('%Y-%m-%d')
                previous_date_str = previous_date.strftime('%Y-%m-%d')
                
                current_revenue = 0
                previous_revenue = 0
                
                # Calculate revenue from daily sales (using same logic as total sales)
                for order in current_orders:
                    order_date = self._parse_date(order.get('created_at'))
                    if order_date and order_date.strftime('%Y-%m-%d') == current_date_str:
                        current_revenue += float(order.get('total_price', 0) or 0)
                
                for order in previous_orders:
                    order_date = self._parse_date(order.get('created_at'))
                    if order_date and order_date.strftime('%Y-%m-%d') == previous_date_str:
                        previous_revenue += float(order.get('total_price', 0) or 0)
                
                comparison_data.append({
                    'date': current_date_str,
                    'current_period': current_revenue,
                    'previous_period': previous_revenue,
                    'value': current_revenue  # For chart compatibility
                })
                
                current_date += timedelta(days=1)
                previous_date += timedelta(days=1)
            
            # Calculate totals
            total_current = sum(item['current_period'] for item in comparison_data)
            total_previous = sum(item['previous_period'] for item in comparison_data)
            growth_rate = ((total_current - total_previous) / total_previous) * 100 if total_previous > 0 else 0
            
            logger.info(f"📊 COMPARISON SUMMARY:")
            logger.info(f"   Current period total: ${total_current:.2f}")
            logger.info(f"   Previous period total: ${total_previous:.2f}")
            logger.info(f"   Growth rate: {growth_rate:.1f}%")
            
            return {
                'comparison_chart': comparison_data,
                'total_current_period': total_current,
                'total_previous_period': total_previous,
                'growth_rate': round(growth_rate, 2),
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'period_length': period_length,
                    'previous_start': previous_start_dt.strftime('%Y-%m-%d'),
                    'previous_end': previous_end_dt.strftime('%Y-%m-%d'),
                    'calculation_method': 'period_over_period_revenue'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting {platform} historical comparison: {str(e)}")
            return {
                'comparison_chart': [],
                'total_current_period': 0,
                'total_previous_period': 0,
                'error': str(e)
            }


# Global instance
component_data_manager = ComponentDataManager()