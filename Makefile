.PHONY: run deploy

run: main.py config.py
	pipenv run uvicorn main:app --reload

deploy: docker-compose.yml
	sudo docker-compose up