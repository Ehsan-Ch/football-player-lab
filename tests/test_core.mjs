import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {aggregate,cohort,percentile,rate,csv,fields} from '../web/core.mjs';
const report=JSON.parse(fs.readFileSync(new URL('../reports/results.json',import.meta.url),'utf8'));
test('browser aggregation agrees with independent Python report',()=>{
 const actual=new Map(aggregate(report.matches).map(p=>[p.id,p]));
 for(const p of report.players){const a=actual.get(p.id);assert.equal(a.appearances,p.appearances);assert.equal(a.role,p.role);assert.ok(Math.abs(a.minutes-p.minutes)<1e-8);for(const k of fields){assert.ok(Math.abs(a.stats[k]-p.stats[k])<1e-8);assert.ok(Math.abs(a.per90[k]-p.per90[k])<1e-8);}}
});
test('cohort filters role, team and minutes without changing totals',()=>{const p=aggregate(report.matches);const c=cohort(p,{role:'Forward',team:'Argentina',minutes:180});assert.ok(c.length>0);assert.ok(c.every(x=>x.role==='Forward'&&x.team==='Argentina'&&x.minutes>=180));assert.equal(cohort(p,{role:'Forward',minutes:10000}).length,0);});
test('scope changes use only selected matches',()=>{const final=aggregate(report.matches.filter(m=>m.stage==='Final'));assert.equal(final.find(p=>p.id===3009).stats.goals,3);assert.ok(final.every(p=>p.appearances===1));});
test('midrank ties and empty denominators',()=>{assert.equal(percentile(3,[3,3,3]),50);assert.equal(percentile(null,[1]),null);assert.equal(percentile(1,[]),null);assert.equal(rate(2,180),1);assert.equal(rate(2,0),null);});
test('CSV quotes names and preserves comparison fields',()=>{const p=aggregate(report.matches).slice(0,1);p[0].name='A, "B"';const out=csv(p);assert.ok(out.includes('"A, ""B"""'));assert.ok(out.includes('"npxg_per90"'));assert.equal(out.split('\r\n').length,2);});
