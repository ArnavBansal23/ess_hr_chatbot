import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Flask secret key (used for sessions, cookies etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "default-flask-secret")

    # JWT Config
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    #DB credentials
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
    MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")






