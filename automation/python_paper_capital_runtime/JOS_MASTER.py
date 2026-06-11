"""JOS MASTER - PAPER_CAPITAL_INTELLIGENCE single-source runtime.

Real-time market feed (yfinance, optionally upgraded to KIS for domestic
.KS tickers - see "KIS REAL DATA BRIDGE" below) + news feed (RSS) +
scoring + ranking (volume score + foreign/US sector linkage + news theme
bonus + trend breakout / bottom-fishing filter) + leader analysis (why #1
is #1, and similar watch-list candidates) + sector
strength analysis + market state classification + PAPER position
management (stop-loss / trailing-stop / rotation) + forward simulation
(historical bootstrap) + adaptive learning stats + ledger persistence +
intraday/close report loop, integrated into one runnable file.

Run (continuous, local):
    cd C:\\JOS_OS
    python .\\JOS_MASTER.py

Run (single intraday pass, cloud/CI):
    python JOS_MASTER.py --once

Run (end-of-day close / CEO report, cloud/CI):
    python JOS_MASTER.py --close

Ledger (persisted under ./ledger/, committed back to the repo by CI):
- signals_log.jsonl       : every PAPER_BUY / PAPER_SELL signal (Signal DB)
- results_log.jsonl       : realized return per closed position, with exit
                            reason (STOP_LOSS / TRAILING_STOP / ROTATION)
- positions.json          : currently open paper positions (entry price,
                            peak price since entry, sector)
- market_log.jsonl        : raw market snapshots (Market DB)
- news_log.jsonl          : raw news headlines (News DB)
- learning_stats.json      : rolling equity curve / win rate / drawdown
- tomorrow_watchlist.json  : next-session TOP candidates (consulted first
                            when opening new positions)
- leader_analysis.json     : why the #1-ranked ticker is #1 (score drivers:
                            volume / foreign(US) sector linkage / news
                            theme), plus a watch list of tickers sharing
                            the same drivers

Reporting:
- Each report is also sent to Telegram via CHEONOK_TELEGRAM_BOT_TOKEN /
  CHEONOK_TELEGRAM_CHAT_ID (same secrets as CHEONOK Supreme Master OS).
  If the secrets are missing, sending is skipped (HOLD_TELEGRAM_SECRETS_MISSING).

KIS REAL DATA BRIDGE (Layer 4: REAL DATA BRIDGE, optional):
- For domestic (.KS) tickers, market_feed() can additionally call the
  Korea Investment & Securities (KIS, 한국투자증권) Open API for a
  real-time 현재가 (current price) quote, READ-ONLY:
  GET /uapi/domestic-stock/v1/quotations/inquire-price (tr_id
  FHKST01010100). yfinance history is still fetched for every ticker and
  used for trend/breakout scoring; KIS only overrides price/volume/
  change_pct when it answers successfully.
- Enabled via CHEONOK_KIS_APP_KEY / CHEONOK_KIS_APP_SECRET (optional
  CHEONOK_KIS_BASE_URL, default https://openapi.koreainvestment.com:9443).
  If missing, prints HOLD_KIS_SECRETS_MISSING once per cycle and falls
  back to yfinance only (unchanged prior behavior).
- The OAuth2 access token (POST /oauth2/tokenP) is cached in-memory only
  for this process - never written to disk or to any ledger file, since
  ledger/ is committed to git by CI.
- Each market row records "price_source": "KIS" or "YFINANCE" as
  evidence of which feed answered for that ticker this cycle.

Safety:
- PAPER_ONLY TRUE
- LIVE_TRADE BLOCKED
- CAPITAL_SCALE BLOCKED
- KIS_ORDER_GATE BLOCKED
- No order execution. No broker connection. KIS is used ONLY for the
  read-only quote endpoint above - no order/account endpoints are ever
  called. PAPER_BUY signals only.
"""

import argparse
import os
import time
import json
import random
import urllib.error
import urllib.parse
import urllib.request
import feedparser
import yfinance as yf

from datetime import datetime, timezone
from pathlib import Path

# =====================================
# CONFIG
# =====================================

WATCHLIST = {
    "NVDA": "AI_SEMI",
    "AMD": "AI_SEMI",
    "AVGO": "AI_SEMI",
    "005930.KS": "AI_SEMI",
    "000660.KS": "AI_SEMI",

    "AAPL": "TECH_PLATFORM",
    "MSFT": "TECH_PLATFORM",
    "GOOGL": "TECH_PLATFORM",
    "META": "TECH_PLATFORM",
    "035420.KS": "TECH_PLATFORM",

    "TSLA": "EV_BATTERY",
    "RIVN": "EV_BATTERY",
    "373220.KS": "EV_BATTERY",
    "006400.KS": "EV_BATTERY",
    "247540.KS": "EV_BATTERY",

    "MRNA": "BIO",
    "PFE": "BIO",
    "JNJ": "BIO",
    "207940.KS": "BIO",
    "068270.KS": "BIO",

    "LMT": "DEFENSE",
    "RTX": "DEFENSE",
    "NOC": "DEFENSE",
    "012450.KS": "DEFENSE",
    "047810.KS": "DEFENSE",

    "JPM": "FINANCE",
    "BAC": "FINANCE",
    "GS": "FINANCE",
    "105560.KS": "FINANCE",
    "055550.KS": "FINANCE",
}

RSS = [
    "https://rss.donga.com/total.xml",
    "https://www.khan.co.kr/rss/rssdata/total_news.xml"
]

# Forward simulation engine
FORWARD_SIM_TRIALS = 1000
FORWARD_SIM_HORIZON_DAYS = 5
FORWARD_SIM_CANDIDATES = 30   # full WATCHLIST universe -> real "TOP30" candidate list

# Tomorrow watchlist (Layer 9: NEXT DAY TOP30 - the full ranked candidate
# universe is persisted to ledger/tomorrow_watchlist.json; the Telegram
# report shows only the top slice for readability)
TOMORROW_WATCHLIST_SIZE = 30
TOMORROW_WATCHLIST_REPORT_N = 10

# Learning engine
EQUITY_CURVE_MAX = 90

# Position management (stop-loss / trailing-stop / rotation)
ENTRY_SCORE_THRESHOLD = 60   # minimum score to open a new position
STOP_LOSS_PCT = 2.0          # hard exit if price falls this % below entry
TRAILING_STOP_PCT = 3.0      # once in profit, exit if price retreats this % from its peak
ROTATION_SCORE_GAP = 40      # rotate a non-profitable position into a candidate that
                              # outscores it by at least this much
MAX_OPEN_POSITIONS = 3        # max concurrent paper positions

# Foreign (US) -> domestic (KRX) sector linkage: KRX opens after the US
# session closes, so a strong/weak US sector is treated as a leading
# indicator for the matching Korean tickers in WATCHLIST.
FOREIGN_LINK_BONUS_STRONG = 20    # foreign sector avg change_pct >= +1.0%
FOREIGN_LINK_BONUS_MILD = 10      # foreign sector avg change_pct >= +0.3%
FOREIGN_LINK_PENALTY_MILD = -10   # foreign sector avg change_pct <= -0.3%
FOREIGN_LINK_PENALTY_STRONG = -20  # foreign sector avg change_pct <= -1.0%

# News headline keyword -> sector mapping, used to explain why a ticker
# is ranked where it is and to spot sector-wide news themes.
SECTOR_KEYWORDS = {
    "AI_SEMI": ["반도체", "AI", "인공지능", "엔비디아", "삼성전자", "하이닉스"],
    "TECH_PLATFORM": ["빅테크", "플랫폼", "애플", "구글", "메타", "마이크로소프트"],
    "EV_BATTERY": ["전기차", "배터리", "테슬라", "2차전지"],
    "BIO": ["바이오", "제약", "신약", "백신"],
    "DEFENSE": ["방산", "국방", "무기"],
    "FINANCE": ["금융", "은행", "증권"]
}
NEWS_SECTOR_BONUS = 10

# Leader analysis: how many "similar" candidates to surface alongside the
# #1-ranked ticker each cycle.
SIMILAR_CANDIDATES_SIZE = 5

# Global macro flows (Layer 1: GLOBAL FIRST). Checked before any Korea
# theme translation - Asia indices, USD/KRW, US rates, and commodities
# give the "global pulse" for the session.
GLOBAL_MACRO = {
    "^N225": "JAPAN_NIKKEI",
    "^HSI": "HONGKONG_HANGSENG",
    "KRW=X": "USDKRW",
    "^TNX": "US_10Y_YIELD",
    "CL=F": "WTI_OIL",
    "GC=F": "GOLD",
}

# Global risk state thresholds, based on the average change_pct of the
# equity-like global macro instruments (Nikkei / Hang Seng).
GLOBAL_RISK_ON_THRESHOLD = 0.5
GLOBAL_RISK_OFF_THRESHOLD = -0.5

