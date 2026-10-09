/* ============================================================
   Chit Kids: the child's own phone view (ADR-0012).
   Talks only to /api/kids/phone/device/* on the phone gateway with a device
   token from pairing. The server decides what the phone may see; a section
   a parent did not share is simply not in the response.
   Demo mode (?demo=1) uses built-in sample data and says so on screen.
   ============================================================ */
const Q = new URLSearchParams(location.search);
const DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const SHORT = ['Su','Mo','Tu','We','Th','Fr','Sa'];
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const mins = t => { const [h,m]=t.split(':').map(Number); return h*60+m; };
const hhmm = m => String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const nowD = () => Q.get('now') ? new Date(Q.get('now')) : new Date();
const wd = d => (d.getDay()+6)%7;                       // server weekdays: Monday = 0


/* ---------- appearance: the same choices as the web app, remembered on this phone ---------- */
const look = Object.assign({mode:'dark',palette:'classic'}, (()=>{ try{ return JSON.parse(localStorage.getItem('chitkids.appearance')||'null')||{}; }catch{ return {}; } })());
if (!['dark','light','auto'].includes(look.mode)) look.mode='dark';
if (!['classic','spectrum'].includes(look.palette)) look.palette='classic';
function applyLook(){
  const mode=Q.get('theme')||look.mode, pal=Q.get('palette')||look.palette;
  const t=mode==='auto'?(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'):mode;
  document.documentElement.dataset.theme=t; document.documentElement.dataset.palette=pal;
  document.querySelector('meta[name=theme-color]').setAttribute('content',t==='dark'?'#05070d':'#eef2fb');
}
function setLook(patch){ Object.assign(look,patch); try{ localStorage.setItem('chitkids.appearance',JSON.stringify(look)); }catch{} applyLook(); }
matchMedia('(prefers-color-scheme:dark)').addEventListener?.('change',()=>{ if(look.mode==='auto') applyLook(); });
applyLook();

/* ---------- state ---------- */
const state = { layout:store.get('layout','list'), tab:'today', seg:'today', view:null, server:null, queue:store.get('queue',[]), mode:'boot', error:'', note:'', offline:false, savedAt:null, busy:false };
const SUBJ_COLORS = { maths:'#1e88e5', mathe:'#1e88e5', german:'#e53935', deutsch:'#e53935', english:'#fb8c00', englisch:'#fb8c00', biology:'#8d6e63', biologie:'#8d6e63',
  geography:'#7cb342', geografie:'#7cb342', erdkunde:'#7cb342', sport:'#43a047', music:'#d81b60', musik:'#d81b60', art:'#f9a825', kunst:'#f9a825',
  french:'#8e24aa', 'französisch':'#8e24aa', history:'#a1887f', geschichte:'#a1887f', ethics:'#3949ab', ethik:'#3949ab', physics:'#00acc1', physik:'#00acc1', chemistry:'#5e35b1', chemie:'#5e35b1' };
const PALETTE = ['#1e88e5','#e53935','#fb8c00','#7cb342','#43a047','#d81b60','#f9a825','#8e24aa','#00acc1','#6d4c41','#3949ab','#f4511e'];
const accent = s => { const k=String(s).toLowerCase().trim(); if (SUBJ_COLORS[k]) return SUBJ_COLORS[k]; let h=0; for (const c of k) h=(h*31+c.charCodeAt(0))>>>0; return PALETTE[h%PALETTE.length]; };
const KIND_LETTER = {core:'c',minor:'m',elective:'e'};
const KIND_NAME = {core:'Core',minor:'Minor',elective:'Elective'};
/* A subject has a name (lists, sheets) and a short code (tight places like the week plan) with its type as a superscript: M<sup>c</sup>. */
const codeMark = (code,kind) => `${esc(code)}${kind&&KIND_LETTER[kind]?`<sup class="ty" title="${KIND_NAME[kind]}">${KIND_LETTER[kind]}</sup>`:''}`;
const subjectOf = name => (state.view&&state.view.subjects||[]).find(s=>s.name.toLowerCase()===String(name).toLowerCase());
const abbr = s => { s=String(s); return s.length>7 ? s.slice(0,4)+'.' : s; };

/* ---------- icons ---------- */
const P = {
  sun:'<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.3 5.3l1.7 1.7M17 17l1.7 1.7M5.3 18.7 7 17M17 7l1.7-1.7"/>',
  grid:'<rect x="3.5" y="3.5" width="7" height="7" rx="1.6"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.6"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.6"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.6"/>',
  star:'<path d="M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.2l-5.6 3 1.1-6.3L2.9 9.5l6.3-.9z"/>',
  chart:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  pill:'<rect x="2.8" y="8.2" width="18.4" height="7.6" rx="3.8" transform="rotate(-40 12 12)"/><path d="M9.2 7.7l7.1 7.1"/>',
  check:'<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  lock:'<rect x="5" y="10.5" width="14" height="10" rx="2.6"/><path d="M8 10.5V8a4 4 0 018 0v2.5"/>',
  bag:'<rect x="4.5" y="8" width="15" height="12.5" rx="3"/><path d="M9 8V6.5A3 3 0 0112 3.5a3 3 0 013 3V8M4.5 13h15"/>',
  music:'<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
  doc:'<path d="M7 3.5h7l4 4V20a1.5 1.5 0 01-1.5 1.5h-9.5A1.5 1.5 0 015.5 20V5A1.5 1.5 0 017 3.5z"/><path d="M14 3.5V8h4M9 13h6M9 16.5h6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/>',
  cap:'<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11.5V16c3.5 2.6 8.5 2.6 12 0v-4.5"/>',
  share:'<path d="M12 15V3.5M7.5 8L12 3.5 16.5 8"/><path d="M6 11.5H5.2A1.7 1.7 0 003.5 13.2v6.1a1.7 1.7 0 001.7 1.7h13.6a1.7 1.7 0 001.7-1.7v-6.1a1.7 1.7 0 00-1.7-1.7H18"/>',
  food:'<path d="M7 3v7a2.5 2.5 0 005 0V3M9.5 3v18M17 21V3c-2.2 1.2-3 4-3 7s1 4 3 4"/>',
  qr:'<rect x="3.5" y="3.5" width="6.5" height="6.5" rx="1.2"/><rect x="14" y="3.5" width="6.5" height="6.5" rx="1.2"/><rect x="3.5" y="14" width="6.5" height="6.5" rx="1.2"/><path d="M14 14h3v3h-3zM19 14v1M14 19h1M17.5 19h3v1.5"/>',
  book:'<path d="M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 004 20.5zM4 20.5A2.5 2.5 0 006.5 18H20v3H6.5A2.5 2.5 0 014 20.5z"/><path d="M8.5 7.5H15"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  x:'<path d="M6 6l12 12M18 6L6 18"/>',
  list:'<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
  cards:'<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/>',
  undo:'<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 010 12h-3"/>',
  wifi:'<path d="M2.5 9a15 15 0 0119 0M5.5 12.5a10.5 10.5 0 0113 0M8.8 16a5.5 5.5 0 016.4 0"/><circle cx="12" cy="19.2" r="1" fill="currentColor"/>',
};
const ic = (n,extra='') => `<svg class="i ${extra}" viewBox="0 0 24 24" aria-hidden="true">${P[n]}</svg>`;
const star = (cls='') => `<svg class="i f ${cls}" viewBox="0 0 24 24" aria-hidden="true">${P.star}</svg>`;
// The Chit mark: five stars traced into a lowercase c, the newest one lit.
const mark = () => `<svg class="m" viewBox="0 0 100 100" aria-hidden="true"><polyline points="70.6,25.5 34,22.3 18,50 34,77.7 70.6,74.5" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/><g fill="currentColor"><circle cx="34" cy="22.3" r="6"/><circle cx="18" cy="50" r="6"/><circle cx="34" cy="77.7" r="6"/><circle cx="70.6" cy="74.5" r="6"/></g><circle cx="70.6" cy="25.5" r="17" fill="none" stroke="#ffd34d" stroke-width="3" opacity=".55"/><circle cx="70.6" cy="25.5" r="10" fill="#ffd34d"/></svg>`;
const emojiOr = (icon,fallback) => icon ? `<span class="em" aria-hidden="true">${esc(icon)}</span>` : ic(fallback);
const reminderIcon = t => /bag|pack|pe |sport|gym/i.test(t)?'bag':/music|recorder|instrument/i.test(t)?'music':'doc';

/* ---------- derived data ---------- */
const slotsOf = (v) => (v.school?.slots||[]);
const roomOf = n => String(n||'').replace(/,?\s*period\s*\d+/i,'').trim();          // "Room A204, period 1" -> "Room A204"
const roomShort = n => roomOf(n).replace(/^Room\s+/i,'');
function lessonsFor(v, date){
  const w = wd(date); if (w>4 && !slotsOf(v).some(s=>s.weekday===w)) return null;
  const items = slotsOf(v).filter(s=>s.weekday===w).map(s=>({kind:s.kind,start:mins(s.start),end:mins(s.end),title:s.title,room:roomOf(s.note)}));
  return items.length ? items.sort((a,b)=>a.start-b.start) : null;
}
const isLesson = x => x.kind==='lesson';
const MODE_WORD = {walk:'walk',cycle:'cycle',car:'drive'};
const PART_TIME = {morning:450,day:900,evening:1080};            // a chore has a part of the day, not a clock time
const BAG_TIME = '19:30';                                         // default; the child will be able to change it (K6)
const leaveText = a => a.escort==='parent'&&a.escort_name ? `${a.escort_name} takes you${a.leave_by?' · leaves '+a.leave_by:''}` : a.leave_by ? `Leave by ${a.leave_by} · ${MODE_WORD[a.mode]||'travel'} ${a.travel_minutes} min` : '';
/* Everything on one day, by time: lessons, breaks, the child's activities and calendar events. */
function dayItems(v,date){
  const w=wd(date), iso=isoDay(date), out=[];
  slotsOf(v).filter(s=>s.weekday===w).forEach(s=>out.push({t:s.kind==='lesson'?'lesson':s.kind==='care'?'care':'break',start:mins(s.start),end:mins(s.end),title:s.title,room:roomOf(s.note)}));
  (v.activities?.weekly||[]).filter(a=>a.weekdays.includes(w)).forEach(a=>out.push({t:'activity',start:mins(a.start),end:a.end?mins(a.end):mins(a.start)+60,title:a.name,room:a.place||'',icon:a.icon||'',a}));
  (v.activities?.events||[]).filter(e=>e.date===iso).forEach(e=>out.push({t:'event',start:e.start?mins(e.start):-1,end:e.end?mins(e.end):1440,title:e.title,room:'',allDay:e.all_day,icon:e.icon||'',e}));
  return out.sort((a,b)=>a.start-b.start||a.end-b.end);
}
/* What leads the Today screen (kid-experience.md, 3.2): bag and first lesson in the morning, homework and the activity after school, the bag again in the evening. */
function dayMode(v,n){
  const nm=n.getHours()*60+n.getMinutes(), lessons=v.share.timetable?lessonsFor(v,day0()):null, bag=mins(BAG_TIME);
  if(v.share.timetable&&!lessons) return 'weekend';
  if(!lessons) return nm<mins('12:00')?'morning':nm<bag?'after':'evening';
  if(nm<lessons[0].start) return 'morning';
  if(nm<lessons[lessons.length-1].end) return 'school';
  return nm<bag?'after':'evening';
}
const addDays = (d,n)=>{ const x=new Date(d); x.setDate(x.getDate()+n); return x; };
const day0 = () => { const d=nowD(); return new Date(d.getFullYear(),d.getMonth(),d.getDate()); };
const nextSchoolDay = (v,d) => { let x=addDays(d,1); for(let i=0;i<7;i++){ if(lessonsFor(v,x)) return x; x=addDays(x,1);} return null; };
const fmtDate = d => `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
const gradeColor = g => g<=1.5?'#2e9b4a':g<=2.5?'#1f9d8f':g<=3.5?'#2f80d6':g<=4.5?'#d98a00':'#cf5a45';
const gradeWord = g => g<=1.5?'Excellent':g<=2.5?'Good':g<=3.5?'Solid':g<=4.5?'Room to grow':'Needs a plan';
const PARTS = {morning:'Morning',day:'Day',evening:'Evening'};

/* ---------- views ---------- */
function heroGradient(h){
  if(h<5||h>=21) return ['linear-gradient(160deg,#1a237e,#4527a0)','#3a2b8a'];
  if(h<12)       return ['linear-gradient(160deg,#e08a00,#a65a00)','#a65a00'];
  if(h<17)       return ['linear-gradient(160deg,#00897b,#00574b)','#00695c'];
  return               ['linear-gradient(160deg,#6a4fd0,#3a2b8a)','#3a2b8a'];
}
const greet = h => h<5?'Still up?':h<12?'Good morning':h<17?'Good afternoon':h<21?'Good evening':'Good night';
const avatarBtn = () => `<button class="avatar" data-act="me" aria-label="About this app">${esc((state.view.child.name||'?')[0])}</button>`;
const banner = () => { const n=state.queue.length;
  if(state.view.demo) return `<div class="ribbon demo">${ic('lock')} Demo data. Nothing here is real.</div>`;
  if(state.offline) return `<div class="ribbon" role="status">${ic('wifi')} Offline. Showing what was saved${state.savedAt?' at '+esc(state.savedAt):''}.${n?` ${n} change${n===1?'':'s'} will be saved when you are back online.`:''}</div>`;
  return n ? `<div class="ribbon" role="status">${ic('wifi')} Saving ${n} change${n===1?'':'s'}…</div>` : ''; };

/* ---------- Today: what leads depends on the time of day ---------- */
const inText = m => `${m>=60?Math.floor(m/60)+' h ':''}${m%60} min`;
function nextUpCard(v,date,isToday,nm,items){
  const live=items.filter(x=>x.t!=='break'||false);
  if(isToday){
    const cur=items.find(x=>x.start>=0&&nm>=x.start&&nm<x.end&&!(x.t==='event'&&x.allDay));
    if(cur){
      const pct=Math.round((nm-cur.start)/Math.max(1,cur.end-cur.start)*100), after=items.find(x=>x.start>=cur.end&&x.t!=='break'&&x.start>=0);
      return `<div class="card now"><div class="ic ${cur.icon?'emoji':''}">${cur.icon?emojiOr(cur.icon):ic(cur.t==='lesson'?'cap':cur.t==='break'?'food':'star')}</div><div style="flex:1">
        <b>${cur.t==='lesson'?'Now: ':''}${esc(cur.title)}</b>
        <span>${cur.room?esc(cur.room)+' · ':''}until ${hhmm(cur.end)}${after?` · next ${esc(after.title)} at ${hhmm(after.start)}`:''}</span>
        <div class="bar"><i style="width:${pct}%"></i></div></div></div>`;
    }
    const nxt=items.find(x=>x.start>nm&&x.t!=='break');
    if(nxt){
      const first=items.find(x=>x.t==='lesson'), d=nxt.start-nm;
      const lab = nxt===first ? `School starts in ${inText(d)}` : `Next up · in ${inText(d)}`;
      const leave = nxt.t==='activity'&&leaveText(nxt.a) ? `<p class="leave">${ic('clock')} ${esc(leaveText(nxt.a))}</p>` : '';
      return `<div class="card next"><div class="lab">${lab}</div><h3>${nxt.icon?`<span class="em" aria-hidden="true">${esc(nxt.icon)}</span> `:''}${esc(nxt.title)}${nxt===first?' first':''}</h3><p>${hhmm(nxt.start)}${nxt.room?' · '+esc(nxt.room):''}</p>${leave}</div>`;
    }
    const nx=nextSchoolDay(v,date), li=nx&&v.share.timetable?lessonsFor(v,nx)[0]:null;
    return `<div class="card now"><div class="ic">${ic('check')}</div><div><b>${items.some(x=>x.t==='lesson')?'School is done for today':'Nothing more planned'}</b><span>${li?`${isoDay(nx)===isoDay(addDays(date,1))?'Tomorrow':DAYS[nx.getDay()]} starts with ${esc(li.title)} at ${hhmm(li.start)}`:'Enjoy the evening.'}</span></div></div>`;
  }
  const first=items.find(x=>x.t!=='break'&&x.start>=0);
  if(!first) return `<div class="card now"><div class="ic">${ic('sun')}</div><div><b>Nothing planned tomorrow</b><span>${(()=>{const nx=nextSchoolDay(v,date);return nx?'Next school day: '+DAYS[nx.getDay()]:'Enjoy the break';})()}</span></div></div>`;
  return `<div class="card next"><div class="lab">Tomorrow starts with</div><h3>${esc(first.title)}</h3><p>${hhmm(first.start)}${first.room?' · '+esc(first.room):''}</p></div>`;
}

function bagCard(v,mode,isToday){
  const b=v.bag; if(!b) return '';
  const todayIso=isoDay(day0());
  if(!b.available) return b.reason==='timetable_not_shared' && (mode==='morning'||mode==='evening') ? `<div class="sec"><div class="card note">${ic('bag')}<span>The bag list needs your timetable, which your parents have not shared.</span></div></div>` : '';
  const want = isToday && mode==='morning' ? b.days.find(d=>d.date===todayIso) : (!isToday||mode==='evening'||mode==='weekend') ? b.days.find(d=>d.date>todayIso) : null;
  if(!want) return '';
  const rel=daysFromToday(want.date), when=rel===0?'':rel===1?'tomorrow':DAYS[new Date(want.date+'T00:00:00').getDay()];
  const shown=want.items.filter(e=>!e.na&&!(isCards()&&e.source==='reminder'));
  const done=shown.filter(e=>e.ticked).length;
  const rows=shown.map(e=>{
    const why = e.source==='reminder'?'reminder':e.source==='homework'?'homework':e.for.length?'for '+e.for.join(', '):'';
    return `<div class="row hw ${e.ticked?'done':''}"><button class="chkb" data-act="bagtick" data-date="${esc(want.date)}" data-key="${esc(e.key)}" aria-pressed="${e.ticked}" aria-label="${esc(e.label)}${why?', '+esc(why):''}"><span class="chk ${e.ticked?'done':''}">${ic('check')}</span></button>
      <div class="body" style="cursor:default"><span class="g"><div class="t">${esc(e.label)}</div>${why?`<div class="s">${esc(why)}</div>`:''}</span></div></div>`;
  }).join('');
  return `<div class="sec"><h2>${rel===0?'Before you go':'Pack for '+when} <span>${shown.length?(shown.every(e=>e.ticked)?'bag ready':`${done} of ${shown.length}`):''}</span></h2>
    ${shown.length?`<div class="list">${rows}</div>`:`<div class="card note">${ic('bag')}<span>Nothing to pack yet. Add what you take for each subject.</span></div>`}
    ${shown.length&&shown.every(e=>e.ticked)?`<div class="ready">${ic('check')} Bag ready. Nice.</div>`:''}
    <button class="link" data-act="bagedit">${ic('plus')} Edit my bag lists</button></div>`;
}

function laterList(v,items,isToday,nm,showChores){
  const rows=[];
  items.filter(x=>x.t!=='break'&&(!isToday||x.end>nm||x.start<0)).forEach(x=>{
    if(x.t==='lesson'||x.t==='care') rows.push({k:x.start,html:`<div class="row"><span class="time">${hhmm(x.start)}</span>${x.t==='lesson'?`<span class="tag" style="--ac:${accent(x.title)}">${esc(x.title)}</span>`:`<span class="t">${esc(x.title)}</span>`}<span class="g"><div class="s" style="margin:0;text-align:right">${esc(x.room)}</div></span></div>`});
    else if(x.t==='activity') rows.push({k:x.start,html:`<div class="row act"><span class="time">${hhmm(x.start)}</span><div class="bk ${x.icon?'emoji':''}">${emojiOr(x.icon,'star')}</div><span class="g"><div class="t">${esc(x.title)}</div><div class="s">${esc([x.room,leaveText(x.a)].filter(Boolean).join(' · '))}</div></span></div>`});
    else rows.push({k:x.start,html:`<div class="row act"><span class="time">${x.allDay?'All day':hhmm(x.start)}</span><div class="bk ${x.icon?'emoji':''}">${emojiOr(x.icon,'clock')}</div><span class="g"><div class="t">${esc(x.title)}</div><div class="s">${esc(x.e.source||'Calendar')}</div></span></div>`});
  });
  if(showChores&&v.stars) v.stars.chores.forEach(c=>rows.push({k:PART_TIME[c.day_part]??1000,html:choreRow(c,true)}));
  rows.sort((a,b)=>a.k-b.k);
  return rows.length?`<div class="sec"><h2>${isToday?'Later today':'Tomorrow'} <span>${rows.length} thing${rows.length===1?'':'s'}</span></h2><div class="list">${rows.map(r=>r.html).join('')}</div></div>`:'';
}

function viewToday(){
  const v=state.view, n=nowD(), h=n.getHours(), nm=h*60+n.getMinutes();
  const isToday = state.seg==='today';
  const showDate = isToday ? day0() : addDays(day0(),1);
  const items = dayItems(v, showDate);
  const mode = dayMode(v,n);
  const [grad,heroTxt] = heroGradient(h);
  const hasPlan = v.share.timetable || v.activities;
  const nowCard = hasPlan ? nextUpCard(v,showDate,isToday,nm,items) : '';

  const bagHtml = bagCard(v,mode,isToday);
  const bagShown = !!bagHtml && v.bag?.available;
  const rems = v.reminders ? (isToday?v.reminders.today:v.reminders.tomorrow) : [];
  const remHtml = remindersBlock(rems, isoDay(showDate), isToday, bagShown);
  const dueHtml = v.homework && isToday ? homeworkPeek(v.homework.tasks) : '';
  const choresAsCards = isCards() && isToday && v.stars && v.stars.chores.length;
  const laterHtml = laterList(v,items,isToday,nm,isToday&&!choresAsCards);
  const choreHtml = choresAsCards ? `<div class="sec"><h2>My chores <span>${layoutToggle()}</span></h2>${cardsGrid(v.stars.chores.map(choreCard))}</div>` : '';
  let medHtml='';
  if(v.health&&isToday){ const m=v.health.meds.filter(x=>x.due_today); if(m.length) medHtml=`<div class="sec"><h2>Medicine</h2><div class="list">${m.map(medRow).join('')}</div></div>`; }
  const goal = v.stars && v.stars.goals.filter(g=>!g.reached).sort((a,b)=>a.cost-b.cost)[0];
  const earnHtml = v.stars&&isToday&&(mode==='weekend'||mode==='after') ? `<div class="sec"><button class="card earn" data-act="tab" data-id="stars">${star()}<span><b>${v.stars.total} stars</b>${goal?`<small>${goal.cost-goal.have} to ${esc(goal.title)}</small>`:''}</span></button></div>` : '';

  const blocks = {next:`<div class="sec" style="margin-top:18px">${nowCard}</div>`, bag:bagHtml, rem:remHtml, due:dueHtml, chores:choreHtml, later:laterHtml, med:medHtml, earn:earnHtml};
  const order = !isToday ? ['next','bag','rem','later'] : {
    morning:['next','bag','rem','due','chores','later','med'], school:['next','rem','due','chores','later','med'], after:['next','due','chores','later','earn','rem','med'],
    evening:['bag','next','rem','due','chores','later','med'], weekend:['next','chores','later','due','earn','rem','med']}[mode];
  const body = order.map(k=>blocks[k]||'').join('');

  const next = v.stars && v.stars.goals.filter(g=>!g.reached).sort((a,b)=>a.cost-b.cost)[0];
  const hw = v.homework ? hwSummary(v.homework.tasks) : null;
  const chips = v.stars ? `<span class="chip">${star()} ${v.stars.total} stars</span>` + (hw&&hw.due_tomorrow?`<span class="chip">${ic('book')} ${hw.due_tomorrow} due tomorrow</span>`:next?`<span class="chip">${ic('star')} ${next.cost-next.have} to ${esc(next.title.length>18?next.title.slice(0,17)+'…':next.title)}</span>`:'') : (hw&&hw.due_tomorrow?`<span class="chip">${ic('book')} ${hw.due_tomorrow} due tomorrow</span>`:'');
  const inst = (!isStandalone() && isIOS && !store.get('hideInstall',false) && !v.demo) ? `<div class="install">${ic('share')}<span>Add me to your Home Screen</span><button data-act="install">How</button></div>`:'';

  return `<div class="screen">${banner()}
    <header class="hero" style="--hero:${grad};--herotext:${heroTxt}">
      <div class="hrow"><div><h1>${greet(h)}, <em>${esc(v.child.name)}</em></h1><p>${fmtDate(showDate)}</p></div>${avatarBtn()}</div>
      <div class="chips">${chips}</div>
      ${hasPlan?`<div class="seg" role="group" aria-label="Day"><button class="${isToday?'on':''}" aria-pressed="${isToday}" data-act="seg" data-v="today">Today</button><button class="${!isToday?'on':''}" aria-pressed="${!isToday}" data-act="seg" data-v="tomorrow">Tomorrow</button></div>`:''}
    </header>${inst}
    ${body}
    <div class="lock-note">${ic('lock')}<span>Your parents choose what shows up here.</span></div></div>`;
}

function choreRow(c,withTime){
  const s = c.outcome==='well'?'well' : c.outcome==='again'?'again' : c.done ? (c.star?'sent':'done') : 'todo';
  const lab = s==='well'?`<span class="pill">${ic('check')} Done well</span>` : s==='again'?`<span class="pill amber">Try again tomorrow</span>` : s==='sent'?`<span class="pill amber">Waiting for a parent</span>` : s==='done'?`<span class="pill gray">Done</span>` : c.star?`<span class="starb">${star()}+1</span>`:`<span class="pill gray">Tick</span>`;
  return `<button class="row" data-act="chore" data-id="${esc(c.id)}" aria-pressed="${!!c.done}" ${c.outcome?'disabled':''}>
    ${withTime?`<span class="time">${c.day_part==='morning'?'AM':c.day_part==='evening'?'PM':'Day'}</span>`:''}<span class="chk ${s}">${ic('check')}</span><span class="g"><div class="t">${esc(c.title)}</div><div class="s">${PARTS[c.day_part]||'Today'} chore${c.star?'':' · tick only, no star'}</div></span>${lab}</button>`;
}
function choreList(){ return `<div class="list">${state.view.stars.chores.map(c=>choreRow(c,false)).join('')}</div>`; }

function medRow(m){
  const n=nowD(), nm=n.getHours()*60+n.getMinutes(), t=mins(m.time);
  const st = m.status==='given'?`<span class="pill">${ic('check')} Given</span>` : (nm>=t||m.status==='missed')?`<span class="pill amber">Ask ${esc(m.reminds||'a parent')}</span>`:`<span class="pill gray">${esc(m.time)}</span>`;
  return `<div class="row"><div class="bk">${ic('pill')}</div><div class="g"><div class="t">${esc(m.name)}</div><div class="s">${esc(m.dose||'')}${m.reminds?(m.dose?' · ':'')+esc(m.reminds)+' reminds you':''}</div></div>${st}</div>`;
}

function viewPlan(){
  const v=state.view, n=nowD(), nm=n.getHours()*60+n.getMinutes(), td=wd(n);
  const monday = addDays(day0(), -td);
  let grid='', nowb='', gridHtml='';
  if(v.school){
    const lessons = slotsOf(v).filter(s=>s.kind==='lesson'&&s.weekday<=4);
    const starts = [...new Set(lessons.map(s=>s.start))].sort();
    const head = [0,1,2,3,4].map(d=>{ const x=addDays(monday,d); return `<div class="h ${d===td?'today':''}">${SHORT[x.getDay()]}<small>${x.getDate()}.${x.getMonth()+1}.</small></div>`; }).join('');
    grid=`<div></div>${head}`;
    starts.forEach((st,i)=>{
      grid+=`<div class="p">${i+1}<small>${st}</small></div>`;
      for(let d=0;d<=4;d++){
        const c=lessons.find(s=>s.weekday===d&&s.start===st);
        if(!c){ grid+=`<div class="cell empty"></div>`; continue; }
        const cur = d===td && nm>=mins(c.start) && nm<mins(c.end);
        grid+=`<button class="cell ${cur?'cur':''}" style="--ac:${accent(c.title)}" data-act="cell" data-d="${d}" data-s="${st}" aria-label="${esc(c.title)}${c.subject_kind?', '+KIND_NAME[c.subject_kind]:''}, ${esc(roomOf(c.note))}">${c.code?codeMark(c.code,c.subject_kind):esc(abbr(c.title))}<small>${esc(roomShort(c.note))}</small></button>`;
      }
    });
    gridHtml = starts.length ? `<div class="week">${grid}</div><div class="legend">Codes: <sup>c</sup> core · <sup>m</sup> minor · <sup>e</sup> elective</div>` : `<div class="card empty" style="margin:16px"><b>🗓️</b>No lessons yet. A parent adds them in Chit.</div>`;
    const items=lessonsFor(v,n);
    if(items){ const cur=items.find(x=>nm>=x.start&&nm<x.end&&isLesson(x)), nx=items.find(x=>x.start>nm&&isLesson(x));
      nowb = cur?`<div class="card now" style="margin:6px 16px 14px"><div class="ic">${ic('cap')}</div><div><b>Now: ${esc(cur.title)}${cur.room?' · '+esc(cur.room):''}</b><span>until ${hhmm(cur.end)}${nx?` · next ${esc(nx.title)} at ${hhmm(nx.start)}`:''}</span></div></div>`
        : nx?`<div class="card now" style="margin:6px 16px 14px"><div class="ic">${ic('clock')}</div><div><b>Next: ${esc(nx.title)}</b><span>${hhmm(nx.start)}${nx.room?' · '+esc(nx.room):''}</span></div></div>`:''; }
  }
  const fri=addDays(monday,4);

  // Activities: the regular week
  const act=v.activities, weekly=act?.weekly||[];
  const actHtml = act ? `<div class="sec"><h2>Activities <span>every week</span></h2>${weekly.length?`<div class="list">${weekly.map(a=>`
      <div class="row act"><span class="time" style="width:54px">${a.weekdays.map(d=>['Mo','Tu','We','Th','Fr','Sa','Su'][d]).join(' ')}</span><div class="bk ${a.icon?'emoji':''}">${emojiOr(a.icon,'star')}</div>
      <span class="g"><div class="t">${esc(a.name)}</div><div class="s">${esc([a.start+(a.end?'–'+a.end:''),a.place,leaveText(a)].filter(Boolean).join(' · '))}</div></span></div>`).join('')}</div>`
      :`<div class="card note">${ic('star')}<span>No regular activities yet. A parent adds them in the household settings.</span></div>`}</div>` : '';

  // Coming up: events from the child's own calendars
  let evHtml='';
  if(act){
    const byDay={}; (act.events||[]).forEach(e=>(byDay[e.date]=byDay[e.date]||[]).push(e));
    const notice = {unconfigured:'No calendar is linked to you yet. A parent can add the school or club calendar.', unavailable:'The calendar could not be read right now. It will try again.', stale:'Showing the last saved calendar. It could not be refreshed just now.', partial:'Some calendars could not be read, so this list may be incomplete.'}[act.events_state]||'';
    const days=Object.keys(byDay).sort();
    evHtml = `<div class="sec"><h2>Coming up <span>next 2 weeks</span></h2>${notice?`<div class="card note">${ic('wifi')}<span>${notice}</span></div>`:''}
      ${days.length?days.map(d=>{ const dt=new Date(d+'T00:00:00'), rel=daysFromToday(d); return `<div class="grp" style="margin:12px 4px 4px">${rel===0?'Today':rel===1?'Tomorrow':DAYS[dt.getDay()]+' '+dt.getDate()+' '+MONTHS[dt.getMonth()].slice(0,3)}</div><div class="list">${byDay[d].map(e=>`
        <div class="row act"><span class="time">${e.all_day?'All day':e.start}</span><div class="bk ${e.icon?'emoji':''}">${emojiOr(e.icon,'clock')}</div><span class="g"><div class="t">${esc(e.title)}</div><div class="s">${esc([e.end&&!e.all_day?'until '+e.end:'',e.source].filter(Boolean).join(' · '))}</div></span></div>`).join('')}</div>`; }).join(''):(notice?'':`<div class="card note">${ic('clock')}<span>Nothing in your calendar for the next two weeks.</span></div>`)}</div>`;
  }
  return `<div class="screen">${banner()}<div class="top"><div><h1>Plan</h1><small>${v.school?`${monday.getDate()} ${MONTHS[monday.getMonth()].slice(0,3)} – ${fri.getDate()} ${MONTHS[fri.getMonth()].slice(0,3)} · tap a lesson`:'Your week'}</small></div>${avatarBtn()}</div>${nowb}${gridHtml}${actHtml}${evHtml}</div>`;
}

/* ---------- bag lists: what I take for each subject or activity ---------- */
const BAG_IDEAS = {sport:['Sports kit','Water bottle'],pe:['Sports kit','Water bottle'],sportunterricht:['Sportzeug','Trinkflasche'],music:['Recorder'],musik:['Flöte'],art:['Apron','Paints'],kunst:['Malkasten','Kittel'],maths:['Geometry set'],mathe:['Geodreieck'],swimming:['Swim bag','Towel'],schwimmen:['Badesachen','Handtuch']};
function bagSheet(){
  const v=state.view, b=v.bag; if(!b) return;
  const lessons=[...new Set(slotsOf(v).filter(s=>s.kind==='lesson').map(s=>s.title))].sort();
  const acts=[...new Set((v.activities?.weekly||[]).map(a=>a.name))];
  const names=[...new Set([...lessons,...acts,...b.items.map(i=>i.subject)])];
  const rows=names.map(name=>{
    const own=b.items.filter(i=>i.subject.toLowerCase()===name.toLowerCase());
    const ideas=(BAG_IDEAS[name.toLowerCase()]||[]).filter(l=>!own.some(i=>i.label.toLowerCase()===l.toLowerCase()));
    return `<div class="bagrow"><span class="tag" style="--ac:${accent(name)}">${esc(name)}</span><div class="chipset">
      ${own.map(i=>`<button class="on" data-act="bagdel" data-id="${esc(i.id)}" aria-label="Remove ${esc(i.label)} from ${esc(name)}">${esc(i.label)} ✕</button>`).join('')}
      ${ideas.map(l=>`<button data-act="bagadd" data-subject="${esc(name)}" data-label="${esc(l)}" aria-label="Add ${esc(l)} to ${esc(name)}">+ ${esc(l)}</button>`).join('')}</div></div>`;
  }).join('');
  openSheet(`<h2>My bag lists</h2><p class="sub2">What you take for each subject or activity. Tap a suggestion to add it, or tap an item to remove it.</p>
    ${rows||'<p class="sub2">Your timetable is empty, so there are no subjects yet.</p>'}
    <label class="flabel" for="bagsubj">Add something else</label>
    <input class="finput" id="bagsubj" list="bagnames" maxlength="60" placeholder="Subject or activity" autocomplete="off"><datalist id="bagnames">${names.map(n=>`<option value="${esc(n)}">`).join('')}</datalist>
    <input class="finput" id="baglabel" maxlength="60" placeholder="Item, for example Recorder" autocomplete="off" style="margin-top:8px">
    <div class="err" id="bagerr" role="alert"></div>
    <button class="btn" data-act="bagnew">Add</button><button class="btn t" data-act="close">Done</button>`,'bag');
}

/* ---------- homework ---------- */
const isoDay = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const daysFromToday = iso => Math.round((new Date(iso+'T00:00:00') - day0())/86400000);
function hwSummary(tasks){                      // same rules as the hub; used for demo data and as the live fallback
  const open=tasks.filter(t=>!t.done&&!t.dismissed), monday=addDays(day0(),-wd(day0()));
  return {due_tomorrow:open.filter(t=>t.days===1).length, tests_soon:open.filter(t=>t.kind==='test'&&t.days>=0&&t.days<=14).length,
    overdue:open.filter(t=>t.days<0).length, done_this_week:tasks.filter(t=>t.done&&t.done_on>=isoDay(monday)).length,
    week:[0,1,2,3,4].map(i=>{ const day=isoDay(addDays(monday,i)); const o=open.filter(t=>t.due_on===day); return {day,open:o.length,tests:o.filter(t=>t.kind==='test').length}; })};
}
const dueText = t => t.done?'done':t.days<0?(t.days===-1?'yesterday':`${-t.days} days ago`):t.days===0?'today':t.days===1?'tomorrow':t.days<7?DAYS[new Date(t.due_on+'T00:00:00').getDay()]:`${new Date(t.due_on+'T00:00:00').getDate()} ${MONTHS[new Date(t.due_on+'T00:00:00').getMonth()].slice(0,3)}`;
function hwRow(t){
  const tag = t.subject?`<span class="tag" style="--ac:${accent(t.subject)}">${esc(t.subject)}</span>`:'';
  const test = t.kind==='test'?`<span class="pill amber">Test${!t.done&&t.days>=0?` · ${t.days===0?'today':t.days===1?'tomorrow':'in '+t.days+' days'}`:''}</span>`:'';
  return `<div class="row hw ${t.done?'done':''}"><button class="chkb" data-act="hwdone" data-id="${esc(t.id)}" aria-label="${t.done?'Mark not done':'Mark done'}: ${esc(t.title)}"><span class="chk ${t.done?'done':''}">${ic('check')}</span></button>
    <button class="body" data-act="hwopen" data-id="${esc(t.id)}"><span class="g"><div class="t">${esc(t.title)}</div><div class="s" style="${t.days<0&&!t.done?'color:var(--soft-red);font-weight:700':''}">${tag?'':''}${esc(t.subject||'')}${t.subject?' · ':''}${dueText(t)}</div></span>${test}</button></div>`;
}
/* ---------- layout: list or two-column cards with Done / Not relevant ---------- */
const isCards = () => state.layout==='cards';
const layoutToggle = () => `<button class="lay" data-act="layout" aria-label="${isCards()?'Show as a list':'Show as cards'}" title="${isCards()?'Show as a list':'Show as cards'}">${ic(isCards()?'list':'cards')}</button>`;
/* One card: icon, title, a line of detail, then the buttons. `act` holds the data attributes that say which item the buttons act on. */
function taskCard(o){
  const closed = o.state==='done'||o.state==='na';
  const buttons = o.locked ? '' : closed
    ? `<button class="tc-btn" data-act="${o.undoAct}" ${o.attrs} aria-label="Undo: ${esc(o.title)}">${ic('undo')} Undo</button>`
    : `<button class="tc-btn ok" data-act="${o.doneAct}" ${o.attrs} aria-label="Done: ${esc(o.title)}">${ic('check')} Done</button>${o.naAct?`<button class="tc-btn na" data-act="${o.naAct}" ${o.attrs} aria-label="Not relevant: ${esc(o.title)}">${ic('x')} Not relevant</button>`:''}`;
  return `<div class="tcard ${o.state||''}"><div class="tc-top"><span class="tc-ic" aria-hidden="true">${o.icon}</span>${o.pill||''}</div>
    <div class="tc-title">${esc(o.title)}</div><div class="tc-sub">${esc(o.sub||'')}</div>${o.state?`<div class="tc-state">${o.state==='done'?'Done':'Not relevant'}</div>`:''}<div class="tc-act">${buttons}</div></div>`;
}
const cardsGrid = cards => `<div class="cards">${cards.join('')}</div>`;
function hwCard(t){
  const closed = t.done?'done':t.dismissed?'na':null;
  const pill = t.kind==='test'&&!closed ? `<span class="pill amber">Test${t.days>=0?` · ${t.days===0?'today':t.days===1?'tomorrow':'in '+t.days+' d'}`:''}</span>` : '';
  return taskCard({icon:t.kind==='test'?'📝':'📘',title:t.title,sub:[t.subject,dueText(t)].filter(Boolean).join(' · '),pill,state:closed,attrs:`data-id="${esc(t.id)}"`,
    doneAct:'hwdone',naAct:'hwdismiss',undoAct:t.done?'hwdone':'hwdismiss'});
}
function remCard(r,dateIso){
  return taskCard({icon:reminderEmoji(r.title),title:r.title,sub:PARTS[r.day_part]||'Reminder',state:r.state,attrs:`data-id="${esc(r.id)}" data-date="${esc(dateIso)}"`,
    doneAct:'remdone',naAct:'remna',undoAct:'remundo'});
}
function choreCard(c){
  const s2 = c.outcome==='well'?'well':c.outcome==='again'?'again':c.done?(c.star?'sent':'done'):'todo';
  const pill = s2==='well'?`<span class="pill">${ic('check')} Done well</span>`:s2==='again'?`<span class="pill amber">Try again</span>`:s2==='sent'?`<span class="pill amber">Waiting for a parent</span>`:c.star?`<span class="starb">${star()}+1</span>`:'';
  return taskCard({icon:c.day_part==='morning'?'🌅':c.day_part==='evening'?'🌙':'🧹',title:c.title,sub:(PARTS[c.day_part]||'Today')+(c.star?'':' · tick only'),pill,
    state:c.done?'done':null,locked:!!c.outcome,attrs:`data-id="${esc(c.id)}"`,doneAct:'chore',undoAct:'chore'});    // a chore is done or not: the star stays a parent decision
}
const reminderEmoji = t => /bag|pack|pe |sport|gym/i.test(t)?'🎒':/music|recorder|instrument/i.test(t)?'🎵':/form|sign|letter|doc/i.test(t)?'📄':/swim/i.test(t)?'🏊':'🔔';
function remindersBlock(rems,dateIso,isToday,bagShown){
  const live = rems.filter(r=>r.state!=='na'), hidden = rems.filter(r=>r.state==='na');
  if(!rems.length || (!isCards()&&bagShown)) return '';           // in the list layout the bag checklist already carries today's reminders
  const head = `<h2>${isToday?'Don\'t forget':'Pack for tomorrow'} <span>${layoutToggle()}</span></h2>`;
  const body = isCards()
    ? cardsGrid(rems.map(r=>remCard(r,dateIso)))
    : `<div class="list">${rems.map(r=>`<div class="row hw ${r.state==='done'?'done':''} ${r.state==='na'?'na':''}"><button class="chkb" data-act="${r.state==='done'?'remundo':'remdone'}" data-id="${esc(r.id)}" data-date="${esc(dateIso)}" aria-pressed="${r.state==='done'}" aria-label="${r.state==='done'?'Not done':'Done'}: ${esc(r.title)}"><span class="chk ${r.state==='done'?'done':''}">${ic('check')}</span></button>
        <div class="body" style="cursor:default"><span class="g"><div class="t">${esc(r.title)}</div><div class="s">${r.state==='na'?'Not relevant':esc(PARTS[r.day_part]||'')}</div></span></div>
        ${r.state==='na'?`<button class="rowx" data-act="remundo" data-id="${esc(r.id)}" data-date="${esc(dateIso)}" aria-label="Undo: ${esc(r.title)}">${ic('undo')}</button>`:`<button class="rowx" data-act="remna" data-id="${esc(r.id)}" data-date="${esc(dateIso)}" aria-label="Not relevant: ${esc(r.title)}" title="Not relevant">${ic('x')}</button>`}</div>`).join('')}</div>`;
  return `<div class="sec">${head}${body}</div>`;
}
function homeworkPeek(tasks){
  const soon=tasks.filter(t=>!t.done&&!t.dismissed&&(t.days<=1||(t.kind==='test'&&t.days<=7))).sort((a,b)=>a.days-b.days).slice(0,3);
  if(!soon.length) return '';
  return `<div class="sec"><h2>Due soon <span><button data-act="tab" data-id="homework" style="color:var(--primary);font-weight:800;min-height:44px">See all</button> ${layoutToggle()}</span></h2>${isCards()?cardsGrid(soon.map(hwCard)):`<div class="list">${soon.map(hwRow).join('')}</div>`}</div>`;
}
function hwNaRow(t){
  return `<div class="row hw na"><div class="body" style="cursor:default"><span class="g"><div class="t">${esc(t.title)}</div><div class="s">${esc([t.subject,'not relevant'].filter(Boolean).join(' · '))}</div></span></div>
    <button class="rowx" data-act="hwdismiss" data-id="${esc(t.id)}" aria-label="Undo: ${esc(t.title)}">${ic('undo')}</button></div>`;
}
function viewHomework(){
  const h=state.view.homework, tasks=h.tasks, sum=h.summary||hwSummary(tasks), td=wd(nowD());
  const open=tasks.filter(t=>!t.done&&!t.dismissed).sort((a,b)=>a.days-b.days||a.title.localeCompare(b.title)), done=tasks.filter(t=>t.done), na=tasks.filter(t=>t.dismissed);
  const groups=[['Overdue',open.filter(t=>t.days<0),'over'],['Today',open.filter(t=>t.days===0)],['Tomorrow',open.filter(t=>t.days===1)],['This week',open.filter(t=>t.days>=2&&t.days<7)],['Later',open.filter(t=>t.days>=7)]];
  const top=Math.max(1,...sum.week.map(d=>d.open));
  const bars=sum.week.map((d,i)=>`<div class="${i===td?'today':''}"><i class="${d.tests?'test':d.open?'has':''}" style="height:${d.open?14+Math.round(d.open/top*54):8}px"></i><span>${['Mo','Tu','We','Th','Fr'][i]}</span></div>`).join('');
  const list = open.length ? groups.filter(g=>g[1].length).map(g=>`<div class="grp ${g[2]||''}">${g[0]}</div><div class="sec" style="margin-top:0">${isCards()?cardsGrid(g[1].map(hwCard)):`<div class="list">${g[1].map(hwRow).join('')}</div>`}</div>`).join('')
    : `<div class="card empty" style="margin:16px"><b>🎉</b>Nothing open. Enjoy the free time!</div>`;
  return `<div class="screen" style="padding-bottom:84px">${banner()}<div class="top"><div><h1>Homework</h1><small>${open.length} open · tap the circle when it is done</small></div>${avatarBtn()}</div>
    <div class="tiles"><div class="tile"><b>${sum.due_tomorrow}</b><span>due tomorrow</span></div><div class="tile"><b>${sum.tests_soon}</b><span>tests in 2 weeks</span></div>
      <div class="tile ${sum.overdue?'warn':''}"><b>${sum.overdue}</b><span>overdue</span></div><div class="tile good"><b>${sum.done_this_week}</b><span>done this week</span></div></div>
    <div class="wkbars" aria-label="Open homework per day this week">${bars}</div>
    <div class="lay-row">${layoutToggle()}</div>${list}
    ${done.length?`<details class="doneset" ${state.showDone?'open':''} id="doneset"><summary>Done recently (${done.length})</summary><div class="sec" style="margin-top:0"><div class="list">${done.map(hwRow).join('')}</div></div></details>`:''}
    ${na.length?`<details class="doneset" id="naset"><summary>Not relevant (${na.length})</summary><div class="sec" style="margin-top:0"><div class="list">${na.map(hwNaRow).join('')}</div></div></details>`:''}
  </div>`;
}
const nextLessonDate = (v,subject) => { for(let i=1;i<=14;i++){ const d=addDays(day0(),i); if(slotsOf(v).some(s=>s.kind==='lesson'&&s.weekday===wd(d)&&s.title===subject)) return d; } return null; };
const hwState = { kind:'homework', subject:'', due:'', touchedDue:false };
function addHwSheet(){
  const v=state.view, subs=v.homework.subjects||[];
  hwState.kind='homework'; hwState.subject=''; hwState.touchedDue=false; hwState.due=isoDay(addDays(day0(),1));
  const groups=['core','minor','elective'].map(k=>[k,subs.filter(x=>x.kind===k)]).filter(g=>g[1].length);
  const picker = groups.length ? groups.map(([k,list])=>`<div class="grp sm">${KIND_NAME[k]}</div><div class="chipset subjset">${list.map(x=>`<button class="subj" style="--ac:${accent(x.name)}" data-act="hwsubj" data-s="${esc(x.name)}" aria-pressed="false">${esc(x.name)}<sup class="ty">${KIND_LETTER[k]}</sup></button>`).join('')}</div>`).join('')
    : `<div class="card note">${ic('cap')}<span>No subjects yet. A parent adds lessons to the school day, and your subjects appear here.</span></div>`;
  openSheet(`<h2>Add to my list</h2><p class="sub2">Homework or a test. Your parents can see it too.</p>
    <div class="chipset" id="kindset"><button class="on" data-act="hwkind" data-k="homework">Homework</button><button data-act="hwkind" data-k="test">Test or exam</button></div>
    <label class="flabel">Subject <span style="font-weight:600">(optional)</span></label>${picker}
    <label class="flabel" for="hwtitle">What do you need to do?</label><input class="finput" id="hwtitle" maxlength="200" placeholder="Worksheet 4, fractions" autocomplete="off">
    <label class="flabel" for="hwdue">Due</label><input class="finput" id="hwdue" type="date" value="${hwState.due}">
    <div class="err" id="hwerr" role="alert"></div>
    <button class="btn" data-act="hwsave">Save</button><button class="btn t" data-act="close">Cancel</button>`);
}
function suggestDue(){                                      // homework is due at the next lesson of that subject; a test defaults to a week out
  if(hwState.touchedDue) return;
  const next=hwState.subject&&hwState.kind==='homework'?nextLessonDate(state.view,hwState.subject):null;
  hwState.due=isoDay(next||addDays(day0(),hwState.kind==='test'?7:1)); document.getElementById('hwdue').value=hwState.due;
}
function saveHw(){
  const subject=hwState.subject, title=document.getElementById('hwtitle').value.trim(), due=document.getElementById('hwdue').value, err=document.getElementById('hwerr');
  if(!title){ err.textContent='Write what you need to do.'; return; }
  if(!due){ err.textContent='Pick a date.'; return; }
  enqueue({type:'hwadd',tmp:'tmp-'+uid(),body:{kind:hwState.kind,subject:subject||null,title,due_on:due}});
  closeSheet();
}
function hwSheet(id){
  const t=state.view.homework.tasks.find(x=>x.id===id); if(!t) return;
  openSheet(`${t.subject?`<span class="tag" style="--ac:${accent(t.subject)};font-size:15px">${esc(t.subject)}</span>`:''}<h2 style="margin-top:12px">${esc(t.title)}</h2>
    <p class="sub2">${t.kind==='test'?'Test':'Homework'} · due ${dueText(t)} (${t.due_on}) · added by ${t.by==='child'?'you':'a parent'}</p>
    <button class="btn" data-act="hwdone" data-id="${esc(t.id)}" data-close="1">${t.done?'Not done yet':'Mark as done'}</button>
    ${t.by==='child'?`<button class="btn t" data-act="hwdel" data-id="${esc(t.id)}">Delete</button>`:'<p class="sub2" style="text-align:center;margin-top:12px">A parent added this, so only a parent can delete it.</p>'}
    <button class="btn t" data-act="close">Close</button>`);
}
function setHwDone(id,done){ enqueue({type:'hwtick',tid:id,done}); }
function delHw(id){ enqueue({type:'hwdel',tid:id}); closeSheet(); }

function makeDemoBag(v){
  const days=[], today=day0();
  const dayFor=d=>{ const titles=slotsOf(v).filter(x=>x.kind==='lesson'&&x.weekday===wd(d)).sort((a,b)=>a.start.localeCompare(b.start)).map(x=>x.title); return titles; };
  const first=dayFor(today).length?today:null, nx=nextSchoolDay(v,today);
  [first,nx].filter(Boolean).forEach(d=>{
    const titles=dayFor(d), acts=(v.activities.weekly||[]).filter(a=>a.weekdays.includes(wd(d))).map(a=>a.name), entries=[], seen={};
    const add=(label,source,why)=>{ const key=label.toLowerCase(); if(!seen[key]){ seen[key]={key,label,source,for:[],ticked:false}; entries.push(seen[key]); } if(why&&!seen[key].for.includes(why)) seen[key].for.push(why); };
    [...new Set(titles)].forEach(t=>v.bag.items.filter(i=>i.subject.toLowerCase()===t.toLowerCase()).forEach(i=>add(i.label,'subject',t)));
    (daysFromToday(isoDay(d))===0?v.reminders.today:daysFromToday(isoDay(d))===1?v.reminders.tomorrow:[]).forEach(r=>add(r.title,'reminder',null));
    v.homework.tasks.filter(t=>t.kind==='homework'&&!t.done&&!t.dismissed&&t.due_on===isoDay(d)).forEach(t=>add(t.subject?t.subject+': '+t.title:t.title,'homework',t.subject));
    acts.forEach(a=>v.bag.items.filter(i=>i.subject.toLowerCase()===a.toLowerCase()).forEach(i=>add(i.label,'activity',a)));
    days.push({date:isoDay(d),weekday:wd(d),items:entries,ready:false});
  });
  v.bag.days=days; v.bag.available=days.length>0;
}

function viewStars(){
  const s=state.view.stars, td=wd(nowD());
  const week = s.week.map((c,i)=>`<div><i class="${c?'on':''}" ${i===td&&!c?'style="outline:2px dashed #fff;outline-offset:-2px"':''}>${c?star():''}</i>${['Mo','Tu','We','Th','Fr','Sa','Su'][i]}</div>`).join('');
  const thisWeek = s.week.reduce((a,b)=>a+b,0);
  const goals = s.goals.length ? s.goals.map(g=>{
    const pct=Math.min(100,Math.round(g.have/g.cost*100));
    const tag = g.approved?`<span class="pill">${ic('check')} Approved</span>`:g.reached?`<span class="pill amber">Reached! Ask a parent</span>`:`<span class="starb">${star()} ${g.cost}</span>`;
    return `<div class="goal ${g.reached?'hit':''}"><div class="hd"><div><h3>${esc(g.title)}</h3>${g.note?`<p>${esc(g.note)}</p>`:''}</div>${tag}</div>
      <div class="pr"><i style="width:${pct}%"></i></div>
      <div class="meta"><span>${Math.min(g.have,g.cost)} / ${g.cost} stars</span><span>${g.approved?'Enjoy it!':g.reached?'A parent says yes':(g.cost-g.have)+' to go'}</span></div></div>`;
  }).join('') : `<div class="card empty"><b>🎯</b>No goals yet. Ask a parent to set one with you.</div>`;
  return `<div class="screen">${banner()}<div class="top"><div><h1>Stars</h1><small>Only grow. Nothing is ever taken away.</small></div>${avatarBtn()}</div>
    <div class="stars-hero">${star('bg')}<div class="big">${star()}${s.total}</div><p>${thisWeek?thisWeek+(thisWeek===1?' star':' stars')+' this week. Keep it going!':'A fresh week. Your first star is waiting.'}</p><div class="days">${week}</div></div>
    ${s.chores.length?`<div class="sec"><h2>Chores today <span>${s.chores.filter(c=>c.star).length} earn a star ${layoutToggle()}</span></h2>${isCards()?cardsGrid(s.chores.map(choreCard)):choreList()}</div>`:''}
    <div class="sec"><h2>My goals <span>stars count toward every goal</span></h2>${goals}</div></div>`;
}

function viewGrades(){
  const g=state.view.grades;
  const subs = g.subjects.map((s,i)=>{
    const c=gradeColor(s.average), pos=(s.average-1)/5*100;
    return `<button class="sub" style="--gc:${c}" data-act="sub" data-i="${i}">
      <div class="hd"><span class="tag" style="--ac:${accent(s.name)}">${esc(s.name)}</span><span class="g"></span><span style="text-align:right"><span class="val">${s.average.toFixed(1)}</span><div style="font-size:12px;color:var(--muted);font-weight:700">${gradeWord(s.average)}</div></span></div>
      <div class="scale"><i style="left:${pos}%"></i></div><div class="scl"><span>1 best</span><span>6</span></div></button>`;
  }).join('');
  const body = g.subjects.length ? `<div class="avg" style="--gc:${gradeColor(g.overall)}"><div class="n">${g.overall.toFixed(1)}</div><div><b>${gradeWord(g.overall)}</b><span>Overall average across ${g.subjects.length} subjects</span></div></div>
    <div class="sec"><h2>Subjects <span>tap for the details</span></h2>${subs}</div>` : `<div class="card empty" style="margin:16px"><b>📘</b>No grades yet.</div>`;
  return `<div class="screen">${banner()}<div class="top"><div><h1>Grades</h1><small>German scale: 1 is best, 6 is lowest</small></div>${avatarBtn()}</div>${body}
    <div class="lock-note">${ic('lock')}<span>Averages mix written and spoken grades, as your school does.</span></div></div>`;
}

function viewHealth(){
  const meds=state.view.health.meds, n=nowD(), nm=n.getHours()*60+n.getMinutes();
  const today=meds.filter(m=>m.due_today);
  const up=today.filter(m=>m.status!=='given'&&mins(m.time)>nm)[0];
  const days=[...Array(7)].map((_,i)=>{ const d=addDays(day0(),i-6), key=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    const due=meds.map(m=>m.week.find(w=>w.day===key)).filter(w=>w&&w.due); return {d,due,ok:due.length&&due.every(w=>w.status==='given')}; });
  const hist=days.map(x=>`<div><i style="background:${x.ok?'var(--pc)':'var(--surface2)'};color:var(--on-pc)">${x.ok?ic('check'):''}</i>${SHORT[x.d.getDay()]}</div>`).join('');
  return `<div class="screen">${banner()}<div class="top"><div><h1>Health</h1><small>Just for you and your parents</small></div>${avatarBtn()}</div>
    <div class="sec" style="margin-top:8px"><div class="card now"><div class="ic">${ic('pill')}</div><div><b>${up?`Next: ${esc(up.name)} at ${esc(up.time)}`:today.length?'All done for today':'Nothing to take today'}</b><span>${up&&up.reminds?esc(up.reminds)+' will remind you':''}</span></div></div></div>
    <div class="sec"><h2>Today</h2>${today.length?`<div class="list">${today.map(medRow).join('')}</div>`:'<div class="card empty"><b>🌿</b>Nothing to take today.</div>'}</div>
    <div class="sec"><h2>Last 7 days</h2><div class="card w"><div class="days" style="margin:0;color:var(--text)">${hist}</div></div></div>
    <div class="lock-note">${ic('lock')}<span>Medicine is private. It never shows on shared screens at home.</span></div></div>`;
}

/* ---------- screens before pairing ---------- */
function viewWelcome(){
  const app=isStandalone();
  return `<div class="screen center"><div class="logo">${mark()}</div><h1>${app?'Pair this app':'Chit Kids'}</h1>
    <p class="lead">${state.error?esc(state.error):app?'This app is on your Home Screen but not linked to your plan yet.':'Your school day, stars and reminders, on your phone.'}</p>
    ${app?`<button class="btn" data-act="manual">Type the codes from my parent's screen</button>`:''}
    <div class="card" style="text-align:left;margin:20px 0 8px"><b style="font-size:16px">${app?'Your parent can show you the codes':'Set this phone up'}</b>
      <ol class="steps"><li><span>A parent opens <b>Household settings</b>, then <b>Kids' phones</b></span></li><li><span>They turn it on for you and tap <b>Pair a phone</b></span></li>
      ${app?`<li><span>On their screen you will see a <b>link code</b> and <b>6 digits</b>. Type both here</span></li>`:`<li><span>Scan the QR code with this phone's <b>Camera</b></span></li><li><span>Type the 6 digits from their screen</span></li>`}</ol></div>
    ${app?'':`<button class="btn t" data-act="manual">I have a link code instead</button>`}
    <button class="btn t" data-act="demo">Look around with demo data</button></div>`;
}

function linkField(){
  return `<input id="link" maxlength="9" autocapitalize="characters" autocorrect="off" spellcheck="false" value="${esc(state.link||'')}" placeholder="LINK CODE" aria-label="Link code from your parent's screen">`;
}
function viewPair(){
  return `<div class="screen center"><div class="logo">${ic('lock')}</div><h1>Almost there</h1>
    <p class="lead">${state.manual?'Type the link code and the 6 digits shown on your parent\'s screen.':'Type the 6 digits shown on your parent\'s screen.'}</p>
    <form id="pairform" autocomplete="off">${state.manual?linkField():''}<input id="code" inputmode="numeric" pattern="[0-9 ]*" maxlength="7" autocomplete="one-time-code" placeholder="000 000" aria-label="6 digit code">
    <div class="err" id="pairerr" role="alert">${esc(state.error)}</div>
    <button class="btn" type="submit" ${state.busy?'disabled':''}>${state.busy?'Connecting…':'Connect'}</button></form>
    <button class="btn t" data-act="cancelpair">Not now</button></div>`;
}

/* ---------- shell ---------- */
const TABS = [
  {id:'today',label:'Today',icon:'sun',mod:'var(--cyan)',view:viewToday,need:null},
  {id:'plan',label:'Plan',icon:'grid',mod:'var(--violet)',view:viewPlan,need:['school','activities']},
  {id:'homework',label:'Homework',icon:'book',mod:'var(--lime)',view:viewHomework,need:'homework'},
  {id:'stars',label:'Stars',icon:'star',mod:'var(--amber)',view:viewStars,need:'stars'},
  {id:'grades',label:'Grades',icon:'chart',mod:'var(--magenta)',view:viewGrades,need:'grades'},
  {id:'health',label:'Health',icon:'pill',mod:'var(--red)',view:viewHealth,need:'health'},
];
const visibleTabs = () => TABS.filter(t=>!t.need||[].concat(t.need).some(k=>state.view[k]));
const isWide = () => matchMedia('(min-width:760px)').matches;      // tablet or landscape: Today stays on the left, the chosen tab on the right
function focusSelector(){
  const f=document.activeElement, d=f&&f.dataset; if(!d||!d.act) return null;
  const q=x=>String(x).replace(/["\\]/g,'\\$&');
  return `#view [data-act="${q(d.act)}"]`+(d.id?`[data-id="${q(d.id)}"]`:'')+(d.key?`[data-key="${q(d.key)}"]`:'')+(d.date?`[data-date="${q(d.date)}"]`:'');
}
function render(keepScroll){
  const v=document.getElementById('view'), nav=document.getElementById('nav');
  const ys=[...v.querySelectorAll('.pane')].map(p=>p.scrollTop), y=v.scrollTop, keep=focusSelector();
  if (state.mode==='app' && state.view){
    const wide=isWide();
    const tabs=visibleTabs().filter(t=>!(wide&&t.id==='today'&&visibleTabs().length>1));
    if(!tabs.find(t=>t.id===state.tab)) state.tab=tabs[0]?.id||'today';
    const tab=TABS.find(t=>t.id===state.tab);
    v.classList.toggle('wide',wide&&tabs.length>0&&tab.id!=='today');
    v.innerHTML = v.classList.contains('wide') ? `<div class="pane">${viewToday()}</div><div class="pane">${tab.view()}</div>` : tab.view();
    nav.hidden=false;
    const fab=document.getElementById('fab'); fab.hidden = state.tab!=='homework'; fab.innerHTML=ic('plus')+' Add homework';
    nav.innerHTML = tabs.map(t=>`<button class="${t.id===state.tab?'on':''}" style="--mod:${t.mod}" data-act="tab" data-id="${t.id}" ${t.id===state.tab?'aria-current="page"':''}><span class="pl">${t.id==='stars'&&t.id===state.tab?star():ic(t.icon)}</span>${t.label}</button>`).join('');
  } else {
    v.classList.remove('wide');
    nav.hidden=true; document.getElementById('fab').hidden=true;
    v.innerHTML = state.mode==='pair'?viewPair() : state.mode==='boot'?'<div class="screen center"><div class="logo">'+mark()+'</div></div>' : viewWelcome();
    if(state.mode==='pair'){ const f=document.getElementById('link')||document.getElementById('code'); if(f&&!(state.busy)) f.focus(); }
  }
  if(keepScroll){ v.scrollTop=y; v.querySelectorAll('.pane').forEach((p,i)=>{ p.scrollTop=ys[i]||0; }); } else v.scrollTop=0;
  if(keep){ const el=document.querySelector(keep); if(el) el.focus({preventScroll:true}); }
}
window.matchMedia('(min-width:760px)').addEventListener?.('change',()=>{ if(state.mode==='app') render(true); });

