#!/usr/bin/env python3
"""
Test script to verify LLM caching system
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from llm_cache_manager import llm_cache_manager
from dashboard_orchestrator import DashboardOrchestrator

async def test_llm_caching():
    """Test the LLM caching system"""
    
    print("🧪 Testing LLM caching system...")
    
    try:
        # Test data
        test_client_id = "test-client-123"
        test_data = {
            "client_id": test_client_id,
            "data_type": "ecommerce",
            "schema_type": "sales",
            "data": [
                {"product": "Laptop", "price": 999.99, "quantity": 5, "date": "2024-01-15"},
                {"product": "Mouse", "price": 29.99, "quantity": 10, "date": "2024-01-16"},
                {"product": "Keyboard", "price": 79.99, "quantity": 3, "date": "2024-01-17"}
            ],
            "total_records": 3
        }
        
        # Test 1: Check cache initially (should be empty)
        print("\n📋 Test 1: Check initial cache state")
        cached_response = await llm_cache_manager.get_cached_llm_response(test_client_id, test_data)
        if cached_response is None:
            print("✅ No cached response found (expected)")
        else:
            print("❌ Unexpected cached response found")
            return False
        
        # Test 2: Store a test response
        print("\n📋 Test 2: Store test response in cache")
        test_response = {
            "kpis": [
                {"id": "kpi1", "display_name": "Total Revenue", "value": "5000", "trend": {"percentage": 10.0, "direction": "up"}}
            ],
            "charts": [
                {"id": "chart1", "display_name": "Sales by Product", "chart_type": "bar", "data": [{"name": "Laptop", "value": 4999.95}]}
            ],
            "tables": [
                {"id": "table1", "display_name": "Product Sales", "data": [["Laptop", "4999.95", "5"]], "columns": ["Product", "Revenue", "Quantity"]}
            ]
        }
        
        cache_success = await llm_cache_manager.store_cached_llm_response(test_client_id, test_data, test_response)
        if cache_success:
            print("✅ Test response cached successfully")
        else:
            print("❌ Failed to cache test response")
            return False
        
        # Test 3: Retrieve cached response
        print("\n📋 Test 3: Retrieve cached response")
        retrieved_response = await llm_cache_manager.get_cached_llm_response(test_client_id, test_data)
        if retrieved_response and retrieved_response.get("kpis"):
            print("✅ Cached response retrieved successfully")
            print(f"   KPIs: {len(retrieved_response.get('kpis', []))}")
            print(f"   Charts: {len(retrieved_response.get('charts', []))}")
            print(f"   Tables: {len(retrieved_response.get('tables', []))}")
        else:
            print("❌ Failed to retrieve cached response")
            return False
        
        # Test 4: Test data change detection
        print("\n📋 Test 4: Test data change detection")
        modified_data = test_data.copy()
        modified_data["data"][0]["price"] = 1099.99  # Change price
        
        changed_response = await llm_cache_manager.get_cached_llm_response(test_client_id, modified_data)
        if changed_response is None:
            print("✅ Cache correctly detected data change (no cached response returned)")
        else:
            print("❌ Cache failed to detect data change")
            return False
        
        # Test 5: Test cache invalidation
        print("\n📋 Test 5: Test cache invalidation")
        invalidate_success = await llm_cache_manager.invalidate_cache(test_client_id)
        if invalidate_success:
            print("✅ Cache invalidated successfully")
        else:
            print("❌ Failed to invalidate cache")
            return False
        
        # Verify cache is empty after invalidation
        empty_response = await llm_cache_manager.get_cached_llm_response(test_client_id, test_data)
        if empty_response is None:
            print("✅ Cache is empty after invalidation (expected)")
        else:
            print("❌ Cache still contains data after invalidation")
            return False
        
        # Test 6: Test cache stats
        print("\n📋 Test 6: Test cache statistics")
        stats = await llm_cache_manager.get_cache_stats()
        if "total_entries" in stats:
            print(f"✅ Cache stats retrieved: {stats['total_entries']} entries")
        else:
            print("❌ Failed to get cache stats")
            return False
        
        # Test 7: Test with dashboard orchestrator
        print("\n📋 Test 7: Test with dashboard orchestrator")
        orchestrator = DashboardOrchestrator()
        
        # Store a response first
        await llm_cache_manager.store_cached_llm_response(test_client_id, test_data, test_response)
        
        # Test the orchestrator's cache integration
        insights = await orchestrator._extract_business_insights_from_data(test_data)
        if insights and "error" not in insights:
            print("✅ Dashboard orchestrator successfully used cached response")
        else:
            print("❌ Dashboard orchestrator failed to use cached response")
            return False
        
        print("\n🎉 All LLM caching tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_cleanup():
    """Test cache cleanup functionality"""
    
    print("\n🧹 Testing cache cleanup...")
    
    try:
        # Test cleanup with no expired entries
        cleaned_count = await llm_cache_manager.cleanup_expired_cache(max_age_days=1)
        print(f"✅ Cache cleanup completed: {cleaned_count} entries cleaned")
        return True
        
    except Exception as e:
        print(f"❌ Cache cleanup test failed: {e}")
        return False

if __name__ == "__main__":
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key before running this test")
        sys.exit(1)
    
    # Run the tests
    success = asyncio.run(test_llm_caching())
    cleanup_success = asyncio.run(test_cache_cleanup())
    
    if success and cleanup_success:
        print("\n✅ All LLM caching tests completed successfully!")
    else:
        print("\n❌ Some LLM caching tests failed!")
        sys.exit(1) 