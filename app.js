'use strict';
// Harper Rail: This is a standalone local itinerary planner.
// It deliberately does NOT query, scrape, monitor or book Korail seats.
const KEY = 'harper-rail-routes-v1';
const $ = id => document.getElementById(id);
let journeys = [];
try { const parsed = JSON.parse(localStorage.getItem(KEY) || '[]'); journeys = Array.isArray(parsed) ? parsed : []; } catch { journeys = []; }
function persist() { try { localStorage.setItem(KEY, JSON.stringify(journeys)); return true; } catch { toast('브라우저 저장이 차단되어 있습니다.'); return false; } }
function toast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toast.timeout); toast.timeout = setTimeout(() => el.classList.remove('show'), 3100); }
function localDate() { const d = new Date(); const y = d.getFullYear(), m = String(d.getMonth()+1).padStart(2,'0'), day=String(d.getDate()).padStart(2,'0'); return `${y}-${m}-${day}`; }
$('date').min=localDate(); $('date').value=localDate();
function tabs(id) { document.querySelectorAll('.tab').forEach(t=>{ const selected=t.dataset.tab===id;t.classList.toggle('active',selected);t.setAttribute('aria-selected', String(selected)); }); document.querySelectorAll('.panel').forEach(p=>{p.hidden=p.id!==id;p.classList.toggle('active',p.id===id);}); }
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>tabs(t.dataset.tab)));
$('swap').addEventListener('click',()=>{const a=$('from').value; $('from').value=$('to').value; $('to').value=a;});
function values(){return {from:$('from').value,to:$('to').value,date:$('date').value,time:$('time').value,train:$('train').value.trim(),seat:$('class').value,count:$('count').value,alias:$('alias').value.trim()};}
function loadValues(v){$('from').value=v.from;$('to').value=v.to;$('date').value=v.date;$('time').value=v.time;$('train').value=v.train;$('class').value=v.seat;$('count').value=v.count;$('alias').value=v.alias;tabs('search');window.scrollTo({top:0,behavior:'smooth'});}
function validate(v){if(v.from===v.to){toast('출발역과 도착역은 달라야 해요.');return false;}if(!v.date || v.date<localDate()){toast('오늘 또는 이후 날짜를 선택해 주세요.');return false;}return true;}
$('journeyForm').addEventListener('submit',e=>{e.preventDefault();const v=values();if(!validate(v))return;journeys.unshift({...v,id:(crypto.randomUUID ? crypto.randomUUID() : String(Date.now()))});if(journeys.length>100)journeys=journeys.slice(0,100);if(persist()){render();toast('여정이 이 브라우저에 저장됐어요.');tabs('saved');}});
$('openBooking').addEventListener('click',()=>{const v=values();if(!validate(v))return;window.open('https://www.korail.com/ticket/main','_blank','noopener,noreferrer');toast('코레일에서 조건을 다시 입력하고 직접 예매해 주세요.');});
document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>{const morning=b.dataset.preset==='morning';$('from').value=morning?'대전':'수서';$('to').value=morning?'수서':'대전';$('time').value=morning?'07:00':'19:00';toast('출퇴근 조건이 입력됐어요.');}));
const labels={both:'일반실 + 특실',standard:'일반실',first:'특실'};
function render(){const el=$('savedList');el.replaceChildren();$('savedCount').textContent=String(journeys.length);if(!journeys.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='아직 저장한 여정이 없습니다.';el.append(empty);return;}for(const v of journeys){const card=document.createElement('div');card.className='saveditem';const title=document.createElement('h3');title.textContent=(v.alias?`${v.alias} · `:'')+`${v.from} → ${v.to}`;const detail=document.createElement('p');detail.textContent=`${v.date} ${v.time} · ${labels[v.seat]||v.seat} · ${v.count}명${v.train?' · '+v.train+'호':''}`;const actions=document.createElement('div');actions.className='itemactions';const edit=document.createElement('button');edit.type='button';edit.textContent='조건 불러오기';edit.onclick=()=>loadValues(v);const official=document.createElement('button');official.type='button';official.textContent='공식 예매 ↗';official.onclick=()=>window.open('https://www.korail.com/ticket/main','_blank','noopener,noreferrer');const del=document.createElement('button');del.type='button';del.className='delete';del.textContent='삭제';del.onclick=()=>{journeys=journeys.filter(x=>x.id!==v.id);persist();render();};actions.append(edit,official,del);card.append(title,detail,actions);el.append(card);}}
render();
