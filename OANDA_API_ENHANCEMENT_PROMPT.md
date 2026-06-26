# Enhanced Trading Analyzer with OANDA API - Development Prompt

## PROJECT OBJECTIVE

Upgrade the existing trading_analyzer.py script to use **OANDA API** instead of yfinance for:
1. Real-time, broker-direct data (same as MT4)
2. Accurate bid-ask prices (not approximations)
3. Actual broker volume data
4. Consistent with user's trading account

---

## CURRENT STATE

**Existing Script (trading_analyzer.py):**
- Uses: yfinance library
- Data source: Yahoo Finance (delayed, aggregated)
- Accuracy: ~95% (differs from MT4)
- Problem: Price mismatches with broker

**Desired State:**
- Uses: OANDA v20 API
- Data source: OANDA servers (real-time)
- Accuracy: 99.99% (matches MT4)
- Benefit: Direct broker data

---

## TECHNICAL REQUIREMENTS

### 1. OANDA API SETUP

**Authentication:**
```python
import v20

# OANDA credentials (user provides these)
OANDA_ACCOUNT_ID = "user_input"  # e.g., "101-123-456789-001"
OANDA_API_TOKEN = "user_input"   # e.g., "abc123xyz..."
OANDA_ENVIRONMENT = "fxpractice" or "fxpractice" (demo vs live)

# Connect
client = v20.Context(
    hostname=f"https://stream-{OANDA_ENVIRONMENT}.oanda.com",
    token=OANDA_API_TOKEN,
    username=OANDA_ACCOUNT_ID
)
```

**Instruments supported by OANDA:**
```
Metals:
- "XAU_USD" (Gold/USD) ← Main focus
- "XAG_USD" (Silver/USD)

Crypto (CFD):
- "BTC_USD" (Bitcoin)
- "ETH_USD" (Ethereum)

Forex:
- "EUR_USD"
- "GBP_USD"
- etc.
```

### 2. DATA FETCHING LOGIC

**Fetch OHLCV Candles:**
```python
def fetch_oanda_data(instrument, granularity, count=100):
    """
    Fetch historical candles from OANDA
    
    Args:
        instrument: "XAU_USD" (OANDA format)
        granularity: "M5", "M15", "H1", "H4", "D" (OANDA format)
        count: number of candles (max 5000)
    
    Returns:
        DataFrame with OHLCV data
    
    Response structure:
    {
        "candles": [
            {
                "complete": true,
                "bid": {
                    "o": "4050.25",  # open
                    "h": "4055.00",
                    "l": "4048.50",
                    "c": "4053.75"
                },
                "ask": {
                    "o": "4050.35",
                    "h": "4055.10",
                    "l": "4048.60",
                    "c": "4053.85"
                },
                "volume": 523,
                "time": "2026-06-26T05:00:00Z"
            }
        ]
    }
    
    Implementation:
    - Use mid-price: (bid + ask) / 2
    - Use bid volume for analysis
    - Convert to pandas DataFrame
    - Handle timestamps (UTC)
    """
    pass
```

**Timeframe Mapping:**
```python
TIMEFRAME_MAP = {
    "5m": "M5",
    "15m": "M15",
    "30m": "M30",
    "1h": "H1",
    "4h": "H4",
    "1d": "D"
}

# Convert user input to OANDA format
oanda_tf = TIMEFRAME_MAP.get(user_timeframe)
```

### 3. ERROR HANDLING

**Handle common OANDA errors:**
```python
try:
    response = client.instrument.candles(...)
except v20.errors.V400BadRequestError as e:
    # Invalid request (wrong instrument, granularity, etc)
    print(f"Bad request: {e.msg}")
except v20.errors.V401UnauthorizedError as e:
    # Invalid API key/token
    print("Auth failed: Check OANDA_API_TOKEN")
except v20.errors.V404NotFoundError as e:
    # Instrument not found in OANDA
    print(f"Instrument not supported: {instrument}")
except v20.errors.V429RateLimitError as e:
    # Rate limit hit
    print("Rate limited: Wait 1 minute")
except ConnectionError as e:
    # Network error
    print("Connection failed: Check internet")
except Exception as e:
    # Fallback to yfinance
    print(f"OANDA error: {e}, falling back to yfinance")
    return fetch_yfinance_data(symbol, timeframe)  # Graceful degradation
```

### 4. DATA VALIDATION

**Ensure data quality:**
```python
def validate_oanda_data(df):
    """
    Validate OANDA data before analysis
    
    Checks:
    - No NaN values in OHLCV
    - Volume > 0
    - High >= Low
    - Close between High and Low
    - Timestamps in chronological order
    - No duplicate timestamps
    
    Return: (is_valid: bool, error_message: str)
    """
    pass
```

---

## SCRIPT STRUCTURE

### **New Architecture:**

