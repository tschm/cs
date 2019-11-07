#!make
PROJECT_VERSION := 0.4

SHELL := /bin/bash
IMAGE := tschm/cs

# needed to get the ${PORT} environment variable
include .env
export

.PHONY: help build jupyter tag hub slides clean


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
	echo "http://localhost:${PORT}"
	docker-compose up jupyter

tag:
	git tag -a ${PROJECT_VERSION} -m "new tag"
	git push --tags

hub: tag
	docker build -f binder/Dockerfile --tag ${IMAGE}:latest --no-cache .
	docker push ${IMAGE}:latest
	docker tag ${IMAGE}:latest ${IMAGE}:${PROJECT_VERSION}
	docker push ${IMAGE}:${PROJECT_VERSION}
	docker rmi -f ${IMAGE}:${PROJECT_VERSION}

slides:
	docker-compose up -d
	python slides.py

clean:
	docker-compose down -v --rmi all --remove-orphans
