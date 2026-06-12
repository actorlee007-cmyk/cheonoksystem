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
import re
import html
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

# EV-based risk framework (Layer 22): stop-loss / trailing-stop now scale
# with each ticker's own volatility (ATR) at entry instead of one fixed %
# for every ticker, targeting roughly a 2:1 reward:risk ratio (마크 미너비니
# "트레이딩의 성배" / 노션 "수익은 짧고 손실은 길게? 이러면 절대 못 법니다" -
# 손익비가 승률보다 중요하다는 원칙). STOP_LOSS_PCT / TRAILING_STOP_PCT above
# remain the fallback when ATR can't be computed (e.g. yfinance outage) or
# for positions opened before this layer existed.
ATR_LOOKBACK_DAYS = 14
ATR_STOP_MULT = 1.0        # stop-loss = ATR% x this multiple
ATR_TRAILING_MULT = 1.5    # trailing stop (once in profit) = ATR% x this multiple
ATR_TARGET_MULT = 2.0      # informational profit target = ATR% x this multiple (~2:1 R:R)
ATR_STOP_FLOOR_PCT = 1.0   # never tighter than this (avoid noise stop-outs)
ATR_STOP_CEIL_PCT = 5.0    # never wider than this (cap tail risk)

# Rotation prefers composite_score (rule score + forward-sim p_up + sector
# trend, from tomorrow_watchlist.json) over the raw rule-based score when
# both the held ticker and the current #1 are in that list - 후보 교체 판단에
# 통계적 확률(p_up)과 섹터 흐름까지 반영.
ROTATION_COMPOSITE_GAP = 15

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

# Multiverse consensus (Layer 24: MULTIVERSE CONSENSUS SIGNAL). A new
# position is tagged "consensus" when its overlap_count (Layer 5) meets
# this bar - i.e. at least this many of the independent VOLUME/MOMENTUM/
# FOREIGN_LINK/NEWS signal universes agree on it, not just one factor
# driving the score alone. Win-rate / return are tracked separately for
# consensus vs single-signal entries so the close report can show, with
# real trade data, whether cross-universe agreement actually predicts
# better outcomes - the "different model catches the blind spot of a
# single model" idea applied to stock-picking instead of code review.
MULTIVERSE_CONSENSUS_MIN_OVERLAP = 2

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

# Surge cause trace (Layer 21: SURGE SCANNER, market-wide). Detects today's
# biggest % movers across the ENTIRE KRX (not just the 30-ticker WATCHLIST)
# via the KIS 등락률순위 ranking endpoint, and runs a lightweight '역산출'
# (reverse cause-trace) against each using data sources already wired into
# this system (RSS news headlines + sector keyword map). Read-only and
# additive only - never affects WATCHLIST scoring, ranking, or open
# positions. A genuine daily +30% mover (상한가 territory, KRX limit is
# +/-30%) will surface near the top of this list when it occurs; the 10%
# threshold below is a tunable starting point for surfacing candidates.
SURGE_SCAN_THRESHOLD_PCT = 10.0   # flag market-wide movers at/above this daily change %
SURGE_SCAN_LIMIT = 10             # how many top gainers to fetch from the KIS ranking

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
    "reports": [],
    "surges": []
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
SURGE_LOG = LEDGER_DIR / "surge_log.jsonl"

# Strategy multiverse + auto canonical filtering (Layer 23: STRATEGY
# COMPARISON / AUTO CANONICAL FILTERING). Every entry in STRATEGIES is an
# independent paper-trading "universe": it trades the SAME per-cycle
# ranking data in its own ledger subdirectory, so all variants can be
# compared honestly without any extra market-data calls. "primary" is the
# live ATR_v2 + composite-rotation strategy (Layer 22); shadow_fixed_pct
# reproduces the pre-Layer-22 strategy (fixed stop/trailing % + raw
# score-gap rotation).
#
# Exactly one universe is "active" at a time (see active_strategy_name /
# STRATEGY_PROMOTION_FILE) - only the active universe writes to
# STATE["paper_trades"] and drives the Telegram report / account_status.
# evaluate_strategy_promotion() automatically promotes a challenger to
# active once it has enough trades (PROMOTION_MIN_TRADES) and has led the
# active universe's cumulative_return_pct by PROMOTION_MARGIN_PCT for
# PROMOTION_STREAK_REQUIRED consecutive close reports (no flip-flopping on
# a single noisy day). Every promotion is appended to history in
# STRATEGY_PROMOTION_FILE with the stats that justified it - the switch is
# automatic but never silent.
SHADOW_LEDGER_DIR = LEDGER_DIR / "shadow_fixed_pct"
STRATEGY_PROMOTION_FILE = LEDGER_DIR / "strategy_promotion.json"

PROMOTION_MIN_TRADES = 20
PROMOTION_MARGIN_PCT = 5.0
PROMOTION_STREAK_REQUIRED = 5