/* ---------- sheets ---------- */
let lastFocus=null, sheetKind=null;
function openSheet(html,kind){
  const s=document.getElementById('sheet'); lastFocus=document.activeElement; sheetKind=kind||null;
  s.innerHTML='<div class="grab"></div>'+html; s.scrollTop=0;
  const h=s.querySelector('h2'); if(h){ h.id='sheettitle'; s.setAttribute('aria-labelledby','sheettitle'); } else s.removeAttribute('aria-labelledby');
  s.setAttribute('role','dialog'); s.setAttribute('aria-modal','true'); s.tabIndex=-1;
  s.classList.add('on'); document.getElementById('back').classList.add('on');
  ['view','nav','fab'].forEach(id=>{ document.getElementById(id).inert=true; });
  s.focus({preventScroll:true});
}
function closeSheet(){
  const s=document.getElementById('sheet'); if(!s.classList.contains('on')) return;
  s.classList.remove('on'); document.getElementById('back').classList.remove('on'); sheetKind=null;
  ['view','nav','fab'].forEach(id=>{ document.getElementById(id).inert=false; });
  if(lastFocus&&document.contains(lastFocus)) lastFocus.focus({preventScroll:true});
}
document.getElementById('back').onclick = closeSheet;
document.addEventListener('keydown',e=>{
  const s=document.getElementById('sheet'); if(!s.classList.contains('on')) return;
  if(e.key==='Escape'){ closeSheet(); return; }
  if(e.key!=='Tab') return;
  const f=[...s.querySelectorAll('button,input,[href],select,textarea,summary,[tabindex]:not([tabindex="-1"])')].filter(x=>!x.disabled&&x.offsetParent!==null);
  if(!f.length) return; const first=f[0], last=f[f.length-1];
  if(e.shiftKey&&(document.activeElement===first||document.activeElement===s)){ e.preventDefault(); last.focus(); }
  else if(!e.shiftKey&&document.activeElement===last){ e.preventDefault(); first.focus(); }
});

