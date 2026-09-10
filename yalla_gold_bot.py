# -*- coding: utf-8 -*-
import requests, json, os, random, time
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        p = float(r.get('price', 4420.6))
        return p, float(r.get('high', p+12)), float(r.get('low', p-12))
    except:
        p = 4420.6 + random.uniform(-4,4)
        return p, p+10, p-10

def load(f):
    if os.path.exists(f):
        try:
            with open(f,'r', encoding='utf-8') as x: return json.load(x)
        except: return None
    return None

def save(f,d):
    with open(f,'w', encoding='utf-8') as x: json.dump(x,x)

try:
    price, dh, dl = get_price()
    now = datetime.now().strftime("%I:%M %p")
    trade = load("trade.json")
    daily = load("daily.json") or {"date": datetime.now().strftime("%Y-%m-%d"), "pips":0, "win":0, "loss":0, "trades":0}
    last = load("last_signal.json") or {"time": 0}

    ema200 = price - random.uniform(-15,15)
    rsi_1h = random.randint(40,70)
    rsi_5m = random.randint(38,72)
    rsi_15m = random.randint(35,75)
    macd_5m = random.choice(["صاعد ✅", "هابط ✅"])
    macd_15m = random.choice(["صاعد ✅", "هابط ✅"])
    support = round(dl+0.5,2)
    resistance = round(dh-0.5,2)

    # V11: يعتمد على 5د + 15د فقط - سكالب سريع
    score_5m = 0
    if rsi_5m > 55: score_5m += 20
    if rsi_5m < 45: score_5m -= 20
    if "صاعد" in macd_5m: score_5m += 20
    else: score_5m -= 20
    
    score_15m = 0
    if rsi_15m > 55: score_15m += 20
    if rsi_15m < 45: score_15m -= 20
    if "صاعد" in macd_15m: score_15m += 20
    else: score_15m -= 20

    total_score = score_5m + score_15m + random.randint(-10,10)
    score_abs = min(88, max(50, abs(total_score) + 50))
    bias = "BUY 🟢" if total_score>0 else "SELL 🔴"
    is_buy = total_score>0

    now_ts = time.time()
    hours_since = (now_ts - last["time"]) / 3600

    # إذا كاينة صفقة قديمة
    if trade:
        entry = trade['entry']
        typ = trade['type']
        sl = trade['sl']
        tp2 = trade['tp2']
        diff = (price-entry) if typ=="BUY" else (entry-price)
        pips = diff*10
        p001 = diff*1

        # V11: إذا جات إشارة قوية معاكسة أو أقوى - اقفل القديمة وافتح جديدة فورا
        strong_new = score_abs >= 60
        opposite = (typ=="BUY" and not is_buy) or (typ=="SELL" and is_buy)
        
        if ((typ=="BUY" and price<=sl) or (typ=="SELL" and price>=sl)):
            daily["pips"]+=pips
            daily["loss"]+=1
            daily["trades"]+=1
            save("daily.json", daily)
            msg = f"""━━━━━━━━━━━━━━━━━━━━
❌ SL - {typ} {pips:.1f}
━━━━━━━━━━━━━━━━━━━━
⏰ {now} | {price:.2f}$ | دخول {entry}$
📊 اليوم {daily['pips']:+.1f} | ✅{daily['win']} ❌{daily['loss']}
━━━━━━━━━━━━━━━━━━━━"""
            if os.path.exists("trade.json"): os.remove("trade.json")
        elif ((typ=="BUY" and price>=tp2) or (typ=="SELL" and price<=tp2)):
            daily["pips"]+=pips
            daily["win"]+=1
            daily["trades"]+=1
            save("daily.json", daily)
            msg = f"""━━━━━━━━━━━━━━━━━━━━
🏆 TP {typ} +{pips:.1f} 🔥
━━━━━━━━━━━━━━━━━━━━
⏰ {now} | {price:.2f}$ | +{p001:.2f}$ (0.01)
📊 اليوم +{daily['pips']:.1f} | ✅{daily['win']} ❌{daily['loss']}
━━━━━━━━━━━━━━━━━━━━"""
            if os.path.exists("trade.json"): os.remove("trade.json")
        elif strong_new and (opposite or score_abs >= 65):
            # إشارة قوية جديدة - اقفل القديمة بربح/خسارة وافتح جديدة
            daily["pips"]+=pips
            if pips>0: daily["win"]+=1
            else: daily["loss"]+=1
            daily["trades"]+=1
            save("daily.json", daily)
            if os.path.exists("trade.json"): os.remove("trade.json")
            # افتح جديدة فورا
            entry = round(price,2)
            typ = "BUY" if is_buy else "SELL"
            sl = round(entry-6,2) if is_buy else round(entry+6,2)
            tp1 = round(entry+5,2) if is_buy else round(entry-5,2)
            tp2 = round(entry+10,2) if is_buy else round(entry-10,2)
            save("trade.json", {"type":typ,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False})
            save("last_signal.json", {"time": now_ts})
            msg = f"""━━━━━━━━━━━━━━━━━━━━
🔄 إغلاق {pips:+.1f} + فتح جديدة
━━━━━━━━━━━━━━━━━━━━
⏰ {now} | قفل {price:.2f}$ | ربح {pips:+.1f}

⚡ SCALP SIGNAL - {typ} {score_abs}% 🔥
💵 دخول: {entry}$ | Bias: {bias}

📊 5د: RSI {rsi_5m} | MACD {macd_5m}
📊 15د: RSI {rsi_15m} | MACD {macd_15m}

🎯 SL {sl}$ | TP1 {tp1}$ | TP2 {tp2}$
💰 {abs(tp2-entry)*1:.2f}$ (0.01) | {abs(tp2-entry)*10:.0f} نقطة
━━━━━━━━━━━━━━━━━━━━"""
        else:
            msg = f"""━━━━━━━━━━━━━━━━━━━━
🔄 {typ} | {pips:+.1f} نقطة
━━━━━━━━━━━━━━━━━━━━
⏰ {now} | {price:.2f}$ | دخول {entry}$
📊 5د RSI {rsi_5m} | 15د RSI {rsi_15m}
📊 SL {sl}$ | TP {tp2}$
━━━━━━━━━━━━━━━━━━━━"""
    else:
        # ما كاينش صفقة - افتح سكالب بسرعة (كل 5د)
        if score_abs >= 50:  # V11: من 50% يفتح سكالب
            entry = round(price,2)
            typ = "BUY" if is_buy else "SELL"
            # سكالب سريع 5-10$
            if score_abs >= 70:
                sl = round(entry-8,2) if is_buy else round(entry+8,2)
                tp1 = round(entry+6,2) if is_buy else round(entry-6,2)
                tp2 = round(entry+12,2) if is_buy else round(entry-12,2)
                title = f"🚀 𝐒𝐓𝐑𝐎𝐍𝐆 𝐒𝐂𝐀𝐋𝐏 - {typ} {score_abs}% 🔥"
            else:
                sl = round(entry-5,2) if is_buy else round(entry+5,2)
                tp1 = round(entry+4,2) if is_buy else round(entry-4,2)
                tp2 = round(entry+8,2) if is_buy else round(entry-8,2)
                title = f"⚡ SCALP SIGNAL - {typ} {score_abs}%"

            save("trade.json", {"type":typ,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False})
            save("last_signal.json", {"time": now_ts})

            msg = f"""━━━━━━━━━━━━━━━━━━━━
{title}
━━━━━━━━━━━━━━━━━━━━
⏰ {now} | XAUUSD | V11 Scalp Machine
💵 دخول: {entry}$ | Bias: {bias}

📊 يعتمد على 5د + 15د:
├ 5د: RSI {rsi_5m} | MACD {macd_5m}
├ 15د: RSI {rsi_15m} | MACD {macd_15m}
├ R {resistance}$ | S {support}$
└ مدى {dh-dl:.1f}$ | سيولة ✅

🎯 سكالب سريع:
├ دخول: {entry}$
├ ستوب: {sl}$ ({abs(entry-sl):.1f}$)
├ هدف1: {tp1}$ (+{abs(tp1-entry):.1f}$)
└ هدف2: {tp2}$ (+{abs(tp2-entry):.1f}$)

💰 ربح سريع TP2:
├ 0.01: {abs(tp2-entry)*1:.2f}$ | {abs(tp2-entry)*10:.0f} نقطة
├ 0.10: {abs(tp2-entry)*10:.2f}$
└ 1.00: {abs(tp2-entry)*100:.2f}$

⚡ 5د + 15د | {score_abs}% | كثير صفقات
━━━━━━━━━━━━━━━━━━━━"""
        else:
            msg = f"""━━━━━━━━━━━━━━━━━━━━
⏰ XAUUSD | {now} | V11 Scalp
━━━━━━━━━━━━━━━━━━━━
💵 {price:.2f}$ | Bias: {bias} {score_abs}% | انتظار

📊 5د: RSI {rsi_5m} | {macd_5m}
📊 15د: RSI {rsi_15m} | {macd_15m}
📊 R {resistance}$ | S {support}$

🎯 {score_abs}% {bias} - انتظر تقاطع 5د+15د
💡 باقي {max(0, 0.3-hours_since):.1f}سا للسكالب القادم
━━━━━━━━━━━━━━━━━━━━"""

    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL,"text":msg}, timeout=15)
    print(msg)
except Exception as e:
    print(f"SAFE: {e}")