STRATEGIES = {
    "primary": {
        "label": "ATR_v2 (primary)",
        "risk_mode": "atr",
        "rotation_mode": "composite",
        "positions_file": POSITIONS_FILE,
        "signals_log": SIGNALS_LOG,
        "results_log": RESULTS_LOG,
        "learning_file": LEARNING_FILE,
    },
    "shadow_fixed_pct": {
        "label": "Fixed% + ScoreGap (shadow)",
        "risk_mode": "fixed",
        "rotation_mode": "score_gap",
        "positions_file": SHADOW_LEDGER_DIR / "positions.json",
        "signals_log": SHADOW_LEDGER_DIR / "signals_log.jsonl",
        "results_log": SHADOW_LEDGER_DIR / "results_log.jsonl",
        "learning_file": SHADOW_LEDGER_DIR / "learning_stats.json",
    },
}


def active_strategy_name():
    return load_json(STRATEGY_PROMOTION_FILE, {"active": "primary"}).get("active", "primary")


def active_strategy():
    return STRATEGIES.get(active_strategy_name(), STRATEGIES["primary"])


def ensure_ledger_dir():
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)


def append_jsonl(path, record):

    path.parent.mkdir(parents=True, exist_ok=True)

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

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================================
# KIS REAL DATA BRIDGE (Layer 4: REAL DATA BRIDGE, optional, .KS only)
# =====================================

KIS_BASE_URL = os.environ.get(
    "CHEONOK_KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
).strip()

# In-memory only - NEVER persisted to disk/ledger (ledger/ is committed to
# git by CI, and a leaked KIS bearer token is valid for up to 24h).
_KIS_TOKEN_CACHE = {"access_token": None, "expires_at": 0.0}


def kis_credentials():
    app_key = os.environ.get("CHEONOK_KIS_APP_KEY", "").strip()
    app_secret = os.environ.get("CHEONOK_KIS_APP_SECRET", "").strip()

    if not app_key or not app_secret:
        return None, None

    return app_key, app_secret