function lessonSheet(day,start){
  const c=slotsOf(state.view).find(s=>s.kind==='lesson'&&s.weekday===day&&s.start===start); if(!c) return;
  const ac=accent(c.title), g=state.view.grades&&state.view.grades.subjects.find(s=>s.name===c.title);
  openSheet(`<span class="tag" style="--ac:${ac};font-size:15px">${esc(c.title)}</span>${c.code?` <span class="tag" style="--ac:${ac};font-size:15px">${codeMark(c.code,c.subject_kind)}</span>`:''}
    ${c.subject_kind?`<p class="sub2" style="margin:8px 0 0">${KIND_NAME[c.subject_kind]} subject</p>`:''}
    <h2 style="margin-top:12px">${DAYS[(day+1)%7]}</h2><p class="sub2">${c.start} – ${c.end}${c.note?' · '+esc(c.note):''}</p>
    ${g?`<div class="perm"><div class="bk">${ic('chart')}</div><div class="g">Your average: ${g.average.toFixed(1)}<small>${gradeWord(g.average)}</small></div></div>`:''}
    <button class="btn t" data-act="close">Close</button>`);
}
const KIND_WORD = {core:'Core',minor:'Minor',elective:'Elective'};
function weightText(kind){                  // how this subject's written and spoken grades are combined, from the household setting
  const w=state.view.grades.weights, pct=w&&w[kind+'_written_pct']; if(pct==null) return '';
  return pct===50?'Written and spoken count equally.':pct<50?`Spoken counts a bit more (${100-pct}%) than written (${pct}%).`:`Written counts a bit more (${pct}%) than spoken (${100-pct}%).`;
}
function gradeSheet(i){
  const s=state.view.grades.subjects[i];
  const list=(type,lab)=>{ const a=s.grades.filter(g=>g.type===type); return a.length?`<h3 style="margin:16px 0 8px;font-size:15px;color:var(--muted)">${lab}</h3><div class="gchips">${a.map(g=>`<span class="gc" style="--gc:${gradeColor(g.grade)}"><b>${Number.isInteger(g.grade)?g.grade:g.grade.toFixed(1)}</b>${esc(g.note||lab)}</span>`).join('')}</div>`:''; };
  openSheet(`<span class="tag" style="--ac:${accent(s.name)};font-size:15px">${esc(s.name)}</span><h2 style="margin-top:12px">${s.average.toFixed(1)} · ${gradeWord(s.average)}</h2>
    <p class="sub2">${KIND_WORD[s.kind]||'Subject'} subject. ${weightText(s.kind)}</p>${list('written','Written')}${list('oral','Spoken')}<button class="btn t" data-act="close">Close</button>`);
}
/* What you can keep private from your parents (grades, medicine): allowed from the age your parents set. Parents then see "private", never what is in it. */
function privacyRows(v){
  const p=v.privacy; if(!p) return '';
  const rows=[['grades','Grades','Your marks and averages'],['health','Medicine','Your medicine reminders']];
  return `<h3 style="margin:16px 0 8px;font-size:15px;color:var(--muted)">Keep private from your parents</h3>`+rows.map(([k,t,sub])=>{
    const x=p[k];
    if(!x.eligible) return `<div class="perm"><div class="bk">${ic('lock')}</div><div class="g">${t}<small>Your parents keep this until you are ${x.min_age}${x.chosen?'. They changed the age, so it is not private any more.':''}</small></div></div>`;
    return `<div class="perm"><div class="bk" style="${x.private?'background:var(--pc);color:var(--on-pc)':''}">${ic(x.private?'lock':'check')}</div><div class="g">${t}<small>${x.private?'Only you can see this':sub+'. Your parents can see this'}</small></div><button class="btn t" data-act="privacy" data-k="${k}" data-on="${x.private?0:1}">${x.private?'Share again':'Make private'}</button></div>`;
  }).join('')+(p.health&&p.health.eligible?`<p class="sub2" style="margin:2px 0 0">Medicine your parents marked as safety-critical always stays visible to them.</p>`:'');
}
async function setPrivacy(section,on){
  if(state.view.demo){ state.view.privacy[section].private=!!on; state.view.privacy[section].chosen=!!on; meSheet(); return; }
  try{ const r=await call('PUT','/privacy',{section,private:!!on}); state.server.privacy=r.privacy; state.view.privacy=r.privacy; store.set('snapshot',state.server); meSheet(); }
  catch(e){ if(e instanceof Unpaired) return unpaired('This phone is not paired any more. Ask a parent for a new QR code.'); toast(e.status?e.message:'Cannot reach Chit. Try again on the home Wi-Fi.'); }
}
function meSheet(){
  const v=state.view, sh=v.share;
  const rows=[['timetable','Timetable','Lessons and rooms'],['stars','Stars and chores','Goals and what you earn'],['reminders','Reminders','Things to bring'],['homework','Homework and tests','Your list, written by you or a parent'],['activities','Activities and calendar','Training times and when to leave'],['bag','Bag checklist','What to pack for tomorrow'],['grades','Grades','Averages per subject'],['health','Health','Medicine reminders']];
  openSheet(`<h2>Hi ${esc(v.child.name)}</h2><p class="sub2">This is your own view. You can look and tick off your chores. Your parents plan everything else.</p>
    <h3 style="margin:0 0 8px;font-size:15px;color:var(--muted)">Look</h3>
    <div class="look"><div class="chipset" role="group" aria-label="Colour mode">${[['dark','Dark'],['light','Light'],['auto','Match phone']].map(([k,t])=>`<button data-act="lookmode" data-k="${k}" aria-pressed="${look.mode===k}" class="${look.mode===k?'on':''}">${t}</button>`).join('')}</div>
    <div class="chipset" role="group" aria-label="Palette">${[['classic','Classic'],['spectrum','Spectrum']].map(([k,t])=>`<button data-act="lookpal" data-k="${k}" aria-pressed="${look.palette===k}" class="${look.palette===k?'on':''}">${t}</button>`).join('')}</div></div>
    <h3 style="margin:0 0 8px;font-size:15px;color:var(--muted)">Your parents are sharing</h3>
    ${rows.map(([k,t,s])=>`<div class="perm"><div class="bk" style="${sh[k]?'background:var(--pc);color:var(--on-pc)':''}">${ic(sh[k]?'check':'lock')}</div><div class="g">${t}<small>${sh[k]?s:'Hidden by your parents'}</small></div></div>`).join('')}
    ${privacyRows(v)}
    ${v.demo?'':`<button class="btn" data-act="install">${ic('share')} Add to Home Screen</button><button class="btn t" data-act="unpair">Remove this phone</button>`}
    <button class="btn t" data-act="close">Close</button>`);
}
let handoffAt=0;
async function prepareHandoff(force){
  // iOS gives the Home Screen app its own empty storage. While this page is open in Safari, keep a fresh one-use link in the address
  // bar and in the manifest, so "Add to Home Screen" at any moment carries the pairing over (exchanged on the app's first launch).
  if(!isIOS||isStandalone()||state.view?.demo||!store.get('token')) return false;
  if(!force&&Date.now()-handoffAt<8*60*1000) return true;
  try{
    const {handoff}=await call('POST','/handoff'); handoffAt=Date.now();
    const link=document.querySelector('link[rel=manifest]'); if(link) link.href=`${API}/manifest?h=${encodeURIComponent(handoff)}`;
    history.replaceState(null,'',`/?h=${encodeURIComponent(handoff)}`); return true;
  }catch{ return false; }
}
async function installSheet(){
  const ok = await prepareHandoff(true);
  const note = ok||!isIOS ? '' : '<p class="sub2">Could not prepare the link. You can still install, then pair the app with the codes from your parent.</p>';
  openSheet(`<h2>Put Chit on your Home Screen</h2><p class="sub2">It then opens full screen like a normal app. No App Store needed.</p>${note}
    <ol class="steps"><li><span>Stay in <b>Safari</b></span></li><li><span>Tap the <b>Share</b> button <span style="color:var(--primary)">${ic('share')}</span></span></li><li><span>Choose <b>Add to Home Screen</b>, keep <b>Open as Web App</b> on, tap <b>Add</b></span></li><li><span>Open Chit from your Home Screen. If it asks to be paired, ask a parent to show the link code and 6 digits.</span></li></ol>
    <button class="btn" data-act="hideinstall">Got it</button>`);
}

