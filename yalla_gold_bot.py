import requests, json, os, random, time
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

# امسح العالق
for f in ["trade.json","last_signal.json","daily.json"]:
    if os.path.exists(f):
        try: os.remove(f)
        except: pass

try:
    r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
    price = float(r.get('price', 4420.6))
except:
    price = 4420.6

now = datetime.now().strftime("%I:%M %p")
typ = random.choice(["BUY","SELL"])
entry = round(price,2)
sl = round(entry-5,2) if typ=="BUY" else round(entry+5,2)
tp = round(entry+8,2) if typ=="BUY" else round(entry-8,2)

msg = f"""⚡ SCALP SIGNAL - {typ} {random.randint(55,78)}% ⏰ 30د FIX
⏰ {now} | XAUUSD
💵 دخول {entry}$ | SL {sl}$ | TP {tp}$
✅ هذا تاست مضمون - إذا وصلك معناها البوت رجع!"""

# حفظ باش ما يعلقش
with open("trade.json","w") as x: json.dump({"type":typ,"entry":entry,"sl":sl,"tp1":tp-2,"tp2":tp,"tp1_hit":False}, x)
with open("last_signal.json","w") as x: json.dump({"time": time.time()}, x)

resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL,"text":msg}, timeout=15)
print(resp.text)
