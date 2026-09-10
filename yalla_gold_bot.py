# V21 Golden Fusion Pro V6 - تداول حقيقي
import requests, json, os, time, sys
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def send_tg(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL,"text":text}, timeout=15)
    except: pass

def get_tv_price():
    try:
        url = "https://scanner.tradingview.com/forex/scan"
        payload = {"symbols":{"tickers":["OANDA:XAUUSD"],"query":{"types":[]}},"columns":["close"]}
        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers, timeout=10).json()
        return float(r['data'][0]['d'][0])
    except: return None

def get_tv_candles(interval_tv, limit=100):
    try:
        resolution = {"5m":"5","15m":"15","1h":"60","4h":"240"}.get(interval_tv, "5")
        to_ts = int(time.time())
        mins = {"5m":5,"15m":15,"1h":60,"4h":240}[interval_tv]
        from_ts = to_ts - (limit * mins * 60) - 3600
        url = f"https://api.tradingview.com/tv/udf/1/history?symbol=OANDA:XAUUSD&resolution={resolution}&from={from_ts}&to={to_ts}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        if r.get('s') == 'ok' and 'c' in r:
            return [{"o": float(r['o'][i]),"h": float(r['h'][i]),"l": float(r['l'][i]),"c": float(r['c'][i]),"v": 100} for i in range(len(r['c']))][-limit:]
    except: pass
    return None

def get_binance_candles(interval, limit=100):
    for base in ["https://api.binance.com", "https://data-api.binance.vision"]:
        try:
            data = requests.get(f"{base}/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}", timeout=10).json()
            if isinstance(data, list) and len(data) > 10:
                return [{"o":float(c[1]),"h":float(c[2]),"l":float(c[3]),"c":float(c[4]),"v":float(c[5])} for c in data]
        except: continue
    return None

def get_candles(interval, limit=100):
    c = get_tv_candles(interval, limit)
    if c: return c
    return get_binance_candles(interval, limit)

def ema_series(closes, period):
    k = 2/(period+1)
    ema = [closes[0]]
    for c in closes[1:]:
        ema.append(c*k + ema[-1]*(1-k))
    return ema

def ema_last(candles, period):
    closes=[c['c'] for c in candles]
    return ema_series(closes, period)[-1]

def rsi_last(candles, p=14):
    closes=[c['c'] for c in candles]
    if len(closes) < p+1: return 50
    gains=[]; losses=[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]
        gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains[-p:])/p; al=sum(losses[-p:])/p
    if al==0: return 100
    rs=ag/al
    return 100-(100/(1+rs))

def macd_last(candles):
    closes=[c['c'] for c in candles]
    if len(closes) < 35: return 0,0,False,False
    ema12 = ema_series(closes,12)
    ema26 = ema_series(closes,26)
    macd_line = [a-b for a,b in zip(ema12, ema26)]
    signal_line = ema_series(macd_line, 9)
    last_macd = macd_line[-1]
    last_signal = signal_line[-1]
    bullish = last_macd > last_signal and last_macd > 0
    bearish = last_macd < last_signal and last_macd < 0
    return last_macd, last_signal, bullish, bearish

def atr_last(candles, p=14):
    trs=[]
    for i in range(1,len(candles)):
        trs.append(max(candles[i]['h']-candles[i]['l'], abs(candles[i]['h']-candles[i-1]['c']), abs(candles[i]['l']-candles[i-1]['c'])))
    return sum(trs[-p:])/p if len(trs)>=p else 5

def load(f):
    if os.path.exists(f):
        try:
            with open(f,'r',encoding='utf-8') as x:
                data=json.load(x)
                if isinstance(data, dict) and "entry" not in data:
                    return None
                return data
        except: return None
    return None
def save(f,d):
    with open(f,'w',encoding='utf-8') as x: json.dump(d,x)