function burst(x,y){
  for(let i=0;i<9;i++){ const e=document.createElement('div'); e.className='burst'; e.textContent=i%2?'⭐':'✨';
    e.style.left=x+'px'; e.style.top=y+'px'; e.style.setProperty('--dx',(Math.random()*180-90)+'px'); e.style.setProperty('--dy',(-40-Math.random()*120)+'px'); e.style.setProperty('--rot',(Math.random()*360)+'deg');
    document.body.appendChild(e); setTimeout(()=>e.remove(),950); }
}

/* ---------- network ---------- */
function unpaired(msg){ store.wipe(); store.del('queue'); state.queue=[]; state.server=null; state.view=null; state.mode='welcome'; state.error=msg||''; closeSheet(); render(); }
/* ---------- offline write queue (K4) ----------
   A change (tick, add, delete) is applied to the screen at once and kept in a queue that survives closing the app. It is sent when the hub is
   reachable. If the hub refuses a change (for example a parent already reviewed that chore) it is dropped and the child is told. */
const uid = () => Math.random().toString(36).slice(2,10);
const clone = o => JSON.parse(JSON.stringify(o));
function recomputeBag(v){ (v.bag?.days||[]).forEach(d=>{ d.ready=d.items.length>0&&d.items.every(e=>e.ticked); }); }
function applyOp(v,op){
  if(op.type==='chore'){ const c=v.stars?.chores.find(x=>x.id===op.cid); if(c&&!c.outcome) c.done=op.done; }
  else if(op.type==='hwtick'){ const t=v.homework?.tasks.find(x=>x.id===op.tid); if(t){ t.done=op.done; t.done_on=op.done?isoDay(day0()):null; if(op.done) t.dismissed=false; } }
  else if(op.type==='hwadd'&&v.homework){ const b=op.body; v.homework.tasks.push({id:op.tmp,kind:b.kind,subject:b.subject,title:b.title,due_on:b.due_on,note:null,done:!!op.done,done_on:op.done?isoDay(day0()):null,by:'child',days:daysFromToday(b.due_on),pending:true}); }
  else if(op.type==='hwdel'&&v.homework){ v.homework.tasks=v.homework.tasks.filter(t=>t.id!==op.tid); }
  else if(op.type==='hwdismiss'){ const t=v.homework?.tasks.find(x=>x.id===op.tid); if(t){ t.dismissed=op.dismissed; if(op.dismissed){ t.done=false; t.done_on=null; } } }
  else if(op.type==='remstate'){
    const set=r=>{ if(r.id===op.rid) r.state=op.state; };
    if(v.reminders){ if(op.date===isoDay(day0())) v.reminders.today.forEach(set); if(op.date===isoDay(addDays(day0(),1))) v.reminders.tomorrow.forEach(set); }
    (v.bag?.days||[]).forEach(d=>{ if(d.date===op.date) d.items.forEach(e=>{ if(e.rid===op.rid){ e.na=op.state==='na'; e.ticked=op.state==='done'; } }); });
  }
  else if(op.type==='bagtick'){ (v.bag?.days||[]).forEach(d=>{ if(d.date===op.date) d.items.forEach(e=>{ if(e.key===op.key) e.ticked=op.done; }); }); }
  else if(op.type==='bagadd'&&v.bag){
    v.bag.items.push({id:op.tmp,subject:op.subject,label:op.label,by:'child',pending:true});
    const key=op.label.trim().toLowerCase();
    v.bag.days.forEach(d=>{
      const titles=slotsOf(v).filter(s=>s.kind==='lesson'&&s.weekday===d.weekday).map(s=>s.title.toLowerCase());
      const acts=(v.activities?.weekly||[]).filter(a=>a.weekdays.includes(d.weekday)).map(a=>a.name.toLowerCase());
      const hit=titles.includes(op.subject.toLowerCase())?'subject':acts.includes(op.subject.toLowerCase())?'activity':null;
      if(!hit) return;
      const e=d.items.find(x=>x.key===key); if(e){ if(!e.for.includes(op.subject)) e.for.push(op.subject); } else d.items.push({key,label:op.label.trim(),source:hit,for:[op.subject],ticked:false});
    });
  }
  else if(op.type==='bagdel'&&v.bag){
    const item=v.bag.items.find(i=>i.id===op.iid); v.bag.items=v.bag.items.filter(i=>i.id!==op.iid);
    if(item) v.bag.days.forEach(d=>{ const key=item.label.toLowerCase(); const e=d.items.find(x=>x.key===key); if(!e) return;
      e.for=e.for.filter(x=>x.toLowerCase()!==item.subject.toLowerCase()); if(!e.for.length&&(e.source==='subject'||e.source==='activity')) d.items=d.items.filter(x=>x!==e); });
  }
  if(v.homework) v.homework.summary=hwSummary(v.homework.tasks);
  recomputeBag(v);
}
const overlay = server => { const v=clone(server); state.queue.forEach(op=>applyOp(v,op)); return v; };
const saveQueue = () => store.set('queue',state.queue);

