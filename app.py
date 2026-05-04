#!/usr/bin/env python3
"""
WaBiz Pro - WhatsApp Business API Backend
Integrates with WhatsApp Business Cloud API (Meta)
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import requests
from pathlib import Path
import hashlib
import hmac

app = Flask(__name__)

# ==================== CONFIG ====================
# WhatsApp API Configuration
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "wabiz_pro_2024")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")

# Phone number ID from WhatsApp Business API
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

# Data storage
DATA_DIR = Path("/home/tedy/.openclaw/workspace/whatsapp-business/data")
DATA_DIR.mkdir(exist_ok=True)

# ==================== HELPERS ====================

def load_business(phone):
    """Load business config"""
    config_file = DATA_DIR / f"{phone}.json"
    if config_file.exists():
        return json.loads(config_file.read_text())
    return None

def save_business(phone, data):
    """Save business config"""
    config_file = DATA_DIR / f"{phone}.json"
    config_file.write_text(json.dumps(data, indent=2))

def load_orders(phone):
    """Load orders for a business"""
    orders_file = DATA_DIR / f"{phone}_orders.json"
    if orders_file.exists():
        return json.loads(orders_file.read_text())
    return []

def save_order(phone, order):
    """Save a new order"""
    orders = load_orders(phone)
    orders.append(order)
    orders_file = DATA_DIR / f"{phone}_orders.json"
    orders_file.write_text(json.dumps(orders, indent=2))

def load_customers(phone):
    """Load customers for a business"""
    customers_file = DATA_DIR / f"{phone}_customers.json"
    if customers_file.exists():
        return json.loads(customers_file.read_text())
    return {}

def save_customer(phone, customer_data):
    """Save customer info"""
    customers = load_customers(phone)
    customer_id = customer_data['phone']
    customers[customer_id] = customer_data
    customers_file = DATA_DIR / f"{phone}_customers.json"
    customers_file.write_text(json.dumps(customers, indent=2))

# ==================== WHATSAPP API ====================

def send_whatsapp_message(to, message, interactive=None, media=None):
    """Send message via WhatsApp Business API"""
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        return {"error": "WhatsApp API not configured"}
    
    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    if interactive:
        # Interactive message with buttons
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
    elif media:
        # Media message
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "product",
                "body": {"text": message}
            }
        }
    else:
        # Simple text message
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def send_interactive_buttons(to, message, buttons):
    """Send interactive button message (like Jasper's Market)"""
    interactive = {
        "type": "button",
        "body": {"text": message},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": b['id'], "title": b['title']}}
                for b in buttons
            ]
        }
    }
    return send_whatsapp_message(to, message, interactive=interactive)

def send_product_list(to, business):
    """Send product catalog as interactive list (like Jasper's)"""
    products = business.get('products', [])
    
    # Build rows for list message
    rows = []
    for i, p in enumerate(products):
        rows.append({
            "id": f"product_{i}",
            "title": p.get('name', 'Product')[:24],
            "description": p.get('price', '')
        })
    
    interactive = {
        "type": "list",
        "header": {"type": "text", "text": f"🛒 {business['name']}"},
        "body": {"text": "Select a product to order:"},
        "action": {
            "button": "View Products",
            "sections": [{"title": "Products", "rows": rows}]
        }
    }
    
    return send_whatsapp_message(to, "Browse our products:", interactive=interactive)

def send_order_confirmation(to, order):
    """Send order confirmation template"""
    interactive = {
        "type": "button",
        "body": {
            "text": f"✅ Order #{order['id']} Confirmed!\n\n"
                    f"Items: {', '.join(order['items'])}\n"
                    f"Total: GH₵{order['total']}\n\n"
                    f"Delivery: {order.get('delivery_address', 'N/A')}"
        },
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": "track_order", "title": "📍 Track Order"}},
                {"type": "reply", "reply": {"id": "reorder", "title": "🔄 Reorder"}}
            ]
        }
    }
    return send_whatsapp_message(to, "", interactive=interactive)

# ==================== MESSAGE HANDLING ====================

