.PHONY: setup data test test-encoder test-metta test-1d clean

VENV ?= .venv
PY ?= python3

setup:
	$(PY) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

# Fetches all datasets used by the project into data/. Shallow clones
# only; nothing here is committed to the repo (see .gitignore).
data:
	mkdir -p data
	test -d data/arc-agi || git clone --depth 1 https://github.com/fchollet/ARC-AGI.git data/arc-agi
	test -d data/ConceptARC || git clone --depth 1 https://github.com/victorvikram/ConceptARC.git data/ConceptARC
	test -d data/mini-arc-real || git clone --depth 1 https://github.com/KSB21ST/MINI-ARC.git data/mini-arc-real
	test -d data/re-arc || git clone --depth 1 https://github.com/michaelhodel/re-arc.git data/re-arc
	@echo "NOTE: Mini-ARC is at KSB21ST/MINI-ARC (Kim et al. 2022), NOT"
	@echo "pfletcherhill/mini-arc, which was miscited in the Milestone 1"
	@echo "plan's footnote [^5] - see docs/decisions.md, D3."
	@echo "NOTE: 1D-ARC (optozorax/arc_1d) is a Rust generator, not a data"
	@echo "dump; see docs/decisions.md, D5, for why it is not fetched here."

test:
	PYTHONPATH=python $(PY) -m pytest tests/ -v

test-encoder:
	PYTHONPATH=python $(PY) -m pytest tests/test_encoder.py -v

test-metta:
	PYTHONPATH=python $(PY) -m pytest tests/test_metta_integration.py -v

test-1d:
	PYTHONPATH=python $(PY) -m pytest tests/test_1d_arc.py -v

# Exports every task in every fetched dataset to a human-readable .metta
# file (one per task) under exports/metta_corpus/. Regenerable from
# source; not committed to git. See python/export_corpus.py.
export:
	PYTHONPATH=python $(PY) python/export_corpus.py --dataset all --out-dir exports/metta_corpus
	cp exports/metta_corpus/manifest.md docs/corpus_manifest.md

# Leave-one-task-out cross-validation sweep over ConceptARC's
# InsideOutside group (Sprint B validation). See
# python/experiment_insideoutside.py and docs/decisions.md D9.
# Output is a small, genuinely committed artifact (not a regenerable
# corpus blob), so it goes to docs/, not experiments/results/ (which is
# gitignored wholesale).
experiment-insideoutside:
	PYTHONPATH=python $(PY) python/experiment_insideoutside.py | tee docs/insideoutside_leave_one_out_sweep.txt

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf .pytest_cache
