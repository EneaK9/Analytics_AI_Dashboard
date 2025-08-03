#!/usr/bin/env python3
"""
Quick script to check cache entries using direct database access
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_admin_client
import json
from datetime import datetime

def check_cache_entries():
    """Check what's actually in the cache table"""
    try:
        db_client = get_admin_client()
        
        # Get all cache entries
        response = db_client.table("llm_response_cache").select("*").order("created_at", desc=True).execute()
        
        print("🔍 Cache Entries in Database:")
        print("=" * 50)
        
        if response.data:
            print(f"Found {len(response.data)} cache entries:")
            
            for i, entry in enumerate(response.data[:10]):  # Show first 10
                created_at = entry.get('created_at', 'Unknown')
                client_id = entry.get('client_id', 'Unknown')
                data_type = entry.get('data_type', 'Unknown')
                data_hash = entry.get('data_hash', 'Unknown')
                total_records = entry.get('total_records', 0)
                has_response = bool(entry.get('llm_response'))
                
                print(f"\n{i+1}. Entry {entry.get('id', 'N/A')}")
                print(f"   Created: {created_at}")
                print(f"   Client: {client_id}")
                print(f"   Type: {data_type}")
                print(f"   Hash: {data_hash[:12]}...")
                print(f"   Records: {total_records}")
                print(f"   Has Data: {has_response}")
                
                # Parse date
                try:
                    if created_at != 'Unknown':
                        if created_at.endswith('Z'):
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            dt = datetime.fromisoformat(created_at)
                        date_only = dt.date().isoformat()
                        print(f"   Date: {date_only}")
                except:
                    print(f"   Date: Could not parse")
            
            if len(response.data) > 10:
                print(f"\n... and {len(response.data) - 10} more entries")
                
        else:
            print("❌ No cache entries found!")
            print("\n💡 This explains why your date filtering isn't working.")
            print("   To fix this:")
            print("   1. Call GET /api/dashboard/metrics?fast_mode=true (without dates)")
            print("   2. This will generate a cache entry for today")
            print("   3. Then test with today's date")
        
        # Check for specific client
        client_id = "0c965b09-f8bd-42f9-ae30-1015c4ec1ea2"
        client_response = db_client.table("llm_response_cache").select("*").eq("client_id", client_id).order("created_at", desc=True).execute()
        
        print(f"\n🎯 Entries for client {client_id}:")
        if client_response.data:
            print(f"   Found {len(client_response.data)} entries")
            for entry in client_response.data:
                created_at = entry.get('created_at', 'Unknown')
                data_type = entry.get('data_type', 'Unknown')
                print(f"   - {created_at} ({data_type})")
        else:
            print("   ❌ No entries found for this client!")
            
    except Exception as e:
        print(f"❌ Error checking cache: {e}")

if __name__ == "__main__":
    check_cache_entries()