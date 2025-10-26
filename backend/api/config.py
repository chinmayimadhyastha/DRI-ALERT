# api/config.py
import os
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'DriAlert')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'DriAlert')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    RATE_LIMIT = "200 per day, 50 per hour"
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI')

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True