function enqueue(op){
  op.id=uid();
  if(state.view.demo){ applyOp(state.view,op); render(true); return; }
  const q=state.queue, same=(a,b)=>a.type===b.type&&(a.cid||a.tid||a.iid||(a.rid&&a.rid+a.date)||a.date+a.key)===(b.cid||b.tid||b.iid||(b.rid&&b.rid+b.date)||b.date+b.key);
  const tmp = op.tid||op.iid;
  if(tmp&&String(tmp).startsWith('tmp-')){                        // an item that has not reached the hub yet: edit or cancel its pending add
    const add=q.find(x=>x.tmp===tmp);
    if(add){ if(op.type==='hwtick') add.done=op.done; else { q.splice(q.indexOf(add),1); } saveQueue(); state.view=overlay(state.server); render(true); return; }
  }
  const prev=q.findIndex(x=>same(x,op)&&(op.type.endsWith('tick')||['chore','hwdismiss','remstate'].includes(op.type))); if(prev>=0) q.splice(prev,1);   // the last tick on the same thing wins
  q.push(op); saveQueue();
  state.view=overlay(state.server); render(true); flush();
}

let flushing=false;
async function flush(){
  if(flushing||!state.queue.length||state.view?.demo||state.mode!=='app') return;
  flushing=true; let dropped=false, offline=false;
  try{
    while(state.queue.length){
      const op=state.queue[0];
      try{ await sendOp(op); state.queue.shift(); saveQueue(); }
      catch(e){
        if(e instanceof Unpaired) throw e;
        if(e.status){ state.queue.shift(); saveQueue(); dropped=true; toast(e.message); }   // the hub said no: drop it, say why
        else { offline=true; break; }                                                         // no connection: keep it for later
      }
    }
  }catch(e){ flushing=false; if(e instanceof Unpaired) return unpaired('This phone is not paired any more.'); throw e; }
  flushing=false;
  if(offline){ state.offline=true; render(true); return; }
  await refresh(true);
}