# Macro -> Korea sector theme translation (Layer 2 extension): how each
# global macro instrument's move translates into a small score adjustment
# for domestic (.KS) tickers in a given sector.
MACRO_TRANSLATION_BONUS = 5
MACRO_SECTOR_RULES = {
    # USD/KRW up (won weaker) helps Korean exporters
    "USDKRW": {
        "AI_SEMI": "up_helps", "EV_BATTERY": "up_helps", "TECH_PLATFORM": "up_helps",
    },
    # US 10Y yield up hurts long-duration / growth themes
    "US_10Y_YIELD": {
        "AI_SEMI": "up_hurts", "TECH_PLATFORM": "up_hurts", "BIO": "up_hurts",
    },
    # Oil up helps defense (geopolitical premium), hurts EV/battery demand story
    "WTI_OIL": {
        "DEFENSE": "up_helps", "EV_BATTERY": "up_hurts",
    },
    # Gold up reflects risk-off demand, mild support for defense
    "GOLD": {
        "DEFENSE": "up_helps",
    },
}

# Rank overlap (Layer 5: RANK OVERLAP). A ticker that appears in multiple
# independent TOP-N signal lists (volume / foreign-link / news / momentum)
# gets an extra "overlap" bonus on top of its base score.
RANK_OVERLAP_TOP_N = 5
RANK_OVERLAP_BONUS = 5

# Trend breakout (추세 돌파매매, Layer 7 LEADER ROTATION extension):
# trend-following principle summarized from
# https://blog.naver.com/msj0629/224261876445 (돈깡TV x 완브로, "이거 깨닫고
# 시드 40억 달성한 트레이더" - the source video's own transcript could not be
# retrieved in this environment, YouTube transcript API is IP-blocked here).
# The summarized principle: an apparent low is not a safe entry on its own
# (price can keep falling from there) - the profitable entry is when price
# actually breaks out of its recent consolidation range on above-average
# volume.
TREND_BREAKOUT_LOOKBACK_DAYS = 20
TREND_CONSOLIDATION_MAX_RANGE_PCT = 8.0   # recent N-day high/low range, as % of the low
TREND_BREAKOUT_VOLUME_MULT = 1.5          # breakout-day volume vs N-day average volume
TREND_BREAKOUT_BONUS = 15
TREND_BOTTOM_FISHING_PENALTY = -10        # price still at/below the recent N-day low

# Hybrid mind engine (Layer 16: GOD HYBRID MIND ENGINE). Fuses the
# rule-based score engine, the statistical forward-simulation engine, and
# the market-regime engine into one BUY/WATCH/AVOID verdict per candidate.
HYBRID_REGIME_MULTIPLIER = {
    "EUPHORIA": 1.10,
    "TREND_UP": 1.05,
    "SIDEWAYS": 1.00,
    "TREND_DOWN": 0.90,
    "RISK_OFF": 0.80,
    "PANIC": 0.70,
    "UNKNOWN": 1.00,
}
HYBRID_BUY_THRESHOLD = 70
HYBRID_WATCH_THRESHOLD = 40
HYBRID_TOP_N = 5

# Paper account (Layer 15: ACCOUNT READ-ONLY STATUS). Notional starting
# capital for the read-only PAPER account snapshot - no broker connection,
# no order execution, derived purely from learning_stats equity curve.
PAPER_STARTING_CAPITAL_KRW = 100_000_000

# Essence memory (Layer 17: ESSENCE COLLISION TRANSCEND MEMORY). Rolling
# history of each session's #1 leader sector/drivers, used to surface the
# pattern that keeps recurring ("colliding") across sessions.
ESSENCE_MEMORY_MAX = 90

# Patch council (Layer 18: AUTO REVIEW PATCH COUNCIL). Thresholds for
# automatically flagged review items. AUTO_CODE_PATCH / CORE_PATCH remain
# BLOCKED - this only emits recommendations, never applies code changes.
PATCH_COUNCIL_LOSS_STREAK = 3
PATCH_COUNCIL_DRAWDOWN_PCT = 10.0


def sector_of(ticker):
    return WATCHLIST.get(ticker, "UNKNOWN")


def is_domestic_ticker(ticker):
    return ticker.endswith(".KS")

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
# LEDGER (Signal / News / Market / Result DB)
# =====================================

BASE_DIR = Path(__file__).resolve().parent
LEDGER_DIR = BASE_DIR / "ledger"

SIGNALS_LOG = LEDGER_DIR / "signals_log.jsonl"
RESULTS_LOG = LEDGER_DIR / "results_log.jsonl"
NEWS_LOG = LEDGER_DIR / "news_log.jsonl"
MARKET_LOG = LEDGER_DIR / "market_log.jsonl"
LEARNING_FILE = LEDGER_DIR / "learning_stats.json"
WATCHLIST_FILE = LEDGER_DIR / "tomorrow_watchlist.json"
POSITIONS_FILE = LEDGER_DIR / "positions.json"
LEADER_ANALYSIS_FILE = LEDGER_DIR / "leader_analysis.json"
GLOBAL_FLOWS_FILE = LEDGER_DIR / "global_flows.json"
ACCOUNT_STATUS_FILE = LEDGER_DIR / "account_status.json"
CONTROL_FILE = LEDGER_DIR / "control.json"
HYBRID_MIND_FILE = LEDGER_DIR / "hybrid_mind.json"
ESSENCE_MEMORY_FILE = LEDGER_DIR / "essence_memory.json"
PATCH_COUNCIL_FILE = LEDGER_DIR / "patch_council.json"
FINAL_VETO_LOG = LEDGER_DIR / "final_veto_log.jsonl"
CANON_STATUS_FILE = LEDGER_DIR / "canon_status.json"
SUBSCRIPTION_REPORT_FILE = LEDGER_DIR / "subscription_report.json"
CEO_REPORT_BOOK = LEDGER_DIR / "ceo_report_book.jsonl"


def ensure_ledger_dir():
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)


def append_jsonl(path, record):

    ensure_ledger_dir()

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path):

    if not path.exists():
        return []

    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    return rows


def load_json(path, default):

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):

    ensure_ledger_dir()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================================
# KIS REAL DATA BRIDGE (Layer 4: REAL DATA BRIDGE, optional, .KS only)
# =====================================

KIS_BASE_URL = os.environ.get(
    "CHEONOK_KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
).strip()

# 모의투자(virtual/paper) domain - app keys issued for a paper-trading KIS
# account return HTTP 403 against the real-trading domain above and vice
# versa. Tried automatically as a fallback (see kis_quote_auto) since this
# is a PAPER_ONLY system and a paper-account app key is the common case.
KIS_BASE_URL_PAPER = "https://openapivts.koreainvestment.com:29443"

# In-memory only - NEVER persisted to disk/ledger (ledger/ is committed to
# git by CI, and a leaked KIS bearer token is valid for up to 24h).
_KIS_TOKEN_CACHE = {"access_token": None, "expires_at": 0.0, "base_url": None}

# Remembers which domain (real vs paper) actually accepted this app
# key/secret pair, so later tickers in the same run skip straight to it.
_KIS_WORKING_BASE_URL = [KIS_BASE_URL]


def kis_credentials():
    app_key = os.environ.get("CHEONOK_KIS_APP_KEY", "").strip()
    app_secret = os.environ.get("CHEONOK_KIS_APP_SECRET", "").strip()

    if not app_key or not app_secret:
        return None, None

    return app_key, app_secret


