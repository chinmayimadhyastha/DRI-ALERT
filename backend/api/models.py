from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import logging
from mongodb_config import get_mongo_db

logger = logging.getLogger(__name__)

class User:
    def __init__(self, email, password, role='driver'):
        self.email = email.lower().strip()
        self.password_hash = generate_password_hash(password)
        self.role = role
        self.is_active = True
        self.last_login = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        """FIXED: Proper error handling and logging"""
        try:
            db = get_mongo_db()
            if db is None:
                logger.error("❌ Database connection failed in save()")
                return False

            user_data = {
                'email': self.email,
                'password_hash': self.password_hash,
                'role': self.role,
                'is_active': self.is_active,
                'last_login': self.last_login,
                'created_at': self.created_at,
                'updated_at': datetime.utcnow()
            }

            if hasattr(self, '_id') and self._id:
                result = db.users.update_one({'_id': self._id}, {'$set': user_data})
                logger.info(f"✅ User updated: {self.email}")
                return True
            else:
                result = db.users.insert_one(user_data)
                self._id = result.inserted_id
                logger.info(f"✅ User created: {self.email} with ID: {self._id}")
                verification = db.users.find_one({'_id': self._id})
                if verification:
                    logger.info(f"✅ Save verified: User {self.email} exists in database")
                    return True
                else:
                    logger.error(f"❌ Save failed: User {self.email} not found after insert")
                    return False
        except Exception as e:
            logger.error(f"❌ Error saving user {self.email}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def find_by_email(email):
        try:
            db = get_mongo_db()
            if db is None:
                logger.error("❌ Database connection failed in find_by_email()")
                return None

            user_data = db.users.find_one({'email': email.lower().strip()})
            logger.info(f"🔍 Search for {email}: {'Found' if user_data else 'Not found'}")

            if user_data:
                user = User.__new__(User)
                user._id = user_data['_id']
                user.email = user_data['email']
                user.password_hash = user_data['password_hash']
                user.role = user_data['role']
                user.is_active = user_data['is_active']
                user.last_login = user_data.get('last_login')
                user.created_at = user_data['created_at']
                user.updated_at = user_data.get('updated_at')
                return user
            return None
        except Exception as e:
            logger.error(f"❌ Error finding user {email}: {str(e)}")
            return None

    def to_dict(self):
        return {
            'email': self.email,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            '_id': str(self._id) if hasattr(self, '_id') else None,
            'role': self.role,
            'is_active': self.is_active
        }

    @staticmethod
    def get_all_users():
        try:
            db = get_mongo_db()
            if db is None:
                return []

            users = []
            for user_data in db.users.find():
                user = User.__new__(User)
                user._id = user_data['_id']
                user.email = user_data['email']
                user.password_hash = user_data['password_hash']
                user.role = user_data['role']
                user.is_active = user_data['is_active']
                user.last_login = user_data.get('last_login')
                user.created_at = user_data['created_at']
                user.updated_at = user_data.get('updated_at')
                users.append(user)
            return users
        except Exception as e:
            logger.error(f"❌ Error getting users: {str(e)}")
            return []
