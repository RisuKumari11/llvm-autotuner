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
llm:
	python -m src.autotuner.cli llm-search \
		--budget 60 \
		--backend ollama \
		--temperature 0.8
smoke:
	python -m src.autotuner.cli baselines
	python -m src.autotuner.cli search --method hillclimb --budget 8 --seed 0
	python -m src.autotuner.cli compare		
ablations:
	PYTHONPATH=. python scripts/ablation_table.py	