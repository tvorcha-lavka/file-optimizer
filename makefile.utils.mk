# --- Functions --------------------------------------------------------------------------------------------------------

define LOG_HEADER_WINDOWS
  @powershell -Command '\
	$$s=" $(1) "; $$d="="; \
	$$w=$(TERMINAL_WIDTH); \
	$$l=[math]::Floor(($$w - $$s.Length) / 2); \
	$$r=$$w - $$s.Length - $$l; \
	Write-Host ""; \
	Write-Host ($$($$d * $$l) + $$s + $$($$d * $$r)); \
	Write-Host ""; \
  '
endef
define LOG_HEADER_UNIX
  @bash -c '\
    s=" $(1) "; d="="; \
    w=$(TERMINAL_WIDTH); \
    l=$$(( (w - $${#s}) / 2 )); \
    r=$$(( w - $${#s} - l )); \
    echo ""; \
    printf "%*s" $$l "" | tr " " $$d; \
    printf "%s" "$$s"; printf "%*s\n" $$r "" | tr " " $$d; \
    echo ""; \
  '
endef

# --- Variables --------------------------------------------------------------------------------------------------------

# Define shell type
ifeq ($(OS), Windows_NT)
  IS_GIT_BASH := $(findstring MINGW,$(shell uname -s 2>&1))

  ifneq ($(IS_GIT_BASH),)
    SHELL_TYPE := Unix
  else
    SHELL_TYPE := Windows
  endif
else
  SHELL_TYPE := Unix
endif

# Define shell variables
ifeq ($(SHELL_TYPE),Windows)
  TERMINAL_WIDTH := $(shell powershell -Command "[Console]::WindowWidth")
  LOG_HEADER = $(LOG_HEADER_WINDOWS)
  DEV_NULL := >nul 2>&1
else
  TERMINAL_WIDTH := $(shell tput cols)
  LOG_HEADER = $(LOG_HEADER_UNIX)
  DEV_NULL := >/dev/null 2>&1
endif

# --- Variable Usage ---------------------------------------------------------------------------------------------------

# LOG_HEADER: $(call LOG_HEADER,<name-of-process>)
#    example: $(call LOG_HEADER,pytest with coverage)		returns: ====== pytest with coverage ======
#    example: $(call LOG_HEADER,flake8) 					returns: ============= flake8 =============
