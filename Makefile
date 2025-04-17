RESET = \033[0m
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
CYAN = \033[36m

VENV_DIR = .venv_batch
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
REQUIREMENTS = selenium beautifulsoup4 requests Pillow
SCRIPT = single_card_scraper.py

TXT =

all: venv install

venv:
	@echo "$(CYAN)🐍 Creating virtual environment...$(RESET)"
	@python3 -m venv $(VENV_DIR)

install: venv
	@echo "$(YELLOW)📦 Installing dependencies...$(RESET)"
	@$(PIP) install --upgrade pip > /dev/null
	@$(PIP) install $(REQUIREMENTS) > /dev/null
	@echo "$(GREEN)✅ Environment ready!$(RESET)"

run: all
	@if [ -z "$(TXT)" ]; then 		echo "$(RED)❌ Missing TXT file. Usage: make run TXT=cards.txt$(RESET)"; 		exit 1; 	fi
	@echo "$(BLUE)▶️ Running script with TXT: $(TXT)$(RESET)"
	@$(PYTHON) $(SCRIPT) "$(TXT)"

clean:
	@rm -rf $(VENV_DIR)
	@echo "$(RED)🧼 Environment removed: $(VENV_DIR)$(RESET)"

re: clean all

help:
	@echo "$(CYAN)🛠 Commands available:$(RESET)\n"
	@echo "$(CYAN)make all$(RESET) - Setup environment"
	@echo "$(CYAN)make run TXT=cards.txt$(RESET) - Run script"
	@echo "$(CYAN)make clean$(RESET) - Clean environment"
	@echo "$(CYAN)make re$(RESET) - Reinstall everything"

.PHONY: all venv install run clean re help