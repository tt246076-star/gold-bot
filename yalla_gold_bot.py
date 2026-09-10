import requests
BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "@YallaGoldICTBot"
try:
    r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
    price = r.get('price', 2650)
except:
    price = 2650
text = f"💰 الذهب: ${price} / الأونصة\n🤖 يلا قولد بوت - تحديث كل 5 دقايق\n📈 @YallaGoldICTBot"
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.get(url, params={"chat_id": CHANNEL, "text": text})
print("تم")
