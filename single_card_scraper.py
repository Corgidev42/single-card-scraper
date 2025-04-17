import sys
import os
import time
import requests
from PIL import Image, ImageEnhance
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Vérification arguments
if len(sys.argv) < 2:
    print("❌ Usage: python single_card_scraper.py <file.txt>")
    sys.exit(1)

txt_file = sys.argv[1]

if not os.path.isfile(txt_file):
    print(f"❌ File not found: {txt_file}")
    sys.exit(1)

# Setup Selenium
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

print(f"📂 Output folder: {output_folder}")

images_for_pdf = []

# Lire fichier txt
with open(txt_file, 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

# === Choix de la langue sur la première carte ===
first_url = lines[0]
print(f"🌐 Loading first card to detect languages: {first_url}")
driver.get(first_url)
time.sleep(3)

# Récupération des onglets langues directement avec Selenium
lang_tabs = driver.find_elements(By.CSS_SELECTOR, 'li[data-tab-lang]')

langs = []
for tab in lang_tabs:
    lang_code = tab.get_attribute("data-tab-lang")
    if lang_code:
        langs.append((lang_code.upper(), tab))  # Maintenant ce sont des WebElements natifs Selenium ✅

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

# Clic propre Selenium (cette fois sur WebElement, pas sur Tag)
lang_element.click()
time.sleep(2)

print(f"✅ Language selected: {chosen_lang_code}\n")

# Traitement de toutes les cartes
card_idx = 1

for url in lines:
    try:
        print(f"🌐 Loading card: {url}")
        driver.get(url)
        time.sleep(3)

        # Sélectionner l'onglet langue
        lang_button = driver.find_element(By.CSS_SELECTOR, f'li[data-tab-lang="{chosen_lang}"]')
        lang_button.click()
        time.sleep(2)

        # Rescraper après changement de langue
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        edition_links = soup.select(f'div[data-tab-lang="{chosen_lang}"] a.card-details__variant')

        if not edition_links:
            print(f"⚠️ No editions found for {url}")
            continue

        print("\n🎴 Available editions:")
        for idx, link in enumerate(edition_links):
            code = link.find('dd').text.strip()
            title = link.find('dt').text.strip()
            print(f"{idx+1} - {title} ({code})")

        edition_choice = int(input("❓ Choose edition (number): ")) - 1

        selected_edition_link = edition_links[edition_choice]['href']
        selected_url = f"https://cards.fabtcg.com{selected_edition_link}"

        print(f"🔎 Loading edition page: {selected_url}")
        driver.get(selected_url)
        time.sleep(2)

        # Chercher l'image principale
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

        # Traitement impression
        img = Image.open(local_path).convert("RGB")

        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)

        resized = img.resize((content_width, content_height), Image.LANCZOS)
        final_img = Image.new("RGB", (final_width, final_height), (255, 255, 255))
        final_img.paste(resized, (bleed, bleed))

        cmyk_img = final_img.convert("CMYK")

        tiff_name = f"card_{card_idx}_print_ready.tif"
        tiff_path = os.path.join(output_folder, tiff_name)
        cmyk_img.save(tiff_path, "TIFF", dpi=(dpi, dpi))
        images_for_pdf.append(cmyk_img)

        card_idx += 1

    except Exception as e:
        print(f"❌ Error processing {url}: {e}")

if images_for_pdf:
    pdf_path = os.path.join(output_folder, "batch_cards_print.pdf")
    first_img = images_for_pdf[0]
    other_imgs = images_for_pdf[1:]
    first_img.save(pdf_path, "PDF", save_all=True, append_images=other_imgs)
    print(f"✅ PDF generated: {pdf_path}")
else:
    print("⚠️ No cards processed.")

driver.quit()
