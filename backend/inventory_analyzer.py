"""
Comprehensive Inventory Analytics Module
Analyzes client data to extract inventory metrics, sales KPIs, trends, and alerts
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class InventoryAnalyzer:
    """Comprehensive inventory analytics for client data"""
    
    def __init__(self):
        self.client_data = None
        self.processed_data = None
        
    def analyze_inventory_data(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis function that processes client data and returns comprehensive inventory analytics
        """
        try:
            logger.info(f"🔍 Starting comprehensive inventory analysis for client {client_data.get('client_id', 'unknown')}")
            
            self.client_data = client_data
            data_records = client_data.get('data', [])
            
            if not data_records:
                logger.warning("⚠️  No data records found, returning empty analytics")
                return self._get_empty_analytics()
            
            logger.info(f"📊 Processing {len(data_records)} data records")
            
            # Convert to DataFrame for easier analysis
            df = self._prepare_dataframe(data_records)
            
            if df.empty:
                logger.warning("⚠️  No valid records after processing, returning empty analytics")
                return self._get_empty_analytics()
            
            # Perform comprehensive analysis
            analytics = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": f"Successfully analyzed {len(df)} records",
                "data_summary": self._analyze_data_summary(df),
                "sku_inventory": self._analyze_sku_inventory(df),
                "sales_kpis": self._calculate_sales_kpis(df),
                "trend_analysis": self._analyze_trends(df),
                "alerts_summary": self._generate_alerts(df),
                "recommendations": self._generate_recommendations(df)
            }
            
            logger.info(f"✅ Inventory analysis completed successfully")
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error in inventory analysis: {str(e)}")
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "message": f"Analysis failed: {str(e)}",
                "error": str(e),
                **self._get_empty_analytics()
            }

    def _prepare_dataframe(self, data_records: List[Dict]) -> pd.DataFrame:
        """Convert raw data records to a structured DataFrame"""
        try:
            # Flatten and normalize data records
            flattened_records = []
            
            for record in data_records:
                # Handle nested structures and extract relevant fields
                flat_record = self._flatten_record(record)
                if flat_record:
                    flattened_records.append(flat_record)
            
            if not flattened_records:
                return pd.DataFrame()
            
            df = pd.DataFrame(flattened_records)
            
            # Standardize column names and data types
            df = self._standardize_dataframe(df)
            
            logger.info(f"📋 Prepared DataFrame with {len(df)} rows and columns: {list(df.columns)}")
            
            # Debug: Show sample of actual data for better field mapping
            if len(flattened_records) > 0:
                sample_record = flattened_records[0]
                logger.info(f"🔍 Sample record keys: {list(sample_record.keys())}")
                
                # Show a few sample values to understand data structure
                for key, value in list(sample_record.items())[:10]:
                    logger.info(f"  {key}: {type(value).__name__} = {str(value)[:100]}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error preparing DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _flatten_record(self, record: Dict) -> Optional[Dict]:
        """Flatten a single record and extract relevant inventory/sales fields"""
        try:
            flat_record = {}
            
            # Check if this is Amazon order data and handle specially
            if self._is_amazon_order_data(record):
                return self._extract_from_amazon_order(record)
            
            # Comprehensive field mappings for inventory data - expanded to catch more variations
            field_mappings = {
                # Product/SKU identifiers - be more careful with 'id' to avoid order_id confusion
                'sku': ['sku', 'sku_code', 'product_id', 'item_id', 'product_code', 'code', 'item_code', 
                       'product_sku', 'barcode', 'upc', 'part_number', 'catalog_number', 'model', 'asin'],
                'product_name': ['product_name', 'item_name', 'name', 'product', 'item', 'title', 'description',
                               'product_title', 'item_description', 'product_description', 'goods', 'article'],
                
                # Inventory quantities - expanded list
                'quantity': ['quantity', 'qty', 'stock', 'inventory', 'on_hand', 'available', 'count', 'units',
                           'on_hand_qty', 'current_qty', 'stock_qty', 'available_qty', 'balance', 'level'],
                'stock_level': ['stock_level', 'current_stock', 'available_stock', 'inventory_level'],
                'incoming_stock': ['incoming', 'incoming_stock', 'pending_receipts', 'inbound', 'ordered', 'purchase_qty'],
                'outgoing_stock': ['outgoing', 'outgoing_stock', 'pending_shipments', 'allocated', 'reserved', 'committed'],
                
                # Sales data - expanded list
                'sales_amount': ['sales', 'revenue', 'amount', 'total', 'value', 'sales_value', 'gross_sales',
                               'net_sales', 'total_sales', 'revenue_amount', 'sales_total', 'order_total',
                               'line_total', 'subtotal', 'gross_amount', 'net_amount'],
                'units_sold': ['units_sold', 'quantity_sold', 'sold', 'sales_qty', 'qty_sold', 'sold_qty',
                             'sales_units', 'units', 'volume', 'pieces_sold'],
                'unit_price': ['price', 'unit_price', 'cost', 'rate', 'selling_price', 'list_price',
                             'retail_price', 'wholesale_price', 'unit_cost', 'item_price'],
                
                # Date fields - expanded list
                'date': ['date', 'timestamp', 'created_at', 'sale_date', 'transaction_date', 'order_date',
                        'invoice_date', 'purchase_date', 'delivery_date', 'ship_date', 'created', 'time'],
                'order_date': ['order_date', 'order_timestamp', 'ordered_at', 'purchase_time'],
                
                # Customer/region - expanded list
                'customer': ['customer', 'customer_id', 'client', 'customer_name', 'buyer', 'account'],
                'region': ['region', 'location', 'territory', 'state', 'country', 'city', 'area', 'zone'],
                
                # Additional business fields
                'category': ['category', 'product_category', 'item_category', 'type', 'classification'],
                'supplier': ['supplier', 'vendor', 'manufacturer', 'brand'],
                'cost': ['cost', 'purchase_cost', 'wholesale_cost', 'cogs', 'cost_price'],
                'profit': ['profit', 'margin', 'profit_margin', 'gross_profit'],
                'discount': ['discount', 'discount_amount', 'promotion', 'rebate']
            }
            
            # Extract and map fields using standard mapping
            for target_field, possible_names in field_mappings.items():
                value = self._extract_field_value(record, possible_names)
                if value is not None:
                    flat_record[target_field] = value
            
            # If we didn't find much data, try intelligent field detection
            if len(flat_record) < 3:  # If we found very few fields
                intelligent_data = self._intelligent_field_detection(record)
                
                # Try to map the intelligent fields to our standard fields
                numeric_fields = intelligent_data['numeric_fields']
                text_fields = intelligent_data['text_fields']
                date_fields = intelligent_data['date_fields']
                
                # Smart field mapping for e-commerce/order data
                self._smart_ecommerce_mapping(flat_record, record, numeric_fields, text_fields)
                
                # Auto-assign date fields
                if date_fields and 'date' not in flat_record:
                    first_date_key = list(date_fields.keys())[0]
                    flat_record['date'] = date_fields[first_date_key]
                    logger.info(f"🎯 Auto-mapped '{first_date_key}' as date")
            
            # Add metadata
            flat_record['_source_type'] = record.get('_source_type', 'unknown')
            flat_record['_source_file'] = record.get('_source_file', 'unknown')
            flat_record['_record_id'] = record.get('_record_id', 'unknown')
            
            return flat_record if flat_record else None
            
        except Exception as e:
            logger.warning(f"⚠️  Error flattening record: {str(e)}")
            return None
    
    def _is_amazon_order_data(self, record: Dict) -> bool:
        """Check if this record is Amazon order data"""
        try:
            # Check for Amazon-specific order fields
            amazon_order_indicators = [
                'order_id' in record and 'marketplace_id' in record,
                'order_id' in record and record.get('platform', '').lower() == 'amazon',
                'order_id' in record and 'sales_channel' in record and 'amazon' in str(record.get('sales_channel', '')).lower(),
                'order_id' in record and 'number_of_items_shipped' in record,
                'order_id' in record and len(str(record.get('order_id', ''))) > 10  # Amazon order IDs are long
            ]
            
            return any(amazon_order_indicators)
        except:
            return False
    
    def _extract_from_amazon_order(self, record: Dict) -> Optional[Dict]:
        """Extract product information from Amazon order data"""
        try:
            # For Amazon orders, we need to create synthetic product records
            # since we don't have actual product data
            
            order_id = record.get('order_id', '')
            total_price = record.get('total_price', 0)
            items_shipped = record.get('number_of_items_shipped', 1)
            items_unshipped = record.get('number_of_items_unshipped', 0)
            
            # Calculate estimated unit price
            unit_price = total_price / max(items_shipped, 1) if items_shipped > 0 else total_price
            
            # Create a synthetic SKU from order information
            # Convert order_id to string to handle both int and string types
            order_id_str = str(order_id)
            synthetic_sku = f"AMZ-ORDER-{order_id_str[-8:]}"  # Last 8 chars of order ID
            
            # Try to extract more meaningful product info if available
            product_name = "Amazon Order Item"
            if 'product_name' in record:
                product_name = record['product_name']
            elif 'title' in record:
                product_name = record['title']
            
            return {
                'sku': synthetic_sku,
                'product_name': product_name,
                'sales_amount': total_price,
                'unit_price': unit_price,
                'units_sold': items_shipped,
                'quantity': 0,  # No inventory data available from orders
                'date': record.get('created_at') or record.get('updated_at'),
                'category': 'amazon_order',
                '_source_type': record.get('_source_type', 'amazon_order'),
                '_source_file': record.get('_source_file', 'amazon_order'),
                '_record_id': record.get('_record_id', order_id_str),
                '_original_order_id': order_id_str  # Keep reference to original order
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting from Amazon order: {e}")
            return None
    
    def _extract_field_value(self, record: Dict, field_names: List[str]) -> Any:
        """Extract value from record using multiple possible field names"""
        for field_name in field_names:
            # Check direct field
            if field_name in record:
                return record[field_name]
            
            # Check case-insensitive
            for key, value in record.items():
                if key.lower() == field_name.lower():
                    return value
                    
            # Check partial matches (if field name contains the target)
            for key, value in record.items():
                if field_name.lower() in key.lower() and len(key) < 50:  # Avoid matching very long strings
                    return value
                    
            # Check nested fields (one level deep)
            for key, value in record.items():
                if isinstance(value, dict):
                    for nested_key, nested_value in value.items():
                        if nested_key.lower() == field_name.lower():
                            return nested_value
                        # Also check partial matches in nested fields
                        if field_name.lower() in nested_key.lower() and len(nested_key) < 50:
                            return nested_value
        
        return None
    
    def _intelligent_field_detection(self, record: Dict) -> Dict[str, Any]:
        """Intelligently detect and extract any relevant fields from the record"""
        extracted = {}
        
        # Look for any field that might contain numbers (potential quantities, prices, etc.)
        numeric_fields = {}
        text_fields = {}
        date_fields = {}
        
        for key, value in record.items():
            # Skip metadata fields
            if key.startswith('_'):
                continue
                
            # Try to categorize fields by content
            if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                numeric_fields[key] = value
            elif isinstance(value, str) and len(value) < 100:  # Reasonable length text
                text_fields[key] = value
            elif 'date' in key.lower() or 'time' in key.lower():
                date_fields[key] = value
        
        # If we have very few mapped fields, try to guess from the intelligent detection
        logger.info(f"🧠 Intelligent field detection found:")
        logger.info(f"  Numeric fields: {list(numeric_fields.keys())}")
        logger.info(f"  Text fields: {list(text_fields.keys())}")
        logger.info(f"  Date fields: {list(date_fields.keys())}")
        
        return {
            'numeric_fields': numeric_fields,
            'text_fields': text_fields,
            'date_fields': date_fields
        }
    
    def _smart_ecommerce_mapping(self, flat_record: Dict, record: Dict, numeric_fields: Dict, text_fields: Dict):
        """Smart mapping for e-commerce/order data"""
        
        # E-commerce specific field mapping
        ecommerce_mappings = {
            # Units sold mappings
            'units_sold': ['number_of_items_shipped', 'items_shipped', 'qty_shipped', 'quantity_sold', 'items_sold'],
            
            # Sales amount mappings  
            'sales_amount': ['total_price', 'order_total', 'total_amount', 'gross_amount', 'net_amount'],
            
            # SKU/Product ID mappings (for e-commerce, order_id can serve as identifier)
            'sku': ['order_id', 'order_number', 'transaction_id', 'item_id'],
            
            # Product name (combine platform + channel for e-commerce)
            'platform': ['platform', 'marketplace', 'channel'],
            'sales_channel': ['sales_channel', 'channel', 'marketplace_name'],
            
            # Additional e-commerce fields
            'order_status': ['order_status', 'status', 'fulfillment_status'],
            'currency': ['currency', 'currency_code'],
        }
        
        # Apply e-commerce specific mappings
        for target_field, possible_names in ecommerce_mappings.items():
            if target_field not in flat_record:
                value = self._extract_field_value(record, possible_names)
                if value is not None:
                    flat_record[target_field] = value
                    logger.info(f"🛒 E-commerce mapped '{possible_names[0]}' as {target_field}: {value}")
        
        # Create synthetic product name from platform + sales_channel if we don't have a proper product name
        if 'product_name' not in flat_record:
            platform = flat_record.get('platform', '')
            channel = flat_record.get('sales_channel', '')
            if platform or channel:
                product_name = f"{platform} {channel}".strip()
                if product_name:
                    flat_record['product_name'] = product_name
                    logger.info(f"🎯 Created synthetic product_name: {product_name}")
        
        # If we have total_price but not unit_price, and we have units_sold, calculate unit_price
        if 'unit_price' not in flat_record and 'sales_amount' in flat_record and 'units_sold' in flat_record:
            try:
                sales_amount = float(flat_record['sales_amount'])
                units_sold = float(flat_record['units_sold'])
                if units_sold > 0:
                    unit_price = sales_amount / units_sold
                    flat_record['unit_price'] = unit_price
                    logger.info(f"📊 Calculated unit_price: ${unit_price:.2f}")
            except (ValueError, TypeError):
                pass
        
        # If we still don't have enough fields, fall back to basic auto-assignment
        if len([k for k in flat_record.keys() if not k.startswith('_')]) < 3:
            self._fallback_auto_assignment(flat_record, numeric_fields, text_fields)
    
    def _fallback_auto_assignment(self, flat_record: Dict, numeric_fields: Dict, text_fields: Dict):
        """Fallback auto-assignment if specific mappings don't work"""
        
        # Auto-assign first text field as product name if we don't have one
        if 'product_name' not in flat_record and text_fields:
            first_text_key = list(text_fields.keys())[0]
            flat_record['product_name'] = text_fields[first_text_key]
            logger.info(f"🎯 Fallback mapped '{first_text_key}' as product_name")
        
        # Auto-assign first text field as SKU if we don't have one and have multiple text fields
        if 'sku' not in flat_record and len(text_fields) > 1:
            sku_key = list(text_fields.keys())[1] if len(text_fields) > 1 else list(text_fields.keys())[0]
            flat_record['sku'] = text_fields[sku_key]
            logger.info(f"🎯 Fallback mapped '{sku_key}' as sku")
        
        # Auto-assign numeric fields to likely categories
        numeric_keys = list(numeric_fields.keys())
        if numeric_keys:
            # First numeric field might be quantity/units_sold
            if 'quantity' not in flat_record and 'units_sold' not in flat_record:
                flat_record['units_sold'] = numeric_fields[numeric_keys[0]]
                logger.info(f"🎯 Fallback mapped '{numeric_keys[0]}' as units_sold")
            
            # Find the largest numeric value (likely sales amount)
            largest_value_key = max(numeric_keys, key=lambda k: float(numeric_fields[k]) if isinstance(numeric_fields[k], (int, float)) else 0)
            if 'sales_amount' not in flat_record and largest_value_key:
                flat_record['sales_amount'] = numeric_fields[largest_value_key]
                logger.info(f"🎯 Fallback mapped '{largest_value_key}' as sales_amount (largest value)")
            
            # If we have both sales_amount and units_sold, calculate unit_price
            if 'unit_price' not in flat_record and 'sales_amount' in flat_record and 'units_sold' in flat_record:
                try:
                    sales_amount = float(flat_record['sales_amount'])
                    units_sold = float(flat_record['units_sold'])
                    if units_sold > 0:
                        unit_price = sales_amount / units_sold
                        flat_record['unit_price'] = unit_price
                        logger.info(f"📊 Calculated unit_price from sales/units: ${unit_price:.2f}")
                except (ValueError, TypeError):
                    pass
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types and clean the DataFrame"""
        try:
            # Convert numeric fields - expanded to include e-commerce fields
            numeric_fields = ['quantity', 'stock_level', 'incoming_stock', 'outgoing_stock', 
                            'sales_amount', 'units_sold', 'unit_price', 'total_price', 
                            'number_of_items_shipped', 'number_of_items_unshipped']
            
            for field in numeric_fields:
                if field in df.columns:
                    df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)
            
            # Convert date fields
            date_fields = ['date', 'order_date']
            for field in date_fields:
                if field in df.columns:
                    df[field] = pd.to_datetime(df[field], errors='coerce')
            
            # Clean string fields - expanded to include e-commerce fields
            string_fields = ['sku', 'product_name', 'customer', 'region', 'platform', 
                           'sales_channel', 'order_status', 'currency', 'order_id']
            for field in string_fields:
                if field in df.columns:
                    df[field] = df[field].astype(str).str.strip()
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error standardizing DataFrame: {str(e)}")
            return df
    
    def _analyze_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall data quality and summary statistics"""
        try:
            total_records = len(df)
            
            # Count distinct SKUs/products
            sku_count = df['sku'].nunique() if 'sku' in df.columns else 0
            product_count = df['product_name'].nunique() if 'product_name' in df.columns else 0
            total_skus = max(sku_count, product_count)
            
            # Determine analysis period
            if 'date' in df.columns and not df['date'].isna().all():
                min_date = df['date'].min()
                max_date = df['date'].max()
                analysis_period = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
            else:
                analysis_period = "Date range unknown"
            
            # Calculate data completeness - be more flexible about what constitutes good data
            important_fields = ['sku', 'product_name', 'quantity', 'sales_amount']
            available_fields = sum(1 for field in important_fields if field in df.columns and not df[field].isna().all())
            data_completeness = available_fields / len(important_fields)
            
            # If basic inventory fields are missing, check if we have any meaningful business data
            if data_completeness < 0.25:
                # Look for any fields that might contain business data
                business_like_fields = [col for col in df.columns if not col.startswith('_') and col != 'date']
                if business_like_fields:
                    # Adjust completeness score if we have some business-like fields
                    data_completeness = min(0.5, len(business_like_fields) / 10)  # Cap at 50% for auto-detected fields
            
            return {
                "total_records": total_records,
                "total_skus": total_skus,
                "analysis_period": analysis_period,
                "data_completeness": round(data_completeness, 2),
                "available_fields": list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing data summary: {str(e)}")
            return {
                "total_records": 0,
                "total_skus": 0,
                "analysis_period": "Error",
                "data_completeness": 0.0,
                "available_fields": []
            }
    
    def _analyze_sku_inventory(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze SKU-level inventory data"""
        try:
            skus = []
            
            # Group by SKU or product name
            group_field = 'sku' if 'sku' in df.columns else 'product_name'
            
            if group_field not in df.columns:
                logger.warning("⚠️  No SKU or product name field found")
                return self._get_empty_sku_inventory()
            
            grouped = df.groupby(group_field)
            
            for sku_code, group in grouped:
                if pd.isna(sku_code) or str(sku_code).strip() == '':
                    continue
                
                # Calculate inventory metrics - handle e-commerce data where we might not have traditional inventory
                on_hand = group['quantity'].sum() if 'quantity' in df.columns else group['stock_level'].sum() if 'stock_level' in df.columns else 0
                incoming = group['incoming_stock'].sum() if 'incoming_stock' in df.columns else 0
                outgoing = group['outgoing_stock'].sum() if 'outgoing_stock' in df.columns else 0
                
                # For e-commerce data, units_sold represents actual sales, not outgoing inventory
                units_sold = group['units_sold'].sum() if 'units_sold' in df.columns else 0
                
                # If we don't have traditional inventory but have sales data, estimate inventory based on sales
                if on_hand == 0 and units_sold > 0:
                    # Estimate on-hand inventory as a multiple of recent sales (conservative approach)
                    on_hand = units_sold * 2  # Assume 2x recent sales as reasonable inventory level
                    logger.info(f"📦 Estimated inventory for {sku_code}: {on_hand} units (based on {units_sold} units sold)")
                
                # If we don't have explicit outgoing, use units_sold
                if outgoing == 0 and units_sold > 0:
                    outgoing = units_sold
                
                # Get product name
                product_name = group['product_name'].iloc[0] if 'product_name' in df.columns else str(sku_code)
                
                # Calculate unit price (average)
                unit_price = group['unit_price'].mean() if 'unit_price' in df.columns else group['sales_amount'].sum() / max(group['units_sold'].sum(), 1) if 'sales_amount' in df.columns and 'units_sold' in df.columns else 0
                
                sku_data = {
                    "sku_code": str(sku_code),
                    "item_name": str(product_name),
                    "on_hand_inventory": max(0, float(on_hand)),
                    "incoming_inventory": max(0, float(incoming)),
                    "outgoing_inventory": max(0, float(outgoing)),
                    "current_availability": max(0, float(on_hand + incoming - outgoing)),
                    "units_sold": max(0, float(units_sold)),  # Add units_sold to the output
                    "unit_price": max(0, float(unit_price)),
                    "total_value": max(0, float(on_hand * unit_price)),
                    "total_sales": max(0, float(group['sales_amount'].sum() if 'sales_amount' in df.columns else 0)),
                    "status": self._determine_stock_status(on_hand, incoming, outgoing)
                }
                
                skus.append(sku_data)
            
            # Sort by total value descending
            skus.sort(key=lambda x: x['total_value'], reverse=True)
            
            # Calculate summary statistics
            summary_stats = self._calculate_sku_summary_stats(skus)
            
            return {
                "skus": skus,  # Return ALL SKUs - no limit
                "summary_stats": summary_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing SKU inventory: {str(e)}")
            return self._get_empty_sku_inventory()
    
    def _determine_stock_status(self, on_hand: float, incoming: float, outgoing: float) -> str:
        """Determine stock status based on inventory levels"""
        current_availability = on_hand + incoming - outgoing
        
        if current_availability <= 0:
            return "out_of_stock"
        elif current_availability < 10:  # Low stock threshold
            return "low_stock"
        elif on_hand > 100:  # High stock threshold
            return "high_stock"
        else:
            return "normal_stock"
    
    def _calculate_sku_summary_stats(self, skus: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for SKU inventory"""
        if not skus:
            return {
                "total_skus": 0,
                "total_inventory_value": 0,
                "low_stock_count": 0,
                "out_of_stock_count": 0,
                "overstock_count": 0
            }
        
        total_value = sum(sku['total_value'] for sku in skus)
        low_stock_count = sum(1 for sku in skus if sku['status'] == 'low_stock')
        out_of_stock_count = sum(1 for sku in skus if sku['status'] == 'out_of_stock')
        overstock_count = sum(1 for sku in skus if sku['status'] == 'high_stock')
        
        return {
            "total_skus": len(skus),
            "total_inventory_value": round(total_value, 2),
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "overstock_count": overstock_count
        }
    
    def _calculate_sales_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate sales KPIs for different time periods"""
        try:
            # Use timezone-aware datetime to match pandas datetime objects
            from datetime import timezone
            current_date = datetime.now(timezone.utc)
            
            # Initialize KPIs with default values
            kpis = {
                "total_sales_7_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "total_sales_30_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "total_sales_90_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "inventory_turnover_rate": {"value": 0, "display_value": "0.0x", "trend": "neutral"},
                "days_of_stock_remaining": {"value": 0, "display_value": "0 days", "trend": "neutral"},
                "average_order_value": {"value": 0, "display_value": "$0.00"},
                "total_active_skus": 0
            }
            
            # Check if we have date and sales data
            if 'date' not in df.columns or 'sales_amount' not in df.columns:
                logger.warning("⚠️  Missing date or sales data for KPI calculation")
                return kpis
            
            # Filter out records with invalid dates
            df_with_dates = df[df['date'].notna()].copy()
            
            if df_with_dates.empty:
                logger.warning("⚠️  No records with valid dates")
                return kpis
            
            # Calculate sales for different periods
            for days, kpi_key in [(7, 'total_sales_7_days'), (30, 'total_sales_30_days'), (90, 'total_sales_90_days')]:
                cutoff_date = current_date - timedelta(days=days)
                period_sales = df_with_dates[df_with_dates['date'] >= cutoff_date]['sales_amount'].sum()
                
                kpis[kpi_key] = {
                    "value": round(period_sales, 2),
                    "display_value": f"${period_sales:,.2f}",
                    "trend": self._calculate_trend(df_with_dates, days)
                }
            
            # Calculate inventory turnover rate - handle e-commerce data
            total_inventory = df['quantity'].sum() if 'quantity' in df.columns else 0
            total_units_sold = df['units_sold'].sum() if 'units_sold' in df.columns else 0
            
            # For e-commerce data without traditional inventory, use sales velocity instead
            if total_inventory > 0:
                turnover_rate = total_units_sold / total_inventory
                kpis["inventory_turnover_rate"] = {
                    "value": round(turnover_rate, 2),
                    "display_value": f"{turnover_rate:.1f}x",
                    "trend": "positive" if turnover_rate > 1 else "neutral"
                }
            elif total_units_sold > 0:
                # For e-commerce: calculate sales velocity (units sold per day)
                days_in_period = 30  # Consider last 30 days
                sales_velocity = total_units_sold / days_in_period
                kpis["inventory_turnover_rate"] = {
                    "value": round(sales_velocity, 2),
                    "display_value": f"{sales_velocity:.1f} units/day",
                    "trend": "positive" if sales_velocity > 1 else "neutral"
                }
            
            # Calculate days of stock remaining
            if total_units_sold > 0:
                daily_sales_rate = total_units_sold / 30  # Approximate daily rate
                days_remaining = total_inventory / daily_sales_rate if daily_sales_rate > 0 else 0
                kpis["days_of_stock_remaining"] = {
                    "value": round(days_remaining, 0),
                    "display_value": f"{days_remaining:.0f} days",
                    "trend": "negative" if days_remaining < 30 else "neutral"
                }
            
            # Calculate average order value
            if 'sales_amount' in df.columns and len(df) > 0:
                avg_order_value = df['sales_amount'].mean()
                kpis["average_order_value"] = {
                    "value": round(avg_order_value, 2),
                    "display_value": f"${avg_order_value:.2f}"
                }
            
            # Count active SKUs - consider both traditional and e-commerce data
            if 'sku' in df.columns:
                kpis["total_active_skus"] = df['sku'].nunique()
            elif 'product_name' in df.columns:
                kpis["total_active_skus"] = df['product_name'].nunique()
            elif 'order_id' in df.columns:
                # For pure order data, count unique orders as proxy for active products
                kpis["total_active_skus"] = df['order_id'].nunique()
            
            return kpis
            
        except Exception as e:
            logger.error(f"❌ Error calculating sales KPIs: {str(e)}")
            return {
                "total_sales_7_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "total_sales_30_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "total_sales_90_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "inventory_turnover_rate": {"value": 0, "display_value": "0.0x", "trend": "neutral"},
                "days_of_stock_remaining": {"value": 0, "display_value": "0 days", "trend": "neutral"},
                "average_order_value": {"value": 0, "display_value": "$0.00"},
                "total_active_skus": 0
            }
    
    def _calculate_trend(self, df: pd.DataFrame, days: int) -> str:
        """Calculate trend direction for a given period"""
        try:
            from datetime import timezone
            current_date = datetime.now(timezone.utc)
            current_period_start = current_date - timedelta(days=days)
            previous_period_start = current_date - timedelta(days=days*2)
            previous_period_end = current_period_start
            
            current_sales = df[df['date'] >= current_period_start]['sales_amount'].sum()
            previous_sales = df[(df['date'] >= previous_period_start) & (df['date'] < previous_period_end)]['sales_amount'].sum()
            
            if previous_sales == 0:
                return "neutral"
            
            change_percent = ((current_sales - previous_sales) / previous_sales) * 100
            
            if change_percent > 5:
                return "positive"
            elif change_percent < -5:
                return "negative"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in inventory and sales data"""
        return {
            "daily_sales_trends": [],
            "daily_inventory_trends": [],
            "weekly_sales_trends": [],
            "sales_comparison": {},
            "trend_summary": {"overall_direction": "neutral", "growth_rate": 0, "volatility": 0}
        }
    
    def _generate_alerts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate inventory and sales alerts"""
        try:
            alerts = {
                "low_stock_alerts": [],
                "overstock_alerts": [],
                "sales_spike_alerts": [],
                "sales_slowdown_alerts": [],
                "summary": {
                    "total_alerts": 0,
                    "critical_alerts": 0,
                    "high_priority_alerts": 0,
                    "affected_skus": [],
                    "total_affected_skus": 0
                }
            }
            
            # Group by SKU for alert analysis
            group_field = 'sku' if 'sku' in df.columns else 'product_name'
            
            if group_field not in df.columns:
                return alerts
            
            grouped = df.groupby(group_field)
            affected_skus = set()
            
            for sku_code, group in grouped:
                if pd.isna(sku_code):
                    continue
                
                # Low stock alerts
                current_stock = group['quantity'].sum() if 'quantity' in df.columns else 0
                if current_stock < 10:  # Low stock threshold
                    severity = "critical" if current_stock == 0 else "high"
                    alerts["low_stock_alerts"].append({
                        "sku": str(sku_code),
                        "product_name": str(group['product_name'].iloc[0]) if 'product_name' in df.columns else str(sku_code),
                        "current_stock": int(current_stock),
                        "threshold": 10,
                        "severity": severity,
                        "message": f"Stock level critically low" if current_stock == 0 else f"Stock level below threshold"
                    })
                    affected_skus.add(str(sku_code))
            
            # Calculate summary
            total_alerts = len(alerts["low_stock_alerts"])
            critical_alerts = sum(1 for alert in alerts["low_stock_alerts"] if alert["severity"] == "critical")
            high_priority_alerts = sum(1 for alert in alerts["low_stock_alerts"] if alert["severity"] == "high")
            
            alerts["summary"] = {
                "total_alerts": total_alerts,
                "critical_alerts": critical_alerts,
                "high_priority_alerts": high_priority_alerts,
                "affected_skus": list(affected_skus),
                "total_affected_skus": len(affected_skus)
            }
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error generating alerts: {str(e)}")
            return {
                "low_stock_alerts": [],
                "overstock_alerts": [],
                "sales_spike_alerts": [],
                "sales_slowdown_alerts": [],
                "summary": {
                    "total_alerts": 0,
                    "critical_alerts": 0,
                    "high_priority_alerts": 0,
                    "affected_skus": [],
                    "total_affected_skus": 0
                }
            }
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on the analysis"""
        try:
            recommendations = []
            
            # Analyze data quality
            if len(df) < 100:
                recommendations.append("Consider uploading more comprehensive data for better analytics accuracy")
            
            # Check for missing critical fields
            critical_fields = ['sku', 'product_name', 'quantity', 'sales_amount', 'date']
            missing_fields = [field for field in critical_fields if field not in df.columns or df[field].isna().all()]
            
            if missing_fields:
                recommendations.append(f"Improve data completeness by including: {', '.join(missing_fields)}")
            
            # Add default recommendations if none generated
            if not recommendations:
                recommendations = [
                    "Continue monitoring inventory levels and sales performance",
                    "Consider implementing automated alerts for low stock situations"
                ]
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {str(e)}")
            return ["Enable more comprehensive data collection for better recommendations"]
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            "data_summary": {
                "total_records": 0,
                "total_skus": 0,
                "analysis_period": "No data",
                "data_completeness": 0.0
            },
            "sku_inventory": self._get_empty_sku_inventory(),
            "sales_kpis": {
                "total_sales_7_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "total_sales_30_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "total_sales_90_days": {"value": 0, "display_value": "$0.00", "trend": "neutral"},
                "inventory_turnover_rate": {"value": 0, "display_value": "0.0x", "trend": "neutral"},
                "days_of_stock_remaining": {"value": 0, "display_value": "0 days", "trend": "neutral"},
                "average_order_value": {"value": 0, "display_value": "$0.00"},
                "total_active_skus": 0
            },
            "trend_analysis": {
                "daily_sales_trends": [],
                "daily_inventory_trends": [],
                "weekly_sales_trends": [],
                "sales_comparison": {},
                "trend_summary": {"overall_direction": "neutral", "growth_rate": 0, "volatility": 0}
            },
            "alerts_summary": {
                "low_stock_alerts": [],
                "overstock_alerts": [],
                "sales_spike_alerts": [],
                "sales_slowdown_alerts": [],
                "summary": {
                    "total_alerts": 0,
                    "critical_alerts": 0,
                    "high_priority_alerts": 0,
                    "affected_skus": [],
                    "total_affected_skus": 0
                }
            },
            "recommendations": ["Upload inventory and sales data to enable comprehensive analytics"]
        }
    
    def _get_empty_sku_inventory(self) -> Dict[str, Any]:
        """Return empty SKU inventory structure"""
        return {
            "skus": [],
            "summary_stats": {
                "total_skus": 0,
                "total_inventory_value": 0,
                "low_stock_count": 0,
                "out_of_stock_count": 0,
                "overstock_count": 0
            }
        }

# Create global instance
inventory_analyzer = InventoryAnalyzer()

# Create global instance
inventory_analyzer = InventoryAnalyzer()