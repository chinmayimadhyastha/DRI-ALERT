from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions here to avoid circular imports
db = SQLAlchemy()
jwt = JWTManager()