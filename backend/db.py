from langchain_community.utilities import SQLDatabase
from config import Config
import logging


logger = logging.getLogger(__name__)
db = None

def init_db():

    try:
        mysql_user = Config.MYSQL_USER
        mysql_password = Config.MYSQL_PASSWORD
        mysql_host = Config.MYSQL_HOST
        mysql_port = Config.MYSQL_PORT
        mysql_db_name = Config.MYSQL_DB_NAME



        if not all([mysql_user, mysql_password, mysql_host, mysql_port, mysql_db_name]):
            logger.error("One or more MySQL environment variables are missing.")
            return None

        mysql_uri = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db_name}"

        db = SQLDatabase.from_uri(mysql_uri)
        logger.info("Database connected successfully.")
        return db

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return None



