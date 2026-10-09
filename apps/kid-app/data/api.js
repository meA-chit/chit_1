/* ============================================================
   DATA LAYER: the only file that knows the hub's endpoints and where the phone keeps its data.
   Everything else (app.js) renders and decides; it calls call(), sendOp() and store only.
   A native app replaces this file (and demo.js) and keeps the contract below.

   Base: /api/kids/phone/device  (phone gateway, device bearer token)
   GET    /view                         everything this child may see (a section not shared is absent)
   POST   /pair {secret|link, code, label}  -> {token}      POST /exchange {handoff} -> {token}      POST /handoff      POST /unpair
   POST   /chores/{id}/done {done}
   POST   /homework {kind,subject,title,due_on}   POST /homework/{id}/done {done}   POST /homework/{id}/dismiss {dismissed}   DELETE /homework/{id}
   POST   /reminders/{id}/state {state,date}
   POST   /bag/tick {date,key,done}   POST /bag/items {subject,label}   DELETE /bag/items/{id}
   PUT    /privacy {section,private}
   ============================================================ */
const API = '/api/kids/phone/device';

/* ---------- storage (every access guarded: private windows can throw) ---------- */
const store = {
  get(k,d){ try{ const v=localStorage.getItem('chitkids.'+k); return v?JSON.parse(v):d; }catch{ return d; } },
  set(k,v){ try{ localStorage.setItem('chitkids.'+k,JSON.stringify(v)); }catch{} },
  del(k){ try{ localStorage.removeItem('chitkids.'+k); }catch{} },
  wipe(){ ['token','snapshot','queue'].forEach(k=>this.del(k)); },
};


class Unpaired extends Error {}
async function call(method, path, body, token){
  const t = token ?? store.get('token');
  const res = await fetch(API+path, {method, headers:{Accept:'application/json', ...(body?{'Content-Type':'application/json'}:{}), ...(t?{Authorization:'Bearer '+t}:{})}, body: body?JSON.stringify(body):undefined, cache:'no-store'});
  const data = await res.json().catch(()=>({}));
  if(res.status===401 && t) throw new Unpaired();
  if(!res.ok){ const e=new Error(data.error||'Something went wrong'); e.status=res.status; throw e; }
  return data;
}

async function sendOp(op){
  if(op.type==='chore') return call('POST',`/chores/${encodeURIComponent(op.cid)}/done`,{done:op.done});
  if(op.type==='hwtick') return call('POST',`/homework/${encodeURIComponent(op.tid)}/done`,{done:op.done});
  if(op.type==='hwadd'){ const r=await call('POST','/homework',op.body); if(op.done) await call('POST',`/homework/${encodeURIComponent(r.id)}/done`,{done:true}); return r; }
  if(op.type==='hwdel') return call('DELETE',`/homework/${encodeURIComponent(op.tid)}`);
  if(op.type==='hwdismiss') return call('POST',`/homework/${encodeURIComponent(op.tid)}/dismiss`,{dismissed:op.dismissed});
  if(op.type==='remstate') return call('POST',`/reminders/${encodeURIComponent(op.rid)}/state`,{state:op.state,date:op.date});
  if(op.type==='bagtick') return call('POST','/bag/tick',{date:op.date,key:op.key,done:op.done});
  if(op.type==='bagadd') return call('POST','/bag/items',{subject:op.subject,label:op.label});
  if(op.type==='bagdel') return call('DELETE',`/bag/items/${encodeURIComponent(op.iid)}`);
}
