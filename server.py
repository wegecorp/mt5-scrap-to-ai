#!/usr/bin/env python3
"""
Lightweight Local API Server for MT5 Trading Dashboard
Zero extra pip dependencies (uses Python built-in http.server)
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys

# Add current directory to path so we can import trading_analyzer_mt5
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trading_analyzer_mt5 as ta_mt5

PORT = 5000
DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

os.makedirs(DASHBOARD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


class DashboardAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/analyze':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                body = json.loads(post_data.decode('utf-8'))
                symbol = body.get('symbol', 'XAUUSDm')
                timeframe = body.get('timeframe', '1h')
                
                print(f"[*] Menjalankan analisa MT5 untuk {symbol} ({timeframe})...")
                result = ta_mt5.analyze_symbol(symbol, timeframe)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                err_res = {"error": str(e)}
                self.wfile.write(json.dumps(err_res).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/history':
            try:
                files = []
                if os.path.exists(REPORTS_DIR):
                    for fname in os.listdir(REPORTS_DIR):
                        if fname.endswith('.txt') or fname.endswith('.md'):
                            fpath = os.path.join(REPORTS_DIR, fname)
                            mtime = os.path.getmtime(fpath)
                            size = os.path.getsize(fpath)
                            files.append({
                                "filename": fname,
                                "mtime": mtime,
                                "size": size
                            })
                files.sort(key=lambda x: x['mtime'], reverse=True)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"files": files[:30]}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
        elif parsed.path == '/api/symbols':
            try:
                symbols = ta_mt5.get_all_symbols()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"symbols": symbols}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
        elif parsed.path == '/api/report':
            query = urllib.parse.parse_qs(parsed.query)
            fname = query.get('file', [''])[0]
            target_path = os.path.join(REPORTS_DIR, os.path.basename(fname))
            if os.path.exists(target_path) and (fname.endswith('.txt') or fname.endswith('.md')):
                with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"filename": fname, "content": content}).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        else:
            # Fall back to serving static dashboard files
            super().do_GET()


def run():
    print("======================================================================")
    print("🚀 MENJALANKAN SERVER MT5 DASHBOARD...")
    print("======================================================================")
    
    # Initialize MT5 to wake up terminal application
    try:
        import MetaTrader5 as mt5
        mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
        init_ok = mt5.initialize(path=mt5_path) if os.path.exists(mt5_path) else mt5.initialize()
        if init_ok:
            print("[✓] Terhubung ke MetaTrader 5 Terminal")
        else:
            print("[!] Peringatan: MT5 Terminal belum aktif. Mode fallback siap.")
    except Exception as e:
        print(f"[!] Info MT5: {e}")

    def auto_open_browser():
        import time
        import webbrowser
        time.sleep(1.2)
        webbrowser.open(f"http://localhost:{PORT}")

    import threading
    threading.Thread(target=auto_open_browser, daemon=True).start()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardAPIHandler) as httpd:
        print(f"\n🌐 Dashboard siap diakses pada: http://localhost:{PORT}")
        print("💡 Tekan Ctrl+C di jendela ini jika ingin mematikan server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nMematikan server...")


if __name__ == "__main__":
    run()
