# V18 - OB حقيقي + Gold Price API + حماية API
import requests, json, os, time
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def get_gold_price():
    # 1- يحاول يجيب سعر الذهب الحقيقي XAU
    try:
        r=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
        return float(r['price']) # سعر حقيقي 4412$
    except:
        try:
            # 2- fallback PAXG من Binance
            url="https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
            return float(requests.get(url,timeout=10).json()['price'])
        except:
            return None

def get_candles(interval, limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}"
        return [{"o":float(c[1]),"h":float(c[2]),"l":float(c[3]),"c":float(c[4]),"v":float(c[5])} for c in requests.get(url,timeout=10).json()]
    except: return None

def rsi(candles, p=14):
    closes=[c['c'] for c in candles]; g,l=[],[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]; g.append(max(d,0)); l.append(max(-d,0))
    if len(g)<p: return 50
    ag=sum(g[-p:])/p; al=sum(l[-p:])/p
    if al==0: return 100
    return 100-(100/(1+ag/al))

def ema(candles, period):
    closes=[c['c'] for c in candles]; k=2/(period+1); e=closes[0]
    for c in closes[1:]: e=c*k+e*(1-k)
    return e

def atr(candles, p=14):
    trs=[]
    for i in range(1,len(candles)):
        trs.append(max(candles[i]['h']-candles[i]['l'], abs(candles[i]['h']-candles[i-1]['c']), abs(candles[i]['l']-candles[i-1]['c'])))
    return sum(trs[-p:])/p if len(trs)>=p else 5

# ✅ تصليح 3: OB حقيقي مثل صورتك
def detect_ob_real(candles):
    ob_bull=None; ob_bear=None; ob_bull_price=0; ob_bear_price=0
    # يدور على آخر 15 شمعة
    for i in range(len(candles)-15, len(candles)-3):
        # OB صاعد: شمعة حمراء قبل صعود قوي (مثل صورتك 4438$)
        if candles[i]['c'] < candles[i]['o']: # حمراء
            # بعدها شمعتين خضر قوية
            if candles[i+1]['c'] > candles[i+1]['o'] and candles[i+2]['c'] > candles[i+1]['h']:
                body = candles[i+1]['c']-candles[i+1]['o']
                rng = candles[i+1]['h']-candles[i+1]['l']
                if rng>0 and body/rng > 0.6: # جسم قوي 60%+
                    ob_bull=True; ob_bull_price=candles[i]['l']
        # OB هابط
        if candles[i]['c'] > candles[i]['o']: # خضراء
            if candles[i+1]['c'] < candles[i+1]['o'] and candles[i+2]['c'] < candles[i+1]['l']:
                body = candles[i+1]['o']-candles[i+1]['c']
                rng = candles[i+1]['h']-candles[i+1]['l']
                if rng>0 and body/rng > 0.6:
                    ob_bear=True; ob_bear_price=candles[i]['h']
    return ob_bull, ob_bull_price, ob_bear, ob_bear_price

def load(f):
    if os.path.exists(f):
        try:
            with open(f,'r',encoding='utf-8') as x: return json.load(x)
        except: return None
    return None
def save(f,d):
    with open(f,'w',encoding='utf-8') as x: json.dump(d,x)

def send_tg(text):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL,"text":text}, timeout=15)
    except: pass

