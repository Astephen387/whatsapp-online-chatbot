from flask import Flask, request, jsonify, send_file
import json
import logging
import os
from datetime import datetime
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# ==========================================
# LOGGING SETUP
# ==========================================

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
# ==========================================
# DATABASE CONNECTION (FOR CLOUD)
# ==========================================

def connect_to_database():
    """Connect to database - works on cloud too"""
    try:
        # For cloud, use environment variables
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=os.environ.get('DB_NAME', 'whatsap_online bot'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            autocommit=True
        )
        return connection
    except Error as e:
        logging.error(f"Database connection failed: {e}")
        return None

# ==========================================
# IMPORT BOT LOGIC
# ==========================================

# Import your main bot functions
from main import process_message, get_all_products, get_products_by_category, search_products_smart

# ==========================================
# WEBHOOK VERIFICATION
# ==========================================

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'my_secure_token_123')

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify the webhook with Meta/WhatsApp"""
    try:
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token and mode == 'subscribe' and token == VERIFY_TOKEN:
            logging.info("Webhook verified successfully")
            return challenge, 200
        else:
            logging.warning("Webhook verification failed")
            return "Verification failed", 403
    except Exception as e:
        logging.error(f"Verification error: {e}")
        return "Error", 500

# ==========================================
# INCOMING MESSAGE HANDLER
# ==========================================

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.json
        logging.info(f"Received webhook: {json.dumps(data, indent=2)}")
        
        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    if 'messages' in change.get('value', {}):
                        for message in change['value']['messages']:
                            phone_number = message.get('from')
                            text = message.get('text', {}).get('body', '')
                            
                            if phone_number and text:
                                response = process_message(text, phone_number)
                                
                                # TODO: Send response via WhatsApp API
                                # We'll implement this when we get API credentials
                                logging.info(f"Response to {phone_number}: {response}")
        
        return "OK", 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return "Error", 500

# ==========================================
# HEALTH CHECK
# ==========================================

@app.route('/health', methods=['GET'])
def health_check():
    """Check if the API is running"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }), 200

# ==========================================
# DASHBOARD (Optional)
# ==========================================

@app.route('/')
def home():
    """Home page"""
    return """
    <h1>🤖 TechShop WhatsApp Bot</h1>
    <p>Status: ✅ Running</p>
    <p>Time: {}</p>
    <p>Endpoints:</p>
    <ul>
        <li>GET /webhook - Verification</li>
        <li>POST /webhook - Receive messages</li>
        <li>GET /health - Health check</li>
    </ul>
    """.format(datetime.now().isoformat())

# ==========================================
# RUN THE SERVER
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print("🚀 WhatsApp API Server Starting...")
    print(f"📡 Port: {port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port)