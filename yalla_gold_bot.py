import requests, datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "@YallaGold"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r['price'])
    except:
        return 4385.0

price = get_price()
now = datetime.datetime.now().strftime("%H:%M")
msg = f"YallaGold 🏆\n💰 الذهب: ${price:.2f}\n⏰ {now}\n📊 تحليل: انتظار - سوق متذبذب\n\n#XAUUSD #ذهب"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, data={"chat_id": CHANNEL, "text": msg})
print(f"SEND TO {CHANNEL} -> {res.text}")

# اذا فشل نطبع الخطأ باش نشوفوه في Actions
if not res.ok:
    print("FAILED! Check if bot is admin in @YallaGold and channel @ is correct")
