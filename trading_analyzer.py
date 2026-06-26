#!/usr/bin/env python3
"""
Trading Technical Analysis CLI Tool
Analyze XAU/USD, crypto, forex dengan indicators + ready-to-paste AI prompt
"""

import sys
import io
# Fix encoding hanya di Windows — Termux/Linux sudah UTF-8 by default
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple

# Color codes untuk terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def fetch_data(symbol: str, timeframe: str = "1h", days: int = 60) -> pd.DataFrame:
    """Fetch OHLCV data dari yfinance"""
    try:
        print(f"{Colors.BLUE}[*] Fetching data for {symbol} ({timeframe})...{Colors.RESET}")
        
        # Map timeframe ke yfinance interval
        tf_map = {
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        
        interval = tf_map.get(timeframe, "1h")
        
        # Download data
        df = yf.download(symbol, period=f"{days}d", interval=interval,
                         progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"{Colors.RED}[!] No data found for {symbol}{Colors.RESET}")
            return None
        
        # yfinance v1+ mengembalikan MultiIndex columns — ratakan ke single level
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Pastikan kolom standar OHLCV ada
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"{Colors.RED}[!] Kolom tidak ditemukan: {missing}{Colors.RESET}")
            return None
        
        return df
    except Exception as e:
        print(f"{Colors.RED}[!] Error fetching data: {e}{Colors.RESET}")
        return None


# ── Pure pandas/numpy indicator helpers (no pandas-ta / numba needed) ──────
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
# ───────────────────────────────────────────────────────────────────────────


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators (pure pandas/numpy — works on Termux too)"""
    try:
        print(f"{Colors.BLUE}[*] Calculating indicators...{Colors.RESET}")
        
        close = df['Close']

        # EMA & SMA
        df['EMA20'] = _ema(close, 20)
        df['EMA50'] = _ema(close, 50)
        df['SMA20'] = _sma(close, 20)
        df['SMA50'] = _sma(close, 50)

        # RSI
        df['RSI'] = _rsi(close, 14)

        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = _macd(close)

        # Bollinger Bands
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = _bbands(close)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']

        # ATR
        df['ATR'] = _atr(df['High'], df['Low'], close)

        return df
    except Exception as e:
        print(f"{Colors.RED}[!] Error calculating indicators: {e}{Colors.RESET}")
        return None


def generate_signal(df: pd.DataFrame) -> Tuple[str, float]:
    """Generate BUY/SELL/NEUTRAL signal based on confluence"""
    latest = df.iloc[-1]
    
    # Count bullish signals
    bullish_count = 0
    bearish_count = 0
    
    # EMA trend
    if latest['EMA20'] > latest['EMA50']:
        bullish_count += 1
    else:
        bearish_count += 1
    
    # RSI
    if latest['RSI'] < 30:
        bullish_count += 1  # Oversold = potential bounce
    elif latest['RSI'] > 70:
        bearish_count += 1  # Overbought = potential reversal
    
    # MACD
    if latest['MACD'] > latest['MACD_Signal']:
        bullish_count += 1
    else:
        bearish_count += 1
    
    # Bollinger Bands
    if latest['Close'] < latest['BB_Lower']:
        bullish_count += 1
    elif latest['Close'] > latest['BB_Upper']:
        bearish_count += 1
    
    # Determine signal
    total_signals = bullish_count + bearish_count
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

def format_report(symbol: str, timeframe: str, df: pd.DataFrame) -> str:
    """Format detailed report"""
    latest = df.iloc[-1]
    signal, confidence = generate_signal(df)
    
    # Determine trend
    trend = "Uptrend" if latest['EMA20'] > latest['EMA50'] else "Downtrend"
    
    # RSI interpretation
    if latest['RSI'] < 30:
        rsi_status = "Oversold (Reversal potential)"
    elif latest['RSI'] > 70:
        rsi_status = "Overbought (Reversal potential)"
    else:
        rsi_status = "Neutral"
    
    # MACD interpretation
    macd_status = "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
    
    # Bollinger interpretation
    if latest['Close'] < latest['BB_Lower']:
        bb_status = "Below lower band (Reversal potential)"
    elif latest['Close'] > latest['BB_Upper']:
        bb_status = "Above upper band (Reversal potential)"
    else:
        bb_status = "Between bands (Neutral)"
    
    # Color signal
    if signal == "BUY":
        signal_color = Colors.GREEN
    elif signal == "SELL":
        signal_color = Colors.RED
    else:
        signal_color = Colors.YELLOW
    
    report = f"""
{Colors.BOLD}{'='*70}
TECHNICAL ANALYSIS REPORT: {symbol} ({timeframe})
{'='*70}{Colors.RESET}

{Colors.BOLD}[TIMESTAMP]{Colors.RESET}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Last candle: {df.index[-1].strftime('%Y-%m-%d %H:%M:%S')}

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
Indicators aligned: Yes/No (check below)
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
- Risk/Reward:     {(2.5):.1f}:1.5

* These are suggested levels based on ATR volatility. Adjust based on your risk tolerance.

{Colors.BOLD}{'='*70}
READY TO PASTE PROMPT FOR AI ANALYSIS
{'='*70}{Colors.RESET}

