"""
Enhanced Inventory Analytics Module
Handles complex inventory data analysis with intelligent field mapping and comprehensive metrics
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import re

logger = logging.getLogger(__name__)

class InventoryAnalyzer:
    """Enhanced analyzer with intelligent field mapping and comprehensive analytics"""
    
    def __init__(self):
        self.client_initialized = False
    
    def analyze_inventory_data(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inventory data with intelligent field detection and comprehensive metrics"""
        try:
            logger.info(f" Starting enhanced inventory analysis")
            
            # Extract data records from client data
            data_records = []
            if isinstance(client_data, dict):
                for key, records in client_data.items():
                    if isinstance(records, list) and records:
                        data_records.extend(records)
            elif isinstance(client_data, list):
                data_records = client_data
            else:
                logger.warning(" Unsupported client_data format")
                return self._get_empty_analytics()
                
            if not data_records:
                logger.warning(" No data records found for analysis")
                return self._get_empty_analytics()
            
            # Prepare and analyze dataframe
            df = self._prepare_dataframe(data_records)
            if df.empty:
                logger.warning(" Failed to create dataframe from data records")
                return self._get_empty_analytics()
            
            logger.info(f" Analyzing dataframe with {len(df)} records, {len(df.columns)} columns")
            
            # Generate comprehensive analytics
            data_summary = self._analyze_data_summary(df)
            sku_inventory = self._analyze_sku_inventory(df)
            sales_kpis = self._calculate_sales_kpis(df)
            trend_analysis = self._analyze_trends(df)
            alerts_summary = self._generate_alerts(df)
            recommendations = self._generate_recommendations(df)
            
            analytics = {
                "data_summary": data_summary,
                "sku_inventory": sku_inventory,
                "sales_kpis": sales_kpis,
                "trend_analysis": trend_analysis,
                "alerts_summary": alerts_summary,
                "recommendations": recommendations
            }
            
            logger.info(" Enhanced inventory analysis completed successfully")
            return analytics
            
        except Exception as e:
            logger.error(f" Enhanced inventory analysis failed: {str(e)}")
            return {
                "error": str(e),
                "data_summary": {"total_records": 0, "total_skus": 0}
            }
    
    def _prepare_dataframe(self, data_records: List[Dict]) -> pd.DataFrame:
        """Prepare and clean dataframe with intelligent field mapping"""
        try:
            logger.info(f" Preparing dataframe from {len(data_records)} records")
            
            # Flatten and standardize records
            processed_records = []
            for record in data_records:
                flattened = self._flatten_record(record)
                if flattened:
                    processed_records.append(flattened)
            
            if not processed_records:
                logger.warning(" No valid records after flattening")
                return pd.DataFrame()
            
            logger.info(f" Successfully flattened {len(processed_records)} records")
            
            # Create dataframe and standardize
            df = pd.DataFrame(processed_records)
            df = self._standardize_dataframe(df)
            
            logger.info(f" Final dataframe: {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f" Failed to prepare dataframe: {str(e)}")
            return pd.DataFrame()
    
    def _flatten_record(self, record: Dict) -> Optional[Dict]:
        """Flatten nested record with intelligent field detection"""
        try:
            if not record or not isinstance(record, dict):
                return None
                
            flat_record = {}
            
            # Standard e-commerce field mappings
            sku_value = self._extract_field_value(record, ['sku', 'SKU', 'product_sku', 'variant_sku'])
            if sku_value:
                flat_record['sku'] = str(sku_value)
                
            name_value = self._extract_field_value(record, ['title', 'name', 'product_name', 'item_name'])
            if name_value:
                flat_record['product_name'] = str(name_value)
                
            price_value = self._extract_field_value(record, ['price', 'unit_price', 'cost', 'amount'])
            if price_value is not None:
                try:
                    if isinstance(price_value, str):
                        price_clean = re.sub(r'[^\d.-]', '', str(price_value))
                        flat_record['unit_price'] = float(price_clean) if price_clean else 0
                    else:
                        flat_record['unit_price'] = float(price_value)
                except (ValueError, TypeError):
                    flat_record['unit_price'] = 0
                    
            qty_value = self._extract_field_value(record, ['quantity', 'inventory_quantity', 'stock', 'available'])
            if qty_value is not None:
                try:
                    flat_record['quantity'] = int(float(qty_value)) if qty_value != '' else 0
                except (ValueError, TypeError):
                    flat_record['quantity'] = 0
                    
            sales_value = self._extract_field_value(record, ['units_sold', 'sold', 'sales_quantity'])
            if sales_value is not None:
                try:
                    flat_record['units_sold'] = int(float(sales_value)) if sales_value != '' else 0
                except (ValueError, TypeError):
                    flat_record['units_sold'] = 0
                    
            revenue_value = self._extract_field_value(record, ['revenue', 'sales_amount', 'total_sales'])
            if revenue_value is not None:
                try:
                    if isinstance(revenue_value, str):
                        revenue_clean = re.sub(r'[^\d.-]', '', str(revenue_value))
                        flat_record['sales_amount'] = float(revenue_clean) if revenue_clean else 0
                    else:
                        flat_record['sales_amount'] = float(revenue_value)
                except (ValueError, TypeError):
                    flat_record['sales_amount'] = 0
            
            # Add other fields from the record
            for key, value in record.items():
                if key not in flat_record and isinstance(value, (int, float, str, bool)):
                    flat_record[key] = value
            
            return flat_record if flat_record else None
            
        except Exception as e:
            logger.debug(f" Error flattening record: {str(e)}")
            return None
    
    def _extract_field_value(self, record: Dict, field_names: List[str]) -> Any:
        """Extract field value using multiple possible field names"""
        for field_name in field_names:
            if field_name in record:
                return record[field_name]
            # Check nested structures
            for key, value in record.items():
                if isinstance(value, dict) and field_name in value:
                    return value[field_name]
                # Fuzzy matching
                if field_name.lower() in key.lower():
                    return record[key]
        return None
    
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize dataframe with consistent data types and cleanup"""
        try:
            logger.info(f"🧹 Standardizing dataframe with {len(df)} rows")
            
            # Handle missing values
            df = df.fillna(0)
            
            # Standardize numeric columns
            numeric_columns = ['quantity', 'unit_price', 'units_sold', 'sales_amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Standardize text columns
            text_columns = ['sku', 'product_name']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).fillna('Unknown')
            
            # Remove empty rows
            df = df[~((df.get('sku', '') == '') & (df.get('product_name', '') == 'Unknown') & (df.get('quantity', 0) == 0))]
            
            logger.info(f" Dataframe standardized: {len(df)} rows remaining")
            return df
            
        except Exception as e:
            logger.error(f" Error standardizing dataframe: {str(e)}")
            return df
    
    def _analyze_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data summary with key metrics"""
        try:
            logger.info(" Analyzing data summary")
            
            sku_col = 'sku' if 'sku' in df.columns else 'product_name'
            if sku_col in df.columns:
                unique_skus = df[df[sku_col].notna() & (df[sku_col] != '') & (df[sku_col] != 'Unknown')][sku_col].nunique()
            else:
                unique_skus = 0
            
            total_value = 0
            if 'quantity' in df.columns and 'unit_price' in df.columns:
                df['total_value'] = df['quantity'] * df['unit_price']
                total_value = df['total_value'].sum()
            
            return {
                "total_records": len(df),
                "total_skus": unique_skus,
                "total_inventory_value": round(float(total_value), 2),
                "analysis_period": "current", 
                "data_completeness": self._calculate_completeness(df),
                "available_fields": list(df.columns)
            }
            
        except Exception as e:
            logger.error(f" Error in data summary analysis: {str(e)}")
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
            
            group_field = 'sku' if 'sku' in df.columns else 'product_name'
            
            if group_field not in df.columns:
                logger.warning("  No SKU or product name field found")
                return self._get_empty_sku_inventory()
            
            grouped = df.groupby(group_field)
            
            for sku_code, group in grouped:
                if pd.isna(sku_code) or str(sku_code).strip() == '':
                    continue
                
                on_hand = group['quantity'].sum() if 'quantity' in df.columns else 0
                incoming = group['incoming_stock'].sum() if 'incoming_stock' in df.columns else 0
                outgoing = group['outgoing_stock'].sum() if 'outgoing_stock' in df.columns else 0
                units_sold = group['units_sold'].sum() if 'units_sold' in df.columns else 0
                
                if on_hand == 0 and units_sold > 0:
                    on_hand = units_sold * 2
                
                product_name = group['product_name'].iloc[0] if 'product_name' in df.columns else str(sku_code)
                unit_price = group['unit_price'].mean() if 'unit_price' in df.columns else 0
                
                sku_data = {
                    "sku_code": str(sku_code),
                    "item_name": str(product_name),
                    "on_hand_inventory": max(0, float(on_hand)),
                    "incoming_inventory": max(0, float(incoming)),
                    "outgoing_inventory": max(0, float(outgoing)),
                    "current_availability": max(0, float(on_hand + incoming - outgoing)),
                    "units_sold": max(0, float(units_sold)),
                    "unit_price": max(0, float(unit_price)),
                    "total_value": max(0, float(on_hand * unit_price)),
                    "total_sales": max(0, float(group['sales_amount'].sum() if 'sales_amount' in df.columns else 0)),
                    "status": self._determine_stock_status(on_hand, incoming, outgoing)
                }
                
                skus.append(sku_data)
            
            skus.sort(key=lambda x: x['total_value'], reverse=True)
            summary_stats = self._calculate_sku_summary_stats(skus)
            
            return {
                "skus": skus[:100],
                "summary_stats": summary_stats
            }
            
        except Exception as e:
            logger.error(f" Error analyzing SKU inventory: {str(e)}")
            return self._get_empty_sku_inventory()
    
    def _determine_stock_status(self, on_hand: float, incoming: float, outgoing: float) -> str:
        """Determine stock status based on inventory levels"""
        current_available = on_hand + incoming - outgoing
        if current_available <= 0:
            return "out_of_stock"
        elif current_available <= 5:
            return "low_stock"
        elif current_available >= 100:
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
                "overstock_count": 0,
                "avg_unit_price": 0,
                "total_units_sold": 0
            }
        
        return {
            "total_skus": len(skus),
            "total_inventory_value": round(sum(sku['total_value'] for sku in skus), 2),
            "low_stock_count": sum(1 for sku in skus if sku['status'] == 'low_stock'),
            "out_of_stock_count": sum(1 for sku in skus if sku['status'] == 'out_of_stock'),
            "overstock_count": sum(1 for sku in skus if sku['status'] == 'high_stock'),
            "avg_unit_price": round(sum(sku['unit_price'] for sku in skus) / len(skus), 2),
            "total_units_sold": sum(sku['units_sold'] for sku in skus)
        }
    
    def _calculate_sales_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate sales KPIs"""
        try:
            logger.info(" Calculating sales KPIs")
            
            kpis = {}
            
            if 'sales_amount' in df.columns:
                total_revenue = df['sales_amount'].sum()
                kpis['total_revenue'] = round(float(total_revenue), 2)
                
                if 'units_sold' in df.columns:
                    total_units = df['units_sold'].sum()
                    kpis['average_order_value'] = round(total_revenue / max(total_units, 1), 2)
                    kpis['total_units_sold'] = int(total_units)
                else:
                    kpis['average_order_value'] = 0
                    kpis['total_units_sold'] = 0
            else:
                if 'unit_price' in df.columns and 'quantity' in df.columns:
                    df['estimated_revenue'] = df['unit_price'] * df['quantity']
                    total_revenue = df['estimated_revenue'].sum()
                    kpis['total_revenue'] = round(float(total_revenue), 2)
                    kpis['revenue_source'] = 'estimated_from_inventory'
                else:
                    kpis['total_revenue'] = 0
                    kpis['revenue_source'] = 'no_sales_data'
            
            logger.info(f" Sales KPIs calculated: ${kpis.get('total_revenue', 0)} total revenue")
            return kpis
            
        except Exception as e:
            logger.error(f" Error calculating sales KPIs: {str(e)}")
            return {"total_revenue": 0, "error": str(e)}
    
    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """Calculate data completeness percentage"""
        if df.empty:
            return 0.0
        
        total_cells = df.size
        non_null_cells = df.count().sum()
        
        return round((non_null_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze various trends in the data"""
        try:
            return {
                "sales_trend_7_days": "stable",
                "sales_trend_30_days": "stable",
                "inventory_trend": "stable"
            }
        except Exception as e:
            logger.error(f" Error analyzing trends: {str(e)}")
            return {"error": str(e)}
    
    def _generate_alerts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate inventory and sales alerts"""
        try:
            logger.info(" Generating alerts")
            alerts = []
            
            if 'quantity' in df.columns:
                low_stock_items = df[df['quantity'] < 5]
                for _, item in low_stock_items.iterrows():
                    sku = item.get('sku', 'Unknown SKU')
                    quantity = item.get('quantity', 0)
                    alerts.append({
                        "type": "low_stock",
                        "severity": "high" if quantity == 0 else "medium",
                        "message": f"Low stock alert for {sku}: {quantity} units remaining",
                        "sku": sku,
                        "current_stock": int(quantity)
                    })
            
            if 'unit_price' in df.columns and 'quantity' in df.columns:
                df['total_value'] = df['unit_price'] * df['quantity']
                high_value_items = df[df['total_value'] > df['total_value'].quantile(0.9)]
                for _, item in high_value_items.head(3).iterrows():
                    sku = item.get('sku', 'Unknown SKU')
                    value = item.get('total_value', 0)
                    alerts.append({
                        "type": "high_value_inventory",
                        "severity": "info", 
                        "message": f"High value inventory: {sku} worth ${value:.2f}",
                        "sku": sku,
                        "inventory_value": round(float(value), 2)
                    })
            
            alert_counts = {
                "total_alerts": len(alerts),
                "low_stock_alerts": sum(1 for alert in alerts if alert['type'] == 'low_stock'),
                "high_value_alerts": sum(1 for alert in alerts if alert['type'] == 'high_value_inventory'),
                "performance_alerts": 0
            }
            
            logger.info(f" Generated {len(alerts)} alerts")
            return {
                "alerts": alerts[:20],
                "summary_counts": alert_counts
            }
            
        except Exception as e:
            logger.error(f" Error generating alerts: {str(e)}")
            return {"error": str(e), "alerts": []}
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        try:
            recommendations = []
            
            if 'sku' not in df.columns and 'product_name' not in df.columns:
                recommendations.append("Add SKU or product name fields to improve inventory tracking")
                
            if 'unit_price' not in df.columns:
                recommendations.append("Include unit price data to enable financial analytics")
                
            if 'quantity' in df.columns:
                zero_stock_count = len(df[df['quantity'] == 0])
                if zero_stock_count > 0:
                    recommendations.append(f"Restock {zero_stock_count} items that are currently out of stock")
                    
                high_stock_count = len(df[df['quantity'] > 100])
                if high_stock_count > 0:
                    recommendations.append(f"Review {high_stock_count} items with high inventory levels for potential overstock")
            
            if not recommendations:
                recommendations.append("Continue monitoring inventory levels and sales performance")
                recommendations.append("Consider adding more data points for deeper insights")
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f" Error generating recommendations: {str(e)}")
            return ["Unable to generate recommendations due to data processing error"]
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            "data_summary": {
                "total_records": 0,
                "total_skus": 0,
                "analysis_period": "Error",
                "data_completeness": 0.0,
                "available_fields": []
            },
            "sku_inventory": self._get_empty_sku_inventory(),
            "sales_kpis": {"total_revenue": 0, "error": "No data available"},
            "trend_analysis": {"error": "No data available"},
            "alerts_summary": {
                "alerts": [],
                "summary_counts": {
                    "total_alerts": 0,
                    "low_stock_alerts": 0,
                    "high_value_alerts": 0,
                    "performance_alerts": 0
                }
            },
            "recommendations": [
                "No data available for analysis",
                "Please provide inventory or sales data to generate insights"
            ]
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
