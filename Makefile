#!make
PROJECT_VERSION := 0.9.5

SHELL := /bin/bash
IMAGE := tschm/cs


.PHONY: help build jupyter jupyterlab tag clean-notebooks


.DEFAULT: help

help:
	@echo "make build"
	@echo "       Build the docker image."
	@echo "make jupyter"
	@echo "       Start the Jupyter server."
	@echo "make tag"
	@echo "       Make a tag on Github."
	@echo "make hub"
	@echo "       Push Docker Image to DockerHub."


build:
	docker-compose build jupyter

jupyter: build
	echo "http://localhost:8888"
	docker-compose up jupyter

jupyterlab: build
	echo "http://localhost:8888/lab"
	docker-compose up jupyter

# Any tag will automatically trigger the construction of a docker image and a push to dockerhub
# Github actions
tag:
	git tag -a ${PROJECT_VERSION} -m "new tag"
	git push --tags

clean-notebooks:
	docker-compose exec jupyter jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace **/*.ipynb