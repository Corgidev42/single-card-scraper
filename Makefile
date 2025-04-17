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

# 📂 Output folders
BATCH_FOLDER = batch_cards
SINGLE_FOLDER = single_cards

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

# 🧹 Clean venv only
clean:
	@echo "$(RED)🧹 Cleaning virtual environment...$(RESET)"
	@rm -rf $(VENV_DIR)

# 🧹 Full clean: venv + generated folders
fclean: clean
	@echo "$(RED)🧹 Removing generated folders...$(RESET)"
	@rm -rf $(BATCH_FOLDER) $(SINGLE_FOLDER)

# 🔁 Full reset
re: fclean all

# 📜 Help
help:
	@echo ""
	@echo "$(BOLD)Available commands:$(RESET)"
	@echo "$(CYAN)make all$(RESET)       → Create venv + install dependencies"
	@echo "$(CYAN)make run$(RESET)       → Run the scraper on cards.txt"
	@echo "$(CYAN)make clean$(RESET)     → Remove virtual environment only"
	@echo "$(CYAN)make fclean$(RESET)    → Full clean (venv + generated folders)"
	@echo "$(CYAN)make re$(RESET)        → Full reset (clean + reinstall)"
	@echo ""

.PHONY: all venv install run clean fclean re help