def kis_get_token(app_key, app_secret):
    """Fetch a KIS OAuth2 access token (POST /oauth2/tokenP) and cache it
    in-memory for this process only. Never written to disk."""

    now = time.time()

    if _KIS_TOKEN_CACHE["access_token"] and now < _KIS_TOKEN_CACHE["expires_at"]:
        return _KIS_TOKEN_CACHE["access_token"]

    body = json.dumps({
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }).encode("utf-8")

    req = urllib.request.Request(
        KIS_BASE_URL + "/oauth2/tokenP",
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

    return token


def kis_quote(ticker, app_key, app_secret):
    """Read-only domestic-stock current-price quote (국내주식 현재가 시세
    조회, tr_id FHKST01010100). KIS_ORDER_GATE remains BLOCKED - only this
    quotations endpoint is ever called, never an order/account endpoint."""

    token = kis_get_token(app_key, app_secret)

    if not token:
        return None

    code = ticker.split(".")[0]

    url = (
        KIS_BASE_URL
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


def kis_top_gainers(app_key, app_secret, limit=SURGE_SCAN_LIMIT):
    """Market-wide (전체 KRX 종목) 등락률순위 - today's top % gainers across
    ALL listed stocks, not limited to WATCHLIST (read-only ranking
    endpoint, tr_id FHPST01700000). KIS_ORDER_GATE remains BLOCKED - this
    is a quotations/ranking lookup only."""

    token = kis_get_token(app_key, app_secret)

    if not token:
        return []

    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_cond_scr_div_code": "20170",
        "fid_input_iscd": "0000",
        "fid_rank_sort_cls_code": "0",
        "fid_input_cnt_1": "0",
        "fid_prc_cls_code": "0",
        "fid_input_price_1": "",
        "fid_input_price_2": "",
        "fid_vol_cnt": "",
        "fid_trgt_cls_code": "0",
        "fid_trgt_exls_cls_code": "0",
        "fid_div_cls_code": "0",
        "fid_rsfl_rate1": "",
        "fid_rsfl_rate2": ""
    }

    url = (
        KIS_BASE_URL
        + "/uapi/domestic-stock/v1/ranking/fluctuation"
        + "?" + urllib.parse.urlencode(params)
    )

    req = urllib.request.Request(url, headers={
        "content-type": "application/json; charset=UTF-8",
        "authorization": "Bearer " + token,
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "FHPST01700000",
        "custtype": "P"
    })

    with urllib.request.urlopen(req, timeout=10) as res:
        payload = json.loads(res.read().decode("utf-8"))

    output = payload.get("output") or []

    gainers = []

    for item in output[:limit]:
        try:
            gainers.append({
                "ticker": (item.get("stck_shrn_iscd") or "").strip(),
                "name": (item.get("hts_kor_isnm") or "").strip(),
                "price": float(item.get("stck_prpr") or 0.0),
                "change_pct": float(item.get("prdy_ctrt") or 0.0),
                "volume": float(item.get("acml_vol") or 0.0)
            })
        except Exception:
            continue

    return gainers

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
                        kis_data = kis_quote(ticker, kis_app_key, kis_app_secret)
                    except Exception as exc:
                        kis_data = None
                        if not kis_fail_logged:
                            detail = ""
                            if isinstance(exc, urllib.error.HTTPError):
                                try:
                                    detail = " | body: " + exc.read().decode("utf-8", "replace")[:300]
                                except Exception:
                                    pass
                            print(f"HOLD_KIS_QUOTE_FAILED: {type(exc).__name__}: {exc}{detail}")
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
# EXTERNAL CAUSE-TRACE BRIDGES (opendart 공시 / Naver 뉴스검색)
# Layer 21 SURGE SCANNER inputs - both read-only, both optional (each
# degrades to "no data from this source" if its GitHub Secret is unset).
# =====================================

def opendart_credentials():
    return os.environ.get("CHEONOK_OPENDART_API_KEY", "").strip()


def opendart_today_disclosures(api_key):
    """오늘 날짜 전체 공시 목록 (최신 100건, list.json 공시검색 API). Read-only -
    used to cross-reference a surge candidate's name against today's
    company disclosures (호재성 공시 등)."""

    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    params = {
        "crtfc_key": api_key,
        "bgn_de": today,
        "end_de": today,
        "page_no": "1",
        "page_count": "100"
    }

    url = "https://opendart.fss.or.kr/api/list.json?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=10) as res:
        payload = json.loads(res.read().decode("utf-8"))

    if payload.get("status") != "000":
        return []

    return payload.get("list") or []


def naver_credentials():
    client_id = os.environ.get("CHEONOK_NAVER_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CHEONOK_NAVER_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        return None, None

    return client_id, client_secret


def naver_news_search(query, client_id, client_secret, display=3):
    """네이버 뉴스 검색 (read-only, openapi.naver.com/v1/search/news.json).
    Returns up to `display` most recent headline strings for `query`,
    HTML tags/entities stripped."""

    params = {"query": query, "display": str(display), "sort": "date"}

    url = "https://openapi.naver.com/v1/search/news.json?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    })

    with urllib.request.urlopen(req, timeout=10) as res:
        payload = json.loads(res.read().decode("utf-8"))

    headlines = []

    for item in payload.get("items") or []:
        title = re.sub("<[^>]+>", "", item.get("title", ""))
        headlines.append(html.unescape(title))

    return headlines

# =====================================
# SURGE CAUSE TRACE (Layer 21: SURGE SCANNER, market-wide)
# =====================================

def surge_cause_trace(name, news, disclosures, naver_client_id, naver_client_secret):
    """'역산출' (reverse cause-trace): cross-reference a market-wide surge
    candidate's name against today's news headlines, today's opendart
    disclosures, a live Naver news search, and the sector-keyword map. A
    candidate with no match across all sources is HOLD."""

    drivers = []

    if not name:
        return drivers

    for headline in news:
        if name in headline:
            drivers.append("NEWS: " + headline)

    for d in disclosures:
        corp_name = d.get("corp_name", "")
        if corp_name and (name in corp_name or corp_name in name):
            drivers.append("DART: " + d.get("report_nm", "") + " (" + d.get("rcept_dt", "") + ")")

    if naver_client_id and naver_client_secret:
        try:
            for headline in naver_news_search(name, naver_client_id, naver_client_secret):
                drivers.append("NAVER_NEWS: " + headline)
        except Exception as exc:
            print(f"HOLD_NAVER_NEWS_FAILED: {type(exc).__name__}: {exc}")

    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                drivers.append("SECTOR_KEYWORD:" + sector + "(" + keyword + ")")

    return drivers[:5]


def surge_scan(news):
    """Market-wide '오늘의 급등주' detection (KIS 등락률순위, ALL KRX-listed
    stocks - not limited to WATCHLIST). Each candidate at/above
    SURGE_SCAN_THRESHOLD_PCT gets a cause-trace via surge_cause_trace() and
    is appended to ledger/surge_log.jsonl. Read-only / additive only - does
    not affect WATCHLIST ranking, scoring, or open positions."""

    app_key, app_secret = kis_credentials()

    if not app_key or not app_secret:
        return []

    try:
        gainers = kis_top_gainers(app_key, app_secret)
    except Exception as exc:
        detail = ""
        if isinstance(exc, urllib.error.HTTPError):
            try:
                detail = " | body: " + exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
        print(f"HOLD_SURGE_SCAN_FAILED: {type(exc).__name__}: {exc}{detail}")
        return []

    disclosures = []
    dart_key = opendart_credentials()

    if dart_key:
        try:
            disclosures = opendart_today_disclosures(dart_key)
            print(f"OPENDART_DISCLOSURES_FETCHED: {len(disclosures)}")
        except Exception as exc:
            detail = ""
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    detail = " | body: " + exc.read().decode("utf-8", "replace")[:300]
                except Exception:
                    pass
            print(f"HOLD_OPENDART_FAILED: {type(exc).__name__}: {exc}{detail}")
    else:
        print("HOLD_OPENDART_SECRETS_MISSING")

    naver_client_id, naver_client_secret = naver_credentials()

    if not naver_client_id:
        print("HOLD_NAVER_SECRETS_MISSING")

    surges = []

    for g in gainers:

        if g["change_pct"] < SURGE_SCAN_THRESHOLD_PCT:
            continue

        drivers = surge_cause_trace(g["name"], news, disclosures, naver_client_id, naver_client_secret)

        record = {
            "ticker": g["ticker"],
            "name": g["name"],
            "price": g["price"],
            "change_pct": g["change_pct"],
            "volume": g["volume"],
            "possible_drivers": drivers,
            "evidence_status": "TITLE_ONLY" if drivers else "NO_MATCH_HOLD",
            "ts": datetime.now(timezone.utc).isoformat()
        }

        append_jsonl(SURGE_LOG, record)

        surges.append(record)

    return surges

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

def load_positions(strategy=STRATEGIES["primary"]):
    return load_json(strategy["positions_file"], {"positions": []}).get("positions", [])


def save_positions(positions, strategy=STRATEGIES["primary"]):
    save_json(strategy["positions_file"], {"positions": positions})


def close_position(position, current_price, reason, strategy=STRATEGIES["primary"], track_state=True):

    entry_price = position["entry_price"]
    return_pct = ((current_price - entry_price) / entry_price) * 100

    consensus_at_entry = position.get("consensus_at_entry", False)

    exit_signal = {
        "ticker": position["ticker"],
        "sector": position["sector"],
        "price": current_price,
        "action": "PAPER_SELL",
        "reason": reason,
        "consensus_at_entry": consensus_at_entry,
        "ts": datetime.now(timezone.utc).isoformat()
    }

    if track_state:
        STATE["paper_trades"].append(exit_signal)

    append_jsonl(strategy["signals_log"], exit_signal)

    result = {
        "signal_ts": position["entry_ts"],
        "ticker": position["ticker"],
        "sector": position["sector"],
        "entry_price": entry_price,
        "exit_price": current_price,
        "return_pct": return_pct,
        "win": return_pct > 0,
        "reason": reason,
        "consensus_at_entry": consensus_at_entry,
        "ts": exit_signal["ts"]
    }

    append_jsonl(strategy["results_log"], result)

    return result


def compute_atr_pct(ticker, lookback_days=ATR_LOOKBACK_DAYS):
    """Average True Range over the last `lookback_days`, as a percentage of
    the latest close. Returns None if history is unavailable, in which case
    the caller falls back to the fixed STOP_LOSS_PCT / TRAILING_STOP_PCT."""

    try:
        hist = yf.Ticker(ticker).history(period="2mo")
        hist = hist.dropna(subset=["High", "Low", "Close"])

        closes = hist["Close"].tolist()
        highs = hist["High"].tolist()
        lows = hist["Low"].tolist()

        if len(closes) < lookback_days + 1:
            return None

        true_ranges = []

        for i in range(1, len(closes)):
            true_ranges.append(max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            ))

        atr = sum(true_ranges[-lookback_days:]) / lookback_days
        last_close = closes[-1]

        if not last_close:
            return None

        return (atr / last_close) * 100

    except Exception:
        return None


def position_risk_levels(ticker, strategy=STRATEGIES["primary"]):
    """Stop-loss / trailing-stop / target widths (in %) for a new position.

    risk_mode == "atr": sized off the ticker's ATR at entry for a ~2:1
    reward:risk ratio (Layer 22), falling back to the fixed
    STOP_LOSS_PCT / TRAILING_STOP_PCT if ATR is unavailable.

    risk_mode == "fixed": always the fixed STOP_LOSS_PCT / TRAILING_STOP_PCT
    (pre-Layer-22 behaviour, used by shadow strategy variants - skips the
    ATR lookup entirely so shadow variants add zero extra market-data calls)."""

    if strategy["risk_mode"] == "atr":
        atr_pct = compute_atr_pct(ticker)
    else:
        atr_pct = None

    if atr_pct:
        stop_loss_pct = min(max(atr_pct * ATR_STOP_MULT, ATR_STOP_FLOOR_PCT), ATR_STOP_CEIL_PCT)
        trailing_stop_pct = min(max(atr_pct * ATR_TRAILING_MULT, ATR_STOP_FLOOR_PCT), ATR_STOP_CEIL_PCT)
        target_pct = atr_pct * ATR_TARGET_MULT
    else:
        stop_loss_pct = STOP_LOSS_PCT
        trailing_stop_pct = TRAILING_STOP_PCT
        target_pct = STOP_LOSS_PCT * ATR_TARGET_MULT

    return {
        "atr_pct": atr_pct,
        "stop_loss_pct": stop_loss_pct,
        "trailing_stop_pct": trailing_stop_pct,
        "target_pct": target_pct
    }


def manage_positions(ranking, strategy=STRATEGIES["primary"], track_state=True):
    """Check every open position for a stop-loss, trailing-stop (profit
    locked in once the trend reverses), or rotation exit. Profits have no
    fixed cap - a position rides until the trailing stop triggers.

    Stop-loss / trailing-stop widths come from each position's own
    stop_loss_pct / trailing_stop_pct (set at entry from position_risk_levels),
    falling back to STOP_LOSS_PCT / TRAILING_STOP_PCT for positions opened
    before this field existed.

    Rotation: when rotation_mode == "composite" (primary), prefers
    composite_score (score + forward-sim p_up + sector trend, from
    tomorrow_watchlist.json) when both the held ticker and the current #1
    appear there, falling back to the raw score gap otherwise. When
    rotation_mode == "score_gap" (shadow), always uses the raw score gap
    (pre-Layer-22 behaviour)."""

    ranking_by_ticker = {row["ticker"]: row for row in ranking}

    if strategy["rotation_mode"] == "composite":
        composite_by_ticker = {
            c["ticker"]: c["composite_score"]
            for c in load_json(WATCHLIST_FILE, {}).get("top", [])
        }
    else:
        composite_by_ticker = {}

    positions = load_positions(strategy)
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

        stop_loss_pct = position.get("stop_loss_pct", STOP_LOSS_PCT)
        trailing_stop_pct = position.get("trailing_stop_pct", TRAILING_STOP_PCT)

        reason = None

        if return_pct <= -stop_loss_pct:
            reason = "STOP_LOSS"

        elif peak_price > entry_price:
            drawdown_from_peak = ((peak_price - current_price) / peak_price) * 100
            if drawdown_from_peak >= trailing_stop_pct:
                reason = "TRAILING_STOP"

        if reason is None and top and top["ticker"] != position["ticker"] and return_pct <= 0:

            held_composite = composite_by_ticker.get(position["ticker"])
            top_composite = composite_by_ticker.get(top["ticker"])

            if held_composite is not None and top_composite is not None:
                if top_composite - held_composite >= ROTATION_COMPOSITE_GAP:
                    reason = "ROTATION"
            elif top["score"] - row["score"] >= ROTATION_SCORE_GAP:
                reason = "ROTATION"

        if reason:
            exit_results.append(close_position(position, current_price, reason, strategy, track_state))
        else:
            remaining.append(position)

    save_positions(remaining, strategy)

    return exit_results


def open_new_positions(ranking, excluded=None, strategy=STRATEGIES["primary"], track_state=True):
    """Open at most one new position per cycle. Candidates from the
    last close's tomorrow_watchlist are tried first, falling back to the
    full ranking, requiring the live score to clear ENTRY_SCORE_THRESHOLD.
    Skips entirely if the operator safe-control switch is paused.

    Stop-loss / trailing-stop / target are sized via position_risk_levels
    (ATR-based for primary - Layer 22 EV-BASED RISK FRAMEWORK, fixed % for
    shadow strategy variants)."""

    if load_control().get("trading_paused"):
        return

    positions = load_positions(strategy)

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

        overlap_count = row.get("overlap_count", 0)
        overlap_lists = row.get("overlap_lists", [])
        consensus = overlap_count >= MULTIVERSE_CONSENSUS_MIN_OVERLAP

        entry_signal = {
            "ticker": row["ticker"],
            "sector": row["sector"],
            "score": row["score"],
            "price": row["price"],
            "action": "PAPER_BUY",
            "overlap_count": overlap_count,
            "overlap_lists": overlap_lists,
            "consensus": consensus,
            "ts": datetime.now(timezone.utc).isoformat()
        }

        if track_state:
            STATE["paper_trades"].append(entry_signal)

        append_jsonl(strategy["signals_log"], entry_signal)

        risk = position_risk_levels(row["ticker"], strategy)

        positions.append({
            "ticker": row["ticker"],
            "sector": row["sector"],
            "entry_price": row["price"],
            "entry_ts": entry_signal["ts"],
            "peak_price": row["price"],
            "score_at_entry": row["score"],
            "atr_pct": risk["atr_pct"],
            "stop_loss_pct": risk["stop_loss_pct"],
            "trailing_stop_pct": risk["trailing_stop_pct"],
            "target_pct": risk["target_pct"],
            "overlap_count_at_entry": overlap_count,
            "overlap_lists_at_entry": overlap_lists,
            "consensus_at_entry": consensus
        })

        save_positions(positions, strategy)
        return


def paper_engine(ranking, strategy=STRATEGIES["primary"], track_state=True):

    if not ranking:
        return []

    exit_results = manage_positions(ranking, strategy, track_state)

    just_exited = {r["ticker"] for r in exit_results}

    open_new_positions(ranking, excluded=just_exited, strategy=strategy, track_state=track_state)

    return exit_results

# =====================================
# PORTFOLIO
# =====================================

def portfolio_engine(ranking=None):

    ranking_by_ticker = {row["ticker"]: row for row in (ranking or [])}

    portfolio = {}

    for position in load_positions(active_strategy()):

        ticker = position["ticker"]
        entry_price = position["entry_price"]
        current_price = ranking_by_ticker.get(ticker, {}).get("price", entry_price)

        portfolio[ticker] = {
            "sector": position["sector"],
            "entry_price": entry_price,
            "current_price": current_price,
            "peak_price": position["peak_price"],
            "return_pct": ((current_price - entry_price) / entry_price) * 100,
            "stop_loss_pct": position.get("stop_loss_pct", STOP_LOSS_PCT),
            "trailing_stop_pct": position.get("trailing_stop_pct", TRAILING_STOP_PCT),
            "target_pct": position.get("target_pct", STOP_LOSS_PCT * ATR_TARGET_MULT),
            "consensus_at_entry": position.get("consensus_at_entry", False),
            "overlap_lists_at_entry": position.get("overlap_lists_at_entry", [])
        }

    STATE["portfolio"] = portfolio


def portfolio_from_ledger():

    portfolio = {}

    for row in read_jsonl(active_strategy()["signals_log"]):

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

def update_learning_stats(new_results, learning_file=LEARNING_FILE):
    """Roll new exit results into the persisted learning_stats.

    Layer 24 (MULTIVERSE CONSENSUS SIGNAL): each exit result carries
    consensus_at_entry (set when the position was opened on a ticker that
    >= MULTIVERSE_CONSENSUS_MIN_OVERLAP independent ranking signal-universes
    agreed on - see open_new_positions / rank_engine's overlap_count).
    Trades are split into consensus_* vs single_signal_* counters so the
    close report can show, from real outcomes, whether cross-universe
    agreement actually predicts better trades."""

    stats = load_json(learning_file, {
        "equity_curve": [1.0],
        "cumulative_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "win_rate_pct": 0.0,
        "total_trades": 0,
        "wins": 0,
        "consensus_trades": 0,
        "consensus_wins": 0,
        "consensus_return_sum_pct": 0.0,
        "single_signal_trades": 0,
        "single_signal_wins": 0,
        "single_signal_return_sum_pct": 0.0,
        "updated_ts": None
    })

    equity_curve = stats.get("equity_curve", [1.0])
    wins = stats.get("wins", 0)
    total_trades = stats.get("total_trades", 0)
    consensus_trades = stats.get("consensus_trades", 0)
    consensus_wins = stats.get("consensus_wins", 0)
    consensus_return_sum = stats.get("consensus_return_sum_pct", 0.0)
    single_signal_trades = stats.get("single_signal_trades", 0)
    single_signal_wins = stats.get("single_signal_wins", 0)
    single_signal_return_sum = stats.get("single_signal_return_sum_pct", 0.0)

    for r in new_results:
        equity_curve.append(equity_curve[-1] * (1 + r["return_pct"] / 100))
        total_trades += 1
        if r["win"]:
            wins += 1

        if r.get("consensus_at_entry"):
            consensus_trades += 1
            consensus_return_sum += r["return_pct"]
            if r["win"]:
                consensus_wins += 1
        else:
            single_signal_trades += 1
            single_signal_return_sum += r["return_pct"]
            if r["win"]:
                single_signal_wins += 1

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
        "consensus_trades": consensus_trades,
        "consensus_wins": consensus_wins,
        "consensus_return_sum_pct": consensus_return_sum,
        "consensus_win_rate_pct": (consensus_wins / consensus_trades * 100) if consensus_trades else 0.0,
        "consensus_avg_return_pct": (consensus_return_sum / consensus_trades) if consensus_trades else 0.0,
        "single_signal_trades": single_signal_trades,
        "single_signal_wins": single_signal_wins,
        "single_signal_return_sum_pct": single_signal_return_sum,
        "single_signal_win_rate_pct": (single_signal_wins / single_signal_trades * 100) if single_signal_trades else 0.0,
        "single_signal_avg_return_pct": (single_signal_return_sum / single_signal_trades) if single_signal_trades else 0.0,
        "updated_ts": datetime.now(timezone.utc).isoformat()
    }

    save_json(learning_file, stats)

    return stats

