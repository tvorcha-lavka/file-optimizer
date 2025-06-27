#!/bin/bash

source /scripts/logging.sh

BASE_FLAGS=(
  "--pool=prefork"
  "--concurrency=2"
  "--queues=file-optimizer.queue"
  "--max-tasks-per-child=20"
  "--hostname=file-optimizer@%h"
  "--loglevel=info"
  "--without-mingle"
  "--without-gossip"
)

start() {
  if [[ "$ENV_STATE" == "production" || "$ENV_STATE" == "staging" ]]; then
    log_message INFO "Starting optimize queue in ${GREEN}$ENV_STATE mode${NO_COLOR}..."
  else
    log_message WARNING "Starting optimize queue in ${YELLOW}development mode${NO_COLOR}..."
  fi
  celery -A main worker "${BASE_FLAGS[@]}"
}

start
