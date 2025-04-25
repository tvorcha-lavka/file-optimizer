#!/bin/bash

GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NO_COLOR="\033[0m"


log_message() {
  local level=$1
  local message=$2

  case $level in
    INFO)
      echo -e "${GREEN}INFO${NO_COLOR}:     ${message}"
      ;;
    WARNING)
      echo -e "${YELLOW}WARNING${NO_COLOR}:  ${message}"
      ;;
    ERROR)
      echo -e "${RED}ERROR${NO_COLOR}:    ${message}"
      ;;
    *)
      echo -e "${NO_COLOR}${message}"
      ;;
  esac
}
