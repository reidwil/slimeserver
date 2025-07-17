# Makefile for FIT Viewer Docker app

IMAGE_NAME=fit-viewer
CONTAINER_NAME=fit-viewer-app
PORT=8501
ACTIVITIES_DIR=$(CURDIR)/activities

.PHONY: build start stop logs

build:
	docker build -t $(IMAGE_NAME) .

start: build
	docker run -d --rm \
	  --name $(CONTAINER_NAME) \
	  -p $(PORT):8501 \
	  -v $(ACTIVITIES_DIR):/app/activities \
	  $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME) || true

logs:
	docker logs -f $(CONTAINER_NAME) 