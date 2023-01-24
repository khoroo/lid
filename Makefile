.PHONY: lint clean

lint:
	black --line-length 99 lid.py
	isort lid.py

clean:
	rm -rf __pycache__ build lid.egg-info
