#!/usr/bin/env python3
"""
Trading Technical Analysis CLI Tool with MetaTrader 5 (MT5) Direct Terminal Integration
Zero API registration needed! Reads live market data directly from your active MT5 Exness terminal on Windows, with automatic yfinance fallback.
"""

import sys
import io
import os
import time
from datetime import datetime, timezone
from typing import Dict, Tuple

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


MT5_TIMEFRAME_MAP = {
    "1m": mt5.TIMEFRAME_M1 if mt5 else 1,
    "5m": mt5.TIMEFRAME_M5 if mt5 else 5,
    "15m": mt5.TIMEFRAME_M15 if mt5 else 15,
    "30m": mt5.TIMEFRAME_M30 if mt5 else 30,
    "1h": mt5.TIMEFRAME_H1 if mt5 else 16385,
    "4h": mt5.TIMEFRAME_H4 if mt5 else 16388,
    "1d": mt5.TIMEFRAME_D1 if mt5 else 16408,
}


def fetch_yfinance_fallback(symbol: str, timeframe: str, days: int = 60):
    """Fetch OHLCV data from yfinance as fallback if MT5 terminal is closed/unauthorized"""
    import yfinance as yf
    try:
        tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"}
        interval = tf_map.get(timeframe, "1h")
        
        clean_sym = symbol.upper().replace("M", "").replace("C", "").replace("/", "").replace("-", "")
        aliases = {
            'XAUUSD': 'GC=F', 'GOLD': 'GC=F', 'XAGUSD': 'SI=F',
            'BTCUSD': 'BTC-USD', 'ETHUSD': 'ETH-USD',
            'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'AUDUSD': 'AUDUSD=X'
        }
        target_yf = aliases.get(clean_sym, clean_sym)
        
        print(f"{Colors.BLUE}[*] Mengaktifkan Fallback otomatis ke Yahoo Finance ({target_yf})...{Colors.RESET}")
        df = yf.download(target_yf, period=f"{days}d", interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        req = ['Open', 'High', 'Low', 'Close', 'Volume']
        if any(c not in df.columns for c in req):
            return None, None
        return df[['Open', 'High', 'Low', 'Close', 'Volume']], target_yf
    except Exception as e:
        print(f"{Colors.RED}[!] Error yfinance fallback: {e}{Colors.RESET}")
        return None, None


def fetch_mt5_data(symbol: str, timeframe: str = "1h", count: int = 100):
    """Fetch live historical rates directly from active MT5 Terminal, with yfinance fallback"""
    if not mt5:
        print(f"{Colors.YELLOW}[!] Library MetaTrader5 tidak tersedia.{Colors.RESET}")
        df_yf, yf_s = fetch_yfinance_fallback(symbol, timeframe)
        return df_yf, yf_s or symbol, "Yahoo Finance Fallback", "yfinance"

    mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    initialized = mt5.initialize(path=mt5_path) if os.path.exists(mt5_path) else mt5.initialize()
    if not initialized:
        err = mt5.last_error()
        print(f"{Colors.RED}[!] MT5 Gagal Terkoneksi/Otorisasi (Error: {err}).{Colors.RESET}")
        print(f"{Colors.YELLOW}[Tips] Pastikan aplikasi MetaTrader 5 desktop Anda di Windows terbuka & terhubung ke akun broker!{Colors.RESET}")
        df_yf, yf_s = fetch_yfinance_fallback(symbol, timeframe)
        return df_yf, yf_s or symbol, "Yahoo Finance Fallback (MT5 Not Ready)", "yfinance"

    selected_sym = symbol
    sym_info = mt5.symbol_info(selected_sym)
    if sym_info is None:
        clean = symbol.replace("/", "").replace("-", "").replace("_", "")
        candidates = [clean, clean + "m", clean + "c", clean + ".a", clean.upper(), clean.upper() + "m"]
        for c in candidates:
            if mt5.symbol_info(c) is not None:
                selected_sym = c
                break

    sym_info = mt5.symbol_info(selected_sym)
    if sym_info is None:
        print(f"{Colors.RED}[!] Simbol '{symbol}' tidak ditemukan di Market Watch terminal MT5 Anda.{Colors.RESET}")
        mt5.shutdown()
        df_yf, yf_s = fetch_yfinance_fallback(symbol, timeframe)
        return df_yf, yf_s or symbol, "Yahoo Finance Fallback (Symbol Not Found)", "yfinance"

    if not sym_info.visible:
        mt5.symbol_select(selected_sym, True)

    tf_const = MT5_TIMEFRAME_MAP.get(timeframe, mt5.TIMEFRAME_H1)
    print(f"{Colors.BLUE}[*] Menyedot 100 candle {selected_sym} ({timeframe}) langsung dari terminal MT5...{Colors.RESET}")
    rates = mt5.copy_rates_from_pos(selected_sym, tf_const, 0, count)
    
    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        print(f"{Colors.RED}[!] Gagal mengambil candle dari MT5 (Error: {err}).{Colors.RESET}")
        mt5.shutdown()
        df_yf, yf_s = fetch_yfinance_fallback(symbol, timeframe)
        return df_yf, yf_s or symbol, "Yahoo Finance Fallback (Rates Empty)", "yfinance"

    df = pd.DataFrame(rates)
    df['Timestamp'] = pd.to_datetime(df['time'], unit='s')
    df = df.set_index('Timestamp')
    
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    })

    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    acc_info = mt5.account_info()
    if acc_info:
        login_str = str(acc_info.login)
        masked_login = f"{login_str[:2]}XXXX{login_str[-2:]}" if len(login_str) >= 4 else "XXXXXX"
        acc_str = f"MT5 User ({masked_login}) on {acc_info.server}"
    else:
        acc_str = "Terminal MT5 Windows"
    
    return df, selected_sym, acc_str, "MT5"