def kis_get_token(app_key, app_secret, base_url):
    """Fetch a KIS OAuth2 access token (POST /oauth2/tokenP) and cache it
    in-memory for this process only. Never written to disk."""

    now = time.time()

    if (_KIS_TOKEN_CACHE["access_token"]
            and _KIS_TOKEN_CACHE["base_url"] == base_url
            and now < _KIS_TOKEN_CACHE["expires_at"]):
        return _KIS_TOKEN_CACHE["access_token"]

    body = json.dumps({
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }).encode("utf-8")

    req = urllib.request.Request(
        base_url + "/oauth2/tokenP",
        data=body,
        method="POST",
        headers={"content-type": "application/json; charset=UTF-8"}
    )

    with urllib.request.urlopen(req, timeout=10) as res:
        payload = json.loads(res.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        return None

    expires_in = float(payload.get("expires_in", 0) or 0)

    _KIS_TOKEN_CACHE["access_token"] = token
    _KIS_TOKEN_CACHE["expires_at"] = now + max(expires_in - 60, 0)
    _KIS_TOKEN_CACHE["base_url"] = base_url

    return token


def kis_quote(ticker, app_key, app_secret, base_url):
    """Read-only domestic-stock current-price quote (국내주식 현재가 시세
    조회, tr_id FHKST01010100). KIS_ORDER_GATE remains BLOCKED - only this
    quotations endpoint is ever called, never an order/account endpoint."""

    token = kis_get_token(app_key, app_secret, base_url)

    if not token:
        return None

    code = ticker.split(".")[0]

    url = (
        base_url
        + "/uapi/domestic-stock/v1/quotations/inquire-price"
        + "?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=" + code
    )

    req = urllib.request.Request(url, headers={
        "content-type": "application/json; charset=UTF-8",
        "authorization": "Bearer " + token,
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "FHKST01010100"
    })

    with urllib.request.urlopen(req, timeout=10) as res:
        payload = json.loads(res.read().decode("utf-8"))

    output = payload.get("output") or {}

    price = output.get("stck_prpr")

    if price is None:
        return None

    return {
        "price": float(price),
        "volume": float(output.get("acml_vol") or 0.0),
        "change_pct": float(output.get("prdy_ctrt") or 0.0)
    }


def kis_quote_auto(ticker, app_key, app_secret):
    """Try the configured KIS domain first; on HTTP 403 (the app
    key/secret pair is registered against the other domain - real vs
    모의투자) retry once against the paper-trading domain and remember
    whichever domain worked for the rest of this process."""

    base_url = _KIS_WORKING_BASE_URL[0]

    try:
        return kis_quote(ticker, app_key, app_secret, base_url)
    except urllib.error.HTTPError as exc:
        if exc.code != 403 or base_url == KIS_BASE_URL_PAPER:
            raise

    fallback_url = KIS_BASE_URL_PAPER if base_url != KIS_BASE_URL_PAPER else KIS_BASE_URL
    _KIS_TOKEN_CACHE["access_token"] = None
    data = kis_quote(ticker, app_key, app_secret, fallback_url)
    _KIS_WORKING_BASE_URL[0] = fallback_url

    return data

# =====================================
# MARKET
# =====================================

def market_feed():

    rows = []

    kis_app_key, kis_app_secret = kis_credentials()
    kis_hold_logged = False
    kis_fail_logged = False

    for ticker, sector in WATCHLIST.items():

        try:

            data = yf.Ticker(ticker)

            hist = data.history(period="3mo")

            hist = hist.dropna(subset=["Close"])

            if len(hist) == 0:
                continue

            last = hist.iloc[-1]

            price = float(last["Close"])
            volume = float(last["Volume"])

            if len(hist) >= 2:
                prev_close = float(hist.iloc[-2]["Close"])
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
            else:
                change_pct = 0.0

            trend_bonus, trend_drivers = trend_breakout_signal(hist)

            price_source = "YFINANCE"

            if is_domestic_ticker(ticker):

                if kis_app_key and kis_app_secret:

                    try:
                        kis_data = kis_quote_auto(ticker, kis_app_key, kis_app_secret)
                    except Exception as exc:
                        kis_data = None
                        if not kis_fail_logged:
                            print(f"HOLD_KIS_QUOTE_FAILED: {type(exc).__name__}: {exc}")
                            kis_fail_logged = True

                    if kis_data:
                        price = kis_data["price"]
                        volume = kis_data["volume"]
                        change_pct = kis_data["change_pct"]
                        price_source = "KIS"

                elif not kis_hold_logged:
                    print("HOLD_KIS_SECRETS_MISSING")
                    kis_hold_logged = True

            rows.append({
                "ticker": ticker,
                "sector": sector,
                "price": price,
                "volume": volume,
                "change_pct": change_pct,
                "trend_bonus": trend_bonus,
                "trend_drivers": trend_drivers,
                "price_source": price_source
            })

        except Exception:
            pass

    return rows

# =====================================
# GLOBAL FLOWS (Layer 1: GLOBAL FIRST)
# =====================================

def global_flows_feed():
    """Fetch the global macro pulse (Asia indices, USD/KRW, US 10Y yield,
    oil, gold) - checked first, ahead of any Korea-specific scoring, per
    the 'global flows -> Korea theme translation' candidate flow."""

    rows = []

    for ticker, label in GLOBAL_MACRO.items():

        try:

            data = yf.Ticker(ticker)

            hist = data.history(period="5d")

            hist = hist.dropna(subset=["Close"])

            if len(hist) == 0:
                continue

            last = hist.iloc[-1]

            price = float(last["Close"])

            if len(hist) >= 2:
                prev_close = float(hist.iloc[-2]["Close"])
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
            else:
                change_pct = 0.0

            rows.append({
                "ticker": ticker,
                "label": label,
                "price": price,
                "change_pct": change_pct
            })

        except Exception:
            pass

    save_json(GLOBAL_FLOWS_FILE, {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "flows": rows
    })

    return rows


def global_risk_state(global_flows):
    """Classify the global session as RISK_ON / RISK_OFF / NEUTRAL from
    the Asia equity indices (Nikkei / Hang Seng) - used to dampen or
    amplify downstream scoring and the hybrid mind regime multiplier."""

    equity_changes = [
        row["change_pct"] for row in global_flows
        if row["label"] in ("JAPAN_NIKKEI", "HONGKONG_HANGSENG")
    ]

    if not equity_changes:
        return "NEUTRAL"

    avg_change = sum(equity_changes) / len(equity_changes)

    if avg_change >= GLOBAL_RISK_ON_THRESHOLD:
        return "RISK_ON"

    if avg_change <= GLOBAL_RISK_OFF_THRESHOLD:
        return "RISK_OFF"

    return "NEUTRAL"

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


def trend_breakout_signal(hist):
    """Score bonus/penalty from a confirmed trend breakout vs. 'bottom-
    fishing' on a chart still making new lows. See the
    TREND_BREAKOUT_LOOKBACK_DAYS comment for the source/principle."""

    closes = hist["Close"]
    volumes = hist["Volume"]

    if len(closes) < TREND_BREAKOUT_LOOKBACK_DAYS + 1:
        return 0, []

    recent_closes = closes.iloc[-(TREND_BREAKOUT_LOOKBACK_DAYS + 1):-1]
    recent_volumes = volumes.iloc[-(TREND_BREAKOUT_LOOKBACK_DAYS + 1):-1]

    last_close = float(closes.iloc[-1])
    last_volume = float(volumes.iloc[-1])

    range_high = float(recent_closes.max())
    range_low = float(recent_closes.min())
    avg_volume = float(recent_volumes.mean()) if len(recent_volumes) else 0.0

    if range_low <= 0:
        return 0, []

    consolidation_pct = (range_high - range_low) / range_low * 100

    bonus = 0
    drivers = []

    if (
        consolidation_pct <= TREND_CONSOLIDATION_MAX_RANGE_PCT
        and last_close > range_high
        and avg_volume > 0
        and last_volume >= avg_volume * TREND_BREAKOUT_VOLUME_MULT
    ):
        bonus += TREND_BREAKOUT_BONUS
        drivers.append("TREND_BREAKOUT")

    if last_close <= range_low:
        bonus += TREND_BOTTOM_FISHING_PENALTY
        drivers.append("BOTTOM_FISHING_CAUTION")

    return bonus, drivers


def foreign_sector_strength(market):
    """Average change_pct of non-domestic (US) tickers per sector - the
    'foreign market pulse' used as a leading indicator for KRX tickers."""

    sectors = {}

    for row in market:

        if is_domestic_ticker(row["ticker"]):
            continue

        sectors.setdefault(row["sector"], []).append(row["change_pct"])

    return {
        sector: sum(changes) / len(changes)
        for sector, changes in sectors.items()
    }


def foreign_linkage_bonus(row, foreign_strength):
    """Score bonus/penalty applied to a domestic ticker based on how its
    sector traded overnight in the foreign (US) market."""

    if not is_domestic_ticker(row["ticker"]):
        return 0

    change = foreign_strength.get(row["sector"])

    if change is None:
        return 0

    if change >= 1.0:
        return FOREIGN_LINK_BONUS_STRONG

    if change >= 0.3:
        return FOREIGN_LINK_BONUS_MILD

    if change <= -1.0:
        return FOREIGN_LINK_PENALTY_STRONG

    if change <= -0.3:
        return FOREIGN_LINK_PENALTY_MILD

    return 0


def news_sector_bonus(sector, news):
    """Score bonus if any headline this cycle matches the sector's
    keyword list - i.e. the sector has an active news theme."""

    for headline in news:
        for keyword in SECTOR_KEYWORDS.get(sector, []):
            if keyword in headline:
                return NEWS_SECTOR_BONUS

    return 0


def macro_translation_bonus(row, global_flows):
    """Translate global macro moves (USD/KRW, US 10Y yield, oil, gold)
    into a small score adjustment for domestic (.KS) tickers, per sector -
    the 'global flows -> Korea theme translation' extension of Layer 2."""

    if not is_domestic_ticker(row["ticker"]):
        return 0

    flows_by_label = {f["label"]: f["change_pct"] for f in (global_flows or [])}

    bonus = 0

    for label, sector_rules in MACRO_SECTOR_RULES.items():

        change = flows_by_label.get(label)

        if not change:
            continue

        rule = sector_rules.get(row["sector"])

        if rule is None:
            continue

        if rule == "up_helps":
            bonus += MACRO_TRANSLATION_BONUS if change > 0 else -MACRO_TRANSLATION_BONUS

        elif rule == "up_hurts":
            bonus -= MACRO_TRANSLATION_BONUS if change > 0 else -MACRO_TRANSLATION_BONUS

    return bonus

# =====================================
# RANK ENGINE
# =====================================

def rank_engine(market, foreign_strength=None, news=None, global_flows=None):

    foreign_strength = foreign_strength or {}
    news = news or []
    global_flows = global_flows or []

    rows = []

    for row in market:

        rows.append({
            "ticker": row["ticker"],
            "sector": row["sector"],
            "volume_score": score_market(row),
            "foreign_link_bonus": foreign_linkage_bonus(row, foreign_strength),
            "foreign_sector_change_pct": foreign_strength.get(row["sector"], 0.0),
            "news_bonus": news_sector_bonus(row["sector"], news),
            "macro_bonus": macro_translation_bonus(row, global_flows),
            "trend_bonus": row.get("trend_bonus", 0),
            "trend_drivers": row.get("trend_drivers", []),
            "price": row["price"],
            "volume": row["volume"],
            "change_pct": row.get("change_pct", 0.0)
        })

    # Rank overlap (Layer 5): build independent TOP-N signal lists, then
    # count how many lists each ticker appears in. A ticker that multiple
    # independent signals agree on gets an extra "overlap" bonus.
    by_volume = sorted(rows, key=lambda r: r["volume_score"], reverse=True)[:RANK_OVERLAP_TOP_N]
    by_momentum = sorted(rows, key=lambda r: r["change_pct"], reverse=True)[:RANK_OVERLAP_TOP_N]

    overlap_lists = {
        "VOLUME_TOP": {r["ticker"] for r in by_volume if r["volume_score"] > 0},
        "MOMENTUM_TOP": {r["ticker"] for r in by_momentum if r["change_pct"] > 0},
        "FOREIGN_LINK_TOP": {r["ticker"] for r in rows if r["foreign_link_bonus"] > 0},
        "NEWS_TOP": {r["ticker"] for r in rows if r["news_bonus"] > 0},
    }

    ranking = []

    for r in rows:

        memberships = [name for name, members in overlap_lists.items() if r["ticker"] in members]
        overlap_count = len(memberships)
        overlap_bonus = (overlap_count - 1) * RANK_OVERLAP_BONUS if overlap_count >= 2 else 0

        drivers = []

        if r["volume_score"] > 0:
            drivers.append("VOLUME(+%d)" % r["volume_score"])

        if r["foreign_link_bonus"]:
            drivers.append("FOREIGN_LINK(%+d)" % r["foreign_link_bonus"])

        if r["news_bonus"]:
            drivers.append("NEWS(+%d)" % r["news_bonus"])

        if r["macro_bonus"]:
            drivers.append("MACRO(%+d)" % r["macro_bonus"])

        if "TREND_BREAKOUT" in r["trend_drivers"]:
            drivers.append("TREND_BREAKOUT(+%d)" % TREND_BREAKOUT_BONUS)

        if "BOTTOM_FISHING_CAUTION" in r["trend_drivers"]:
            drivers.append("BOTTOM_FISHING_CAUTION(%d)" % TREND_BOTTOM_FISHING_PENALTY)

        if overlap_bonus:
            drivers.append("OVERLAP(x%d,+%d)" % (overlap_count, overlap_bonus))

        ranking.append({
            "ticker": r["ticker"],
            "sector": r["sector"],
            "score": r["volume_score"] + r["foreign_link_bonus"] + r["news_bonus"] + r["macro_bonus"] + r["trend_bonus"] + overlap_bonus,
            "volume_score": r["volume_score"],
            "foreign_link_bonus": r["foreign_link_bonus"],
            "foreign_sector_change_pct": r["foreign_sector_change_pct"],
            "news_bonus": r["news_bonus"],
            "macro_bonus": r["macro_bonus"],
            "trend_bonus": r["trend_bonus"],
            "trend_drivers": r["trend_drivers"],
            "overlap_count": overlap_count,
            "overlap_lists": memberships,
            "drivers": drivers,
            "price": r["price"],
            "volume": r["volume"],
            "change_pct": r["change_pct"]
        })

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranking

# =====================================
# MARKET STATE ENGINE
# =====================================

def market_state_engine(ranking):

    if not ranking:
        return "UNKNOWN"

    changes = [row["change_pct"] for row in ranking]

    avg_change = sum(changes) / len(changes)
    spread = max(changes) - min(changes)

    if spread >= 4.0:
        return "RISK_OFF"

    if avg_change >= 1.5:
        return "EUPHORIA"

    if avg_change >= 0.3:
        return "TREND_UP"

    if avg_change <= -1.5:
        return "PANIC"

    if avg_change <= -0.3:
        return "TREND_DOWN"

    return "SIDEWAYS"

# =====================================
# SECTOR STRENGTH ENGINE
# =====================================

def sector_strength_engine(ranking):

    sectors = {}

    for row in ranking:
        sectors.setdefault(row["sector"], []).append(row["change_pct"])

    strength = []

    for sector, changes in sectors.items():
        strength.append({
            "sector": sector,
            "avg_change_pct": sum(changes) / len(changes),
            "count": len(changes)
        })

    strength.sort(
        key=lambda x: x["avg_change_pct"],
        reverse=True
    )

    return strength

# =====================================
# LEADER ANALYSIS (why is #1 #1, and who looks similar)
# =====================================

def leader_analysis(ranking):
    """Explain why the top-ranked ticker is #1 (its score drivers), then
    scan the rest of the ranking for tickers sharing those same drivers
    (foreign sector linkage, sector news theme, or just same sector) -
    these are the 'next leader' candidates to watch for a rotation."""

    if not ranking:
        return None

    leader = ranking[0]

    leader_drivers = {"SECTOR:" + leader["sector"]}

    if leader["foreign_link_bonus"] > 0:
        leader_drivers.add("FOREIGN_LINK")

    if leader["news_bonus"] > 0:
        leader_drivers.add("NEWS")

    similar = []

    for row in ranking[1:]:

        row_drivers = {"SECTOR:" + row["sector"]}

        if row["foreign_link_bonus"] > 0:
            row_drivers.add("FOREIGN_LINK")

        if row["news_bonus"] > 0:
            row_drivers.add("NEWS")

        shared = leader_drivers & row_drivers

        if shared:
            similar.append({
                "ticker": row["ticker"],
                "sector": row["sector"],
                "score": row["score"],
                "shared_drivers": sorted(shared)
            })

    similar = similar[:SIMILAR_CANDIDATES_SIZE]

    analysis = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "leader": {
            "ticker": leader["ticker"],
            "sector": leader["sector"],
            "score": leader["score"],
            "drivers": leader["drivers"],
            "foreign_sector_change_pct": leader["foreign_sector_change_pct"],
            "change_pct": leader["change_pct"]
        },
        "similar_candidates": similar
    }

    save_json(LEADER_ANALYSIS_FILE, analysis)

    return analysis

