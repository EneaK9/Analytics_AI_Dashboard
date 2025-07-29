#!/usr/bin/env python3
"""
Test script to verify gpt-4o model is working correctly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dashboard_orchestrator import DashboardOrchestrator

async def test_gpt4o_model():
    """Test that gpt-4o model is working correctly"""
    
    print("🧪 Testing gpt-4o model configuration...")
    
    try:
        # Initialize the orchestrator
        orchestrator = DashboardOrchestrator()
        print("✅ DashboardOrchestrator initialized successfully")
        
        # Test data
        test_data = {
            "data_type": "ecommerce",
            "schema_type": "sales",
            "sample_data": [
                {"product": "Laptop", "price": 999.99, "quantity": 5, "date": "2024-01-15"},
                {"product": "Mouse", "price": 29.99, "quantity": 10, "date": "2024-01-16"},
                {"product": "Keyboard", "price": 79.99, "quantity": 3, "date": "2024-01-17"}
            ],
            "total_records": 3
        }
        
        # Create a test prompt
        prompt = orchestrator._create_llm_analysis_prompt(
            data_type=test_data["data_type"],
            schema_type=test_data["schema_type"],
            sample_data=test_data["sample_data"],
            total_records=test_data["total_records"]
        )
        
        print("✅ Test prompt created successfully")
        print(f"📝 Prompt length: {len(prompt)} characters")
        
        # Test LLM call (this will actually call the API)
        print("🤖 Testing LLM call with gpt-4o...")
        response = await orchestrator._get_llm_analysis(prompt)
        
        print("✅ LLM response received successfully")
        print(f"📝 Response length: {len(response)} characters")
        print(f"📝 Response preview: {response[:200]}...")
        
        # Test parsing the response
        parsed_insights = orchestrator._parse_llm_insights(response, test_data["sample_data"])
        print("✅ Response parsed successfully")
        print(f"📊 Parsed insights: {len(parsed_insights.get('kpis', []))} KPIs, {len(parsed_insights.get('charts', []))} charts")
        
        print("\n🎉 All tests passed! gpt-4o model is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key before running this test")
        sys.exit(1)
    
    # Run the test
    success = asyncio.run(test_gpt4o_model())
    
    if success:
        print("\n✅ gpt-4o model test completed successfully!")
    else:
        print("\n❌ gpt-4o model test failed!")
        sys.exit(1) 