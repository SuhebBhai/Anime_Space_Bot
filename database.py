# database.py
import motor.motor_asyncio
from datetime import datetime
from config import Config


class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.DATABASE_NAME]
        
        # Collections
        self.users = self.db["users"]
        self.episodes = self.db["episodes"]
        self.analytics = self.db["analytics"]
        self.batch = self.db["batch_links"]
    
    # ─── User Methods ───
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add a new user or update existing user info."""
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "last_active": datetime.utcnow()
                },
                "$setdefault": {
                    "joined_date": datetime.utcnow(),
                    "is_banned": False,
                    "files_received": 0
                }
            },
            upsert=True
        )
    
    async def get_user(self, user_id: int):
        """Get user document."""
        return await self.users.find_one({"user_id": user_id})
    
    async def get_all_users_count(self):
        """Get total number of users."""
        return await self.users.count_documents({})
    
    async def get_all_user_ids(self):
        """Get all user IDs for broadcasting."""
        cursor = self.users.find({}, {"user_id": 1})
        user_ids = []
        async for doc in cursor:
            user_ids.append(doc["user_id"])
        return user_ids
    
    async def ban_user(self, user_id: int):
        """Ban a user."""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": True}}
        )
    
    async def unban_user(self, user_id: int):
        """Unban a user."""
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": False}}
        )
    
    async def is_banned(self, user_id: int):
        """Check if user is banned."""
        user = await self.users.find_one({"user_id": user_id})
        if user:
            return user.get("is_banned", False)
        return False
    
    async def increment_files_received(self, user_id: int):
        """Increment the files received counter for a user."""
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"files_received": 1},
                "$set": {"last_active": datetime.utcnow()}
            }
        )
    
    # ─── Episode Mapping Methods ───
    
    async def add_episode(self, episode_code: str, message_id: int, 
                          anime_name: str = None, episode_number: int = None,
                          file_name: str = None, file_size: str = None):
        """Map an episode code to a storage channel message ID."""
        await self.episodes.update_one(
            {"episode_code": episode_code},
            {
                "$set": {
                    "episode_code": episode_code,
                    "message_id": message_id,
                    "anime_name": anime_name,
                    "episode_number": episode_number,
                    "file_name": file_name,
                    "file_size": file_size,
                    "added_date": datetime.utcnow(),
                    "access_count": 0
                }
            },
            upsert=True
        )
    
    async def get_episode(self, episode_code: str):
        """Get episode document by code."""
        return await self.episodes.find_one({"episode_code": episode_code})
    
    async def get_episode_by_message_id(self, message_id: int):
        """Get episode by storage message ID."""
        return await self.episodes.find_one({"message_id": message_id})
    
    async def delete_episode(self, episode_code: str):
        """Delete an episode mapping."""
        result = await self.episodes.delete_one({"episode_code": episode_code})
        return result.deleted_count > 0
    
    async def get_all_episodes(self, anime_name: str = None):
        """Get all episodes, optionally filtered by anime name."""
        query = {}
        if anime_name:
            query["anime_name"] = {"$regex": anime_name, "$options": "i"}
        cursor = self.episodes.find(query).sort("episode_number", 1)
        episodes = []
        async for doc in cursor:
            episodes.append(doc)
        return episodes
    
    async def increment_access_count(self, episode_code: str):
        """Increment how many times an episode has been accessed."""
        await self.episodes.update_one(
            {"episode_code": episode_code},
            {"$inc": {"access_count": 1}}
        )
    
    async def get_total_episodes_count(self):
        """Get total number of stored episodes."""
        return await self.episodes.count_documents({})
    
    # ─── Batch Link Methods ───
    
    async def add_batch(self, batch_id: str, message_ids: list, anime_name: str = None):
        """Store a batch of message IDs under a single batch ID."""
        await self.batch.update_one(
            {"batch_id": batch_id},
            {
                "$set": {
                    "batch_id": batch_id,
                    "message_ids": message_ids,
                    "anime_name": anime_name,
                    "created_date": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    async def get_batch(self, batch_id: str):
        """Get batch document."""
        return await self.batch.find_one({"batch_id": batch_id})
    
    # ─── Analytics Methods ───
    
    async def log_access(self, user_id: int, episode_code: str):
        """Log file access for analytics."""
        await self.analytics.insert_one({
            "user_id": user_id,
            "episode_code": episode_code,
            "accessed_at": datetime.utcnow()
        })
    
    async def get_daily_stats(self, date=None):
        """Get access stats for a specific day."""
        if date is None:
            date = datetime.utcnow().date()
        
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        count = await self.analytics.count_documents({
            "accessed_at": {"$gte": start, "$lte": end}
        })
        return count


# Global database instance
db = Database()