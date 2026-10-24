import json
import unittest
from pathlib import Path
from player_lab.analysis import *

def event(kind,index,period=1,time='00:00:00',**extra):
    return {'id':str(index),'index':index,'period':period,'timestamp':time,'type':{'name':kind},'team':{'id':1,'name':'A'},**extra}

class TimeTests(unittest.TestCase):
    def starters(self):return event('Starting XI',1,tactics={'lineup':[{'player':{'id':i},'position':{'id':1 if i==1 else 14}} for i in range(1,12)]})
    def test_added_time_and_extra_time_clock(self):
        self.assertEqual(seconds('01:02:03.5'),3723.5)
        self.assertEqual(elapsed('46:00',2,{1:48*60,2:50*60}),49*60)
        self.assertEqual(elapsed('106:00',4,{1:48*60,2:50*60,3:16*60,4:17*60}),115*60)
        self.assertEqual(elapsed('125:00',5,{1:45*60,2:45*60}),90*60)
    def test_invalid_time_and_missing_period(self):
        with self.assertRaises(ValueError):seconds('nan:1')
        with self.assertRaises(ValueError):elapsed('40:00',2,{1:2700,2:2700})
        with self.assertRaises(ValueError):period_lengths([])
    def test_duplicate_half_ends_count_once(self):
        ends=[event('Half End',1,time='00:48:00'),event('Half End',2,time='00:48:00'),event('Half End',3,period=2,time='00:51:00')]
        self.assertEqual(period_lengths(ends),{1:2880,2:3060})
    def test_substitution_and_red_card_conserve_minutes(self):
        e=[self.starters(),event('Substitution',2,time='00:30:00',player={'id':2},substitution={'replacement':{'id':12}}),event('Bad Behaviour',3,period=2,time='00:15:00',player={'id':3},bad_behaviour={'card':{'name':'Red Card'}})]
        intervals,loss,roles=playing_intervals(e,{1:48*60,2:50*60})
        self.assertEqual(intervals[2],[(0,1800)]);self.assertEqual(intervals[12],[(1800,5880)])
        self.assertEqual(loss[1],35*60)
        self.assertAlmostEqual(sum(b-a for rows in intervals.values() for a,b in rows),11*5880-35*60)
        self.assertAlmostEqual(sum(sum(v.values()) for v in roles.values()),11*98-35)
    def test_tactical_role_changes_do_not_change_minutes(self):
        e=[self.starters(),event('Tactical Shift',2,time='00:20:00',tactics={'lineup':[{'player':{'id':2},'position':{'id':21}}]})]
        intervals,_,roles=playing_intervals(e,{1:2700,2:2700})
        self.assertEqual(intervals[2],[(0,5400)]);self.assertEqual(roles[2],{'Midfielder':20,'Forward':70})
    def test_bench_dismissal_and_shootout_do_not_remove_minutes(self):
        e=[self.starters(),event('Bad Behaviour',2,player={'id':99},bad_behaviour={'card':{'name':'Red Card'}}),event('Substitution',3,period=5,player={'id':1},substitution={'replacement':{'id':50}})]
        intervals,loss,_=playing_intervals(e,{1:2700,2:2700});self.assertNotIn(50,intervals);self.assertEqual(loss,{})
    def test_invalid_substitution_rejected(self):
        with self.assertRaises(ValueError):playing_intervals([self.starters(),event('Substitution',2,player={'id':99},substitution={'replacement':{'id':50}})],{1:2700,2:2700})

class MetricTests(unittest.TestCase):
    def test_zone_edges_and_invalid_coordinates(self):
        self.assertEqual(zone([0,0]),0);self.assertEqual(zone([120,80]),23);self.assertEqual(zone([20,20]),7)
        self.assertIsNone(zone([-1,40]));self.assertIsNone(zone([float('nan'),2]));self.assertIsNone(zone(None))
    def test_progressive_definition(self):
        self.assertTrue(progressive([45,40],[60,60]));self.assertFalse(progressive([45,40],[59,40]));self.assertFalse(progressive([20,40],[50,40]))
    def test_rate_and_percentile_ties(self):
        self.assertEqual(per90(2,180),1);self.assertIsNone(per90(2,0));self.assertEqual(percentile(5,[5,5]),50);self.assertEqual(percentile(2,[1,2,3]),50);self.assertIsNone(percentile(1,[]))
    def test_role_mapping(self):
        self.assertEqual(role(1),'Goalkeeper');self.assertEqual(role(7),'Defender');self.assertEqual(role(20),'Midfielder');self.assertEqual(role(17),'Forward')

class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=json.loads(Path('reports/results.json').read_text(encoding='utf-8'))
    def test_complete_selection_and_minutes_audits(self):
        self.assertEqual(len(self.r['matches']),16);self.assertEqual(len(self.r['players']),287)
        for m in self.r['matches']:
            for a in m['minutes_audit']:self.assertAlmostEqual(a['observed_minutes'],a['expected_minutes'],places=7)
            for p in m['players']:self.assertAlmostEqual(sum(p['roles'].values()),p['minutes'],places=7)
    def test_aggregates_reconstruct(self):
        actual={p['id']:p for p in aggregate(self.r['matches'])}
        for p in self.r['players']:self.assertEqual(p,actual[p['id']])
    def test_zone_totals_match_player_totals(self):
        for m in self.r['matches']:
            for p in m['players']:
                self.assertEqual(sum(z['shots'] for z in p['shot_zones'].values()),p['stats']['shots'])
                self.assertAlmostEqual(sum(z['xg'] for z in p['shot_zones'].values()),p['stats']['xg'],places=7)
                self.assertLessEqual(sum(p['pass_flows'].values()),p['stats']['completed_passes'])
    def test_shootouts_excluded_and_no_raw_event_records(self):
        self.assertEqual(self.r['summary']['shootout_events_excluded'],106)
        self.assertEqual(self.r['summary']['shots'],387)
        for m in self.r['matches']:self.assertNotIn('events',m);self.assertFalse(m['quality'])
    def test_final_goals_and_penalty_separation(self):
        m=next(m for m in self.r['matches'] if m['id']==3869685)
        messi=next(p for p in m['players'] if p['id']==5503);mbappe=next(p for p in m['players'] if p['id']==3009)
        self.assertEqual(messi['stats']['goals'],2);self.assertEqual(mbappe['stats']['goals'],3)
        self.assertEqual(mbappe['stats']['np_goals'],1);self.assertEqual(messi['stats']['np_goals'],1)
        self.assertGreater(messi['minutes'],120)

if __name__=='__main__':unittest.main()
