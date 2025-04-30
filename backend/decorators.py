from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = User.query.filter_by(email=get_jwt_identity()).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        if current_user.role != 'admin':
            return jsonify({"error": "Admin privileges required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def driver_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = User.query.filter_by(email=get_jwt_identity()).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        if current_user.role != 'driver':
            return jsonify({"error": "Driver privileges required"}), 403
        return fn(*args, **kwargs)
    return wrapper