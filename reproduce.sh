#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python "$base/code/test_event_rules.py"
python "$base/code/demo_synthetic.py" --output "$1"
