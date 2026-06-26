# FAQ & Troubleshooting OANDA API Integration

Dokumen ini berisi solusi atas kendala umum saat menggunakan `trading_analyzer_oanda.py`.

---

### Q1: Muncul error `[!] OANDA Auth Gagal: Cek API Token di .oanda_config` (HTTP 401)
**Solusi:**
1. Pastikan API Token yang dimasukkan sudah benar dan tidak ada spasi di awal/akhir.
2. Pastikan Account ID yang dipakai sesuai dengan environment-nya (jika token dari akun Demo `fxpractice`, jangan set environment ke `fxlive`).
3. Hapus file `.oanda_config` lalu jalankan ulang script untuk memasukkan kredensial baru:
   ```bash
   rm .oanda_config
   python trading_analyzer_oanda.py XAU/USD 1h
   ```

---

### Q2: Muncul peringatan `[!] Instrumen tidak didukung OANDA` (HTTP 404)
**Solusi:**
OANDA menggunakan format simbol `BASE_QUOTE` (contoh: `XAU_USD`, `EUR_USD`, `BTC_USD`). Modul `oanda_config.py` secara otomatis mengonversi input seperti `XAU/USD` atau `GOLD` menjadi `XAU_USD`.
Jika Anda memasukkan saham atau kripto minor yang tidak ada di OANDA, script secara otomatis mengaktifkan mekanisme **Fallback ke yfinance** sehingga Anda tetap mendapatkan hasil analisis tanpa crash.

---

### Q3: Muncul pesan `[!] OANDA Rate Limit tercapai` (HTTP 429)
**Solusi:**
OANDA membatasi jumlah request per detik. Jika Anda menjalankan script berulang kali dalam loop cepat:
1. Beri jeda `sleep 2` detik antar eksekusi.
2. Tunggu 1 menit lalu jalankan kembali.

---

### Q4: Apakah script ini bisa dijalankan di HP via Termux Android?
**Bisa 100%!**
Script didesain menggunakan indikator matematis murni (pandas/numpy) tanpa ketergantungan pada `pandas-ta` yang butuh `numba`/kompiler C. Anda cukup menginstal dependensi:
```bash
pip install -r requirements.txt
python trading_analyzer_oanda.py XAU/USD 1h
```

---

### Q5: Bagaimana mengetahui apakah data yang ditampilkan berasal dari OANDA atau yfinance?
Lihat pada bagian atas output laporan teknikal:
- Jika dari OANDA: Muncul tulisan `📊 DATA SOURCE: OANDA API (Real-time, Broker-Direct)` serta badge hijau di bawah laporan.
- Jika dari fallback yfinance: Muncul tulisan `📊 DATA SOURCE: Yahoo Finance (yfinance fallback)`.
