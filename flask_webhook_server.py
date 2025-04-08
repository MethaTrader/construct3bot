from flask import Flask, request, jsonify
import logging
import os
import sqlite3
import jwt
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='webhook.log'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'data/database.sqlite3')
SECRET_KEY = os.getenv('CRYPTOCLOUD_SECRET_KEY', '')  # Get from CryptoCloud project settings
PORT = int(os.getenv('WEBHOOK_PORT', 5000))

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
            return True
        else:
            logger.error(f"User {user_id} not found in database")
            return False
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        conn.close()

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
        
        # Verify payment status and token
        if status != 'success':
            logger.warning(f"Payment not successful: {status}")
            return jsonify({'status': 'error', 'message': 'Invalid payment status'}), 400
        
        if not verify_token(token, invoice_id):
            logger.warning("Token verification failed")
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
        
        # Extract user_id and amount from order_id (format: user_USER_ID_AMOUNT)
        if order_id.startswith('user_'):
            try:
                parts = order_id.split('_')
                if len(parts) >= 3:
                    user_id = int(parts[1])
                    coins_amount = int(parts[2])
                    
                    # Update user balance
                    if update_user_balance(user_id, coins_amount):
                        logger.info(f"Successfully credited {coins_amount} coins to user {user_id}")
                        return jsonify({'status': 'success', 'message': 'Payment processed'}), 200
                    else:
                        logger.error(f"Failed to update balance for user {user_id}")
                        return jsonify({'status': 'error', 'message': 'Database update failed'}), 500
            except Exception as e:
                logger.error(f"Error parsing order_id: {e}")
                return jsonify({'status': 'error', 'message': f'Invalid order_id format: {e}'}), 400
        
        logger.warning(f"Invalid order_id format: {order_id}")
        return jsonify({'status': 'error', 'message': 'Invalid order_id format'}), 400
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Make sure the data directory exists
    os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
    
    # Start the Flask app
    print(f"Starting webhook server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)