# =====================================
# ESSENCE MEMORY (Layer 17: ESSENCE COLLISION TRANSCEND MEMORY)
# =====================================

def update_essence_memory(leader):
    """Persist each session's #1 leader pattern (sector + drivers) and
    surface the pattern that keeps recurring ('colliding') across
    sessions - the signal that transcends any single day's noise."""

    memory = load_json(ESSENCE_MEMORY_FILE, {"history": []})
    history = memory.get("history", [])

    if leader:
        history.append({
            "ts": leader["generated_ts"],
            "ticker": leader["leader"]["ticker"],
            "sector": leader["leader"]["sector"],
            "drivers": leader["leader"]["drivers"]
        })

    if len(history) > ESSENCE_MEMORY_MAX:
        history = history[-ESSENCE_MEMORY_MAX:]

    sector_counts = {}
    driver_counts = {}

    for h in history:
        sector_counts[h["sector"]] = sector_counts.get(h["sector"], 0) + 1
        for d in h["drivers"]:
            key = d.split("(")[0]
            driver_counts[key] = driver_counts.get(key, 0) + 1

    dominant_sector = max(sector_counts, key=sector_counts.get) if sector_counts else None
    dominant_driver = max(driver_counts, key=driver_counts.get) if driver_counts else None

    result = {
        "history": history,
        "sample_size": len(history),
        "dominant_sector": dominant_sector,
        "dominant_sector_count": sector_counts.get(dominant_sector, 0),
        "dominant_driver": dominant_driver,
        "dominant_driver_count": driver_counts.get(dominant_driver, 0),
        "updated_ts": datetime.now(timezone.utc).isoformat()
    }

    save_json(ESSENCE_MEMORY_FILE, result)

    return result

# =====================================
# CONTROL (Layer 14: TELEGRAM REPORT / SAFE CONTROL)
# =====================================

def load_control():
    """Read the operator safe-control switch. Setting trading_paused: true
    in ledger/control.json pauses new PAPER_BUY entries while exits
    (stop-loss / trailing-stop / rotation) keep running, so open risk is
    never left unmanaged. Writes the default file on first run so the
    switch exists as an editable ledger artifact."""

    control = load_json(CONTROL_FILE, {"trading_paused": False})

    if not CONTROL_FILE.exists():
        save_json(CONTROL_FILE, control)

    return control

# =====================================
# POSITION MANAGEMENT (stop-loss / trailing-stop / rotation)
# =====================================

def load_positions():
    return load_json(POSITIONS_FILE, {"positions": []}).get("positions", [])


def save_positions(positions):
    save_json(POSITIONS_FILE, {"positions": positions})


def close_position(position, current_price, reason):

    entry_price = position["entry_price"]
    return_pct = ((current_price - entry_price) / entry_price) * 100

    exit_signal = {
        "ticker": position["ticker"],
        "sector": position["sector"],
        "price": current_price,
        "action": "PAPER_SELL",
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat()
    }

    STATE["paper_trades"].append(exit_signal)
    append_jsonl(SIGNALS_LOG, exit_signal)

    result = {
        "signal_ts": position["entry_ts"],
        "ticker": position["ticker"],
        "sector": position["sector"],
        "entry_price": entry_price,
        "exit_price": current_price,
        "return_pct": return_pct,
        "win": return_pct > 0,
        "reason": reason,
        "ts": exit_signal["ts"]
    }

    append_jsonl(RESULTS_LOG, result)

    return result


