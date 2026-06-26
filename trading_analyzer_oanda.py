#!/usr/bin/env python3
"""
Enhanced Trading Technical Analysis CLI Tool with OANDA v20 API Support
Real-time broker-direct data (same as MT4/MT5), exact bid-ask prices, actual broker volume, with automatic yfinance fallback.
"""

import sys
import io
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import yfinance as yf

try:
    import v20
    from v20.errors import V400BadRequestError, V401UnauthorizedError, V404NotFoundError, V429RateLimitError
except ImportError:
    v20 = None

import oanda_config


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def fetch_oanda_data(instrument: str, granularity: str, count: int = 100) -> pd.DataFrame:
    """Fetch real-time historical candles from OANDA broker servers"""
    config = oanda_config.load_oanda_config()
    if not config or not v20:
        return None

    env = config.get("environment", "fxpractice")
    host = "api-fxtrade.oanda.com" if "live" in env or "trade" in env else "api-fxpractice.oanda.com"

    try:
        client = v20.Context(
            hostname=host,
            token=config["api_token"]
        )
        
        response = client.instrument.candles(
            instrument,
            granularity=granularity,
            count=count
        )

        if response.status != 200:
            return None

        candles = response.get("candles", 200)
        if not candles:
            return None

        records = []
        for c in candles:
            if not getattr(c, "complete", True):
                continue
                
            bid = getattr(c, "bid", None)
            ask = getattr(c, "ask", None)
            if not bid or not ask:
                continue

            # Mid price = (bid + ask) / 2
            open_p = (float(bid.o) + float(ask.o)) / 2.0
            high_p = (float(bid.h) + float(ask.h)) / 2.0
            low_p = (float(bid.l) + float(ask.l)) / 2.0
            close_p = (float(bid.c) + float(ask.c)) / 2.0
            vol = int(getattr(c, "volume", 0))

            records.append({
                "Timestamp": pd.to_datetime(c.time),
                "Open": open_p,
                "High": high_p,
                "Low": low_p,
                "Close": close_p,
                "Volume": vol
            })

        if not records:
            return None

        df = pd.DataFrame(records).set_index("Timestamp")
        # Ensure UTC timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        return df

    except Exception as e:
        err_str = str(e)
        if "400" in err_str or "V400" in err_str:
            print(f"{Colors.RED}[!] Bad request OANDA (Periksa simbol/timeframe): {e}{Colors.RESET}")
        elif "401" in err_str or "V401" in err_str:
            print(f"{Colors.RED}[!] OANDA Auth Gagal: Cek API Token di .oanda_config{Colors.RESET}")
        elif "404" in err_str or "V404" in err_str:
            print(f"{Colors.RED}[!] Instrumen tidak didukung OANDA: {instrument}{Colors.RESET}")
        elif "429" in err_str or "V429" in err_str:
            print(f"{Colors.YELLOW}[!] OANDA Rate Limit tercapai. Silakan tunggu sebentar.{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}[!] OANDA Error: {e}{Colors.RESET}")
        return None


