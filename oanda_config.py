#!/usr/bin/env python3
"""
OANDA Configuration & Symbol Mapping Module
Manages OANDA API credentials securely and maps tickers between user input, OANDA, and Yahoo Finance.
"""

import os
import sys
import json
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CONFIG_FILE = ".oanda_config"

TIMEFRAME_MAP = {
    "5m": "M5",
    "15m": "M15",
    "30m": "M30",
    "1h": "H1",
    "4h": "H4",
    "1d": "D"
}

OANDA_ALIASES = {
    'XAU/USD': 'XAU_USD', 'XAU=F': 'XAU_USD', 'XAUUSD': 'XAU_USD', 'GOLD': 'XAU_USD', 'GC=F': 'XAU_USD',
    'XAG/USD': 'XAG_USD', 'XAG=F': 'XAG_USD', 'XAGUSD': 'XAG_USD', 'SILVER': 'XAG_USD', 'SI=F': 'XAG_USD',
    'BTC/USD': 'BTC_USD', 'BTC-USD': 'BTC_USD', 'BTCUSD': 'BTC_USD',
    'ETH/USD': 'ETH_USD', 'ETH-USD': 'ETH_USD', 'ETHUSD': 'ETH_USD',
    'EUR/USD': 'EUR_USD', 'EURUSD=X': 'EUR_USD', 'EURUSD': 'EUR_USD',
    'GBP/USD': 'GBP_USD', 'GBPUSD=X': 'GBP_USD', 'GBPUSD': 'GBP_USD',
    'AUD/USD': 'AUD_USD', 'AUDUSD=X': 'AUD_USD', 'AUDUSD': 'AUD_USD',
    'USD/JPY': 'USD_JPY', 'JPY=X': 'USD_JPY', 'USDJPY': 'USD_JPY',
}

YF_ALIASES = {
    'XAU_USD': 'GC=F', 'XAU/USD': 'GC=F', 'XAUUSD': 'GC=F', 'GOLD': 'GC=F',
    'XAG_USD': 'SI=F', 'XAG/USD': 'SI=F', 'XAGUSD': 'SI=F', 'SILVER': 'SI=F',
    'BTC_USD': 'BTC-USD', 'BTC/USD': 'BTC-USD', 'BTCUSD': 'BTC-USD',
    'ETH_USD': 'ETH-USD', 'ETH/USD': 'ETH-USD', 'ETHUSD': 'ETH-USD',
    'EUR_USD': 'EURUSD=X', 'EUR/USD': 'EURUSD=X', 'EURUSD': 'EURUSD=X',
    'GBP_USD': 'GBPUSD=X', 'GBP/USD': 'GBPUSD=X', 'GBPUSD': 'GBPUSD=X',
    'AUD_USD': 'AUDUSD=X', 'AUD/USD': 'AUDUSD=X', 'AUDUSD': 'AUDUSD=X',
    'USD_JPY': 'JPY=X', 'USD/JPY': 'JPY=X', 'USDJPY': 'JPY=X',
}


def symbol_to_oanda(symbol: str) -> str:
    """Convert user symbol to OANDA instrument format (e.g. XAU/USD -> XAU_USD)"""
    sym_upper = symbol.upper()
    if sym_upper in OANDA_ALIASES:
        return OANDA_ALIASES[sym_upper]
    
    # Generic replacement if standard pair XXX/YYY or XXX-YYY
    if "/" in sym_upper:
        return sym_upper.replace("/", "_")
    if "-" in sym_upper:
        return sym_upper.replace("-", "_")
        
    return sym_upper


def symbol_to_yf(symbol: str) -> str:
    """Convert symbol to Yahoo Finance format for fallback (e.g. XAU_USD -> GC=F)"""
    sym_upper = symbol.upper()
    if sym_upper in YF_ALIASES:
        return YF_ALIASES[sym_upper]
        
    if sym_upper in OANDA_ALIASES:
        oanda_sym = OANDA_ALIASES[sym_upper]
        if oanda_sym in YF_ALIASES:
            return YF_ALIASES[oanda_sym]
            
    if "_" in sym_upper:
        return sym_upper.replace("_", "-")
    if "/" in sym_upper:
        return sym_upper.replace("/", "-")
        
    return sym_upper


def load_oanda_config() -> dict:
    """Load OANDA configuration from environment variables or .oanda_config file"""
    # 1. Check environment variables first
    account_id = os.getenv("OANDA_ACCOUNT_ID")
    api_token = os.getenv("OANDA_API_TOKEN")
    environment = os.getenv("OANDA_ENVIRONMENT", "fxpractice")
    
    if account_id and api_token:
        return {
            "account_id": account_id,
            "api_token": api_token,
            "environment": environment
        }
        
    # 2. Check local config file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                if config.get("account_id") and config.get("api_token"):
                    return config
        except Exception as e:
            print(f"[!] Gagal membaca {CONFIG_FILE}: {e}")
            
    return None


def save_oanda_config(account_id: str, api_token: str, environment: str):
    """Save OANDA credentials securely to local JSON file"""
    config = {
        "account_id": account_id,
        "api_token": api_token,
        "environment": environment,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        
    try:
        os.chmod(CONFIG_FILE, 0o600)  # Restrict permissions on Unix/Linux/Termux
    except Exception:
        pass  # Windows filesystem might ignore 0o600
        
    print(f"[✓] Kredensial berhasil disimpan secara aman di {CONFIG_FILE}")


def setup_oanda_credentials():
    """Interactive CLI setup wizard for OANDA API"""
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║                 OANDA API Configuration Setup                      ║
    ║        (Jalankan sekali ini saja, kredensial akan disimpan)        ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    Langkah mendapatkan kredensial OANDA API:
    1. Kunjungi: https://www.oanda.com (Buka akun Demo/Live jika belum punya)
    2. Login ke platform OANDA
    3. Masuk ke menu: Manage API Access (atau Account Settings -> API Access)
    4. Generate API Token baru (v20 REST API)
    5. Salin Account ID Anda (format: 101-123-456789-001)
    """)
    
    account_id = input("Masukkan OANDA Account ID: ").strip()
    api_token = input("Masukkan OANDA API Token: ").strip()
    environment = input("Pilih Environment (fxpractice=demo, fxlive=real) [fxpractice]: ").strip() or "fxpractice"
    
    if not account_id or not api_token:
        print("[!] Account ID dan API Token tidak boleh kosong!")
        return setup_oanda_credentials()
        
    save_oanda_config(account_id, api_token, environment)
    return {
        "account_id": account_id,
        "api_token": api_token,
        "environment": environment
    }
