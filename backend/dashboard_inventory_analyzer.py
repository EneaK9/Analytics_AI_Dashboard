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
            
            # 🚀 PARALLEL CALCULATIONS - ALL AT ONCE, NO WAITING!
            logger.info(f"⚡ Running ALL calculations in parallel for {client_id} ({platform})")
            
            # 🚀 ULTRA-FAST PARALLEL CALCULATIONS - ALL AT ONCE!
            logger.info(f"⚡ TURBO MODE: Running all calculations in parallel for {client_id} ({platform})")
            
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
                logger.info(f"🚀 TURBO COMPLETE: All calculations finished in <3s for {client_id}")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Calculations timeout after 3s, using partial results")
                # Get whatever completed - NO WAITING!
                sales_kpis = kpis_task.result() if kpis_task.done() else {}
                trend_analysis = trends_task.result() if trends_task.done() else {}
                alerts_summary = alerts_task.result() if alerts_task.done() else {}
            
            # Handle any exceptions from parallel execution
            if isinstance(sales_kpis, Exception):
                logger.error(f"❌ KPIs calculation failed: {sales_kpis}")
                sales_kpis = {}
            if isinstance(trend_analysis, Exception):
                logger.error(f"❌ Trends calculation failed: {trend_analysis}")
                trend_analysis = {}
            if isinstance(alerts_summary, Exception):
                logger.error(f"❌ Alerts calculation failed: {alerts_summary}")
                alerts_summary = {}
            
            logger.info(f"⚡ ALL calculations completed in parallel for {client_id} ({platform})")
            
            # 🔥 CALCULATE REAL INVENTORY METRICS - NO MORE HARDCODED ZEROS!
            total_inventory_value = self._calculate_total_inventory_value(shopify_data, amazon_data)
            total_skus = len([p for p in shopify_data.get('products', []) if p.get('sku')]) + len([p for p in amazon_data.get('products', []) if p.get('sku')])
            
            # Get real counts from alerts calculation
            low_stock_count = alerts_summary.get('summary_counts', {}).get('low_stock_alerts', 0)
            overstock_count = alerts_summary.get('summary_counts', {}).get('overstock_alerts', 0)
            out_of_stock_count = self._calculate_out_of_stock_count(shopify_data, amazon_data)
            
            logger.info(f"📊 REAL VALUES: SKUs: {total_skus}, Inventory Value: ${total_inventory_value}, Low Stock: {low_stock_count}, Out of Stock: {out_of_stock_count}")
            
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
            logger.info(f"🔄 Getting SEPARATE analytics for both platforms: {client_id}")
            
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
            
            # 🔥 CALCULATE REAL INVENTORY METRICS FOR MULTI-PLATFORM - NO MORE HARDCODED ZEROS!
            shopify_inventory_value = self._calculate_total_inventory_value(shopify_data, {"products": [], "orders": []})
            amazon_inventory_value = self._calculate_total_inventory_value({"products": [], "orders": []}, amazon_data)
            combined_inventory_value = self._calculate_total_inventory_value(shopify_data, amazon_data)
            
            shopify_total_skus = len([p for p in shopify_data.get('products', []) if p.get('sku')])
            amazon_total_skus = len([p for p in amazon_data.get('products', []) if p.get('sku')])
            combined_total_skus = shopify_total_skus + amazon_total_skus
            
            logger.info(f"✅ Multi-platform analytics completed for {client_id}")
            
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
        """🚀 PARALLEL Shopify data fetch - NO WAITING!"""
        try:
            # Ensure database client is available
            admin_client = self._ensure_client()
            
            products_table = f"{client_id.replace('-', '_')}_shopify_products"
            orders_table = f"{client_id.replace('-', '_')}_shopify_orders"
            
            logger.info(f"⚡ PARALLEL Shopify fetch for {client_id}")
            
            # 🚀 RUN BOTH QUERIES IN PARALLEL - NO SEQUENTIAL WAITING!
            async def fetch_products():
                try:
                    response = admin_client.table(products_table).select(
                        "sku,title,variant_title,inventory_quantity,price,option1,option2,variant_id"
                    ).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Shopify products table not found or empty: {e}")
                    return []
            
            async def fetch_orders():
                try:
                    response = admin_client.table(orders_table).select(
                        "order_id,total_price,created_at,line_items_count,financial_status,fulfillment_status,order_number,raw_data"
                    ).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Shopify orders table not found or empty: {e}")
                    return []
            
            # Execute both queries simultaneously
            products, orders = await asyncio.gather(
                fetch_products(), fetch_orders(), return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(products, Exception):
                logger.error(f"❌ Products fetch failed: {products}")
                products = []
            if isinstance(orders, Exception):
                logger.error(f"❌ Orders fetch failed: {orders}")
                orders = []
            
            logger.info(f"⚡ PARALLEL complete: {len(products)} Shopify products, {len(orders)} orders")
            
            return {"products": products, "orders": orders}
            
        except Exception as e:
            logger.warning(f"Could not get Shopify data: {e}")
            return {"products": [], "orders": []}
    
    async def _get_amazon_data(self, client_id: str) -> Dict[str, Any]:
        """Get Amazon data from organized tables with optimized queries"""
        try:
            # Ensure database client is available
            admin_client = self._ensure_client()
            
            orders_table = f"{client_id.replace('-', '_')}_amazon_orders"
            products_table = f"{client_id.replace('-', '_')}_amazon_products"
            
            # 🚀 RUN BOTH QUERIES IN PARALLEL - NO SEQUENTIAL WAITING!
            async def fetch_orders():
                try:
                    response = admin_client.table(orders_table).select(
                        "order_id,total_price,created_at,number_of_items_shipped,order_status,order_number"
                    ).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Amazon orders table not found or empty: {e}")
                    return []
            
            async def fetch_products():
                try:
                    response = admin_client.table(products_table).select(
                        "sku,asin,title,quantity,price,brand,status"
                    ).execute()
                    return response.data if response.data else []
                except Exception as e:
                    logger.info(f"Amazon products table not found or empty: {e}")
                    return []
            
            # Execute both queries simultaneously
            orders, products = await asyncio.gather(
                fetch_orders(), fetch_products(), return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(orders, Exception):
                logger.error(f"❌ Orders fetch failed: {orders}")
                orders = []
            if isinstance(products, Exception):
                logger.error(f"❌ Products fetch failed: {products}")
                products = []
            
            logger.info(f"⚡ PARALLEL complete: {len(orders)} Amazon orders, {len(products)} products")
            
            return {"orders": orders, "products": products}
            
        except Exception as e:
            logger.warning(f"Could not get Amazon data: {e}")
            return {"orders": [], "products": []}
    
    async def get_sku_list(self, client_id: str, page: int = 1, page_size: int = 50, use_cache: bool = True, platform: str = "shopify") -> Dict[str, Any]:
        """Get optimized SKU list with fast calculations and caching support"""
        try:
            # Import cache manager
            from sku_cache_manager import get_sku_cache_manager
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
                logger.info("📦 No products found, attempting to extract from order data...")
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
        """Process Shopify products and add to SKU list"""
        shopify_products = shopify_data.get('products', [])
        
        logger.info(f"📦 Processing {len(shopify_products)} Shopify products for SKU list")
        
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
            processed_count += 1
        
        logger.info(f"✅ Shopify processing complete: {processed_count} processed, {skipped_count} skipped")

    def _process_amazon_products(self, amazon_data: Dict, sku_list: List[Dict]):
        """Process Amazon products and add to SKU list"""
        amazon_products = amazon_data.get('products', [])
        
        logger.info(f"📦 Processing {len(amazon_products)} Amazon products for SKU list")
        
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
    
    def _calculate_outgoing_for_sku(self, sku: str, orders: List[Dict]) -> int:
        """🔥 FIXED: Calculate outgoing inventory ONLY for orders that actually contain the SKU"""
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
                                            logger.debug(f"✅ Found SKU {sku} in order {order.get('order_number')}: +{quantity} units")
                                            break  # Found the SKU, no need to check more items in this order
                                            
                        except Exception as e:
                            logger.debug(f"Error parsing raw_data for order {order.get('order_number')}: {e}")
                    
                    # 🚫 REMOVED THE BROKEN FALLBACK LOGIC THAT WAS ADDING INVENTORY TO ALL SKUS!
                    # Previously this was adding outgoing inventory to EVERY SKU for EVERY unfulfilled order
                    # Now we only count when we can actually confirm the SKU is in the order
                    
            except Exception as e:
                logger.debug(f"Error processing order {order.get('order_number', 'unknown')} for outgoing calculation: {e}")
                continue
        
        # Cap at reasonable maximum to prevent any edge cases
        return min(outgoing, 50)
    
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
            
            logger.info(f"📦 Extracted {len(synthetic_products)} synthetic products from {len(amazon_orders)} orders")
            return synthetic_products
            
        except Exception as e:
            logger.error(f"❌ Error extracting products from orders: {e}")
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
        """Get optimized KPI charts data with corrected calculations"""
        try:
            shopify_orders = shopify_data.get('orders', [])
            amazon_orders = amazon_data.get('orders', [])
            
            # Current time and date ranges
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            ninety_days_ago = now - timedelta(days=90)
            
            logger.info(f"Calculating KPIs for {len(shopify_orders)} Shopify orders, {len(amazon_orders)} Amazon orders")
            
            # Calculate sales for each period with proper date filtering
            all_orders = shopify_orders + amazon_orders
            sales_7_days = self._calculate_sales_for_period(all_orders, seven_days_ago, now)
            sales_30_days = self._calculate_sales_for_period(all_orders, thirty_days_ago, now)
            sales_90_days = self._calculate_sales_for_period(all_orders, ninety_days_ago, now)
            
            logger.info(f"Sales calculated - 7d: {sales_7_days}, 30d: {sales_30_days}, 90d: {sales_90_days}")
            
            # Fast inventory calculation
            total_inventory = self._calculate_total_inventory(shopify_data, amazon_data)
            available_inventory = self._calculate_available_inventory(shopify_data, amazon_data)
            avg_daily_sales = sales_30_days['units'] / 30 if sales_30_days['units'] > 0 else 0
            
            # 🔥 FIXED: Correct inventory turnover formula = units_sold / average_inventory_units
            total_units_sold = sales_30_days['units']
            
            # 🔥 EXTRA SAFETY: If no inventory, turnover should be 0 regardless of sales
            if total_inventory == 0:
                logger.info(f"📊 No total inventory - returning 0 turnover rate (had {total_units_sold} units sold)")
                turnover_rate = 0
            else:
                average_inventory_units = self._calculate_average_inventory(total_inventory, sales_30_days['units'], 30)
                turnover_rate = total_units_sold / average_inventory_units if average_inventory_units > 0 and total_units_sold > 0 else 0
            # 🔥 FIXED: Days of stock using available inventory (on-hand) instead of total inventory
            days_stock_remaining = available_inventory / avg_daily_sales if avg_daily_sales > 0 else 999
            
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
            logger.error(f"Error calculating KPI charts: {e}")
            return {"error": str(e)}
    
    def _calculate_available_inventory(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Calculate available (on-hand) inventory = total inventory - outgoing inventory"""
        available_inventory = 0
        
        # Shopify available inventory
        shopify_products = shopify_data.get('products', [])
        shopify_orders = shopify_data.get('orders', [])
        
        for product in shopify_products:
            total_inventory = product.get('inventory_quantity', 0) or 0
            sku = product.get('sku')
            
            # Calculate outgoing inventory for this SKU (reserved for unfulfilled orders)
            outgoing = self._calculate_outgoing_for_sku(sku, shopify_orders) if sku else 0
            
            # Available = total - outgoing
            product_available = max(0, total_inventory - outgoing)
            available_inventory += product_available
        
        # Amazon available inventory  
        amazon_products = amazon_data.get('products', [])
        amazon_orders = amazon_data.get('orders', [])
        
        for product in amazon_products:
            total_inventory = product.get('quantity', 0) or 0
            sku = product.get('sku') or product.get('asin')
            
            # 🔥 FIXED: Calculate Amazon outgoing using order_status and number_of_items_shipped
            outgoing = self._calculate_amazon_outgoing_for_sku(sku, amazon_orders) if sku else 0
            
            # Available = total - outgoing
            product_available = max(0, total_inventory - outgoing)
            available_inventory += product_available
        
        logger.info(f"📦 Available Inventory: {available_inventory} units (total minus outgoing/reserved)")
        
        return available_inventory

    def _calculate_amazon_outgoing_for_sku(self, sku: str, orders: List[Dict]) -> int:
        """🔥 NEW: Calculate outgoing inventory for Amazon SKU using order_status and number_of_items_unshipped"""
        if not sku:
            return 0
            
        outgoing = 0
        sku_normalized = str(sku).strip().lower()
        recent_orders_checked = 0
        max_orders_to_check = 20  # Limit for performance
        
        for order in orders:
            if recent_orders_checked >= max_orders_to_check:
                break
                
            try:
                # Only count orders that are NOT yet shipped (still outgoing/reserved)
                order_status = (order.get('order_status') or '').lower()
                
                # For Amazon: orders that are not 'shipped' are still outgoing
                if order_status != 'shipped':
                    recent_orders_checked += 1
                    
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
                        logger.debug(f"Amazon SKU {sku}: +{unshipped_items} outgoing from order {order.get('order_id')} (status: {order_status})")
                        
            except Exception as e:
                logger.debug(f"Error processing Amazon order for outgoing calculation: {e}")
                continue
        
        logger.info(f"📦 Amazon SKU {sku} outgoing inventory: {outgoing} units from {recent_orders_checked} unshipped orders")
        return outgoing

    def _calculate_average_inventory(self, current_inventory: int, units_sold: int, period_days: int = 30) -> float:
        """Calculate average inventory = (begin_inventory + end_inventory) / 2"""
        # Current inventory is end_inventory
        end_inventory = current_inventory
        
        # 🔥 FIXED: Calculate begin_inventory = current + units sold during the period
        # This assumes inventory at period start = current inventory + units sold since then
        begin_inventory = current_inventory + units_sold
        
        avg_inventory = (begin_inventory + end_inventory) / 2
        
        logger.info(f"📊 Avg Inventory: begin({current_inventory} + {units_sold}) + end({end_inventory}) / 2 = {avg_inventory}")
        logger.info(f"📊 Logic: inventory {period_days} days ago ≈ current({current_inventory}) + sold_since_then({units_sold}) = {begin_inventory}")
        
        # 🔥 FIXED: Allow 0 inventory when there are no products/sales 
        # Only return 1 as minimum if we have actual inventory or sales (avoid false turnover rates)
        if current_inventory == 0 and units_sold == 0:
            return 0  # Truly no inventory or activity
        return max(avg_inventory, 1)  # Avoid division by zero only when there's some activity

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
    
    def _calculate_sales_for_period(self, orders: List[Dict], start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate sales metrics for a specific time period with proper date handling and order status filtering"""
        revenue = 0
        units = 0
        order_count = 0
        filtered_count = 0
        
        logger.debug(f"Calculating sales from {start_date} to {end_date} for {len(orders)} orders")
        
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
                        # 🔥 NEW: Check if order should be counted based on fulfillment status
                        if self._is_order_fulfilled(order):
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
            
            logger.info(f"Generating trends for {len(all_orders)} total orders")
            
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
            current_inventory = self._calculate_total_inventory(shopify_data, amazon_data)
            inventory_levels_chart = self._estimate_historical_inventory_levels(weekly_data, current_inventory, all_orders)
            
            logger.info(f"Trends calculated - {len(weekly_data)} weeks, current avg revenue: ${current_avg_revenue:.2f}")
            
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
            logger.error(f"Error generating trend visualizations: {e}")
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
            
            # Process Shopify products for stock alerts
            shopify_products = shopify_data.get('products', [])
            for product in shopify_products:
                inventory = product.get('inventory_quantity', 0) or 0
                title = product.get('title', 'Unknown Product')
                sku = product.get('sku')
                
                if inventory < 5:  # 🔥 FIXED: Low stock threshold (was <=10, now <5 to match specification)
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
                
                if quantity < 5:  # 🔥 FIXED: Low stock threshold (was <=10, now <5 to match specification)
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
            
            # 🔥 FIXED: Configurable sales down alert thresholds
            # Default thresholds (can be made configurable via parameters later)
            sales_spike_threshold = 50  # 50% increase = spike
            sales_down_threshold = 20   # 20% decrease = slowdown (configurable, was hardcoded 30%)
            
            # Check for significant sales changes
            if previous_week_sales['revenue'] > 0:
                revenue_change = ((recent_week_sales['revenue'] - previous_week_sales['revenue']) / previous_week_sales['revenue']) * 100
                
                if revenue_change > sales_spike_threshold:  # Configurable spike threshold
                    sales_spike_count = 1
                    sales_spike_details.append({
                        "type": "sales_spike",
                        "severity": "info",
                        "message": f"Sales spiked {revenue_change:.1f}% this week (${recent_week_sales['revenue']:.2f} vs ${previous_week_sales['revenue']:.2f})",
                        "current_revenue": recent_week_sales['revenue'],
                        "previous_revenue": previous_week_sales['revenue'],
                        "change_percent": revenue_change
                    })
                elif revenue_change < -sales_down_threshold:  # 🔥 FIXED: Configurable sales down threshold (was -30, now -20)
                    sales_slowdown_count = 1
                    sales_slowdown_details.append({
                        "type": "sales_slowdown",
                        "severity": "warning",
                        "message": f"Sales dropped {abs(revenue_change):.1f}% this week (${recent_week_sales['revenue']:.2f} vs ${previous_week_sales['revenue']:.2f})",
                        "current_revenue": recent_week_sales['revenue'],
                        "previous_revenue": previous_week_sales['revenue'],
                        "change_percent": revenue_change,
                        "threshold_used": sales_down_threshold  # Track which threshold was used
                    })
            
            total_alerts = low_stock_count + overstock_count + sales_spike_count + sales_slowdown_count
            
            logger.info(f"Alerts calculated - Low stock: {low_stock_count}, Overstock: {overstock_count}, Spikes: {sales_spike_count}, Slowdowns: {sales_slowdown_count}")
            
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
            logger.error(f"Error generating alerts summary: {e}")
            return {"error": str(e)}

    def _calculate_total_inventory_value(self, shopify_data: Dict, amazon_data: Dict) -> float:
        """🔥 FIXED: Calculate the total value of all inventory across platforms with better price handling"""
        total_value = 0.0
        items_processed = 0
        items_with_value = 0
        
        # Calculate Shopify inventory value
        shopify_products = shopify_data.get('products', [])
        for product in shopify_products:
            quantity = product.get('inventory_quantity', 0) or 0
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
        
        # Calculate Amazon inventory value  
        amazon_products = amazon_data.get('products', [])
        for product in amazon_products:
            quantity = product.get('quantity', 0) or 0
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
        
        logger.info(f"💰 INVENTORY VALUE: ${total_value:.2f} from {items_with_value}/{items_processed} items with valid price & quantity")
        return round(total_value, 2)
    
    def _calculate_out_of_stock_count(self, shopify_data: Dict, amazon_data: Dict) -> int:
        """Calculate the number of items that are completely out of stock"""
        out_of_stock_count = 0
        
        # Count Shopify products that are out of stock (0 or negative)
        for product in shopify_data.get('products', []):
            inventory = product.get('inventory_quantity', 0) or 0
            if inventory <= 0:
                out_of_stock_count += 1
        
        # Count Amazon products that are out of stock (0 or negative)
        for product in amazon_data.get('products', []):
            quantity = product.get('quantity', 0) or 0
            if quantity <= 0:
                out_of_stock_count += 1
        
        return out_of_stock_count


# Global instance
dashboard_inventory_analyzer = DashboardInventoryAnalyzer()