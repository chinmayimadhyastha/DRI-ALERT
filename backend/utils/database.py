import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy object
db = SQLAlchemy()

# Load environment variables
load_dotenv()

# Function to get the database URI from environment variables
def get_database_uri():
    """
    Get the database URI from environment variables (or default if not set).
    """
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'drowsiness_db')
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"

# Initialize the app's database configuration
def init_app(app):
    """
    Initialize the Flask app with the database configuration.
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    logger.info("✅ Database configured and initialized successfully.")