try:
    gold_price=get_gold_price()
    c5=get_candles("5m",100); c15=get_candles("15m",100); c1h=get_candles("1h",100); c4h=get_candles("4h",100)

    # ✅ تصليح 5: إذا API طاح يخبرك
    if not gold_price or not c5:
        send_tg(f"⚠️ خطأ API - Gold Price أو Binance ما يرد | {datetime.now().strftime('%I:%M %p')}\nسأحاول بعد 5د")
        raise Exception("API fail")

    price=gold_price # الآن سعر حقيقي من Gold API
    now=datetime.now()
    trade=load("trade.json")
    last_weak=load("last_weak.json") or {"time":0}

    rsi5=rsi(c5,14); ema200_4h=ema(c4h,200); ema50_1h=ema(c1h,50); atr5=atr(c5,14)
    fvg_bull = c5[-2]['l'] > c5[-4]['h']; fvg_bear = c5[-2]['h'] < c5[-4]['l']
    last_h=max([c['h'] for c in c5[-11:-1]]); last_l=min([c['l'] for c in c5[-11:-1]])
    mss_bull=price>last_h; mss_bear=price<last_l
    liq_bull=c5[-1]['l']<last_l and c5[-1]['c']>last_l; liq_bear=c5[-1]['h']>last_h and c5[-1]['c']<last_h
    ob_bull, ob_bull_p, ob_bear, ob_bear_p = detect_ob_real(c5)

    buy_score=0; sell_score=0
    if price>ema200_4h: buy_score+=1
    if price<ema200_4h: sell_score+=1
    if rsi5<38: buy_score+=1
    if rsi5>62: sell_score+=1
    if fvg_bull: buy_score+=1
    if fvg_bear: sell_score+=1
    if mss_bull: buy_score+=1
    if mss_bear: sell_score+=1
    if liq_bull: buy_score+=1
    if liq_bear: sell_score+=1
    if ob_bull: buy_score+=1
    if ob_bear: sell_score+=1

    if trade:
        entry,typ,sl,tp=trade['entry'],trade['type'],trade['sl'],trade['tp2']
        diff=(price-entry) if typ=="BUY" else (entry-price)
        pips=diff*10
        if (typ=="BUY" and price<=sl) or (typ=="SELL" and price>=sl):
            msg=f"❌ SL {typ} {pips:.1f} | {now.strftime('%I:%M %p')} | Gold {price:.1f}$"; os.remove("trade.json")
        elif (typ=="BUY" and price>=tp) or (typ=="SELL" and price<=tp):
            msg=f"🏆 TP {typ} +{pips:.1f} 🔥 | {now.strftime('%I:%M %p')} | Gold {price:.1f}$"; os.remove("trade.json")
        else:
            msg=f"🔄 {typ} {pips:+.1f} | {now.strftime('%I:%M %p')} | Gold {price:.1f}$ | OB {ob_bull_p if typ=='BUY' else ob_bear_p}"
    else:
        if buy_score>=4:
            sl=round(price - atr5*1.2,2); tp=round(price + atr5*2.5,2); entry=round(price,2)
            save("trade.json",{"type":"BUY","entry":entry,"sl":sl,"tp2":tp}); save("last_weak.json",{"time":time.time()})
            msg=f"""💎 Gold Price BUY قوي 88% | {price:.1f}$ حقيقي
⏰ {now.strftime('%I:%M %p')} | XAU Gold API
📊 RSI {rsi5:.0f} | Buy {buy_score}/6 | OB حقيقي {'نعم '+str(ob_bull_p)+'$' if ob_bull else 'لا'}
🎯 دخول {entry}$ | SL {sl}$ | TP {tp}$"""
        elif sell_score>=4:
            sl=round(price + atr5*1.2,2); tp=round(price - atr5*2.5,2); entry=round(price,2)
            save("trade.json",{"type":"SELL","entry":entry,"sl":sl,"tp2":tp}); save("last_weak.json",{"time":time.time()})
            msg=f"""💎 Gold Price SELL قوي 88% | {price:.1f}$ حقيقي
⏰ {now.strftime('%I:%M %p')} | XAU Gold API | OB {ob_bear_p}$"""
        else:
            if time.time() - last_weak["time"] < 900:
                print("SKIP weak"); exit()
            save("last_weak.json",{"time":time.time()})
            msg=f"""⏳ تحليلي Gold {price:.1f}$ | {now.strftime('%I:%M %p')}
RSI {rsi5:.0f} | Buy {buy_score}/6 Sell {sell_score}/6
OB {'صاعد '+str(ob_bull_p)+'$' if ob_bull else 'هابط '+str(ob_bear_p)+'$' if ob_bear else 'لا يوجد'} | FVG {'نعم' if fvg_bull or fvg_bear else 'لا'}
🧠 قراري: أنتظر OB حقيقي"""

    send_tg(msg); print(msg)

except Exception as e:
    # ✅ إذا أي خطأ يرسل لك
    err_msg=f"⚠️ خطأ V18: {str(e)[:100]} | {datetime.now().strftime('%I:%M %p')}"
    print(err_msg)
    try: send_tg(err_msg)
    except: pass
