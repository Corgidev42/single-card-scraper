import sys
import os
import time
import requests
from PIL import Image, ImageEnhance
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === Vérification des arguments ===
if len(sys.argv) < 2:
	print("❌ Usage: python single_card_scraper.py <file.txt>")
	sys.exit(1)

txt_file = sys.argv[1]

if not os.path.isfile(txt_file):
	print(f"❌ File not found: {txt_file}")
	sys.exit(1)

# === Setup Selenium ===
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)

dpi = 300
width_mm, height_mm = 69, 94
final_width = int(width_mm / 25.4 * dpi)
final_height = int(height_mm / 25.4 * dpi)
content_width = int(63 / 25.4 * dpi)
content_height = int(88 / 25.4 * dpi)
bleed = int(3 / 25.4 * dpi)

output_folder = "batch_cards"
os.makedirs(output_folder, exist_ok=True)

print(f"\U0001F4C2 Output folder: {output_folder}\n")

# === Lire fichier TXT ===
with open(txt_file, 'r') as f:
	lines = [line.strip() for line in f if line.strip()]

# Parse fichier en [(quantité, url)]
entries = []
for line in lines:
	parts = line.split()
	if parts[0].isdigit():
		quantity = int(parts[0])
		url = parts[1]
	else:
		quantity = 1
		url = parts[0]
	entries.append((quantity, url))

# === Choix de la langue sur la première carte ===
first_quantity, first_url = entries[0]
print(f"\U0001F310 Loading first card to detect languages: {first_url}")
driver.get(first_url)
time.sleep(3)

lang_tabs = driver.find_elements(By.CSS_SELECTOR, 'li[data-tab-lang]')

langs = []
for tab in lang_tabs:
	lang_code = tab.get_attribute("data-tab-lang")
	if lang_code:
		langs.append((lang_code.upper(), tab))

if not langs:
	print("❌ No available languages detected.")
	driver.quit()
	sys.exit(1)

print("\n\U0001F30D Available languages:")
for idx, (lang_code, _) in enumerate(langs):
	print(f"{idx+1} - {lang_code}")

lang_choice = int(input("❓ Choose your language (number): ")) - 1
chosen_lang_code, lang_element = langs[lang_choice]
chosen_lang = chosen_lang_code.lower()

lang_element.click()
time.sleep(2)

print(f"✅ Language selected: {chosen_lang_code}\n")

# === Choix d'édition automatique ===
auto_select_edition = input("❓ Auto select same edition for all cards? (y/n): ").strip().lower()
chosen_edition_idx = None

# === Téléchargement brut des cartes ===
card_idx = 1

for quantity, url in entries:
	try:
		print(f"\n\U0001F310 Loading card: {url}")
		driver.get(url)
		time.sleep(3)

		lang_button = driver.find_element(By.CSS_SELECTOR, f'li[data-tab-lang="{chosen_lang}"]')
		lang_button.click()
		time.sleep(2)

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		edition_links = soup.select(f'div[data-tab-lang="{chosen_lang}"] a.card-details__variant')

		if not edition_links:
			print(f"⚠️ No editions found for {url}")
			continue

		# Si première carte ou pas auto : demander
		if card_idx == 1 or auto_select_edition == 'n':
			print("\n🎴 Available editions:")
			for idx, link in enumerate(edition_links):
				code = link.find('dd').text.strip()
				title = link.find('dt').text.strip()
				print(f"{idx+1} - {title} ({code})")

			edition_choice = int(input("❓ Choose edition (number): ")) - 1
			if auto_select_edition == 'y':
				chosen_edition_idx = edition_choice
		else:
			edition_choice = chosen_edition_idx

		selected_edition_link = edition_links[edition_choice]['href']
		selected_url = f"https://cards.fabtcg.com{selected_edition_link}"

		print(f"🔎 Loading edition page: {selected_url}")
		driver.get(selected_url)
		time.sleep(2)

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		main_img = soup.select_one("div.card-details__faces img")

		if not main_img:
			print(f"❌ No main image found for {selected_url}")
			continue

		img_url = main_img['src']
		response = requests.get(img_url)
		response.raise_for_status()

		ext = img_url.split('.')[-1].split('?')[0]

		# Télécharger autant de copies que demandé
		for copy_idx in range(1, quantity + 1):
			local_name = f"card_{card_idx}_copy{copy_idx}.{ext}"
			local_path = os.path.join(output_folder, local_name)

			with open(local_path, 'wb') as img_file:
				img_file.write(response.content)
			print(f"✅ Downloaded: {local_name}")

		card_idx += 1

	except Exception as e:
		print(f"❌ Error processing {url}: {e}")

# === Terminé ===
driver.quit()
print("\n✅ All downloads completed!")
