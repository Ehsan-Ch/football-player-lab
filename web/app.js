import {aggregate,cohort,metric,percentile,csv} from './core.mjs';
const $=id=>document.getElementById(id),fmt=(x,n=2)=>x==null?'—':Number(x).toFixed(n),escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let report,pool=[],scope=[],idA=5503,idB=3009;
const metrics=[['npxg','Non-penalty xG'],['xa','Shot-assisted xG'],['progressive_passes','Progressive passes'],['completed_dribbles','Completed dribbles'],['pressures','Pressures'],['pass_completion','Pass completion %']];
function options(select,players,value){select.replaceChildren();for(const p of players){const o=document.createElement('option');o.value=p.id;o.textContent=p.name+' · '+p.team;select.append(o);}select.value=String(value);select.disabled=!players.length;}
function refresh(){
 scope=report.matches.filter(m=>$('stage').value==='all'||m.stage===$('stage').value);
 pool=cohort(aggregate(scope),{role:$('role').value,team:$('team').value,minutes:Number($('minutes').value)}).sort((a,b)=>a.name.localeCompare(b.name));
 if(!pool.some(p=>p.id===idA))idA=pool[0]?.id;
 if(!pool.some(p=>p.id===idB))idB=pool.find(p=>p.id!==idA)?.id??pool[0]?.id;
 options($('playerA'),pool,idA);options($('playerB'),pool,idB);
 $('poolNote').textContent=`${pool.length} eligible players · ${scope.length} matches in scope · ${$('role').value} · minimum ${$('minutes').value} elapsed minutes. ${pool.length<5?'Small comparison pool: interpret percentiles cautiously.':''}`;
 $('export').disabled=!pool.length;renderProfiles();renderTable();
}
function card(p,suffix){
 $('name'+suffix).textContent=p?.name??'No eligible player';$('meta'+suffix).textContent=p?`${p.team} · ${p.role} · ${p.appearances} appearances · ${fmt(p.minutes,1)} minutes`:'Broaden the filters or lower the minutes threshold.';
 $('stats'+suffix).innerHTML=p?[[p.stats.goals,'Goals'],[fmt(p.stats.npxg),'NP xG'],[fmt(p.stats.xa),'Shot xA'],[p.stats.key_passes,'Key passes']].map(([v,label])=>`<div><b>${v}</b><span>${label}</span></div>`).join(''):'';
}
function renderProfiles(){
 const a=pool.find(p=>p.id===idA),b=pool.find(p=>p.id===idB);card(a,'A');card(b,'B');
 $('metrics').innerHTML=metrics.map(([key,label])=>{const peers=pool.map(p=>metric(p,key)).filter(x=>x!=null);return `<article class="metric-card"><div class="metric-title">${label}${key==='pass_completion'?'':' /90'}</div>`+[[a,'A',''],[b,'B','b']].map(([p,letter,cls])=>{const val=p?metric(p,key):null,pct=percentile(val,peers);return `<div class="bar-row"><span>${letter}</span><div class="track" title="${pct==null?'No denominator':fmt(pct,1)+' percentile'}"><div class="bar ${cls}" style="width:${pct??0}%"></div></div><strong>${key==='pass_completion'?fmt(val==null?null:100*val,1):fmt(val)}</strong></div>`;}).join('')+'</article>';}).join('');
 renderMaps(a,b);
}
function pitchBase(){return '<rect x="0" y="0" width="120" height="80" fill="#163a32"/><g stroke="#99b7a4" stroke-width=".35" fill="none"><rect x="1" y="1" width="118" height="78"/><path d="M60 1V79 M1 18H18V62H1 M119 18H102V62H119 M1 30H6V50H1 M119 30H114V50H119"/><circle cx="60" cy="40" r="9"/><circle cx="60" cy="40" r=".6" fill="#99b7a4"/></g>';}
const center=z=>[10+(Number(z)%6)*20,10+Math.floor(Number(z)/6)*20];
function map(p,suffix){
 $('mapName'+suffix).textContent=p?.name??'No eligible player';let shapes=pitchBase(),text='No player selected.';const color=suffix==='A'?'#d7eea9':'#ffba8b';
 if(p&&$('mapMode').value==='shots'){
  for(const [zone,v]of Object.entries(p.shot_zones)){const [x,y]=center(zone),radius=2+Math.sqrt(v.xg)*4;shapes+=`<g><title>${v.shots} shots · ${v.goals} goals · ${fmt(v.xg)} xG · ${v.penalties} penalties</title><circle cx="${x}" cy="${y}" r="${radius}" fill="${color}" opacity=".8"/><text x="${x}" y="${y+1.1}" text-anchor="middle" font-size="3" fill="#163a32">${v.shots}</text></g>`;}
  text=`${p.stats.shots} shots · ${p.stats.goals} goals · ${fmt(p.stats.xg)} total xG. Penalties included here; profile NP xG excludes them.`;
 }else if(p){
  const flows=Object.entries(p.pass_flows).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,12);
  shapes+=`<defs><marker id="arrow${suffix}" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto"><path d="M0 0L4 2L0 4" fill="${color}"/></marker></defs>`;
  for(const [route,count]of flows){const [from,to]=route.split(':'),[x,y]=center(from),[x2,y2]=center(to);shapes+=`<g><title>${count} completed passes: zone ${from} → ${to}</title>`+(from===to?`<circle cx="${x}" cy="${y}" r="4" fill="none" stroke="${color}" stroke-width="${Math.min(2,.4+Math.sqrt(count)*.2)}"/>`:`<path d="M${x} ${y} L${x2} ${y2}" stroke="${color}" opacity=".8" stroke-width="${Math.min(2,.4+Math.sqrt(count)*.2)}" marker-end="url(#arrow${suffix})"/>`)+'</g>';}
  text=`Top ${flows.length} zone connections by completed passes, representing ${flows.reduce((s,f)=>s+f[1],0)} of ${p.stats.completed_passes} completed passes. Loops show passes within one zone.`;
 }
 $('pitch'+suffix).innerHTML=`<svg viewBox="-3 -3 126 86" role="img" aria-label="${escape(p?.name??'Empty')} ${$('mapMode').value==='shots'?'shot zones':'passing flows'}">${shapes}</svg>`;$('mapText'+suffix).textContent=text;
}
function renderMaps(a=pool.find(p=>p.id===idA),b=pool.find(p=>p.id===idB)){map(a,'A');map(b,'B');$('mapNote').textContent=$('mapMode').value==='shots'?'6 × 4 spatial bins · bubble size increases with total zone xG · numbers are shot counts · attacking direction →. These are zone centers, not exact shot positions.':'6 × 4 spatial bins · thicker arrows mean more completed passes · top 12 connections per player · attacking direction →. Arrows join zone centers, not exact pass trajectories.';}
function renderTable(){
 const search=$('search').value.toLocaleLowerCase(),key=$('sort').value;
 const rows=pool.filter(p=>(p.name+' '+p.team).toLocaleLowerCase().includes(search)).sort((a,b)=>(metric(b,key)??-Infinity)-(metric(a,key)??-Infinity)||a.name.localeCompare(b.name));
 $('rows').replaceChildren();for(const p of rows.slice(0,20)){const row=document.createElement('tr');row.innerHTML=`<td>${escape(p.name)}<small>${escape(p.team)} · ${escape(p.role)}</small></td><td>${fmt(p.minutes,1)}</td><td>${fmt(p.per90.npxg)}</td><td>${fmt(p.per90.xa)}</td><td>${fmt(p.per90.progressive_passes)}</td>`;const td=document.createElement('td');for(const letter of ['A','B']){const button=document.createElement('button');button.textContent=letter;button.setAttribute('aria-label',`Compare ${p.name} as player ${letter}`);button.onclick=()=>{if(letter==='A')idA=p.id;else idB=p.id;$('player'+letter).value=p.id;renderProfiles();};td.append(button);}row.append(td);$('rows').append(row);}
 if(!rows.length)$('rows').innerHTML='<tr><td colspan="6">No players match these filters.</td></tr>';
 $('tableNote').textContent=`Showing ${Math.min(20,rows.length)} of ${rows.length} matching players. Ordered by ${$('sort').selectedOptions[0].textContent}; values come from the selected match scope. Search affects this table only.`;
}
for(const id of ['stage','role','team','minutes'])$(id).onchange=refresh;
$('playerA').onchange=e=>{idA=Number(e.target.value);renderProfiles();};$('playerB').onchange=e=>{idB=Number(e.target.value);renderProfiles();};
$('mapMode').onchange=()=>renderMaps();$('sort').onchange=renderTable;$('search').oninput=renderTable;
$('export').onclick=()=>{const url=URL.createObjectURL(new Blob(['\ufeff'+csv(pool)],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='touchline-'+$('stage').value.replaceAll(' ','-')+'-'+$('role').value+'-'+$('minutes').value+'min.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
for(const c of document.querySelectorAll('button,select,input'))c.disabled=true;
try{const r=await fetch('./reports/results.json');if(!r.ok)throw Error('Could not load the report');report=await r.json();
 for(const s of [...new Set(report.matches.map(m=>m.stage))]){const o=document.createElement('option');o.value=s;o.textContent=s;$('stage').append(o);}
 for(const t of [...new Set(report.players.map(p=>p.team))].sort()){const o=document.createElement('option');o.value=t;o.textContent=t;$('team').append(o);}
 for(const c of document.querySelectorAll('button,select,input'))c.disabled=false;refresh();
}catch(e){$('error').textContent='Open the public demo or serve this folder locally. '+e.message;}
