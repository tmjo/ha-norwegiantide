__VERSION__ = "2022.01.2"

bump:
	bump2version --allow-dirty --current-version $(__VERSION__) patch Makefile custom_components/norwegiantide/const.py custom_components/norwegiantide/manifest.json

lint:
	isort custom_components
	black custom_components
	flake8 custom_components

install_dev:
	pip install -r requirements-dev.txt