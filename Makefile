# 🎨 Colors
RESET   = \033[0m
GREEN   = \033[32m
RED     = \033[31m
YELLOW  = \033[33m
CYAN    = \033[36m
BOLD    = \033[1m

# 🐍 Python & Virtualenv
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# 📁 Scripts
SCRIPT = single_card_scraper.py
TXT_FILE = cards.txt

# 🧱 Main targets
all: venv install

venv:
	@echo "$(CYAN)🐍 Creating virtual environment...$(RESET)"
	@python3 -m venv $(VENV_DIR)

install: venv
	@echo "$(YELLOW)📦 Installing Python dependencies...$(RESET)"
	@$(PIP) install --upgrade pip
	@$(PIP) install selenium pillow beautifulsoup4 requests

run: all
	@echo "$(GREEN)▶️ Running scraper...$(RESET)"
	@$(PYTHON) $(SCRIPT) $(TXT_FILE)

# 🧹 Clean environment
clean:
	@echo "$(RED)🧹 Cleaning virtual environment...$(RESET)"
	@rm -rf $(VENV_DIR)

# 🔁 Full reset
re: clean all

.PHONY: all venv install run clean re
