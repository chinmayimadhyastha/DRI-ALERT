from flask import Flask, Blueprint, request, jsonify, Response
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from api.routes import main_bp
from io import StringIO
import csv
import os
import logging
from dotenv import load_dotenv

# ---------------------- Initialize Extensions ----------------------
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()

# ---------------------- Models ----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)

class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# ---------------------- Create Flask Application ----------------------
def create_app():
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Configuration
    app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY', 'schimadhya0110')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:chinmayi@localhost:3306/drowsiness_db'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Import blueprints - do this here to avoid circular imports
    from auth_routes import auth_bp
    from admin_routes import admin_bp
    
    # Create a main routes blueprint
    main_bp = Blueprint('main', __name__)
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(main_bp, url_prefix='')
    
    # ---------------------- Main Routes ----------------------
    @main_bp.route("/status", methods=["GET"])
    def status():
        return jsonify({"status": "Server is running"})
    
    @main_bp.route("/register", methods=["POST"])
    def register():
        try:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
            role = data.get("role")
            
            if not all([email, password, role]):
                return jsonify({"error": "All fields are required"}), 400
                
            if User.query.filter_by(email=email).first():
                return jsonify({"error": "User already exists"}), 400
                
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            
            return jsonify({"message": "User registered successfully"}), 201
        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    @main_bp.route("/login", methods=["POST"])
    def login():
        try:
            data = request.get_json()
            email = data.get("email", "").strip()
            password = data.get("password", "").strip()
            
            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400
                
            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password, password):
                return jsonify({"error": "Invalid credentials"}), 401
                
            access_token = create_access_token(identity=email)
            
            return jsonify({
                "message": "Login successful",
                "token": access_token,
                "role": user.role
            }), 200
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            return jsonify({"error": "Login failed"}), 500
    
    @main_bp.route('/detect', methods=['POST'])
    @jwt_required()
    def detect():
        try:
            data = request.get_json()
            status = data.get("status", "Unknown").strip()
            user_email = get_jwt_identity()
            
            if not status:
                return jsonify({"error": "Status is required"}), 400
                
            new_detection = Detection(user=user_email, status=status)
            db.session.add(new_detection)
            db.session.commit()
            
            return jsonify({
                "message": f"Detection saved for {user_email}",
                "status": status
            }), 201
        except Exception as e:
            app.logger.error(f"Detection error: {str(e)}")
            return jsonify({"error": "Failed to save detection"}), 500
    
    @main_bp.route("/logs", methods=["GET"])
    @jwt_required()
    def get_logs():
        try:
            status_filter = request.args.get('status')
            user_filter = request.args.get('user')
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            query = Detection.query.order_by(Detection.timestamp.desc())
            
            if status_filter:
                query = query.filter(Detection.status == status_filter)
                
            current_user_email = get_jwt_identity()
            current_user = User.query.filter_by(email=current_user_email).first()
            
            if current_user.role != 'admin':
                query = query.filter(Detection.user == current_user_email)
            elif user_filter:
                query = query.filter(Detection.user == user_filter)
                
            paginated_logs = query.paginate(page=page, per_page=per_page, error_out=False)
            
            logs_data = [{
                "id": log.id,
                "user": log.user,
                "status": log.status,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for log in paginated_logs.items]
            
            return jsonify({
                "logs": logs_data,
                "total_logs": paginated_logs.total,
                "total_pages": paginated_logs.pages,
                "current_page": page
            }), 200
        except SQLAlchemyError as e:
            app.logger.error(f"Database error fetching logs: {str(e)}")
            return jsonify({"error": "Database operation failed"}), 500
        except Exception as e:
            app.logger.error(f"Unexpected error fetching logs: {str(e)}")
            return jsonify({"error": "Failed to fetch logs"}), 500
    
    @main_bp.route("/analytics", methods=["GET"])
    @jwt_required()
    def analytics_logs():
        try:
            user_email = get_jwt_identity()
            logs = Detection.query.filter_by(user=user_email).all()
            alert_count = sum(1 for log in logs if log.status == "Alert")
            normal_count = len(logs) - alert_count
            return jsonify({
                "total_logs": len(logs),
                "alert_logs": alert_count,
                "normal_logs": normal_count
                }), 200
        except Exception as e:
            app.logger.error(f"Analytics logs error: {str(e)}")
            return jsonify({"error": "Failed to fetch analytics"}), 500
    
    @main_bp.route("/timeline", methods=["GET"])
    @jwt_required()
    def timeline_logs():
        try:
            user_email = get_jwt_identity()
            logs = Detection.query.filter_by(user=user_email).order_by(Detection.timestamp.desc()).all()
            return jsonify({
                "timeline": [{
                    "id": log.id,
                    "status": log.status,
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    } for log in logs]
                    }), 200
        except Exception as e:
            app.logger.error(f"Timeline logs error: {str(e)}")
            return jsonify({"error": "Failed to fetch timeline"}), 500
    
    @main_bp.route("/logs/download", methods=["GET"])
    @jwt_required()
    def download_logs():
        try:
            user_email = get_jwt_identity()
            logs = Detection.query.filter_by(user=user_email).order_by(Detection.timestamp.desc()).all()
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "user", "status", "timestamp"])
            
            for log in logs:
                writer.writerow([log.id, log.user, log.status, log.timestamp])
                
            output.seek(0)
            
            return Response(
                output,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=detection_logs.csv"}
            )
        except Exception as e:
            app.logger.error(f"CSV download error: {str(e)}")
            return jsonify({"error": "Failed to generate CSV"}), 500
    
    @main_bp.route("/profile", methods=["GET"])
    @jwt_required()
    def get_profile():
        try:
            user_email = get_jwt_identity()
            user = User.query.filter_by(email=user_email).first()
            
            return jsonify({
                "email": user_email,
                "role": user.role,
                "message": "Profile fetched successfully"
            }), 200
        except Exception as e:
            app.logger.error(f"Profile error: {str(e)}")
            return jsonify({"error": "Failed to fetch profile"}), 500
    
    @main_bp.route("/filter", methods=["GET"])
    @jwt_required()
    def filtered_logs():
        try:
            status = request.args.get("status")
            user_email = get_jwt_identity()
            
            query = Detection.query.filter_by(user=user_email)
            if status:
                query = query.filter_by(status=status.capitalize())
                
            logs = query.order_by(Detection.timestamp.desc()).all()
            
            return jsonify({
                "logs": [{
                    "id": log.id,
                    "status": log.status,
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                } for log in logs]
            }), 200
        except Exception as e:
            app.logger.error(f"Filter logs error: {str(e)}")
            return jsonify({"error": "Failed to filter logs"}), 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
    return app

# Run the application
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
else:
    # For WSGI servers
    app = create_app()