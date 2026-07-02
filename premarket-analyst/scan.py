#!/usr/bin/env python3
"""Premarket data gatherer. Collects raw data into packet.json. ZERO analysis.
All judgment happens later in the AI prompt layer. Free, keyless sources only:
yfinance (prices/screeners), feedparser (RSS news), requests (econ calendar),
plus Zac's own jarvis-lookup edge function for the Your Book overlay.
"""
import json, re, sys, time, os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

try:
    import yfinance as yf
    import feedparser
    import requests
except ImportError:
    sys.exit("Missing deps. Run: pip install yfinance feedparser requests --break-system-packages")

ET = ZoneInfo("America/New_York"); MEL = ZoneInfo("Australia/Melbourne")
NOW_ET = datetime.now(ET); NOW_MEL = datetime.now(MEL)
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".econ_cache.json")

SNAPSHOT = {"S&P 500": "^GSPC", "Dow": "^DJI", "Nasdaq": "^IXIC", "Russell 2000": "^RUT",
            "VIX": "^VIX", "US 10Y": "^TNX", "US 3M": "^IRX", "WTI Oil": "CL=F", "DXY": "DX-Y.NYB",
            "ASX 200": "^AXJO", "AUD/USD": "AUDUSD=X"}
UNIVERSE = ["NVDA","AMD","AVGO","SMCI","MRVL","TSLA","AAPL","MSFT","META","AMZN","GOOGL","NFLX",
            "DELL","SNOW","PLTR","COIN","MSTR","SOFI","RIVN","NIO","MARA","RIOT","BA","DIS","JPM",
            "BAC","XOM","CVX","HOOD","UBER","CRWD","PANW","CELH","LULU","NKE","CAVA","DKNG","ARM","INTC","MU"]
RSS_FEEDS = ["https://feeds.content.dowjones.io/public/rss/mw_topstories",
             "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
             "https://www.cnbc.com/id/100003114/device/rss/rss.html",
             "https://finance.yahoo.com/news/rssindex",
             "https://news.google.com/rss/search?q=stock+market+earnings+when:1d&hl=en-US&gl=US&ceid=US:en"]
SPAM = re.compile(r"price prediction|20\d\d-20\d\d", re.I)
NAME_STOP = {"the","inc","corp","corporation","holdings","technologies","technology","group","digital",
             "applied","advanced","strategy","motors","energy","platforms","company","co","ltd","plc",
             "global","international","industries","systems","solutions","enterprises","capital","financial"}
PRIMARY = ["bloomberg","reuters","cnbc","marketwatch","barron","yahoo finance","wsj","wall street"]

# Zac's book (units/levels enriched live from his dashboard endpoints)
BOOK = {"holdings": ["WTC.AX","NOW","VOO"],
        "watch": ["CSL.AX","TLX.AX","WDS.AX","BAP.AX","PV1.AX","MU","IONQ","MSFT","OUST","VPG","AMBA"],
        "buy_below": {"WTC.AX":30.0,"NOW":90.0,"CSL.AX":110.0,"TLX.AX":14.0,"WDS.AX":26.0}}
LOOKUP = "https://liqfekbcoopnelrnkkox.supabase.co/functions/v1/jarvis-lookup"

def log(msg): print(f"[scan] {msg}", flush=True)

def safe(fn, fallback=None, label=""):
    try: return fn()
    except Exception as e:
        log(f"WARN {label}: {e}"); return fallback

def two_closes(sym):
    h = yf.Ticker(sym).history(period="5d", interval="1d")
    c = [float(x) for x in h["Close"].dropna().tolist()]
    return c[-1], c[-2] if len(c) > 1 else None

def snapshot():
    def one(item):
        name, sym = item
        def get():
            last, prev = two_closes(sym)
            return {"last": round(last, 3), "prev_close": round(prev, 3) if prev else None,
                    "change_pct": round((last - prev) / prev * 100, 2) if prev else None}
        return name, safe(get, None, f"snapshot {sym}")
    with ThreadPoolExecutor(11) as ex:
        return {n: v for n, v in ex.map(one, SNAPSHOT.items()) if v}