HTF_MAP = {
    "1m": ["15m", "1h"],
    "5m": ["1h", "4h"],
    "15m": ["1h", "4h"],
    "30m": ["4h", "1d"],
    "1h": ["4h", "1d"],
    "4h": ["1d"],
    "1d": ["1d"]
}


def _fmt_p(val: float, digits: int = 2) -> str:
    if digits <= 0:
        return f"{val:,.0f}"
    return f"{val:,.{digits}f}"


def fetch_broker_specs(symbol: str, source_type: str) -> dict:
    specs = {
        "spread": 0,
        "digits": 2,
        "point": 0.01,
        "swap_long": 0.0,
        "swap_short": 0.0,
        "contract_size": 100
    }
    if source_type == "MT5" and mt5:
        try:
            info = mt5.symbol_info(symbol)
            if info:
                specs["spread"] = getattr(info, 'spread', 0)
                specs["digits"] = getattr(info, 'digits', 2)
                specs["point"] = getattr(info, 'point', 0.01)
                specs["swap_long"] = getattr(info, 'swap_long', 0.0)
                specs["swap_short"] = getattr(info, 'swap_short', 0.0)
                specs["contract_size"] = getattr(info, 'trade_contract_size', 100)
        except Exception:
            pass
    return specs


def fetch_htf_trend(symbol: str, timeframe: str, source_type: str) -> str:
    htfs = HTF_MAP.get(timeframe, ["4h", "1d"])
    if timeframe in ["4h", "1d"]:
        htfs = ["1d"]
    
    results = []
    for htf in htfs:
        df_htf = None
        if source_type == "MT5" and mt5:
            tf_const = MT5_TIMEFRAME_MAP.get(htf, mt5.TIMEFRAME_H4)
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 50)
            if rates is not None and len(rates) > 0:
                df_htf = pd.DataFrame(rates)
                df_htf['Close'] = df_htf['close']
        else:
            df_htf, _ = fetch_yfinance_fallback(symbol, htf, days=30)
            
        if df_htf is not None and not df_htf.empty and len(df_htf) >= 20:
            c = df_htf['Close']
            ema20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
            ema50 = c.ewm(span=50, adjust=False).mean().iloc[-1]
            trend = "Bullish" if ema20 > ema50 else "Bearish"
            results.append(f"{htf.upper()}: {trend}")
        else:
            results.append(f"{htf.upper()}: Neutral")
            
    return " | ".join(results) if results else "HTF Status Unavailable"


