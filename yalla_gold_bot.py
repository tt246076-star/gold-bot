# V19.4 FINAL - Exit 0 always - يرسل كل 5 دقايق
import requests, json, os, time, sys
from datetime import datetime

BOT_TOKEN = "8715298565:AAF-UKEgYjry5rifPIkJ6b5r2rRYRDYHwoM"
CHANNEL = "-1003997576330"

def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id":CHANNEL,"text":text}, timeout=15)
        print(f"TG {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"TG fail: {e}")

try:
    send_tg(f"✅ V19.4 START {datetime.now().strftime('%H:%M:%S')}")

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
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10).json()
            if r.get('s') == 'ok' and 'c' in r:
                candles = []
                for i in range(len(r['c'])):
                    candles.append({"o": float(r['o'][i]),"h": float(r['h'][i]),"l": float(r['l'][i]),"c": float(r['c'][i]),"v": 100})
                return candles[-limit:]
        except: pass
        return None

    def get_binance_candles(interval, limit=100):
        for base in ["https://api.binance.com", "https://data-api.binance.vision"]:
            try:
                url = f"{base}/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}"
                data = requests.get(url, timeout=10).json()
                if isinstance(data, list) and len(data) > 10:
                    return [{"o":float(c[1]),"h":float(c[2]),"l":float(c[3]),"c":float(c[4]),"v":float(c[5])} for c in data]
            except: continue
        return None

    def get_gold_price():
        p = get_tv_price()
        if p and 1000 < p < 10000: return p
        for base in ["https://api.binance.com", "https://data-api.binance.vision"]:
            try:
                p = float(requests.get(f"{base}/api/v3/ticker/price?symbol=PAXGUSDT", timeout=8).json()['price'])
                if 1000 < p < 10000: return p
            except: pass
        return None

    def get_candles(interval, limit=100):
        c = get_tv_candles(interval, limit)
        if c: return c
        return get_binance_candles(interval, limit)

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

    def detect_ob_real(candles):
        ob_bull=None; ob_bear=None; ob_bull_price=0; ob_bear_price=0
        for i in range(len(candles)-15, len(candles)-3):
            if candles[i]['c'] < candles[i]['o']:
                if candles[i+1]['c'] > candles[i+1]['o'] and candles[i+2]['c'] > candles[i+1]['h']:
                    body = candles[i+1]['c']-candles[i+1]['o']
                    rng = candles[i+1]['h']-candles[i+1]['l']
                    if rng>0 and body/rng > 0.6:
                        ob_bull=True; ob_bull_price=candles[i]['l']
            if candles[i]['c'] > candles[i]['o']:
                if candles[i+1]['c'] < candles[i+1]['o'] and candles[i+2]['c'] < candles[i+1]['l']:
                    body = candles[i+1]['o']-candles[i+1]['c']
                    rng = candles[i+1]['h']-candles[i+1]['l']
                    if rng>0 and body/rng > 0.6:
                        ob_bear=True; ob_bear_price=candles[i]['h']
        return ob_bull, ob_bull_price, ob_bear, ob_bear_price

    def load(f):
        if os.path.exists(f):
            try:
                with open(f,'r',encoding='utf-8') as x:
                    data=json.load(x)
                    if isinstance(data, dict) and "entry" not in data and "time" not in data:
                        return None
                    return data
            except: return None
        return None
    def save(f,d):
        with open(f,'w',encoding='utf-8') as x: json.dump(d,x)

    c5=get_candles("5m",100)
    if not c5:
        send_tg(f"⚠️ فشل جلب الشموع TV+Binance {datetime.now().strftime('%H:%M')}")
        sys.exit(0)
    c1h=get_candles("1h",100) or c5
    c4h=get_candles("4h",100) or c5

    gold_price=get_gold_price() or c5[-1]['c']
    price=gold_price; now=datetime.now()
    trade=load("trade.json")

    rsi5=rsi(c5,14); ema200_4h=ema(c4h,200); atr5=atr(c5,14)
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

    if trade and "entry" in trade:
        entry,typ,sl,tp=trade['entry'],trade['type'],trade['sl'],trade['tp2']
        diff=(price-entry) if typ=="BUY" else (entry-price); pips=diff*10
        if (typ=="BUY" and price<=sl) or (typ=="SELL" and price>=sl):
            msg=f"❌ SL {typ} {pips:.1f} | {now.strftime('%I:%M %p')} | TV {price:.1f}$"
            try: os.remove("trade.json")
            except: pass
        elif (typ=="BUY" and price>=tp) or (typ=="SELL" and price<=tp):
            msg=f"🏆 TP {typ} +{pips:.1f} 🔥 | {now.strftime('%I:%M %p')} | TV {price:.1f}$"
            try: os.remove("trade.json")
            except: pass
        else:
            msg=f"🔄 {typ} {pips:+.1f} | {now.strftime('%I:%M %p')} | TV {price:.1f}$"
    else:
        if buy_score>=4:
            sl=round(price - atr5*1.2,2); tp=round(price + atr5*2.5,2); entry=round(price,2)
            save("trade.json",{"type":"BUY","entry":entry,"sl":sl,"tp2":tp})
            msg=f"💎 TV BUY {price:.1f}$ | {now.strftime('%I:%M %p')} | RSI {rsi5:.0f} | {buy_score}/6"
        elif sell_score>=4:
            sl=round(price + atr5*1.2,2); tp=round(price - atr5*2.5,2); entry=round(price,2)
            save("trade.json",{"type":"SELL","entry":entry,"sl":sl,"tp2":tp})
            msg=f"💎 TV SELL {price:.1f}$ | {now.strftime('%I:%M %p')} | RSI {rsi5:.0f}"
        else:
            msg=f"⏳ TV {price:.1f}$ | {now.strftime('%I:%M %p')} | RSI {rsi5:.0f} | Buy {buy_score}/6 Sell {sell_score}/6"

    send_tg(msg)
    print(f"Done: {msg}")
    sys.exit(0)

except Exception as e:
    print(f"Error: {e}")
    try:
        send_tg(f"⚠️ V19.4 Error: {str(e)[:200]}")
    except: pass
    sys.exit(0)
