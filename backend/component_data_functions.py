"""
Component-Specific Data Query Functions

This module provides functions to query database for specific component data
with date range and platform filtering. Each function handles a specific
component type and returns appropriately formatted data.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
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
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
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
        """Get inventory levels for a specific platform"""
        try:
            db_client = get_admin_client()
            query = db_client.table(table_name).select("*")
            response = query.execute()
            products = response.data or []
            
            # Generate timeline data based on current inventory levels
            # Note: This is simplified - in a real system you'd have historical inventory tracking
            timeline_data = []
            
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                
                if start_dt and end_dt:
                    current_date = start_dt
                    total_inventory = 0
                    
                    # Calculate total current inventory
                    for product in products:
                        if platform == "shopify":
                            inventory = int(product.get('inventory_quantity', 0) or 0)
                        elif platform == "amazon":
                            inventory = int(product.get('quantity', 0) or 0)
                        total_inventory += inventory
                    
                    # Generate daily data points based on current inventory
                    # NOTE: This uses current inventory as baseline since historical inventory tracking 
                    # is not implemented. For production use, implement proper historical inventory tables.
                    while current_date <= end_dt:
                        # Use current inventory as baseline for all dates in the period
                        # This is a simplification - real systems should track daily inventory changes
                        daily_inventory = total_inventory
                        
                        timeline_data.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'inventory_level': daily_inventory,
                            'value': daily_inventory
                        })
                        current_date += timedelta(days=1)
            
            return {
                'inventory_levels_chart': timeline_data,
                'current_total_inventory': timeline_data[-1]['inventory_level'] if timeline_data else 0,
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'data_points': len(timeline_data)
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


# Global instance
component_data_manager = ComponentDataManager()