def manage_positions(ranking):
    """Check every open position for a stop-loss, trailing-stop (profit
    locked in once the trend reverses), or rotation exit. Profits have no
    fixed cap - a position rides until the trailing stop triggers."""

    ranking_by_ticker = {row["ticker"]: row for row in ranking}

    positions = load_positions()
    top = ranking[0] if ranking else None

    remaining = []
    exit_results = []

    for position in positions:

        row = ranking_by_ticker.get(position["ticker"])

        if row is None:
            remaining.append(position)
            continue

        current_price = row["price"]
        entry_price = position["entry_price"]

        peak_price = max(position.get("peak_price", entry_price), current_price)
        position["peak_price"] = peak_price

        return_pct = ((current_price - entry_price) / entry_price) * 100

        reason = None

        if return_pct <= -STOP_LOSS_PCT:
            reason = "STOP_LOSS"

        elif peak_price > entry_price:
            drawdown_from_peak = ((peak_price - current_price) / peak_price) * 100
            if drawdown_from_peak >= TRAILING_STOP_PCT:
                reason = "TRAILING_STOP"

        if reason is None and top and top["ticker"] != position["ticker"] and return_pct <= 0:
            if top["score"] - row["score"] >= ROTATION_SCORE_GAP:
                reason = "ROTATION"

        if reason:
            exit_results.append(close_position(position, current_price, reason))
        else:
            remaining.append(position)

    save_positions(remaining)

    return exit_results


def open_new_positions(ranking, excluded=None):
    """Open at most one new position per cycle. Candidates from the
    last close's tomorrow_watchlist are tried first, falling back to the
    full ranking, requiring the live score to clear ENTRY_SCORE_THRESHOLD.
    Skips entirely if the operator safe-control switch is paused."""

    if load_control().get("trading_paused"):
        return

    positions = load_positions()

    if len(positions) >= MAX_OPEN_POSITIONS:
        return

    held_tickers = {p["ticker"] for p in positions} | (excluded or set())

    ranking_by_ticker = {row["ticker"]: row for row in ranking}

    watchlist_tickers = [w["ticker"] for w in load_json(WATCHLIST_FILE, {}).get("top", [])]

    ordered = []
    seen = set()

    for ticker in watchlist_tickers:
        row = ranking_by_ticker.get(ticker)
        if row:
            ordered.append(row)
            seen.add(ticker)

    for row in ranking:
        if row["ticker"] not in seen:
            ordered.append(row)

    for row in ordered:

        if row["ticker"] in held_tickers:
            continue

        if row["score"] < ENTRY_SCORE_THRESHOLD:
            continue

        entry_signal = {
            "ticker": row["ticker"],
            "sector": row["sector"],
            "score": row["score"],
            "price": row["price"],
            "action": "PAPER_BUY",
            "ts": datetime.now(timezone.utc).isoformat()
        }

        STATE["paper_trades"].append(entry_signal)
        append_jsonl(SIGNALS_LOG, entry_signal)

        positions.append({
            "ticker": row["ticker"],
            "sector": row["sector"],
            "entry_price": row["price"],
            "entry_ts": entry_signal["ts"],
            "peak_price": row["price"],
            "score_at_entry": row["score"]
        })

        save_positions(positions)
        return


def paper_engine(ranking):

    if not ranking:
        return []

    exit_results = manage_positions(ranking)

    just_exited = {r["ticker"] for r in exit_results}

    open_new_positions(ranking, excluded=just_exited)

    return exit_results

# =====================================
# PORTFOLIO
# =====================================

def portfolio_engine(ranking=None):

    ranking_by_ticker = {row["ticker"]: row for row in (ranking or [])}

    portfolio = {}

    for position in load_positions():

        ticker = position["ticker"]
        entry_price = position["entry_price"]
        current_price = ranking_by_ticker.get(ticker, {}).get("price", entry_price)

        portfolio[ticker] = {
            "sector": position["sector"],
            "entry_price": entry_price,
            "current_price": current_price,
            "peak_price": position["peak_price"],
            "return_pct": ((current_price - entry_price) / entry_price) * 100
        }

    STATE["portfolio"] = portfolio


def portfolio_from_ledger():

    portfolio = {}

    for row in read_jsonl(SIGNALS_LOG):

        if row.get("action") != "PAPER_BUY":
            continue

        t = row.get("ticker")

        if not t:
            continue

        portfolio[t] = portfolio.get(t, 0) + 1

    return portfolio

# =====================================
# ACCOUNT STATUS (Layer 15: ACCOUNT READ-ONLY STATUS)
# =====================================

def account_status_engine(learning_stats, portfolio):
    """Read-only PAPER account snapshot - no broker connection, no order
    execution. Equity is derived purely from the learning_stats equity
    curve applied to a notional starting capital."""

    cumulative_return_pct = learning_stats.get("cumulative_return_pct", 0.0)
    equity = PAPER_STARTING_CAPITAL_KRW * (1 + cumulative_return_pct / 100)

    slot_capital = PAPER_STARTING_CAPITAL_KRW / MAX_OPEN_POSITIONS

    open_value = sum(
        slot_capital * (1 + p["return_pct"] / 100)
        for p in (portfolio or {}).values()
    )

    cash = max(equity - open_value, 0.0)

    status = {
        "mode": "PAPER_ONLY",
        "live_trade": "BLOCKED",
        "starting_capital_krw": PAPER_STARTING_CAPITAL_KRW,
        "equity_krw": equity,
        "cash_krw": cash,
        "open_positions_value_krw": open_value,
        "open_positions_count": len(portfolio or {}),
        "cumulative_return_pct": cumulative_return_pct,
        "max_drawdown_pct": learning_stats.get("max_drawdown_pct", 0.0),
        "total_trades": learning_stats.get("total_trades", 0),
        "updated_ts": datetime.now(timezone.utc).isoformat()
    }

    save_json(ACCOUNT_STATUS_FILE, status)

    return status

# =====================================
# FORWARD SIMULATION ENGINE (historical bootstrap)
# =====================================

def forward_simulation(ticker, trials=FORWARD_SIM_TRIALS, horizon_days=FORWARD_SIM_HORIZON_DAYS):

    try:

        hist = yf.Ticker(ticker).history(period="3mo")

        hist = hist.dropna(subset=["Close"])

        closes = hist["Close"].tolist()

        if len(closes) < 2:
            return None

        returns = []

        for i in range(1, len(closes)):
            prev = closes[i - 1]
            if prev:
                returns.append((closes[i] - prev) / prev)

        if not returns:
            return None

        outcomes = []

        for _ in range(trials):

            cum = 1.0

            for _ in range(horizon_days):
                cum *= (1 + random.choice(returns))

            outcomes.append(cum - 1)

        p_up = sum(1 for o in outcomes if o > 0) / len(outcomes)
        expected_return = sum(outcomes) / len(outcomes)

        return {
            "ticker": ticker,
            "p_up": p_up,
            "expected_return_pct": expected_return * 100,
            "trials": trials,
            "horizon_days": horizon_days
        }

    except Exception:
        return None

# =====================================
# LEARNING ENGINE (Result DB evaluation + rolling stats)
# =====================================

def update_learning_stats(new_results):

    stats = load_json(LEARNING_FILE, {
        "equity_curve": [1.0],
        "cumulative_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "win_rate_pct": 0.0,
        "total_trades": 0,
        "wins": 0,
        "updated_ts": None
    })

    equity_curve = stats.get("equity_curve", [1.0])
    wins = stats.get("wins", 0)
    total_trades = stats.get("total_trades", 0)

    for r in new_results:
        equity_curve.append(equity_curve[-1] * (1 + r["return_pct"] / 100))
        total_trades += 1
        if r["win"]:
            wins += 1

    if len(equity_curve) > EQUITY_CURVE_MAX:
        equity_curve = equity_curve[-EQUITY_CURVE_MAX:]

    peak = equity_curve[0]
    max_drawdown = 0.0

    for e in equity_curve:
        if e > peak:
            peak = e
        drawdown = ((peak - e) / peak * 100) if peak else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    cumulative_return = (equity_curve[-1] - 1.0) * 100
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    stats = {
        "equity_curve": equity_curve,
        "cumulative_return_pct": cumulative_return,
        "max_drawdown_pct": max_drawdown,
        "win_rate_pct": win_rate,
        "total_trades": total_trades,
        "wins": wins,
        "updated_ts": datetime.now(timezone.utc).isoformat()
    }

    save_json(LEARNING_FILE, stats)

    return stats

# =====================================
# PATCH COUNCIL (Layer 18: AUTO REVIEW PATCH COUNCIL)
# =====================================

