import requests
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get("price", 4416.0))
    except:
        return 4416.0

price = get_gold()
time = datetime.now().strftime("%H:%M")

msg = f"""🏆 YallaGold ICT Analysis
💰 XAUUSD: ${price:.2f}
⏰ {time}
📊 انتظار - لا تدخل الان 📊"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, data={"chat_id": CHANNEL, "text": msg})
print(res.text)
