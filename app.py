from flask import Flask, request, jsonify, render_template_string
import requests
import os
import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NILESH AI FOREX PRO</title>
<style>
body{background:#080d19;color:white;font-family:Arial;margin:0;padding:15px}
.box{background:#111b2d;padding:18px;border-radius:14px;margin-bottom:15px}
h1{color:#27aaff;text-align:center}
input,select,button{width:100%;padding:13px;margin:7px 0;
border-radius:8px;border:0;box-sizing:border-box}
button{background:#1689ee;color:white;font-weight:bold}
#answer{white-space:pre-wrap;line-height:1.6}
.green{color:#00e68a}.red{color:#ff5252}
</style>
</head>
<body>
<h1>⚡ NILESH AI</h1>
<p style="text-align:center">FOREX TRADING PRO ULTRA</p>

<div class="box">
<h3>📊 Market Analysis</h3>
<select id="symbol">
<option value="GC=F">Gold XAUUSD (Futures)</option>
<option value="EURUSD=X">EURUSD</option>
<option value="GBPUSD=X">GBPUSD</option>
<option value="USDJPY=X">USDJPY</option>
<option value="BTC-USD">BTCUSD</option>
</select>
<select id="tf">
<option value="5m">5 Minutes</option>
<option value="15m">15 Minutes</option>
<option value="1h">1 Hour</option>
</select>
<button onclick="analyse()">ANALYZE MARKET</button>
<div id="analysis">Waiting for analysis...</div>
</div>

<div class="box">
<h3>🤖 AI Forex Assistant</h3>
<div id="answer">Namaste! Ask me your Forex trading question.</div>
<input id="question" placeholder="Ask your trading question...">
<button onclick="ask()">SEND MESSAGE</button>
</div>

<script>
async function analyse(){
 document.getElementById("analysis").innerText="Analyzing market...";
 let s=document.getElementById("symbol").value;
 let t=document.getElementById("tf").value;
 try{
  let r=await fetch("/analyze?symbol="+s+"&tf="+t);
  let d=await r.json();
  document.getElementById("analysis").innerText=d.result || d.error;
 }catch(e){
  document.getElementById("analysis").innerText="Connection error. Try again.";
 }
}
async function ask(){
 let q=document.getElementById("question").value;
 if(!q)return;
 document.getElementById("answer").innerText="Thinking...";
 let r=await fetch("/chat",{method:"POST",
 headers:{"Content-Type":"application/json"},
 body:JSON.stringify({question:q})});
 let d=await r.json();
 document.getElementById("answer").innerText=d.answer;
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")

    api_key = os.environ.get("GROQ_API_KEY")

    if api_key:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": "Bearer " + api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are NILESH AI, a Forex trading teacher. Explain Forex, SMC, ICT, liquidity, order blocks, FVG and risk management in simple Hindi, Marathi or English. Never guarantee profit. Do not invent live prices or claim unverified signals."
                        },
                        {"role": "user", "content": question}
                    ],
                    "temperature": 0.5
                },
                timeout=30
            )
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            return jsonify({"answer": answer})
        except Exception:
            pass

    return jsonify({
        "answer": "AI API connect nahi hai. फिलहाल Forex basics ke liye sawal pooch sakte hain. Full AI chat ke liye baad mein API key connect karenge."
    })

@app.route("/analyze")
def analyze():
    symbol = request.args.get("symbol", "XAUUSD=X")
    tf = request.args.get("tf", "15m")

    intervals = {"5m": "5m", "15m": "15m", "1h": "1h"}
    interval = intervals.get(tf, "15m")

    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"range": "5d", "interval": interval}
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )
        data = response.json()
        result = data["chart"]["result"][0]
        prices = result["indicators"]["quote"][0]["close"]
        prices = [p for p in prices if p is not None]

        if len(prices) < 50:
            return jsonify({"error": "Not enough market data. Try again later."})

        def ema(values, period):
            k = 2 / (period + 1)
            value = values[0]
            for price in values[1:]:
                value = price * k + value * (1-k)
            return value

        e20 = ema(prices[-100:], 20)
        e50 = ema(prices[-150:], 50)
        price = prices[-1]

        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(x, 0) for x in changes[-14:]]
        losses = [abs(min(x, 0)) for x in changes[-14:]]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14

        if avg_loss == 0:
            rsi = 100
        else:
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))

        if e20 > e50 and price > e20 and rsi > 50:
            signal = "BULLISH BIAS"
        elif e20 < e50 and price < e20 and rsi < 50:
            signal = "BEARISH BIAS"
        else:
            signal = "WAIT / NO TRADE"

        text = (
            f"Symbol: {symbol}\\n"
            f"Timeframe: {tf}\\n"
            f"Latest available price: {price}\\n"
            f"EMA 20: {e20:.5f}\\n"
            f"EMA 50: {e50:.5f}\\n"
            f"RSI 14: {rsi:.2f}\\n\\n"
            f"Market bias: {signal}\\n\\n"
            "Note: This is a basic EMA/RSI analysis, not a confirmed SMC/ICT trade setup. "
            "No automatic BUY/SELL order is placed. Verify prices and confirmations with your broker."
        )

        return jsonify({"result": text})

    except Exception as e:
        return jsonify({"error": "Market data unavailable: " + str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
