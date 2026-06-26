document.addEventListener('DOMContentLoaded', () => {
    const analyzeForm = document.getElementById('analyzeForm');
    const symbolInput = document.getElementById('symbolInput');
    const timeframeSelect = document.getElementById('timeframeSelect');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeSpinner = document.getElementById('analyzeSpinner');
    
    const emptyState = document.getElementById('emptyState');
    const analysisContent = document.getElementById('analysisContent');
    const historyList = document.getElementById('historyList');
    const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
    
    // Display Elements
    const displaySymbol = document.getElementById('displaySymbol');
    const displayTimeframe = document.getElementById('displayTimeframe');
    const displaySource = document.getElementById('displaySource');
    const displayBrokerInfo = document.getElementById('displayBrokerInfo');
    const displayTimestamp = document.getElementById('displayTimestamp');
    
    const displaySignal = document.getElementById('displaySignal');
    const confidenceFill = document.getElementById('confidenceFill');
    const displayConfidence = document.getElementById('displayConfidence');
    
    const metricPrice = document.getElementById('metricPrice');
    const metricChange = document.getElementById('metricChange');
    const metricHigh = document.getElementById('metricHigh');
    const metricLow = document.getElementById('metricLow');
    const metricVolume = document.getElementById('metricVolume');
    const metricATR = document.getElementById('metricATR');
    
    const metricTrend = document.getElementById('metricTrend');
    const metricEMA20 = document.getElementById('metricEMA20');
    const metricEMA50 = document.getElementById('metricEMA50');
    const metricEMAPos = document.getElementById('metricEMAPos');
    
    const metricRSI = document.getElementById('metricRSI');
    const metricRSIStatus = document.getElementById('metricRSIStatus');
    const rsiThumb = document.getElementById('rsiThumb');
    
    const metricMACD = document.getElementById('metricMACD');
    const metricMACDSig = document.getElementById('metricMACDSig');
    const metricMACDHist = document.getElementById('metricMACDHist');
    const metricBBUpper = document.getElementById('metricBBUpper');
    const metricBBLower = document.getElementById('metricBBLower');
    
    const metricSpread = document.getElementById('metricSpread');
    const metricSwapLong = document.getElementById('metricSwapLong');
    const metricSwapShort = document.getElementById('metricSwapShort');
    const metricPoint = document.getElementById('metricPoint');
    const metricHTFTrend = document.getElementById('metricHTFTrend');
    const metricSupport = document.getElementById('metricSupport');
    const metricResistance = document.getElementById('metricResistance');
    const metricSession = document.getElementById('metricSession');
    const metricPatterns = document.getElementById('metricPatterns');
    const metricServerTime = document.getElementById('metricServerTime');
    const metricPP = document.getElementById('metricPP');
    const metricR1 = document.getElementById('metricR1');
    const metricR2 = document.getElementById('metricR2');
    const metricS1 = document.getElementById('metricS1');
    const metricS2 = document.getElementById('metricS2');
    
    const copyPromptBtn = document.getElementById('copyPromptBtn');
    const savedFilePath = document.getElementById('savedFilePath');
    const promptTextPreview = document.getElementById('promptTextPreview');
    const reportTextPreview = document.getElementById('reportTextPreview');
    
    const toastNotification = document.getElementById('toastNotification');
    const toastMessage = document.getElementById('toastMessage');

    let currentPromptText = "";
    let currentReportText = "";

    const symbolList = document.getElementById('symbolList');

    // Load Available Symbols for Autocomplete Search
    const loadSymbols = async () => {
        try {
            const res = await fetch('/api/symbols');
            const data = await res.json();
            if (data.symbols && data.symbols.length > 0) {
                symbolList.innerHTML = data.symbols.map(s => `<option value="${s}">`).join('');
            }
        } catch (err) {
            console.error("Gagal memuat simbol:", err);
        }
    };

    // Quick Tags Click
    document.querySelectorAll('.tag-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            symbolInput.value = btn.getAttribute('data-sym');
        });
    });

    // Load History
    const loadHistory = async () => {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.files && data.files.length > 0) {
                historyList.innerHTML = data.files.map(f => {
                    const dateStr = new Date(f.mtime * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    const cleanName = f.filename.replace('analysis_', '').replace('.txt', '');
                    return `
                        <div class="history-item" data-file="${f.filename}">
                            <span class="history-name" title="${f.filename}">${cleanName}</span>
                            <span class="history-time">${dateStr}</span>
                        </div>
                    `;
                }).join('');

                document.querySelectorAll('.history-item').forEach(item => {
                    item.addEventListener('click', () => loadReportFile(item.getAttribute('data-file')));
                });
            } else {
                historyList.innerHTML = `<div style="font-size:0.8rem;color:var(--muted);text-align:center;padding:1rem;">No reports saved yet.</div>`;
            }
        } catch (err) {
            historyList.innerHTML = `<div style="font-size:0.8rem;color:var(--error);text-align:center;padding:1rem;">Failed to load history.</div>`;
        }
    };

    const loadReportFile = async (filename) => {
        try {
            showToast(`Loading ${filename}...`);
            const res = await fetch(`/api/report?file=${encodeURIComponent(filename)}`);
            const data = await res.json();
            if (data.content) {
                reportTextPreview.value = data.content;
                
                const parts = data.content.split("AI PROMPT:");
                if (parts.length > 1) {
                    currentPromptText = parts[1].replace(/={10,}/g, '').trim();
                    promptTextPreview.value = currentPromptText;
                }
                
                emptyState.classList.add('hidden');
                analysisContent.classList.remove('hidden');
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        } catch (err) {
            showToast("Failed to read report file.");
        }
    };

    const showToast = (msg) => {
        toastMessage.textContent = msg;
        toastNotification.classList.add('show');
        setTimeout(() => {
            toastNotification.classList.remove('show');
        }, 2500);
    };

    const fmtUSD = (val) => {
        if (isNaN(val) || val === undefined || val === null) return "$0.00";
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
    };

    const fmtNum = (val, dec = 2) => {
        if (isNaN(val) || val === undefined || val === null) return "-";
        return Number(val).toFixed(dec);
    };

    // Analyze Submit
    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const symbol = symbolInput.value.trim();
        const timeframe = timeframeSelect.value;
        if (!symbol) return;

        analyzeBtn.disabled = true;
        analyzeSpinner.style.display = 'block';

        try {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, timeframe })
            });
            const data = await res.json();

            if (data.error) {
                alert(`Error MT5: ${data.error}`);
                return;
            }

            if (data.success) {
                renderAnalysis(data);
                loadHistory();
                showToast("Analysis completed!");
            }
        } catch (err) {
            alert("Connection error. Ensure server.py is running.");
        } finally {
            analyzeBtn.disabled = false;
            analyzeSpinner.style.display = 'none';
        }
    });

    // Render Analysis Data
    const renderAnalysis = (data) => {
        emptyState.classList.add('hidden');
        analysisContent.classList.remove('hidden');

        displaySymbol.textContent = data.symbol || symbolInput.value;
        displayTimeframe.textContent = data.timeframe || "1h";
        displaySource.textContent = data.source || 'MT5';
        displayBrokerInfo.textContent = data.broker_info || "Broker Sync";
        displayTimestamp.textContent = `Update: ${data.timestamp || new Date().toLocaleTimeString()}`;

        // Signal Badge
        const sig = data.signal || "NEUTRAL";
        displaySignal.textContent = sig;
        displaySignal.className = `display-mega ${sig}`;

        const conf = data.confidence || 50;
        confidenceFill.style.width = `${conf}%`;
        displayConfidence.textContent = `${Math.round(conf)}%`;

        // Price & Tick Stats
        metricPrice.textContent = fmtUSD(data.current_price);
        const chg = data.price_change_pct || 0;
        metricChange.textContent = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
        metricChange.className = `chg-tag font-mono ${chg >= 0 ? 'up' : 'down'}`;

        metricHigh.textContent = fmtUSD(data.high);
        metricLow.textContent = fmtUSD(data.low);
        metricVolume.textContent = data.volume ? Number(data.volume).toLocaleString() : "-";
        metricATR.textContent = fmtNum(data.atr, 2);

        // Trend
        metricTrend.textContent = data.trend || "UPTREND";
        metricEMA20.textContent = fmtNum(data.ema20, 2);
        metricEMA50.textContent = fmtNum(data.ema50, 2);
        
        if (data.current_price > data.ema20) {
            metricEMAPos.textContent = "Above EMA20 (Bullish)";
            metricEMAPos.style.color = "var(--success)";
        } else {
            metricEMAPos.textContent = "Below EMA20 (Bearish)";
            metricEMAPos.style.color = "var(--error)";
        }

        // RSI
        const rsiVal = data.rsi || 50;
        metricRSI.textContent = rsiVal.toFixed(1);
        rsiThumb.style.left = `${Math.min(100, Math.max(0, rsiVal))}%`;

        if (rsiVal < 30) {
            metricRSIStatus.textContent = "Oversold";
            metricRSIStatus.style.color = "var(--success)";
        } else if (rsiVal > 70) {
            metricRSIStatus.textContent = "Overbought";
            metricRSIStatus.style.color = "var(--error)";
        } else {
            metricRSIStatus.textContent = "Neutral";
            metricRSIStatus.style.color = "var(--ink)";
        }

        // MACD & BB
        metricMACD.textContent = fmtNum(data.macd, 2);
        metricMACDSig.textContent = fmtNum(data.macd_signal, 2);
        metricMACDHist.textContent = `${data.macd_hist >= 0 ? '+' : ''}${fmtNum(data.macd_hist, 2)}`;
        metricMACDHist.style.color = data.macd_hist >= 0 ? "var(--success)" : "var(--error)";

        metricBBUpper.textContent = fmtUSD(data.bb_upper);
        metricBBLower.textContent = fmtUSD(data.bb_lower);

        if (metricSpread) metricSpread.textContent = `${data.broker_spread || 0} pts`;
        if (metricSwapLong) metricSwapLong.textContent = data.broker_swap_long || "0.0";
        if (metricSwapShort) metricSwapShort.textContent = data.broker_swap_short || "0.0";
        if (metricPoint) metricPoint.textContent = data.broker_point || "0.01";
        if (metricHTFTrend) metricHTFTrend.textContent = data.htf_trend || "-";
        if (metricSupport) metricSupport.textContent = fmtUSD(data.key_support);
        if (metricResistance) metricResistance.textContent = fmtUSD(data.key_resistance);

        if (metricSession && data.market_environment) metricSession.textContent = data.market_environment.trading_session || "-";
        if (metricServerTime && data.market_environment) {
            const timeParts = (data.market_environment.server_time_utc || "").split(' ');
            metricServerTime.textContent = timeParts.length > 1 ? timeParts[1] : (data.market_environment.server_time_utc || "-");
        }
        if (metricPatterns && data.candlestick_patterns) metricPatterns.textContent = data.candlestick_patterns.summary_status || "Normal";
        
        if (data.structural_levels && data.structural_levels.daily_pivots) {
            const piv = data.structural_levels.daily_pivots;
            if (metricPP) metricPP.textContent = fmtUSD(piv.PP);
            if (metricR1) metricR1.textContent = fmtNum(piv.R1, 2);
            if (metricR2) metricR2.textContent = fmtNum(piv.R2, 2);
            if (metricS1) metricS1.textContent = fmtNum(piv.S1, 2);
            if (metricS2) metricS2.textContent = fmtNum(piv.S2, 2);
        }

        // Files & Prompts
        savedFilePath.textContent = `reports/${data.saved_file || 'analysis.txt'}`;
        currentPromptText = data.prompt || "";
        currentReportText = data.report || "";

        promptTextPreview.value = currentPromptText;
        reportTextPreview.value = currentReportText;
    };

    copyPromptBtn.addEventListener('click', async () => {
        if (!currentPromptText) return;
        try {
            await navigator.clipboard.writeText(currentPromptText);
            showToast("Complete MD Dossier copied to clipboard");
        } catch (err) {
            promptTextPreview.select();
            document.execCommand("Copy");
            showToast("Complete MD Dossier copied to clipboard");
        }
    });

    refreshHistoryBtn.addEventListener('click', loadHistory);

    loadSymbols();
    loadHistory();
});