```
trading_analyzer_oanda.py
├── OANDA API Connection
│   ├── authenticate()
│   ├── fetch_oanda_data()
│   └── validate_oanda_data()
├── Data Processing (unchanged)
│   ├── calculate_indicators()
│   └── generate_signal()
├── Report Generation (enhanced)
│   ├── format_report()
│   ├── generate_ai_prompt()
│   └── add_oanda_metadata()
├── CLI Interface (updated)
│   └── main()
└── Utils
    ├── fallback_to_yfinance()
    └── config_oanda()
```

### **Main Function Update:**

```python
def main():
    """Main function with OANDA support"""
    
    # 1. Setup OANDA (first time only)
    if not os.path.exists(".oanda_config"):
        setup_oanda_credentials()  # Interactive setup
    
    # 2. Load credentials
    oanda_config = load_oanda_config()
    
    # 3. Parse arguments
    symbol = sys.argv[1]  # e.g., "XAU/USD"
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1h"
    
    # 4. Convert to OANDA format
    oanda_instrument = symbol_to_oanda(symbol)  # "XAU/USD" → "XAU_USD"
    oanda_tf = TIMEFRAME_MAP[timeframe]
    
    # 5. Fetch OANDA data
    print(f"[*] Connecting to OANDA...")
    df = fetch_oanda_data(oanda_instrument, oanda_tf, count=100)
    
    if df is None:
        print(f"[!] OANDA failed, falling back to yfinance...")
        df = fetch_yfinance_data(symbol, timeframe)
    
    # 6. Calculate indicators (unchanged)
    df = calculate_indicators(df)
    
    # 7. Generate report (enhanced)
    report = format_report(symbol, timeframe, df, data_source="OANDA")
    print(report)
    
    # 8. Generate AI prompt
    prompt = generate_ai_prompt(symbol, timeframe, df)
    print(prompt)
    
    # 9. Add OANDA metadata
    add_oanda_metadata(report, oanda_config)
```

---

## FIRST-TIME SETUP

### **Interactive Configuration:**

```python
def setup_oanda_credentials():
    """Interactive OANDA setup (runs once)"""
    
    print("""
    ╔════════════════════════════════════════════╗
    ║      OANDA API Configuration Setup         ║
    ║  (Run this once, credentials saved)        ║
    ╚════════════════════════════════════════════╝
    
    Get your OANDA credentials:
    1. Visit: https://www.oanda.com (open account if needed)
    2. Login to platform
    3. Go to: Account Settings → API Access
    4. Generate API Token (v20 REST API)
    5. Copy Account ID (format: 101-123-456789-001)
    """)
    
    account_id = input("Enter OANDA Account ID: ").strip()
    api_token = input("Enter OANDA API Token: ").strip()
    environment = input("Environment (fxpractice=demo, fxlive=real) [fxpractice]: ").strip() or "fxpractice"
    
    # Validate
    print("[*] Testing OANDA connection...")
    if validate_oanda_credentials(account_id, api_token, environment):
        print("[✓] Credentials valid!")
        save_oanda_config(account_id, api_token, environment)
    else:
        print("[!] Invalid credentials. Try again.")
        return setup_oanda_credentials()
```

**Save credentials securely:**
```python
def save_oanda_config(account_id, api_token, environment):
    """Save to encrypted .oanda_config file"""
    config = {
        "account_id": account_id,
        "api_token": api_token,
        "environment": environment,
        "timestamp": datetime.now().isoformat()
    }
    
    # Use keyring or simple .gitignore'd file
    # IMPORTANT: Add .oanda_config to .gitignore
    
    with open(".oanda_config", "w") as f:
        json.dump(config, f)
    
    os.chmod(".oanda_config", 0o600)  # Read-only
    print("[✓] Credentials saved to .oanda_config")
```

---

## USAGE EXAMPLES

### **First Run (Setup):**
```bash
python trading_analyzer_oanda.py
# → Prompts for OANDA credentials
# → Saves securely
# → Exits (setup complete)
```

### **Subsequent Runs (Normal Analysis):**
```bash
# Gold 1-hour
python trading_analyzer_oanda.py XAU/USD 1h

# Bitcoin 15-minute
python trading_analyzer_oanda.py BTC-USD 15m

# EUR/USD 4-hour
python trading_analyzer_oanda.py EUR/USD 4h
```

### **With Fallback (If OANDA fails):**
```bash
python trading_analyzer_oanda.py XAU/USD 1h --fallback
# → Tries OANDA first
# → Falls back to yfinance if OANDA down
# → Shows which data source used in report
```

---

## REPORT ENHANCEMENT

### **Add Data Source Info:**

