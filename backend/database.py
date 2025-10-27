"""
MongoDB database connection and management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database client singleton"""
    client: AsyncIOMotorClient = None

database = Database()


async def connect_to_mongo():
    """Establish MongoDB connection"""
    database.client = AsyncIOMotorClient(settings.mongodb_url)
    logger.info("Connected to MongoDB successfully")
    return database.client


async def close_mongo_connection():
    """Close MongoDB connection"""
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")


def get_database():
    """Get database instance"""
    return database.client[settings.database_name]


async def ping():
    """Ping database to check connection"""
    try:
        await database.client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"Database ping failed: {e}")
        return False


