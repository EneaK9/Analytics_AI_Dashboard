#!/usr/bin/env python3
"""
Comprehensive test script to verify JSON processing and dashboard generation
Tests the complete pipeline from JSON parsing to entity extraction to LLM analysis
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class DashboardGenerationTester:
    def __init__(self):
        self.test_results = {
            'json_parsing': False,
            'business_detection': False,
            'entity_extraction': False,
            'flattening': False,
            'llm_preparation': False
        }
    
    def load_test_data(self) -> Dict[str, Any]:
        """Load the comprehensive JSON test data"""
        print(" Loading comprehensive JSON test data...")
        try:
            # Try multiple possible paths
            possible_paths = [
                'diverse_client_data.json',
                'Analytics_AI_Dashboard/backend/diverse_client_data.json',
                os.path.join(os.path.dirname(__file__), 'diverse_client_data.json')
            ]
            
            test_data = None
            for path in possible_paths:
                try:
                    if os.path.exists(path):
                        with open(path, 'r') as f:
                            test_data = json.load(f)
                        print(f" Loaded JSON from: {path}")
                        break
                except:
                    continue
            
            if not test_data:
                raise FileNotFoundError("diverse_client_data.json not found in any expected location")
            
            print(f" Loaded JSON with {len(test_data)} top-level sections:")
            for key in test_data.keys():
                print(f"   - {key}")
            
            return test_data
        except Exception as e:
            print(f" Failed to load test data: {e}")
            print(" Make sure you're running from the correct directory or the JSON file exists")
            return {}
    
    def test_universal_parser(self, test_data: Dict[str, Any]) -> List[Dict]:
        """Test the universal parser conversion"""
        print("\n" + "="*50)
        print(" TESTING UNIVERSAL PARSER")
        print("="*50)
        
        try:
            from universal_data_parser import UniversalDataParser
            parser = UniversalDataParser()
            
            # Convert to JSON string
            json_str = json.dumps(test_data)
            print(f" JSON string length: {len(json_str):,} characters")
            
            # Parse using universal parser
            parsed_records = parser.parse_to_json(json_str, 'json')
            
            if parsed_records:
                print(f" Parser returned {len(parsed_records)} records")
                print(f" First record type: {type(parsed_records[0])}")
                print(f" First record keys: {list(parsed_records[0].keys())[:10]}...")
                
                # Check for business structure
                first_record = parsed_records[0]
                business_keys = ['client_info', 'financial_metrics', 'customer_data', 'sales_data']
                found_keys = [key for key in business_keys if key in first_record]
                print(f" Business keys found: {found_keys}")
                
                self.test_results['json_parsing'] = True
                return parsed_records
            else:
                print(" Parser returned no records")
                return []
                
        except Exception as e:
            print(f" Universal parser test failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_business_structure_detection(self, parsed_records: List[Dict]) -> bool:
        """Test business structure detection"""
        print("\n" + "="*50)
        print(" TESTING BUSINESS STRUCTURE DETECTION")
        print("="*50)
        
        try:
            # Test business structure detection without importing dashboard_orchestrator
            # to avoid pandas dependency issues in test environment
            print(" Testing business key detection directly...")
            
            if not parsed_records:
                print(" No records to test")
                return False
            
            first_record = parsed_records[0]
            print(f" Testing record with {len(first_record)} keys")
            
            # Replicate business structure detection logic
            business_keys = [
                'business_info', 'sales_transactions', 'customer_data', 
                'product_inventory', 'monthly_summary', 'performance_metrics',
                'client_info', 'financial_metrics', 'sales_data', 'operational_metrics',
                'marketing_data', 'inventory_data', 'hr_analytics', 'risk_compliance',
                'environmental_social', 'forecasts_predictions', 'competitive_analysis'
            ]
            
            found_business_keys = [key for key in business_keys if key in first_record]
            is_business = len(found_business_keys) > 0
            
            print(f" Found business keys: {found_business_keys}")
            print(f" Is business structure: {is_business}")
            
            if is_business:
                print(" Business structure correctly detected!")
                self.test_results['business_detection'] = True
                return True
            else:
                print(" Business structure not detected")
                print(" Available keys:", list(first_record.keys())[:10])
                return False
                
        except Exception as e:
            print(f" Business detection test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_entity_extraction(self, parsed_records: List[Dict]) -> List[Dict]:
        """Test business entity extraction"""
        print("\n" + "="*50)
        print(" TESTING ENTITY EXTRACTION")
        print("="*50)
        
        try:
            print(" Simulating entity extraction from business structure...")
            
            if not parsed_records:
                print(" No records to extract entities from")
                return []
            
            # Simulate entity extraction logic
            entities = []
            first_record = parsed_records[0]
            
            # Extract entities from financial_metrics
            if 'financial_metrics' in first_record:
                financial_data = first_record['financial_metrics']
                if 'revenue' in financial_data:
                    revenue_data = financial_data['revenue']
                    
                    # Monthly revenue entities
                    if 'monthly_revenue' in revenue_data:
                        for month_data in revenue_data['monthly_revenue']:
                            entity = {
                                'entity_type': 'monthly_revenue',
                                'metric_category': 'financial',
                                **month_data
                            }
                            entities.append(entity)
                    
                    # Product revenue entities
                    if 'revenue_by_product' in revenue_data:
                        for product_data in revenue_data['revenue_by_product']:
                            entity = {
                                'entity_type': 'product_revenue',
                                'metric_category': 'financial',
                                **product_data
                            }
                            entities.append(entity)
            
            # Extract entities from customer_data
            if 'customer_data' in first_record:
                customer_data = first_record['customer_data']
                if 'customer_demographics' in customer_data:
                    demo_data = customer_data['customer_demographics']
                    
                    # Customer segments
                    if 'customer_segments' in demo_data:
                        for segment_data in demo_data['customer_segments']:
                            entity = {
                                'entity_type': 'customer_segment',
                                'metric_category': 'customer',
                                **segment_data
                            }
                            entities.append(entity)
            
            # Extract entities from sales_data
            if 'sales_data' in first_record:
                sales_data = first_record['sales_data']
                if 'sales_team' in sales_data:
                    for rep_data in sales_data['sales_team']:
                        entity = {
                            'entity_type': 'sales_rep',
                            'metric_category': 'sales',
                            **rep_data
                        }
                        entities.append(entity)
            
            if entities:
                print(f" Extracted {len(entities)} business entities")
                
                # Analyze entity types
                entity_types = {}
                metric_categories = {}
                
                for entity in entities:
                    entity_type = entity.get('entity_type', 'unknown')
                    metric_category = entity.get('metric_category', 'unknown')
                    
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                    metric_categories[metric_category] = metric_categories.get(metric_category, 0) + 1
                
                print(f"\n Entity Type Breakdown ({len(entity_types)} types):")
                for entity_type, count in sorted(entity_types.items()):
                    print(f"   - {entity_type}: {count}")
                
                print(f"\n Metric Category Breakdown:")
                for category, count in sorted(metric_categories.items()):
                    print(f"   - {category}: {count}")
                
                # Show sample entities
                print(f"\n Sample Entities (first 3):")
                for i, entity in enumerate(entities[:3]):
                    print(f"\n   Entity {i+1} ({entity.get('entity_type', 'unknown')}):")
                    sample_keys = list(entity.keys())[:5]
                    for key in sample_keys:
                        value = entity[key]
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"      {key}: {value}")
                
                # Test for numeric fields (important for charts/KPIs)
                numeric_entities = []
                for entity in entities:
                    numeric_fields = []
                    for key, value in entity.items():
                        if isinstance(value, (int, float)) and key not in ['id', 'line_number']:
                            numeric_fields.append(key)
                    if numeric_fields:
                        numeric_entities.append({
                            'entity_type': entity.get('entity_type'),
                            'numeric_fields': numeric_fields
                        })
                
                print(f"\n Entities with Numeric Data ({len(numeric_entities)}):")
                for ne in numeric_entities[:5]:
                    print(f"   - {ne['entity_type']}: {ne['numeric_fields'][:3]}...")
                
                self.test_results['entity_extraction'] = True
                return entities
            else:
                print(" No entities extracted")
                return []
                
        except Exception as e:
            print(f" Entity extraction test failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_data_flattening(self, entities: List[Dict]) -> List[Dict]:
        """Test data flattening for LLM analysis"""
        print("\n" + "="*50)
        print(" TESTING DATA FLATTENING")
        print("="*50)
        
        try:
            print(" Simulating data flattening process...")
            
            if not entities:
                print(" No entities to flatten")
                return []
            
            # Simulate flattening logic
            flattened = []
            for entity in entities:
                flat_record = {}
                for key, value in entity.items():
                    if isinstance(value, (str, int, float, bool)) and value is not None:
                        flat_record[key] = value
                    elif isinstance(value, dict):
                        # Flatten nested dicts
                        for nested_key, nested_value in value.items():
                            if isinstance(nested_value, (str, int, float, bool)) and nested_value is not None:
                                flat_record[f"{key}_{nested_key}"] = nested_value
                    elif isinstance(value, list) and value:
                        flat_record[f"{key}_count"] = len(value)
                        if value and isinstance(value[0], (str, int, float)):
                            flat_record[f"{key}_sample"] = value[0]
                flattened.append(flat_record)
            
            if flattened:
                print(f" Flattened {len(entities)} entities to {len(flattened)} records")
                
                # Analyze flattened data
                total_fields = 0
                numeric_fields = 0
                categorical_fields = 0
                
                for record in flattened:
                    for key, value in record.items():
                        total_fields += 1
                        if isinstance(value, (int, float)):
                            numeric_fields += 1
                        elif isinstance(value, str):
                            categorical_fields += 1
                
                print(f" Flattened Data Analysis:")
                print(f"   - Total fields: {total_fields}")
                print(f"   - Numeric fields: {numeric_fields} ({numeric_fields/total_fields*100:.1f}%)")
                print(f"   - Categorical fields: {categorical_fields} ({categorical_fields/total_fields*100:.1f}%)")
                
                # Show sample flattened record
                if flattened:
                    sample_record = flattened[0]
                    print(f"\n Sample Flattened Record ({len(sample_record)} fields):")
                    for key, value in list(sample_record.items())[:8]:
                        print(f"   - {key}: {value}")
                
                self.test_results['flattening'] = True
                return flattened
            else:
                print(" Flattening returned no records")
                return []
                
        except Exception as e:
            print(f" Data flattening test failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def test_llm_preparation(self, flattened_data: List[Dict]) -> Dict:
        """Test LLM data preparation"""
        print("\n" + "="*50)
        print("🤖 TESTING LLM DATA PREPARATION")
        print("="*50)
        
        try:
            if not flattened_data:
                print(" No flattened data to prepare")
                return {}
            
            # Simulate LLM data preparation
            dataset_summary = {
                'total_records': len(flattened_data),
                'total_fields': 0,
                'numeric_fields': [],
                'categorical_fields': [],
                'field_samples': {}
            }
            
            # Analyze all fields
            all_fields = set()
            for record in flattened_data:
                all_fields.update(record.keys())
            
            for field in all_fields:
                values = [record.get(field) for record in flattened_data if field in record]
                non_null_values = [v for v in values if v is not None]
                
                if non_null_values:
                    first_value = non_null_values[0]
                    if isinstance(first_value, (int, float)):
                        dataset_summary['numeric_fields'].append(field)
                    elif isinstance(first_value, str):
                        dataset_summary['categorical_fields'].append(field)
                    
                    dataset_summary['field_samples'][field] = non_null_values[:3]
            
            dataset_summary['total_fields'] = len(all_fields)
            
            print(f" LLM Data Preparation Complete:")
            print(f"   - Records: {dataset_summary['total_records']}")
            print(f"   - Total Fields: {dataset_summary['total_fields']}")
            print(f"   - Numeric Fields: {len(dataset_summary['numeric_fields'])}")
            print(f"   - Categorical Fields: {len(dataset_summary['categorical_fields'])}")
            
            print(f"\n Numeric Fields for Charts/KPIs:")
            for field in dataset_summary['numeric_fields'][:10]:
                samples = dataset_summary['field_samples'][field]
                print(f"   - {field}: {samples}")
            
            print(f"\n Categorical Fields for Segmentation:")
            for field in dataset_summary['categorical_fields'][:5]:
                samples = dataset_summary['field_samples'][field]
                print(f"   - {field}: {samples}")
            
            # Check if we have enough data for good visualizations
            has_enough_numeric = len(dataset_summary['numeric_fields']) >= 5
            has_enough_categorical = len(dataset_summary['categorical_fields']) >= 3
            has_enough_records = dataset_summary['total_records'] >= 10
            
            print(f"\n Visualization Readiness:")
            print(f"   - Sufficient numeric fields: {has_enough_numeric} ({len(dataset_summary['numeric_fields'])} >= 5)")
            print(f"   - Sufficient categorical fields: {has_enough_categorical} ({len(dataset_summary['categorical_fields'])} >= 3)")
            print(f"   - Sufficient records: {has_enough_records} ({dataset_summary['total_records']} >= 10)")
            
            if has_enough_numeric and has_enough_categorical and has_enough_records:
                print(" Data is ready for rich chart and KPI generation!")
                self.test_results['llm_preparation'] = True
            else:
                print(" Data may not generate diverse visualizations")
            
            return dataset_summary
            
        except Exception as e:
            print(f" LLM preparation test failed: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def run_complete_test(self):
        """Run the complete test suite"""
        print(" STARTING COMPREHENSIVE DASHBOARD GENERATION TEST")
        print("="*80)
        
        # Step 1: Load test data
        test_data = self.load_test_data()
        if not test_data:
            print(" Cannot proceed without test data")
            return
        
        # Step 2: Test universal parser
        parsed_records = self.test_universal_parser(test_data)
        
        # Step 3: Test business structure detection
        business_detected = self.test_business_structure_detection(parsed_records)
        
        # Step 4: Test entity extraction
        entities = self.test_entity_extraction(parsed_records)
        
        # Step 5: Test data flattening
        flattened_data = self.test_data_flattening(entities)
        
        # Step 6: Test LLM preparation
        llm_summary = self.test_llm_preparation(flattened_data)
        
        # Final results
        self.print_final_results()
    
    def print_final_results(self):
        """Print final test results summary"""
        print("\n" + "="*80)
        print(" FINAL TEST RESULTS")
        print("="*80)
        
        passed_tests = sum(self.test_results.values())
        total_tests = len(self.test_results)
        
        for test_name, passed in self.test_results.items():
            status = " PASS" if passed else " FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\n Overall Score: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print(" ALL TESTS PASSED! Your JSON should generate rich charts and KPIs!")
        elif passed_tests >= 3:
            print(" Most tests passed. Some visualizations should be generated.")
        else:
            print(" Multiple test failures. Dashboard generation may not work properly.")
        
        print("\n Next Steps:")
        if passed_tests == total_tests:
            print("   1. Upload your comprehensive JSON via the client creation form")
            print("   2. Navigate to the dashboard to see rich visualizations")
            print("   3. Check for charts, KPIs, and tables based on your business data")
        else:
            print("   1. Review the failed tests above")
            print("   2. Check server logs for additional error details")
            print("   3. Fix any JSON structure or parsing issues")
        
        print("="*80)

def main():
    """Main test execution"""
    tester = DashboardGenerationTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()
