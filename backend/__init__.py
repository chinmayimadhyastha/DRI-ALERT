import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_class=None):
    """Application factory pattern"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Configure application
    if config_class:
        app.config.from_object(config_class)
    else:
        # Default configuration
        app.config.update(
            JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "fallback_secret_key"),
            SQLALCHEMY_DATABASE_URI=os.getenv(
                "DATABASE_URL",
                "mysql+pymysql://root:chinmayi@localhost/drowsiness_db?charset=utf8mb4"
            ),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SQLALCHEMY_ENGINE_OPTIONS={
                'pool_recycle': 299,
                'pool_pre_ping': True
            },
            JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour expiration
        )
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        }
    )
    
    # Import models (must be done here to avoid circular imports)
    from api.models import User, Detection
    
    # Register blueprints
    from api.routes import api
    from api.auth_routes import auth_bp
    from api.admin_routes import admin_bp
    
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Create database tables if needed
    with app.app_context():
        if os.getenv("FLASK_ENV") == "development":
            db.create_all()
            print("✅ Database tables created")
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app