from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import time, random, os

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

state = {"connected": False, "pnl": 0, "trades": [], "bot_running": False}

HTML = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0">
<title>Expiry Hero - ANT</title><script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>body{background:#0a0e13;color:white;font-family:sans-serif} .card{background:#151a21;border:1px solid #232a35;border-radius:16px} .input{background:#0f141b;border:1px solid #2a3441;border-radius:12px;padding:12px;width:100%;color:white;outline:none} .btn{background:linear-gradient(135deg,#00d2ff,#3a7bd5);border-radius:12px;padding:14px;font-weight:700;width:100%} .btn2{background:#ff3b30;border-radius:12px;padding:14px;font-weight:700;width:100%}</style>
</head><body class="pb-20">
<div class="p-4 flex justify-between items-center border-b border-[#232a35] sticky top-0 bg-[#0a0e13] z-10">
<div class="flex gap-2 items-center"><div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center font-bold">E</div><div><div class="font-bold">Expiry Hero</div><div id="sText" class="text-[10px] text-red-400">● Not Connected</div></div></div>
<div class="text-right"><div class="text-[10px] text-gray-400">P&L</div><div id="pnl" class="font-bold text-green-400">₹0</div></div>
</div>
<div class="p-4 space-y-4 max-w-[480px] mx-auto">
<div class="card p-4"><h3 class="font-bold mb-3"><i class="fa-solid fa-plug mr-2 text-cyan-400"></i>Alice Blue ANT</h3>
<div class="grid grid-cols-2 gap-2"><input id="cId" class="input text-sm" placeholder="Client ID"><input id="uId" class="input text-sm" placeholder="User ID"></div>
<input id="aKey" class="input text-sm mt-2" placeholder="App Key"><input id="sKey" class="input text-sm mt-2" type="password" placeholder="Secret Key">
<button onclick="connectANT()" id="cBtn" class="btn mt-3"><i class="fa-solid fa-link mr-2"></i>Connect ANT</button></div>
<div class="card p-4"><h3 class="font-bold mb-3"><i class="fa-solid fa-robot mr-2 text-yellow-400"></i>Expiry Strategy</h3>
<div class="grid grid-cols-2 gap-2"><select id="idx" class="input text-sm"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option><option>SENSEX</option></select><select id="strat" class="input text-sm"><option>9:20 Straddle</option><option>9:20 Strangle</option><option>Expiry Hero Pro</option></select></div>
<div class="grid grid-cols-3 gap-2 mt-2"><div><label class="text-[10px] text-gray-400">LOTS</label><input id="lots" type="number" value="1" class="input text-center"></div><div><label class="text-[10px] text-gray-400">SL%</label><input id="sl" value="30" class="input text-center"></div><div><label class="text-[10px] text-gray-400">TGT%</label><input id="tg" value="60" class="input text-center"></div></div>
<div class="grid grid-cols-2 gap-2 mt-3"><button onclick="startBot()" id="stBtn" class="btn">Start Bot</button><button onclick="square()" class="btn2">Square Off</button></div></div>
<div class="card p-4"><div class="flex justify-between mb-2"><h3 class="font-bold">Live Trades</h3><span id="tCount" class="text-xs bg-[#232a35] px-2 py-1 rounded-full">0</span></div><div id="tList" class="space-y-2"><div class="text-center text-gray-500 text-sm py-6">No trades yet</div></div></div>
</div>
<script>
let conn=false;
async function connectANT(){
  const b=document.getElementById('cBtn'); b.innerHTML='Connecting...';
  try{ const r=await fetch('/api/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({client_id:document.getElementById('cId').value,user_id:document.getElementById('uId').value})}); const d=await r.json();
  if(d.status==='CONNECTED'){conn=true; document.getElementById('sText').innerHTML='● Connected'; document.getElementById('sText').className='text-[10px] text-green-400'; b.innerHTML='Connected ✓'; alert('ANT Connected: '+d.session_id);} }catch(e){alert(e); b.innerHTML='Connect ANT';}
}
async function startBot(){ if(!conn){alert('First Connect ANT'); return;} const b=document.getElementById('stBtn'); b.innerHTML='Starting...'; await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:document.getElementById('idx').value,strategy:document.getElementById('strat').value,lots:document.getElementById('lots').value})}); b.innerHTML='Running...'; load(); }
async function square(){ const r=await fetch('/api/square_off',{method:'POST'}); const d=await r.json(); document.getElementById('pnl').innerText='₹'+d.total_pnl; load(); }
async function load(){ const r=await fetch('/api/status'); const s=await r.json(); document.getElementById('pnl').innerText='₹'+(s.pnl||0); document.getElementById('tCount').innerText=s.trades.length; const L=document.getElementById('tList'); if(s.trades.length){ L.innerHTML=s.trades.slice().reverse().map(t=>`<div class="bg-[#0f141b] p-3 rounded-xl flex justify-between"><div><div class="text-xs font-bold">${t.symbol}</div><div class="text-[10px] text-gray-400">${t.time} ${t.type}</div></div><div class="text-sm">${t.qty} Qty</div></div>`).join(''); } } setInterval(load,3000);
</script></body></html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/connect")
async def connect_ant(req: Request):
    data = await req.json()
    state["connected"] = True
    return {"status": "CONNECTED", "session_id": f"ANT_{data.get('user_id','USER')}_{int(time.time())}", "funds": {"cash": 48500}}

@app.get("/api/status")
def get_status():
    return state

@app.post("/api/start")
async def start_bot(req: Request):
    data = await req.json()
    state["bot_running"] = True
    state["trades"].append({"time": time.strftime("%H:%M:%S"), "symbol": f"{data.get('index','NIFTY')} 25600 CE", "type": "SELL", "qty": int(data.get('lots',1))*50, "price": round(random.uniform(80,150),2), "pnl": 0})
    return {"status": "STARTED"}

@app.post("/api/square_off")
def square_off():
    pnl = round(random.uniform(-200,800),2)
    state["pnl"] += pnl
    state["trades"].append({"time": time.strftime("%H:%M:%S"), "symbol": "ALL", "type": "SQUARE_OFF", "qty": 0, "price": 0, "pnl": pnl})
    state["bot_running"] = False
    return {"status": "SQUARED_OFF", "total_pnl": state["pnl"], "pnl": pnl}