At top of report:
```
═══════════════════════════════════════════════════════════════════════
TECHNICAL ANALYSIS REPORT: XAU/USD (1h)
═══════════════════════════════════════════════════════════════════════

📊 DATA SOURCE: OANDA API (Real-time, Broker-Direct)
   Account: 101-123-456789-001
   Instrument: XAU_USD
   Last update: 2026-06-26 17:22:52 UTC
   Data latency: <1 second

[REST OF REPORT UNCHANGED]
```

### **Add Data Quality Badge:**

In report footer:
```
═══════════════════════════════════════════════════════════════════════
✓ Data verified against OANDA broker servers
✓ Prices match MT4 platform
✓ Volume from live market data
═══════════════════════════════════════════════════════════════════════
```

---

## DEPENDENCIES

**New requirements.txt:**
```
yfinance==0.2.38
pandas==2.2.0
pandas-ta==0.3.14b0
v20==3.0.41
requests==2.31.0
python-dotenv==1.0.0
keyring==24.0.0
```

**Installation:**
```bash
pip install -r requirements.txt
```

---

## FALLBACK STRATEGY

**If OANDA fails:**
```python
def fetch_data_with_fallback(symbol, timeframe):
    """Try OANDA first, fallback to yfinance"""
    
    try:
        # Try OANDA
        oanda_instrument = symbol_to_oanda(symbol)
        df = fetch_oanda_data(oanda_instrument, timeframe_map[timeframe])
        if df is not None:
            return df, "OANDA"  # Success
    except Exception as e:
        print(f"[!] OANDA error: {e}")
    
    try:
        # Fallback to yfinance
        print(f"[*] Falling back to yfinance...")
        df = fetch_yfinance_data(symbol, timeframe)
        return df, "yfinance"  # Fallback
    except Exception as e:
        print(f"[!] yfinance also failed: {e}")
        return None, None
```

---

## TESTING CHECKLIST

Before deployment:

```
☐ OANDA authentication works
☐ Can fetch XAU_USD data (1h, 15m, 5m)
☐ Can fetch BTC_USD data
☐ Can fetch EUR_USD data
☐ Indicators calculate correctly on OANDA data
☐ Signal generation matches manual MT4 analysis
☐ Prices match MT4 platform
☐ Fallback to yfinance works
☐ Error messages are clear
☐ Credentials stored securely
☐ Report format unchanged (just add data source)
☐ AI prompt generates correctly
☐ Works on CLI (terminal)
☐ Works on Termux (Android)
```

---

## COMPARISON AFTER UPGRADE

| Aspect | Before (yfinance) | After (OANDA) |
|--------|-------------------|---------------|
| Data source | Yahoo Finance | OANDA Broker |
| Accuracy | ~95% | 99.99% |
| Latency | 5-15 min delay | <1 second |
| Price match MT4 | ❌ Often differs | ✅ Exact match |
| Volume | Aggregated | Broker actual |
| Bid-ask | Mid-price est | Exact broker prices |
| Setup time | Instant | ~5 min (first time) |

---

## DOCUMENTATION TO INCLUDE

1. **README update:**
   - How to get OANDA API token
   - Setup instructions
   - Troubleshooting common errors

2. **SETUP_GUIDE.md update:**
   - OANDA setup section
   - Credentials security notes
   - Data accuracy comparison

3. **In-code comments:**
   - Explain OANDA API calls
   - Document symbol mapping
   - Note timeframe differences

---

## DELIVERABLES

1. `trading_analyzer_oanda.py` - Main script (OANDA-enabled)
2. `oanda_config.py` - OANDA configuration module
3. Updated `requirements.txt`
4. Updated `SETUP_GUIDE.md` (with OANDA section)
5. `FAQ_OANDA.md` (troubleshooting)
6. `.oanda_config.example` (template, not actual credentials)

---

## NOTES FOR DEVELOPER (AI AGENT)

1. **Don't hardcode credentials** - Always prompt user or read from secure config
2. **Error handling is critical** - OANDA API can timeout, rate limit, or reject requests
3. **Fallback to yfinance** - Users should never get "no data" error
4. **Test thoroughly** - Verify OANDA prices match MT4 before releasing
5. **Keep backward compatibility** - Script should work with/without OANDA
6. **Security first** - Never log API tokens or credentials
7. **Clear messaging** - User should know if using OANDA or yfinance
8. **Document well** - People need to understand setup process

---

## SUCCESS CRITERIA

✅ Script runs without yfinance (OANDA only) option
✅ Prices from OANDA match MT4 platform (within 1 pip)
✅ Credentials stored securely, never exposed
✅ Graceful fallback to yfinance if OANDA fails
✅ Report clearly shows data source used
✅ Setup takes <5 minutes (first time)
✅ Works on desktop, laptop, Termux (Android)
✅ All existing features work unchanged
✅ Signal accuracy improved (fewer false signals)
✅ User trusts the data = takes more trades = profits!

---

**Ready to build? Start with OANDA authentication module, then data fetching, then integrate into existing script.**