async function refresh(keepScroll=true){
  if(state.view?.demo) return;
  try{
    const view=await call('GET','/view'); state.server=view; state.view=overlay(view); state.offline=false; state.mode='app';
    store.set('snapshot',view); store.set('savedAt',new Date().toTimeString().slice(0,5));
  }catch(e){
    if(e instanceof Unpaired) return unpaired('This phone is not paired any more. Ask a parent for a new QR code.');
    const snap=state.server||store.get('snapshot',null);
    if(!snap) { state.mode='welcome'; state.error='Cannot reach Chit. Check that you are on the home Wi-Fi.'; render(); return; }
    state.server=snap; state.view=overlay(snap); state.offline=true; state.savedAt=store.get('savedAt',''); state.mode='app';
  }
  if(!document.getElementById('sheet').classList.contains('on')) render(keepScroll); else if(sheetKind==='bag') bagSheet();
}

async function boot(){
  if(Q.get('demo')==='1'){ state.view=DEMO; makeDemoBag(DEMO); state.mode='app'; return render(); }
  let secret=''; const frag=new URLSearchParams(location.hash.slice(1)); if(frag.get('p')) secret=frag.get('p');
  const handoff=Q.get('h');
  if(store.get('token') && handoff && isStandalone()) history.replaceState(null,'','/');   // the one-use link was already used on a previous launch
  if(!store.get('token') && handoff){
    try{ const {token}=await call('POST','/exchange',{handoff}); store.set('token',token); history.replaceState(null,'','/'); }
    catch(e){ history.replaceState(null,'','/'); state.error=e.message; }
  }
  if(!store.get('token') && secret){ state.pairSecret=secret; state.mode='pair'; state.error=''; return render(); }
  if(!store.get('token')){ state.mode='welcome'; return render(); }
  state.mode='boot'; render();
  await refresh(false); prepareHandoff(); flush();
}

