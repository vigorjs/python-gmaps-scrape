from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import json
import re

chrome_options = webdriver.ChromeOptions()

service = Service(
  ChromeDriverManager().install()
)

# proxy='http://mixaliskitas_gmail_com-country-us-region-new_york-city-new_york_city:5pyqsmquyy@gate.nodemaven.com:8080'

# options = {
#     'proxy': {
#         'http': proxy,
#         'https': proxy,
#         'no_proxy': 'localhost,127.0.0.1'
#     }
# }

# driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=options)

keyword = input("Masukkan Keyword : ")
deepSearch = input('Deepsearch Nomor, Websites & Alamat? *jika ON estimasi -+ 100 data/10 menit | (y/n) : ').lower().strip() == 'y'

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
    for item in items:
        data = {}

        try:
            data['nama'] = item.find_element(By.CSS_SELECTOR, '.fontHeadlineSmall').text
        except Exception:
            pass

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
            pass
        
        try:
            rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
            rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") if piece.replace(",", ".").replace(".", "", 1).isdigit()]

            if rating_numbers:
                data['ratings'] = rating_numbers[0]
                data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else 0
        except Exception:
            pass

        try:
            text_content = item.text
            phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
            matches = re.findall(phone_pattern, text_content)

            phone_numbers = [match[0] for match in matches]
            unique_phone_numbers = list(set(phone_numbers))

            data['nomor'] = unique_phone_numbers[0] if unique_phone_numbers else None   
        except Exception:
            pass

        if (deepSearch):
            try:
                item.click()
                time.sleep(6)
                item_detail = driver.find_element(By.CSS_SELECTOR, 'div[jstcache="4"] > div div[role="main"] > div:nth-child(2)')
            except Exception:
                pass
            
            try:
                data['alamat'] = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium').text
            except Exception:
                pass

            try:
                url_pattern = r'https?://(?:www\.)?[a-zA-Z0-9./]+'

                if not (data.get('website')):
                    website = item_detail.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    if re.match(url_pattern, website):
                        data['website'] = website
            except Exception:
                pass

            try:
                if not data.get('nomor'):
                    try:
                        nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium').text
                        if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                            data['nomor'] = nomor_text
                    except NoSuchElementException:
                        if website:
                            try:
                                nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(6) button > div > div .fontBodyMedium').text
                                if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                                    data['nomor'] = nomor_text
                                break
                            except Exception:
                                pass
                        else:
                            try:
                                nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(7) button > div > div .fontBodyMedium').text
                                if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                                    data['nomor'] = nomor_text
                            except NoSuchElementException:
                                try:
                                    nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(4) button > div > div .fontBodyMedium').text
                                    if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                                        data['nomor'] = nomor_text
                                except NoSuchElementException:
                                    pass
            except Exception:
                pass

        if(data.get('nama')):
            results.append(data)

        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    csv_data_obj =  open('data.csv', 'w', encoding='utf-8')
    csv_writer = csv.writer(csv_data_obj)
    header = ['nama','jenis_usaha','link','ratings','reviews','nomor', 'alamat', 'website']
    csv_writer.writerow(header)

    for data in results:
        csv_writer.writerow(data.values())

    csv_data_obj.close()
finally:
    time.sleep(60)
    driver.quit()