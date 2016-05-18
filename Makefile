.PHONY: test

test: shpy.py
	python tests.py && git commit -q -m "Pass tests" --allow-empty

shpy.py:
	curl -O https://raw.githubusercontent.com/AlexanderWingard/shpy/prototype/shpy.py
