.PHONY: style quality

# make sure to test the local checkout in scripts and not the pre-installed one (don't use quotes!)
# export PYTHONPATH = src

check_dirs := scripts

style:
	python -m black --line-length 119 --target-version py310 $(check_dirs)
	python -m isort $(check_dirs) --profile black

quality:
	python -m flake8 --max-line-length 119 $(check_dirs)