def calculate_key_levels(df: pd.DataFrame) -> Tuple[float, float]:
    """Calculate key support and resistance from recent 30 candles"""
    if len(df) < 5:
        return float(df['Low'].min()), float(df['High'].max())
    window = df.iloc[-30:-1] if len(df) >= 31 else df.iloc[:-1]
    sup = float(window['Low'].min())
    res = float(window['High'].max())
    return sup, res


def get_recent_candles_table(df: pd.DataFrame, digits: int = 2, count: int = 5) -> str:
    """Format recent 5 candles before latest candle as text table"""
    if len(df) < 2:
        return "Insufficient historical candles."
    start_idx = max(0, len(df) - 1 - count)
    end_idx = len(df) - 1
    recent_df = df.iloc[start_idx:end_idx]
    
    lines = [f"{'Time':<16} | {'Open':<10} | {'High':<10} | {'Low':<10} | {'Close':<10} | {'Vol':<8}"]
    lines.append("-" * 78)
    for idx, row in recent_df.iterrows():
        t_str = idx.strftime('%Y-%m-%d %H:%M') if hasattr(idx, 'strftime') else str(idx)[:16]
        lines.append(f"{t_str:<16} | {_fmt_p(row['Open'], digits):<10} | {_fmt_p(row['High'], digits):<10} | {_fmt_p(row['Low'], digits):<10} | {_fmt_p(row['Close'], digits):<10} | {row['Volume']:<8.0f}")
    return "\n".join(lines)


_MTF_CACHE = {}
_MTF_CACHE_TTL = 60.0


def identify_trading_session(dt_val) -> str:
    """Identify active Forex/Gold trading session(s) based on candle timestamp"""
    try:
        if isinstance(dt_val, (int, float, np.integer, np.floating)):
            dt_utc = datetime.fromtimestamp(int(dt_val), tz=timezone.utc)
        elif hasattr(dt_val, 'tzinfo') and dt_val.tzinfo is not None:
            dt_utc = dt_val.astimezone(timezone.utc)
        elif isinstance(dt_val, str):
            dt_utc = pd.to_datetime(dt_val).tz_localize('UTC')
        else:
            dt_utc = pd.to_datetime(dt_val)
        
        h = dt_utc.hour
        sessions = []
        if 22 <= h or h < 7:
            sessions.append("Sydney")
        if 0 <= h < 9:
            sessions.append("Tokyo")
        if 8 <= h < 17:
            sessions.append("London")
        if 13 <= h < 22:
            sessions.append("New York")
        
        return " / ".join(sessions) if sessions else "Market Closed / Inter-session"
    except Exception:
        return "London / New York Session"


def detect_candlestick_patterns_vectorized(df: pd.DataFrame) -> Tuple[list, str]:
    """Pure vectorized numpy/pandas candlestick pattern recognition"""
    if df is None or len(df) < 2:
        return [], "Normal Price Action"
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    body = abs(latest['Close'] - latest['Open'])
    rng = latest['High'] - latest['Low']
    upper_wick = latest['High'] - max(latest['Close'], latest['Open'])
    lower_wick = min(latest['Close'], latest['Open']) - latest['Low']
    
    patterns = []
    if rng > 0 and lower_wick >= 2.0 * body and upper_wick <= 0.5 * body:
        patterns.append("Bullish Pin Bar (Hammer)")
    elif rng > 0 and upper_wick >= 2.0 * body and lower_wick <= 0.5 * body:
        patterns.append("Bearish Pin Bar (Shooting Star)")
        
    if latest['Close'] > latest['Open'] and prev['Close'] < prev['Open'] and latest['Close'] >= prev['Open'] and latest['Open'] <= prev['Close'] and body > abs(prev['Close'] - prev['Open']):
        patterns.append("Bullish Engulfing")
    elif latest['Close'] < latest['Open'] and prev['Close'] > prev['Open'] and latest['Close'] <= prev['Open'] and latest['Open'] >= prev['Close'] and body > abs(prev['Close'] - prev['Open']):
        patterns.append("Bearish Engulfing")
        
    if rng > 0 and body <= rng * 0.1:
        patterns.append("Doji (Indecision)")
        
    status_str = " + ".join(patterns) if patterns else "Standard Candle (No Key Reversal Pattern)"
    return patterns, status_str


