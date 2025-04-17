# 🃏 FABTCG Batch Scraper

## 📌 Description

This script batch downloads cards from **cards.fabtcg.com**,  
allowing you to pick:

- One language for all cards (e.g., French)
- One edition per card (e.g., Cold Foil, Regular)

All images are processed for **print-ready** format (CMYK, 300 DPI, bleed) and compiled into a single PDF.

---

## 🛠 Requirements

- Python 3
- Google Chrome installed
- ChromeDriver installed and accessible globally
- Python libraries: selenium, requests, Pillow, beautifulsoup4

---

## ▶️ Usage

Prepare a `.txt` file like:

```
https://cards.fabtcg.com/card/arakni-marionette/HNT001/
https://cards.fabtcg.com/card/the-hunted/HNT002/
```

Then:

```bash
make run TXT=cards.txt
```

The script will:
1. Ask you **one time** for the language (for all cards)
2. For each card, let you **choose the edition** (Cold Foil, Rainbow Foil, etc.)

---

## 📂 Project Structure

```
fabtcg_batch_scraper/
├── single_card_scraper.py
├── Makefile
├── README.md
└── .venv_batch/ (ignored)
```

---

## 📜 License

Educational and personal use only.

---

## 👤 Author

- **Vincent B.** (`vbonnard.dev@gmail.com`)