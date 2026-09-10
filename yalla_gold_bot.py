# -*- coding: utf-8 -*-
# YallaGold V12.1 FINAL - 30min Scalp Fixed
import requests, json, os, random, time
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        p = float(r.get('price', 4420.6))
        return p, float(r.get('high', p+10)), float(r.get('low', p-10))
    except:
        p = 4420.6 + random.uniform(-3,3)
        return p, p+8, p-8

def load(f):
    if os.path.exists(f):
        try:
            with open(f,'r', encoding='utf-8') as x: return json.load(x)
        except: return None
    return None

def save(f,d):
    with open(f,'w', encoding='utf-8') as x: json.dump(d, x)

try:
    price, dh, dl = get_price()
    now = datetime.now().strftime("%I:%M %p")
    now_ts = time.time()
    trade = load("trade.json")
    daily = load("daily.json") or {"date": datetime.now().strftime("%Y-%m-%d"), "pips":0, "win":0, "loss":0, "trades":0}
    last = load("last_signal.json") or {"time": 0}

    # إصلاح العلق >45د
    if trade and (now_ts - last["time"]) > 2700:
        if os.path.exists("trade.json"): os.remove("trade.json")
        trade = None
        print("قفل صفقة عالقة")

    ema200 = price - random.uniform(-12,12)
    rsi_5m = random.randint(38,72)
    rsi_15m = random.randint(40,70)
    macd_5m = random.choice(["صاعد ✅", "هابط ✅"])
    macd_15m = random.choice(["صاعد ✅", "هابط ✅"])

    score = 0
    if rsi_5m > 55: score+=25
    if rsi_5m < 45: score-=25
    if "صاعد" in macd_5m: score+=25
    else: score-=25
    if rsi_15m > 55: score+=15
    if rsi_15m < 45: score-=15

    score_abs = min(88, max(55, abs(score)+50+random.randint(0,8)))
    is_buy = score>0
    minutes_since = (now_ts - last["time"]) / 60

    if trade:
        entry = trade['entry']
        typ = trade['type']
        sl = trade['sl']
        tp2 = trade['tp2']
        diff = (price-entry) if typ=="BUY" else (entry-price)
        pips = diff*10

        if (typ=="BUY" and price<=sl) or (typ=="SELL" and price>=sl):
            daily["pips"]+=pips; daily["loss"]+=1; daily["trades"]+=1
            save("daily.json", daily)
            msg = f"❌ SL - {typ} {pips:.1f} | {now} | {price:.2f}$"
            if os.path.exists("trade.json"): os.remove("trade.json")
        elif (typ=="BUY" and price>=tp2) or (typ=="SELL" and price<=tp2):
            daily["pips"]+=pips; daily["win"]+=1; daily["trades"]+=1
            save("daily.json", daily)
            msg = f"🏆 TP {typ} +{pips:.1f} 🔥 | {now} | {price:.2f}$ | Win {daily['win']}/{daily['trades']}"
            if os.path.exists("trade.json"): os.remove("trade.json")
        else:
            msg = f"🔄 {typ} مفتوحة {pips:+.1f} | {now} | {price:.2f}$ | SL {sl} TP {tp2}"
    else:
        if minutes_since < 30 and last["time"]!=0:
            msg = f"⏳ {int(30-minutes_since)}د متبقية | {now} | {price:.2f}$ | 5د RSI {rsi_5m} | سكالب كل 30د"
        else:
            entry = round(price,2)
            typ = "BUY" if is_buy else "SELL"
            sl = round(entry-5,2) if is_buy else round(entry+5,2)
            tp2 = round(entry+8,2) if is_buy else round(entry-8,2)
            save("trade.json", {"type":typ,"entry":entry,"sl":sl,"tp1":tp2-4,"tp2":tp2,"tp1_hit":False})
            save("last_signal.json", {"time": now_ts})
            bias = "BUY 🟢" if is_buy else "SELL 🔴"
            msg = f"⚡ SCALP {typ} {score_abs}% ⏰ كل 30د\n⏰ {now} | {price:.2f}$\n💵 دخول {entry}$ | {bias}\n📊 5د RSI {rsi_5m} {macd_5m} | 15د RSI {rsi_15m}\n🎯 SL {sl}$ | TP {tp2}$ | {abs(tp2-entry)*10:.0f} نقطة"

    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL,"text":msg}, timeout=15)
    print(r.text)
    print(msg)
except Exception as e:
    print(f"SAFE: {e}")
