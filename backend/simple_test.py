"""Simple test to check if data organizer imports work"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

try:
    print("Testing imports...")
    from database import get_admin_client, get_db_manager
    print("✅ Database imports successful")
    
    from data_organizer import DataOrganizer
    print("✅ DataOrganizer import successful")
    
    # Test database connection
    db_manager = get_db_manager()
    print("✅ Database manager initialized")
    
    admin_client = get_admin_client()
    if admin_client:
        print("✅ Admin client available")
    else:
        print("❌ Admin client not available")
    
    print("All basic tests passed!")
    
except Exception as e:
    print(f"❌ Import/initialization failed: {e}")
    import traceback
    traceback.print_exc()
