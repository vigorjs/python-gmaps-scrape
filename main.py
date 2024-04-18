from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
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
    for i, item in enumerate(items):
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

        if not (deepSearch) :    
            try:
                data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
            except Exception:
                data['website'] = "tidak ada website"
                pass
        
        try:
            rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
            rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") if piece.replace(",", ".").replace(".", "", 1).isdigit()]

            if rating_numbers:
                data['ratings'] = rating_numbers[0]
                data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else 0
        except Exception:
            data['ratings'] = "tidak ada rating"
            data['reviews'] = "tidak ada rating"
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
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[jstcache="4"] > div div[role="main"] > div:nth-child(2)')))
                item_detail = driver.find_element(By.CSS_SELECTOR, 'div[jstcache="4"] > div div[role="main"] > div:nth-child(2)')
            except Exception as e:
                print(f"Exception when clicking item and waiting for detail.")
                pass

            try:
                WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium')))
                data['alamat'] = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium').text
            except Exception as e:
                data['alamat'] = "tidak ada alamat"
                print(f"Exception when getting address.")
                pass

            try:
                url_pattern = r'https?://(?:www\.)?[a-zA-Z0-9./]+'

                if not (data.get('website')):
                    WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a')))
                    website = item_detail.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    if re.match(url_pattern, website):
                        data['website'] = website
                    else :
                        data['website'] = "tidak ada website"
            except Exception as e:
                data['website'] = "tidak ada website"
                print(f"Exception when getting website.")
                pass

            try:
                if data.get('nomor') == None:
                    try:
                        WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium')))
                        nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium').text
                        if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                            data['nomor'] = nomor_text
                    except NoSuchElementException:
                        if website:
                            try:
                                WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div:nth-child(6) button > div > div .fontBodyMedium')))
                                nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(6) button > div > div .fontBodyMedium').text
                                if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                                    data['nomor'] = nomor_text
                            except Exception as e:
                                print(f"Exception when getting phone number.")
                                pass
                        else:
                            try:
                                WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div:nth-child(7) button > div > div .fontBodyMedium')))
                                nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(7) button > div > div .fontBodyMedium').text
                                if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                                    data['nomor'] = nomor_text
                            except NoSuchElementException:
                                try:
                                    WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div:nth-child(4) button > div > div .fontBodyMedium')))
                                    nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(4) button > div > div .fontBodyMedium').text
                                    if re.match(r".*\d$", nomor_text):  # Memeriksa apakah karakter terakhir adalah angka
                                        data['nomor'] = nomor_text
                                except NoSuchElementException:
                                    data['nomor'] = "tidak ada nomor"
                                    pass
            except Exception as e:
                print(f"Exception when getting phone number.")
                pass

        if(data.get('nama')):
            results.append(data)
            print(f"scrapped {i} data")

        #export json
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    #export csv
    csv_data_obj =  open('data.csv', 'w', encoding='utf-8')
    csv_writer = csv.writer(csv_data_obj)
    header = ['nama','jenis_usaha','link','ratings','reviews','nomor', 'alamat', 'website'] if deepSearch else ['nama','jenis_usaha','link', 'website', 'ratings','reviews','nomor']
    csv_writer.writerow(header)

    for data in results:
        csv_writer.writerow(data.values())

    csv_data_obj.close()

    #export excel
    df = pd.DataFrame(results)
    df.to_excel('data.xlsx', index=False)

finally:
    time.sleep(30)
    print(f"Data berhasil di Scrape")
    driver.quit()