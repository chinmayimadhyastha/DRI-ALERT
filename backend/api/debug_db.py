import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB connection and operations"""
    print("🔍 Testing MongoDB Connection...")
    
    # Check environment variables
    mongodb_uri = os.getenv('MONGODB_URI')
    print(f"MONGODB_URI found: {'✅' if mongodb_uri else '❌'}")
    
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in environment variables")
        print("Expected format: mongodb+srv://username:password@cluster.mongodb.net/database")
        return False
    
    # Hide password for security
    safe_uri = mongodb_uri.replace(mongodb_uri.split('://')[1].split('@')[0], "***:***")
    print(f"Connection String: {safe_uri}")
    
    try:
        # Test connection
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test ping
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get database
        db = client['drowsiness_detection']
        print(f"✅ Database 'drowsiness_detection' connected")
        
        # Test collections
        collections = db.list_collection_names()
        print(f"📁 Collections: {collections}")
        
        # Test write operation
        test_doc = {"test": "connection", "timestamp": "2025-10-10"}
        result = db.test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted: {result.inserted_id}")
        
        # Clean up test document
        db.test_collection.delete_one({"_id": result.inserted_id})
        print("🧹 Test document cleaned up")
        
        # Check users collection
        user_count = db.users.count_documents({})
        print(f"👥 Current users in database: {user_count}")
        
        if user_count > 0:
            users = list(db.users.find({}, {"email": 1, "role": 1}))
            for user in users:
                print(f"   - {user.get('email')} ({user.get('role')})")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

def test_user_creation():
    """Test user creation directly"""
    print("\n🧪 Testing User Creation...")
    
    try:
        # Import your models
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from models import User
        
        # Try creating a test user
        test_user = User("debug@test.com", "password123", "driver")
        
        if test_user.save():
            print("✅ User creation successful!")
            
            # Try finding the user
            found_user = User.find_by_email("debug@test.com")
            if found_user:
                print("✅ User retrieval successful!")
                print(f"   Email: {found_user.email}")
                print(f"   Role: {found_user.role}")
                
                # Test password check
                if found_user.check_password("password123"):
                    print("✅ Password verification successful!")
                else:
                    print("❌ Password verification failed!")
            else:
                print("❌ User retrieval failed!")
        else:
            print("❌ User creation failed!")
            
    except Exception as e:
        print(f"❌ User creation test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Database Diagnostics Started")
    print("=" * 50)
    
    # Test 1: MongoDB Connection
    if test_mongodb_connection():
        # Test 2: User Creation
        test_user_creation()
    
    print("=" * 50)
    print("🏁 Diagnostics Complete")
