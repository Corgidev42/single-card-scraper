import sys
import os
import time
import requests
from PIL import Image, ImageEnhance
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === Arguments ===
if len(sys.argv) < 2:
	print("Usage: python single_card_scraper.py <file.txt> [vivid]")
	sys.exit(1)

txt_file = sys.argv[1]
boost_mode = sys.argv[2].lower() if len(sys.argv) > 2 else "none"

if not os.path.isfile(txt_file):
	print(f"File not found: {txt_file}")
	sys.exit(1)

# === Selenium Setup ===
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# === Print Config ===
dpi = 300
width_mm, height_mm = 69, 94
final_width = int(width_mm / 25.4 * dpi)
final_height = int(height_mm / 25.4 * dpi)
content_width = int(63 / 25.4 * dpi)
content_height = int(88 / 25.4 * dpi)
bleed = int(3 / 25.4 * dpi)

output_folder = "batch_cards"
os.makedirs(output_folder, exist_ok=True)

# === Read Card URLs ===
with open(txt_file, 'r') as f:
	lines = [line.strip() for line in f if line.strip()]

entries = []
for line in lines:
	parts = line.split()
	quantity = int(parts[0]) if parts[0].isdigit() else 1
	url = parts[1] if parts[0].isdigit() else parts[0]
	entries.append((quantity, url))

# === Select Language ===
first_quantity, first_url = entries[0]
print(f"Loading first card: {first_url}")
driver.get(first_url)
time.sleep(3)

lang_tabs = driver.find_elements(By.CSS_SELECTOR, 'li[data-tab-lang]')
langs = [(tab.get_attribute("data-tab-lang").upper(), tab) for tab in lang_tabs if tab.get_attribute("data-tab-lang")]

if not langs:
	print("No available languages detected.")
	driver.quit()
	sys.exit(1)

print("Available languages:")
for idx, (lang_code, _) in enumerate(langs):
	print(f"{idx + 1} - {lang_code}")

lang_choice = int(input("Choose your language (number): ")) - 1
chosen_lang_code, lang_element = langs[lang_choice]
chosen_lang = chosen_lang_code.lower()

lang_element.click()
time.sleep(2)

# === Auto Edition Selection ===
auto_select_edition = input("Auto select same edition for all cards? (y/n): ").strip().lower()
chosen_edition_idx = None

# === Download Cards ===
for quantity, url in entries:
	try:
		print(f"Loading card: {url}")
		driver.get(url)
		time.sleep(3)

		lang_button = driver.find_element(By.CSS_SELECTOR, f'li[data-tab-lang="{chosen_lang}"]')
		lang_button.click()
		time.sleep(2)

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		edition_links = soup.select(f'div[data-tab-lang="{chosen_lang}"] a.card-details__variant')

		if not edition_links:
			print(f"No editions found for {url}")
			continue

		if chosen_edition_idx is None or auto_select_edition == 'n':
			print("Available editions:")
			for idx, link in enumerate(edition_links):
				code = link.find('dd').text.strip()
				title = link.find('dt').text.strip()
				print(f"{idx + 1} - {title} ({code})")

			edition_choice = int(input("Choose edition (number): ")) - 1
			if auto_select_edition == 'y':
				chosen_edition_idx = edition_choice
		else:
			edition_choice = chosen_edition_idx

		selected_edition_link = edition_links[edition_choice]['href']
		selected_url = f"https://cards.fabtcg.com{selected_edition_link}"

		print(f"Loading edition page: {selected_url}")
		driver.get(selected_url)
		time.sleep(2)

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		img_tags = soup.select("div.card-details__faces img")

		if not img_tags:
			print(f"No card faces found for {selected_url}")
			continue

		card_name_tag = soup.select_one("h1")
		if not card_name_tag:
			print(f"No card name found for {selected_url}")
			continue

		card_name = card_name_tag.text.strip()
		safe_card_name = card_name.replace(" ", "_").replace(",", "").replace("'", "").replace("/", "-")

		for idx, img_tag in enumerate(img_tags):
			img_url = img_tag['src']
			face = "recto" if idx == 0 else "verso"
			img = Image.open(requests.get(img_url, stream=True).raw).convert("RGB")

			if boost_mode == "vivid":
				enhancer = ImageEnhance.Color(img)
				img = enhancer.enhance(1.2)
				enhancer = ImageEnhance.Contrast(img)
				img = enhancer.enhance(1.1)
				enhancer = ImageEnhance.Brightness(img)
				img = enhancer.enhance(1.05)

			resized = img.resize((content_width, content_height), Image.LANCZOS)
			final_img = Image.new("RGB", (final_width, final_height), (0, 0, 0))
			final_img.paste(resized, (bleed, bleed))

			cmyk_img = final_img.convert("CMYK")

			for copy_num in range(1, quantity + 1):
				suffix = f"_copy{copy_num}" if quantity > 1 else ""
				tiff_filename = f"{safe_card_name}{suffix}_{face}_print_ready.tif"
				tiff_path = os.path.join(output_folder, tiff_filename)
				cmyk_img.save(tiff_path, "TIFF", dpi=(dpi, dpi))
				print(f"Saved: {tiff_filename}")

	except Exception as e:
		print(f"Error processing {url}: {e}")

# === Close driver ===
driver.quit()
print("All done.")


# === Génération PDF final ===
def export_images_to_pdf(folder):
	print("Creating final print PDF...")
	tiff_files = sorted(
		f for f in os.listdir(folder)
		if f.lower().endswith("_print_ready.tif")
	)

	if not tiff_files:
		print("No images found for PDF generation.")
		return

	first_image = Image.open(os.path.join(folder, tiff_files[0]))
	other_images = [Image.open(os.path.join(folder, f)) for f in tiff_files[1:]]

	pdf_path = os.path.join(folder, "batch_cards_print.pdf")
	first_image.save(pdf_path, "PDF", save_all=True, append_images=other_images)
	print(f"PDF generated: {pdf_path}")

export_images_to_pdf(output_folder)

# === Demande nettoyage fichiers ===
def cleanup_prompt(folder):
	print("Select what you want to delete:")
	print("  t - Print-ready TIFF files")
	print("  p - PDF file")
	print("  a - All of the above")
	print("  n - Keep everything")

	answer = input("Your choice [t/p/a/n]: ").strip().lower()

	delete_tiff = answer in ('t', 'a')
	delete_pdf = answer in ('p', 'a')

	deleted_tif = 0
	deleted_pdf = False

	if delete_tiff:
		for filename in os.listdir(folder):
			if filename.endswith("_print_ready.tif"):
				try:
					os.remove(os.path.join(folder, filename))
					deleted_tif += 1
				except Exception as e:
					print(f"Error deleting TIFF {filename}: {e}")

	if delete_pdf:
		pdf_path = os.path.join(folder, "batch_cards_print.pdf")
		if os.path.exists(pdf_path):
			try:
				os.remove(pdf_path)
				deleted_pdf = True
			except Exception as e:
				print(f"Error deleting PDF: {e}")

	print()
	if answer == 'n':
		print("No files deleted.")
	else:
		if delete_tiff:
			print(f"Deleted {deleted_tif} TIFF file(s).")
		if delete_pdf and deleted_pdf:
			print("Deleted PDF file.")

cleanup_prompt(output_folder)

driver.quit()
print("All done.")
# === Fin du script ===
