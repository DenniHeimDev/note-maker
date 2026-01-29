.PHONY: venv install install-dev test run format lint

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && python -m pip install -U pip && pip install -r requirements.txt

install-dev:
	. .venv/bin/activate && python -m pip install -U pip && pip install -r requirements.txt -r requirements-dev.txt

test:
	. .venv/bin/activate && pytest -q

run:
	. .venv/bin/activate && uvicorn note_maker.server:app --reload
