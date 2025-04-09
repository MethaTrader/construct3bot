from flask import Flask, request, jsonify
import logging
import os
import sqlite3
import jwt
import requests
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
DATABASE_URL = os.getenv('DATABASE_URL', 'data/database.sqlite3')
SECRET_KEY = os.getenv('CRYPTOCLOUD_SECRET_KEY', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

app = Flask(__name__)

def verify_token(token, invoice_id):
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

def update_user_balance(user_id, amount):
    """Update user balance in the database"""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # First, get current balance
        cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            current_balance = result[0]
            new_balance = current_balance + amount
            
            # Update balance
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "UPDATE users SET balance = ?, last_active = ? WHERE telegram_id = ?",
                (new_balance, now, user_id)
            )
            conn.commit()
            
            logger.info(f"Updated balance for user {user_id}: {current_balance} -> {new_balance}")
            return True, current_balance, new_balance
        else:
            logger.error(f"User {user_id} not found in database")
            return False, 0, 0
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False, 0, 0
    finally:
        conn.close()

def send_telegram_notification(user_id, message):
    """Send a notification to the user via Telegram"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set, cannot send notification")
        return False
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info(f"Notification sent to user {user_id}")
            return True
        else:
            logger.error(f"Failed to send notification: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

@app.route('/payment/webhook', methods=['POST'])
def handle_webhook():
    """Handle payment webhook from CryptoCloud"""
    try:
        # Get data from request - CryptoCloud sends form data
        data = request.form
        
        logger.info(f"Received webhook: {data}")
        
        # Extract payment information
        status = data.get('status')
        invoice_id = data.get('invoice_id')
        order_id = data.get('order_id', '')
        token = data.get('token', '')
        amount_crypto = data.get('amount_crypto', '0')
        currency = data.get('currency', 'Unknown')
        
        # Additional fields
        add_fields = json.loads(data.get('add_fields', '{}'))
        coin_amount = int(add_fields.get('coin_amount', 0))
        
        # Verify payment status and token
        if status != 'success':
            logger.warning(f"Payment not successful: {status}")
            return jsonify({'status': 'error', 'message': 'Invalid payment status'}), 400
        
        if not verify_token(token, invoice_id):
            logger.warning("Token verification failed")
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
        
        # Parse the new order_id format (telegramID.hash)
        try:
            user_id_part = order_id.split('.')[0]
            user_id = int(user_id_part)
            
            # If coin_amount wasn't in add_fields, try to get it from somewhere else or use a default
            if coin_amount == 0:
                logger.warning(f"Coin amount not found in add_fields, using default value based on order ID: {order_id}")
                # Here you could implement a lookup table or other method to determine coin amount
            
            # Update user balance
            update_success, old_balance, new_balance = update_user_balance(user_id, coin_amount)
            
            if update_success:
                logger.info(f"Successfully credited {coin_amount} coins to user {user_id}")
                
                # Send notification to user
                notification_message = (
                    f"✅ <b>Payment Successful!</b>\n\n"
                    f"Your payment of {amount_crypto} {currency} has been received.\n"
                    f"{coin_amount} coins have been added to your balance.\n\n"
                    f"Old balance: {old_balance} coins\n"
                    f"New balance: {new_balance} coins\n\n"
                    f"Thank you for your purchase!"
                )
                
                send_telegram_notification(user_id, notification_message)
                return jsonify({'status': 'success', 'message': 'Payment processed'}), 200
            else:
                logger.error(f"Failed to update balance for user {user_id}")
                return jsonify({'status': 'error', 'message': 'Database update failed'}), 500
                
        except Exception as e:
            logger.error(f"Error parsing order_id or processing payment: {e}")
            return jsonify({'status': 'error', 'message': f'Invalid order_id format or processing error: {e}'}), 400
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Make sure the data directory exists
    os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
    
    # Start the Flask app
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    app.run(host='0.0.0.0', port=port)