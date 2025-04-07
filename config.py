import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    bot_token: str
    database_url: str
    admin_ids: list[int]

def load_config() -> Config:
    # Load .env file
    load_dotenv()
    
    # Get bot token from .env
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError('BOT_TOKEN environment variable is not set')
    
    # Get database URL from .env
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError('DATABASE_URL environment variable is not set')
    
    # Parse admin IDs
    admin_ids_str = os.getenv('ADMIN_IDS', '')
    admin_ids = [
        int(admin_id.strip()) 
        for admin_id in admin_ids_str.split(',') 
        if admin_id.strip().isdigit()
    ]
    
    return Config(
        bot_token=bot_token,
        database_url=database_url,
        admin_ids=admin_ids
    )