async function submitPair(e){
  e.preventDefault(); if(state.busy) return;
  const code=document.getElementById('code').value.replace(/\s/g,'');
  const link=state.manual?document.getElementById('link').value.replace(/[^A-Za-z0-9]/g,'').toUpperCase():'';
  state.link=state.manual?document.getElementById('link').value:'';
  if(state.manual&&link.length!==8){ state.error='Enter the 8-character link code.'; return render(true); }
  if(code.length!==6){ state.error='Enter all 6 digits.'; return render(true), document.getElementById('code').focus(); }
  state.busy=true; state.error=''; render(true);
  try{
    const {token}=await call('POST','/pair',{...(state.manual?{link}:{secret:state.pairSecret}),code,label:/iphone/i.test(navigator.userAgent)?'iPhone':/ipad/i.test(navigator.userAgent)?'iPad':/android/i.test(navigator.userAgent)?'Android phone':'Browser'},'');
    store.set('token',token); state.pairSecret=''; state.manual=false; history.replaceState(null,'','/');
    state.busy=false; await refresh(false); prepareHandoff(true);
    if(state.mode==='app') openSheet(`<div style="text-align:center"><div class="logo" style="margin:6px auto 12px">${ic('check')}</div><h2>You are connected, ${esc(state.view.child.name)}!</h2><p class="sub2">This phone now shows your own plan. Your parents can remove it any time.</p></div><button class="btn" data-act="close">Let's go</button>`);
  }catch(err){
    state.busy=false; state.error=err.message||'Could not connect.';
    if(err.status===410||err.status===423||err.status===429){ state.pairSecret=''; state.manual=false; state.link=''; history.replaceState(null,'','/'); state.mode='welcome'; }
    render(true);
    const c=document.getElementById('code'); if(c&&state.mode==='pair'){ c.value=''; (document.getElementById('link')&&err.status!==403?document.getElementById('link'):c).focus(); }
  }
}

