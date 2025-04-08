# CryptoCloud Payment Integration Setup

This document explains how to set up the CryptoCloud payment system with your Telegram bot.

## 1. CryptoCloud Setup

1. Create an account on [CryptoCloud](https://cryptocloud.plus/)
2. Create a new project in your dashboard
3. Get your Shop ID and API Key from the project settings
4. Set up a Secret Key for webhook verification
5. Configure the webhook URL in your CryptoCloud project settings:
   - Set the URL to: `http://YOUR_SERVER_IP:8000/payment/webhook`

## 2. Bot Configuration

1. Add the following environment variables to your bot's `.env` file:

```
CRYPTOCLOUD_SHOP_ID=your_shop_id_here
CRYPTOCLOUD_API_KEY=your_api_key_here
```

## 3. Webhook Server Setup

1. Copy the `webhook_server.py` file to your server (same directory as your bot)
2. Create a `webhook.env` file with the following settings:

```
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
DATABASE_URL=data/database.sqlite3
CRYPTOCLOUD_SECRET_KEY=your_secret_key_from_cryptocloud_project_settings
```

3. Install additional dependencies:

```bash
pip install aiohttp pyjwt
```

4. Set up the webhook server as a systemd service:

```bash
# Copy the service file
sudo cp cryptocloud-webhook.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable cryptocloud-webhook

# Start the service
sudo systemctl start cryptocloud-webhook

# Check status
sudo systemctl status cryptocloud-webhook
```

## 4. Firewall Configuration

Ensure port 8000 is open on your server:

```bash
# Using UFW (Ubuntu's default firewall)
sudo ufw allow 8000/tcp
sudo ufw reload

# Using iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

## 5. Testing the Payment Flow

1. Start a conversation with your bot
2. Navigate to the balance section
3. Click "Top Up Balance"
4. Select a coin package
5. Choose "CryptoCloud" as the payment method
6. Click "Pay Now" and complete the payment
7. Check the webhook server logs:

```bash
sudo journalctl -u cryptocloud-webhook -f
```

8. Verify that your balance has been updated in the bot

## Troubleshooting

- **Webhook not receiving payments**: Check the firewall settings and ensure port 8000 is open
- **Payment received but balance not updated**: Check the webhook server logs for errors
- **Invalid token errors**: Verify your Secret Key is correctly set in both CryptoCloud and your webhook server

## Security Recommendations

- Consider using HTTPS for your webhook URL in production
- Restrict access to your webhook server by IP if possible
- Regularly check your payment logs for suspicious activity