try:
    c5=get_candles("5m",100); c15=get_candles("15m",100); c1h=get_candles("1h",100); c4h=get_candles("4h",100)
    if not c5 or not c15 or not c1h or not c4h:
        sys.exit(0)

    price = get_tv_price() or c5[-1]['c']
    now = datetime.now()
    trade = load("trade.json")

    ema200_4h = ema_last(c4h,200)
    rsi_1h = rsi_last(c1h,14)
    rsi_5m = rsi_last(c5,14)
    macd_line, signal_line, macd_bull, macd_bear = macd_last(c1h)
    atr5 = atr_last(c5,14)

    last_20_15m = c15[-20:]
    resistance = max([c['h'] for c in last_20_15m])
    support = min([c['l'] for c in last_20_15m])

    last_24_1h = c1h[-24:] if len(c1h)>=24 else c1h
    daily_high = max([c['h'] for c in last_24_1h])
    daily_low = min([c['l'] for c in last_24_1h])
    daily_range = daily_high - daily_low

    above_ema = price > ema200_4h
    ema_text = f"EMA200 {ema200_4h:.1f} | فوق EMA200" if above_ema else f"EMA200 {ema200_4h:.1f} | تحت EMA200"
    macd_status = "صاعد" if macd_bull else "هابط" if macd_bear else "متعادل"

    last_candle_5m = c5[-1]
    prev_candle_5m = c5[-2]
    body_5m = abs(last_candle_5m['c'] - last_candle_5m['o'])
    range_5m = last_candle_5m['h'] - last_candle_5m['l']
    if range_5m > 0 and body_5m/range_5m > 0.6:
        if last_candle_5m['c'] < prev_candle_5m['l']:
            explosion = "انفجار سفلي"
        elif last_candle_5m['c'] > prev_candle_5m['h']:
            explosion = "انفجار علوي"
        else:
            explosion = "تجميع"
    else:
        explosion = "تجميع"

    buy_score=0; sell_score=0
    if above_ema: buy_score+=1
    else: sell_score+=1
    if rsi_1h < 35: buy_score+=1
    elif rsi_1h > 65: sell_score+=1
    if macd_bull: buy_score+=1
    elif macd_bear: sell_score+=1
    if price <= support + atr5*0.3: buy_score+=1
    if price >= resistance - atr5*0.3: sell_score+=1
    if explosion == "انفجار سفلي": sell_score+=1
    elif explosion == "انفجار علوي": buy_score+=1
    if rsi_5m < 30: buy_score+=1
    elif rsi_5m > 70: sell_score+=1

    total = 6
    if buy_score > sell_score:
        bias = "BUY"; bias_pct = int(buy_score/total*100)
        if bias_pct < 50: bias_pct = 50 + buy_score*3
    elif sell_score > buy_score:
        bias = "SELL"; bias_pct = int(sell_score/total*100)
        if bias_pct < 50: bias_pct = 50 + sell_score*3
    else:
        bias = "SELL" if rsi_1h > 50 else "BUY"; bias_pct = 50

    if bias_pct > 75: bias_pct = 75
    if bias_pct < 50: bias_pct = 50

    status = "انتظار" if bias_pct < 63 else "تداول"
    status_emoji = "⛔" if status=="انتظار" else "✅"

    if bias_pct >= 63:
        decision = f"BUY {bias_pct}% - دخول" if bias=="BUY" else f"SELL {bias_pct}% - دخول"
        expert = "السوق في اتجاه صاعد - ادخل مع ادارة راس مال 1%" if bias=="BUY" and rsi_1h < 70 else "السوق في اتجاه هابط - ادخل مع وقف خسارة" if bias=="SELL" and rsi_1h > 30 else "انتظر تاكيد"
    else:
        decision = f"SELL {bias_pct}% - انتظر كسر ${support:.1f}" if bias=="SELL" else f"BUY {bias_pct}% - انتظر اختراق ${resistance:.1f}"
        if 40 <= rsi_1h <= 60 and explosion == "تجميع":
            expert = "لا تدخل الان - السوق في تجميع"
        elif rsi_1h < 35:
            expert = "تشبع بيعي - انتظر شمعة انعكاس صاعدة"
        elif rsi_1h > 65:
            expert = "تشبع شرائي - انتظر شمعة انعكاس هابطة"
        else:
            expert = "انتظر كسر واضح مع فوليوم"

    if trade and "entry" in trade:
        entry,typ,sl,tp=trade['entry'],trade['type'],trade['sl'],trade['tp2']
        diff=(price-entry) if typ=="BUY" else (entry-price)
        pips=diff*10
        if (typ=="BUY" and price<=sl) or (typ=="SELL" and price>=sl):
            msg=f"❌ SL {typ} {pips:.1f} | {now.strftime('%I:%M %p')} | TV {price:.1f}$\nتحذير: ادارة راس مال 1% فقط"
            try: os.remove("trade.json")
            except: pass
        elif (typ=="BUY" and price>=tp) or (typ=="SELL" and price<=tp):
            msg=f"🏆 TP {typ} +{pips:.1f} | {now.strftime('%I:%M %p')} | TV {price:.1f}$"
            try: os.remove("trade.json")
            except: pass
        else:
            msg=f"🔄 {typ} {pips:+.1f} | {now.strftime('%I:%M %p')} | TV {price:.1f}$ | SL {sl}$ TP {tp}$"
    else:
        if bias_pct >= 63:
            if bias == "BUY":
                sl = round(price - atr5*1.2,2); tp = round(price + atr5*2.2,2); entry = round(price,2)
                save("trade.json",{"type":"BUY","entry":entry,"sl":sl,"tp2":tp})
                msg = f"SCALP BUY {bias_pct}% كل 30د\n{now.strftime('%I:%M %p')} | {price:.1f}$\nدخول BUY | ${entry}\nRSI {rsi_1h:.0f} د1H | RSI {rsi_5m:.0f} د5 {macd_status}\nSL {sl}$ | TP {tp}$\nتحذير: تداول حقيقي - مخاطرة 1% فقط | ليس نصيحة مالية"
            else:
                sl = round(price + atr5*1.2,2); tp = round(price - atr5*2.2,2); entry = round(price,2)
                save("trade.json",{"type":"SELL","entry":entry,"sl":sl,"tp2":tp})
                msg = f"SCALP SELL {bias_pct}% كل 30د\n{now.strftime('%I:%M %p')} | {price:.1f}$\nدخول SELL | ${entry}\nRSI {rsi_1h:.0f} د1H | RSI {rsi_5m:.0f} د5 {macd_status}\nSL {sl}$ | TP {tp}$\nتحذير: تداول حقيقي - مخاطرة 1% فقط | ليس نصيحة مالية"
        else:
            msg = f"XAUUSD | {now.strftime('%I:%M %p')} | Golden Fusion Pro V6\n━━━━━━━━━━━━━━━\nالسعر: ${price:.2f} (TradingView)\nBias: {bias} {bias_pct}% | الحالة: {status} {status_emoji}\nتحليل 4 فريمات احترافي:\n- 4H: {ema_text}\n- 1H: RSI {rsi_1h:.0f} | MACD {macd_status}\n- 15m: R {resistance:.1f}$ | S {support:.1f}$\n- 5m: {explosion} | RSI {rsi_5m:.0f}\nمستويات اليوم:\n- مقاومة: ${resistance:.1f} (قوية)\n- دعم: ${support:.1f} (قوية)\n- هاي: ${daily_high:.1f} | لو: ${daily_low:.1f}\n- المدى: ${daily_range:.1f}\nالقرار: {decision}\nنصيحة الخبير: {expert}\nتنبيه: تداول حقيقي - ادارة راس مال 1-2% | ليس نصيحة مالية"

    send_tg(msg)
    sys.exit(0)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(0)
