import mysql.connector
from mysql.connector import Error
import re
from datetime import datetime
import logging
import os
from difflib import get_close_matches

# ==========================================
# CREATE LOGS FOLDER IF NOT EXISTS
# ==========================================

if not os.path.exists('logs'):
    os.makedirs('logs')

# ==========================================
# LOGGING SETUP
# ==========================================

logging.basicConfig(
    filename='logs/bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==========================================
# DATABASE CONNECTION
# ==========================================

def connect_to_database():
    """Connect to MariaDB/MySQL database"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='whatsap_online bot',
            user='root',
            password='',
            autocommit=True
        )
        return connection
    except Error as e:
        logging.error(f"Database connection failed: {e}")
        print(f"❌ Database Error: {e}")
        return None

# ==========================================
# TEST DATABASE CONNECTION
# ==========================================

def test_database():
    """Test if database is accessible"""
    connection = connect_to_database()
    if connection:
        print("✅ Database connected successfully!")
        connection.close()
        return True
    else:
        print("❌ Database connection failed!")
        print("🔧 Check:")
        print("1. Is MySQL running in XAMPP?")
        print("2. Does database 'whatsap_online bot' exist?")
        print("3. Are the tables created?")
        return False

# ==========================================
# PRODUCT FUNCTIONS - ENHANCED SEARCH
# ==========================================

def get_all_products():
    """Get all products from database"""
    connection = connect_to_database()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE status = 'active'")
        products = cursor.fetchall()
        return products
    except Error as e:
        logging.error(f"Error fetching products: {e}")
        return []
    finally:
        connection.close()

def get_products_by_category(category):
    """Get products filtered by category"""
    connection = connect_to_database()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM products WHERE category = %s AND status = 'active'"
        cursor.execute(query, (category,))
        products = cursor.fetchall()
        return products
    except Error as e:
        logging.error(f"Error fetching products by category: {e}")
        return []
    finally:
        connection.close()

def search_products_exact(search_term):
    """Search products by name, brand, or model (EXACT MATCH)"""
    connection = connect_to_database()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT * FROM products 
            WHERE (LOWER(name) LIKE %s 
            OR LOWER(brand) LIKE %s 
            OR LOWER(model) LIKE %s)
            AND status = 'active'
        """
        search_pattern = f"%{search_term.lower()}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        products = cursor.fetchall()
        return products
    except Error as e:
        logging.error(f"Error searching products: {e}")
        return []
    finally:
        connection.close()

def search_products_smart(search_term):
    """
    SMART SEARCH: Finds products even with partial or misspelled searches
    """
    # Step 1: Try exact partial match first
    exact_results = search_products_exact(search_term)
    if exact_results:
        return exact_results, "exact"
    
    # Step 2: If no exact match, try fuzzy matching
    all_products = get_all_products()
    if not all_products:
        return [], "none"
    
    # Get all product names and IDs for fuzzy matching
    product_names = {}
    for product in all_products:
        searchable_text = f"{product['name']} {product['brand']} {product['model']}".lower()
        product_names[product['product_id']] = {
            'text': searchable_text,
            'product': product
        }
    
    search_lower = search_term.lower()
    matches = []
    
    for pid, data in product_names.items():
        if search_lower in data['text']:
            matches.append(data['product'])
        else:
            words = data['text'].split()
            for word in words:
                if len(search_lower) >= 3 and search_lower in word:
                    matches.append(data['product'])
                    break
                if len(search_lower) >= 2 and word.startswith(search_lower):
                    matches.append(data['product'])
                    break
    
    if matches:
        return matches, "fuzzy"
    
    # Step 3: Try brand matching
    brand_matches = []
    search_lower = search_term.lower()
    all_products = get_all_products()
    
    for product in all_products:
        brand_lower = product['brand'].lower()
        if len(search_lower) >= 2 and brand_lower.startswith(search_lower):
            brand_matches.append(product)
        elif search_lower in brand_lower:
            brand_matches.append(product)
    
    if brand_matches:
        return brand_matches, "brand"
    
    return [], "none"

def get_product_by_id(product_id):
    """Get single product by its ID"""
    connection = connect_to_database()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM products WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        return product
    except Error as e:
        logging.error(f"Error fetching product by ID: {e}")
        return None
    finally:
        connection.close()

def check_stock(product_id, quantity):
    """Check if product has enough stock"""
    product = get_product_by_id(product_id)
    if not product:
        return False
    return product['stock'] >= quantity

def update_stock(product_id, quantity):
    """Update stock after order"""
    connection = connect_to_database()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        query = "UPDATE products SET stock = stock - %s WHERE product_id = %s"
        cursor.execute(query, (quantity, product_id))
        connection.commit()
        return True
    except Error as e:
        logging.error(f"Error updating stock: {e}")
        return False
    finally:
        connection.close()

# ==========================================
# CUSTOMER FUNCTIONS
# ==========================================

def get_or_create_customer(phone_number, name=""):
    """Get existing customer or create new one"""
    connection = connect_to_database()
    if not connection:
        print("❌ No database connection in get_or_create_customer")
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM customers WHERE whatsapp_number = %s"
        cursor.execute(query, (phone_number,))
        customer = cursor.fetchone()
        
        if customer:
            return customer
        
        if name:
            query = "INSERT INTO customers (name, whatsapp_number) VALUES (%s, %s)"
            cursor.execute(query, (name, phone_number))
            connection.commit()
        else:
            query = "INSERT INTO customers (whatsapp_number) VALUES (%s)"
            cursor.execute(query, (phone_number,))
            connection.commit()
        
        customer_id = cursor.lastrowid
        return {
            'customer_id': customer_id, 
            'name': name if name else 'Customer', 
            'whatsapp_number': phone_number
        }
            
    except Error as e:
        logging.error(f"Error with customer: {e}")
        print(f"❌ Customer error: {e}")
        return None
    finally:
        connection.close()

# ==========================================
# ORDER FUNCTIONS
# ==========================================

def create_order(customer_id, product_id, quantity, delivery_address=""):
    """Create a new order in the database"""
    connection = connect_to_database()
    if not connection:
        return None
    
    try:
        product = get_product_by_id(product_id)
        if not product:
            return None
        
        total_price = product['price'] * quantity
        
        cursor = connection.cursor()
        query = """
            INSERT INTO orders 
            (customer_id, product_id, quantity, total_price, delivery_address) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (customer_id, product_id, quantity, total_price, delivery_address))
        connection.commit()
        order_id = cursor.lastrowid
        
        update_stock(product_id, quantity)
        
        logging.info(f"Order created: {order_id} - Product: {product_id} - Quantity: {quantity}")
        
        return order_id
    except Error as e:
        logging.error(f"Error creating order: {e}")
        return None
    finally:
        connection.close()

# ==========================================
# BOT RESPONSE FUNCTIONS
# ==========================================

def format_product_message(product):
    """Format a single product for WhatsApp message"""
    message = f"""
📱 *{product['name']}*
Brand: {product['brand']}
Model: {product['model']}

💰 Price: {product['price']:,} FCFA
📦 Stock: {product['stock']} units

{product['description']}
"""
    if product.get('color'):
        message += f"🎨 Color: {product['color']}\n"
    if product.get('ram'):
        message += f"💾 RAM: {product['ram']}\n"
    if product.get('storage'):
        message += f"💽 Storage: {product['storage']}\n"
    if product.get('processor'):
        message += f"⚡ Processor: {product['processor']}\n"
    if product.get('screen_size'):
        message += f"📐 Screen: {product['screen_size']}\n"
    
    message += f"\n🆔 Product ID: {product['product_id']}"
    return message

def format_product_list(products, search_type="exact"):
    """Format a list of products with smart search indicators"""
    if not products:
        return "❌ No products found."
    
    indicator = {
        "exact": "",
        "fuzzy": "\n💡 *Showing similar results*\n",
        "brand": "\n💡 *Showing products from this brand*\n",
        "none": "\n❌ No matches found.\n"
    }.get(search_type, "")
    
    message = f"📋 *Available Products:*{indicator}\n\n"
    
    display_products = products[:10]
    for product in display_products:
        message += f"• *{product['name']}*\n"
        message += f"  💰 {product['price']:,} FCFA | 📦 {product['stock']} units\n"
        message += f"  🆔 {product['product_id']}\n\n"
    
    if len(products) > 10:
        message += f"📊 And {len(products) - 10} more products available.\n"
    
    message += "\n🔍 To see details, search by product ID or name.\n"
    message += "💡 Tip: Type *order [ID] [qty]* to buy"
    
    return message

def suggest_alternatives(search_term):
    """Suggest alternative products when no exact match found"""
    all_products = get_all_products()
    if not all_products:
        return "❌ No products available in our catalog."
    
    product_names = []
    for product in all_products:
        product_names.append(product['name'])
        product_names.append(product['brand'])
        product_names.append(product['model'])
    
    search_lower = search_term.lower()
    suggestions = get_close_matches(search_lower, [name.lower() for name in product_names], n=5, cutoff=0.3)
    
    if suggestions:
        suggestion_products = []
        for sugg in suggestions:
            for product in all_products:
                if (sugg in product['name'].lower() or 
                    sugg in product['brand'].lower() or 
                    sugg in product['model'].lower()):
                    if product not in suggestion_products:
                        suggestion_products.append(product)
                        break
        
        if suggestion_products:
            message = f"❌ No exact match for '{search_term}'.\n\n"
            message += f"💡 *Did you mean one of these?*\n\n"
            for product in suggestion_products[:5]:
                message += f"• *{product['name']}*\n"
                message += f"  💰 {product['price']:,} FCFA\n"
                message += f"  🆔 {product['product_id']}\n\n"
            message += "\n📝 Tip: Just type the product name to search"
            return message
    
    return f"❌ No products found matching '{search_term}'.\n\n💡 Try typing a brand name like *samsung* or *iphone*"

# ==========================================
# MAIN BOT LOGIC - COMPLETE REWRITE
# ==========================================

def process_message(message, phone_number):
    """
    Process incoming WhatsApp messages
    ANY text that's not a command = AUTO SEARCH
    """
    
    # Log the incoming message
    logging.info(f"Message from {phone_number}: {message}")
    
    # Get or create customer
    customer = get_or_create_customer(phone_number)
    if not customer:
        logging.error(f"Failed to get/create customer for {phone_number}")
        return "❌ System error. Please try again later."
    
    # Clean the message
    clean_message = message.strip().lower()
    
    # ==========================================
    # STEP 1: CHECK FOR COMMANDS FIRST
    # ==========================================
    
    # COMMAND: hi, hello, hey, help, start
    if clean_message in ['hi', 'hello', 'hey', 'help', 'start']:
        return f"""
👋 *Welcome to TechShop!* 

We sell quality phones, laptops, and accessories.

*How can I help you today?*

📱 Type *phones* to see our phones
💻 Type *laptops* to see our laptops
🎧 Type *accessories* to see our accessories
📦 Type *stock [product ID]* to check availability
🛒 Type *order [product ID] [quantity]* to buy
❓ Type *faq* for common questions
👨‍💼 Type *agent* to talk to a human

💡 *Just type a product name to search!*
• Type *iphone* → finds iPhones
• Type *samsung* → finds Samsung
• Type *dell* → finds Dell laptops
"""
    
    # COMMAND: phones, phone, laptops, laptop, accessories, accessory
    if clean_message in ['phones', 'phone', 'laptops', 'laptop', 'accessories', 'accessory']:
        category_map = {
            'phone': 'Phone',
            'phones': 'Phone',
            'laptop': 'Laptop',
            'laptops': 'Laptop',
            'accessory': 'Accessory',
            'accessories': 'Accessory'
        }
        category = category_map.get(clean_message, clean_message.capitalize())
        products = get_products_by_category(category)
        
        if not products:
            return f"❌ Sorry, no {category}s found in our catalog."
        
        return format_product_list(products, "exact")
    
    # COMMAND: stock [product_id]
    if clean_message.startswith('stock '):
        product_id = clean_message[6:].strip().upper()
        product = get_product_by_id(product_id)
        
        if not product:
            return f"❌ Product {product_id} not found.\n\n💡 Just type the product name to search for it."
        
        return f"""
📦 *Stock Check*

🆔 Product: {product['product_id']}
📱 Name: {product['name']}
📦 Stock: {product['stock']} units
💰 Price: {product['price']:,} FCFA

Status: {'✅ Available' if product['stock'] > 0 else '❌ Out of stock'}
"""
    
    # COMMAND: order [product_id] [quantity]
    if clean_message.startswith('order '):
        parts = clean_message[6:].strip().split()
        
        if len(parts) < 2:
            return "❌ Please specify: `order [product ID] [quantity]`\nExample: `order PH001 2`"
        
        product_id = parts[0].upper()
        try:
            quantity = int(parts[1])
        except ValueError:
            return "❌ Quantity must be a number."
        
        if quantity <= 0:
            return "❌ Quantity must be greater than 0."
        
        product = get_product_by_id(product_id)
        if not product:
            return f"❌ Product {product_id} not found.\n\n💡 Just type the product name to find the correct ID."
        
        if not check_stock(product_id, quantity):
            return f"❌ Sorry, only {product['stock']} units of {product['name']} available."
        
        order_id = create_order(customer['customer_id'], product_id, quantity, "Pending delivery address")
        
        if order_id:
            return f"""
✅ *Order Confirmed!*

🆔 Order ID: {order_id}
📱 Product: {product['name']}
📦 Quantity: {quantity}
💰 Total: {product['price'] * quantity:,} FCFA

📋 Please reply with your delivery address to complete your order.

To confirm your address, type:
*address [your address]*

Example:
*address Douala, Cameroon*
"""
        else:
            return "❌ Order failed. Please try again."
    
    # COMMAND: address [address]
    if clean_message.startswith('address '):
        address = clean_message[8:].strip()
        if len(address) < 5:
            return "❌ Please provide a complete address."
        
        return f"""
✅ *Address Received!*

📍 {address}

We'll confirm your order within 24 hours.

You'll receive a confirmation message when your order is ready.

Thank you for shopping with TechShop! 🙏
"""
    
    # COMMAND: faq
    if clean_message == 'faq':
        return """
❓ *Frequently Asked Questions*

1️⃣ *Delivery*
We deliver to all major cities. Delivery takes 1-3 business days.

2️⃣ *Payment*
We accept:
• Mobile Money (MTN, Orange)
• Bank Transfer
• Cash on Delivery

3️⃣ *Warranty*
• Phones: 1 year warranty
• Laptops: 1 year warranty
• Accessories: 6 months warranty

4️⃣ *Returns*
Items can be returned within 7 days of purchase.

5️⃣ *Stock*
Type: *stock [product ID]*

Need more help? Type *agent* to talk to a human.
"""
    
    # COMMAND: agent
    if clean_message == 'agent':
        return """
👨‍💼 *Connecting you to a human agent*

One of our representatives will contact you within 30 minutes.

Please wait for our message or call us at:
📞 +237 6XX XXX XXX

Thank you for your patience! 🙏
"""
    
    # ==========================================
    # STEP 2: IF NOT A COMMAND → AUTO SEARCH!
    # ==========================================
    
    # Check if it's a product ID (like PH001)
    if re.match(r'^[A-Z]{2}\d{3}$', clean_message.upper()):
        product = get_product_by_id(clean_message.upper())
        if product:
            return format_product_message(product)
    
    # AUTO SEARCH: ANY text with 2 or more characters
    if len(clean_message) >= 2:
        products, search_type = search_products_smart(clean_message)
        if products:
            return f"🔍 *Search results for '{message}':*\n\n" + format_product_list(products, search_type)
        else:
            # No results found - show suggestions
            return suggest_alternatives(message)
    
    # ==========================================
    # STEP 3: FALLBACK (should never reach here)
    # ==========================================
    
    return """
❓ I didn't understand that.

Here's what you can do:

📱 Just type a product name to search:
• *iphone* → finds iPhones
• *samsung* → finds Samsung
• *dell* → finds Dell laptops

📋 Or use these commands:
• Type *phones* for phones
• Type *laptops* for laptops
• Type *accessories* for accessories
• Type *order [ID] [qty]* to buy
• Type *faq* for common questions
• Type *agent* for human help
"""

# ==========================================
# RUN THE BOT
# ==========================================

if __name__ == "__main__":
    print("🤖 WhatsApp Bot Starting...")
    print("=" * 50)
    
    # Test database connection first
    print("\n🔍 Testing database connection...")
    if not test_database():
        print("\n❌ Cannot start bot - database not accessible!")
        print("📋 Please fix the database issues above and restart.")
        exit(1)
    
    print("\n✅ All systems ready!")
    print("\n🧠 SMART SEARCH: Just type ANY product name!")
    print("   Example: 'iphone' → finds iPhones")
    print("   Example: 'samsung' → finds Samsung")
    print("   Example: 'dell' → finds Dell laptops")
    print("\nTest the bot by typing messages below:")
    print("(Type 'exit' to quit)")
    print("-" * 50)
    
    test_phone = "237699999999"
    
    while True:
        try:
            user_input = input("\n👤 You: ")
            
            if user_input.lower() == 'exit':
                print("👋 Goodbye!")
                break
            
            response = process_message(user_input, test_phone)
            print(f"\n🤖 Bot: {response}")
            print("-" * 50)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.")