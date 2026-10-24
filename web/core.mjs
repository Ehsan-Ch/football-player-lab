export const fields=['shots','np_shots','goals','np_goals','xg','npxg','xa','passes','completed_passes','progressive_passes','key_passes','dribbles','completed_dribbles','pressures','recoveries'];
export const rate=(value,minutes)=>minutes>0?value*90/minutes:null;
export function percentile(value,peers){if(value==null||!peers.length)return null;return 100*(peers.filter(x=>x<value).length+.5*peers.filter(x=>x===value).length)/peers.length;}
export function aggregate(matches){
 const map=new Map();
 for(const match of matches)for(const p of match.players){
  if(!map.has(p.id))map.set(p.id,{id:p.id,name:p.name,team:p.team,minutes:0,appearances:0,roles:{},stats:Object.fromEntries(fields.map(k=>[k,0])),shot_zones:{},pass_flows:{}});
  const a=map.get(p.id);a.minutes+=p.minutes;a.appearances++;
  for(const [k,v]of Object.entries(p.roles))a.roles[k]=(a.roles[k]||0)+v;
  for(const k of fields)a.stats[k]+=p.stats[k];
  for(const [z,v]of Object.entries(p.shot_zones)){a.shot_zones[z]??={shots:0,goals:0,xg:0,penalties:0};for(const k of Object.keys(v))a.shot_zones[z][k]+=v[k];}
  for(const [z,v]of Object.entries(p.pass_flows))a.pass_flows[z]=(a.pass_flows[z]||0)+v;
 }
 return [...map.values()].map(p=>({...p,role:Object.keys(p.roles).sort((a,b)=>p.roles[b]-p.roles[a])[0],per90:Object.fromEntries(fields.map(k=>[k,rate(p.stats[k],p.minutes)])),pass_completion:p.stats.passes?p.stats.completed_passes/p.stats.passes:null}));
}
export function cohort(players,{role='Forward',team='all',minutes=90}={}){return players.filter(p=>p.minutes>=minutes&&(role==='Outfield'?p.role!=='Goalkeeper':p.role===role)&&(team==='all'||p.team===team));}
export const metric=(p,key)=>key==='pass_completion'?p.pass_completion:p.per90[key];
export function csv(players){
 const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
 const keys=['name','team','role','appearances','minutes',...fields,...fields.map(k=>k+'_per90'),'pass_completion'];
 return [keys,...players.map(p=>[p.name,p.team,p.role,p.appearances,p.minutes,...fields.map(k=>p.stats[k]),...fields.map(k=>p.per90[k]),p.pass_completion])].map(row=>row.map(quote).join(',')).join('\r\n');
}
