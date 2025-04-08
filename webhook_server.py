import logging
import os
import json
import jwt
import asyncio
import aiosqlite
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Configuration
HOST = os.getenv('WEBHOOK_HOST', '0.0.0.0')
PORT = int(os.getenv('WEBHOOK_PORT', 8000))
DATABASE_URL = os.getenv('DATABASE_URL', 'data/database.sqlite3')
SECRET_KEY = os.getenv('CRYPTOCLOUD_SECRET_KEY', '')  # Get from CryptoCloud project settings

async def verify_token(token, invoice_id):
    """Verify the JWT token from CryptoCloud"""
    try:
        if not SECRET_KEY:
            logger.warning("SECRET_KEY not set, skipping token verification")
            return True
            
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # The token should contain the invoice UUID
        if 'id' in decoded:
            return True
        return False
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return False

async def update_user_balance(user_id, amount):
    """Update user balance in the database"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            # First, get current balance
            query = "SELECT balance FROM users WHERE telegram_id = ?"
            cursor = await db.execute(query, (user_id,))
            result = await cursor.fetchone()
            
            if result:
                current_balance = result[0]
                new_balance = current_balance + amount
                
                # Update balance
                update_query = "UPDATE users SET balance = ?, last_active = ? WHERE telegram_id = ?"
                await db.execute(update_query, (new_balance, datetime.utcnow(), user_id))
                await db.commit()
                
                logger.info(f"Updated balance for user {user_id}: {current_balance} -> {new_balance}")
                return True
            else:
                logger.error(f"User {user_id} not found in database")
                return False
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

async def handle_webhook(request):
    """Handle payment webhook from CryptoCloud"""
    try:
        if request.content_type == 'application/x-www-form-urlencoded':
            data = await request.post()
        else:
            data = await request.json()
        
        logger.info(f"Received webhook: {data}")
        
        # Extract payment information
        status = data.get('status')
        invoice_id = data.get('invoice_id')
        order_id = data.get('order_id', '')
        token = data.get('token', '')
        
        # Verify payment status and token
        if status != 'success':
            logger.warning(f"Payment not successful: {status}")
            return web.json_response({'status': 'error', 'message': 'Invalid payment status'})
        
        if not await verify_token(token, invoice_id):
            logger.warning("Token verification failed")
            return web.json_response({'status': 'error', 'message': 'Invalid token'})
        
        # Extract user_id and amount from order_id (format: user_USER_ID_AMOUNT)
        if order_id.startswith('user_'):
            parts = order_id.split('_')
            if len(parts) >= 3:
                user_id = int(parts[1])
                coins_amount = int(parts[2])
                
                # Update user balance
                if await update_user_balance(user_id, coins_amount):
                    logger.info(f"Successfully credited {coins_amount} coins to user {user_id}")
                    return web.json_response({'status': 'success', 'message': 'Payment processed'})
                else:
                    logger.error(f"Failed to update balance for user {user_id}")
                    return web.json_response({'status': 'error', 'message': 'Database update failed'})
        
        logger.warning(f"Invalid order_id format: {order_id}")
        return web.json_response({'status': 'error', 'message': 'Invalid order_id format'})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return web.json_response({'status': 'error', 'message': 'Internal server error'})

async def main():
    app = web.Application()
    app.router.add_post('/payment/webhook', handle_webhook)
    
    logger.info(f"Starting webhook server on {HOST}:{PORT}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    
    print(f"======== Webhook server running at http://{HOST}:{PORT}/payment/webhook ========")
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())