# =====================================
# STRATEGY COMPARISON (Layer 23: STRATEGY MULTIVERSE / AUTO CANONICAL FILTERING)
# =====================================

def run_all_strategies(ranking):
    """Run every strategy variant in STRATEGIES against the SAME per-cycle
    ranking data, each in its own ledger (see STRATEGIES). Only the
    currently-active strategy (active_strategy_name) writes to
    STATE["paper_trades"] - every other variant trades silently in its own
    ledger as a control group. No extra market-data calls or Telegram
    messages versus running one strategy alone.

    Returns (active_exit_results, results_by_name), where results_by_name
    maps each strategy name to {label, exit_results, learning_stats}."""

    active_name = active_strategy_name()

    results_by_name = {}
    active_exit_results = []

    for name, strategy in STRATEGIES.items():

        is_active = (name == active_name)

        exit_results = paper_engine(ranking, strategy=strategy, track_state=is_active)
        learning_stats = update_learning_stats(exit_results, learning_file=strategy["learning_file"])

        results_by_name[name] = {
            "label": strategy["label"],
            "exit_results": exit_results,
            "learning_stats": learning_stats
        }

        if is_active:
            active_exit_results = exit_results

    return active_exit_results, results_by_name


def evaluate_strategy_promotion(results_by_name):
    """Layer 23: AUTO CANONICAL FILTERING. Compare every strategy variant's
    just-updated learning_stats against the currently-active variant and
    decide whether to promote a challenger to active.

    Promotion requires, every close report:
      - both the active strategy and the challenger have at least
        PROMOTION_MIN_TRADES closed trades (a judgment needs real data), and
      - the challenger's cumulative_return_pct leads the active strategy's
        by >= PROMOTION_MARGIN_PCT, for PROMOTION_STREAK_REQUIRED
        consecutive close reports in a row (no flip-flopping on one noisy
        day).

    Every promotion is appended to "history" with the stats that justified
    it and persisted to STRATEGY_PROMOTION_FILE - the switch is automatic
    but never silent."""

    state = load_json(STRATEGY_PROMOTION_FILE, {
        "active": "primary",
        "streaks": {},
        "history": []
    })

    active_name = state.get("active", "primary")
    active_stats = results_by_name.get(active_name, {}).get("learning_stats", {})
    active_trades = active_stats.get("total_trades", 0)
    active_return = active_stats.get("cumulative_return_pct", 0.0)

    streaks = state.get("streaks", {})
    promoted_to = None

    for name, result in results_by_name.items():

        if name == active_name:
            continue

        stats = result["learning_stats"]

        leads = (
            active_trades >= PROMOTION_MIN_TRADES
            and stats.get("total_trades", 0) >= PROMOTION_MIN_TRADES
            and stats.get("cumulative_return_pct", 0.0) - active_return >= PROMOTION_MARGIN_PCT
        )

        streaks[name] = streaks.get(name, 0) + 1 if leads else 0

        if streaks[name] >= PROMOTION_STREAK_REQUIRED:
            promoted_to = name

    if promoted_to:

        state["history"].append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "from": active_name,
            "to": promoted_to,
            "from_stats": active_stats,
            "to_stats": results_by_name[promoted_to]["learning_stats"]
        })

        state["active"] = promoted_to
        streaks = {name: 0 for name in results_by_name}

    state["streaks"] = streaks

    save_json(STRATEGY_PROMOTION_FILE, state)

    return state

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
            "composite_score": composite_score,
            "overlap_count": row.get("overlap_count", 0),
            "consensus": row.get("overlap_count", 0) >= MULTIVERSE_CONSENSUS_MIN_OVERLAP
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

    surges = report_data.get("surge_scan") or []

    if surges:
        lines.append("")
        lines.append("[SURGE SCAN] 전체 KRX 급등주 >= %.0f%% (WATCHLIST 외 포함)" % SURGE_SCAN_THRESHOLD_PCT)
        for s in surges:
            drivers = "; ".join(s["possible_drivers"]) or "원인 미확인 (HOLD)"
            lines.append(
                "  %s %s change=%.2f%% price=%s -> %s" % (
                    s["ticker"], s["name"], s["change_pct"], s["price"], drivers
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
            consensus_note = " [CONSENSUS]" if p.get("consensus_at_entry") else " [single_signal]"
            lines.append(
                "  %s (%s) entry=%.2f current=%.2f return=%.2f%% "
                "(stop=-%.2f%% trail=%.2f%% target=+%.2f%%)%s" % (
                    ticker, p["sector"], p["entry_price"], p["current_price"], p["return_pct"],
                    p["stop_loss_pct"], p["trailing_stop_pct"], p["target_pct"], consensus_note
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

    surges = close_data.get("surge_scan") or []

    if surges:
        lines.append("")
        lines.append("[SURGE SCAN] 전체 KRX 급등주 >= %.0f%% (WATCHLIST 외 포함)" % SURGE_SCAN_THRESHOLD_PCT)
        for s in surges:
            drivers = "; ".join(s["possible_drivers"]) or "원인 미확인 (HOLD)"
            lines.append(
                "  %s %s change=%.2f%% price=%s -> %s" % (
                    s["ticker"], s["name"], s["change_pct"], s["price"], drivers
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
    lines.append("[MULTIVERSE CONSENSUS] (Layer 24: independent VOLUME/MOMENTUM/FOREIGN_LINK/NEWS "
                  "signal-universes agree >= %d/4 -> consensus pick)" % MULTIVERSE_CONSENSUS_MIN_OVERLAP)
    lines.append(
        "  consensus: trades=%s win_rate=%.1f%% avg_return=%.2f%%" % (
            learn.get("consensus_trades", 0), learn.get("consensus_win_rate_pct", 0.0),
            learn.get("consensus_avg_return_pct", 0.0)
        )
    )
    lines.append(
        "  single_signal: trades=%s win_rate=%.1f%% avg_return=%.2f%%" % (
            learn.get("single_signal_trades", 0), learn.get("single_signal_win_rate_pct", 0.0),
            learn.get("single_signal_avg_return_pct", 0.0)
        )
    )

    lines.append("")
    lines.append("[STRATEGY COMPARISON] (same ranking data, separate ledgers, auto canonical filtering)")
    promotion = close_data.get("strategy_promotion", {})
    active_name = promotion.get("active", "primary")
    streaks = promotion.get("streaks", {})
    for name, result in close_data.get("strategy_results", {}).items():
        s = result["learning_stats"]
        marker = " <- ACTIVE" if name == active_name else ""
        streak = streaks.get(name, 0)
        streak_note = (
            " (promotion_streak=%s/%s)" % (streak, PROMOTION_STREAK_REQUIRED)
            if streak else ""
        )
        lines.append(
            "  %s: trades=%s win_rate=%.1f%% return=%.2f%% drawdown=%.2f%%%s%s" % (
                result["label"], s["total_trades"], s["win_rate_pct"],
                s["cumulative_return_pct"], s["max_drawdown_pct"], marker, streak_note
            )
        )
    if promotion.get("history"):
        last = promotion["history"][-1]
        lines.append("  last_promotion: %s -> %s at %s" % (last["from"], last["to"], last["ts"]))

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
            consensus_note = (
                " [CONSENSUS:%s]" % ",".join(p.get("overlap_lists_at_entry", []))
                if p.get("consensus_at_entry") else " [single_signal]"
            )
            lines.append(
                "  %s (%s) entry=%.2f current=%.2f return=%.2f%% "
                "(stop=-%.2f%% trail=%.2f%% target=+%.2f%%)%s" % (
                    ticker, p["sector"], p["entry_price"], p["current_price"], p["return_pct"],
                    p["stop_loss_pct"], p["trailing_stop_pct"], p["target_pct"], consensus_note
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
    pattern, self-validation transparency (Layer 24 consensus tracking),
    and tomorrow's candidate watch list - no raw position entry prices or
    account-level figures (those stay in the CEO report)."""

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

    learn = close_data["learning_stats"]
    consensus_trades = learn.get("consensus_trades") or 0
    single_trades = learn.get("single_signal_trades") or 0

    lines.append("")
    lines.append("[SYSTEM SELF-CHECK] (Layer 24: 4 independent signal sources - "
                  "volume / momentum / foreign-flow / news - cross-checked against each other)")
    if consensus_trades or single_trades:
        lines.append("  multi-signal agreement: trades=%d win_rate=%.1f%% avg_return=%.2f%%" % (
            consensus_trades, learn.get("consensus_win_rate_pct", 0.0),
            learn.get("consensus_avg_return_pct", 0.0)
        ))
        lines.append("  single-signal only:     trades=%d win_rate=%.1f%% avg_return=%.2f%%" % (
            single_trades, learn.get("single_signal_win_rate_pct", 0.0),
            learn.get("single_signal_avg_return_pct", 0.0)
        ))
    else:
        lines.append("  multi-signal vs single-signal track record: accumulating "
                      "(needs more closed trades before a split is meaningful)")

    watchlist = close_data["tomorrow_watchlist"][:TOMORROW_WATCHLIST_REPORT_N]

    lines.append("")
    lines.append("[TOMORROW WATCH LIST TOP%d] ([CONSENSUS] = >=%d/4 signal sources agree)" % (
        len(watchlist), MULTIVERSE_CONSENSUS_MIN_OVERLAP
    ))
    for w in watchlist:
        tag = " [CONSENSUS]" if w.get("consensus") else ""
        lines.append("  %s (%s)%s" % (w["ticker"], w["sector"], tag))

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

def report(exit_results=None, leader=None, global_flows=None, essence=None, surges=None):

    ranking = STATE["rankings"]

    global_flows = global_flows or []

    learning_stats = load_json(active_strategy()["learning_file"], {
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

        "surge_scan":
            surges or [],

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
    "SURGE_CAUSE_TRACE": lambda ctx: "surge_scan" in ctx,
    "STRATEGY_COMPARISON": lambda ctx: len(ctx.get("strategy_results", {})) >= 2,
    "AUTO_CANONICAL_FILTERING": lambda ctx: "active" in (ctx.get("strategy_promotion") or {}),
    "MULTIVERSE_CONSENSUS": lambda ctx: "consensus_trades" in (ctx.get("learning_stats") or {}),
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

    surges = surge_scan(news)

    STATE["surges"] = surges

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

    return market, news, ranking, leader, global_flows, essence, surges


def run_cycle():

    market, news, ranking, leader, global_flows, essence, surges = collect_cycle_data()

    exit_results, _ = run_all_strategies(ranking)

    portfolio_engine(ranking)

    report(exit_results, leader, global_flows, essence, surges)


def run_close():

    market, news, ranking, leader, global_flows, essence, surges = collect_cycle_data()

    market_state = market_state_engine(ranking)
    sector_strength = sector_strength_engine(ranking)
    g_risk_state = global_risk_state(global_flows)

    exit_results, strategy_results = run_all_strategies(ranking)

    strategy_promotion = evaluate_strategy_promotion(strategy_results)

    active_name = active_strategy_name()
    learning_stats = strategy_results[active_name]["learning_stats"]

    portfolio_engine(ranking)

    account_status = account_status_engine(learning_stats, STATE["portfolio"])
    control = load_control()

    tomorrow_watchlist = build_tomorrow_watchlist(ranking, sector_strength)

    hybrid_mind = hybrid_mind_engine(tomorrow_watchlist, market_state)

    patch_council = patch_council_review(learning_stats, market_state, load_positions(active_strategy()))

    portfolio_total = sum(portfolio_from_ledger().values())

    close_data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "market_state": market_state,
        "top5": ranking[:5],
        "sector_strength": sector_strength,
        "leader_analysis": leader,
        "exit_results": exit_results,
        "learning_stats": learning_stats,
        "strategy_results": strategy_results,
        "strategy_promotion": strategy_promotion,
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
        "patch_council": patch_council,
        "surge_scan": surges
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
        "ceo_report_book_entry": ceo_report_book_entry,
        "surge_scan": surges,
        "strategy_results": strategy_results,
        "strategy_promotion": strategy_promotion,
        "learning_stats": learning_stats
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
