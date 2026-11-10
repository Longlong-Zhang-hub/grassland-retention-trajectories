# Common-age retention and post-exit trajectories — software and synthetic tests

Software associated with the manuscript **Common-age retention and post-exit trajectories of mapped grassland gains in northern China**, under revision for *Ecological Indicators* (manuscript ECOLIND-64756).

**Software version:** `0.1.0-rc1`  
**Code and authorized synthetic test license:** MIT (see `LICENSE` and `LICENSE_SCOPE.md`).  
**Authors:** Longqi Zhang, Guodong Jia, Xinxiao Yu.

This repository provides three author-owned Python programs, deterministic event-rule tests, a synthetic example, and a frozen contract for selected summary displays. It **does not include** the 17 research-summary input CSVs, their private manifests, upstream remote-sensing products, or the complete data-processing and model-fitting workflow. The synthetic cases are invented and explicitly labeled `SYNTHETIC_NOT_STUDY_DATA`; passing the tests does not verify the historical study estimates.

## Run the code-only demonstrations

Python 3.10+ is sufficient for the code-only workflow (no third-party packages required):

```bash
python code/test_event_rules.py
python code/demo_synthetic.py --output synthetic_run
```

The tests cover 17 predefined event and eligibility rules. The demonstration writes two CSVs, which can be checked against `examples/synthetic/expected/`. Choose a **new** output directory each time.

## Reproduction scope

`code/run_reproduction.py` can regenerate **selected frozen aggregate display outputs** only when the separately authorized 17 byte-identical research CSVs, manifest, and dictionary are supplied. It does not rebuild annual 30-m events, model fits, spatial bootstrap distributions, prediction validation, original raster products, or all manuscript figures. See `PUBLICATION_REPRODUCIBILITY_SCOPE.md` and `QUICKSTART.md` for specifics. Research inputs remain under separate permission and source-license review.

The publication and its analytical definitions remain the authoritative sources for the study estimates; the code-only release must not be described as a full open-data reproduction package.

## Citation and licensing

For software citation, use `CITATION.cff`. A persistent repository DOI can be cited **only after** it has been assigned and verified by the archive provider. This file intentionally contains no invented DOI.

The MIT license applies only to the authorized author-owned code and synthetic materials in this release. Dependencies and third-party products retain their own licenses. See `LICENSE_SCOPE.md`, `docs/DEPENDENCY_TERMS.md`, and `docs/DATA_PRODUCT_SCOPE.md`.