def get_structural_and_mtf_data(symbol: str, current_price: float, source_type: str) -> dict:
    """Fetch MTF EMA trend and Daily Pivot Points Standard synchronously with 60s caching"""
    now = time.time()
    cache = _MTF_CACHE.get(symbol)
    if cache and (now - cache['timestamp']) < _MTF_CACHE_TTL:
        return cache['data']
    
    pivots = {"PP": 0.0, "R1": 0.0, "R2": 0.0, "R3": 0.0, "S1": 0.0, "S2": 0.0, "S3": 0.0}
    h4_high, h4_low = current_price * 1.01, current_price * 0.99
    mtf_trend = {
        "H1": {"trend": "Neutral", "ema50": current_price, "price_above": True},
        "H4": {"trend": "Neutral", "ema50": current_price, "price_above": True},
        "D1": {"trend": "Neutral", "ema20": current_price}
    }
    
    if source_type == "MT5" and mt5:
        try:
            d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 1, 2)
            if d1_rates is not None and len(d1_rates) > 0:
                prev_d1 = d1_rates[0]
                hp, lp, cp = float(prev_d1['high']), float(prev_d1['low']), float(prev_d1['close'])
                pp = (hp + lp + cp) / 3.0
                pivots = {
                    "PP": pp,
                    "R1": 2.0 * pp - lp,
                    "S1": 2.0 * pp - hp,
                    "R2": pp + (hp - lp),
                    "S2": pp - (hp - lp),
                    "R3": hp + 2.0 * (pp - lp),
                    "S3": lp - 2.0 * (hp - pp)
                }
                if len(d1_rates) > 1:
                    d1_c = float(d1_rates[-1]['close'])
                    mtf_trend["D1"] = {"trend": "Bullish" if d1_c > pp else "Bearish", "ema20": pp}
            
            h4_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
            if h4_rates is not None and len(h4_rates) > 0:
                df_h4 = pd.DataFrame(h4_rates)
                h4_high = float(df_h4['high'].tail(30).max())
                h4_low = float(df_h4['low'].tail(30).min())
                if len(df_h4) >= 20:
                    ema50_h4 = float(df_h4['close'].ewm(span=50, adjust=False).mean().iloc[-1])
                    mtf_trend["H4"] = {
                        "trend": "Bullish (Uptrend)" if current_price > ema50_h4 else "Bearish (Downtrend)",
                        "ema50": ema50_h4,
                        "price_above": bool(current_price > ema50_h4)
                    }
                    
            h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            if h1_rates is not None and len(h1_rates) >= 20:
                df_h1 = pd.DataFrame(h1_rates)
                ema50_h1 = float(df_h1['close'].ewm(span=50, adjust=False).mean().iloc[-1])
                mtf_trend["H1"] = {
                    "trend": "Bullish (Uptrend)" if current_price > ema50_h1 else "Bearish (Downtrend)",
                    "ema50": ema50_h1,
                    "price_above": bool(current_price > ema50_h1)
                }
        except Exception:
            pass
    else:
        try:
            df_d1, _ = fetch_yfinance_fallback(symbol, "1d", days=10)
            if df_d1 is not None and len(df_d1) >= 2:
                prev_d1 = df_d1.iloc[-2]
                hp, lp, cp = float(prev_d1['High']), float(prev_d1['Low']), float(prev_d1['Close'])
                pp = (hp + lp + cp) / 3.0
                pivots = {
                    "PP": pp, "R1": 2*pp - lp, "S1": 2*pp - hp,
                    "R2": pp + (hp - lp), "S2": pp - (hp - lp),
                    "R3": hp + 2*(pp - lp), "S3": lp - 2*(hp - pp)
                }
        except Exception:
            pass

    data = {
        "daily_pivots": pivots,
        "h4_swing_high": h4_high,
        "h4_swing_low": h4_low,
        "mtf_trend": mtf_trend
    }
    _MTF_CACHE[symbol] = {"timestamp": now, "data": data}
    return data


# ── Pure pandas/numpy indicator helpers ──────────────────────────────────────
def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast   = _ema(series, fast)
    ema_slow   = _ema(series, slow)
    macd_line  = ema_fast - ema_slow
    signal_line= _ema(macd_line, signal)
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram

