import os
import logging
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from auth_routes import auth_bp
from detection_routes import detection_bp
from admin_routes import admin_bp

# Load environment
load_dotenv()

# Import models
from models import User
from mongodb_config import get_mongo_db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'DriAlert')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'DriAlert')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# ✅ FIXED: Simple CORS - let flask-cors handle everything
CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,  # ✅ ADD THIS
         allow_headers=["Content-Type", "Authorization"],  # ✅ ADD THIS
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])  # ✅ ADD THIS

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(detection_bp, url_prefix='/api/detection')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Initialize JWT
jwt = JWTManager(app)

# ✅ REMOVED @app.after_request - flask-cors handles it automatically

@app.route('/debug/db', methods=['GET'])
def debug_db():
    try:
        users = User.get_all_users()
        return jsonify({
            'total_users': len(users),
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'DriAlert API Server',
        'version': '1.0',
        'endpoints': {
            'auth': '/api/auth',
            'detection': '/api/detection',
            'admin': '/api/admin',
            'health': '/api/health'
        }
    }), 200

if __name__ == "__main__":
    logger.info("🚀 Starting Flask server...")
    logger.info("📍 Server running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
