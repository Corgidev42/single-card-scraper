import sys
import os
import time
import requests
from PIL import Image, ImageEnhance, ImageCms
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import subprocess

# === Auto-install numpy ===
try:
	import numpy as np
except ImportError:
	print("📦 numpy manquant → installation automatique...")
	subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
	import numpy as np

def apply_soft_curve(img):
	arr = np.asarray(img).astype(np.float32)
	arr = (arr / 255.0) ** 0.825 * 255
	return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode=img.mode)

def convert_to_cmyk_softcurve(img):
	img = apply_soft_curve(img.convert("RGB"))
	icc_profile = "ISOcoated_v2_eci.icc"
	if not os.path.exists(icc_profile):
		print("\n❌ Profil ICC manquant. Télécharger ici : http://www.eci.org/_media/downloads/icc_profiles_from_eci/eci_offset_2009.zip")
		sys.exit(1)
	srgb = ImageCms.createProfile("sRGB")
	cmyk_prof = ImageCms.getOpenProfile(icc_profile)
	xform = ImageCms.buildTransformFromOpenProfiles(srgb, cmyk_prof, "RGB", "CMYK")
	return ImageCms.applyTransform(img, xform)

if len(sys.argv) < 2:
	print("Usage: python single_card_scraper.py <file.txt>")
	sys.exit(1)

txt_file = sys.argv[1]
if not os.path.isfile(txt_file):
	print(f"File not found: {txt_file}")
	sys.exit(1)

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)

# Print config
dpi = 300
target_width = int(63 / 25.4 * dpi)
target_height = int(88 / 25.4 * dpi)

output_folder = "batch_cards"
os.makedirs(output_folder, exist_ok=True)

with open(txt_file, 'r') as f:
	entries = [(int(p[0]), p[1]) if p[0].isdigit() else (1, p[0]) for p in [line.strip().split() for line in f if line.strip()]]

# Select language
first_quantity, first_url = entries[0]
driver.get(first_url)
time.sleep(3)

lang_tabs = driver.find_elements(By.CSS_SELECTOR, 'li[data-tab-lang]')
langs = [(tab.get_attribute("data-tab-lang").upper(), tab) for tab in lang_tabs if tab.get_attribute("data-tab-lang")]
if not langs:
	print("No language options found.")
	driver.quit()
	sys.exit(1)

print("Available languages:")
for i, (code, _) in enumerate(langs):
	print(f"{i+1} - {code}")
lang_choice = int(input("Choose your language (number): ")) - 1
chosen_lang, lang_element = langs[lang_choice]
lang_element.click()
time.sleep(2)

# Ask edition choice mode
auto_select = input("Auto select same edition for all cards? (y/n): ").strip().lower() == 'y'
chosen_edition_idx = None

for quantity, url in entries:
	success = False
	while not success:
		try:
			print(f"\n🔄 Loading card: {url}")
			driver.get(url)
			time.sleep(3)
			driver.find_element(By.CSS_SELECTOR, f'li[data-tab-lang="{chosen_lang.lower()}"]').click()
			time.sleep(2)

			soup = BeautifulSoup(driver.page_source, 'html.parser')
			editions = soup.select(f'div[data-tab-lang="{chosen_lang.lower()}"] a.card-details__variant')

			if not editions:
				raise ValueError("No editions found for this card.")

			# Si l'index pré-sélectionné n'est plus valide → re-proposer le choix
			if chosen_edition_idx is None or not auto_select or chosen_edition_idx >= len(editions):
				print("Available editions:")
				for i, e in enumerate(editions):
					print(f"{i+1} - {e.find('dt').text.strip()} ({e.find('dd').text.strip()})")
				chosen_edition_idx = int(input("Choose edition (number): ")) - 1

			selected_href = editions[chosen_edition_idx]['href']
			selected_url = f"https://cards.fabtcg.com{selected_href}"
			driver.get(selected_url)
			time.sleep(2)
			soup = BeautifulSoup(driver.page_source, 'html.parser')

			name_tag = soup.select_one("h1")
			if not name_tag:
				raise ValueError("No card name found.")

			card_name = name_tag.text.strip().replace(" ", "_").replace("/", "-")
			img_tags = soup.select("div.card-details__faces img")
			if not img_tags:
				raise ValueError("No image found for this card.")

			for idx, img_tag in enumerate(img_tags):
				img_url = img_tag['src']
				img = Image.open(requests.get(img_url, stream=True).raw)
				resized = img.resize((target_width, target_height), Image.LANCZOS)
				cmyk_img = convert_to_cmyk_softcurve(resized)

				for n in range(quantity):
					suffix = f"_copy{n+1}" if quantity > 1 else ""
					face = "recto" if idx == 0 else "verso"
					filename = f"{card_name}{suffix}_{face}_print_ready.tif"
					cmyk_img.save(os.path.join(output_folder, filename), "TIFF", dpi=(dpi, dpi))
					print(f"✅ Saved: {filename}")
			success = True

		except Exception as e:
			print(f"❌ Error with {url}: {e}")
			url = input("🔁 Enter a new valid URL to retry this card (or press Enter to skip): ").strip()
			if not url:
				break

# PDF merge
from PIL import Image as PILImage

def export_images_to_pdf(folder):
	print("\n📄 Creating final print PDF...")
	tiff_files = sorted(f for f in os.listdir(folder) if f.lower().endswith("_print_ready.tif"))
	if not tiff_files:
		print("⚠️ No images found for PDF.")
		return
	first = PILImage.open(os.path.join(folder, tiff_files[0]))
	rest = [PILImage.open(os.path.join(folder, f)) for f in tiff_files[1:]]
	pdf_path = os.path.join(folder, "batch_cards_print.pdf")
	first.save(pdf_path, "PDF", save_all=True, append_images=rest)
	print(f"✅ PDF generated: {pdf_path}")

export_images_to_pdf(output_folder)

# Cleanup prompt
def cleanup_prompt(folder):
	print("\n🧹 Cleanup options:")
	print("  t - TIFF files")
	print("  p - PDF")
	print("  a - All")
	print("  n - Nothing")
	choice = input("Your choice [t/p/a/n]: ").strip().lower()
	if choice in ('t', 'a'):
		for f in os.listdir(folder):
			if f.endswith("_print_ready.tif"):
				os.remove(os.path.join(folder, f))
	if choice in ('p', 'a'):
		pdf_path = os.path.join(folder, "batch_cards_print.pdf")
		if os.path.exists(pdf_path):
			os.remove(pdf_path)
	print("✅ Cleanup done.")

cleanup_prompt(output_folder)
driver.quit()
print("✨ All done.")