def process_message(business, customer_phone, message_text, message_type=None):
    """Process incoming message and generate response"""
    products = business.get('products', [])
    auto_replies = business.get('auto_replies', {})
    message = message_text.strip().lower()
    
    # Track customer
    customers = load_customers(business['phone'])
    if customer_phone not in customers:
        save_customer(business['phone'], {
            'phone': customer_phone,
            'first_contact': datetime.now().isoformat(),
            'total_orders': 0
        })
    
    # Handle button responses (interactive)
    if message_type == "button":
        if message.startswith("product_"):
            idx = int(message.split("_")[1])
            if 0 <= idx < len(products):
                p = products[idx]
                return send_interactive_buttons(
                    customer_phone,
                    f"{p['name']} - {p['price']}\n\n{p.get('description', '')}",
                    [
                        {"id": f"order_{idx}", "title": "🛒 Order Now"},
                        {"id": "catalog", "title": "📋 More Products"}
                    ]
                )
        elif message == "catalog":
            return send_product_list(customer_phone, business)
        elif message.startswith("order_"):
            return send_whatsapp_message(
                customer_phone,
                "Please send your:\n1. Name\n2. Delivery address\n3. Phone number"
            )
    
    # Handle order (number input)
    if message.isdigit():
        idx = int(message) - 1
        if 0 <= idx < len(products):
            p = products[idx]
            return send_interactive_buttons(
                customer_phone,
                f"Great choice! *{p['name']}* - {p['price']}\n\nTo confirm order, reply with your details.",
                [
                    {"id": f"order_{idx}", "title": "🛒 Order Now"},
                    {"id": "catalog", "title": "More Products"}
                ]
            )
    
    # Check auto-replies
    for keyword, reply in auto_replies.items():
        if keyword.lower() in message:
            return send_whatsapp_message(customer_phone, reply)
    
    # Default - show catalog
    return send_product_list(customer_phone, business)

# ==================== FLASK ROUTES ====================

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "WaBiz Pro",
        "whatsapp_api": "connected" if ACCESS_TOKEN else "not_configured"
    })

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Verify webhook for WhatsApp"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print(f"Webhook verified!")
        return challenge, 200
    
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook_receive():
    """Receive messages from WhatsApp"""
    data = request.json
    
    if data.get('object') != 'whatsapp_business_account':
        return jsonify({"status": "ignored"}), 200
    
    # Process each entry
    for entry in data.get('entry', []):
        for change in entry.get('changes', []):
            value = change.get('value', {})
            
            # Handle status updates (delivered, read)
            for status in value.get('statuses', []):
                print(f"Message status: {status.get('status')}")
            
            # Handle incoming messages
            for msg in value.get('messages', []):
                phone_id = value.get('metadata', {}).get('phone_number_id')
                from_num = msg.get('from')
                msg_type = msg.get('type')
                
                if msg_type == "text":
                    text = msg.get('text', {}).get('body', '')
                    print(f"Message from {from_num}: {text}")
                    
                    # Get business for this phone ID
                    business = load_business(PHONE_NUMBER_ID)
                    if business:
                        process_message(business, from_num, text, msg_type)
                        
                elif msg_type == "interactive":
                    interactive = msg.get('interactive', {})
                    if interactive.get('type') == "button":
                        button_id = interactive.get('button_reply', {}).get('id', '')
                        
                        business = load_business(PHONE_NUMBER_ID)
                        if business:
                            process_message(business, from_num, button_id, "button")
    
    return jsonify({"status": "ok"}), 200

# ==================== BUSINESS API ====================

@app.route('/api/setup', methods=['POST'])
def setup_business():
    """Set up a new business"""
    data = request.json
    
    phone = data.get('phone', '').replace('+', '').replace('233', '')
    name = data.get('name', '')
    welcome_msg = data.get('welcome_msg', 'Thanks for contacting us!')
    products = data.get('products', [])
    
    if not phone or not name:
        return jsonify({"error": "Missing required fields"}), 400
    
    business_data = {
        "phone": phone,
        "name": name,
        "welcome_msg": welcome_msg,
        "products": products,
        "auto_replies": data.get('auto_replies', {}),
        "created_at": datetime.now().isoformat()
    }
    
    save_business(phone, business_data)
    
    # If this is the configured WhatsApp number, also save as active
    if phone == PHONE_NUMBER_ID:
        save_business(PHONE_NUMBER_ID, business_data)
    
    return jsonify({
        "success": True,
        "phone": phone,
        "message": f"Business '{name}' set up successfully"
    })

