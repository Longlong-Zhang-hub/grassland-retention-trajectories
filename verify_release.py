# SPDX-License-Identifier: MIT
"""Validate ZIP members, then extract and execute the selected offline workflows."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import unicodedata
import zipfile

MANIFEST = 'SHA256SUMS.csv'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def validate_names(z):
    seen = set()
    for member in z.infolist():
        name = member.filename
        parts = name.split('/')
        if (member.is_dir() or PurePosixPath(name).is_absolute() or '\\' in name or ':' in name
                or any(p in {'', '.', '..'} or p.endswith((' ', '.')) or any(ord(c)<32 for c in p)
                       or re.fullmatch(r'(?i)(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',p)
                       for p in parts)
                or stat.S_ISLNK(member.external_attr >> 16)):
            raise ValueError(f'Unsafe ZIP member: {name}')
        key = unicodedata.normalize('NFC', name).casefold()
        if key in seen:
            raise ValueError(f'Duplicate ZIP member: {name}')
        seen.add(key)
    if any(any('/'.join(name.split('/')[:i]) in seen for i in range(1,len(name.split('/')))) for name in seen):
        raise ValueError('ZIP file and directory collision')


def verify_zip(path, extract=None):
    with zipfile.ZipFile(path) as z:
        validate_names(z)
        if z.testzip() is not None:
            raise ValueError('ZIP CRC mismatch')
        rows = list(csv.DictReader(io.StringIO(z.read(MANIFEST).decode('utf-8-sig'))))
        names = set(z.namelist())-{MANIFEST}
        if len(rows)!=len(names) or {r['file'] for r in rows}!=names:
            raise ValueError('ZIP manifest coverage mismatch')
        for row in rows:
            content=z.read(row['file'])
            if len(content)!=int(row['bytes']) or digest(content)!=row['sha256']:
                raise ValueError(f"ZIP payload identity mismatch: {row['file']}")
        members=[dict(file=i.filename,bytes=i.file_size,sha256=digest(z.read(i)),crc32=f'{i.CRC:08x}') for i in z.infolist()]
        if extract is not None:
            extract.mkdir(parents=True,exist_ok=False)
            z.extractall(extract)
    return members


def execute(cwd, args, log, expected=0, diagnostic=''):
    env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1',
         'MPLBACKEND':'Agg','MPLCONFIGDIR':str((log.parent/'mpl-cache').resolve())}
    run=subprocess.run([sys.executable,*args],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=120)
    log.write_text(f'python {args!r}\nexit={run.returncode}\n\nSTDOUT\n{run.stdout}\nSTDERR\n{run.stderr}',encoding='utf-8')
    if run.returncode!=expected or diagnostic not in run.stdout+run.stderr:
        raise RuntimeError(f'Execution differed from expectation, see {log}')
    return run


def verify_execution(path, mode, output):
    output.mkdir(parents=True,exist_ok=False)
    root=output/'extracted'; members=verify_zip(path,root)
    if mode=='code' and any(m['file'].startswith('data/') for m in members):
        raise ValueError('Code archive unexpectedly contains research input')
    candidate=root if mode=='code' else root/'candidate'
    rules=execute(candidate,['code/test_event_rules.py'],output/'rules.log',diagnostic='Ran 17 tests')
    cases=re.findall(r'^(test_\w+) .* \.\.\. ok$',rules.stderr,re.M)
    if len(set(cases))!=17:
        raise ValueError('Did not verify seventeen individual rule passes')
    result=dict(archive=path.name,mode=mode,members=len(members),rules=cases,archive_sha256=digest(path.read_bytes()))
    if mode=='code':
        demo=output/'synthetic-output'
        execute(candidate,['-S','code/demo_synthetic.py','--output',str(demo)],output/'synthetic.log',diagnostic='SYNTHETIC_NOT_STUDY_DATA: 3')
        for p in demo.iterdir():
            if p.read_bytes()!=(candidate/'examples/synthetic/expected'/p.name).read_bytes():
                raise ValueError(f'Synthetic output differs: {p.name}')
        with (demo/'SYNTHETIC_EVENT_RESULTS.csv').open(newline='',encoding='utf-8') as stream:
            a,b,c=list(csv.DictReader(stream))
        assert (a['case_id'],a['first_exit'],a['confirmation'],a['return_year'],a['reexit'])==('9007199254740993','2002','2003','2004','1')
        assert (b['case_id'],b['H3_return'],b['H5_return'])==('18446744073709551615','0','NA')
        assert c['exit_status']=='MISSING_OBSERVATION' and c['first_exit']=='NA'
        result['synthetic_outputs']={p.name:digest(p.read_bytes()) for p in demo.iterdir()}
        execute(candidate,['code/run_reproduction.py','--output',str(output/'must-not-exist')],output/'real-without-inputs.log',2,'Missing required input: INPUT_HASHES.csv')
        assert not (output/'must-not-exist').exists()
    else:
        rebuilt=output/'rebuilt'
        execute(candidate,['code/run_reproduction.py','--output',str(rebuilt)],output/'rebuild.log',diagnostic='"status": "PASS"')
        report=json.loads((rebuilt/'READBACK_REPORT.json').read_text(encoding='utf-8'))
        assert (report['input_files'],report['dictionary_fields'],report['synthetic_tests'])==(17,214,17)
        with (candidate/'EXPECTED_OUTPUT_HASHES.csv').open(encoding='utf-8-sig',newline='') as stream:
            rows=list(csv.DictReader(stream))
        assert len(rows)==16
        for row in rows:
            actual=(rebuilt/row['file']).read_bytes()
            if len(actual)!=int(row['bytes']) or digest(actual)!=row['sha256']:
                raise ValueError(f"Frozen byte mismatch: {row['file']}")
            row['actual_sha256']=digest(actual)
            row['byte_match']='PASS'
        result['outputs']=rows
        result['environment']={k:report[k] for k in ['python','matplotlib']}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('archive',type=Path)
    cli.add_argument('--mode',choices=['code','real'],required=True)
    cli.add_argument('--output',type=Path,required=True)
    args=cli.parse_args()
    print(json.dumps(verify_execution(args.archive.resolve(),args.mode,args.output.resolve()),indent=2))
