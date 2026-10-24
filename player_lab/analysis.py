"""Deterministic player metrics. Publishes aggregate analysis, never raw events."""
import json
import math
from collections import Counter,defaultdict
from pathlib import Path
from .data import load

BASE_MINUTES={1:0,2:45,3:90,4:105}
FIELDS=('shots','np_shots','goals','np_goals','xg','npxg','xa','passes','completed_passes','progressive_passes','key_passes','dribbles','completed_dribbles','pressures','recoveries')

def seconds(value):
    parts=[float(x) for x in value.split(':')]
    if len(parts) not in (2,3) or any(not math.isfinite(x) or x<0 for x in parts):raise ValueError('Invalid time')
    if len(parts)==2:return parts[0]*60+parts[1]
    return parts[0]*3600+parts[1]*60+parts[2]

def period_lengths(events):
    lengths={}
    for e in events:
        p=e['period']
        if p<=4 and e['type']['name']=='Half End':lengths[p]=max(lengths.get(p,0),seconds(e['timestamp']))
    if sorted(lengths) not in ([1,2],[1,2,3,4]):raise ValueError('Missing complete match periods')
    return lengths

def elapsed(clock,period,lengths):
    if period==5:return sum(lengths.values())
    if period not in lengths:raise ValueError('Invalid match period')
    within=seconds(clock)-BASE_MINUTES[period]*60
    if within<0 or within>lengths[period]+1:raise ValueError('Clock outside period')
    return sum(v for p,v in lengths.items() if p<period)+min(within,lengths[period])

def role(position):
    if position==1:return 'Goalkeeper'
    if 2<=position<=8:return 'Defender'
    if 9<=position<=16 or 18<=position<=20:return 'Midfielder'
    if position in (17,21,22,23,24,25):return 'Forward'
    raise ValueError('Unknown position')

def playing_intervals(events,lengths):
    active={};intervals=defaultdict(list);teams={};red_loss=Counter();role_active={};role_minutes=defaultdict(Counter)
    def close_role(pid,now):
        start,position=role_active.pop(pid);role_minutes[pid][role(position)]+=(now-start)/60
    for e in sorted(events,key=lambda e:e['index']):
        if e['period']>4:continue
        kind=e['type']['name'];now=sum(v for p,v in lengths.items() if p<e['period'])+seconds(e['timestamp'])
        if kind=='Starting XI':
            lineup=e['tactics']['lineup']
            if len(lineup)!=11:raise ValueError('Expected eleven starters')
            for p in lineup:
                pid=p['player']['id']
                if pid in active:raise ValueError('Duplicate starter')
                active[pid]=0;teams[pid]=e['team']['id'];role_active[pid]=(0,p['position']['id'])
        elif kind=='Substitution':
            out=e['player']['id'];incoming=e['substitution']['replacement']['id']
            if out not in active or incoming in active:raise ValueError('Invalid substitution')
            position=role_active[out][1];close_role(out,now)
            intervals[out].append((active.pop(out),now));active[incoming]=now;teams[incoming]=e['team']['id'];role_active[incoming]=(now,position)
        elif kind=='Tactical Shift':
            for p in e['tactics']['lineup']:
                pid=p['player']['id']
                if pid in active:
                    close_role(pid,now);role_active[pid]=(now,p['position']['id'])
        elif e.get('bad_behaviour',{}).get('card',{}).get('name') in ('Red Card','Second Yellow') or e.get('foul_committed',{}).get('card',{}).get('name') in ('Red Card','Second Yellow'):
            pid=e.get('player',{}).get('id')
            if pid in active:
                close_role(pid,now);intervals[pid].append((active.pop(pid),now));red_loss[teams[pid]]+=sum(lengths.values())-now
    for pid,start in active.items():
        intervals[pid].append((start,sum(lengths.values())));close_role(pid,sum(lengths.values()))
    return intervals,red_loss,role_minutes