"""
    
    return report

def generate_ai_prompt(symbol: str, timeframe: str, df: pd.DataFrame) -> str:
    """Generate ready-to-paste prompt for AI"""
    latest = df.iloc[-1]
    signal, confidence = generate_signal(df)
    
    # Get previous candle for comparison
    prev = df.iloc[-2] if len(df) > 1 else latest
    price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
    
    prompt = f"""
Analyze this XAU/USD technical setup ({timeframe} timeframe):

CURRENT PRICE: ${latest['Close']:.2f}
- Change from previous: {price_change:+.2f}%
- 24h High: ${latest['High']:.2f}
- 24h Low: ${latest['Low']:.2f}

TREND INDICATORS:
- EMA20: ${latest['EMA20']:.2f} {'(above EMA50 - bullish)' if latest['EMA20'] > latest['EMA50'] else '(below EMA50 - bearish)'}
- EMA50: ${latest['EMA50']:.2f}
- Trend Direction: {'Uptrend' if latest['EMA20'] > latest['EMA50'] else 'Downtrend'}

MOMENTUM:
- RSI(14): {latest['RSI']:.2f} {'(Oversold - reversal potential)' if latest['RSI'] < 30 else '(Overbought - reversal potential)' if latest['RSI'] > 70 else '(Neutral zone)'}
- MACD: {latest['MACD']:.4f} vs Signal: {latest['MACD_Signal']:.4f} ({'Bullish crossover' if latest['MACD'] > latest['MACD_Signal'] else 'Bearish crossover'})

VOLATILITY:
- Bollinger Bands (20,2):
  - Price: ${latest['Close']:.2f}
  - Upper: ${latest['BB_Upper']:.2f}
  - Middle: ${latest['BB_Middle']:.2f}
  - Lower: ${latest['BB_Lower']:.2f}
  - Status: {'Price near lower band (Reversal zone)' if latest['Close'] < latest['BB_Lower'] + (latest['BB_Width']*0.2) else 'Price near upper band' if latest['Close'] > latest['BB_Upper'] - (latest['BB_Width']*0.2) else 'Mid-range'}
- ATR: ${latest['ATR']:.2f}

MY SIGNAL: {signal} (Confidence: {confidence*100:.0f}%)

QUESTIONS:
1. Do you agree with this {signal} signal? Why or why not?
2. What's your entry level and stop loss? (suggest ATR-based levels)
3. What's realistic take profit target?
4. What's the risk/reward ratio?
5. Any confluence factors I'm missing?
6. Market sentiment/macro factors that could affect this setup?

Please provide detailed analysis with entry/exit levels.
"""
    
    return prompt

def main():
    """Main function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 Trading Technical Analysis CLI{Colors.RESET}\n")
    
    # Parse arguments
    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}Usage: python trading_analyzer.py <symbol> [timeframe]{Colors.RESET}")
        print(f"{Colors.YELLOW}Example: python trading_analyzer.py XAU/USD 1h{Colors.RESET}")
        print(f"\nSupported symbols:")
        print(f"  - Gold: XAU=F (or XAUUSD)")
        print(f"  - Bitcoin: BTC-USD")
        print(f"  - Ethereum: ETH-USD")
        print(f"  - EUR/USD: EURUSD=X")
        print(f"  - GBP/USD: GBPUSD=X")
        print(f"\nSupported timeframes: 5m, 15m, 30m, 1h, 4h, 1d")
        sys.exit(1)
    
    symbol = sys.argv[1]
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1h"
    
    # Auto-konversi ticker umum ke format Yahoo Finance
    TICKER_ALIASES = {
        'XAU/USD': 'GC=F', 'XAUUSD': 'GC=F', 'GOLD': 'GC=F',
        'XAG/USD': 'SI=F', 'XAGUSD': 'SI=F', 'SILVER': 'SI=F',
        'BTC/USD': 'BTC-USD', 'BTCUSD': 'BTC-USD',
        'ETH/USD': 'ETH-USD', 'ETHUSD': 'ETH-USD',
        'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X',
        'USD/JPY': 'JPY=X',   'AUD/USD': 'AUDUSD=X',
    }
    symbol_upper = symbol.upper()
    if symbol_upper in TICKER_ALIASES:
        original = symbol
        symbol = TICKER_ALIASES[symbol_upper]
        print(f"{Colors.YELLOW}[~] '{original}' → '{symbol}' (Yahoo Finance format){Colors.RESET}")
    
    # Fetch data
    df = fetch_data(symbol, timeframe)

    if df is None:
        sys.exit(1)
    
    # Calculate indicators
    df = calculate_indicators(df)
    if df is None:
        sys.exit(1)
    
    # Generate report
    report = format_report(symbol, timeframe, df)
    print(report)
    
    # Generate AI prompt
    prompt = generate_ai_prompt(symbol, timeframe, df)
    print(f"\n{Colors.BOLD}{Colors.BLUE}[COPY THIS PROMPT BELOW TO PASTE IN CLAUDE/GEMINI]{Colors.RESET}\n")
    print(f"{Colors.WHITE}{prompt}{Colors.RESET}\n")
    
    # Save to file option
    try:
        os.makedirs("reports", exist_ok=True)
        filename = f"analysis_{symbol.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join("reports", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n\n" + "="*70 + "\n")
            f.write("AI PROMPT:\n")
            f.write("="*70 + "\n\n")
            f.write(prompt)
        print(f"{Colors.GREEN}[✓] Analysis saved to: {filepath}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.YELLOW}[!] Could not save file: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()