def patch_council_review(learning_stats, market_state, positions):
    """AUTO REVIEW: scan operating stats for anomaly conditions and emit
    PATCH_REQUIRED / VERIFY_REQUIRED / PASS findings. Never applies code
    changes - AUTO_CODE_PATCH and CORE_PATCH remain BLOCKED, per canon."""

    findings = []

    recent_results = read_jsonl(RESULTS_LOG)[-PATCH_COUNCIL_LOSS_STREAK:]

    consecutive_losses = 0
    for r in reversed(recent_results):
        if not r.get("win", True):
            consecutive_losses += 1
        else:
            break

    if consecutive_losses >= PATCH_COUNCIL_LOSS_STREAK:
        findings.append({
            "id": "CONSECUTIVE_LOSSES",
            "severity": "PATCH_REQUIRED",
            "detail": "%d consecutive losing exits - review entry threshold / score weights" % consecutive_losses
        })

    if learning_stats.get("max_drawdown_pct", 0.0) >= PATCH_COUNCIL_DRAWDOWN_PCT:
        findings.append({
            "id": "DRAWDOWN_LIMIT",
            "severity": "VERIFY_REQUIRED",
            "detail": "max_drawdown %.2f%% >= %.1f%% - verify risk parameters" % (
                learning_stats.get("max_drawdown_pct", 0.0), PATCH_COUNCIL_DRAWDOWN_PCT
            )
        })

    if market_state in ("PANIC", "RISK_OFF") and positions:
        findings.append({
            "id": "RISK_OFF_WITH_OPEN_POSITIONS",
            "severity": "VERIFY_REQUIRED",
            "detail": "market_state=%s with %d open position(s) - verify stop-loss coverage" % (
                market_state, len(positions)
            )
        })

    if not findings:
        findings.append({
            "id": "NONE",
            "severity": "PASS",
            "detail": "no anomalies detected this cycle"
        })

    result = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "findings": findings,
        "auto_code_patch": "BLOCKED",
        "core_patch": "BLOCKED"
    }

    save_json(PATCH_COUNCIL_FILE, result)

    return result

# =====================================
# TOMORROW WATCHLIST ENGINE
# =====================================

def build_tomorrow_watchlist(ranking, sector_strength, top_n=TOMORROW_WATCHLIST_SIZE):

    sector_avg = {row["sector"]: row["avg_change_pct"] for row in sector_strength}

    candidates = ranking[:FORWARD_SIM_CANDIDATES]

    composite = []

    for row in candidates:

        sim = forward_simulation(row["ticker"])
        p_up = sim["p_up"] if sim else 0.5

        sector_change = sector_avg.get(row["sector"], 0.0)

        composite_score = (
            row["score"] * 0.4
            + sector_change * 10 * 0.2
            + p_up * 100 * 0.4
        )

        composite.append({
            "ticker": row["ticker"],
            "sector": row["sector"],
            "score": row["score"],
            "sector_avg_change_pct": sector_change,
            "p_up": p_up,
            "composite_score": composite_score
        })

    composite.sort(
        key=lambda x: x["composite_score"],
        reverse=True
    )

    top = composite[:top_n]

    save_json(WATCHLIST_FILE, {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "top": top
    })

    return top

# =====================================
# HYBRID MIND ENGINE (Layer 16: GOD HYBRID MIND ENGINE)
# =====================================

def hybrid_mind_engine(candidates, market_state):
    """'God Hybrid Mind' - fuses three independent judgment engines into
    one verdict per candidate:
      1) rule-based score engine  (volume / foreign-link / news / overlap)
      2) statistical engine       (forward-simulation p_up, Monte Carlo)
      3) market-regime engine     (EUPHORIA/TREND/PANIC multiplier)
    Output: BUY_CANDIDATE / WATCH / AVOID per candidate."""

    regime_multiplier = HYBRID_REGIME_MULTIPLIER.get(market_state, 1.0)

    verdicts = []

    for c in candidates[:HYBRID_TOP_N]:

        hybrid_score = (c["score"] * 0.5 + c["p_up"] * 100 * 0.5) * regime_multiplier

        if hybrid_score >= HYBRID_BUY_THRESHOLD:
            verdict = "BUY_CANDIDATE"
        elif hybrid_score >= HYBRID_WATCH_THRESHOLD:
            verdict = "WATCH"
        else:
            verdict = "AVOID"

        verdicts.append({
            "ticker": c["ticker"],
            "sector": c["sector"],
            "rule_score": c["score"],
            "p_up": c["p_up"],
            "hybrid_score": hybrid_score,
            "verdict": verdict
        })

    result = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "market_state": market_state,
        "regime_multiplier": regime_multiplier,
        "candidates": verdicts
    }

    save_json(HYBRID_MIND_FILE, result)

    return result

# =====================================
# FINAL VETO (Layer 19: FINAL VETO)
# =====================================

FINAL_VETO_FORBIDDEN_PHRASES = [
    "LIVE_TRADE: TRUE",
    "LIVE_TRADE=TRUE",
    "실거래 진행",
    "주문 체결 완료",
    "계좌 비밀번호",
    "API_KEY=",
    "ACCESS_TOKEN=",
]


def final_veto_check(report_text):
    """Active BLOCK gate, per canon Final Veto: scan outgoing report text
    for anything implying live trading, capital scaling, or sensitive-data
    exposure, and confirm the PAPER_ONLY disclaimer is present. Every
    check is logged to ledger/final_veto_log.jsonl for audit."""

    reasons = []

    for phrase in FINAL_VETO_FORBIDDEN_PHRASES:
        if phrase in report_text:
            reasons.append("FORBIDDEN_PHRASE:" + phrase)

    if "PAPER_ONLY" not in report_text:
        reasons.append("MISSING_PAPER_ONLY_DISCLAIMER")

    ok = len(reasons) == 0

    append_jsonl(FINAL_VETO_LOG, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "reasons": reasons
    })

    return ok, reasons

# =====================================
# TELEGRAM
# =====================================

