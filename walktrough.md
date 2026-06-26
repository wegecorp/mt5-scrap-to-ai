# 📈 Trading Analyzer — Panduan Penggunaan

Tool CLI untuk analisis teknikal aset trading (Gold, Crypto, Forex) langsung dari terminal.  
Output: laporan indikator + prompt siap paste ke Claude / Gemini / ChatGPT.

---

## Daftar Isi

1. [Persyaratan](#persyaratan)
2. [Instalasi](#instalasi)
3. [Cara Pakai](#cara-pakai)
4. [Simbol yang Didukung](#simbol-yang-didukung)
5. [Contoh Output](#contoh-output)
6. [Cara Pakai di HP — Termux Android](#cara-pakai-di-hp--termux-android)
7. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Persyaratan

- **Python 3.9 atau lebih baru**
- Koneksi internet (untuk fetch data Yahoo Finance)
- Terminal: PowerShell (Windows) atau Termux (Android)

Cek versi Python kamu:
```bash
python --version
```

---

## Instalasi

### Windows (PowerShell)

```powershell
# 1. Masuk ke folder project
cd D:\Project\ANALISISTRADING-V1

# 2. Install semua library yang dibutuhkan
pip install -r requirements.txt
```

### Android (Termux)

```bash
# 1. Install Python
pkg update && pkg upgrade
pkg install python

# 2. Masuk ke folder project
cd ~/ANALISISTRADING-V1

# 3. Install dependencies
pip install -r requirements.txt
```

Proses install hanya perlu dilakukan **satu kali**.

---

## Cara Pakai

Format perintah:
```
python trading_analyzer.py <SIMBOL> [TIMEFRAME]
```

- `SIMBOL` — aset yang ingin dianalisis (wajib diisi)
- `TIMEFRAME` — opsional, default `1h` jika tidak diisi

### Contoh perintah

```bash
# Gold 1 jam
python trading_analyzer.py XAU/USD 1h

# Gold 15 menit
python trading_analyzer.py XAU/USD 15m

# Gold 4 jam (nama bebas)
python trading_analyzer.py GOLD 4h

# Bitcoin harian
python trading_analyzer.py BTC/USD 1d

# Euro/Dollar 1 jam
python trading_analyzer.py EUR/USD 1h
```

### Timeframe yang tersedia

| Kode  | Keterangan |
|-------|------------|
| `5m`  | 5 menit    |
| `15m` | 15 menit   |
| `30m` | 30 menit   |
| `1h`  | 1 jam *(default)* |
| `4h`  | 4 jam      |
| `1d`  | Harian     |

---

## Simbol yang Didukung

Ketik dengan format yang familiar — script otomatis konversi ke format Yahoo Finance.

### 🥇 Komoditas

| Ketik ini        | Aset   |
|-----------------|--------|
| `XAU/USD` atau `GOLD`   | Emas   |
| `XAG/USD` atau `SILVER` | Perak  |

### ₿ Kripto

| Ketik ini           | Aset      |
|--------------------|-----------|
| `BTC/USD` atau `BTCUSD` | Bitcoin   |
| `ETH/USD` atau `ETHUSD` | Ethereum  |

### 💱 Forex

| Ketik ini  | Aset           |
|-----------|----------------|
| `EUR/USD` | Euro / Dollar  |
| `GBP/USD` | Pound / Dollar |
| `USD/JPY` | Dollar / Yen   |
| `AUD/USD` | Aussie / Dollar|

> Untuk aset lain, gunakan kode Yahoo Finance langsung.  
> Contoh: `AAPL` (Apple), `^GSPC` (S&P500)

---

## Contoh Output

Script menghasilkan **dua bagian** output:

### Bagian 1 — Laporan Teknikal

```
======================================================================
TECHNICAL ANALYSIS REPORT: GC=F (1h)
======================================================================

[PRICE ACTION]
Current Price:    $4060.00
Previous Close:   $4046.10
Daily High:       $4062.70
Daily Low:        $4044.60

[KEY INDICATORS]
EMA 20:    $4035.33   │  EMA 50:  $4047.56
Trend:     Downtrend

RSI (14):  59.81   → Neutral
MACD:      3.83    → Bullish crossover

Bollinger Bands:
  Upper: $4064.93 │ Middle: $4037.37 │ Lower: $4009.80

ATR (14): $20.40  → Volatilitas Normal

[CONFLUENCE]
- EMA trend:      ✗ Bearish
- RSI momentum:   ✗ Bearish
- MACD direction: ✓ Bullish
- Price position: ✗ Bearish

[SIGNAL]
Signal:     NEUTRAL
Confidence: 50%

[TRADE SETUP]
Entry:       $4060.00
Stop Loss:   $4029.40  ← 1.5× ATR di bawah entry
Take Profit: $4110.99  ← 2.5× ATR di atas entry
Risk/Reward: 2.5 : 1.5
======================================================================
```

### Bagian 2 — Prompt untuk AI

Setelah laporan, script menampilkan **prompt siap copy-paste** ke Claude / Gemini / ChatGPT:

```
[COPY THIS PROMPT BELOW TO PASTE IN CLAUDE/GEMINI]

Analyze this XAU/USD technical setup (1h timeframe):

CURRENT PRICE: $4060.00
...
[lengkap dengan semua data indikator + pertanyaan]
```

Tinggal **copy → paste ke AI** → dapat analisis mendalam.

### File tersimpan otomatis

Setiap run, hasil analisis disimpan ke file `.txt` di folder yang sama:
```
analysis_GC=F_20260626_162939.txt
```

---

## Cara Pakai di HP — Termux Android

### Langkah-langkah

**1. Install Termux**  
Download dari [F-Droid](https://f-droid.org/packages/com.termux/) — **jangan dari Play Store** (versi Play Store sudah tidak diupdate).

**2. Install Python di Termux**
```bash
pkg update && pkg upgrade
pkg install python
```

**3. Transfer file project ke HP**  
Pilih salah satu cara:
- Hubungkan USB → copy folder ke storage HP
- Gunakan `git clone` jika sudah ada di GitHub
- Upload ke Google Drive → download di HP

**4. Masuk ke folder project**
```bash
# Jika copy ke storage utama
cd /sdcard/ANALISISTRADING-V1

# Atau jika di home Termux
cd ~/ANALISISTRADING-V1
```

**5. Install & jalankan**
```bash
pip install -r requirements.txt
python trading_analyzer.py XAU/USD 1h
```

> ✅ Script yang sama, hasil yang sama — tidak ada perbedaan antara Windows dan Android.

---

## FAQ & Troubleshooting

### ❓ "No data found for XAU/USD"
Yahoo Finance sesekali down. Tunggu 1-2 menit lalu coba lagi.  
Atau coba alternatif: `python trading_analyzer.py GOLD 1h`

### ❓ Script lambat saat pertama jalan
Normal — script mengunduh data 60 hari terakhir untuk perhitungan indikator yang akurat. Setelah itu biasanya 3-5 detik.

### ❓ Error saat `pip install`
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
Jika masih error, pastikan Python versi 3.9+:
```bash
python --version
```

### ❓ RSI / MACD muncul `NaN`
Data historis tidak cukup. Biasanya terjadi di aset yang baru listing.  
Coba timeframe lebih besar: `1h` atau `1d`.

### ❓ File analisis tidak tersimpan
Pastikan kamu menjalankan script dari folder yang bisa ditulis.  
Di Termux: jalankan dari folder home `~/`.

---

## Indikator yang Digunakan

| Indikator | Parameter | Fungsi |
|-----------|-----------|--------|
| **EMA** | 20 & 50 periode | Deteksi arah trend |
| **RSI** | 14 periode | Momentum & kondisi overbought/oversold |
| **MACD** | 12 / 26 / 9 | Konfirmasi arah & kekuatan trend |
| **Bollinger Bands** | 20 periode, 2σ | Volatilitas & posisi harga |
| **ATR** | 14 periode | Dasar kalkulasi Stop Loss & Take Profit |

Semua indikator dihitung dari data **OHLCV real-time** yang diambil langsung dari Yahoo Finance.

---

*Tool ini untuk keperluan edukasi dan analisis pribadi.*  
*Bukan merupakan saran investasi atau finansial.*
