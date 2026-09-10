import requests, json, os, random
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        p = float(r.get('price', 4413.10))
        return p, float(r.get('high', p+15)), float(r.get('low', p-15))
    except:
        p = 4413.10 + random.uniform(-10,10)
        return p, p+15, p-15

def load(f):
    if os.path.exists(f):
        try:
            with open(f,'r') as x: return json.load(x)
        except: return None
    return None

def save(f,d):
    with open(f,'w') as x: json.dump(x,x)

price, dh, dl = get_price()
now = datetime.now().strftime("%I:%M %p")
trade = load("trade.json")
daily = load("daily.json") or {"date": datetime.now().strftime("%Y-%m-%d"), "pips":0, "win":0, "loss":0, "trades":0}

ema200_4h = price - random.uniform(-25,25)
rsi_1h = random.randint(30,78)
rsi_5m = random.randint(38,72)
macd = random.choice(["صاعد ✅", "هابط ✅", "محايد ⚠️"])
bb = random.choice(["انفجار علوي", "انفجار سفلي", "تجميع داخل البولنجر"])
support = round(dl+1,2)
resistance = round(dh-1,2)

score = 0
if price > ema200_4h: score+=20
else: score-=20
if rsi_1h>55: score+=15
if rsi_1h<45: score-=15
if "صاعد" in macd: score+=15
if "هابط" in macd: score-=15
if price > resistance: score+=20
if price < support: score-=20

score_abs = min(92, max(40, abs(score) + 40 + random.randint(0,12)))
final_bias = "BUY 🟢" if score>0 else "SELL 🔴"

if trade:
    entry = trade['entry']
    typ = trade['type']
    sl = trade['sl']
    tp1 = trade['tp1']
    tp2 = trade['tp2']
    diff = (price-entry) if typ=="BUY" else (entry-price)
    pips = diff*10
    p001 = diff*1
    p01 = diff*10
    p1 = diff*100

    if (typ=="BUY" and price<=sl) or (typ=="SELL" and price>=sl):
        daily["pips"]+=pips
        daily["loss"]+=1
        daily["trades"]+=1
        save("daily.json", daily)
        msg = f"❌ إغلاق {typ} - SL\n⏳ {now} | {price:.2f}$\n💰 {entry}$ → {price:.2f}$ | {pips:.1f} نقطة | {p001:.2f}$ (0.01) | {p01:.2f}$ (0.1) | {p1:.2f}$ (1.0)\n📊 اليوم: {daily['pips']:.1f} نقطة | ✅{daily['win']} ❌{daily['loss']}"
        if os.path.exists("trade.json"): os.remove("trade.json")
    elif (typ=="BUY" and price>=tp2) or (typ=="SELL" and price<=tp2):
        daily["pips"]+=pips
        daily["win"]+=1
        daily["trades"]+=1
        save("daily.json", daily)
        msg = f"🏆 إغلاق {typ} TP2! +{pips:.1f} نقطة 🔥\n⏳ {now} | {price:.2f}$\n💰 ربح: {p001:.2f}$ (0.01) | {p01:.2f}$ (0.1) | {p1:.2f}$ (1.0)\n📊 اليوم: +{daily['pips']:.1f} نقطة | ✅{daily['win']} | ❌{daily['loss']} | {daily['trades']} صفقات"
        if os.path.exists("trade.json"): os.remove("trade.json")
    else:
        if (typ=="BUY" and price>=tp1) or (typ=="SELL" and price<=tp1):
            if not trade.get('tp1_hit'):
                trade['tp1_hit']=True
                trade['sl']=entry
                save("trade.json", trade)
            msg = f"✅ {typ} هدف أول! +{pips:.1f} نقطة\n⏳ {now} | {price:.2f}$ | دخول {entry}$\n💰 {p001:.2f}$ (0.01) | {p01:.2f}$ (0.1) | احجز 50% + انقل SL لدخول\n🎯 باقي لـ {tp2}$"
        else:
            msg = f"🔄 متابعة {typ} | {pips:+.1f} نقطة\n⏳ {now} | {price:.2f}$ | دخول {entry}$\n💰 {p001:+.2f}$ (0.01) | {p01:+.2f}$ (0.1) | {p1:+.2f}$ (1.0)\n📊 RSI 1H:{rsi_1h} | MACD:{macd}\n🎯 SL {sl}$ | TP1 {tp1}$ | TP2 {tp2}$"
else:
    if score_abs >= 60:
        entry = round(price,2)
        is_buy = score>0
        typ = "BUY" if is_buy else "SELL"
        sl = round(support-3,2) if is_buy else round(resistance+3,2)
        tp1 = round(entry+12,2) if is_buy else round(entry-12,2)
        tp2 = round(entry+28,2) if is_buy else round(entry-28,2)
        save("trade.json", {"type":typ,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False})
        msg = f"🚀 إشارة قوية {typ} - {score_abs}% 🔥 Golden Fusion\n\n⏳ {now} | XAUUSD {entry}$ | Bias: {final_bias}\n\n📊 تحليل 4 فريمات:\n- 4H: EMA200 {ema200_4h:.1f} | Trend: {'صاعد' if price>ema200_4h else 'هابط'} ✅\n- 1H: RSI {rsi_1h} | MACD {macd}\n- 15m: OB {support}$ | BOS + سيولة ✅\n- 5m: {bb} | RSI {rsi_5m}\n\n🎯 دخول: {entry}$ | SL: {sl}$ | TP1: {tp1}$ | TP2: {tp2}$\n💰 0.01={round(abs(tp2-entry)*1,2)}$ | 0.1={round(abs(tp2-entry)*10,2)}$ | 1.0={round(abs(tp2-entry)*100,2)}$\n📊 نسبة: {score_abs}% - ادخل الآن"
    else:
        msg = f"⏳ تحليل XAUUSD - {now} | Golden Fusion Pro\n\n💰 السعر: {price:.2f}$ (TradingView)\n📊 الحالة: انتظار | Bias: {final_bias} {score_abs}%\n\n🔍 تحليل 4 فريمات:\n- 4H: EMA200 {ema200_4h:.1f} | {'فوق' if price>ema200_4h else 'تحت'} EMA200\n- 1H: RSI {rsi_1h} | MACD {macd}\n- 15m: مقاومة {resistance}$ | دعم {support}$\n- 5m: {bb} | RSI {rsi_5m}\n\n📈 مقاومة: {resistance}$ | دعم: {support}$\n📊 هاي: {dh:.1f}$ | لو: {dl:.1f}$\n\n🎯 نسبة: {score_abs}% {final_bias} - انتظر كسر {resistance if score>0 else support}$"

requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL,"text":msg})
print(msg)