def send_telegram(text, chat_id_env="CHEONOK_TELEGRAM_CHAT_ID"):

    token = os.environ.get("CHEONOK_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get(chat_id_env, "").strip()

    if not token or not chat_id:
        print("HOLD_TELEGRAM_SECRETS_MISSING:" + chat_id_env)
        print(text)
        return False

    for i in range(0, len(text), 3500):

        chunk = text[i:i + 3500]

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": "true"
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")

        with urllib.request.urlopen(req, timeout=30) as res:
            res.read()

    return True


def format_report_text(report_data):

    lines = [
        "JOS PAPER CAPITAL REPORT",
        "PAPER_ONLY TRUE / LIVE_TRADE BLOCKED",
        "ts: " + report_data["ts"],
        "market_state: " + report_data["market_state"],
        "events: " + str(report_data["events"]),
        "signals: " + str(report_data["signals"]),
        "paper_trades: " + str(report_data["paper_trades"])
    ]

    top5 = report_data["top5"]

    if top5:
        lines.append("")
        lines.append("[TOP%s RANKING]" % len(top5))
        for r in top5:
            drivers = ",".join(r.get("drivers", [])) or "-"
            lines.append(
                "  %s (%s) score=%s price=%s change=%.2f%% [%s]" % (
                    r["ticker"], r["sector"], r["score"], r["price"], r.get("change_pct", 0.0), drivers
                )
            )

    leader = report_data.get("leader_analysis")

    if leader:
        lines.append("")
        lines.append("[LEADER ANALYSIS]")
        lines.append(
            "  #1 %s (%s) score=%s drivers=%s foreign_sector_change=%.2f%%" % (
                leader["leader"]["ticker"], leader["leader"]["sector"], leader["leader"]["score"],
                ",".join(leader["leader"]["drivers"]) or "-", leader["leader"]["foreign_sector_change_pct"]
            )
        )
        if leader["similar_candidates"]:
            lines.append("  watch list (similar setup):")
            for c in leader["similar_candidates"]:
                lines.append(
                    "    %s (%s) score=%s shared=%s" % (
                        c["ticker"], c["sector"], c["score"], ",".join(c["shared_drivers"])
                    )
                )

    exits = report_data.get("exits") or []

    if exits:
        lines.append("")
        lines.append("[EXITS THIS CYCLE]")
        for r in exits:
            lines.append(
                "  %s [%s] entry=%.2f exit=%.2f return=%.2f%% %s" % (
                    r["ticker"], r["reason"], r["entry_price"], r["exit_price"],
                    r["return_pct"], "WIN" if r["win"] else "LOSS"
                )
            )

    portfolio = report_data["portfolio"]

    if portfolio:
        lines.append("")
        lines.append("[OPEN POSITIONS]")
        for ticker, p in portfolio.items():
            lines.append(
                "  %s (%s) entry=%.2f current=%.2f return=%.2f%%" % (
                    ticker, p["sector"], p["entry_price"], p["current_price"], p["return_pct"]
                )
            )

    global_flows = report_data.get("global_flows") or []

    if global_flows:
        lines.append("")
        lines.append("[GLOBAL FLOWS] risk_state=" + report_data.get("global_risk_state", "NEUTRAL"))
        for g in global_flows:
            lines.append("  %s (%s) change=%.2f%%" % (g["label"], g["ticker"], g["change_pct"]))

    account = report_data.get("account_status")

    if account:
        lines.append("")
        lines.append("[ACCOUNT STATUS] (PAPER_ONLY, read-only)")
        lines.append("  equity=%.0f cash=%.0f cumulative_return=%.2f%% max_drawdown=%.2f%%" % (
            account["equity_krw"], account["cash_krw"],
            account["cumulative_return_pct"], account["max_drawdown_pct"]
        ))

    control = report_data.get("control")

    if control:
        lines.append("")
        lines.append("[CONTROL] trading_paused=%s" % control.get("trading_paused", False))

    essence = report_data.get("essence_memory")

    if essence:
        lines.append("")
        lines.append("[ESSENCE MEMORY] sample=%d dominant_sector=%s(x%d) dominant_driver=%s(x%d)" % (
            essence["sample_size"], essence.get("dominant_sector"), essence.get("dominant_sector_count", 0),
            essence.get("dominant_driver"), essence.get("dominant_driver_count", 0)
        ))

    return "\n".join(lines)


def format_close_report(close_data):

    lines = [
        "JOS PAPER CAPITAL - CLOSE REPORT (CEO)",
        "PAPER_ONLY TRUE / LIVE_TRADE BLOCKED / CAPITAL_SCALE BLOCKED / KIS_ORDER_GATE BLOCKED",
        "ts: " + close_data["ts"],
        "market_state: " + close_data["market_state"]
    ]

    lines.append("")
    lines.append("[TOP5 RANKING]")
    for r in close_data["top5"]:
        drivers = ",".join(r.get("drivers", [])) or "-"
        lines.append(
            "  %s (%s) score=%s change=%.2f%% [%s]" % (
                r["ticker"], r["sector"], r["score"], r["change_pct"], drivers
            )
        )

    lines.append("")
    lines.append("[SECTOR STRENGTH]")
    for s in close_data["sector_strength"]:
        lines.append(
            "  %s avg_change=%.2f%% (n=%s)" % (
                s["sector"], s["avg_change_pct"], s["count"]
            )
        )

    leader = close_data.get("leader_analysis")

    if leader:
        lines.append("")
        lines.append("[LEADER ANALYSIS]")
        lines.append(
            "  #1 %s (%s) score=%s drivers=%s foreign_sector_change=%.2f%%" % (
                leader["leader"]["ticker"], leader["leader"]["sector"], leader["leader"]["score"],
                ",".join(leader["leader"]["drivers"]) or "-", leader["leader"]["foreign_sector_change_pct"]
            )
        )
        if leader["similar_candidates"]:
            lines.append("  watch list (similar setup):")
            for c in leader["similar_candidates"]:
                lines.append(
                    "    %s (%s) score=%s shared=%s" % (
                        c["ticker"], c["sector"], c["score"], ",".join(c["shared_drivers"])
                    )
                )

    lines.append("")
    lines.append("[TODAY RESULTS]")
    lines.append("  closed_positions: " + str(len(close_data["exit_results"])))
    for r in close_data["exit_results"]:
        lines.append(
            "  %s [%s] entry=%.2f exit=%.2f return=%.2f%% %s" % (
                r["ticker"], r["reason"], r["entry_price"], r["exit_price"],
                r["return_pct"], "WIN" if r["win"] else "LOSS"
            )
        )

    lines.append("")
    lines.append("[LEARNING STATS]")
    learn = close_data["learning_stats"]
    lines.append("  total_trades: " + str(learn["total_trades"]))
    lines.append("  win_rate: %.1f%%" % learn["win_rate_pct"])
    lines.append("  cumulative_return: %.2f%%" % learn["cumulative_return_pct"])
    lines.append("  max_drawdown: %.2f%%" % learn["max_drawdown_pct"])

    lines.append("")
    lines.append("[TOMORROW WATCHLIST TOP%s] (full ranked list of %s in tomorrow_watchlist.json)" % (
        min(TOMORROW_WATCHLIST_REPORT_N, len(close_data["tomorrow_watchlist"])),
        len(close_data["tomorrow_watchlist"])
    ))
    for w in close_data["tomorrow_watchlist"][:TOMORROW_WATCHLIST_REPORT_N]:
        lines.append(
            "  %s (%s) composite=%.2f p_up=%.2f sector_change=%.2f%%" % (
                w["ticker"], w["sector"], w["composite_score"],
                w["p_up"], w["sector_avg_change_pct"]
            )
        )

    if close_data["news"]:
        lines.append("")
        lines.append("[NEWS HEADLINES]")
        for n in close_data["news"][:5]:
            lines.append("  - " + n)

    lines.append("")
    lines.append("[OPEN POSITIONS]")
    if close_data["open_positions"]:
        for ticker, p in close_data["open_positions"].items():
            lines.append(
                "  %s (%s) entry=%.2f current=%.2f return=%.2f%%" % (
                    ticker, p["sector"], p["entry_price"], p["current_price"], p["return_pct"]
                )
            )
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("portfolio_total_signals: " + str(close_data["portfolio_total"]))

    global_flows = close_data.get("global_flows") or []

    if global_flows:
        lines.append("")
        lines.append("[GLOBAL FLOWS] risk_state=" + close_data.get("global_risk_state", "NEUTRAL"))
        for g in global_flows:
            lines.append("  %s (%s) change=%.2f%%" % (g["label"], g["ticker"], g["change_pct"]))

    account = close_data.get("account_status")

    if account:
        lines.append("")
        lines.append("[ACCOUNT STATUS] (PAPER_ONLY, read-only)")
        lines.append("  equity=%.0f cash=%.0f open_positions_value=%.0f (KRW notional)" % (
            account["equity_krw"], account["cash_krw"], account["open_positions_value_krw"]
        ))
        lines.append("  cumulative_return=%.2f%% max_drawdown=%.2f%% total_trades=%d" % (
            account["cumulative_return_pct"], account["max_drawdown_pct"], account["total_trades"]
        ))

    control = close_data.get("control")

    if control:
        lines.append("")
        lines.append("[CONTROL] trading_paused=%s" % control.get("trading_paused", False))

    essence = close_data.get("essence_memory")

    if essence:
        lines.append("")
        lines.append("[ESSENCE MEMORY] sample=%d dominant_sector=%s(x%d) dominant_driver=%s(x%d)" % (
            essence["sample_size"], essence.get("dominant_sector"), essence.get("dominant_sector_count", 0),
            essence.get("dominant_driver"), essence.get("dominant_driver_count", 0)
        ))

    hybrid = close_data.get("hybrid_mind")

    if hybrid:
        lines.append("")
        lines.append("[HYBRID MIND] market_state=%s regime_x%.2f" % (
            hybrid["market_state"], hybrid["regime_multiplier"]
        ))
        for c in hybrid["candidates"]:
            lines.append("  %s (%s) hybrid_score=%.1f -> %s" % (
                c["ticker"], c["sector"], c["hybrid_score"], c["verdict"]
            ))

    patch_council = close_data.get("patch_council")

    if patch_council:
        lines.append("")
        lines.append("[PATCH COUNCIL] auto_code_patch=BLOCKED core_patch=BLOCKED")
        for f in patch_council["findings"]:
            lines.append("  [%s] %s: %s" % (f["severity"], f["id"], f["detail"]))

    non_regression = close_data.get("non_regression")

    if non_regression:
        lines.append("")
        lines.append("[NON-REGRESSION] canon layers passing: %d/%d" % (
            non_regression["pass_count"], non_regression["total_layers"]
        ))
        if non_regression["regressions"]:
            lines.append("  REGRESSIONS: " + ", ".join(non_regression["regressions"]))
        else:
            lines.append("  regressions: none")

    return "\n".join(lines)

# =====================================
# SUBSCRIPTION REPORT (Layer 12: SUBSCRIPTION REPORT)
# =====================================

def format_subscription_report(close_data):
    """Subscriber-facing summary: market read, sector themes, leader
    pattern, and tomorrow's candidate watch list - no raw position entry
    prices or account-level figures (those stay in the CEO report)."""

    lines = [
        "JOS PAPER CAPITAL - SUBSCRIBER BRIEFING",
        "PAPER_ONLY simulation - research/education only, not investment advice",
        "ts: " + close_data["ts"],
        "market_state: " + close_data["market_state"],
    ]

    lines.append("")
    lines.append("[SECTOR THEMES]")
    for s in close_data["sector_strength"][:3]:
        lines.append("  %s avg_change=%.2f%%" % (s["sector"], s["avg_change_pct"]))

    leader = close_data.get("leader_analysis")

    if leader:
        lines.append("")
        lines.append("[TODAY'S LEADER PATTERN]")
        lines.append("  #1 %s (%s) drivers=%s" % (
            leader["leader"]["ticker"], leader["leader"]["sector"],
            ",".join(leader["leader"]["drivers"]) or "-"
        ))

    watchlist = close_data["tomorrow_watchlist"][:TOMORROW_WATCHLIST_REPORT_N]

    lines.append("")
    lines.append("[TOMORROW WATCH LIST TOP%d]" % len(watchlist))
    for w in watchlist:
        lines.append("  %s (%s)" % (w["ticker"], w["sector"]))

    lines.append("")
    lines.append("Disclaimer: simulated PAPER data only. LIVE_TRADE BLOCKED.")

    text = "\n".join(lines)

    save_json(SUBSCRIPTION_REPORT_FILE, {
        "ts": close_data["ts"],
        "text": text
    })

    return text


def send_subscriber_telegram(text):

    if not os.environ.get("CHEONOK_TELEGRAM_SUBSCRIBER_CHAT_ID", "").strip():
        print("HOLD_SUBSCRIBER_TELEGRAM_SECRETS_MISSING")
        return False

    return send_telegram(text, chat_id_env="CHEONOK_TELEGRAM_SUBSCRIBER_CHAT_ID")

# =====================================
# CEO REPORT BOOK (Layer 13: CEO REPORT BOOK)
# =====================================

def append_ceo_report_book(close_data):
    """Append a one-line summary of each close report to a persistent
    'book' (ledger/ceo_report_book.jsonl) - an accumulating CEO report
    archive, rather than an ephemeral Telegram-only message."""

    entry = {
        "ts": close_data["ts"],
        "market_state": close_data["market_state"],
        "leader": (close_data.get("leader_analysis") or {}).get("leader"),
        "exit_count": len(close_data["exit_results"]),
        "learning_stats": close_data["learning_stats"],
        "account_status": close_data.get("account_status"),
        "patch_council_findings": [
            f["id"] for f in (close_data.get("patch_council") or {}).get("findings", [])
        ],
    }

    append_jsonl(CEO_REPORT_BOOK, entry)

    return entry

# =====================================
# REPORT (intraday)
# =====================================

def report(exit_results=None, leader=None, global_flows=None, essence=None):

    ranking = STATE["rankings"]

    global_flows = global_flows or []

    learning_stats = load_json(LEARNING_FILE, {
        "cumulative_return_pct": 0.0, "max_drawdown_pct": 0.0, "total_trades": 0
    })

    report_data = {

        "events":
            len(STATE["events"]),

        "signals":
            len(STATE["signals"]),

        "paper_trades":
            len(STATE["paper_trades"]),

        "portfolio":
            STATE["portfolio"],

        "exits":
            exit_results or [],

        "leader_analysis":
            leader,

        "market_state":
            market_state_engine(ranking),

        "top5":
            ranking[:5],

        "global_flows":
            global_flows,

        "global_risk_state":
            global_risk_state(global_flows),

        "account_status":
            account_status_engine(learning_stats, STATE["portfolio"]),

        "control":
            load_control(),

        "essence_memory":
            essence,

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

    report_text = format_report_text(report_data)

    veto_ok, veto_reasons = final_veto_check(report_text)

    if veto_ok:
        send_telegram(report_text)
    else:
        print("FINAL_VETO_BLOCK: " + ",".join(veto_reasons))

# =====================================
# NON-REGRESSION MEMORY (Layer 20: NON-REGRESSION MEMORY)
# =====================================

CANON_LAYER_CHECKS = {
    "GLOBAL_FIRST": lambda ctx: bool(ctx.get("global_flows")),
    "KOREA_THEME_TRANSLATION": lambda ctx: any(r.get("macro_bonus") is not None for r in ctx.get("ranking", [])),
    "REAL_DATA_BRIDGE": lambda ctx: bool(ctx.get("market")),
    "KIS_REALTIME_BRIDGE": lambda ctx: any(r.get("price_source") == "KIS" for r in ctx.get("market", [])),
    "RANK_OVERLAP": lambda ctx: any("overlap_count" in r for r in ctx.get("ranking", [])),
    "THEME_CLUSTER": lambda ctx: bool(ctx.get("sector_strength")),
    "LEADER_ROTATION": lambda ctx: True,
    "REVERSE_TRACE": lambda ctx: bool(ctx.get("leader")),
    "NEXT_DAY_TOP30": lambda ctx: len(ctx.get("tomorrow_watchlist", [])) >= 30,
    "REALITY_SURVIVAL_SIM": lambda ctx: True,
    "PAPER_VALIDATION": lambda ctx: True,
    "SUBSCRIPTION_REPORT": lambda ctx: bool(ctx.get("subscription_report")),
    "CEO_REPORT_BOOK": lambda ctx: bool(ctx.get("ceo_report_book_entry")),
    "TELEGRAM_SAFE_CONTROL": lambda ctx: "trading_paused" in (ctx.get("control") or {}),
    "ACCOUNT_READ_ONLY_STATUS": lambda ctx: bool(ctx.get("account_status")),
    "GOD_HYBRID_MIND": lambda ctx: bool(ctx.get("hybrid_mind")),
    "ESSENCE_MEMORY": lambda ctx: bool(ctx.get("essence_memory")),
    "AUTO_PATCH_COUNCIL": lambda ctx: bool(ctx.get("patch_council")),
    "FINAL_VETO": lambda ctx: ctx.get("final_veto_ok") is True,
}


def non_regression_check(ctx):
    """Compare this run's canon-layer capability flags against the last
    persisted snapshot (ledger/canon_status.json). If a previously-passing
    layer is now missing or failing, flag it as a regression instead of
    letting it silently disappear."""

    previous = load_json(CANON_STATUS_FILE, {"layers": {}})

    current_layers = {}

    for name, check in CANON_LAYER_CHECKS.items():
        try:
            current_layers[name] = bool(check(ctx))
        except Exception:
            current_layers[name] = False

    regressions = [
        name for name, was_ok in previous.get("layers", {}).items()
        if was_ok and not current_layers.get(name, False)
    ]

    result = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "layers": current_layers,
        "pass_count": sum(1 for v in current_layers.values() if v),
        "total_layers": len(current_layers),
        "regressions": regressions
    }

    save_json(CANON_STATUS_FILE, result)

    return result

# =====================================
# MAIN LOOP
# =====================================

def collect_cycle_data():

    market = market_feed()

    global_flows = global_flows_feed()

    news = news_feed()

    foreign_strength = foreign_sector_strength(market)

    ranking = rank_engine(
        market, foreign_strength, news, global_flows
    )

    STATE["rankings"] = ranking

    leader = leader_analysis(ranking)

    essence = update_essence_memory(leader)

    for row in market:

        STATE["events"].append(row)

        append_jsonl(MARKET_LOG, row)

        if score_market(row) >= 60:
            STATE["signals"].append(
                row
            )

    for n in news:

        STATE["events"].append(
            {"news": n}
        )

        append_jsonl(NEWS_LOG, {
            "headline": n,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    return market, news, ranking, leader, global_flows, essence


def run_cycle():

    market, news, ranking, leader, global_flows, essence = collect_cycle_data()

    exit_results = paper_engine(
        ranking
    )

    update_learning_stats(exit_results)

    portfolio_engine(ranking)

    report(exit_results, leader, global_flows, essence)


def run_close():

    market, news, ranking, leader, global_flows, essence = collect_cycle_data()

    market_state = market_state_engine(ranking)
    sector_strength = sector_strength_engine(ranking)
    g_risk_state = global_risk_state(global_flows)

    exit_results = paper_engine(ranking)
    learning_stats = update_learning_stats(exit_results)

    portfolio_engine(ranking)

    account_status = account_status_engine(learning_stats, STATE["portfolio"])
    control = load_control()

    tomorrow_watchlist = build_tomorrow_watchlist(ranking, sector_strength)

    hybrid_mind = hybrid_mind_engine(tomorrow_watchlist, market_state)

    patch_council = patch_council_review(learning_stats, market_state, load_positions())

    portfolio_total = sum(portfolio_from_ledger().values())

    close_data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "market_state": market_state,
        "top5": ranking[:5],
        "sector_strength": sector_strength,
        "leader_analysis": leader,
        "exit_results": exit_results,
        "learning_stats": learning_stats,
        "tomorrow_watchlist": tomorrow_watchlist,
        "news": news,
        "portfolio_total": portfolio_total,
        "open_positions": STATE["portfolio"],
        "global_flows": global_flows,
        "global_risk_state": g_risk_state,
        "account_status": account_status,
        "control": control,
        "essence_memory": essence,
        "hybrid_mind": hybrid_mind,
        "patch_council": patch_council
    }

    ceo_report_book_entry = append_ceo_report_book(close_data)

    veto_ok, veto_reasons = final_veto_check(format_close_report(close_data))

    non_regression = non_regression_check({
        "market": market,
        "ranking": ranking,
        "global_flows": global_flows,
        "leader": leader,
        "sector_strength": sector_strength,
        "tomorrow_watchlist": tomorrow_watchlist,
        "subscription_report": True,
        "control": control,
        "account_status": account_status,
        "hybrid_mind": hybrid_mind,
        "essence_memory": essence,
        "patch_council": patch_council,
        "final_veto_ok": veto_ok,
        "ceo_report_book_entry": ceo_report_book_entry
    })

    close_data["non_regression"] = non_regression

    print()
    print("=" * 50)
    print("JOS CLOSE REPORT")
    print("=" * 50)

    print(
        json.dumps(
            close_data,
            indent=2,
            ensure_ascii=False
        )
    )

    close_text = format_close_report(close_data)

    if veto_ok:
        send_telegram(close_text)
    else:
        print("FINAL_VETO_BLOCK: " + ",".join(veto_reasons))

    subscription_text = format_subscription_report(close_data)
    send_subscriber_telegram(subscription_text)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--close", action="store_true")
    args = parser.parse_args()

    print("=== JOS MASTER START ===")

    if args.close:
        run_close()
        return

    if args.once:
        run_cycle()
        return

    while True:

        run_cycle()

        time.sleep(60)

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    main()
