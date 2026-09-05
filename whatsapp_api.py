from flask import Flask, request, jsonify
from datetime import datetime
import os
import logging

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

# ==========================================
# VERIFY TOKEN (For WhatsApp Webhook)
# ==========================================

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'my_secure_token_123')

# ==========================================
# IMPORT YOUR BOT LOGIC
# ==========================================

try:
    from main import process_message, search_products_smart, get_all_products
    print("✅ Bot logic imported successfully!")
except ImportError as e:
    print(f"⚠️ Could not import main.py: {e}")
    # Create a fallback function if main.py isn't available
    def process_message(msg, phone):
        return f"Bot is working! You said: '{msg}'. Please type 'help' for options."

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
# HOME PAGE
# ==========================================

@app.route('/')
def home():
    """Home page showing bot status"""
    return """
    <h1>🤖 TechShop WhatsApp Bot</h1>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Server Time:</strong> {}</p>
    <p><strong>Endpoints:</strong></p>
    <ul>
        <li><a href="/health">GET /health</a> - Health check</li>
        <li><a href="/webhook">GET /webhook</a> - Webhook verification</li>
        <li>POST /webhook - Receive WhatsApp messages</li>
    </ul>
    <p>💡 Your bot is ready to connect to WhatsApp!</p>
    """.format(datetime.now().isoformat())

# ==========================================
# WEBHOOK VERIFICATION (WhatsApp)
# ==========================================

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify the webhook with Meta/WhatsApp"""
    try:
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logging.info(f"Webhook verification - Mode: {mode}, Token: {token}")
        
        if mode and token and mode == 'subscribe' and token == VERIFY_TOKEN:
            logging.info("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            logging.warning("❌ Webhook verification failed - token mismatch")
            return "Verification failed", 403
    except Exception as e:
        logging.error(f"Verification error: {e}")
        return "Error", 500

# ==========================================
# INCOMING MESSAGE HANDLER (WhatsApp)
# ==========================================

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.json
        logging.info(f"📨 Received webhook: {data}")
        
        if 'entry' in data:
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    if 'messages' in change.get('value', {}):
                        for message in change['value']['messages']:
                            phone_number = message.get('from')
                            text = message.get('text', {}).get('body', '')
                            
                            if phone_number and text:
                                logging.info(f"📱 Message from {phone_number}: {text}")
                                
                                # Process the message using your bot
                                response = process_message(text, phone_number)
                                logging.info(f"🤖 Response: {response}")
                                
                                # TODO: Send response via WhatsApp API
                                # (We'll add this in Phase 2)
        
        return "OK", 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return "Error", 500

# ==========================================
# RUN THE SERVER
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print("🚀 WhatsApp API Server Starting...")
    print("=" * 50)
    print(f"📡 Port: {port}")
    print(f"🔗 Health: http://localhost:{port}/health")
    print(f"🔗 Webhook: http://localhost:{port}/webhook")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)