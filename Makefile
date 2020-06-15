#!make
PROJECT_VERSION := 0.7.1

SHELL := /bin/bash
IMAGE := tschm/cs


.PHONY: help build jupyter tag hub slides clean clean-notebooks


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
	echo "http://localhost:8822"
	docker-compose up jupyter

jupyterlab: build
	echo "http://localhost:8822/lab"
	docker-compose up jupyter

tag:
	git tag -a ${PROJECT_VERSION} -m "new tag"
	git push --tags

clean-notebooks:
	docker-compose exec jupyter jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace **/*.ipynb