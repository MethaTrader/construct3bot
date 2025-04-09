from config import load_config

# Load config to get admin IDs
config = load_config()
ADMIN_IDS = config.admin_ids

async def is_admin(user_id: int) -> bool:
    """
    Check if a user is an admin
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    return user_id in ADMIN_IDS 