/* ---------- events ---------- */
document.addEventListener('submit',e=>{ if(e.target.id==='pairform') submitPair(e); });
document.addEventListener('input',e=>{
  const id=e.target.id;
  if(id==='code'){ let d=e.target.value.replace(/\D/g,'').slice(0,6); e.target.value=d.length>3?d.slice(0,3)+' '+d.slice(3):d;
    const ready = !state.manual || document.getElementById('link').value.replace(/[^A-Za-z0-9]/g,'').length===8; if(d.length===6&&ready) document.getElementById('pairform').requestSubmit(); }
  else if(id==='link'){ let l=e.target.value.replace(/[^A-Za-z0-9]/g,'').toUpperCase().slice(0,8); e.target.value=l.length>4?l.slice(0,4)+'-'+l.slice(4):l; if(l.length===8) document.getElementById('code').focus(); }
});
document.addEventListener('change',e=>{ if(e.target.id==='hwdue'){ hwState.touchedDue=true; hwState.due=e.target.value; } });
document.addEventListener('toggle',e=>{ if(e.target.id==='doneset') state.showDone=e.target.open; },true);
document.addEventListener('click',async e=>{
  const b=e.target.closest('[data-act]'); if(!b) return; const a=b.dataset.act;
  if(a==='tab'){ state.tab=b.dataset.id; render(); }
  else if(a==='seg'){ state.seg=b.dataset.v; render(true); }
  else if(a==='chore'){
    const c=state.view.stars.chores.find(x=>x.id===b.dataset.id); if(!c||c.outcome) return;
    const done=!c.done; if(done){ const r=b.getBoundingClientRect(); burst(r.left+30,r.top+25); navigator.vibrate&&navigator.vibrate(12); }
    enqueue({type:'chore',cid:c.id,done});
  }
  else if(a==='bagtick'){
    const day=state.view.bag.days.find(d=>d.date===b.dataset.date), e=day&&day.items.find(x=>x.key===b.dataset.key); if(!e) return;
    if(e.rid) enqueue({type:'remstate',rid:e.rid,date:day.date,state:e.ticked?null:'done'});     // a reminder in the checklist is the reminder itself
    else enqueue({type:'bagtick',date:day.date,key:e.key,done:!e.ticked});
  }
  else if(a==='layout'){ state.layout=isCards()?'list':'cards'; store.set('layout',state.layout); render(true); }
  else if(a==='hwdismiss'){ const t=state.view.homework.tasks.find(x=>x.id===b.dataset.id); if(!t) return; const dismiss=!t.dismissed; enqueue({type:'hwdismiss',tid:t.id,dismissed:dismiss});
    if(dismiss) toast('Marked not relevant',()=>enqueue({type:'hwdismiss',tid:t.id,dismissed:false})); }
  else if(a==='remdone'||a==='remna'||a==='remundo'){ enqueue({type:'remstate',rid:b.dataset.id,date:b.dataset.date,state:a==='remdone'?'done':a==='remna'?'na':null}); }
  else if(a==='bagedit') bagSheet();
  else if(a==='bagadd'){ enqueue({type:'bagadd',tmp:'tmp-'+uid(),subject:b.dataset.subject,label:b.dataset.label}); bagSheet(); }
  else if(a==='bagdel'){ enqueue({type:'bagdel',iid:b.dataset.id}); bagSheet(); }
  else if(a==='bagnew'){
    const subject=document.getElementById('bagsubj').value.trim(), label=document.getElementById('baglabel').value.trim(), err=document.getElementById('bagerr');
    if(!subject||!label){ err.textContent='Write the subject and the item.'; return; }
    if(state.view.bag.items.some(i=>i.subject.toLowerCase()===subject.toLowerCase()&&i.label.toLowerCase()===label.toLowerCase())){ err.textContent='That item is already on the list.'; return; }
    enqueue({type:'bagadd',tmp:'tmp-'+uid(),subject,label}); bagSheet();
  }
  else if(a==='cell') lessonSheet(+b.dataset.d,b.dataset.s);
  else if(a==='sub') gradeSheet(+b.dataset.i);
  else if(a==='me') meSheet();
  else if(a==='lookmode'){ setLook({mode:b.dataset.k}); meSheet(); }
  else if(a==='lookpal'){ setLook({palette:b.dataset.k}); meSheet(); }
  else if(a==='privacy') setPrivacy(b.dataset.k,b.dataset.on==='1');
  else if(a==='install') installSheet();
  else if(a==='hideinstall'){ store.set('hideInstall',true); closeSheet(); render(true); }
  else if(a==='demo'){ location.search='?demo=1'; }
  else if(a==='cancelpair'){ state.manual=false; state.link=''; state.pairSecret=''; history.replaceState(null,'','/'); state.mode='welcome'; state.error=''; render(); }
  else if(a==='unpair'){ try{ await call('POST','/unpair'); }catch{} unpaired('This phone was removed. Pair it again with a new QR code.'); }
  else if(a==='manual'){ state.manual=true; state.mode='pair'; state.error=''; render(); }
  else if(a==='addhw') addHwSheet();
  else if(a==='hwkind'){ hwState.kind=b.dataset.k; document.querySelectorAll('#kindset button').forEach(x=>x.classList.toggle('on',x===b)); suggestDue(); }
  else if(a==='hwsubj'){ const on=b.classList.contains('on'); document.querySelectorAll('.subjset button').forEach(x=>{ x.classList.remove('on'); x.setAttribute('aria-pressed','false'); }); hwState.subject=on?'':b.dataset.s; if(!on){ b.classList.add('on'); b.setAttribute('aria-pressed','true'); } suggestDue(); }
  else if(a==='hwsave') saveHw();
  else if(a==='hwopen') hwSheet(b.dataset.id);
  else if(a==='hwdone'){ const t=state.view.homework.tasks.find(x=>x.id===b.dataset.id); if(b.dataset.close) closeSheet(); if(!t) return; const done=!t.done; setHwDone(t.id,done); if(done) toast('Marked done',()=>setHwDone(t.id,false)); }
  else if(a==='hwdel') delHw(b.dataset.id);
  else if(a==='close') closeSheet();
});
function toast(msg,undo){
  const t=document.createElement('div'); t.className='toast'; t.textContent=msg;
  if(undo){ const b=document.createElement('button'); b.textContent='Undo'; b.setAttribute('aria-label','Undo: '+msg); b.onclick=()=>{ t.remove(); undo(); }; t.appendChild(b); }
  document.body.appendChild(t); setTimeout(()=>t.remove(),undo?7000:3200);
  const l=document.getElementById('live'); if(l){ l.textContent=''; setTimeout(()=>{ l.textContent=msg; },50); }
}

document.addEventListener('visibilitychange',()=>{ if(!document.hidden && state.mode==='app'){ state.queue.length?flush():refresh(true); prepareHandoff(); } });
window.addEventListener('online',()=>{ if(state.mode==='app') state.queue.length?flush():refresh(true); });
setInterval(()=>{ if(state.mode==='app' && !document.hidden) state.queue.length?flush():refresh(true); },60000);
boot();
if('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(()=>{});
