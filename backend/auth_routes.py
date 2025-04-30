from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import logging

from api import db
from api.models import User

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "driver")  # Default to driver role if not specified
        
        if not all([email, password]):
            return jsonify({"error": "Email and password are required"}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400
            
        # Create new user with properly hashed password
        new_user = User(email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in a user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
            
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
            
        access_token = create_access_token(identity=email)
        
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "role": user.role
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get the authenticated user's profile"""
    try:
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "email": user_email,
            "role": user.role,
            "message": "Profile fetched successfully"
        }), 200
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"error": "Failed to fetch profile"}), 500