def zone(location):
    if not location or len(location)<2 or not all(math.isfinite(v) for v in location[:2]):return None
    x,y=location[:2]
    if not (0<=x<=120 and 0<=y<=80):return None
    return min(5,int(x//20))+6*min(3,int(y//20))

def progressive(start,end):
    return zone(start) is not None and zone(end) is not None and end[0]-start[0]>=15 and end[0]>=60

def empty_stats():return {key:0 for key in FIELDS}

def per90(value,minutes):return value*90/minutes if minutes>0 else None

def percentile(value,peers):
    if not peers:return None
    # Midrank: ties share rank; a constant cohort sits at the 50th percentile.
    return 100*(sum(x<value for x in peers)+.5*sum(x==value for x in peers))/len(peers)

def analyze_match(meta,events,lineups):
    lengths=period_lengths(events);duration=sum(lengths.values())/60
    if len({e['id'] for e in events})!=len(events):raise ValueError('Duplicate event IDs')
    players={};audits=[];intervals,red_loss,role_minutes=playing_intervals(events,lengths)
    for team in lineups:
        expected=11*duration-red_loss[team['team_id']]/60;actual=0
        for p in team['lineup']:
            if p['player_id'] not in intervals:continue
            minutes=sum(b-a for a,b in intervals[p['player_id']])/60;roles=dict(role_minutes[p['player_id']])
            actual+=minutes
            if minutes<=0:continue
            players[p['player_id']]={'id':p['player_id'],'name':p.get('player_nickname') or p['player_name'],
                'full_name':p['player_name'],'team':team['team_name'],'team_id':team['team_id'],'minutes':minutes,'roles':roles,
                'stats':empty_stats(),'shot_zones':{},'pass_flows':{}}
        audits.append({'team':team['team_name'],'observed_minutes':actual,'expected_minutes':expected,'difference_seconds':(actual-expected)*60})
    valid=[e for e in events if e['period']<=4];shots={e['id']:e for e in valid if e['type']['name']=='Shot'}
    quality=Counter();own_goals=Counter()
    for e in valid:
        kind=e['type']['name']
        if kind=='Own Goal Against':own_goals[e['team']['name']]+=1
        pid=e.get('player',{}).get('id')
        if pid not in players:
            if pid and kind not in ('Bad Behaviour','Player Off','Player On'):quality['events_without_playing_minutes']+=1
            continue
        p=players[pid];s=p['stats']
        if kind=='Shot':
            shot=e['shot'];xg=shot.get('statsbomb_xg')
            if xg is None or not math.isfinite(xg) or not 0<=xg<=1:raise ValueError('Invalid xG')
            goal=shot['outcome']['name']=='Goal';penalty=shot['type']['name']=='Penalty'
            s['shots']+=1;s['goals']+=int(goal);s['xg']+=xg
            if not penalty:s['np_shots']+=1;s['np_goals']+=int(goal);s['npxg']+=xg
            z=zone(e.get('location'))
            if z is not None:
                b=p['shot_zones'].setdefault(str(z),{'shots':0,'goals':0,'xg':0,'penalties':0});b['shots']+=1;b['goals']+=int(goal);b['xg']+=xg;b['penalties']+=int(penalty)
            else:quality['shots_without_location']+=1
        elif kind=='Pass':
            pas=e['pass'];complete='outcome' not in pas;s['passes']+=1;s['completed_passes']+=int(complete)
            if complete and progressive(e.get('location'),pas.get('end_location')):s['progressive_passes']+=1
            sid=pas.get('assisted_shot_id')
            if sid:
                shot=shots.get(sid)
                if shot and shot['team']['id']==e['team']['id']:
                    s['key_passes']+=1;s['xa']+=shot['shot']['statsbomb_xg']
                else:quality['unresolved_shot_assists']+=1
            a,b=zone(e.get('location')),zone(pas.get('end_location'))
            if complete and a is not None and b is not None:
                key=f'{a}:{b}';p['pass_flows'][key]=p['pass_flows'].get(key,0)+1
        elif kind=='Dribble':s['dribbles']+=1;s['completed_dribbles']+=int(e['dribble']['outcome']['name']=='Complete')
        elif kind=='Pressure':s['pressures']+=1
        elif kind=='Ball Recovery' and not e.get('ball_recovery',{}).get('recovery_failure',False):s['recoveries']+=1
    for a in audits:
        if abs(a['difference_seconds'])>3:quality['minutes_audit_mismatch']+=1
    home,away=meta['home_team']['home_team_name'],meta['away_team']['away_team_name']
    goals={t:sum(p['stats']['goals'] for p in players.values() if p['team']==t)+own_goals[other] for t,other in ((home,away),(away,home))}
    if goals[home]!=meta['home_score'] or goals[away]!=meta['away_score']:raise ValueError('Goals do not reconcile with match score')
    return {'id':meta['match_id'],'date':meta['match_date'],'stage':meta['competition_stage']['name'],
            'home':home,'away':away,'home_score':meta['home_score'],'away_score':meta['away_score'],'duration':duration,
            'period_minutes':{str(k):v/60 for k,v in lengths.items()},'players':list(players.values()),'minutes_audit':audits,
            'quality':dict(quality),'event_count':len(events),'shootout_events_excluded':sum(e['period']==5 for e in events)}

def aggregate(matches):
    players={}
    for match in matches:
        for p in match['players']:
            a=players.setdefault(p['id'],{'id':p['id'],'name':p['name'],'team':p['team'],'minutes':0,'appearances':0,'roles':Counter(),'stats':empty_stats()})
            a['minutes']+=p['minutes'];a['appearances']+=1;a['roles'].update(p['roles'])
            for key in FIELDS:a['stats'][key]+=p['stats'][key]
    for p in players.values():
        p['role']=max(p['roles'],key=p['roles'].get);p['per90']={k:per90(v,p['minutes']) for k,v in p['stats'].items()}
        p['pass_completion']=p['stats']['completed_passes']/p['stats']['passes'] if p['stats']['passes'] else None
    return list(players.values())

def build(root='data',out='reports/results.json'):
    root=Path(root);manifest,meta=load(root);matches=[]
    for m in sorted(meta,key=lambda m:(m['match_date'],m['match_id'])):
        match=analyze_match(m,json.loads((root/f'events/{m["match_id"]}.json').read_bytes()),json.loads((root/f'lineups/{m["match_id"]}.json').read_bytes()))
        matches.append(match);print(m['match_id'],match['quality'],flush=True)
    players=aggregate(matches)
    result={'project':'Touchline','source':'StatsBomb Open Data','revision':manifest['revision'],'selection':manifest['selection'],
            'provenance':manifest['files'],'matches':matches,'players':players,
            'summary':{'matches':len(matches),'players':len(players),'teams':len({p['team'] for p in players}),'shots':sum(p['stats']['shots'] for p in players),
                       'goals':sum(p['stats']['goals'] for p in players),'xg':sum(p['stats']['xg'] for p in players),
                       'source_events':sum(m['event_count'] for m in matches),'shootout_events_excluded':sum(m['shootout_events_excluded'] for m in matches)}}
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    print(json.dumps(result['summary'],indent=2));print('Minute audit max error seconds:',max(abs(a['difference_seconds']) for m in matches for a in m['minutes_audit']))