def movers():
    rows, source = [], "screener"
    def screener():
        got = []
        for scr in ("day_gainers", "most_actives"):
            try:
                r = requests.get(f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=25&scrIds={scr}",
                                 headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                for q in (r.json().get("finance", {}).get("result") or [{}])[0].get("quotes", []):
                    got.append({"ticker": q.get("symbol"), "name": (q.get("shortName") or q.get("symbol") or "")[:40],
                                "price": q.get("regularMarketPrice"), "prev_close": q.get("regularMarketPreviousClose"),
                                "gap_pct": q.get("regularMarketChangePercent"), "market_cap": q.get("marketCap"),
                                "volume": q.get("regularMarketVolume")})
            except Exception as e: log(f"screener {scr} failed: {e}")
        seen, out = set(), []
        for g in got:
            if g["ticker"] and g["ticker"] not in seen: seen.add(g["ticker"]); out.append(g)
        return out
    rows = screener()
    if len(rows) < 5:
        source = "static_universe"; log("screener thin — falling back to static universe")
        for sym in UNIVERSE:
            def get(sym=sym):
                last, prev = two_closes(sym)
                info = yf.Ticker(sym).fast_info
                return {"ticker": sym, "name": sym, "price": round(last, 2), "prev_close": round(prev, 2) if prev else None,
                        "gap_pct": round((last - prev) / prev * 100, 2) if prev else None,
                        "market_cap": getattr(info, "market_cap", None), "volume": getattr(info, "last_volume", None)}
            v = safe(get, None, f"universe {sym}")
            if v: rows.append(v)
    kept = [r for r in rows if r.get("gap_pct") is not None and abs(r["gap_pct"]) >= 4 and (r.get("price") or 0) >= 3]
    kept.sort(key=lambda r: abs(r["gap_pct"]), reverse=True)
    return kept[:12], source

def market_news():
    items = []
    for url in RSS_FEEDS:
        def get(url=url):
            f = feedparser.parse(url)
            return [{"title": e.get("title", "").strip(),
                     "summary": re.sub(r"<[^>]+>", "", e.get("summary", ""))[:220],
                     "source": (f.feed.get("title") or url)[:40], "link": e.get("link", "")}
                    for e in f.entries[:12]]
        for it in safe(get, [], f"rss {url}") or []:
            if it["title"] and not SPAM.search(it["title"]): items.append(it)
    return items[:20], items  # top 20 for packet, all for catalyst matching

def econ_calendar():
    today = NOW_ET.date(); tomorrow = today + timedelta(days=1)
    raw, note = None, ""
    if os.path.exists(CACHE):
        try:
            c = json.load(open(CACHE))
            if time.time() - c.get("fetched_at", 0) < 4 * 3600: raw = c["data"]
        except Exception: pass
    if raw is None:
        try:
            r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json",
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            raw = r.json(); json.dump({"fetched_at": time.time(), "data": raw}, open(CACHE, "w"))
        except Exception as e:
            note = f"live fetch failed ({e}); "
            try: raw = json.load(open(CACHE))["data"]; note += "using cached week"
            except Exception: return {"source": "forexfactory", "error": note + "no cache", "today": [], "tomorrow": []}
    def rows(day):
        out = []
        for ev in raw:
            if ev.get("country") != "USD" or ev.get("impact") != "High": continue
            try: d = datetime.fromisoformat(ev["date"]).astimezone(ET)
            except Exception: continue
            if d.date() == day:
                out.append({"time_et": d.strftime("%-I:%M %p"), "title": ev.get("title"),
                            "forecast": ev.get("forecast"), "previous": ev.get("previous"), "_t": d})
        return [dict((k, v) for k, v in r.items() if k != "_t") for r in sorted(out, key=lambda r: r["_t"])]
    return {"source": "forexfactory", "filter": "USD High-impact", "note": note,
            "today_date": str(today), "tomorrow_date": str(tomorrow), "today": rows(today), "tomorrow": rows(tomorrow)}

def distinctive_tokens(name):
    return [w for w in re.findall(r"[A-Za-z]{4,}", name or "") if w.lower() not in NAME_STOP]

def match_catalyst(ticker, name, all_news, yf_news):
    hits = []
    tk = re.compile(rf"\b{re.escape(ticker)}\b")
    toks = distinctive_tokens(name)
    for n in yf_news:
        t = n.get("title") or (n.get("content") or {}).get("title") or ""
        if t: hits.append({"title": t, "source": "yfinance", "link": ""})
    for it in all_news:
        t = it["title"] + " " + it.get("summary", "")
        if tk.search(t) or any(re.search(rf"\b{re.escape(w)}\b", t, re.I) for w in toks):
            hits.append({"title": it["title"], "source": it["source"], "link": it["link"]})
    hits.sort(key=lambda h: 0 if any(p in h["source"].lower() for p in PRIMARY) else 1)
    dedup, seen = [], set()
    for h in hits:
        k = h["title"][:60]
        if k not in seen: seen.add(k); dedup.append(h)
    return dedup[:4]

def enrich(g, all_news):
    sym = g["ticker"]; t = yf.Ticker(sym)
    out = dict(g)
    def intraday():
        h = t.history(period="1d", interval="5m", prepost=True)
        if h.empty: return {}
        tp = (h["High"] + h["Low"] + h["Close"]) / 3
        vwap = float((tp * h["Volume"]).sum() / max(h["Volume"].sum(), 1))
        reg = h.between_time("09:30", "16:00"); pre = h.between_time("04:00", "09:29")
        return {"vwap": round(vwap, 2), "hod": round(float(h["High"].max()), 2), "lod": round(float(h["Low"].min()), 2),
                "premarket_high": round(float(pre["High"].max()), 2) if not pre.empty else None,
                "premarket_volume": int(pre["Volume"].sum()) if not pre.empty else 0}
    def daily():
        h = t.history(period="1y", interval="1d")
        if len(h) < 2: return {}
        full = h.iloc[:-1] if NOW_ET.hour < 16 else h  # exclude today's partial bar
        c = full["Close"]
        return {"sma200": round(float(c.tail(200).mean()), 2), "prior_high": round(float(full["High"].iloc[-1]), 2),
                "prior_close": round(float(c.iloc[-1]), 2),
                "today_open": round(float(h["Open"].iloc[-1]), 2) if NOW_ET.hour >= 9 else None,
                "avg_vol_20d": int(full["Volume"].tail(20).mean())}
    out["levels"] = safe(intraday, {}, f"intraday {sym}") or {}
    out["daily"] = safe(daily, {}, f"daily {sym}") or {}
    av = out["daily"].get("avg_vol_20d") or 0
    out["rvol"] = round((g.get("volume") or 0) / av, 2) if av else None
    # NOTE: yfinance reports ~0 premarket volume; true premarket RVOL needs a premarket feed
    # (e.g. Alpaca). Full-day relative volume is the keyless stand-in.
    out["next_earnings"] = safe(lambda: str(t.calendar.get("Earnings Date", [None])[0]), None, f"earnings {sym}")
    yf_news = safe(lambda: t.news[:5], [], f"news {sym}") or []
    out["catalysts"] = match_catalyst(sym, g.get("name", ""), all_news, yf_news)
    out["catalyst_found"] = len(out["catalysts"]) > 0
    d, l = out["daily"], out["levels"]
    gp, px, mc = g.get("gap_pct") or 0, g.get("price") or 0, g.get("market_cap") or 0
    out["day_eligible"] = bool(gp > 3 and px > 3 and mc > 1e9 and (out["rvol"] or 0) > 1.5
                               and d.get("prior_high") and px > d["prior_high"])
    out["swing_eligible"] = bool(gp >= 8 and px > 3 and mc >= 8e8 and out["catalyst_found"]
                                 and d.get("today_open") and d.get("prior_high") and d.get("sma200")
                                 and d["today_open"] > d["prior_high"] and d["today_open"] > d["sma200"])
    return out

def your_book():
    syms = BOOK["holdings"] + BOOK["watch"]
    def get():
        r = requests.get(LOOKUP, params={"tickers": ",".join(syms)}, timeout=20)
        return {x["sym"]: x for x in r.json().get("rows", [])}
    px = safe(get, {}, "jarvis-lookup") or {}
    rows = []
    for s in syms:
        p = px.get(s, {})
        bb = BOOK["buy_below"].get(s)
        rows.append({"ticker": s, "held": s in BOOK["holdings"], "price": p.get("price"), "day_pct": p.get("pct"),
                     "low52": p.get("low52"), "high52": p.get("high52"), "buy_below": bb,
                     "buy_zone": bool(bb and p.get("price") is not None and p["price"] <= bb),
                     "big_move": bool(p.get("pct") is not None and abs(p["pct"]) >= 4)})
    return rows

def main():
    log("market snapshot…");   snap = snapshot()
    log("movers…");            gaps, source = movers()
    log("market news…");       top_news, all_news = market_news()
    log("econ calendar…");     cal = econ_calendar()
    log(f"enriching {len(gaps)} gappers (parallel)…")
    with ThreadPoolExecutor(6) as ex:
        gappers = list(ex.map(lambda g: enrich(g, all_news), gaps))
    log("your book…");         book = your_book()
    packet = {
        "generated_at": NOW_ET.isoformat(), "generated_mel": NOW_MEL.isoformat(),
        "candidate_source": source,
        "trading_day_note": f"Run at {NOW_ET.strftime('%-I:%M %p')} ET ({NOW_MEL.strftime('%-I:%M %p')} Melbourne)",
        "scan_params": {"min_abs_gap_pct": 4, "min_price": 3, "max_gappers": 12},
        "criteria": {"day": "gap>3% & price>$3 & mcap>$1B & RVOL>1.5 & price>prior-day high (Trend Join Long)",
                     "swing": "gap>=8% & price>$3 & open>prior high & open>200d SMA & mcap>=$800M & real catalyst"},
        "market_snapshot": snap, "econ_calendar": cal, "gappers": gappers,
        "your_book": book, "market_news": top_news,
        "gaps_to_fill": ["market-wide earnings calendar only partial (per-gapper next-earnings only)",
                         "premarket RVOL is a full-day stand-in (yfinance premarket volume ~0)",
                         "intraday levels need the market to have traded today"]}
    with open(os.path.join(HERE, "packet.json"), "w") as f: json.dump(packet, f, indent=1)
    log(f"WROTE packet.json — {len(gappers)} gappers ({source}), "
        f"{len(cal.get('today', []))} US high-impact events today, "
        f"{sum(1 for b in book if b['buy_zone'])} buy-zone hits on your book")

if __name__ == "__main__":
    main()
