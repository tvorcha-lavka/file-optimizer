# --- Variables --------------------------------------------------------------------------------------------------------
include makefile.utils.mk
include .env

export ENV_STATE ?= development
export PROJECT_NAME ?= file-optimizer
export MAIN_PROJECT_NAME ?= tvorcha-lavka

export DOCKER_NETWORK_NAME ?= tvorcha-network
export DOCKER_VOLUME_NAME ?= tvorcha-efs

export DOCKER_DIR ?= ./docker
export DOCKER_VOLUME_PATH ?= /mnt/efs
export DOCKER_FILE_PATH ?= $(DOCKER_DIR)/Dockerfile

# Define docker variables
ifeq ($(ENV_STATE), development)
  DOCKER_IMAGE_TAG := $(PROJECT_NAME)-dev:latest
  POETRY_FLAGS := ""

  DOCKER_COMPOSE_CONFIG := \
  	--env-file .env \
	-p $(PROJECT_NAME) \
    -f $(DOCKER_DIR)/docker-compose.yml \
    -f $(DOCKER_DIR)/docker-compose.dev.yml

  DOCKER_VOLUME := $(DOCKER_VOLUME_NAME)
else
  DOCKER_IMAGE_TAG := $(PROJECT_NAME):latest
  POETRY_FLAGS := "--only main"

  DOCKER_COMPOSE_CONFIG := \
  	--env-file .env \
	-p $(PROJECT_NAME) \
    -f $(DOCKER_DIR)/docker-compose.yml

  DOCKER_VOLUME := $(DOCKER_VOLUME_NAME) \
    --opt device=$(DOCKER_VOLUME_PATH) \
    --opt type=none \
    --opt o=bind \
    --driver local
endif

# Define additional docker variables
DOCKER_RABBITMQ_COMPOSE_CONFIG := -f $(DOCKER_DIR)/docker-compose.rabbitmq.yml -p $(MAIN_PROJECT_NAME)
DOCKER_TESTING_COMPOSE_CONFIG := -f $(DOCKER_DIR)/docker-compose.test.yml -p pytest run --rm test-runner pytest

# Docker health check
ifeq ($(SHELL_TYPE),Windows)
  IS_RUNNING = inspect -f "{{.State.Running}}" $(1) 2>nul | findstr true >nul
  HEALTH_CHECK = inspect -f "{{.State.Health.Status}}" $(1) 2>nul | findstr healthy >nul
  AWAIT_FOR_SERVICE = \
    echo Waiting for $(1) to be ready... && for /l %%i in (1, 1, 9999) do ( \
      docker $(HEALTH_CHECK) && echo $(1) is ready! && exit /b 0 || timeout /t 2 >nul \
    )
else
  IS_RUNNING = inspect -f "{{.State.Running}}" $(1) 2>/dev/null | grep -q true
  HEALTH_CHECK = inspect -f "{{.State.Health.Status}}" $(1) 2>/dev/null | grep -q healthy
  AWAIT_FOR_SERVICE = \
    echo Waiting for $(1) to be ready... && for i in {1..9999}; do \
      docker $(HEALTH_CHECK) && { echo $(1) is ready!; exit 0; } || sleep 2; \
    done
endif

# --- Docker -----------------------------------------------------------------------------------------------------------
.PHONY: build rebuild destroy network volume check-rabbitmq up stop down down-v logs

rebuild: down destroy build

build:
	$(call LOG_HEADER,build an image: $(DOCKER_IMAGE_TAG))
	@docker build \
	--target base \
	--tag $(DOCKER_IMAGE_TAG) \
	--file $(DOCKER_FILE_PATH) \
	--build-arg POETRY_FLAGS=$(POETRY_FLAGS) .
	$(call LOG_HEADER,the image $(DOCKER_IMAGE_TAG) has been created!)

destroy:
	@docker rmi -f $(DOCKER_IMAGE_TAG) $(DEV_NULL)
	$(call LOG_HEADER,image $(DOCKER_IMAGE_TAG) has been destroyed!)

network:
	@docker network inspect $(DOCKER_NETWORK_NAME) $(DEV_NULL) || ( \
		echo Creating network: $(DOCKER_NETWORK_NAME) && \
		docker network create --driver bridge $(DOCKER_NETWORK_NAME) $(DEV_NULL) && \
		echo Network has been created! \
	)

volume:
	@docker volume inspect $(DOCKER_VOLUME_NAME) $(DEV_NULL) || ( \
		echo Mount volume: $(DOCKER_VOLUME_NAME) && \
		docker volume create $(DOCKER_VOLUME) $(DEV_NULL) && \
		echo Volume has been mounted! \
	)

check-rabbitmq:
	@docker $(call IS_RUNNING,rabbitmq) || ( \
		echo Starting rabbitmq... && \
		docker compose $(DOCKER_RABBITMQ_COMPOSE_CONFIG) up -d $(DEV_NULL) && \
		$(call AWAIT_FOR_SERVICE,rabbitmq) \
	)

up: network volume check-rabbitmq
	$(call LOG_HEADER,starting $(PROJECT_NAME) [$(ENV_STATE)])
	@docker compose $(DOCKER_COMPOSE_CONFIG) up -d
	$(call LOG_HEADER,$(PROJECT_NAME) has been started!)

stop:
	$(call LOG_HEADER,stopping $(PROJECT_NAME))
	@docker compose $(DOCKER_COMPOSE_CONFIG) stop
	$(call LOG_HEADER,$(PROJECT_NAME) has been stopped!)

down:
	$(call LOG_HEADER,shutting down $(PROJECT_NAME))
	@docker compose $(DOCKER_COMPOSE_CONFIG) down $(DEV_NULL)
	$(call LOG_HEADER,$(PROJECT_NAME) has been shut down!)

down-v:
	$(call LOG_HEADER,shutting down $(PROJECT_NAME) and removing volumes)
	@docker compose $(DOCKER_COMPOSE_CONFIG) down -v $(DEV_NULL)
	$(call LOG_HEADER,$(PROJECT_NAME) has been shut down!)

logs:
	$(call LOG_HEADER,$(PROJECT_NAME) logs)
	@docker compose $(DOCKER_COMPOSE_CONFIG) logs -f

# --- Code Linters -----------------------------------------------------------------------------------------------------
.PHONY: lint flake8

lint: flake8

flake8:
	$(call LOG_HEADER,flake8)
	@poetry run flake8 --toml-config=pyproject.toml .
	@echo All done! ✨ 🍰 ✨

# --- Code Formatters --------------------------------------------------------------------------------------------------
.PHONY: reformat isort black

reformat: isort black

isort:
	$(call LOG_HEADER,isort)
	@poetry run isort --settings=pyproject.toml .

black:
	$(call LOG_HEADER,black)
	@poetry run black --config=pyproject.toml .

# --- Type Checking ----------------------------------------------------------------------------------------------------
.PHONY: mypy

mypy:
	$(call LOG_HEADER,mypy)
	@poetry run mypy --config-file=pyproject.toml .

# --- Pytest -----------------------------------------------------------------------------------------------------------
.PHONY: pytest pytest-cov

pytest:
	$(call LOG_HEADER,pytest)
	@docker compose $(DOCKER_TESTING_COMPOSE_CONFIG)

pytest-cov:
	$(call LOG_HEADER,pytest with coverage)
	@docker compose $(DOCKER_TESTING_COMPOSE_CONFIG) -m "not (xfail or skip)" --cov

# --- Code Checking ----------------------------------------------------------------------------------------------------
.PHONY: check

check:
	@make -s reformat lint mypy pytest