def _bbands(series: pd.Series, window=20, std_mult=2):
    middle = _sma(series, window)
    std    = series.rolling(window=window).std(ddof=0)
    upper  = middle + std_mult * std
    lower  = middle - std_mult * std
    return upper, middle, lower

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()
# ─────────────────────────────────────────────────────────────────────────────


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators"""
    try:
        print(f"{Colors.BLUE}[*] Calculating technical indicators...{Colors.RESET}")
        close = df['Close']

        df['EMA20'] = _ema(close, 20)
        df['EMA50'] = _ema(close, 50)
        df['SMA20'] = _sma(close, 20)
        df['SMA50'] = _sma(close, 50)
        df['RSI'] = _rsi(close, 14)
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = _macd(close)
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = _bbands(close)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        df['ATR'] = _atr(df['High'], df['Low'], close)

        return df
    except Exception as e:
        print(f"{Colors.RED}[!] Error calculating indicators: {e}{Colors.RESET}")
        return None


def generate_signal(df: pd.DataFrame) -> Tuple[str, float]:
    """Generate BUY/SELL/NEUTRAL signal based on confluence"""
    latest = df.iloc[-1]
    bullish_count = 0
    bearish_count = 0
    
    if latest['EMA20'] > latest['EMA50']:
        bullish_count += 1
    else:
        bearish_count += 1
        
    if latest['RSI'] < 30:
        bullish_count += 1
    elif latest['RSI'] > 70:
        bearish_count += 1
        
    if latest['MACD'] > latest['MACD_Signal']:
        bullish_count += 1
    else:
        bearish_count += 1
        
    if latest['Close'] < latest['BB_Lower']:
        bullish_count += 1
    elif latest['Close'] > latest['BB_Upper']:
        bearish_count += 1
        
    if bullish_count > bearish_count:
        signal = "BUY"
        confidence = min(0.95, bullish_count / 4 * 0.90 + 0.30)
    elif bearish_count > bullish_count:
        signal = "SELL"
        confidence = min(0.95, bearish_count / 4 * 0.90 + 0.30)
    else:
        signal = "NEUTRAL"
        confidence = 0.50
        
    return signal, confidence


def get_trading_style(timeframe: str) -> str:
    if timeframe in ["1m", "5m"]:
        return "Scalping / Quick Momentum"
    elif timeframe in ["15m", "30m", "1h"]:
        return "Intraday / Day Trading"
    else:
        return "Swing Trading"


def generate_md_dossier(symbol: str, timeframe: str, df: pd.DataFrame, broker_sym: str, acc_str: str, source_type: str, specs: dict, htf_trend: str, sup: float, res: float, recent_tbl: str, env_data: dict = None) -> str:
    latest = df.iloc[-1]
    signal, confidence = generate_signal(df)
    prev = df.iloc[-2] if len(df) > 1 else latest
    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
    digits = specs.get('digits', 2)
    style = get_trading_style(timeframe)
    trend = "Uptrend (Bullish)" if latest['EMA20'] > latest['EMA50'] else "Downtrend (Bearish)"
    
    if latest['RSI'] < 30:
        rsi_status = "Oversold (Reversal potential)"
    elif latest['RSI'] > 70:
        rsi_status = "Overbought (Reversal potential)"
    else:
        rsi_status = "Neutral zone"
        
    macd_status = "Bullish crossover" if latest['MACD'] > latest['MACD_Signal'] else "Bearish crossover"
    bb_status = "Below lower band" if latest['Close'] < latest['BB_Lower'] else "Above upper band" if latest['Close'] > latest['BB_Upper'] else "Between bands"
    
    spread_pts = specs.get('spread', 0)
    point_sz = specs.get('point', 0.01)
    sl_suggest = latest['Close'] - (latest['ATR'] * 1.5) - (spread_pts * point_sz) if signal != "SELL" else latest['Close'] + (latest['ATR'] * 1.5) + (spread_pts * point_sz)
    tp_suggest = latest['Close'] + (latest['ATR'] * 2.5) if signal != "SELL" else latest['Close'] - (latest['ATR'] * 2.5)

    session_str = env_data.get('session', 'London / New York Session') if env_data else 'Standard Session'
    pattern_status = env_data.get('pattern_status', 'Standard Candle') if env_data else 'Standard Candle'
    struct = env_data.get('struct_mtf', {}) if env_data else {}
    piv = struct.get('daily_pivots', {})
    h4_sh = struct.get('h4_swing_high', res)
    h4_sl = struct.get('h4_swing_low', sup)
    
    piv_str = f"PP: {_fmt_p(piv.get('PP', 0), digits)} | R1: {_fmt_p(piv.get('R1', 0), digits)} | S1: {_fmt_p(piv.get('S1', 0), digits)}" if piv else "N/A"

    md = f"""# 📊 QUANTITATIVE TRADING DOSSIER: {broker_sym} ({timeframe})
