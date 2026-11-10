# Running software release `0.1.0-rc1`

MIT-licensed code and synthetic tests; no research CSV inputs are distributed. Run from the extracted archive root with a new output directory name. Python 3.10.8 was tested. The first workflow needs only the standard library.

## Windows PowerShell

```powershell
python code/test_event_rules.py
python code/demo_synthetic.py --output synthetic_run
```

## Linux or macOS

```sh
python3 code/test_event_rules.py
python3 code/demo_synthetic.py --output synthetic_run
```

The tests report 17 cases. The demo writes `SYNTHETIC_NOT_STUDY_DATA.csv` and `SYNTHETIC_EVENT_RESULTS.csv`. Reference files and the synthetic dictionary are in `examples/synthetic/`.

## Real summary display workflow

```text
python code/run_reproduction.py --input approved_inputs --output real_run
```

Use `python3` if that is the platform's Python command. Place all 17 separately approved research CSVs, the matching frozen `INPUT_HASHES.csv` and the pinned `DATA_DICTIONARY.csv` in `approved_inputs`. The included `code/input_contract.json` must retain its original identity. The runner requires preinstalled Matplotlib and NumPy from `requirements-tested.txt`. Those packages are unnecessary for the synthetic workflow. The runner refuses missing or changed inputs, including synthetic substitutions. Successful real execution writes 16 frozen displays and two execution records.
