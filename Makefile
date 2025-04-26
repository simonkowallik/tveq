
setup:
	pip3 install poetry
	poetry install --no-interaction --no-root --no-ansi
	poetry self add poetry-plugin-export

update:
	poetry update
	poetry export -f requirements.txt -o requirements.txt

start:
	streamlit run streamlit_app.py --server.port 8888

run: start
