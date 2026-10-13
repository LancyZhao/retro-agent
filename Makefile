.PHONY: install dev test lint run eval docker fmt

install:        ## install core only (no third-party deps needed)
	python -m pip install -e .

dev:            ## install web + redis + dev extras
	python -m pip install -e ".[web,redis,dev]"

test:           ## run the test suite
	pytest -q

lint:           ## static checks
	ruff check app tests

run:            ## start the web app (needs [web] extra)
	uvicorn app.main:app --reload

eval:           ## run the model/prompt eval harness
	python -m app.eval.run_eval

cli:            ## generate a retrospective on the CLI
	python -m app.cli --period 2026-W41

docker:         ## build + run via docker compose (app + redis)
	docker compose up --build
