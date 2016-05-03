.PHONY: test

test: shpy.py
	python tests.py

shpy.py:
	curl -O https://raw.githubusercontent.com/AlexanderWingard/shpy/prototype/shpy.py
