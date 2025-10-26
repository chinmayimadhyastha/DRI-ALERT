from flask_jwt_extended import JWTManager
import logging
from flask_socketio import SocketIO
from flask_cors import CORS

cors = CORS()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions here to avoid circular imports
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')