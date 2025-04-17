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

print(f"📂 Output folder: {output_folder}\n")

# === Lire fichier TXT ===
with open(txt_file, 'r') as f:
	lines = [line.strip() for line in f if line.strip()]

# === Choix de la langue sur la première carte ===
first_url = lines[0]
print(f"🌐 Loading first card to detect languages: {first_url}")
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

print("\n🌍 Available languages:")
for idx, (lang_code, _) in enumerate(langs):
	print(f"{idx+1} - {lang_code}")

lang_choice = int(input("❓ Choose your language (number): ")) - 1
chosen_lang_code, lang_element = langs[lang_choice]
chosen_lang = chosen_lang_code.lower()

lang_element.click()
time.sleep(2)

print(f"✅ Language selected: {chosen_lang_code}\n")

# === Question : Appliquer une sélection automatique d'édition ? ===
auto_select_edition = input("❓ Auto select same edition for all cards? (y/n): ").strip().lower()

chosen_edition_idx = None

# === Téléchargement brut des cartes ===
card_idx = 1

for url_idx, url in enumerate(lines):
	try:
		print(f"\n🌐 Loading card: {url}")
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

		# Si c'est la première carte et choix auto : demander
		if url_idx == 0 or auto_select_edition == 'n':
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
		local_name = f"card_{card_idx}.{ext}"
		local_path = os.path.join(output_folder, local_name)

		with open(local_path, 'wb') as img_file:
			img_file.write(response.content)
		print(f"✅ Downloaded: {local_name}")

		card_idx += 1

	except Exception as e:
		print(f"❌ Error processing {url}: {e}")

driver.quit()

# === Traitement impression après tous les téléchargements ===
def prepare_images_for_print(folder, boost_mode="vivid"):
	output_suffix = "_print_ready"
	output_format = "TIFF"

	print(f"\n🖨️ Preparing images for print (mode: {boost_mode})...")
	print(f"📐 Each image will be resized to: {final_width}x{final_height} px (69x94 mm @ 300 DPI)")

	for filename in os.listdir(folder):
		if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
			original_path = os.path.join(folder, filename)
			try:
				img = Image.open(original_path).convert("RGB")

				if boost_mode in ("vivid", "ultra-vivid"):
					if boost_mode == "vivid":
						saturation_factor = 1.2
						contrast_factor = 1.1
						brightness_factor = 1.05
					elif boost_mode == "ultra-vivid":
						saturation_factor = 1.4
						contrast_factor = 1.2
						brightness_factor = 1.1

					enhancer = ImageEnhance.Color(img)
					img = enhancer.enhance(saturation_factor)
					enhancer = ImageEnhance.Contrast(img)
					img = enhancer.enhance(contrast_factor)
					enhancer = ImageEnhance.Brightness(img)
					img = enhancer.enhance(brightness_factor)

				resized = img.resize((content_width, content_height), Image.LANCZOS)
				final_img = Image.new("RGB", (final_width, final_height), (255, 255, 255))
				final_img.paste(resized, (bleed, bleed))

				cmyk_img = final_img.convert("CMYK")

				output_name = os.path.splitext(filename)[0] + output_suffix + ".tif"
				output_path = os.path.join(folder, output_name)
				cmyk_img.save(output_path, output_format, dpi=(dpi, dpi))
				print(f"🟢 Ready for print: {output_name}")

			except Exception as e:
				print(f"❌ Error processing {filename}: {e}")

prepare_images_for_print(output_folder, boost_mode="vivid")

# === Génération PDF final ===
print("\n📄 Creating final PDF...")
tiff_files = sorted([
	f for f in os.listdir(output_folder)
	if f.lower().endswith("_print_ready.tif")
])

if not tiff_files:
	print("⚠️ No TIFF files found for PDF generation.")
	sys.exit(1)

first_img = Image.open(os.path.join(output_folder, tiff_files[0]))
other_imgs = [Image.open(os.path.join(output_folder, f)) for f in tiff_files[1:]]

pdf_path = os.path.join(output_folder, "batch_cards_print.pdf")
first_img.save(pdf_path, "PDF", save_all=True, append_images=other_imgs)
print(f"✅ PDF generated: {pdf_path}")
