# SPDX-License-Identifier: MIT
"""Current transparent rule demonstration. SYNTHETIC ONLY, not a historical producer.
Input states: integers by observed calendar year; None is unavailable, never non-target.
No raster reading, model fitting, KM estimation or real-data event extraction.
"""
def onset_kind(previous_year,previous_state,year,state,source=1,target=3):
 if previous_state!=source or state!=target:return None
 if year==previous_year+1:return {'kind':'EXACT','t0':year}
 if (previous_year,year)==(1985,1990):return {'kind':'INTERVAL','left':1985,'right':1990,'t0':None}
 return {'kind':'UNSUPPORTED_GAP','t0':None}

def first_exit(states,t0,target=3):
 if states.get(t0)!=target:raise ValueError('Exact onset must have observed target class')
 last=t0;last_target=t0;excursions=[]
 for y in range(t0+1,max(states)+1):
  s=states.get(y)
  if s is None:return dict(e=None,c=None,censor=last,status='MISSING_OBSERVATION',excursions=excursions)
  if s!=target:
   next_state=states.get(y+1)
   if next_state is not None and next_state!=target:return dict(e=y,c=y+1,censor=None,status='CONFIRMED_EXIT',excursions=excursions)
   if y==max(states):return dict(e=None,c=None,censor=last_target,status='TERMINAL_UNCONFIRMED',excursions=excursions)
   excursions.append(y)
  else:last_target=y
  last=y
 return dict(e=None,c=None,censor=last,status='RIGHT_CENSORED',excursions=excursions)

def post_exit(states,c,target=3):
 if states.get(c) is None or states.get(c-1) is None or states[c]==target or states[c-1]==target:raise ValueError('c must confirm two observed non-target years')
 q=next((y for y in sorted(states) if y>c and states[y]==target),None)
 out={'q':q}
 for h in (3,5):
  eligible=all(states.get(y) is not None for y in range(c+1,c+h+1))
  out['H'+str(h)+'_eligible']=eligible;out['H'+str(h)+'_return']=any(states[y]==target for y in range(c+1,c+h+1)) if eligible else None
 eligible=q is not None and all(states.get(y) is not None for y in range(q+1,q+5))
 out['reexit_eligible']=eligible
 out['reexit']=any(states[y]!=target and states[y+1]!=target for y in range(q+1,q+4)) if eligible else None
 return out

def select_global_first(records):
 """Selection precedes exact-onset restriction; preserve an interval-first identity."""
 if not records:return None
 first=min(records,key=lambda r:r['observed_year'])
 return first if first['kind']=='EXACT' else None

def exact_id(value):
 if not isinstance(value,str) or not value.isdigit():raise ValueError('IDs must be decimal strings; floating-point IDs are forbidden')
 n=int(value)
 if not 0<=n<2**64:raise ValueError('ID outside uint64 range')
 return str(n)
