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
    
    def _get_available_inventory_for_platform(self, client_id: str, platform: str) -> int:
        """Get available inventory for a specific platform (total - outgoing/reserved)"""
        try:
            client = get_admin_client()
            table_names = self._get_table_names(client_id)
            available_inventory = 0
            
            if platform == "shopify":
                # Get Shopify products
                products_query = client.table(table_names['shopify_products']).select('sku, inventory_quantity')
                products_response = products_query.execute()
                products = products_response.data or []
                
                # Get unfulfilled Shopify orders for outgoing calculation
                orders_query = client.table(table_names['shopify_orders']).select('raw_data, financial_status, fulfillment_status')
                orders_response = orders_query.execute()
                orders = orders_response.data or []
                
                for product in products:
                    total_inventory = product.get('inventory_quantity', 0) or 0
                    sku = product.get('sku')
                    
                    # Calculate outgoing inventory (simplified - would need proper SKU matching)
                    outgoing = 0  # TODO: Implement proper SKU-specific outgoing calculation
                    
                    # Available = total - outgoing
                    product_available = max(0, total_inventory - outgoing)
                    available_inventory += product_available
                    
            elif platform == "amazon":
                # Get Amazon products  
                products_query = client.table(table_names['amazon_products']).select('sku, asin, quantity')
                products_response = products_query.execute()
                products = products_response.data or []
                
                for product in products:
                    total_inventory = product.get('quantity', 0) or 0
                    sku = product.get('sku') or product.get('asin')
                    
                    #  FIXED: Calculate Amazon outgoing using order_status and number_of_items_unshipped
                    outgoing = self._calculate_amazon_outgoing_for_sku(client_id, sku, platform) if sku else 0
                    
                    product_available = max(0, total_inventory - outgoing)
                    available_inventory += product_available
                    
            logger.info(f" {platform.upper()} Available Inventory: {available_inventory} units")
            return available_inventory
            
        except Exception as e:
            logger.error(f"Error calculating available inventory for {platform}: {e}")
            return 0

    def _calculate_average_inventory(self, current_inventory: int, units_sold: int, period_days: int = 30) -> float:
        """Calculate average inventory = (begin_inventory + end_inventory) / 2
        
        Returns the actual calculated average inventory value.
        Division by zero should be handled by the calling function.
        """
        # Current inventory is end_inventory
        end_inventory = current_inventory
        
        # Calculate begin_inventory = current + units sold during the period
        # This assumes inventory at period start = current inventory + units sold since then
        begin_inventory = current_inventory + units_sold
        
        avg_inventory = (begin_inventory + end_inventory) / 2
        
        logger.info(f" Avg Inventory: begin({current_inventory} + {units_sold}) + end({end_inventory}) / 2 = {avg_inventory}")
        logger.info(f" Logic: inventory at period start ≈ current({current_inventory}) + sold_since_then({units_sold}) = {begin_inventory}")
        
        # Return the actual calculated value - let calling functions handle zero cases appropriately
        return avg_inventory

    def _extract_units_from_order(self, order, platform: str):
        """Extract units from order using multiple fallback strategies"""
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
                    import json
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
                    pass
        
        # Priority 5: Try Amazon specific fields
        if platform == "amazon":
            if order.get('number_of_items_shipped') is not None:
                try:
                    units_in_order = int(order.get('number_of_items_shipped', 0))
                    if units_in_order > 0:
                        return units_in_order
                except (ValueError, TypeError):
                    pass
        
        # Final fallback: assume 1 unit if we have revenue
        if float(order.get('total_price', 0) or 0) > 0:
            return 1
            
        return 0

    def _calculate_amazon_outgoing_for_sku(self, client_id: str, sku: str, platform: str) -> int:
        """ NEW: Calculate outgoing inventory for Amazon SKU using order_status and number_of_items_unshipped"""
        if not sku or platform != "amazon":
            return 0
            
        try:
            client = get_admin_client()
            table_names = self._get_table_names(client_id)
            
            # Get recent Amazon orders that are not yet shipped
            orders_query = client.table(table_names['amazon_orders']).select('order_id, order_status, number_of_items_unshipped, number_of_items_shipped, raw_data')
            orders_query = orders_query.neq('order_status', 'shipped')  # Only unshipped orders
            orders_query = orders_query.limit(20)  # Limit for performance
            
            orders_response = orders_query.execute()
            orders = orders_response.data or []
            
            outgoing = 0
            
            for order in orders:
                try:
                    # Amazon uses number_of_items_unshipped for pending items
                    unshipped_items = order.get('number_of_items_unshipped', 0) or 0
                    
                    # If we don't have unshipped count, estimate from total items
                    if unshipped_items == 0:
                        total_items = order.get('number_of_items_shipped', 0) or 0
                        total_items += order.get('number_of_items_unshipped', 0) or 0
                        # If order is not shipped, assume all items are unshipped
                        if total_items > 0:
                            unshipped_items = total_items
                        else:
                            unshipped_items = 1  # Conservative estimate
                    
                    # TODO: Ideally, we'd parse raw_data to match specific SKUs in order line items
                    # For now, attribute proportionally if this order contains our SKU
                    # This is a simplified approach - in practice, you'd want to parse order line items
                    if unshipped_items > 0:
                        outgoing += unshipped_items
                        
                except Exception as e:
                    logger.debug(f"Error processing Amazon order for outgoing calculation: {e}")
                    continue
            
            logger.info(f" Amazon SKU {sku} outgoing inventory: {outgoing} units from {len(orders)} unshipped orders")
            return outgoing
            
        except Exception as e:
            logger.error(f"Error calculating Amazon outgoing for SKU {sku}: {e}")
            return 0

    def _is_order_fulfilled(self, order: Dict) -> bool:
        """Check if order should be counted for sales based on platform-specific status rules"""
        platform = order.get('platform', '').lower()
        
        if platform == 'shopify':
            # Shopify: financial_status = 'paid' AND fulfillment_status = 'fulfilled'
            financial_status = (order.get('financial_status', '') or '').lower()
            fulfillment_status = (order.get('fulfillment_status', '') or '').lower()
            return financial_status == 'paid' and fulfillment_status == 'fulfilled'
        
        elif platform == 'amazon':
            # Amazon: order_status = 'shipped'
            order_status = (order.get('order_status', '') or '').lower()
            return order_status == 'shipped'
        
        else:
            # For mixed data or unknown platform, try to detect from fields
            if 'financial_status' in order and 'fulfillment_status' in order:
                # Likely Shopify
                financial_status = (order.get('financial_status', '') or '').lower()
                fulfillment_status = (order.get('fulfillment_status', '') or '').lower()
                return financial_status == 'paid' and fulfillment_status == 'fulfilled'
            elif 'order_status' in order:
                # Likely Amazon
                order_status = (order.get('order_status', '') or '').lower()
                return order_status == 'shipped'
            else:
                # Fallback: include all orders if we can't determine platform
                logger.warning(f"Could not determine platform for order {order.get('order_id', 'unknown')}, including in sales")
                return True
    
    async def get_total_sales_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get total sales data for a specific platform and date range.
        Sums all order prices for the specified period.
        """
        logger.info(f" Getting total sales data for {client_id} - {platform} ({start_date} to {end_date})")
        
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
            
            logger.info(f" Total sales data retrieved for {platform}")
            return result
            
        except Exception as e:
            logger.error(f" Error getting total sales data: {str(e)}")
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
            total_orders = 0  # Count only fulfilled orders
            fulfilled_orders = 0
            filtered_orders = 0
            total_units = 0
            
            for order in orders:
                #  NEW: Check if order should be counted based on fulfillment status
                if self._is_order_fulfilled(order):
                    fulfilled_orders += 1
                    
                    #  FIXED: Use proven units extraction method for all platforms
                    order_value = float(order.get('total_price', 0) or 0)
                    total_revenue += order_value
                    
                    # Extract units using the proven method from inventory levels calculation
                    order_units = self._extract_units_from_order(order, platform)
                    total_units += order_units
                    
                    if order_units > 0:
                        logger.debug(f" {platform.capitalize()} order: ${order_value:.2f}, {order_units} units")
                else:
                    filtered_orders += 1
            
            total_orders = fulfilled_orders  # Only count fulfilled orders
            
            #  EXPLICIT LOGGING: Debug values for zero inventory cases
            logger.info(f" {platform} sales calculation: {len(orders)} total orders, {fulfilled_orders} fulfilled, ${total_revenue:.2f} revenue, {total_units} units")
            
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
            
            # Calculate daily averages for consistent comparison
            first_half_days = max(period_days // 2, 1)
            second_half_days = max(period_days - first_half_days, 1)
            
            first_half_avg_revenue = first_half_revenue / first_half_days
            second_half_avg_revenue = second_half_revenue / second_half_days
            
            # Log filtering results
            logger.info(f" {platform.upper()} SALES FILTERING: Fulfilled: {fulfilled_orders}, Filtered: {filtered_orders}, Revenue: ${total_revenue:.2f}")
            
            return {
                'total_sales_30_days': {
                    'revenue': total_revenue,
                    'orders': total_orders,
                    'units': total_units
                },
                'sales_comparison': {
                    'first_half_avg_revenue': first_half_avg_revenue,
                    'second_half_avg_revenue': second_half_avg_revenue,
                    'growth_rate': ((second_half_avg_revenue - first_half_avg_revenue) / first_half_avg_revenue) * 100 if first_half_avg_revenue > 0 else 0
                },
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': period_days
                }
            }
            
        except Exception as e:
            logger.error(f" Error getting {platform} sales data: {str(e)}")
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
            
            logger.debug(f" Within-period trend for {platform}: First half: ${first_half_revenue}, Second half: ${second_half_revenue}")
            
            return first_half_revenue, second_half_revenue
            
        except Exception as e:
            logger.error(f" Error getting within-period trend: {str(e)}")
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
                logger.warning(f" No inventory data available for {platform} trend calculation")
                return 0.0, 0.0
            
            # Calculate turnover rates for each half
            # Note: Using revenue for trend to show revenue acceleration/deceleration (different from main units-based turnover)
            first_half_turnover = first_half_revenue / inventory_value if inventory_value > 0 else 0
            second_half_turnover = second_half_revenue / inventory_value if inventory_value > 0 else 0
            
            logger.debug(f" Turnover trend for {platform}: Revenue trend - First half: ${first_half_revenue:.2f}, Second half: ${second_half_revenue:.2f}")
            logger.debug(f" Turnover rates - First half: {first_half_turnover:.2f}, Second half: {second_half_turnover:.2f}")
            
            return first_half_turnover, second_half_turnover
            
        except Exception as e:
            logger.error(f" Error getting platform turnover trend: {str(e)}")
            return 0.0, 0.0
    
    async def _get_combined_turnover_trend(self, client_id: str, start_date: Optional[str], end_date: Optional[str], period_days: int, combined_inventory: int) -> tuple[float, float]:
        """Get combined turnover rates for first half and second half of the selected period"""
        try:
            #  FIXED: Use passed inventory to ensure consistency and avoid duplicate data calls
            if combined_inventory <= 0:
                logger.warning(f" No combined inventory data available for trend calculation (inventory: {combined_inventory})")
                return 0.0, 0.0
            
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
            
            # Calculate combined turnover rates for each half using consistent inventory data
            combined_first_half = combined_first_revenue / combined_inventory
            combined_second_half = combined_second_revenue / combined_inventory
            
            logger.debug(f" Combined turnover trend: Revenue - First half: ${combined_first_revenue:.2f}, Second half: ${combined_second_revenue:.2f}")
            logger.debug(f" Combined inventory: {combined_inventory} (Amazon 0 products case handled)")
            logger.debug(f" Combined turnover rates - First half: {combined_first_half:.2f}, Second half: {combined_second_half:.2f}")
            
            return combined_first_half, combined_second_half
            
        except Exception as e:
            logger.error(f" Error getting combined turnover trend: {str(e)}")
            return 0.0, 0.0
    
    async def get_inventory_levels_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get inventory levels data for timeline charts.
        Returns daily inventory data for the specified date range.
        """
        logger.info(f" Getting inventory levels data for {client_id} - {platform} ({start_date} to {end_date})")
        
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
            
            logger.info(f" Inventory levels data retrieved for {platform}")
            return result
            
        except Exception as e:
            logger.error(f" Error getting inventory levels data: {str(e)}")
            return {"error": str(e)}
    
    async def _get_platform_inventory_levels(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """Calculate inventory levels: inventory_at_start_date - cumulative units sold since start date"""
        try:
            db_client = get_admin_client()
            
            # Get current products
            products_response = db_client.table(table_name).select("*").execute()
            products = products_response.data or []
            
            #  CRITICAL: If no products exist, return empty inventory levels immediately
            if not products:
                logger.info(f" No products found in {table_name} for {platform} - returning empty inventory levels")
                
                # Generate empty timeline for the date range
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                
                if not start_dt or not end_dt:
                    return {
                        'inventory_levels_chart': [],
                        'current_total_inventory': 0,
                        'error': 'Invalid date format'
                    }
                
                timeline_data = []
                current_date = start_dt
                while current_date <= end_dt:
                    timeline_data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'inventory_level': 0,
                        'value': 0
                    })
                    current_date += timedelta(days=1)
                
                return {
                    'inventory_levels_chart': timeline_data,
                    'current_total_inventory': 0,
                    'inventory_at_start_date': 0,
                    'period_info': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'data_points': len(timeline_data),
                        'calculation_method': 'no_products_empty_inventory',
                        'total_units_sold_in_period': 0,
                        'total_units_sold_since_start': 0,
                        'daily_sales_calculated': 0
                    }
                }
            
            # Get corresponding orders table
            if platform == "shopify":
                orders_table = table_name.replace('_shopify_products', '_shopify_orders')
            elif platform == "amazon":
                orders_table = table_name.replace('_amazon_products', '_amazon_orders')
            else:
                logger.error(f" Unknown platform: {platform}")
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
            
            logger.info(f" INVENTORY CALCULATION (NEW LOGIC):")
            logger.info(f"    Products: {len(products)}, Orders since start: {len(all_orders_since_start)}")
            logger.info(f"    Platform: {platform}, Date range: {start_date} to {end_date}")
            logger.info(f"    Orders table: {orders_table}, Query: {start_date} to NOW")
            
            # Debug: Show sample orders if any exist
            if all_orders_since_start:
                logger.info(f" Sample order data (first 3):")
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
                logger.warning(f" NO ORDERS FOUND since {start_date}")
                logger.info(f"   Debug: Query was for table '{orders_table}' from {start_date} to NOW")
                
                # Debug: Check what orders actually exist in the database
                try:
                    all_orders_response = db_client.table(orders_table).select("*").limit(5).execute()
                    all_orders = all_orders_response.data or []
                    if all_orders:
                        logger.info(f"    Sample order data from database:")
                        for i, order in enumerate(all_orders[:2]):
                            logger.info(f"   Order {i+1}: created_at={order.get('created_at', 'N/A')[:10]}")
                            logger.info(f"   Order {i+1}: columns: {list(order.keys())}")
                    else:
                        logger.warning(f"    NO ORDERS found in table '{orders_table}' at all!")
                except Exception as e:
                    logger.error(f"    Error checking order dates: {e}")
            
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
            
            logger.info(f" Current total inventory: {current_total_inventory}")
            
            # Step 2: Calculate total units sold from start_date to NOW
            total_units_sold_since_start = 0
            units_extraction_debug = []
            
            for i, order in enumerate(all_orders_since_start):
                order_date = self._parse_date(order.get('created_at', ''))
                if order_date and order_date >= start_dt:
                    units = self._extract_units_from_order(order, platform)
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
                logger.info(f" UNITS EXTRACTION DEBUG:")
                for debug_info in units_extraction_debug:
                    logger.info(f"   Order {debug_info['order_id']} ({debug_info['date']}):")
                    logger.info(f"     lines_of_item: {debug_info['lines_of_item']}")
                    logger.info(f"     line_items_count: {debug_info['line_items_count']}")
                    logger.info(f"     quantity: {debug_info['quantity']}")
                    logger.info(f"      EXTRACTED UNITS: {debug_info['extracted_units']}")
                    logger.info("     " + "-" * 30)
            
            logger.info(f"🧮 CALCULATION BREAKDOWN:")
            logger.info(f"    Current inventory: {current_total_inventory}")
            logger.info(f"    Units sold since {start_date}: {total_units_sold_since_start}")
            logger.info(f"    Using BACKWARDS calculation approach (no need for start_date inventory)")
            
            # Step 4: Calculate daily sales within the selected period
            daily_sales_in_period = {}
            period_orders_processed = 0
            
            for order in all_orders_since_start:
                order_date = self._parse_date(order.get('created_at', ''))
                if order_date and start_dt <= order_date <= end_dt:
                    date_key = order_date.strftime('%Y-%m-%d')
                    units = self._extract_units_from_order(order, platform)
                    daily_sales_in_period[date_key] = daily_sales_in_period.get(date_key, 0) + units
                    period_orders_processed += 1
            
            logger.info(f" PERIOD SALES SUMMARY:")
            logger.info(f"   - Orders in selected period: {period_orders_processed}")
            logger.info(f"   - Days with sales: {len(daily_sales_in_period)}")
            logger.info(f"   - Total period sales: {sum(daily_sales_in_period.values())}")
            if daily_sales_in_period:
                logger.info(f"   - Sample daily sales: {dict(list(daily_sales_in_period.items())[:3])}")
            else:
                logger.warning(f"    NO SALES found in period {start_date} to {end_date}")
            
            #  Step 5: Create timeline working BACKWARDS from current date (user's suggested approach!)
            timeline_data = []
            
            logger.info(f" NEW BACKWARDS CALCULATION APPROACH:")
            logger.info(f"    Current inventory (today): {current_total_inventory}")
            logger.info(f"    Working backwards from {end_dt.date()} to {start_dt.date()}")
            
            # Generate list of dates from end to start (backwards)
            dates_backwards = []
            temp_date = end_dt.date()
            while temp_date >= start_dt.date():
                dates_backwards.append(temp_date)
                temp_date -= timedelta(days=1)
            
            # Calculate inventory for each day working backwards
            cumulative_units_sold_backwards = 0
            
            for i, date in enumerate(dates_backwards):
                date_key = date.strftime('%Y-%m-%d')
                units_sold_this_day = daily_sales_in_period.get(date_key, 0)
                
                if i == 0:
                    # Today (end_dt): use current inventory
                    inventory_level = current_total_inventory
                    logger.info(f"   {date_key} (today): {inventory_level} (current inventory)")
                else:
                    # Previous days: current_inventory + cumulative_units_sold_since_this_day
                    #  FIXED: Add current day's sales to cumulative for next iteration
                    # We need inventory BEFORE this day's sales were sold
                    inventory_level = current_total_inventory + cumulative_units_sold_backwards
                    
                    # Now add today's sales to cumulative for next iteration (going further back)
                    cumulative_units_sold_backwards += units_sold_this_day
                    
                    if i < 6:  # Debug first few days
                        days_back = i
                        cumulative_before_today = cumulative_units_sold_backwards - units_sold_this_day
                        logger.info(f"   {date_key} ({days_back} days ago): {current_total_inventory} + {cumulative_before_today} = {inventory_level}")
                        logger.info(f"      (Adding {units_sold_this_day} units sold this day to cumulative for next iteration)")
                
                timeline_data.append({
                    'date': date_key,
                    'inventory_level': max(0, inventory_level),  # Prevent negative inventory
                    'value': max(0, inventory_level)
                })
            
            # Sort timeline_data by date (ascending) since we built it backwards
            timeline_data.sort(key=lambda x: x['date'])
            
            logger.info(f" BACKWARDS calculation completed:")
            logger.info(f"   - Generated {len(timeline_data)} daily inventory points")
            logger.info(f"   - Sample final timeline (first 3 days):")
            for item in timeline_data[:3]:
                logger.info(f"     {item['date']}: {item['inventory_level']} units")
            
            return {
                'inventory_levels_chart': timeline_data,
                'current_total_inventory': current_total_inventory,
                'period_info': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'data_points': len(timeline_data),
                    'calculation_method': 'backwards_from_current_inventory_plus_daily_sales',
                    'total_units_sold_in_period': sum(daily_sales_in_period.values()),
                    'total_units_sold_since_start': total_units_sold_since_start,
                    'daily_sales_calculated': len(daily_sales_in_period)
                }
            }
            
        except Exception as e:
            logger.error(f" Error getting {platform} inventory levels: {str(e)}")
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
            
            # Calculate combined current inventory properly
            shopify_current = shopify_data.get('current_total_inventory', 0)
            amazon_current = amazon_data.get('current_total_inventory', 0)
            combined_current_inventory = shopify_current + amazon_current
            
            return {
                'inventory_levels_chart': timeline_data,
                'current_total_inventory': combined_current_inventory,
                'combined': True
            }
            
        except Exception as e:
            logger.error(f" Error combining inventory timelines: {str(e)}")
            return {
                'inventory_levels_chart': [],
                'current_total_inventory': 0,
                'error': str(e)
            }
    
    async def get_inventory_turnover_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get inventory turnover data for the specified period with within-period trend analysis"""
        logger.info(f" Getting inventory turnover data for {client_id} - {platform}")
        
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
                #  FIXED: Use IDENTICAL data sources as individual calculations to ensure consistency
                # Get Shopify data using same method as individual Shopify calculation
                shopify_sales_data = await self.get_total_sales_data(client_id, "shopify", start_date, end_date)
                shopify_inventory_data = await self.get_inventory_levels_data(client_id, "shopify", start_date, end_date)
                
                # Get Amazon data using same method as individual Amazon calculation  
                amazon_sales_data = await self.get_total_sales_data(client_id, "amazon", start_date, end_date)
                amazon_inventory_data = await self.get_inventory_levels_data(client_id, "amazon", start_date, end_date)
                
                # Extract using IDENTICAL logic as individual calculations
                shopify_units = shopify_sales_data.get('shopify', {}).get('total_sales_30_days', {}).get('units', 0)
                shopify_revenue = shopify_sales_data.get('shopify', {}).get('total_sales_30_days', {}).get('revenue', 0)
                shopify_inventory = shopify_inventory_data.get('shopify', {}).get('current_total_inventory', 0)
                
                amazon_units = amazon_sales_data.get('amazon', {}).get('total_sales_30_days', {}).get('units', 0)
                amazon_revenue = amazon_sales_data.get('amazon', {}).get('total_sales_30_days', {}).get('revenue', 0)
                amazon_inventory = amazon_inventory_data.get('amazon', {}).get('current_total_inventory', 0)
                
                # Sum using identical sources  
                total_units_sold = shopify_units + amazon_units
                total_sales_revenue = shopify_revenue + amazon_revenue
                total_inventory = shopify_inventory + amazon_inventory
                
                #  DEBUG: Log combined platform values using new consistent data sources
                logger.info(f" COMBINED DEBUG: total_inventory={total_inventory} (Shopify: {shopify_inventory}, Amazon: {amazon_inventory})")
                logger.info(f" COMBINED DEBUG: total_sales_revenue=${total_sales_revenue:.2f} (Shopify: ${shopify_revenue:.2f}, Amazon: ${amazon_revenue:.2f})")
                logger.info(f" COMBINED DEBUG: total_units_sold={total_units_sold} (Shopify: {shopify_units}, Amazon: {amazon_units})")
                
                if amazon_inventory == 0:
                    logger.info(" COMBINED DEBUG: Amazon has 0 products - combined = Shopify only")
                
                #  CONSISTENCY CHECK: Log individual vs combined data comparison
                logger.info(f" CONSISTENCY: Shopify individual calculation will use: {shopify_units} units, {shopify_inventory} inventory")
                logger.info(f" CONSISTENCY: Amazon individual calculation will use: {amazon_units} units, {amazon_inventory} inventory")
                
                #  CRITICAL DEBUG: Check combined units vs revenue consistency
                if total_sales_revenue > 0 and total_units_sold == 0:
                    logger.warning(f" COMBINED CRITICAL ISSUE: Has revenue (${total_sales_revenue:.2f}) but 0 units!")
                    
                    # Try to estimate from orders using new consistent data sources
                    shopify_orders = shopify_sales_data.get('shopify', {}).get('total_sales_30_days', {}).get('orders', 0)
                    amazon_orders = amazon_sales_data.get('amazon', {}).get('total_sales_30_days', {}).get('orders', 0)
                    total_orders = shopify_orders + amazon_orders
                    
                    if total_orders > 0:
                        estimated_units = int(total_orders * 1.5)  # Rough estimate
                        logger.warning(f" COMBINED WORKAROUND: Estimating {estimated_units} units from {total_orders} orders")
                        total_units_sold = estimated_units
                
                #  EXTRA SAFETY: If no combined inventory, return 0 immediately
                if total_inventory == 0:
                    logger.info(f" COMBINED: No inventory (${total_sales_revenue:.2f} sales, {total_units_sold} units) - returning 0 turnover")
                    result = {
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
                        'period_info': {
                            'start_date': start_date,
                            'end_date': end_date,
                            'days': period_days
                        }
                    }
                    logger.info(f" Inventory turnover data calculated for combined (no inventory)")
                    return result
                
                average_inventory = self._calculate_average_inventory(total_inventory, total_units_sold, period_days)
                #  FIXED: Use units-based turnover calculation (units sold / average inventory units)
                # This ensures consistent units and logical combined calculations
                turnover_rate = total_units_sold / average_inventory if average_inventory > 0 and total_units_sold > 0 else 0
                
                logger.info(f" COMBINED TURNOVER: {total_units_sold} units sold / {average_inventory} avg inventory = {turnover_rate:.2f}x")
                
                #  MATHEMATICAL VALIDATION: Combined should never exceed max individual platform
                shopify_avg_inventory = self._calculate_average_inventory(shopify_inventory, shopify_units, period_days)
                shopify_turnover = shopify_units / shopify_avg_inventory if shopify_avg_inventory > 0 and shopify_units > 0 else 0
                amazon_avg_inventory = self._calculate_average_inventory(amazon_inventory, amazon_units, period_days)  
                amazon_turnover = amazon_units / amazon_avg_inventory if amazon_avg_inventory > 0 and amazon_units > 0 else 0
                max_individual_turnover = max(shopify_turnover, amazon_turnover)
                
                logger.info(f" VALIDATION: Shopify individual turnover = {shopify_turnover:.2f}x, Amazon = {amazon_turnover:.2f}x")
                logger.info(f" VALIDATION: Combined turnover = {turnover_rate:.2f}x (should be ≤ {max_individual_turnover:.2f}x)")
                
                if turnover_rate > max_individual_turnover * 1.01:  # Allow 1% tolerance for rounding
                    logger.warning(f" MATHEMATICAL ERROR: Combined turnover ({turnover_rate:.2f}x) > max individual ({max_individual_turnover:.2f}x)!")
                    logger.warning(" This violates basic mathematical logic - investigating data inconsistency")
                
                avg_days_to_sell = 365 / turnover_rate if turnover_rate > 0 else 999
                
                # Get within-period trend for combined platforms
                first_half_turnover, second_half_turnover = await self._get_combined_turnover_trend(
                    client_id, start_date, end_date, period_days, total_inventory
                )
                
                result = {
                    'inventory_turnover_ratio': round(turnover_rate, 2),
                    'avg_days_to_sell': round(avg_days_to_sell, 1),
                    'total_revenue': total_sales_revenue,
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
                
                #  FINAL DEBUG: Log the combined result
                logger.info(f" COMBINED FINAL RESULT: turnover_ratio={result.get('inventory_turnover_ratio', 'N/A')}")
            else:
                #  FIXED: Calculate for specific platform using total_sales/average_inventory
                platform_sales = sales_data.get(platform, {})
                platform_inventory = inventory_data.get(platform, {})
                
                units_sold = platform_sales.get('total_sales_30_days', {}).get('units', 0)
                sales_revenue = platform_sales.get('total_sales_30_days', {}).get('revenue', 0)
                inventory = platform_inventory.get('current_total_inventory', 0)
                
                #  DEBUG: Log all values for debugging
                logger.info(f" {platform} DEBUG: inventory={inventory}, sales_revenue=${sales_revenue:.2f}, units_sold={units_sold}")
                
                #  CRITICAL DEBUG: Check if we have revenue but no units
                if sales_revenue > 0 and units_sold == 0:
                    logger.warning(f" {platform} CRITICAL ISSUE: Has revenue (${sales_revenue:.2f}) but 0 units! Checking sales data structure...")
                    logger.warning(f" Sales data keys: {list(platform_sales.keys())}")
                    if 'total_sales_30_days' in platform_sales:
                        logger.warning(f" total_sales_30_days content: {platform_sales['total_sales_30_days']}")
                    
                    #  TEMPORARY WORKAROUND: Estimate units from orders count if available
                    orders_count = platform_sales.get('total_sales_30_days', {}).get('orders', 0)
                    if orders_count > 0:
                        # Rough estimate: assume 1.5 units per order on average
                        estimated_units = int(orders_count * 1.5)
                        logger.warning(f" WORKAROUND: Estimating {estimated_units} units from {orders_count} orders")
                        units_sold = estimated_units
                
                #  EXTRA SAFETY: If no inventory, return 0 immediately regardless of sales
                # Can't have inventory turnover without inventory!
                if inventory == 0:
                    logger.info(f" {platform}: No inventory (${sales_revenue:.2f} sales, {units_sold} units) - returning 0 turnover")
                    result = {
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
                        'period_info': {
                            'start_date': start_date,
                            'end_date': end_date,
                            'days': period_days
                        }
                    }
                    logger.info(f" Inventory turnover data calculated for {platform} (no activity)")
                    return result
                
                average_inventory = self._calculate_average_inventory(inventory, units_sold, period_days)
                
                #  FIXED: Use units-based turnover calculation (units sold / average inventory units)
                # This ensures consistent units across all platforms
                turnover_rate = units_sold / average_inventory if average_inventory > 0 and units_sold > 0 else 0
                
                logger.info(f" {platform.upper()} TURNOVER: {units_sold} units sold / {average_inventory} avg inventory = {turnover_rate:.2f}x")
                avg_days_to_sell = 365 / turnover_rate if turnover_rate > 0 else 999
                
                # Get within-period turnover trend
                first_half_turnover, second_half_turnover = await self._get_platform_turnover_trend(
                    client_id, platform, start_date, end_date, period_days
                )
                
                result = {
                    'inventory_turnover_ratio': round(turnover_rate, 2),
                    'avg_days_to_sell': round(avg_days_to_sell, 1),
                    'total_revenue': sales_revenue,
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
            
            #  FINAL DEBUG: Log the final result  
            logger.info(f" {platform} FINAL RESULT: turnover_ratio={result.get('inventory_turnover_ratio', 'N/A')}")
            logger.info(f" Inventory turnover data calculated for {platform}")
            return result
            
        except Exception as e:
            logger.error(f" Error getting inventory turnover data: {str(e)}")
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
        logger.info(f" Getting days of stock data for {client_id} - {platform}")
        
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
                
                #  DAYS OF STOCK WORKAROUND: Check for units consistency
                combined_revenue = (
                    sales_data.get('shopify', {}).get('total_sales_30_days', {}).get('revenue', 0) +
                    sales_data.get('amazon', {}).get('total_sales_30_days', {}).get('revenue', 0)
                )
                if combined_revenue > 0 and total_units_sold == 0:
                    combined_orders = (
                        sales_data.get('shopify', {}).get('total_sales_30_days', {}).get('orders', 0) +
                        sales_data.get('amazon', {}).get('total_sales_30_days', {}).get('orders', 0)
                    )
                    if combined_orders > 0:
                        total_units_sold = int(combined_orders * 1.5)
                        logger.warning(f" DAYS OF STOCK COMBINED: Estimated {total_units_sold} units from {combined_orders} orders")
                
                #  FIXED: Use available inventory for combined platforms
                available_inventory = (
                    self._get_available_inventory_for_platform(client_id, "shopify") +
                    self._get_available_inventory_for_platform(client_id, "amazon")
                )
                total_inventory = inventory_data.get('combined', {}).get('current_total_inventory', 0)  # Keep for other metrics
            else:
                total_units_sold = sales_data.get(platform, {}).get('total_sales_30_days', {}).get('units', 0)
                
                #  DAYS OF STOCK WORKAROUND: Check for units consistency (single platform)
                platform_revenue = sales_data.get(platform, {}).get('total_sales_30_days', {}).get('revenue', 0)
                if platform_revenue > 0 and total_units_sold == 0:
                    platform_orders = sales_data.get(platform, {}).get('total_sales_30_days', {}).get('orders', 0)
                    if platform_orders > 0:
                        total_units_sold = int(platform_orders * 1.5)
                        logger.warning(f" DAYS OF STOCK {platform}: Estimated {total_units_sold} units from {platform_orders} orders")
                #  FIXED: Use available inventory for specific platform  
                available_inventory = self._get_available_inventory_for_platform(client_id, platform)
                total_inventory = inventory_data.get(platform, {}).get('current_total_inventory', 0)  # Keep for other metrics
            
            # Calculate daily sales velocity
            period_days = 30  # default
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                if start_dt and end_dt:
                    period_days = max((end_dt - start_dt).days + 1, 1)  # Include both start and end dates
            
            daily_sales_velocity = total_units_sold / period_days if period_days > 0 else 0
            #  FIXED: Days of stock using available inventory (on-hand) instead of total inventory
            days_of_stock = available_inventory / max(daily_sales_velocity, 1) if daily_sales_velocity > 0 else 999
            
            # Categorize stock levels - Note: This is simplified for aggregate view
            # In a real implementation, you'd want to calculate this per SKU
            low_stock_count = 1 if days_of_stock < 7 else 0  # TODO: Implement per-SKU calculation
            out_of_stock_count = 1 if total_inventory == 0 else 0  # TODO: Implement per-SKU calculation
            overstock_count = 1 if days_of_stock > 90 else 0  # TODO: Implement per-SKU calculation
            
            result = {
                'avg_days_of_stock': round(days_of_stock, 1),
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'overstock_count': overstock_count,
                'daily_sales_velocity': round(daily_sales_velocity, 2),
                'current_inventory': total_inventory,
                'period_days': period_days
            }
            
            logger.info(f" Days of stock data calculated for {platform}")
            return result
            
        except Exception as e:
            logger.error(f" Error getting days of stock data: {str(e)}")
            return {"error": str(e)}

    async def get_units_sold_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get units sold data using real orders data with CONSISTENT date filtering"""
        logger.info(f" UNITS SOLD REQUEST - Getting data for {client_id} - {platform} ({start_date} to {end_date})")
        
        tables = self._get_table_names(client_id)
        logger.info(f" UNITS SOLD - Tables available: {tables}")
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
            logger.info(f" UNITS SOLD FINAL RESULT for {platform}:")
            for platform_key, platform_result in result.items():
                if isinstance(platform_result, dict) and 'units_sold_chart' in platform_result:
                    chart_data = platform_result['units_sold_chart']
                    total_units = sum(item['units_sold'] for item in chart_data) if chart_data else 0
                    logger.info(f"    {platform_key}: {len(chart_data)} data points, {total_units} total units")
                    if chart_data:
                        logger.info(f"      First: {chart_data[0]}")
                        logger.info(f"      Last: {chart_data[-1]}")
            
            return result
            
        except Exception as e:
            logger.error(f" Error getting units sold data: {str(e)}")
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
                    logger.info(f" UNITS SOLD - Filtering orders >= {start_dt.isoformat()}")
            
            if end_date:
                end_dt = self._parse_date(end_date)
                if end_dt:
                    query = query.lte("created_at", end_dt.isoformat())
                    logger.info(f" UNITS SOLD - Filtering orders <= {end_dt.isoformat()}")
            
            # Execute query with filters
            orders_response = query.execute()
            orders = orders_response.data or []
            
            logger.info(f" UNITS SOLD DEBUG - Platform: {platform}, Orders: {len(orders)}")
            
            # Sample a few orders to understand the data structure
            if orders:
                logger.info(f" SAMPLE ORDER DATA STRUCTURE:")
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
                logger.warning(f" NO ORDERS FOUND in table {table_name} after date filtering!")
                logger.warning(f" Check if orders exist in the date range {start_date} to {end_date}")
            
            timeline_data = []
            
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)
                
                logger.info(f" PARSED DATE RANGE: {start_dt} to {end_dt}")
                
                # Check if dates are realistic
                from datetime import datetime
                current_year = datetime.now().year
                if start_dt and start_dt.year > current_year:
                    logger.warning(f" FUTURE DATE DETECTED: {start_dt.year} > {current_year}")
                    logger.warning(f" You selected dates in {start_dt.year} - check if you have orders in the future!")
                
                if start_dt and end_dt:
                    #  FIXED: Filter orders by fulfillment status before calculating daily sales
                    fulfilled_orders = [order for order in orders if self._is_order_fulfilled(order)]
                    logger.info(f" UNITS SOLD FILTERING: {len(orders)} total orders → {len(fulfilled_orders)} fulfilled orders")
                    
                    # Calculate daily sales from fulfilled orders only
                    daily_sales = await self._calculate_daily_sales_from_orders(fulfilled_orders, platform, start_dt, end_dt)
                    
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
            logger.error(f" Error getting {platform} units sold: {str(e)}")
            return {
                'units_sold_chart': [],
                'total_units_sold': 0,
                'error': str(e)
            }

    async def _calculate_daily_sales_from_orders(self, orders: List[Dict], platform: str, start_dt: datetime, end_dt: datetime) -> Dict[str, int]:
        """Calculate daily sales quantities from FULFILLED orders only (Shopify: paid+fulfilled, Amazon: shipped)"""
        daily_sales = {}
        
        # Initialize all dates with 0 sales
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_sales[date_str] = 0
            current_date += timedelta(days=1)
        
        logger.info(f" Processing {len(orders)} FULFILLED orders for daily units sold calculation ({platform})")
        
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
                        logger.info(f" Order {orders_processed}: No created_at date")
                    continue
                    
                order_date = self._parse_date(created_at)
                if not order_date:
                    if orders_processed <= 5:  # Log first few
                        logger.info(f" Order {orders_processed}: Could not parse date {created_at}")
                    continue
                
                date_str = order_date.strftime('%Y-%m-%d')
                units_sold = 0
                
                if orders_processed <= 5:  # Log first few orders for debugging
                    logger.info(f" Processing Order {orders_processed}: {order.get('order_number', 'Unknown')} on {date_str}")
                
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
                                            logger.info(f"     ️ Line item quantity: {quantity}")
                            else:
                                # No line items in raw_data, use fallback
                                fallback_count = int(order.get('line_items_count', 1) or 1)
                                units_sold = fallback_count
                                if orders_processed <= 5:
                                    logger.info(f"     ️ Using fallback line_items_count: {fallback_count}")
                        except Exception as e:
                            logger.debug(f"Error parsing Shopify order {order.get('order_number')}: {e}")
                            # Fallback to line_items_count if available
                            fallback_count = int(order.get('line_items_count', 1) or 1)
                            units_sold = fallback_count
                            if orders_processed <= 5:
                                logger.info(f"     ️ Error fallback line_items_count: {fallback_count}")
                    else:
                        # No raw_data, try other fields
                        fallback_count = int(order.get('line_items_count', 1) or 1)
                        units_sold = fallback_count
                        if orders_processed <= 5:
                            logger.info(f"     ️ No raw_data, using line_items_count: {fallback_count}")
                    
                    # Alternative: Check if there's a direct units/quantity field
                    if units_sold == 0:
                        alt_quantity = order.get('quantity') or order.get('units') or order.get('total_quantity')
                        if alt_quantity:
                            units_sold = int(alt_quantity)
                            if orders_processed <= 5:
                                logger.info(f"     ️ Using alternative quantity field: {units_sold}")
                        
                elif platform == "amazon":
                    #  FIXED: Amazon orders use number_of_items_shipped (not 'quantity')
                    units_sold = int(order.get('number_of_items_shipped', 1) or 1)
                    if orders_processed <= 5:
                        logger.info(f"     ️ Amazon number_of_items_shipped: {units_sold}")
                
                # LOG DETAILED DEBUG INFO if units_sold is still 0
                if units_sold == 0:
                    if orders_processed <= 5:
                        logger.warning(f" Order {orders_processed} has 0 units extracted:")
                        logger.warning(f"   Order number: {order.get('order_number', 'N/A')}")
                        logger.warning(f"   Total price: {order.get('total_price', 'N/A')}")
                        logger.warning(f"   Line items count: {order.get('line_items_count', 'N/A')}")
                        logger.warning(f"   Has raw_data: {bool(order.get('raw_data'))}")
                        
                        # Try to parse raw_data one more time with detailed logging
                        raw_data = order.get('raw_data')
                        if raw_data:
                            try:
                                if isinstance(raw_data, str):
                                    parsed = json.loads(raw_data)
                                else:
                                    parsed = raw_data
                                logger.warning(f"   Raw data keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                                if 'line_items' in parsed:
                                    line_items = parsed['line_items']
                                    logger.warning(f"   Line items type: {type(line_items)}")
                                    logger.warning(f"   Line items length: {len(line_items) if isinstance(line_items, list) else 'Not a list'}")
                                    if isinstance(line_items, list) and len(line_items) > 0:
                                        logger.warning(f"   First line item: {line_items[0]}")
                            except Exception as e:
                                logger.warning(f"   Raw data parse error: {e}")
                    
                    #  FIXED: Only use fallback for orders with actual revenue
                    order_revenue = float(order.get('total_price', 0) or 0)
                    if order_revenue > 0:
                        # Only for orders with revenue, use minimal fallback
                        units_sold = 1
                        if orders_processed <= 5:
                            logger.info(f"     ️ Fallback: Order has revenue ${order_revenue:.2f}, counting as 1 unit")
                    else:
                        # No revenue, no units - skip this order
                        if orders_processed <= 5:
                            logger.info(f"      Skipping: Order has no revenue and no extractable units")
                        continue  # Skip adding to daily_sales
                
                # Add to daily sales (since orders are pre-filtered, we know date is in range)
                if date_str in daily_sales:
                    daily_sales[date_str] += units_sold
                    total_units_extracted += units_sold
                    if units_sold > 0:
                        orders_with_units += 1
                        if orders_processed <= 5:  # Log first few
                            logger.info(f"    Added {units_sold} units to {date_str} (total now: {daily_sales[date_str]})")
                else:
                    # This shouldn't happen since orders are pre-filtered, but log it
                    logger.warning(f" Order date {date_str} not in expected range!")
                    
            except Exception as e:
                logger.debug(f"Error processing order for daily sales: {e}")
                continue
        
        # Log comprehensive summary
        non_zero_days = len([v for v in daily_sales.values() if v > 0])
        
        logger.info(f" DAILY SALES CALCULATION SUMMARY:")
        logger.info(f"    Total orders processed: {orders_processed}")
        logger.info(f"    Orders with units: {orders_with_units}")
        logger.info(f"    Total units extracted: {total_units_extracted}")
        logger.info(f"    Active sales days: {non_zero_days}")
        
        if total_units_extracted == 0:
            logger.warning(f" ZERO UNITS EXTRACTED! Possible issues:")
            logger.warning(f"   - Orders missing line_items or quantity data")
            logger.warning(f"   - Raw_data field malformed or empty")
            logger.warning(f"   - Quantity fields not where expected")
            
            if len(orders) > 0:
                logger.info(f" DEBUGGING HINT:")
                logger.info(f"   You have {len(orders)} orders in the selected date range")
                logger.info(f"   But no units could be extracted from them")
                logger.info(f"   Check the order data structure and quantity fields")
        
        return daily_sales

    async def get_historical_comparison_data(self, client_id: str, platform: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get historical comparison data with period-over-period analysis"""
        logger.info(f" HISTORICAL COMPARISON REQUEST - Getting data for {client_id} - {platform} ({start_date} to {end_date})")
        
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
            
            logger.info(f" HISTORICAL COMPARISON FINAL RESULT for {platform}:")
            for platform_key, platform_result in result.items():
                if isinstance(platform_result, dict) and 'comparison_chart' in platform_result:
                    chart_data = platform_result['comparison_chart']
                    current_total = platform_result.get('total_current_period', 0)
                    previous_total = platform_result.get('total_previous_period', 0)
                    logger.info(f"    {platform_key}: {len(chart_data)} data points")
                    logger.info(f"      Current: ${current_total:.2f}, Previous: ${previous_total:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f" Error getting historical comparison data: {str(e)}")
            return {"error": str(e)}

    async def _get_platform_historical_comparison(self, table_name: str, platform: str, start_date: Optional[str], end_date: Optional[str]) -> Dict[str, Any]:
        """Get historical comparison data for a specific platform"""
        try:
            if not start_date or not end_date:
                logger.warning(f" Historical comparison requires both start_date and end_date")
                return {'comparison_chart': [], 'total_current_period': 0, 'total_previous_period': 0, 'error': 'Missing date range'}
            
            db_client = get_admin_client()
            
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)
            
            if not start_dt or not end_dt:
                logger.warning(f" Could not parse dates: {start_date}, {end_date}")
                return {'comparison_chart': [], 'total_current_period': 0, 'total_previous_period': 0, 'error': 'Invalid dates'}
            
            # Calculate period length
            period_length = (end_dt - start_dt).days + 1
            
            # Calculate previous period (same length, going backwards)
            previous_end_dt = start_dt - timedelta(days=1)
            previous_start_dt = previous_end_dt - timedelta(days=period_length - 1)
            
            logger.info(f" HISTORICAL COMPARISON PERIODS:")
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
            
            logger.info(f" ORDERS FOUND:")
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
                
                # Calculate revenue from daily sales (using same logic as total sales with filtering)
                for order in current_orders:
                    order_date = self._parse_date(order.get('created_at'))
                    if order_date and order_date.strftime('%Y-%m-%d') == current_date_str:
                        #  NEW: Only count fulfilled orders
                        if self._is_order_fulfilled(order):
                            current_revenue += float(order.get('total_price', 0) or 0)
                
                for order in previous_orders:
                    order_date = self._parse_date(order.get('created_at'))
                    if order_date and order_date.strftime('%Y-%m-%d') == previous_date_str:
                        #  NEW: Only count fulfilled orders
                        if self._is_order_fulfilled(order):
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
            
            logger.info(f" COMPARISON SUMMARY:")
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
            logger.error(f" Error getting {platform} historical comparison: {str(e)}")
            return {
                'comparison_chart': [],
                'total_current_period': 0,
                'total_previous_period': 0,
                'error': str(e)
            }


# Global instance
component_data_manager = ComponentDataManager()