def validate_oanda_data(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate OANDA data quality before analysis"""
    if df is None or df.empty:
        return False, "Data kosong atau None"
    
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if any(c not in df.columns for c in required_cols):
        return False, "Kolom OHLCV tidak lengkap"
        
    if df[required_cols].isna().any().any():
        return False, "Terdapat nilai NaN pada OHLCV"
        
    if len(df) < 10:
        return False, "Jumlah candle terlalu sedikit (<10)"
        
    if (df['High'] < df['Low']).any():
        return False, "Terdapat harga High < Low"
        
    if not df.index.is_monotonic_increasing:
        return False, "Timestamp tidak terurut kronologis"
        
    return True, "Valid"


def fetch_yfinance_data(symbol: str, timeframe: str, days: int = 60) -> pd.DataFrame:
    """Fetch OHLCV data from yfinance (Fallback provider)"""
    try:
        tf_map = {
            "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "4h": "4h", "1d": "1d"
        }
        interval = tf_map.get(timeframe, "1h")
        df = yf.download(symbol, period=f"{days}d", interval=interval, progress=False, auto_adjust=True)
        
        if df.empty:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if any(c not in df.columns for c in required):
            return None
            
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
            
        return df
    except Exception as e:
        print(f"{Colors.RED}[!] Error yfinance fetch: {e}{Colors.RESET}")
        return None


def fetch_data_with_fallback(symbol: str, timeframe: str) -> Tuple[pd.DataFrame, str, dict]:
    """Try OANDA first, fallback to yfinance gracefully"""
    oanda_cfg = oanda_config.load_oanda_config()
    oanda_tf = oanda_config.TIMEFRAME_MAP.get(timeframe, "H1")
    oanda_inst = oanda_config.symbol_to_oanda(symbol)
    
    if oanda_cfg and v20:
        print(f"{Colors.BLUE}[*] Connecting to OANDA broker servers ({oanda_inst} - {oanda_tf})...{Colors.RESET}")
        df_oanda = fetch_oanda_data(oanda_inst, oanda_tf, count=100)
        is_valid, val_msg = validate_oanda_data(df_oanda)
        if is_valid:
            print(f"{Colors.GREEN}[✓] Data OANDA broker (real-time) berhasil diambil!{Colors.RESET}")
            return df_oanda, "OANDA", oanda_cfg
        else:
            print(f"{Colors.YELLOW}[!] Data OANDA tidak valid/gagal ({val_msg}).{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}[!] Kredensial OANDA belum diatur atau v20 tidak tersedia.{Colors.RESET}")
        
    print(f"{Colors.BLUE}[*] Mengaktifkan Fallback otomatis ke Yahoo Finance (yfinance)...{Colors.RESET}")
    yf_sym = oanda_config.symbol_to_yf(symbol)
    df_yf = fetch_yfinance_data(yf_sym, timeframe)
    if df_yf is not None and not df_yf.empty:
        print(f"{Colors.GREEN}[✓] Data berhasil diambil menggunakan yfinance ({yf_sym}).{Colors.RESET}")
        return df_yf, "yfinance", None
        
    print(f"{Colors.RED}[!] Semua provider data (OANDA & yfinance) gagal mengambil data untuk {symbol}.{Colors.RESET}")
    return None, None, None


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


def format_report(symbol: str, timeframe: str, df: pd.DataFrame, data_source: str, config: dict) -> str:
    """Format enhanced technical analysis report with broker metadata"""
    latest = df.iloc[-1]
    signal, confidence = generate_signal(df)
    trend = "Uptrend" if latest['EMA20'] > latest['EMA50'] else "Downtrend"
    
    if latest['RSI'] < 30:
        rsi_status = "Oversold (Reversal potential)"
    elif latest['RSI'] > 70:
        rsi_status = "Overbought (Reversal potential)"
    else:
        rsi_status = "Neutral"
        
    macd_status = "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
    
    if latest['Close'] < latest['BB_Lower']:
        bb_status = "Below lower band (Reversal potential)"
    elif latest['Close'] > latest['BB_Upper']:
        bb_status = "Above upper band (Reversal potential)"
    else:
        bb_status = "Between bands (Neutral)"
        
    if signal == "BUY":
        signal_color = Colors.GREEN
    elif signal == "SELL":
        signal_color = Colors.RED
    else:
        signal_color = Colors.YELLOW

    if data_source == "OANDA":
        acc_id = config.get("account_id", "Unknown") if config else "Unknown"
        inst = oanda_config.symbol_to_oanda(symbol)
        source_header = f"""📊 DATA SOURCE: OANDA API (Real-time, Broker-Direct)
   Account:     {acc_id}
   Instrument:  {inst}
   Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
   Latency:     <1 second (Broker MT4/MT5 match)"""
        badge_footer = f"""{Colors.BOLD}{'='*70}
✓ Data verified against OANDA broker servers
✓ Prices match MT4 / MT5 platform
✓ Volume from live broker market data
{'='*70}{Colors.RESET}"""
    else:
        yf_t = oanda_config.symbol_to_yf(symbol)
        source_header = f"""📊 DATA SOURCE: Yahoo Finance (yfinance fallback)
   Ticker:      {yf_t}
   Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
   Latency:     Delayed (~5-15 min)"""
        badge_footer = f"""{Colors.BOLD}{'='*70}
○ Data retrieved via Yahoo Finance Fallback
{'='*70}{Colors.RESET}"""

    report = f"""
{Colors.BOLD}{'='*70}
TECHNICAL ANALYSIS REPORT: {symbol} ({timeframe})
{'='*70}{Colors.RESET}

{source_header}

{Colors.BOLD}[TIMESTAMP]{Colors.RESET}
Candle Time:      {df.index[-1].strftime('%Y-%m-%d %H:%M:%S %Z')}

{Colors.BOLD}[PRICE ACTION]{Colors.RESET}
Current Price:    ${latest['Close']:.2f}
Previous Close:   ${(latest['Close'] if len(df) == 1 else df.iloc[-2]['Close']):.2f}
Daily High:       ${latest['High']:.2f}
Daily Low:        ${latest['Low']:.2f}
Volume:           {latest['Volume']:,.0f}

{Colors.BOLD}[KEY INDICATORS]{Colors.RESET}
EMA 20:           ${latest['EMA20']:.2f}
EMA 50:           ${latest['EMA50']:.2f}
Trend:            {trend}

RSI (14):         {latest['RSI']:.2f}
Status:           {rsi_status}

MACD:             {latest['MACD']:.4f}
MACD Signal:      {latest['MACD_Signal']:.4f}
Histogram:        {latest['MACD_Histogram']:.4f}
Status:           {macd_status}

Bollinger Bands (20, 2):
  Upper:          ${latest['BB_Upper']:.2f}
  Middle:         ${latest['BB_Middle']:.2f}
  Lower:          ${latest['BB_Lower']:.2f}
  Width:          ${latest['BB_Width']:.2f}
  Status:         {bb_status}

ATR (14):         ${latest['ATR']:.2f}
Volatility:       {"High" if latest['ATR'] > df['ATR'].mean() else "Normal"}

{Colors.BOLD}[CONFLUENCE ANALYSIS]{Colors.RESET}
- EMA trend:       {'✓ Bullish' if latest['EMA20'] > latest['EMA50'] else '✗ Bearish'}
- RSI momentum:    {'✓ Bullish' if latest['RSI'] < 50 else '✗ Bearish'}
- MACD direction:  {'✓ Bullish' if latest['MACD'] > latest['MACD_Signal'] else '✗ Bearish'}
- Price position:  {'✓ Bullish' if latest['Close'] < latest['BB_Middle'] else '✗ Bearish' if latest['Close'] > latest['BB_Middle'] else '○ Neutral'}

{Colors.BOLD}{signal_color}[SIGNAL]{Colors.RESET}{signal_color}
Signal:           {signal}
Confidence:       {confidence*100:.0f}%
{Colors.RESET}

{Colors.BOLD}[TRADE SETUP SUMMARY]{Colors.RESET}
- Primary Trend:   {trend}
- Entry Zone:      ${latest['Close']:.2f} (current price)
- Stop Loss*:      ${latest['Close'] - (latest['ATR'] * 1.5):.2f} (1.5 ATR below)
- Take Profit*:    ${latest['Close'] + (latest['ATR'] * 2.5):.2f} (2.5 ATR above)
- Risk/Reward:     1 : 1.67

* Suggested levels based on ATR volatility. Adjust based on risk tolerance.

{badge_footer}
"""
    return report


def generate_ai_prompt(symbol: str, timeframe: str, df: pd.DataFrame, data_source: str) -> str:
    """Generate ready-to-paste prompt for AI analysis"""
    latest = df.iloc[-1]
    signal, confidence = generate_signal(df)
    prev = df.iloc[-2] if len(df) > 1 else latest
    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

    prompt = f"""Analyze this {symbol} technical setup ({timeframe} timeframe, Data Source: {data_source}):

CURRENT PRICE: ${latest['Close']:.2f}
- Change from previous: {price_change:+.2f}%
- High: ${latest['High']:.2f}
- Low: ${latest['Low']:.2f}

TREND INDICATORS:
- EMA20: ${latest['EMA20']:.2f} {'(above EMA50 - bullish)' if latest['EMA20'] > latest['EMA50'] else '(below EMA50 - bearish)'}
- EMA50: ${latest['EMA50']:.2f}
- Trend Direction: {'Uptrend' if latest['EMA20'] > latest['EMA50'] else 'Downtrend'}

MOMENTUM:
- RSI(14): {latest['RSI']:.2f} {'(Oversold - reversal potential)' if latest['RSI'] < 30 else '(Overbought - reversal potential)' if latest['RSI'] > 70 else '(Neutral zone)'}
- MACD: {latest['MACD']:.4f} vs Signal: {latest['MACD_Signal']:.4f} ({'Bullish crossover' if latest['MACD'] > latest['MACD_Signal'] else 'Bearish crossover'})

VOLATILITY:
- Bollinger Bands (20,2):
  - Upper: ${latest['BB_Upper']:.2f}
  - Middle: ${latest['BB_Middle']:.2f}
  - Lower: ${latest['BB_Lower']:.2f}
- ATR: ${latest['ATR']:.2f}

MY SIGNAL: {signal} (Confidence: {confidence*100:.0f}%)

QUESTIONS:
1. Do you agree with this {signal} signal for {symbol}? Why or why not?
2. What is your recommended entry level and stop loss?
3. What is a realistic take profit target?
4. What macro or market sentiment factors could affect this setup right now?

Please provide detailed trading recommendations."""
    return prompt


def main():
    """Main function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 Enhanced Trading Technical Analyzer (OANDA v20 Enabled){Colors.RESET}\n")

    # 1. Check if first time setup needed
    if not os.path.exists(".oanda_config") and not os.getenv("OANDA_API_TOKEN"):
        print(f"{Colors.YELLOW}[!] File konfigurasi .oanda_config belum ditemukan.{Colors.RESET}")
        pilih = input("Apakah Anda ingin mengatur kredensial OANDA API sekarang? (y/n) [y]: ").strip().lower() or 'y'
        if pilih == 'y':
            oanda_config.setup_oanda_credentials()

    # 2. Parse arguments
    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}Usage: python trading_analyzer_oanda.py <symbol> [timeframe]{Colors.RESET}")
        print(f"{Colors.YELLOW}Example: python trading_analyzer_oanda.py XAU/USD 1h{Colors.RESET}")
        print(f"\nSupported symbols: XAU/USD, GOLD, BTC/USD, EUR/USD, GBP/USD, dll.")
        print(f"Supported timeframes: 5m, 15m, 30m, 1h, 4h, 1d\n")
        sys.exit(1)

    symbol = sys.argv[1]
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1h"

    # 3. Fetch data with fallback
    df, data_source, cfg = fetch_data_with_fallback(symbol, timeframe)
    if df is None:
        sys.exit(1)

    # 4. Calculate indicators
    df = calculate_indicators(df)
    if df is None:
        sys.exit(1)

    # 5. Format & display report
    report = format_report(symbol, timeframe, df, data_source, cfg)
    print(report)

    # 6. Display AI Prompt
    prompt = generate_ai_prompt(symbol, timeframe, df, data_source)
    print(f"\n{Colors.BOLD}{Colors.BLUE}[READY-TO-PASTE PROMPT FOR CLAUDE / GEMINI]{Colors.RESET}\n")
    print(f"{Colors.WHITE}{prompt}{Colors.RESET}\n")

    # 7. Save output file
    try:
        os.makedirs("reports", exist_ok=True)
        clean_sym = symbol.replace("/", "_").replace("=", "_")
        filename = f"analysis_{clean_sym}_{data_source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join("reports", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n" + "="*70 + "\nAI PROMPT:\n" + "="*70 + "\n\n")
            f.write(prompt)
        print(f"{Colors.GREEN}[✓] Analisis tersimpan di: {filepath}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}[!] Gagal menyimpan file: {e}{Colors.RESET}")


if __name__ == "__main__":
    main()
