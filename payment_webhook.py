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
DEFAULT_ADMIN_ID = os.getenv('DEFAULT_ADMIN_ID', '0')  # For fallback

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

def parse_order_id(order_id):
    """Parse user_id from order_id format tg_userID_hash"""
    try:
        if not order_id:
            return None, False
            
        # Parse the format tg_userID_hash
        if order_id.startswith("tg_"):
            parts = order_id.split('_')
            if len(parts) >= 3:
                return int(parts[1]), True
                
        # If not in our format, log it and return None
        logger.warning(f"Order ID not in expected format: {order_id}")
        return None, False
    except Exception as e:
        logger.error(f"Error parsing order_id '{order_id}': {e}")
        return None, False

def estimate_coin_amount(amount_value):
    """Estimate coin amount based on payment amount"""
    try:
        amount_value = float(amount_value)
        # Simple mapping - adjust based on your actual pricing
        coin_packages = {
            25: 500,   # ~$25 = 500 coins
            50: 1000,  # ~$50 = 1000 coins
            150: 3000, # ~$150 = 3000 coins
            500: 10000 # ~$500 = 10000 coins
        }
        
        # Find closest package by price
        closest_price = min(coin_packages.keys(), key=lambda x: abs(x - amount_value))
        coin_amount = coin_packages[closest_price]
        
        logger.info(f"Estimated coin_amount from payment amount {amount_value}: {coin_amount}")
        return coin_amount
    except Exception as e:
        logger.warning(f"Failed to estimate coin_amount: {e}")
        return 500  # Default fallback

@app.route('/payment/webhook', methods=['POST'])
def handle_webhook():
    """Handle payment webhook from CryptoCloud"""
    try:
        # Get form data and log it for debugging
        form_data = request.form
        logger.info(f"Received webhook form data keys: {list(form_data.keys())}")
        
        # Check if the webhook is missing order_id
        if 'order_id' not in form_data:
            logger.warning("Missing order_id in webhook data")
            
        # Get critical payment information
        status = form_data.get('status', '')
        invoice_id = form_data.get('invoice_id', '')
        order_id = form_data.get('order_id', '')
        token = form_data.get('token', '')
        amount_crypto = form_data.get('amount_crypto', '0')
        currency = form_data.get('currency', 'Unknown')
        
        # Log the extracted data
        logger.info(f"Payment info - Status: {status}, Invoice: {invoice_id}, Order ID: {order_id}")
        
        # Verify payment status
        if status != 'success':
            logger.warning(f"Payment not successful: {status}")
            return jsonify({'status': 'error', 'message': 'Invalid payment status'}), 400
        
        # Try to verify token
        token_valid = verify_token(token, invoice_id)
        logger.info(f"Token verification result: {token_valid}")
        
        # Parse order_id to get user_id
        user_id, success = parse_order_id(order_id)
        logger.info(f"Parsed user_id from order_id: {user_id if user_id else 'None'} (success: {success})")
        
        # Get coin amount from add_fields
        coin_amount = 0
        add_fields_str = form_data.get('add_fields', '{}')
        try:
            add_fields = json.loads(add_fields_str)
            logger.info(f"Parsed add_fields: {add_fields}")
            
            if 'coin_amount' in add_fields:
                coin_amount = int(add_fields['coin_amount'])
                logger.info(f"Found coin_amount in add_fields: {coin_amount}")
        except Exception as e:
            logger.warning(f"Error processing add_fields: {e}")
        
        # Fallback if we didn't get a user_id from order_id
        if not user_id:
            # Try to get from add_fields
            try:
                if 'user_id' in add_fields:
                    user_id = int(add_fields['user_id'])
                    logger.info(f"Got user_id from add_fields: {user_id}")
            except Exception as e:
                logger.warning(f"Error getting user_id from add_fields: {e}")
                
            # If still no user_id, use default admin
            if not user_id:
                if DEFAULT_ADMIN_ID.isdigit():
                    user_id = int(DEFAULT_ADMIN_ID)
                    logger.warning(f"Using default admin as fallback user_id: {user_id}")
                else:
                    logger.error("Could not determine user_id and no valid default admin is set")
                    return jsonify({'status': 'error', 'message': 'Invalid or missing user ID'}), 400
        
        # If we don't have a coin_amount, estimate from the payment amount
        if coin_amount == 0:
            coin_amount = estimate_coin_amount(amount_crypto)
            logger.info(f"Using estimated coin_amount: {coin_amount}")
        
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
            
            notification_sent = send_telegram_notification(user_id, notification_message)
            logger.info(f"Notification sent: {notification_sent}")
            
            return jsonify({'status': 'success', 'message': 'Payment processed'}), 200
        else:
            logger.error(f"Failed to update balance for user {user_id}")
            return jsonify({'status': 'error', 'message': 'Database update failed'}), 500
                
    except Exception as e:
        logger.error(f"Unhandled error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': f'Internal server error: {str(e)}'}), 500

@app.route('/webhook/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify the webhook server is running"""
    return jsonify({
        'status': 'success',
        'message': 'Webhook server is running',
        'time': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Make sure the data directory exists
    os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
    
    # Start the Flask app
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    app.run(host='0.0.0.0', port=port)