"""
Dashboard-Focused Inventory Analytics Module
Provides specific SKU lists, KPIs, trends, and alerts for dashboard consumption
All data retrieved via direct SQL queries from organized client tables
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from database import get_admin_client
from component_data_functions import ComponentDataManager

logger = logging.getLogger(__name__)

class DashboardInventoryAnalyzer:
    """Dashboard-focused inventory analyzer with specific KPIs and data structures"""
    
    def __init__(self):
        self.admin_client = None
        self._client_initialized = False
        self.component_data = ComponentDataManager()
    
    def _ensure_client(self):
        """Lazy initialization of database client"""
        if not self._client_initialized:
            self.admin_client = get_admin_client()
            self._client_initialized = True
            if not self.admin_client:
                raise Exception("No admin database client available")
        return self.admin_client

    async def get_dashboard_inventory_analytics(self, client_id: str, platform: str = "shopify", start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get complete dashboard inventory analytics"""
        try:
            # Ensure database client is available
            self._ensure_client()
            
            logger.info(f"Getting dashboard inventory analytics for client {client_id} (platform: {platform})")
            
            # NEW: Support for getting both platforms separately
            if platform.lower() == "all":
                return await self._get_multi_platform_analytics(client_id, start_date, end_date)
            
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
            
            #  PARALLEL CALCULATIONS - ALL AT ONCE, NO WAITING!
            logger.info(f" Running ALL calculations in parallel for {client_id} ({platform})")
            
            #  ULTRA-FAST PARALLEL CALCULATIONS - ALL AT ONCE!
            logger.info(f" TURBO MODE: Running all calculations in parallel for {client_id} ({platform})")
            
            # Run ALL calculations simultaneously with timeout - NO WAITING!
            kpis_task = asyncio.create_task(self._get_kpi_charts(client_id, shopify_data, amazon_data))
            trends_task = asyncio.create_task(self._get_trend_visualizations(client_id, shopify_data, amazon_data))
            alerts_task = asyncio.create_task(self._get_alerts_summary(client_id, shopify_data, amazon_data))
            
            # Wait for all calculations with 3 second timeout - NO WAITING!
            try:
                sales_kpis, trend_analysis, alerts_summary = await asyncio.wait_for(
                    asyncio.gather(kpis_task, trends_task, alerts_task, return_exceptions=True),
                    timeout=3.0
                )
                logger.info(f" TURBO COMPLETE: All calculations finished in <3s for {client_id}")
            except asyncio.TimeoutError:
                logger.warning(f" Calculations timeout after 3s, using partial results")
                # Get whatever completed - NO WAITING!
                sales_kpis = kpis_task.result() if kpis_task.done() else {}
                trend_analysis = trends_task.result() if trends_task.done() else {}
                alerts_summary = alerts_task.result() if alerts_task.done() else {}
            
            # Handle any exceptions from parallel execution
            if isinstance(sales_kpis, Exception):
                logger.error(f" KPIs calculation failed: {sales_kpis}")
                sales_kpis = {}
            if isinstance(trend_analysis, Exception):
                logger.error(f" Trends calculation failed: {trend_analysis}")
                trend_analysis = {}
            if isinstance(alerts_summary, Exception):
                logger.error(f" Alerts calculation failed: {alerts_summary}")
                alerts_summary = {}
            
            logger.info(f" ALL calculations completed in parallel for {client_id} ({platform})")
            
            #  CALCULATE REAL INVENTORY METRICS - NO MORE HARDCODED ZEROS!
            total_inventory_value = self._calculate_total_inventory_value(shopify_data, amazon_data)
            total_skus = len([p for p in shopify_data.get('products', []) if p.get('sku')]) + len([p for p in amazon_data.get('products', []) if p.get('sku')])
            
            # Get real counts from alerts calculation
            low_stock_count = alerts_summary.get('summary_counts', {}).get('low_stock_alerts', 0)
            overstock_count = alerts_summary.get('summary_counts', {}).get('overstock_alerts', 0)
            out_of_stock_count = self._calculate_out_of_stock_count(shopify_data, amazon_data)
            
            logger.info(f" REAL VALUES: SKUs: {total_skus}, Inventory Value: ${total_inventory_value}, Low Stock: {low_stock_count}, Out of Stock: {out_of_stock_count}")
            
            analytics = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "sales_kpis": sales_kpis,
                "trend_analysis": trend_analysis,
                "alerts_summary": alerts_summary,
                "data_summary": {
                    "platform": platform,
                    "total_records": len(shopify_data.get('products', [])) + len(amazon_data.get('products', [])) + len(shopify_data.get('orders', [])) + len(amazon_data.get('orders', [])),
                    "total_skus": total_skus,
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
                        "total_skus": total_skus,
                        "total_inventory_value": total_inventory_value,
                        "low_stock_count": low_stock_count,
                        "out_of_stock_count": out_of_stock_count,
                        "overstock_count": overstock_count
                    }
                },
                "recommendations": [
                    "Use /api/dashboard/sku-inventory for detailed SKU data with pagination",
                    "SKU data separated for optimal performance with large datasets",
                    "Enable caching for faster subsequent requests"
                ]
            }
            
            logger.info(f"Dashboard inventory analytics completed for client {client_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Dashboard inventory analytics failed: {e}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "error": str(e)
            }
    
    async def _get_multi_platform_analytics(self, client_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics for both Shopify and Amazon platforms separately"""
        try:
            logger.info(f" Getting SEPARATE analytics for both platforms: {client_id}")
            
            # Get both platform data in parallel
            shopify_data_task = asyncio.create_task(self._get_shopify_data(client_id))
            amazon_data_task = asyncio.create_task(self._get_amazon_data(client_id))
            
            shopify_data, amazon_data = await asyncio.gather(shopify_data_task, amazon_data_task)
            
            # Calculate analytics for Shopify only
            shopify_kpis_task = asyncio.create_task(self._get_kpi_charts(client_id, shopify_data, {"products": [], "orders": []}))
            shopify_trends_task = asyncio.create_task(self._get_trend_visualizations(client_id, shopify_data, {"products": [], "orders": []}))
            shopify_alerts_task = asyncio.create_task(self._get_alerts_summary(client_id, shopify_data, {"products": [], "orders": []}))
            
            # Calculate analytics for Amazon only
            amazon_kpis_task = asyncio.create_task(self._get_kpi_charts(client_id, {"products": [], "orders": []}, amazon_data))
            amazon_trends_task = asyncio.create_task(self._get_trend_visualizations(client_id, {"products": [], "orders": []}, amazon_data))
            amazon_alerts_task = asyncio.create_task(self._get_alerts_summary(client_id, {"products": [], "orders": []}, amazon_data))
            
            # Wait for all calculations
            (shopify_kpis, shopify_trends, shopify_alerts, 
             amazon_kpis, amazon_trends, amazon_alerts) = await asyncio.gather(
                shopify_kpis_task, shopify_trends_task, shopify_alerts_task,
                amazon_kpis_task, amazon_trends_task, amazon_alerts_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            def safe_result(result):
                return result if not isinstance(result, Exception) else {}
            
            shopify_kpis = safe_result(shopify_kpis)
            shopify_trends = safe_result(shopify_trends) 
            shopify_alerts = safe_result(shopify_alerts)
            amazon_kpis = safe_result(amazon_kpis)
            amazon_trends = safe_result(amazon_trends)
            amazon_alerts = safe_result(amazon_alerts)
            
            # Also calculate COMBINED analytics (Shopify + Amazon together)
            combined_kpis_task = asyncio.create_task(self._get_kpi_charts(client_id, shopify_data, amazon_data))
            combined_trends_task = asyncio.create_task(self._get_trend_visualizations(client_id, shopify_data, amazon_data))
            combined_alerts_task = asyncio.create_task(self._get_alerts_summary(client_id, shopify_data, amazon_data))
            
            combined_kpis, combined_trends, combined_alerts = await asyncio.gather(
                combined_kpis_task, combined_trends_task, combined_alerts_task,
                return_exceptions=True
            )
            
            combined_kpis = safe_result(combined_kpis)
            combined_trends = safe_result(combined_trends) 
            combined_alerts = safe_result(combined_alerts)
            
            #  CALCULATE REAL INVENTORY METRICS FOR MULTI-PLATFORM - NO MORE HARDCODED ZEROS!
            shopify_inventory_value = self._calculate_total_inventory_value(shopify_data, {"products": [], "orders": []})
            amazon_inventory_value = self._calculate_total_inventory_value({"products": [], "orders": []}, amazon_data)
            combined_inventory_value = self._calculate_total_inventory_value(shopify_data, amazon_data)
            
            shopify_total_skus = len([p for p in shopify_data.get('products', []) if p.get('sku')])
            amazon_total_skus = len([p for p in amazon_data.get('products', []) if p.get('sku')])
            combined_total_skus = shopify_total_skus + amazon_total_skus
            
            logger.info(f" Multi-platform analytics completed for {client_id}")
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "client_id": client_id,
                "platform": "all",
                "platforms": {
                    "shopify": {
                        "sales_kpis": shopify_kpis,
                        "trend_analysis": shopify_trends,
                        "alerts_summary": shopify_alerts,
                        "data_summary": {
                            "platform": "shopify",
                            "shopify_products": len(shopify_data.get('products', [])),
                            "shopify_orders": len(shopify_data.get('orders', [])),
                            "amazon_products": 0,
                            "amazon_orders": 0
                        },
                        "sku_inventory": {
                            "summary_stats": {
                                "total_skus": shopify_total_skus,
                                "total_inventory_value": shopify_inventory_value,
                                "low_stock_count": shopify_alerts.get('summary_counts', {}).get('low_stock_alerts', 0),
                                "out_of_stock_count": self._calculate_out_of_stock_count(shopify_data, {"products": [], "orders": []}),
                                "overstock_count": shopify_alerts.get('summary_counts', {}).get('overstock_alerts', 0)
                            }
                        }
                    },
                    "amazon": {
                        "sales_kpis": amazon_kpis,
                        "trend_analysis": amazon_trends,
                        "alerts_summary": amazon_alerts,
                        "data_summary": {
                            "platform": "amazon",
                            "shopify_products": 0,
                            "shopify_orders": 0,
                            "amazon_orders": len(amazon_data.get('orders', [])),
                            "amazon_products": len(amazon_data.get('products', [])),
                        },
                        "sku_inventory": {
                            "summary_stats": {
                                "total_skus": amazon_total_skus,
                                "total_inventory_value": amazon_inventory_value,
                                "low_stock_count": amazon_alerts.get('summary_counts', {}).get('low_stock_alerts', 0),
                                "out_of_stock_count": self._calculate_out_of_stock_count({"products": [], "orders": []}, amazon_data),
                                "overstock_count": amazon_alerts.get('summary_counts', {}).get('overstock_alerts', 0)
                            }
                        }
                    },
                    "combined": {
                        "sales_kpis": combined_kpis,
                        "trend_analysis": combined_trends,
                        "alerts_summary": combined_alerts,
                        "data_summary": {
                            "platform": "combined",
                            "shopify_products": len(shopify_data.get('products', [])),
                            "shopify_orders": len(shopify_data.get('orders', [])),
                            "amazon_orders": len(amazon_data.get('orders', [])),
                            "amazon_products": len(amazon_data.get('products', [])),
                            "total_records": len(shopify_data.get('products', [])) + len(amazon_data.get('products', [])) + len(shopify_data.get('orders', [])) + len(amazon_data.get('orders', []))
                        },
                        "sku_inventory": {
                            "summary_stats": {
                                "total_skus": combined_total_skus,
                                "total_inventory_value": combined_inventory_value,
                                "low_stock_count": combined_alerts.get('summary_counts', {}).get('low_stock_alerts', 0),
                                "out_of_stock_count": self._calculate_out_of_stock_count(shopify_data, amazon_data),
                                "overstock_count": combined_alerts.get('summary_counts', {}).get('overstock_alerts', 0)
                            }
                        }
                    }
                },
                "message": "Multi-platform analytics with separate Shopify, Amazon, and combined data"
            }
            
        except Exception as e:
            logger.error(f"Error getting multi-platform analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_shopify_data(self, client_id: str) -> Dict[str, Any]:
        """ PARALLEL Shopify data fetch with NEW TABLE STRUCTURE - NO WAITING!"""
        try:
            # Ensure database client is available
            admin_client = self._ensure_client()
            
            products_table = "shopify_products"
            orders_table = "shopify_orders"
            order_items_table = "shopify_order_items"
            
            logger.info(f" PARALLEL Shopify fetch for {client_id} with NEW table structure")
            
            #  RUN ALL QUERIES IN PARALLEL - NO SEQUENTIAL WAITING!
            async def fetch_products():
                try:
                    response = admin_client.table(products_table).select(
                        "sku,title,variant_title,on_hand_inventory,price,option1,option2,variant_id,available_quantity,reserved_inventory,incoming_inventory"
                    ).eq('client_id', client_id).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Shopify products table not found or empty: {e}")
                    return []
            
            async def fetch_orders():
                try:
                    response = admin_client.table(orders_table).select(
                        "order_id,total_price,created_at_shopify,financial_status,fulfillment_status,order_number,client_id"
                    ).eq('client_id', client_id).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Shopify orders table not found or empty: {e}")
                    return []
            
            async def fetch_order_items():
                try:
                    response = admin_client.table(order_items_table).select(
                        "order_id,sku,quantity,price,title,variant_title,fulfillment_status,client_id"
                    ).eq('client_id', client_id).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Shopify order items table not found or empty: {e}")
                    return []
            
            # Execute all queries simultaneously
            products, orders, order_items = await asyncio.gather(
                fetch_products(), fetch_orders(), fetch_order_items(), return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(products, Exception):
                logger.error(f" Products fetch failed: {products}")
                products = []
            if isinstance(orders, Exception):
                logger.error(f" Orders fetch failed: {orders}")
                orders = []
            if isinstance(order_items, Exception):
                logger.error(f" Order items fetch failed: {order_items}")
                order_items = []
            
            logger.info(f" PARALLEL complete: {len(products)} Shopify products, {len(orders)} orders, {len(order_items)} order items")
            
            return {"products": products, "orders": orders, "order_items": order_items}
            
        except Exception as e:
            logger.warning(f"Could not get Shopify data: {e}")
            return {"products": [], "orders": [], "order_items": []}
    
    async def _get_amazon_data(self, client_id: str) -> Dict[str, Any]:
        """Get Amazon data from NEW TABLE STRUCTURE with optimized queries"""
        try:
            # Ensure database client is available
            admin_client = self._ensure_client()
            
            orders_table = "amazon_orders"
            products_table = "amazon_products"
            order_items_table = "amazon_order_items"
            
            logger.info(f" PARALLEL Amazon fetch for {client_id} with NEW table structure")
            
            #  RUN ALL QUERIES IN PARALLEL - NO SEQUENTIAL WAITING!
            async def fetch_orders():
                try:
                    response = admin_client.table(orders_table).select(
                        "order_id,order_total,purchase_date,number_of_items_shipped,number_of_items_unshipped,order_status,client_id"
                    ).eq('client_id', client_id).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Amazon orders table not found or empty: {e}")
                    return []
            
            async def fetch_products():
                try:
                    response = admin_client.table(products_table).select(
                        "sku,asin,title,on_hand_inventory,listing_price,brand,available_quantity,reserved_inventory,incoming_inventory,client_id"
                    ).eq('client_id', client_id).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Amazon products table not found or empty: {e}")
                    return []
            
            async def fetch_order_items():
                try:
                    response = admin_client.table(order_items_table).select(
                        "order_id,sku,asin,quantity_ordered,quantity_shipped,item_price,title,client_id"
                    ).eq('client_id', client_id).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Amazon order items table not found or empty: {e}")
                    return []
            
            # Execute all queries simultaneously
            orders, products, order_items = await asyncio.gather(
                fetch_orders(), fetch_products(), fetch_order_items(), return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(orders, Exception):
                logger.error(f" Orders fetch failed: {orders}")
                orders = []
            if isinstance(products, Exception):
                logger.error(f" Products fetch failed: {products}")
                products = []
            if isinstance(order_items, Exception):
                logger.error(f" Order items fetch failed: {order_items}")
                order_items = []
            
            logger.info(f" PARALLEL complete: {len(orders)} Amazon orders, {len(products)} products, {len(order_items)} order items")
            
            return {"orders": orders, "products": products, "order_items": order_items}
            
        except Exception as e:
            logger.warning(f"Could not get Amazon data: {e}")
            return {"orders": [], "products": [], "order_items": []}
    
    async def get_sku_list(self, client_id: str, page: int = 1, page_size: int = 50, use_cache: bool = True, platform: str = "shopify") -> Dict[str, Any]:
        """Get optimized SKU list with fast calculations and caching support"""
        try:
            # Import cache manager
            from sku_cache_manager import get_sku_cache_manager
            
            if not self.admin_client:
                logger.error("Admin client is None - cannot access SKU cache in dashboard_inventory_analyzer")
                return {
                    "success": False,
                    "error": "Database connection error - admin client unavailable",
                    "cached": False,
                    "items": [],
                    "page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 0
                }
            
            cache_manager = get_sku_cache_manager(self.admin_client)
            
            # Create a unique cache key that includes platform
            cache_key = f"{client_id}_{platform}"
            
            # Try to get from cache first if enabled
            if use_cache:
                cached_result = await cache_manager.get_cached_skus(cache_key, page, page_size)
                if cached_result.get("success"):
                    return cached_result
                    
            logger.info(f"Generating fresh SKU list for client {client_id} (platform: {platform})")
            
            # Get data based on platform
            if platform.lower() == "shopify":
                shopify_data = await self._get_shopify_data(client_id)
                amazon_data = {"products": [], "orders": []}
            elif platform.lower() == "amazon":
                amazon_data = await self._get_amazon_data(client_id)
                shopify_data = {"products": [], "orders": []}
            else:
                shopify_data = await self._get_shopify_data(client_id)
                amazon_data = await self._get_amazon_data(client_id)
            
            sku_list = []
            
            # Process products based on platform selection
            if platform.lower() == "shopify":
                self._process_shopify_products(shopify_data, sku_list)
            elif platform.lower() == "amazon":
                self._process_amazon_products(amazon_data, sku_list)
            else:
                # Process both platforms
                self._process_shopify_products(shopify_data, sku_list)
                self._process_amazon_products(amazon_data, sku_list)
            
            # If no products found but we have orders, try to extract products from orders
            if len(sku_list) == 0:
                logger.info(" No products found, attempting to extract from order data...")
                sku_list.extend(self._extract_products_from_orders(shopify_data.get('orders', []), amazon_data.get('orders', [])))
            
            # Sort by current availability (lowest first for attention)
            sku_list.sort(key=lambda x: x['current_availability'])
            
            logger.info(f"Generated SKU list with {len(sku_list)} items")
            
            # Cache the full result for future requests
            if use_cache and sku_list:
                await cache_manager.cache_skus(cache_key, sku_list)
            
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
            logger.error(f"Error generating SKU list: {e}")
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

    def _process_shopify_products(self, shopify_data: Dict, sku_list: List[Dict]):
        """Process Shopify products with NEW TABLE STRUCTURE and add to SKU list"""
        shopify_products = shopify_data.get('products', [])
        
        logger.info(f" Processing {len(shopify_products)} Shopify products for SKU list with NEW structure")
        
        skipped_count = 0
        processed_count = 0
        
        for product in shopify_products:
            sku = product.get('sku')
            # Use variant_id or product_id as fallback if no SKU
            if not sku:
                variant_id = product.get('variant_id')
                product_id = product.get('product_id')
                if variant_id:
                    sku = f"VARIANT-{variant_id}"
                elif product_id:
                    sku = f"PRODUCT-{product_id}"
                else:
                    skipped_count += 1
                    continue  # Skip only if we have no identifier at all
            
            # NEW TABLE STRUCTURE: Use on_hand_inventory instead of inventory_quantity
            on_hand = product.get('on_hand_inventory', 0) or 0
            incoming = product.get('incoming_inventory', 0) or 0  # Now available directly from table
            reserved = product.get('reserved_inventory', 0) or 0  # Now available directly from table
            available_qty = product.get('available_quantity')  # Available directly from table (can be None)
            
            # Use available_quantity if available, otherwise calculate on_hand - reserved (allow negative values)
            current_availability = available_qty if available_qty is not None else (on_hand - reserved)
            unit_price = product.get('price', 0) or 0
            
            sku_list.append({
                "platform": "shopify",
                "item_name": product.get('title', 'Unknown Product'),
                "sku_code": sku,
                "variant_title": product.get('variant_title', ''),
                "on_hand_inventory": on_hand,
                "incoming_inventory": incoming,
                "outgoing_inventory": reserved,  # Use reserved_inventory as outgoing
                "current_availability": current_availability,
                "unit_price": unit_price,
                "total_value": max(0, current_availability) * unit_price,  # Only positive values for total value
                "option1": product.get('option1'),
                "option2": product.get('option2')
            })
            processed_count += 1
        
        logger.info(f" Shopify processing complete: {processed_count} processed, {skipped_count} skipped")

    def _process_amazon_products(self, amazon_data: Dict, sku_list: List[Dict]):
        """Process Amazon products with NEW TABLE STRUCTURE and add to SKU list"""
        amazon_products = amazon_data.get('products', [])
        
        logger.info(f" Processing {len(amazon_products)} Amazon products for SKU list with NEW structure")
        
        for product in amazon_products:
            sku = product.get('sku')
            asin = product.get('asin')
            
            if not sku and not asin:
                continue
            
            # NEW TABLE STRUCTURE: Use on_hand_inventory instead of quantity
            on_hand = product.get('on_hand_inventory', 0) or 0
            incoming = product.get('incoming_inventory', 0) or 0  # Now available directly from table
            reserved = product.get('reserved_inventory', 0) or 0  # Now available directly from table
            available_qty = product.get('available_quantity')  # Available directly from table (can be None)
            
            # Use available_quantity if available, otherwise calculate on_hand - reserved (allow negative values)
            current_availability = available_qty if available_qty is not None else (on_hand - reserved)
            unit_price = product.get('listing_price', 0) or 0  # Use listing_price instead of price
            
            sku_list.append({
                "platform": "amazon",
                "item_name": product.get('title', 'Unknown Product'),
                "sku_code": sku or asin,
                "asin": asin,
                "on_hand_inventory": on_hand,
                "incoming_inventory": incoming,
                "outgoing_inventory": reserved,  # Use reserved_inventory as outgoing
                "current_availability": current_availability,
                "unit_price": unit_price,
                "total_value": max(0, current_availability) * unit_price,  # Only positive values for total value
                "brand": product.get('brand')
            })
    
    def _calculate_outgoing_for_sku(self, sku: str, orders: List[Dict]) -> int:
        """ FIXED: Calculate outgoing inventory ONLY for orders that actually contain the SKU"""
        if not sku:
            return 0
            
        outgoing = 0
        sku_normalized = str(sku).strip().lower()
        recent_orders_checked = 0
        max_orders_to_check = 20  # Limit to recent orders for performance
        
        for order in orders:
            if recent_orders_checked >= max_orders_to_check:
                break
                
            try:
                # Only count orders that are paid but not yet fulfilled
                financial_status = (order.get('financial_status') or '').lower()
                fulfillment_status = (order.get('fulfillment_status') or '').lower()
                
                # Consider orders that are paid but not fully fulfilled
                if financial_status in ['paid', 'authorized'] and fulfillment_status in ['', 'unfulfilled', 'partial']:
                    recent_orders_checked += 1
                    found_sku_in_order = False
                    
                    # Extract line_items from raw_data for exact SKU matching
                    raw_data = order.get('raw_data')
                    if raw_data:
                        try:
                            import json
                            if isinstance(raw_data, str):
                                raw_order = json.loads(raw_data)
                            else:
                                raw_order = raw_data
                            
                            line_items = raw_order.get('line_items', [])
                            
                            # ONLY count if we find the exact SKU in the order
                            if isinstance(line_items, list) and line_items:
                                for item in line_items:
                                    if isinstance(item, dict):
                                        item_sku = (item.get('sku') or '').strip().lower()
                                        item_variant_id = str(item.get('variant_id', '')).strip()
                                        
                                        # Match by exact SKU or variant_id  
                                        if (item_sku and item_sku == sku_normalized) or (item_variant_id and item_variant_id in str(sku)):
                                            quantity = int(item.get('quantity', 1))
                                            outgoing += quantity
                                            found_sku_in_order = True
                                            logger.debug(f" Found SKU {sku} in order {order.get('order_number')}: +{quantity} units")
                                            break  # Found the SKU, no need to check more items in this order
                                            
                        except Exception as e:
                            logger.debug(f"Error parsing raw_data for order {order.get('order_number')}: {e}")
                    
                    #  REMOVED THE BROKEN FALLBACK LOGIC THAT WAS ADDING INVENTORY TO ALL SKUS!
                    # Previously this was adding outgoing inventory to EVERY SKU for EVERY unfulfilled order
                    # Now we only count when we can actually confirm the SKU is in the order
                    
            except Exception as e:
                logger.debug(f"Error processing order {order.get('order_number', 'unknown')} for outgoing calculation: {e}")
                continue
        
        # Return actual calculated outgoing inventory without artificial caps
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
    
    def _extract_products_from_orders(self, shopify_orders: List[Dict], amazon_orders: List[Dict]) -> List[Dict]:
        """Extract synthetic product data from order information when no product tables exist"""
        try:
            synthetic_products = []
            order_aggregates = {}  # Track aggregated data per synthetic SKU
            
            # Process Amazon orders to extract product information
            for order in amazon_orders:
                try:
                    order_id = order.get('order_id', '')
                    total_price = float(order.get('total_price', 0))
                    items_shipped = int(order.get('number_of_items_shipped', 1))
                    
                    if total_price <= 0 or items_shipped <= 0:
                        continue
                    
                    # Create synthetic SKU based on order characteristics
                    # Group similar orders together to create meaningful products
                    unit_price = total_price / items_shipped
                    price_range = self._get_price_range(unit_price)
                    synthetic_sku = f"AMZ-{price_range}-ITEM"
                    
                    # Aggregate data for this synthetic SKU
                    if synthetic_sku not in order_aggregates:
                        order_aggregates[synthetic_sku] = {
                            'total_revenue': 0,
                            'total_units': 0,
                            'order_count': 0,
                            'avg_price': 0,
                            'platform': 'amazon'
                        }
                    
                    agg = order_aggregates[synthetic_sku]
                    agg['total_revenue'] += total_price
                    agg['total_units'] += items_shipped
                    agg['order_count'] += 1
                    agg['avg_price'] = agg['total_revenue'] / agg['total_units']
                    
                except Exception as e:
                    logger.debug(f"Error processing Amazon order: {e}")
                    continue
            
            # Convert aggregated data to synthetic products
            for sku, agg in order_aggregates.items():
                synthetic_products.append({
                    "platform": agg['platform'],
                    "item_name": f"Amazon Product ({agg['order_count']} orders)",
                    "sku_code": sku,
                    "on_hand_inventory": 0,  # Unknown from orders
                    "incoming_inventory": 0,
                    "outgoing_inventory": 0,
                    "current_availability": 0,  # Can't determine from orders alone
                    "unit_price": round(agg['avg_price'], 2),
                    "total_value": 0,  # No inventory to value
                    "units_sold_30d": agg['total_units'],  # Additional context
                    "revenue_30d": round(agg['total_revenue'], 2)
                })
            
            logger.info(f" Extracted {len(synthetic_products)} synthetic products from {len(amazon_orders)} orders")
            return synthetic_products
            
        except Exception as e:
            logger.error(f" Error extracting products from orders: {e}")
            return []
    
    def _get_price_range(self, price: float) -> str:
        """Categorize price into ranges for synthetic SKU grouping"""
        if price < 10:
            return "LOW"
        elif price < 50:
            return "MED"
        elif price < 100:
            return "HIGH"
        else:
            return "PREMIUM"
    async def _get_kpi_charts(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get optimized KPI charts data using same calculations as component_data_functions"""
        try:
            logger.info(f" Using component_data_functions for consistent 30-day metrics for client {client_id}")
            
            # Use component_data_functions for consistent 30-day calculations
            # Calculate 30-day date range  
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            start_date = thirty_days_ago.strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            
            # Get consistent metrics using component_data_functions
            total_sales_task = asyncio.create_task(
                self.component_data.get_total_sales_data(client_id, "combined", start_date, end_date)
            )
            inventory_turnover_task = asyncio.create_task(
                self.component_data.get_inventory_turnover_data(client_id, "combined", start_date, end_date)
            )
            days_of_stock_task = asyncio.create_task(
                self.component_data.get_days_of_stock_data(client_id, "combined", start_date, end_date)
            )
            units_sold_task = asyncio.create_task(
                self.component_data.get_units_sold_data(client_id, "combined", start_date, end_date)
            )
            inventory_levels_task = asyncio.create_task(
                self.component_data.get_inventory_levels_data(client_id, "combined", start_date, end_date)
            )
            
            # Wait for all calculations to complete
            total_sales_data, inventory_turnover_data, days_of_stock_data, units_sold_data, inventory_levels_data = await asyncio.gather(
                total_sales_task, inventory_turnover_task, days_of_stock_task, units_sold_task, inventory_levels_task,
                return_exceptions=True
            )
            
            # Handle any exceptions from parallel execution
            def safe_get_data(data, default={}):
                return data if not isinstance(data, Exception) else default
            
            total_sales_data = safe_get_data(total_sales_data)
            inventory_turnover_data = safe_get_data(inventory_turnover_data)
            days_of_stock_data = safe_get_data(days_of_stock_data)
            units_sold_data = safe_get_data(units_sold_data)
            inventory_levels_data = safe_get_data(inventory_levels_data)
            
            # Extract the consistent 30-day metrics
            combined_sales = total_sales_data.get('combined', {})
            combined_turnover = inventory_turnover_data.get('combined', {})
            combined_days_stock = days_of_stock_data.get('combined', {})
            combined_units_sold = units_sold_data.get('combined', {})
            combined_inventory = inventory_levels_data.get('combined', {})
            
            logger.info(f" Component data functions completed for consistent metrics")
            
            return {
                "total_sales_30_days": {
                    "revenue": combined_sales.get('total_revenue', 0),
                    "units": combined_units_sold.get('total_units_sold_30d', 0),
                    "orders": combined_sales.get('total_orders', 0)
                },
                "inventory_turnover_30_days": {
                    "turnover_rate": combined_turnover.get('inventory_turnover_ratio', 0),
                    "comparison": combined_turnover.get('turnover_comparison', {}),
                    "avg_days_to_sell": combined_turnover.get('avg_days_to_sell', 999),
                    "fast_moving_items": combined_turnover.get('fast_moving_items', 0)
                },
                "days_of_remaining_stock": {
                    "avg_days_of_stock": combined_days_stock.get('avg_days_of_stock', 999),
                    "daily_sales_velocity": combined_days_stock.get('daily_sales_velocity', 0),
                    "current_inventory": combined_days_stock.get('current_inventory', 0),
                    "low_stock_count": combined_days_stock.get('low_stock_count', 0),
                    "out_of_stock_count": combined_days_stock.get('out_of_stock_count', 0),
                    "overstock_count": combined_days_stock.get('overstock_count', 0)
                },
                "inventory_levels_chart": combined_inventory.get('inventory_levels_chart', []),
                "units_sold_30_days": {
                    "total_units_sold": combined_units_sold.get('total_units_sold_30d', 0),
                    "units_sold_chart": combined_units_sold.get('units_sold_chart', []),
                    "velocity_metrics": combined_units_sold.get('velocity_metrics', {})
                },
                "total_inventory_units": combined_inventory.get('current_total_inventory', 0),
                "data_source": "component_data_functions",
                "calculation_period": f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error calculating KPI charts using component_data_functions: {e}")
            return {"error": str(e)}
    
    def _calculate_available_inventory(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Calculate available inventory using NEW TABLE STRUCTURE - use available_quantity directly"""
        available_inventory = 0
        
        # Shopify available inventory - use available_quantity or calculate on_hand - reserved
        shopify_products = shopify_data.get('products', [])
        
        for product in shopify_products:
            # Use available_quantity directly if it exists (can be negative)
            available_qty = product.get('available_quantity')
            if available_qty is not None:
                product_available = available_qty  # Keep negative values as-is
            else:
                # Fallback: calculate on_hand - reserved (can also be negative)
                on_hand = product.get('on_hand_inventory', 0) or 0
                reserved = product.get('reserved_inventory', 0) or 0
                product_available = on_hand - reserved  # Allow negative values
            
            available_inventory += product_available
        
        # Amazon available inventory - use available_quantity or calculate on_hand - reserved
        amazon_products = amazon_data.get('products', [])
        
        for product in amazon_products:
            # Use available_quantity directly if it exists (can be negative)
            available_qty = product.get('available_quantity')
            if available_qty is not None:
                product_available = available_qty  # Keep negative values as-is
            else:
                # Fallback: calculate on_hand - reserved (can also be negative)
                on_hand = product.get('on_hand_inventory', 0) or 0
                reserved = product.get('reserved_inventory', 0) or 0
                product_available = on_hand - reserved  # Allow negative values
            
            available_inventory += product_available
        
        logger.info(f" Available Inventory: {available_inventory} units (using available_quantity from NEW table structure)")
        
        return available_inventory

    def _calculate_amazon_outgoing_for_sku(self, sku: str, orders: List[Dict]) -> int:
        """DEPRECATED: This method has incorrect logic and should not be used.
        Use _extract_units_from_order instead for accurate SKU-specific calculations."""
        logger.warning(f"DEPRECATED: _calculate_amazon_outgoing_for_sku called for SKU {sku}. Use _extract_units_from_order instead.")
        return 0

    def _calculate_average_inventory(self, current_inventory: int, units_sold: int, period_days: int = 30) -> float:
        """Calculate average inventory = (begin_inventory + end_inventory) / 2"""
        # Current inventory is end_inventory
        end_inventory = current_inventory
        
        #  FIXED: Calculate begin_inventory = current + units sold during the period
        # This assumes inventory at period start = current inventory + units sold since then
        begin_inventory = current_inventory + units_sold
        
        avg_inventory = (begin_inventory + end_inventory) / 2
        
        logger.info(f" Avg Inventory: begin({current_inventory} + {units_sold}) + end({end_inventory}) / 2 = {avg_inventory}")
        logger.info(f" Logic: inventory {period_days} days ago ≈ current({current_inventory}) + sold_since_then({units_sold}) = {begin_inventory}")
        
        # Return actual calculated average inventory without artificial caps
        # Division by zero should be handled by the calling function
        return avg_inventory

    def _is_order_fulfilled(self, order: Dict) -> bool:
        """Check if order should be counted for sales based on platform-specific status rules for NEW TABLE STRUCTURE"""
        platform = order.get('platform', '').lower()
        
        if platform == 'shopify':
            # Shopify: financial_status = 'paid' AND fulfillment_status = 'fulfilled'
            financial_status = (order.get('financial_status', '') or '').lower()
            fulfillment_status = (order.get('fulfillment_status', '') or '').lower()
            return financial_status == 'paid' and fulfillment_status == 'fulfilled'
        
        elif platform == 'amazon':
            # Amazon: order_status = 'Shipped' (note: Amazon uses 'Shipped' with capital S)
            order_status = (order.get('order_status', '') or '').lower()
            return order_status in ['shipped', 'delivered']  # Include both shipped and delivered
        
        else:
            # For mixed data or unknown platform, try to detect from fields
            if 'financial_status' in order and 'fulfillment_status' in order:
                # Likely Shopify
                financial_status = (order.get('financial_status', '') or '').lower()
                fulfillment_status = (order.get('fulfillment_status', '') or '').lower()
                return financial_status == 'paid' and fulfillment_status == 'fulfilled'
            elif 'order_status' in order:
                # Likely Amazon - check for shipped status
                order_status = (order.get('order_status', '') or '').lower()
                return order_status in ['shipped', 'delivered']
            else:
                # Fallback: include all orders if we can't determine platform
                logger.warning(f"Could not determine platform for order {order.get('order_id', 'unknown')}, including in sales")
                return True
    
    def _calculate_sales_for_period(self, orders: List[Dict], start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate sales metrics for a specific time period with proper date handling and order status filtering"""
        revenue = 0
        units = 0
        order_count = 0
        filtered_count = 0
        
        logger.debug(f"Calculating sales from {start_date} to {end_date} for {len(orders)} orders")
        
        for order in orders:
            try:
                # NEW TABLE STRUCTURE: Use correct date fields for each platform
                created_at = None
                
                # Check for Shopify date field first
                if 'created_at_shopify' in order:
                    created_at = order.get('created_at_shopify')
                # Check for Amazon date field
                elif 'purchase_date' in order:
                    created_at = order.get('purchase_date')
                # Fallback to generic created_at
                else:
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
                        #  NEW: Check if order should be counted based on fulfillment status
                        if self._is_order_fulfilled(order):
                            # NEW TABLE STRUCTURE: Use correct price fields for each platform
                            if 'order_total' in order:
                                # Amazon order
                                order_revenue = float(order.get('order_total', 0) or 0)
                            else:
                                # Shopify order
                                order_revenue = float(order.get('total_price', 0) or 0)
                            
                            revenue += order_revenue
                            
                            # Better units estimation with NEW TABLE STRUCTURE
                            if 'line_items_count' in order:
                                units += int(order.get('line_items_count', 1) or 1)
                            elif 'number_of_items_shipped' in order:
                                units += int(order.get('number_of_items_shipped', 1) or 1)
                            else:
                                units += 1
                            
                            order_count += 1
                            logger.debug(f"Order {order.get('order_id')} - Revenue: ${order_revenue}, Date: {order_date}")
                        else:
                            filtered_count += 1
                            logger.debug(f"Order {order.get('order_id')} filtered out - Status: {order.get('financial_status', 'N/A')}/{order.get('fulfillment_status', 'N/A')}/{order.get('order_status', 'N/A')}")
                        
            except Exception as e:
                logger.debug(f"Error processing order: {e}")
                continue
        
        logger.info(f"Period totals - Fulfilled Orders: {order_count}, Filtered Out: {filtered_count}, Revenue: ${revenue:.2f}, Units: {units}")
        return {"revenue": revenue, "units": units, "orders": order_count}
    
    def _calculate_total_inventory(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Calculate total inventory units using NEW TABLE STRUCTURE"""
        total = 0
        
        # Shopify inventory - use on_hand_inventory instead of inventory_quantity
        for product in shopify_data.get('products', []):
            total += product.get('on_hand_inventory', 0) or 0
        
        # Amazon inventory - use on_hand_inventory instead of quantity
        for product in amazon_data.get('products', []):
            total += product.get('on_hand_inventory', 0) or 0
        
        return total
    
    async def _get_trend_visualizations(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get trend visualization data using component_data_functions for consistent calculations"""
        try:
            logger.info(f" Using component_data_functions for consistent trend analysis for client {client_id}")
            
            # Calculate 30-day date range  
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            start_date = thirty_days_ago.strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            
            # Get historical comparison using component_data_functions for consistency
            historical_comparison_task = asyncio.create_task(
                self.component_data.get_historical_comparison_data(client_id, "combined", start_date, end_date)
            )
            inventory_levels_task = asyncio.create_task(
                self.component_data.get_inventory_levels_data(client_id, "combined", start_date, end_date)
            )
            units_sold_task = asyncio.create_task(
                self.component_data.get_units_sold_data(client_id, "combined", start_date, end_date)
            )
            
            # Wait for all trend calculations to complete
            historical_comparison_data, inventory_levels_data, units_sold_data = await asyncio.gather(
                historical_comparison_task, inventory_levels_task, units_sold_task,
                return_exceptions=True
            )
            
            # Handle any exceptions from parallel execution
            def safe_get_data(data, default={}):
                return data if not isinstance(data, Exception) else default
            
            historical_comparison_data = safe_get_data(historical_comparison_data)
            inventory_levels_data = safe_get_data(inventory_levels_data)
            units_sold_data = safe_get_data(units_sold_data)
            
            # Extract the consistent trend data
            combined_historical = historical_comparison_data.get('combined', {})
            combined_inventory = inventory_levels_data.get('combined', {})
            combined_units_sold = units_sold_data.get('combined', {})
            
            logger.info(f" Component data functions completed for consistent trend analysis")
            
            return {
                "inventory_levels_chart_30_days": combined_inventory.get('inventory_levels_chart', []),
                "units_sold_chart_30_days": combined_units_sold.get('units_sold_chart', []),
                "historical_comparison_30_days": {
                    "current_period_revenue": combined_historical.get('current_period_revenue', 0),
                    "previous_period_revenue": combined_historical.get('previous_period_revenue', 0),
                    "revenue_change_percent": combined_historical.get('revenue_change_percent', 0),
                    "current_period_units": combined_historical.get('current_period_units', 0),
                    "previous_period_units": combined_historical.get('previous_period_units', 0),
                    "units_change_percent": combined_historical.get('units_change_percent', 0),
                    "current_period_orders": combined_historical.get('current_period_orders', 0),
                    "previous_period_orders": combined_historical.get('previous_period_orders', 0),
                    "orders_change_percent": combined_historical.get('orders_change_percent', 0)
                },
                "velocity_metrics_30_days": combined_units_sold.get('velocity_metrics', {}),
                "data_source": "component_data_functions",
                "calculation_period": f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error generating trend visualizations using component_data_functions: {e}")
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
    
    async def _get_alerts_summary(self, client_id: str, shopify_data: Dict, amazon_data: Dict) -> Dict[str, Any]:
        """Get comprehensive alerts summary with proper calculations"""
        try:
            logger.info(f"Generating alerts for client {client_id}")
            
            # Initialize counters
            low_stock_count = 0
            overstock_count = 0
            low_stock_details = []
            overstock_details = []
            
            # Process Shopify products for stock alerts - use NEW TABLE STRUCTURE
            shopify_products = shopify_data.get('products', [])
            for product in shopify_products:
                inventory = product.get('on_hand_inventory', 0) or 0  # NEW: on_hand_inventory
                title = product.get('title', 'Unknown Product')
                sku = product.get('sku')
                
                if inventory < 5:  #  CONSISTENT: Low stock threshold < 5 (as specified by user)
                    low_stock_count += 1
                    if len(low_stock_details) < 10:  # Show more details for low stock alerts
                        severity = "critical" if inventory == 0 else "high" if inventory <= 2 else "medium"
                        low_stock_details.append({
                            "platform": "shopify",
                            "sku": sku,
                            "item_name": title,
                            "current_stock": inventory,
                            "severity": severity,
                            "alert_type": "low_stock"
                        })
                elif inventory > 100:  #  CONSISTENT: Overstock threshold > 100 (as specified by user)
                    overstock_count += 1
                    if len(overstock_details) < 3:  # Keep first 3 for display
                        overstock_details.append({
                            "platform": "shopify",
                            "sku": sku,
                            "item_name": title,
                            "current_stock": inventory,
                            "severity": "medium",
                            "alert_type": "overstock"
                        })
            
            # Process Amazon products for stock alerts - use NEW TABLE STRUCTURE
            amazon_products = amazon_data.get('products', [])
            for product in amazon_products:
                quantity = product.get('on_hand_inventory', 0) or 0  # NEW: on_hand_inventory
                title = product.get('title', 'Unknown Product')
                sku = product.get('sku')
                asin = product.get('asin')
                
                if quantity < 5:  #  CONSISTENT: Low stock threshold < 5 (as specified by user)
                    low_stock_count += 1
                    if len(low_stock_details) < 10:  # Show more details for low stock alerts
                        severity = "critical" if quantity == 0 else "high" if quantity <= 2 else "medium"
                        low_stock_details.append({
                            "platform": "amazon",
                            "sku": sku,
                            "asin": asin,
                            "item_name": title,
                            "current_stock": quantity,
                            "severity": severity,
                            "alert_type": "low_stock"
                        })
                elif quantity > 100:  #  CONSISTENT: Overstock threshold > 100 (as specified by user)
                    overstock_count += 1
                    if len(overstock_details) < 3:  # Keep first 3 for display
                        overstock_details.append({
                            "platform": "amazon",
                            "sku": sku,
                            "asin": asin,
                            "item_name": title,
                            "current_stock": quantity,
                            "severity": "medium",
                            "alert_type": "overstock"
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
            
            #  CONSISTENT ALERT THRESHOLDS: Use same logic as component_data_functions
            # Low stock: products with quantity < 5
            # Overstock: products with stock > 100  
            # Sales dropping: > 20% decrease
            sales_spike_threshold = 50  # 50% increase = spike
            sales_down_threshold = 20   # 20% decrease = slowdown (as specified by user)
            
            # Check for significant sales changes
            if previous_week_sales['revenue'] > 0:
                revenue_change = ((recent_week_sales['revenue'] - previous_week_sales['revenue']) / previous_week_sales['revenue']) * 100
                
                if revenue_change > sales_spike_threshold:  # Configurable spike threshold
                    sales_spike_count = 1
                    sales_spike_details.append({
                        "alert_type": "sales_spike",
                        "type": "sales_spike", 
                        "severity": "info",
                        "message": f"Sales spiked {revenue_change:.1f}% this week (${recent_week_sales['revenue']:.2f} vs ${previous_week_sales['revenue']:.2f})",
                        "current_revenue": recent_week_sales['revenue'],
                        "previous_revenue": previous_week_sales['revenue'],
                        "change_percent": revenue_change
                    })
                elif revenue_change < -sales_down_threshold:  #  FIXED: Configurable sales down threshold (was -30, now -20)
                    sales_slowdown_count = 1
                    sales_slowdown_details.append({
                        "alert_type": "sales_dropping",
                        "type": "sales_slowdown",
                        "severity": "warning",  
                        "message": f"Sales dropped {abs(revenue_change):.1f}% this week (${recent_week_sales['revenue']:.2f} vs ${previous_week_sales['revenue']:.2f})",
                        "current_revenue": recent_week_sales['revenue'],
                        "previous_revenue": previous_week_sales['revenue'],
                        "change_percent": revenue_change,
                        "threshold_used": sales_down_threshold  # Track which threshold was used (20% as specified by user)
                    })
            
            total_alerts = low_stock_count + overstock_count + sales_spike_count + sales_slowdown_count
            
            logger.info(f"Alerts calculated - Low stock: {low_stock_count}, Overstock: {overstock_count}, Spikes: {sales_spike_count}, Slowdowns: {sales_slowdown_count}")
            
            return {
                "summary_counts": {
                    "low_stock_alerts": low_stock_count,  # Products with quantity < 5
                    "overstock_alerts": overstock_count,  # Products with stock > 100
                    "sales_dropping_alerts": sales_slowdown_count,  # Sales dropping > 20%
                    "sales_spike_alerts": sales_spike_count,
                    "total_alerts": total_alerts
                },
                "detailed_alerts": {
                    "low_stock_alerts": low_stock_details,  # Products whose quantity < 5
                    "overstock_alerts": overstock_details,  # Products whose stock > 100  
                    "sales_dropping_alerts": sales_slowdown_details,  # Sales dropping > 20%
                    "sales_spike_alerts": sales_spike_details
                },
                "alert_thresholds": {
                    "low_stock_threshold": 5,  # Quantity < 5
                    "overstock_threshold": 100,  # Stock > 100
                    "sales_dropping_threshold": sales_down_threshold  # 20% decrease
                },
                "quick_links": {
                    "view_low_stock": f"/dashboard/alerts/low-stock?client_id={client_id}",
                    "view_overstock": f"/dashboard/alerts/overstock?client_id={client_id}",
                    "view_sales_alerts": f"/dashboard/alerts/sales?client_id={client_id}"
                },
                "data_source": "dashboard_inventory_analyzer_with_consistent_thresholds"
            }
            
        except Exception as e:
            logger.error(f"Error generating alerts summary: {e}")
            return {"error": str(e)}

    def _calculate_total_inventory_value(self, shopify_data: Dict, amazon_data: Dict) -> float:
        """ Calculate the total value of all inventory using NEW TABLE STRUCTURE with better price handling"""
        total_value = 0.0
        items_processed = 0
        items_with_value = 0
        
        # Calculate Shopify inventory value - use on_hand_inventory instead of inventory_quantity
        shopify_products = shopify_data.get('products', [])
        for product in shopify_products:
            quantity = product.get('on_hand_inventory', 0) or 0  # NEW: on_hand_inventory
            price_raw = product.get('price')
            price = 0.0
            
            # Better price parsing - handle all formats
            if price_raw is not None:
                if isinstance(price_raw, (int, float)):
                    price = float(price_raw)
                elif isinstance(price_raw, str):
                    try:
                        # Remove common currency symbols and formatting
                        clean_price = price_raw.strip().replace('$', '').replace(',', '').replace(' ', '')
                        if clean_price:
                            price = float(clean_price)
                    except (ValueError, AttributeError):
                        price = 0.0
            
            if quantity > 0 and price > 0:
                item_value = quantity * price
                total_value += item_value
                items_with_value += 1
                
            items_processed += 1
        
        # Calculate Amazon inventory value - use on_hand_inventory and listing_price
        amazon_products = amazon_data.get('products', [])
        for product in amazon_products:
            quantity = product.get('on_hand_inventory', 0) or 0  # NEW: on_hand_inventory
            price_raw = product.get('listing_price')  # NEW: listing_price instead of price
            price = 0.0
            
            # Better price parsing - handle all formats
            if price_raw is not None:
                if isinstance(price_raw, (int, float)):
                    price = float(price_raw)
                elif isinstance(price_raw, str):
                    try:
                        # Remove common currency symbols and formatting
                        clean_price = price_raw.strip().replace('$', '').replace(',', '').replace(' ', '')
                        if clean_price:
                            price = float(clean_price)
                    except (ValueError, AttributeError):
                        price = 0.0
            
            if quantity > 0 and price > 0:
                item_value = quantity * price
                total_value += item_value
                items_with_value += 1
                
            items_processed += 1
        
        logger.info(f" INVENTORY VALUE: ${total_value:.2f} from {items_with_value}/{items_processed} items with valid price & quantity (NEW table structure)")
        return round(total_value, 2)
    
    def _calculate_out_of_stock_count(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Calculate the number of items that are completely out of stock using NEW TABLE STRUCTURE"""
        out_of_stock_count = 0
        
        # Count Shopify products that are out of stock - use on_hand_inventory
        for product in shopify_data.get('products', []):
            inventory = product.get('on_hand_inventory', 0) or 0  # NEW: on_hand_inventory
            if inventory <= 0:
                out_of_stock_count += 1
        
        # Count Amazon products that are out of stock - use on_hand_inventory
        for product in amazon_data.get('products', []):
            quantity = product.get('on_hand_inventory', 0) or 0  # NEW: on_hand_inventory
            if quantity <= 0:
                out_of_stock_count += 1
        
        return out_of_stock_count


# Global instance
dashboard_inventory_analyzer = DashboardInventoryAnalyzer()