import requests
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"  # YallaGold Private ID ✅

def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get("price", 4395.70))
    except:
        return 4395.70

price = get_gold()
time = datetime.now().strftime("%H:%M")

msg = f"""🏆 YallaGold ICT Analysis
💰 XAUUSD: ${price:.2f}
⏰ {time}
📊 انتظار - لا تدخل الان
🔗 t.me/+0RhWuGnsfHo3MTNk"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, data={"chat_id": CHANNEL, "text": msg})
print(f"RESULT: {res.text}")
