.PHONY: install lint clean

install:
	pip install -r requirements.txt

lint:
	black --line-length 99 lid.py
	isort lid.py

clean:
	rm -rf __pycache__ build lid.egg-info
