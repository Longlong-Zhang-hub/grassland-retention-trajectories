# SPDX-License-Identifier: MIT
"""Run deterministic synthetic event-rule examples with the Python standard library."""
import argparse
import csv
from pathlib import Path

from event_rules import exact_id, first_exit, onset_kind, post_exit
from run_reproduction import enforce_offline

LABEL = 'SYNTHETIC_NOT_STUDY_DATA'
STATES = {
    '9007199254740993': (1, 3, 2, 2, 3, 3, 2, 2, 2),
    '18446744073709551615': (1, 3, 2, 2, 2, 2, 2, None, 2),
    '42': (1, 3, 3, None, 3, 2, 2, 3, 3),
}
INPUT_FIELDS = ['provenance', 'case_id', 'year', 'state']
OUTPUT_FIELDS = ['provenance', 'case_id', 'onset_year', 'first_exit', 'confirmation',
                 'censor', 'exit_status', 'return_year', 'H3_eligible', 'H3_return',
                 'H5_eligible', 'H5_return', 'reexit_eligible', 'reexit']


def example_rows():
    for case_id, states in STATES.items():
        for year, state in enumerate(states, 2000):
            yield dict(provenance=LABEL, case_id=case_id, year=str(year),
                       state='NA' if state is None else str(state))


def write_csv(path, fields, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def display(value):
    if value is None:
        return 'NA'
    if isinstance(value, bool):
        return int(value)
    return value


def main():
    enforce_offline()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error('choose a new output directory')
    fixture = Path(__file__).resolve().parents[1] / 'examples/synthetic/SYNTHETIC_NOT_STUDY_DATA.csv'
    with fixture.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != INPUT_FIELDS or list(reader) != list(example_rows()):
            parser.error('synthetic fixture identity differs from the generated cases')
    cases = {}
    for row in example_rows():
        case_id = exact_id(row['case_id'])
        cases.setdefault(case_id, {})[int(row['year'])] = None if row['state'] == 'NA' else int(row['state'])
    results = []
    for case_id, states in cases.items():
        onset = onset_kind(2000, states[2000], 2001, states[2001])['t0']
        exit_info = first_exit(states, onset)
        post = post_exit(states, exit_info['c']) if exit_info['c'] is not None else {}
        values = [LABEL, case_id, onset, exit_info['e'], exit_info['c'], exit_info['censor'],
                  exit_info['status'], post.get('q'), post.get('H3_eligible'), post.get('H3_return'),
                  post.get('H5_eligible'), post.get('H5_return'), post.get('reexit_eligible'), post.get('reexit')]
        results.append(dict(zip(OUTPUT_FIELDS, map(display, values))))
    args.output.mkdir(parents=True, exist_ok=False)
    write_csv(args.output / fixture.name, INPUT_FIELDS, example_rows())
    write_csv(args.output / 'SYNTHETIC_EVENT_RESULTS.csv', OUTPUT_FIELDS, results)
    print(f'{LABEL}: {len(cases)} invented cases; 2 CSV files')


if __name__ == '__main__':
    main()