> **Timestamp:** {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')} | **Data Source:** {source_type} ({acc_str})

---

## 1. Broker Specifications & Costs
* **Live Spread:** `{spread_pts} points` (Point Size: `{point_sz}`)
* **Overnight Swap:** Long `{specs.get('swap_long', 0.0)}` / Short `{specs.get('swap_short', 0.0)}`
* **Price Precision:** `{digits} decimal digits`

## 1.5 Market Environment & Context
* **Active Trading Session:** `{session_str}`
* **Candlestick Pattern Recognition (15m):** `{pattern_status}`

## 2. Market Structure & Major Confluence
* **Higher Timeframe Trend:** `{htf_trend}`
* **Current Timeframe Trend:** `{trend}` (EMA20: `{_fmt_p(latest['EMA20'], digits)}`, EMA50: `{_fmt_p(latest['EMA50'], digits)}`)
* **Daily Pivots (Standard D1):** `{piv_str}`
* **H4 Structural Zones (30-bar):** Swing High `${_fmt_p(h4_sh, digits)}` / Swing Low `${_fmt_p(h4_sl, digits)}`
* **Local Support & Resistance:** Support `${_fmt_p(sup, digits)}` / Resistance `${_fmt_p(res, digits)}`


## 3. Price Action (Recent 5 Historical Candles)
```text
{recent_tbl}
```

## 4. Momentum & Volatility Audit
* **Tick Price:** `${_fmt_p(latest['Close'], digits)}` ({price_change:+.2f}%) | **Daily High/Low:** `${_fmt_p(latest['High'], digits)}` / `${_fmt_p(latest['Low'], digits)}`
* **Volume:** `{latest['Volume']:,.0f}` | **ATR(14) Volatility:** `${_fmt_p(latest['ATR'], digits)}`
* **RSI(14):** `{latest['RSI']:.2f}` *({rsi_status})*
* **MACD Indicator:** `{latest['MACD']:.4f}` vs Signal `{latest['MACD_Signal']:.4f}` *({macd_status}, Hist: {latest['MACD_Histogram']:+.4f})*

## 5. Automated System Confluence
> **SIGNAL:** **{signal}** | **Confidence Score:** `{confidence*100:.0f}%`
> **Initial Reference Setup:** Entry `${_fmt_p(latest['Close'], digits)}` | SL `${_fmt_p(sl_suggest, digits)}` | TP `${_fmt_p(tp_suggest, digits)}` *(1:1.67 R/R)*

---

# 🤖 INSTRUCTIONS & TASKS FOR AI MODEL

Act as an elite institutional quantitative hedge fund trader. Your intended trading style for this `{timeframe}` chart is **{style}**. Analyze the comprehensive quantitative dossier above and execute these strict tasks:

### TASK 1: MARKET REGIME & STRATEGY IDENTIFICATION
1. **Market Regime Diagnosis:** Diagnose the exact current market state (*Strong Trending, Range-Bound/Consolidation, or Volatility Expansion/Breakout*).
2. **Strategy Fit:** Recommend the single most effective trading strategy for this setup (e.g., *EMA Pullback Continuation, Support Bounce, Breakout Momentum, or Sit on Hands / No Trade*). Explain your quantitative reasoning.

### TASK 2: COST FEASIBILITY & RISK AUDIT
1. **Spread & Swap Audit:** Evaluate whether the broker spread (`{spread_pts} pts`) and overnight swap costs make this **{style}** trade thesis viable with positive expectancy.
2. **Precise Execution Plan:** Provide precise actionable levels for **Entry Zone**, **Stop Loss** *(MUST explicitly factor in the `{spread_pts} pts` spread buffer)*, and **Take Profit (TP1 & TP2)** adhering strictly to `{digits} decimal digits`.
3. **Invalidation Level:** Define the exact price level where this trading thesis is 100% invalidated.
"""
    return md


def format_report(symbol: str, timeframe: str, df: pd.DataFrame, broker_sym: str, acc_str: str, source_type: str, specs: dict, htf_trend: str, sup: float, res: float, recent_tbl: str, env_data: dict = None) -> str:
    return generate_md_dossier(symbol, timeframe, df, broker_sym, acc_str, source_type, specs, htf_trend, sup, res, recent_tbl, env_data)


def generate_ai_prompt(symbol: str, timeframe: str, df: pd.DataFrame, broker_sym: str, source_type: str, specs: dict, htf_trend: str, sup: float, res: float, recent_tbl: str, env_data: dict = None) -> str:
    return generate_md_dossier(symbol, timeframe, df, broker_sym, "", source_type, specs, htf_trend, sup, res, recent_tbl, env_data)


def analyze_symbol(symbol: str, timeframe: str = "1h") -> dict:
    """Modular function for Web Dashboard API"""
    df, broker_sym, acc_str, source_type = fetch_mt5_data(symbol, timeframe)
    if df is None:
        return {"error": f"Gagal mengambil data untuk simbol {symbol}"}

    df = calculate_indicators(df)
    if df is None:
        return {"error": "Gagal mengkalkulasi indikator teknikal"}

    specs = fetch_broker_specs(broker_sym, source_type)
    htf_trend = fetch_htf_trend(broker_sym, timeframe, source_type)
    sup, res = calculate_key_levels(df)
    recent_tbl = get_recent_candles_table(df, specs.get('digits', 2), count=5)

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
    signal, confidence = generate_signal(df)
    trend = "UPTREND (Bullish)" if latest['EMA20'] > latest['EMA50'] else "DOWNTREND (Bearish)"

    latest_ts = df.index[-1]
    session_str = identify_trading_session(latest_ts)
    patterns_list, pattern_status = detect_candlestick_patterns_vectorized(df)
    struct_mtf = get_structural_and_mtf_data(broker_sym, float(latest['Close']), source_type)

    env_data = {
        "session": session_str,
        "patterns": patterns_list,
        "pattern_status": pattern_status,
        "struct_mtf": struct_mtf
    }

    dossier = generate_md_dossier(symbol, timeframe, df, broker_sym, acc_str, source_type, specs, htf_trend, sup, res, recent_tbl, env_data)

    os.makedirs("reports", exist_ok=True)
    filename = f"analysis_{source_type}_{broker_sym}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join("reports", filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(dossier)
    except Exception:
        pass

    return {
        "success": True,
        "symbol": broker_sym,
        "source": source_type,
        "broker_info": acc_str,
        "timeframe": timeframe,
        "timestamp": df.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
        "current_price": float(latest['Close']),
        "price_change_pct": float(price_change),
        "high": float(latest['High']),
        "low": float(latest['Low']),
        "volume": float(latest['Volume']),
        "ema20": float(latest['EMA20']),
        "ema50": float(latest['EMA50']),
        "trend": trend,
        "rsi": float(latest['RSI']),
        "macd": float(latest['MACD']),
        "macd_signal": float(latest['MACD_Signal']),
        "macd_hist": float(latest['MACD_Histogram']),
        "bb_upper": float(latest['BB_Upper']),
        "bb_middle": float(latest['BB_Middle']),
        "bb_lower": float(latest['BB_Lower']),
        "atr": float(latest['ATR']),
        "signal": signal,
        "confidence": float(confidence * 100),
        "broker_spread": int(specs.get('spread', 0)),
        "broker_point": float(specs.get('point', 0.01)),
        "broker_digits": int(specs.get('digits', 2)),
        "broker_swap_long": float(specs.get('swap_long', 0.0)),
        "broker_swap_short": float(specs.get('swap_short', 0.0)),
        "key_support": float(sup),
        "key_resistance": float(res),
        "htf_trend": htf_trend,
        "market_environment": {
            "spread_points": int(specs.get('spread', 0)),
            "trading_session": session_str,
            "server_time_utc": str(pd.to_datetime(latest_ts).tz_localize(None))
        },
        "multi_timeframe_trend": struct_mtf.get('mtf_trend', {}),
        "structural_levels": {
            "daily_pivots": struct_mtf.get('daily_pivots', {}),
            "h4_swing_high": float(struct_mtf.get('h4_swing_high', res)),
            "h4_swing_low": float(struct_mtf.get('h4_swing_low', sup))
        },
        "candlestick_patterns": {
            "detected_patterns": patterns_list,
            "summary_status": pattern_status
        },
        "recent_candles": recent_tbl,
        "prompt": dossier,
        "report": dossier,
        "saved_file": filename
    }


def get_all_symbols() -> list:
    """Fetch all available symbol names from MT5 Market Watch or terminal, with fallback"""
    fallback_symbols = [
        "XAUUSD", "XAUUSDm", "XAUUSDc", "EURUSD", "EURUSDm", "GBPUSD", "GBPUSDm", 
        "USDJPY", "USDJPYm", "AUDUSD", "AUDUSDm", "USDCHF", "USDCHFm", 
        "USDCAD", "USDCADm", "NZDUSD", "NZDUSDm", "EURGBP", "EURGBPm", 
        "EURJPY", "EURJPYm", "GBPJPY", "GBPJPYm", "XAGUSD", "XAGUSDm", 
        "BTCUSD", "BTCUSDm", "ETHUSD", "ETHUSDm", "US30", "US30m", 
        "NAS100", "NAS100m", "SPX500", "SPX500m", "GER40", "GER40m",
        "UK100", "JP225", "OILUSD", "BRENT"
    ]
    if not mt5:
        return sorted(list(set(fallback_symbols)))

    mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    initialized = mt5.initialize(path=mt5_path) if os.path.exists(mt5_path) else mt5.initialize()
    if not initialized:
        return sorted(list(set(fallback_symbols)))

    try:
        symbols = mt5.symbols_get()
        if symbols:
            sym_list = [s.name for s in symbols]
            return sorted(list(set(sym_list)))
    except Exception:
        pass
    return sorted(list(set(fallback_symbols)))


def main():
    """Main function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 MT5 Direct Terminal Technical Analyzer (Zero-API Setup){Colors.RESET}\n")

    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}Usage: python trading_analyzer_mt5.py <symbol> [timeframe]{Colors.RESET}")
        print(f"{Colors.YELLOW}Example: python trading_analyzer_mt5.py XAUUSDm 1h{Colors.RESET}")
        print(f"Supported timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d\n")
        sys.exit(1)

    symbol = sys.argv[1]
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1h"

    df, broker_sym, acc_str, source_type = fetch_mt5_data(symbol, timeframe)
    if df is None:
        print(f"{Colors.RED}[!] Gagal mengambil data dari MT5 maupun yfinance.{Colors.RESET}")
        sys.exit(1)

    df = calculate_indicators(df)
    if df is None:
        sys.exit(1)

    specs = fetch_broker_specs(broker_sym, source_type)
    htf_trend = fetch_htf_trend(broker_sym, timeframe, source_type)
    sup, res = calculate_key_levels(df)
    recent_tbl = get_recent_candles_table(df, specs.get('digits', 2), count=5)

    latest_ts = df.index[-1]
    session_str = identify_trading_session(latest_ts)
    patterns_list, pattern_status = detect_candlestick_patterns_vectorized(df)
    struct_mtf = get_structural_and_mtf_data(broker_sym, float(df.iloc[-1]['Close']), source_type)

    env_data = {
        "session": session_str,
        "patterns": patterns_list,
        "pattern_status": pattern_status,
        "struct_mtf": struct_mtf
    }

    dossier = generate_md_dossier(symbol, timeframe, df, broker_sym, acc_str, source_type, specs, htf_trend, sup, res, recent_tbl, env_data)
    print(dossier)

    try:
        os.makedirs("reports", exist_ok=True)
        filename = f"analysis_{source_type}_{broker_sym}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join("reports", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(dossier)
        print(f"{Colors.GREEN}[✓] Analisis terpadu berformat Markdown tersimpan di: {filepath}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}[!] Gagal menyimpan file: {e}{Colors.RESET}")
    finally:
        if mt5 and source_type == "MT5":
            mt5.shutdown()


if __name__ == "__main__":
    main()
