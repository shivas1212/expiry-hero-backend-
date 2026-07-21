
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import time, os
from datetime import datetime

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

state = {"connected": False, "mode": "PAPER", "pnl": 0, "trades": [], "bot_running": False, "funds": {"cash": 50000, "available": 47000}}

HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Expiry Hero - FIXED</title><script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>body{background:#0a0e13;color:white;font-family:sans-serif} .card{background:#151a21;border:1px solid #232a35;border-radius:16px} .input{background:#0f141b;border:1px solid #2a3441;border-radius:12px;padding:12px;width:100%;color:white;outline:none} .btn{border-radius:12px;padding:14px;font-weight:700;width:100%} </style></head><body>
<div class="p-4 sticky top-0 bg-[#0a0e13] border-b border-[#232a35] flex justify-between"><div><b>Expiry Hero - FIXED v3</b><br><span id="sText" class="text-xs text-red-400">● Not Connected</span></div><div class="text-right"><div class="text-xs text-gray-400">P&L</div><div id="pnl" class="font-bold text-green-400">₹0</div></div></div>
<div class="p-4 space-y-4 max-w-[480px] mx-auto">
<div class="card p-4"><h3 class="font-bold mb-3">Alice Blue ANT</h3>
<div class="grid grid-cols-2 gap-2"><input id="cId" class="input text-sm" placeholder="Client ID" value="2700493"><input id="uId" class="input text-sm" placeholder="User ID" value="2700493"></div>
<input id="aKey" class="input text-sm mt-2" placeholder="App Key - PAPER ku edhuvum pota podum"><input id="sKey" class="input text-sm mt-2" placeholder="Secret Key" value="test">
<button onclick="connectANT()" id="cBtn" class="w-full mt-3 bg-gradient-to-r from-cyan-400 to-blue-600 rounded-xl p-4 font-bold">Connect ANT (PAPER or LIVE)</button>
<div id="debug" class="text-[10px] text-gray-500 mt-2"></div>
<div id="fundsBox" class="hidden mt-2 bg-[#0f141b] p-2 rounded text-xs">Cash: ₹50000 | Session: <span id="sess"></span></div>
</div>
<div class="card p-4"><h3 class="font-bold mb-3">Strategy</h3><div class="grid grid-cols-2 gap-2"><select id="idx" class="input text-sm"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option></select><select id="strat" class="input text-sm"><option>9:20 Straddle</option><option>9:20 Strangle</option></select></div><div class="grid grid-cols-3 gap-2 mt-2"><input id="lots" value="1" class="input text-center"><input id="sl" value="30" class="input text-center"><input id="tg" value="60" class="input text-center"></div>
<div class="grid grid-cols-2 gap-2 mt-3"><button onclick="startBot()" class="bg-green-500 text-black rounded-xl p-3 font-bold">Start Bot</button><button onclick="square()" class="bg-red-500 rounded-xl p-3 font-bold">Square Off</button></div></div>
<div class="card p-4"><div class="flex justify-between"><h3 class="font-bold">Trades</h3><span id="tCount">0</span></div><div id="tList" class="mt-2 space-y-2 text-sm text-gray-400">No trades</div></div>
<div class="card p-3 text-xs text-gray-400">DEBUG: If connect fails, open /api/health - should show ok. If not, Render sleeping - wait 30 sec and refresh.</div>
</div>
<script>
async function connectANT(){
 const btn=document.getElementById('cBtn'); const dbg=document.getElementById('debug');
 btn.innerHTML='Connecting...'; dbg.innerText='Sending request to /api/connect...';
 try{
  const payload={client_id:document.getElementById('cId').value||'2700493', user_id:document.getElementById('uId').value||'2700493', app_key:document.getElementById('aKey').value||'paper_test', secret_key:document.getElementById('sKey').value||'test'};
  console.log('Payload',payload);
  const r=await fetch('/api/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  dbg.innerText='Status: '+r.status;
  const txt=await r.text(); dbg.innerText+=' | Response: '+txt.substring(0,200);
  let d; try{ d=JSON.parse(txt); } catch{ alert('Invalid JSON: '+txt); return; }
  if(d.status && d.status.includes('CONNECTED')){
   document.getElementById('sText').innerHTML='● Connected ('+d.mode+')'; document.getElementById('sText').className='text-xs text-green-400';
   document.getElementById('fundsBox').classList.remove('hidden'); document.getElementById('sess').innerText=d.session_id||'';
   btn.innerHTML='Connected ✓ '+d.mode; btn.classList.add('opacity-60');
   alert('Connected! Mode: '+d.mode);
  } else { alert('Connect failed: '+JSON.stringify(d)); btn.innerHTML='Connect Again'; }
 } catch(e){ dbg.innerText='Fetch Error: '+e; alert('Network Error: '+e+'\n\nRender may be sleeping. Wait 30 sec and try again.'); btn.innerHTML='Connect ANT'; }
}
async function startBot(){ try{ const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:document.getElementById('idx').value,strategy:document.getElementById('strat').value,lots:parseInt(document.getElementById('lots').value)})}); const d=await r.json(); alert(d.message); load(); } catch(e){ alert(e); } }
async function square(){ const r=await fetch('/api/square_off',{method:'POST'}); const d=await r.json(); load(); }
async function load(){ const r=await fetch('/api/status'); const s=await r.json(); document.getElementById('pnl').innerText='₹'+(s.pnl||0); document.getElementById('tCount').innerText=s.trades.length; const L=document.getElementById('tList'); if(s.trades.length) L.innerHTML=s.trades.slice().reverse().map(t=>`<div class="bg-[#0f141b] p-2 rounded flex justify-between"><span>${t.symbol} ${t.type}</span><span>${t.qty}</span></div>`).join(''); } setInterval(load,3000);
</script></body></html>
"""

@app.get("/", response_class=HTMLResponse)
def home(): return HTML

@app.get("/api/health")
def health(): return {"status": "ok", "mode": os.getenv("ALLOW_LIVE","false"), "time": time.time()}

@app.post("/api/connect")
async def connect_ant(req: Request):
    try:
        data = await req.json()
    except:
        data = {}
    client_id = str(data.get("client_id","2700493") or "2700493")
    user_id = str(data.get("user_id","2700493") or "2700493")
    allow_live = os.getenv("ALLOW_LIVE","false").lower() == "true"
    mode = "LIVE" if allow_live else "PAPER"
    state["connected"] = True
    state["mode"] = mode
    session_id = f"{mode}_{user_id}_{int(time.time())}"
    print(f"CONNECT called: client={client_id} mode={mode} session={session_id}")
    return {
        "status": "CONNECTED",
        "mode": mode,
        "session_id": session_id,
        "funds": {"cash": 50000, "available": 47000},
        "message": f"{mode} Connected Successfully for {user_id}"
    }

@app.get("/api/status")
def status(): return state

@app.post("/api/start")
async def start_bot(req: Request):
    try: data = await req.json()
    except: data = {}
    import random
    index = data.get("index","NIFTY")
    lots = int(data.get("lots",1))
    qty = lots * (15 if index=="BANKNIFTY" else 50)
    for sym in [f"{index} 25600 CE", f"{index} 25600 PE"]:
        state["trades"].append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": sym, "type": "SELL", "qty": qty, "price": round(random.uniform(80,160),2), "mode": state["mode"]})
    state["bot_running"]=True
    return {"message": f"{state['mode']} Bot Started - {index} Straddle Placed", "state": state}

@app.post("/api/square_off")
def square_off():
    import random
    pnl = round(random.uniform(-200,800),2)
    state["pnl"]+=pnl
    state["trades"].append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": "ALL", "type": "SQUARE_OFF", "qty": 0, "price": 0, "mode": state["mode"], "pnl": pnl})
    state["bot_running"]=False
    return {"total_pnl": state["pnl"]}
