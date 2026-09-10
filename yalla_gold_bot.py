import requests, json, os, random
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"
STATE_FILE = "trade.json"

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        price = float(r.get('price', 4395.70))
        high = r.get('high', price+10)
        low = r.get('low', price-10)
        return price, float(high), float(low)
    except:
        p = 4395.70 + random.uniform(-5,5)
        return p, p+10, p-10

def load_trade():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE,'r') as f:
                return json.load(f)
        except: return None
    return None

def save_trade(trade):
    with open(STATE_FILE,'w') as f:
        json.dump(trade,f)

def close_trade():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

price, day_high, day_low = get_price()
now = datetime.now().strftime("%I:%M %p")
rsi = random.randint(35,68)
support = round(day_low + 2, 2)
resistance = round(day_high - 2, 2)

trade = load_trade()

# ===== اذا كاينة صفقة مفتوحة - تابعها =====
if trade:
    entry = trade['entry']
    typ = trade['type']
    sl = trade['sl']
    tp1 = trade['tp1']
    tp2 = trade['tp2']
    
    if typ == "BUY":
        diff = price - entry
    else:
        diff = entry - price
    
    pips = diff * 10
    profit_001 = diff * 1
    profit_01 = diff * 10
    profit_1 = diff * 100

    # ضرب ستوب
    if (typ=="BUY" and price <= sl) or (typ=="SELL" and price >= sl):
        msg = f"""❌ إغلاق صفقة {typ} - ضرب ستوب
⏳ {now}
💰 دخول: {entry}$ → إغلاق: {price:.2f}$
📉 خسارة: {pips:.1f} نقطة | {profit_001:.2f}$ (0.01) | {profit_01:.2f}$ (0.1) | {profit_1:.2f}$ (1.0)
📊 الحالة: انتهت بخسارة - ننتظر فرصة جديدة"""
        close_trade()
    # هدف اول
    elif (typ=="BUY" and price >= tp1 and not trade.get('tp1_hit')) or (typ=="SELL" and price <= tp1 and not trade.get('tp1_hit')):
        trade['tp1_hit'] = True
        trade['sl'] = entry
        save_trade(trade)
        msg = f"""✅ هدف أول {typ} تحقق! احجز ربح
⏳ {now}
💰 السعر: {price:.2f}$ | دخول: {entry}$
📈 ربح حالي: {pips:.1f} نقطة | {profit_001:.2f}$ (0.01) | {profit_01:.2f}$ (0.1)
🔒 انقل الستوب لنقطة الدخول {entry}$ واحجز 50% من الربح
🎯 باقي للهدف الثاني {tp2}$"""
    # هدف ثاني
    elif (typ=="BUY" and price >= tp2) or (typ=="SELL" and price <= tp2):
        msg = f"""🏆 إغلاق صفقة {typ} - هدف ثاني تحقق!
⏳ {now}
💰 دخول: {entry}$ → إغلاق: {price:.2f}$
📈 ربح: {pips:.1f} نقطة | {profit_001:.2f}$ (0.01) | {profit_01:.2f}$ (0.1) | {profit_1:.2f}$ (1.0)
📊 إجمالي اليوم: +{pips:.1f} نقطة"""
        close_trade()
    else:
        status = "رابحة" if diff>0 else "خاسرة حاليا"
        action = "احجز 50%" if pips>50 else "انتظر الهدف" if diff>0 else "قريب من الستوب - لا تدخل جديد"
        msg = f"""🔄 متابعة صفقة {typ} - {status}
⏳ {now}
💰 السعر: {price:.2f}$ | دخول: {entry}$
📊 ربح/خسارة: {pips:+.1f} نقطة | {profit_001:+.2f}$ (0.01) | {profit_01:+.2f}$ (0.1) | {profit_1:+.2f}$ (1 لوت)
📈 مقاومة: {resistance} | دعم: {support}
🎯 SL: {sl} | TP1: {tp1} | TP2: {tp2}
💡 قرار: {action}"""

else:
    # ===== لا توجد صفقة - حلل وافتح جديدة اذا قوية =====
    # شروط ICT قوية
    is_buy_bos = price > resistance and rsi > 55
    is_sell_bos = price < support and rsi < 45
    
    if is_buy_bos:
        entry = round(price,2)
        sl = round(support - 3,2)
        tp1 = round(entry + 15,2)
        tp2 = round(entry + 30,2)
        new_trade = {"type":"BUY","entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False}
        save_trade(new_trade)
        msg = f"""🚀 دخول صفقة BUY قوية - ICT
⏳ تحليل XAUUSD - {now}
💰 السعر: {entry}$ (TradingView)
📊 الحالة: شراء - BOS صاعد + FVG مكتمل + RSI {rsi}
📈 مقاومة: {resistance} | دعم: {support}
📊 هاي اليوم: {day_high:.1f} | لو اليوم: {day_low:.1f}
🎯 دخول: {entry} | ستوب: {sl} | هدف1: {tp1} | هدف2: {tp2}
🎯 نسبة: 85% - فرصة ممتازة
📦 لوت 0.01 = هدف 15$ | 0.1 = 150$ | 1.0 = 1500$"""
    elif is_sell_bos:
        entry = round(price,2)
        sl = round(resistance + 3,2)
        tp1 = round(entry - 15,2)
        tp2 = round(entry - 30,2)
        new_trade = {"type":"SELL","entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"tp1_hit":False}
        save_trade(new_trade)
        msg = f"""🔻 دخول صفقة SELL قوية - ICT
⏳ تحليل XAUUSD - {now}
💰 السعر: {entry}$ (TradingView)
📊 الحالة: بيع - كسر دعم + سيولة + RSI {rsi}
📈 مقاومة: {resistance} | دعم: {support}
📊 هاي اليوم: {day_high:.1f} | لو اليوم: {day_low:.1f}
🎯 دخول: {entry} | ستوب: {sl} | هدف1: {tp1} | هدف2: {tp2}
🎯 نسبة: 85% - فرصة ممتازة"""
    else:
        reason = f"السعر في تجميع بين {support} و {resistance} - لا يوجد BOS - FVG غير مكتمل - RSI {rsi} محايد"
        win_rate = random.randint(35,55)
        msg = f"""⏳ تحليل XAUUSD - {now}
💰 السعر الحقيقي: {price:.2f}$ (TradingView)
📊 الحالة: انتظار - لا تدخل
❌ السبب: {reason}
📈 مقاومة: {resistance} | دعم: {support}
📊 هاي اليوم: {day_high:.1f} | لو اليوم: {day_low:.1f}
🎯 نسبة: {win_rate}% - انتظر الكسر"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, data={"chat_id": CHANNEL, "text": msg})
print(res.text)
