# Trading Technical Analysis CLI Tool - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.8+ installed
- pip (Python package manager)

### 2. Installation

#### Option A: Desktop/Laptop (Windows, Mac, Linux)

```bash
# 1. Clone/download the files
# Place these files in a folder:
#   - trading_analyzer.py
#   - requirements.txt

# 2. Open terminal/command prompt in that folder

# 3. Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the tool
python trading_analyzer.py XAU/USD 1h
```

#### Option B: Android Phone (Using Termux)

```bash
# 1. Install Termux from Play Store (https://play.google.com/store/apps/details?id=com.termux)

# 2. Open Termux and run:
apt update
apt install python pip git

# 3. Download files (clone or copy)
# Create folder:
mkdir trading-analyzer
cd trading-analyzer

# Copy trading_analyzer.py and requirements.txt into this folder

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run
python trading_analyzer.py XAU/USD 1h
```

---

## MetaTrader 5 (MT5 Windows) Direct Terminal Integration (Zero-API Setup)

Bagi Anda pengguna Windows yang memiliki aplikasi terminal **MetaTrader 5 Exness** terbuka di desktop, Anda bisa menggunakan `trading_analyzer_mt5.py`.

### Keunggulan Utama:
- **100% Tanpa Daftar API**: Tidak butuh registrasi API token, tidak butuh Account ID khusus, tidak butuh file konfigurasi kredensial `.env`.
- **Persis Chart Exness Anda**: Harga Bid, Ask, Spread, dan Tick Volume diambil langsung dari terminal MT5 lokal Anda secara instan (<0.05 detik).

### Cara Menjalankan:
1. Pastikan aplikasi desktop **MetaTrader 5 Exness** Anda sedang terbuka dan login ke akun trading (Demo/Real).
2. Buka terminal Windows lalu ketik:
   ```bash
   python trading_analyzer_mt5.py XAUUSDm 1h
   ```
   *(Jika akun Exness Anda Standard/Pro, biasanya simbol berakhiran `m`, contoh: `EURUSDm`, `BTCUSDm`).*

---

## OANDA API v20 Setup & Multi-Provider Data

Fitur baru `trading_analyzer_oanda.py` memungkinkan pengambilan data harga bid-ask dan volume langsung dari server broker OANDA (100% real-time, cocok dengan MT4/MT5). Jika koneksi OANDA gagal, script akan **otomatis fallback ke yfinance**.

