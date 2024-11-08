import sys
import os
import asyncio
import aiohttp
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
from urllib.parse import urljoin, urlparse

if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

async def scrape_emails(data):
    async with aiohttp.ClientSession() as session:
        try:
            website = data.get('website')
            if not website:
                print(f"No website URL provided for {data['nama']}. Skipping email scraping.")
                data['email'] = "tidak ada email"
                return
            
            print(f"Scraping emails for {data['nama']} from {website}")
            
            async with session.get(website, timeout=10) as response:
                if response.status != 200:
                    print(f"Failed to fetch {website} with status {response.status}")
                    data['email'] = "tidak ada email"
                    return
                
                soup = BeautifulSoup(await response.text(), 'html.parser')
                
                # Kumpulkan semua tautan internal tanpa query parameters
                internal_links = set()
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href'].strip()
                    # Periksa apakah URL relatif
                    if href.startswith('/'):
                        # Abaikan URL dengan query parameters
                        if '?' not in href:
                            full_url = urljoin(website, href)
                            internal_links.add(full_url)
                    elif href.startswith(website):
                        if '?' not in href:
                            internal_links.add(href)
                # Batasi hingga 50 tautan internal
                internal_links = list(internal_links)[:50]
                
                emails = set()
                email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
                
                # Ekstrak email dari halaman utama
                # Dari tautan mailto
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href'].strip()
                    if href.lower().startswith('mailto:'):
                        # Ekstrak email dari tautan mailto
                        mailto_content = href[7:]  # Hapus 'mailto:'
                        # Mailto bisa memiliki banyak email dipisahkan oleh koma atau titik koma
                        extracted_emails = re.split(r'[;,]', mailto_content)
                        for email in extracted_emails:
                            email = email.strip()
                            if email:
                                # Validasi format email
                                if email_pattern.fullmatch(email):
                                    emails.add(email.lower())
                
                # Dari teks halaman utama
                page_text = soup.get_text()
                emails_in_text = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', page_text)
                for email in emails_in_text:
                    emails.add(email.lower())
                
                # Proses tautan internal
                for page_url in internal_links:
                    try:
                        async with session.get(page_url, timeout=10) as page_response:
                            if page_response.status != 200:
                                print(f"Failed to fetch {page_url} with status {page_response.status}")
                                continue
                            
                            page_soup = BeautifulSoup(await page_response.text(), 'html.parser')
                            
                            # Dari tautan mailto
                            for a_tag in page_soup.find_all('a', href=True):
                                href = a_tag['href'].strip()
                                if href.lower().startswith('mailto:'):
                                    mailto_content = href[7:]
                                    extracted_emails = re.split(r'[;,]', mailto_content)
                                    for email in extracted_emails:
                                        email = email.strip()
                                        if email:
                                            if email_pattern.fullmatch(email):
                                                emails.add(email.lower())
                            
                            # Dari teks halaman
                            page_text = page_soup.get_text()
                            emails_in_text = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', page_text)
                            for email in emails_in_text:
                                emails.add(email.lower())
                    except Exception as e:
                        print(f"Error fetching {page_url}: {e}")
                        continue
                
                if emails:
                    data['email'] = list(emails)
                else:
                    data['email'] = "tidak ada email"
                
                print(f"Emails scraped for {data['nama']}: {data['email']}")
        except Exception as e:
            print(f"Exception when scraping emails for {data['nama']}: {e}")
            data['email'] = "tidak ada email"

def scrape_item_details(driver, item, data):
    try:
        print(f"scraping item details for {data['nama']}")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(item)).click()
        time.sleep(5)
        item_detail = driver.find_element(By.CSS_SELECTOR, 'div[jstcache="4"] > div div[role="main"] > div:nth-child(2)')

        print(f"scraping address for {data['nama']}")
        WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium')))
        data['alamat'] = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium').text

        if data.get('website') is None:
            WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a')))
            website = item_detail.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            url_pattern = r'^https?://(?:www\.)?[a-zA-Z0-9./]+$'
            if re.match(url_pattern, website):
                data['website'] = website

        if data.get('nomor') is None:
            WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium')))
            nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium').text
            phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4,5}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,4}))'
            matches = re.findall(phone_pattern, nomor_text)
            phone_numbers = [match[0] for match in matches]
            unique_phone_numbers = list(set(phone_numbers))
            data['nomor'] = unique_phone_numbers[0] if unique_phone_numbers else None
    except Exception as e:
        print(f"Exception when scraping item details for {data['nama']}: {e}")

async def main():
    keyword = input("Masukkan Keyword : ")
    deepSearch = input('DeepScrape Nomor, Websites & Alamat? *jika ON estimasi -+ 100 data/15 menit | (y/n) : ').lower().strip() == 'y'
    deepSearchEmail = False
    if deepSearch:
        deepSearchEmail = input('DeepScrape Email? -+ 50 data/30 menit | (y/n) : ').lower().strip() == 'y'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(f'https://www.google.com/maps/search/{keyword}')

        try:
            WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception:
            pass

        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        driver.execute_script("""
            var scrollableDiv = arguments[0];
            function scrollWithinElement(scrollableDiv) {
                return new Promise((resolve, reject) => {
                    var totalHeight = 0;
                    var distance = 1000;
                    var scrollDelay = 3000;
                    
                    var timer = setInterval(() => {
                        var scrollHeightBefore = scrollableDiv.scrollHeight;
                        scrollableDiv.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeightBefore) {
                            totalHeight = 0;
                          
                            setTimeout(() => {
                                var scrollHeightAfter = scrollableDiv.scrollHeight;
                                if (scrollHeightAfter > scrollHeightBefore) {
                                    return;
                                } else {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, scrollDelay);
                          
                        }
                    }, 200);
                });
            }
            return scrollWithinElement(scrollableDiv);
        """, scrollable_div)

        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
        results = []
        tasks = []
        for i, item in enumerate(items):
            data = {}

            try:
                data['nama'] = item.find_element(By.CSS_SELECTOR, '.fontHeadlineSmall').text
            except Exception:
                continue

            try:
                data['jenis_usaha'] = item.find_element(By.CSS_SELECTOR, 'div.fontBodyMedium:nth-child(2) > div:nth-child(4) > div:nth-child(1) > span:nth-child(1) > span').text
            except Exception:
                pass

            try:
                data['link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
            except Exception:
                pass

            try:
                data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
            except Exception:
                data['website'] = None

            try:
                rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
                rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") if piece.replace(",", ".").replace(".", "", 1).isdigit()]

                if rating_numbers:
                    data['ratings'] = rating_numbers[0]
                    data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else 0
            except Exception:
                data['ratings'] = "tidak ada rating"
                data['reviews'] = "tidak ada rating"

            try:
                text_content = item.text
                phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4,5}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,4}))'
                matches = re.findall(phone_pattern, text_content)
                phone_numbers = [match[0] for match in matches]
                unique_phone_numbers = list(set(phone_numbers))
                data['nomor'] = unique_phone_numbers[0] if unique_phone_numbers else None
            except Exception:
                pass

            if deepSearch:
                scrape_item_details(driver, item, data)

            if deepSearchEmail:
                tasks.append(asyncio.create_task(scrape_emails(data)))

            results.append(data)
            print(f"scraped {i} data \n ' '")

        if deepSearchEmail:
            await asyncio.gather(*tasks)

        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        df = pd.DataFrame(results)
        df.to_excel('data.xlsx', index=False)
        df.to_csv('data.csv', index=False)

    finally:
        print(f"Data scraping complete")
        time.sleep(30)
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
