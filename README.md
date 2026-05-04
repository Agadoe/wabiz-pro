# 💬 WaBiz Pro
### WhatsApp Business Platform for Ghana

A complete WhatsApp Business solution built for Ghanaian SMEs. Accept orders, send broadcasts, track analytics - all from WhatsApp.

---

## 🚀 Quick Start

### 1. Get WhatsApp Business API
1. Go to [Meta Developers](https://developers.facebook.com/)
2. Create an app → WhatsApp product
3. Get your credentials (Phone Number ID, Access Token)

### 2. Configure
```bash
cd whatsapp-business
./setup.sh
```

Or manually create `.env`:
```env
WHATSAPP_ACCESS_TOKEN=your_token_here
PHONE_NUMBER_ID=your_phone_number_id
VERIFY_TOKEN=your_verify_token
```

### 3. Run
```bash
python3 app.py
```

### 4. Open Admin Panel
```
http://localhost:5000
```

Add your products, customize auto-replies, and share your WhatsApp catalog!

---

## 📁 Files

| File | Description |
|------|-------------|
| `index.html` | Admin dashboard (catalog, marketing, orders, analytics, pricing) |
| `app.py` | Flask backend with WhatsApp API integration |
| `setup.sh` | Interactive setup script |
| `README.md` | This file |

---

## 🔑 Features

### For Customers (via WhatsApp)
- 📋 Browse products via interactive menu
- 🛒 Order with one tap
- 📍 Track order status
- 🔄 Quick reorder

### For Business Owners (Dashboard)
- 📦 Product catalog management
- 📢 Broadcast messages to all customers
- 📅 Schedule marketing campaigns
- 📊 Revenue & customer analytics
- 💰 Subscription plans (Free/Starter/Pro/Enterprise)

---

## 💳 Pricing Plans

| Plan | Price | Features |
|------|-------|----------|
| Free | GH₵0/mo | 5 products, basic auto-reply |
| Starter | GH₵150/mo | 20 products, broadcasts, orders |
| Pro | GH₵400/mo | Unlimited everything |
| Enterprise | GH₵1,000/mo | Multi-user, API, priority support |

---

## 🔧 WhatsApp API Setup

### Getting Credentials
1. **Meta Developer Account**: https://developers.facebook.com/
2. **Create App**: Select "WhatsApp" product
3. **Get Credentials**:
   - Phone Number ID
   - Access Token (Temporary - needs refreshing)
   - WABA ID

### Webhook Setup
Your server URL must be publicly accessible. Options:
- **ngrok**: `ngrok http 5000`
- **Railway/Render**: Deploy the app
- **Cloud VPS**: Deploy to AWS/DigitalOcean

Configure in Meta dashboard:
- URL: `https://your-domain.com/webhook`
- Verify Token: (from .env)
- Fields: `messages`, `message_statuses`

---

## 📱 Demo

Open `index.html` in a browser to see:
- Product catalog builder
- WhatsApp interactive preview
- Marketing broadcast templates
- Analytics dashboard

Click "Test on WhatsApp" to open real WhatsApp with your catalog!

---

## 🌍 Built For Ghana

- Mobile Money payment integration
- Ghana Cedis (GH₵) pricing
- Local support
- Affordable for SMEs

---

## 📄 License

MIT License - Build your business on top of this!

---

## 🙏 Credits

- [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Jasper's Market Sample](https://github.com/fbsamples/whatsapp-business-jaspers-market)