### 1. Cara Mendapatkan OANDA API Token
1. Login ke platform [OANDA](https://www.oanda.com) (Anda bisa menggunakan akun Demo `fxpractice` atau Real `fxlive`).
2. Masuk ke menu **Manage API Access** (atau **Account Settings** -> **API Access**).
3. Klik **Generate API Token** (v20 REST API).
4. Salin **Account ID** Anda (format: `101-123-456789-001`) dan **API Token** Anda.

### 2. Konfigurasi Kredensial
Saat Anda menjalankan `trading_analyzer_oanda.py` pertama kali, script akan otomatis memunculkan panduan interaktif di terminal untuk memasukkan Account ID dan API Token, lalu menyimpannya secara aman di file `.oanda_config`.

Atau, Anda juga bisa membuat file `.env` (copy dari `.oanda_config.example`):
```env
OANDA_ACCOUNT_ID="101-123-456789-001"
OANDA_API_TOKEN="abc123xyz_token_anda"
OANDA_ENVIRONMENT="fxpractice"
```

---

## Usage

### Basic Usage
```bash
python trading_analyzer.py <SYMBOL> [TIMEFRAME]
```

### Examples

**Gold (XAU/USD) - 1 Hour**
```bash
python trading_analyzer.py XAU/USD 1h
```

**Bitcoin - 4 Hour**
```bash
python trading_analyzer.py BTC-USD 4h
```

**EUR/USD - 15 Minutes**
```bash
python trading_analyzer.py EURUSD=X 15m
```

**ETH/USD - Daily**
```bash
python trading_analyzer.py ETH-USD 1d
```

### Supported Symbols

**Precious Metals:**
- `XAU/USD` or `XAU=F` (Gold)
- `XAG/USD` (Silver)

**Cryptocurrency:**
- `BTC-USD` (Bitcoin)
- `ETH-USD` (Ethereum)
- `SOL-USD` (Solana)
- etc. (any crypto with -USD suffix)

**Forex:**
- `EURUSD=X` (EUR/USD)
- `GBPUSD=X` (GBP/USD)
- `AUDUSD=X` (AUD/USD)
- etc. (format: XXXYYY=X)

### Supported Timeframes
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day

---

## What You Get

### Output Includes:

1. **Technical Analysis Report**
   - Current price + volume
   - EMA 20/50 (trend)
   - RSI (momentum)
   - MACD (direction)
   - Bollinger Bands (volatility)
   - ATR (volatility measure)
   - Confluence analysis

2. **Signal Generation**
   - BUY / SELL / NEUTRAL
   - Confidence percentage
   - Suggested Stop Loss (1.5 ATR below)
   - Suggested Take Profit (2.5 ATR above)

3. **Ready-to-Paste AI Prompt**
   - Formatted data for Claude/Gemini
   - All indicators included
   - Pre-written questions for AI analysis
   - Just copy → paste → get analysis

4. **Auto-save to file**
   - File saved as: `analysis_XAU_USD_20260626_143000.txt`
   - Contains full report + AI prompt

---

## Workflow Example

```
$ python trading_analyzer.py XAU/USD 1h

[*] Fetching data for XAU/USD (1h)...
[*] Calculating indicators...

========================================
TECHNICAL ANALYSIS REPORT: XAU/USD (1h)
========================================

[TIMESTAMP]
Generated: 2026-06-26 14:30:00 UTC

[PRICE ACTION]
Current Price:    $2050.25
...

[KEY INDICATORS]
EMA 20:           $2048.75
EMA 50:           $2045.00
...

[SIGNAL]
Signal:           BUY
Confidence:       70%

========================================
READY TO PASTE PROMPT FOR AI ANALYSIS
========================================

Analyze this XAU/USD technical setup (1h timeframe):

CURRENT PRICE: $2050.25
...

MY SIGNAL: BUY (Confidence: 70%)

QUESTIONS:
1. Do you agree with this BUY signal?
...

[✓] Analysis saved to: analysis_XAU_USD_20260626_143000.txt
```

**Next Step:**
1. Copy the prompt (from "Analyze this XAU/USD..." to end)
2. Paste into Claude.ai or Gemini
3. Get detailed analysis + entry/exit levels
4. Execute trade in Exness

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'yfinance'"
**Solution:** Install dependencies again
```bash
pip install -r requirements.txt
```

### Issue: "No data found for XAU/USD"
**Solution:** Try alternative symbol
- Use `XAU=F` instead of `XAU/USD`
- Use `GC=F` for gold futures

### Issue: Script won't run on Termux
**Solution:**
```bash
# Make it executable
chmod +x trading_analyzer.py

# Run with python explicitly
python3 trading_analyzer.py XAU/USD 1h
```

### Issue: Very slow data fetch
**Solution:** 
- This is normal first time (downloading 30 days data)
- Subsequent runs are cached by yfinance
- Use shorter timeframe (5m, 15m) for faster fetch

---

## Advanced Usage

### Change data lookback period
Edit `trading_analyzer.py`, line ~40:
```python
days: int = 30  # Change this number (default 30 days)
```

### Customize indicators
Edit `calculate_indicators()` function to add/remove indicators

### Automate runs
**Windows (Task Scheduler):**
```batch
# Create batch file: run_analysis.bat
python C:\path\to\trading_analyzer.py XAU/USD 1h
```
Then schedule via Task Scheduler

**Mac/Linux (Cron):**
```bash
# Run every hour
0 * * * * cd /path/to/script && python trading_analyzer.py XAU/USD 1h
```

---

## Tips

1. **Use 1H timeframe** for intraday analysis (sweet spot for gold)
2. **Run during market hours** (gold market: 2am-1am UTC)
3. **Copy entire prompt** to AI for best analysis
4. **Save files** for trade journal/review
5. **Backtest first** - run multiple symbols to see pattern accuracy

---

## Support / Issues

If script crashes:
1. Check Python version: `python --version` (should be 3.8+)
2. Reinstall requirements: `pip install -r requirements.txt --upgrade`
3. Check internet connection (needs to fetch data)
4. Try different symbol if data not found

---

## Next Steps

1. ✅ Run: `python trading_analyzer.py XAU/USD 1h`
2. ✅ Copy the AI prompt
3. ✅ Paste to Claude/Gemini
4. ✅ Get detailed analysis
5. ✅ Execute trade in Exness
6. ✅ Log results in your trade journal (Notion?)

---

**Happy trading! 🚀**
