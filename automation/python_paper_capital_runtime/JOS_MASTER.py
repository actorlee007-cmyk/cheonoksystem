"""JOS MASTER - PAPER_CAPITAL_INTELLIGENCE single-source runtime.

Real-time market feed (yfinance) + news feed (RSS) + scoring + ranking +
PAPER portfolio + live report loop, integrated into one runnable file.

Run:
    python JOS_MASTER.py

Safety:
- PAPER_ONLY TRUE
- LIVE_TRADE BLOCKED
- CAPITAL_SCALE BLOCKED
- KIS_ORDER_GATE BLOCKED
- No order execution. No broker connection. PAPER_BUY signals only.
"""

import time
import json
import random
import feedparser
import yfinance as yf

from datetime import datetime, timezone

# =====================================
# CONFIG
# =====================================

WATCHLIST = [
    "AAPL",
    "TSLA",
    "NVDA",
    "MSFT",
    "005930.KS"
]

RSS = [
    "https://rss.donga.com/total.xml",
    "https://www.khan.co.kr/rss/rssdata/total_news.xml"
]

# =====================================
# STATE
# =====================================

STATE = {
    "events": [],
    "signals": [],
    "paper_trades": [],
    "rankings": [],
    "portfolio": [],
    "reports": []
}

# =====================================
# MARKET
# =====================================

def market_feed():

    rows = []

    for ticker in WATCHLIST:

        try:

            data = yf.Ticker(ticker)

            hist = data.history(period="1d")

            if len(hist) == 0:
                continue

            last = hist.iloc[-1]

            rows.append({
                "ticker": ticker,
                "price": float(last["Close"]),
                "volume": float(last["Volume"])
            })

        except Exception:
            pass

    return rows

# =====================================
# NEWS
# =====================================

def news_feed():

    news = []

    for url in RSS:

        try:

            feed = feedparser.parse(url)

            for item in feed.entries[:5]:

                news.append(item.title)

        except Exception:
            pass

    return news

# =====================================
# SCORE
# =====================================

def score_market(row):

    score = 0

    volume = row["volume"]

    if volume > 100000:
        score += 30

    if volume > 500000:
        score += 30

    if volume > 1000000:
        score += 40

    return score

# =====================================
# RANK ENGINE
# =====================================

def rank_engine(market):

    ranking = []

    for row in market:

        ranking.append({
            "ticker": row["ticker"],
            "score": score_market(row),
            "price": row["price"],
            "volume": row["volume"]
        })

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranking

# =====================================
# PAPER ENGINE
# =====================================

def paper_engine(ranking):

    if len(ranking) == 0:
        return

    top = ranking[0]

    if top["score"] >= 60:

        trade = {
            "ticker": top["ticker"],
            "score": top["score"],
            "action": "PAPER_BUY",
            "ts": datetime.now(
                timezone.utc
            ).isoformat()
        }

        STATE["paper_trades"].append(trade)

# =====================================
# PORTFOLIO
# =====================================

def portfolio_engine():

    portfolio = {}

    for trade in STATE["paper_trades"]:

        t = trade["ticker"]

        portfolio[t] = portfolio.get(t, 0) + 1

    STATE["portfolio"] = portfolio

# =====================================
# REPORT
# =====================================

def report():

    report_data = {

        "events":
            len(STATE["events"]),

        "signals":
            len(STATE["signals"]),

        "paper_trades":
            len(STATE["paper_trades"]),

        "portfolio":
            STATE["portfolio"],

        "top_rank":

            STATE["rankings"][0]
            if len(STATE["rankings"]) > 0
            else None,

        "ts":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    STATE["reports"].append(
        report_data
    )

    print()
    print("=" * 50)
    print("JOS REPORT")
    print("=" * 50)

    print(
        json.dumps(
            report_data,
            indent=2,
            ensure_ascii=False
        )
    )

# =====================================
# MAIN LOOP
# =====================================

def main():

    print("=== JOS MASTER START ===")

    while True:

        market = market_feed()

        news = news_feed()

        ranking = rank_engine(
            market
        )

        STATE["rankings"] = ranking

        for row in market:

            STATE["events"].append(row)

            if score_market(row) >= 60:
                STATE["signals"].append(
                    row
                )

        for n in news:

            STATE["events"].append(
                {"news": n}
            )

        paper_engine(
            ranking
        )

        portfolio_engine()

        report()

        time.sleep(60)

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    main()
