baselines:
	python -m src.autotuner.cli baselines
report:
	python -m src.autotuner.cli report
test:
	pytest -q
search:
	python -m src.autotuner.cli search --method random --budget 60 --seed 0
	python -m src.autotuner.cli search --method hillclimb --budget 60 --seed 0
	python -m src.autotuner.cli compare