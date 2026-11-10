# SPDX-License-Identifier: MIT
"""Offline display reconstruction from frozen summaries; never runs a scientific model."""
from pathlib import Path
import argparse,csv,hashlib,json,sys,platform,unittest,io,math,stat
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reject_link(path):
 for component in (path, *path.parents):
  try:
   status = component.lstat()
  except FileNotFoundError:
   continue
  if stat.S_ISLNK(status.st_mode) or getattr(status, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
   raise ValueError('Linked input path refused: '+component.name)

def read(p):
 reject_link(p)
 if not p.is_file():raise ValueError('Missing required input: '+p.name)
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(p,rr):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def enforce_offline():
 def deny(event, args):
  if event.startswith('socket.') or event in ('subprocess.Popen','os.system','os.posix_spawn'):
   raise PermissionError('OFFLINE_POLICY_BLOCKED: '+event)
 sys.addaudithook(deny)

def run():
 parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=Path(__file__).resolve().parents[1]/'data');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 if args.output.exists() or args.output.is_symlink():raise ValueError('Output directory already exists; choose a new directory to protect prior files')
 manifest=read(args.input/'INPUT_HASHES.csv');dictionary=read(args.input/'DATA_DICTIONARY.csv');datasets={}
 if sha(args.input/'INPUT_HASHES.csv')!='6d730d9c600cecdd4455aa7fba8c166f3cadeded884ee4e3b30c7d29df90a1bd':raise ValueError('Frozen input manifest identity mismatch')
 if sha(args.input/'DATA_DICTIONARY.csv')!='f8e5ab84bd9b95976f08ea26d05af71819f9d84d810e191ca6bf0338e6efb841':raise ValueError('Data dictionary identity mismatch')
 contract_path=Path(__file__).with_name('input_contract.json')
 reject_link(contract_path)
 if sha(contract_path)!='49e23ed1d0393eddaac48f103f72454d7e1bf5fad0a493045a8d0f3be908c6b2':raise ValueError('Input contract identity mismatch')
 contract=json.loads(contract_path.read_text(encoding='utf-8'))
 if len(manifest)!=17 or {r['file'] for r in manifest}!=set(contract):raise ValueError('Missing, duplicate or unknown manifest key')
 if not dictionary or not {'file','field','storage','meaning','missing','precision'}.issubset(dictionary[0]):raise ValueError('Data dictionary has missing schema fields')
 declared={(r['file'],r['field']) for r in dictionary}
 if len(declared)!=len(dictionary):raise ValueError('Duplicate data-dictionary field definitions')
 for r in manifest:
  p=args.input/r['file']
  if p.parent.resolve()!=args.input.resolve():raise ValueError('Unsafe input path')
  reject_link(p)
  if not p.is_file():raise ValueError('Missing required input: '+p.name)
  if sha(p)!=r['sha256'] or p.stat().st_size!=int(r['bytes']):raise ValueError('Input identity mismatch: '+p.name)
  datasets[r['file']]=read(p)
  if not datasets[r['file']]:raise ValueError('Empty required summary table: '+p.name)
  unknown=[k for k in datasets[r['file']][0] if (r['file'],k) not in declared]
  if unknown:raise ValueError('Missing dictionary definition in '+p.name+': '+','.join(unknown))
 # Metadata and row-key safeguards; no scientific recomputation.
 if declared!={(n,k) for n,c in contract.items() for k in c['fields']}:raise ValueError('Dictionary field coverage mismatch')
 for n,rows in datasets.items():
  c=contract[n]
  if list(rows[0])!=c['fields'] or len(rows)!=c['rows']:raise ValueError('Schema/row count mismatch: '+n)
  keys=[tuple(r[k] for k in c['keys']) for r in rows]
  if len(keys)!=len(set(keys)):raise ValueError('Duplicate key: '+n)
 # Check schema and explicit semantics before creating outputs.
 for r in datasets['retention.csv']:
  if not 0<=float(r['S'])<=1 or r['age'] not in ['5','10']:raise ValueError('Invalid frozen retention value or age')
 for r in datasets['hazard_coefficients.csv']:
  if r['beta'] not in ['','NA'] and not math.isfinite(float(r['beta'])):raise ValueError('Invalid coefficient')
 try:
  import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 except ImportError as exc:raise ValueError('Plotting requires the recorded matplotlib/numpy environment; no automatic installation is attempted') from exc
 matplotlib.rcParams.update({'svg.hashsalt':'J6P_R1','font.family':'DejaVu Sans','font.size':10})
 args.output.mkdir(parents=True)
 import test_event_rules
 stream=io.StringIO();res=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_event_rules));(args.output/'RULE_TEST_LOG.txt').write_text(stream.getvalue(),encoding='utf-8')
 if not res.wasSuccessful():raise ValueError('Synthetic rule tests failed')
 rr=[dict(estimand=r['estimand'],pathway=r['pathway'],age=r['age'],retention_percent=format(float(r['S'])*100,'.6f'),initial_area_km2=r['initial_area_km2'],area_unit=r['initial_area_unit'],risk_area_km2=r['Y_km2']) for r in datasets['retention.csv']]
 save(args.output/'RETENTION_DISPLAY.csv',rr)
 save(args.output/'CROSS_PRODUCT_DISPLAY.csv',datasets['cross_product.csv'])
 save(args.output/'SAMPLE_FLOW_DISPLAY.csv',datasets['hazard_flow.csv'])
 save(args.output/'RZSM_POINT_AND_NA_DISPLAY.csv',datasets['hazard_coefficients.csv'])
 for name in ['main_data_sources','main_design_windows','main_postexit','occupancy','reappearance','reexit']:
  cells=datasets[name+'.csv'];nr=1+max(int(r['row']) for r in cells);nc=1+max(int(r['column']) for r in cells);matrix=[['']*nc for _ in range(nr)]
  for r in cells:matrix[int(r['row'])][int(r['column'])]=r['display_value']
  with (args.output/(name.upper()+'_DISPLAY.csv')).open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(matrix)
 fig,axs=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
 for ax,path,title in zip(axs,['C_to_G','B_to_G'],['C to G','B to G']):
  selected=[r for r in rr if r['pathway']==path and r['age']=='10'];ax.barh([r['estimand'].replace('B-','') for r in selected],[float(r['retention_percent']) for r in selected],color='#236c94');ax.set_xlim(0,100);ax.set_xlabel('Ten-year retention (%)');ax.set_title(title)
 fig.suptitle('RETENTION_FIRST_LOCATION | frozen estimates; populations differ',fontsize=11);fig.savefig(args.output/'RETENTION_FIRST_LOCATION.svg',metadata={'Date':None});fig.savefig(args.output/'RETENTION_FIRST_LOCATION.png',dpi=150);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
 for ax,path,title in zip(axs,['cropland_to_grassland','barren_to_grassland'],['C to G','B to G']):
  for pop,color,style in [('ORIGINAL','#777777','--'),('STRICT','#b45f20','-')]:
   s=sorted([r for r in datasets['s11_points.csv'] if r['pathway']==path and r['population']==pop],key=lambda r:int(r['relative_year']));ax.plot([int(r['relative_year']) for r in s],[float(r['adjusted']) for r in s],style,marker='o',color=color,label=pop)
  ax.axhline(0,color='black',lw=.6);ax.set_title(title);ax.set_xlabel('Relative year');ax.set_ylabel('Adjusted RZSM difference (m³/m³)');ax.legend(fontsize=8)
 fig.suptitle('S11_RZSM_POINTS | selected populations; no new intervals',fontsize=11);fig.savefig(args.output/'S11_RZSM_POINTS.svg',metadata={'Date':None});fig.savefig(args.output/'S11_RZSM_POINTS.png',dpi=150);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(9,4),layout='constrained')
 for ax,path in zip(axs,['C_to_G','B_to_G']):
  for product,color in [('CLCD','#2166ac'),('GLC','#b35806')]:
   s=sorted([r for r in datasets['cross_product.csv'] if r['pathway']==path and r['product'].startswith(product)],key=lambda r:int(r['horizon']));ax.plot([int(r['horizon']) for r in s],[100*float(r['estimate']) for r in s],'o-',label=product,color=color)
  ax.set_title(path);ax.set_xlabel('Age (years)');ax.set_ylabel('Frozen retention (%)');ax.set_ylim(0,100);ax.legend()
 fig.suptitle('CROSS_PRODUCT_COMMON_SUPPORT | agreement is not accuracy',fontsize=11);fig.savefig(args.output/'CROSS_PRODUCT_COMMON_SUPPORT.svg',metadata={'Date':None});fig.savefig(args.output/'CROSS_PRODUCT_COMMON_SUPPORT.png',dpi=150);plt.close(fig)
 outputs=[{'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(args.output.iterdir()) if p.is_file()]
 report=dict(status='PASS',input_files=len(manifest),dictionary_fields=len(dictionary),synthetic_tests=res.testsRun,failures=0,python=platform.python_version(),matplotlib=matplotlib.__version__,scope='R1_OUTPUT and R2_RULES; not historical or raw end-to-end reproduction',outputs=outputs)
 (args.output/'READBACK_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'status':'PASS','tests':res.testsRun,'outputs':len(outputs)}))
if __name__=='__main__':
 try:
  enforce_offline()
  run()
 except (ValueError,KeyError) as exc:print('ERROR: '+str(exc),file=sys.stderr);sys.exit(2)