@app.route('/api/business/<phone>', methods=['GET'])
def get_business(phone):
    """Get business config"""
    phone = phone.replace('+', '').replace('233', '')
    business = load_business(phone)
    
    if not business:
        return jsonify({"error": "Business not found"}), 404
    
    return jsonify(business)

@app.route('/api/catalog/<phone>', methods=['GET'])
def get_catalog(phone):
    """Get business catalog for sharing"""
    phone = phone.replace('+', '').replace('233', '')
    business = load_business(phone)
    
    if not business:
        return jsonify({"error": "Business not found"}), 404
    
    products = business.get('products', [])
    catalog_text = f"*{business['name']}* 🛒\n\n"
    catalog_text += f"{business.get('welcome_msg', 'Welcome!')}\n\n"
    catalog_text += "*Our Products:*\n"
    
    for i, p in enumerate(products):
        desc = p.get('description', '')
        catalog_text += f"{i+1}. {p['name']} - {p['price']}"
        if desc:
            catalog_text += f" ({desc})"
        catalog_text += "\n"
    
    return jsonify({
        "name": business['name'],
        "welcome_msg": business.get('welcome_msg', ''),
        "products": products,
        "catalog_text": catalog_text
    })

@app.route('/api/send', methods=['POST'])
def api_send_message():
    """API to send message to customer"""
    data = request.json
    
    to = data.get('to', '').replace('+', '').replace('233', '')
    message = data.get('message', '')
    
    result = send_whatsapp_message(to, message)
    return jsonify(result)

@app.route('/api/orders/<phone>', methods=['GET'])
def get_orders(phone):
    """Get all orders for a business"""
    phone = phone.replace('+', '').replace('233', '')
    orders = load_orders(phone)
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order"""
    data = request.json
    
    business_phone = data.get('business_phone', '').replace('+', '').replace('233', '')
    customer_phone = data.get('customer_phone', '')
    items = data.get('items', [])
    total = data.get('total', 0)
    delivery_address = data.get('delivery_address', '')
    customer_name = data.get('customer_name', '')
    
    order = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "business_phone": business_phone,
        "customer_phone": customer_phone,
        "customer_name": customer_name,
        "items": items,
        "total": total,
        "delivery_address": delivery_address,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    save_order(business_phone, order)
    
    # Send confirmation via WhatsApp
    send_order_confirmation(customer_phone, order)
    
    # Update customer order count
    customers = load_customers(business_phone)
    if customer_phone in customers:
        customers[customer_phone]['total_orders'] = customers[customer_phone].get('total_orders', 0) + 1
        customers[customer_phone]['last_order'] = datetime.now().isoformat()
        save_customer(business_phone, customers[customer_phone])
    
    return jsonify({"success": True, "order_id": order['id']})

@app.route('/api/customers/<phone>', methods=['GET'])
def get_customers(phone):
    """Get all customers for a business"""
    phone = phone.replace('+', '').replace('233', '')
    customers = load_customers(phone)
    return jsonify(customers)

@app.route('/api/broadcast', methods=['POST'])
def broadcast():
    """Send broadcast message to all customers"""
    data = request.json
    
    business_phone = data.get('business_phone', '').replace('+', '').replace('233', '')
    message = data.get('message', '')
    
    business = load_business(business_phone)
    if not business:
        return jsonify({"error": "Business not found"}), 404
    
    customers = load_customers(business_phone)
    
    # Send to all customers
    sent = 0
    for customer_id in customers:
        result = send_whatsapp_message(customer_id, message)
        if 'messages' in result:
            sent += 1
    
    return jsonify({
        "success": True,
        "sent": sent,
        "total": len(customers)
    })

# ==================== VERIFY SIGNATURE ====================

def verify_signature(payload, signature):
    """Verify request is from Facebook"""
    if not signature or not ACCESS_TOKEN:
        return True  # Skip if not configured
    
    expected = hmac.new(
        ACCESS_TOKEN.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)

# ==================== MAIN ====================

if __name__ == '__main__':
    print("🚀 WaBiz Pro Server")
    print(f"WhatsApp API: {'Connected' if ACCESS_TOKEN else 'Not Configured'}")
    print(f"Webhook verification token: {VERIFY_TOKEN[:10]}...")
    print("\nTo configure WhatsApp API, set these environment variables:")
    print("  WHATSAPP_ACCESS_TOKEN=...")
    print("  PHONE_NUMBER_ID=...")
    print("\nRunning on http://localhost:5000")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)