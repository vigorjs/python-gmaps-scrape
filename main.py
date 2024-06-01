import sys
import os
if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
import time
# import csv
import json
import re

keyword = input("Masukkan Keyword : ")
deepSearch = input('DeepScrape Nomor, Websites & Alamat? *jika ON estimasi -+ 100 data/15 menit | (y/n) : ').lower().strip() == 'y'
if (deepSearch):
    deepSearchEmail = input('DeepScrape Email? -+ 50 data/30 menit | (y/n) : ').lower().strip() == 'y'

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
            phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4,5}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,4}))'
            matches = re.findall(phone_pattern, text_content)

            phone_numbers = [match[0] for match in matches]
            unique_phone_numbers = list(set(phone_numbers))

            data['nomor'] = unique_phone_numbers[0] if unique_phone_numbers else None
        except Exception:
            pass

        if (deepSearch):
            try:
                print(f"scraping item........")
                time.sleep(3)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(item)).click()
                time.sleep(3)
                item_detail = driver.find_element(By.CSS_SELECTOR, 'div[jstcache="4"] > div div[role="main"] > div:nth-child(2)')
                print(f"item clicked {data['nama']}")
            except Exception as e:
                print(f"Exception when clicking item and waiting for detail. : {e} \n\n")
                pass

            try:
                print(f"scraping address......")
                WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium')))
                data['alamat'] = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div button div div .fontBodyMedium').text
                print(f"address scraped")
            except Exception as e:
                data['alamat'] = "tidak ada alamat"
                print(f"Exception when getting address.")
                pass

            try:
                if data.get('website') == None:
                    WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a')))
                    website = item_detail.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                    url_pattern = r'https?://(?:www\.)?[a-zA-Z0-9./]+'
                    if re.match(url_pattern, website):
                        data['website'] = website
            except Exception as e:
                print(f"Exception when getting website : {e} \n\n")
                pass

            try:
                if data.get('nomor') == None:
                    print(f"nomor 1")
                    WebDriverWait(item_detail, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium')))
                    print(f"nomor 2")
                    nomor_text = item_detail.find_element(By.CSS_SELECTOR, 'div[role="region"] div:nth-child(5) button > div > div .fontBodyMedium')
                    print(f"nomor 3")
                    text_content = nomor_text.text
                    
                    phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
                    print(f"nomor 4")
                    matches = re.findall(phone_pattern, text_content)

                    print(f"nomor 5")
                    phone_numbers = [match[0] for match in matches]
                    print(f"nomor 6")
                    unique_phone_numbers = list(set(phone_numbers))

                    print(f"nomor 7")
                    data['nomor'] = unique_phone_numbers[0] if unique_phone_numbers else None
                    
            except Exception as e:
                print(f"Exception when getting phone number\n\n")
                pass

            if (deepSearchEmail):
                session = HTMLSession()
                matches = []
                try:
                    response = session.get(data.get('website'))
                    soup = BeautifulSoup(response.content, 'html.parser')
                    data_url = str(soup.find_all('a'))

                    for match in re.finditer('href="/', data_url):
                        find = data_url[match.start() + 6:match.end() + 30]
                        find = find[:find.find('"')].strip()
                        
                        if find != "/":
                            final_url = f'{data["website"]}{find}'
                            matches.append(final_url)
                            if len(matches) >= 50:
                                break
                    
                    emails = []

                    for pages in matches:
                        try:
                            response = session.get(pages)
                            soup = BeautifulSoup(response.content, 'html.parser')
                            print(f'Scraping Email from {pages}..... \n')

                            for lnk in soup.find_all('a'):
                                if 'mailto:' in lnk.get('href'):
                                    emails.append(lnk.get('href').split(':')[1])
                            print(f"emails : {emails} \n")

                            email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
                            emails.extend(re.findall(email_pattern, soup.get_text()))
                            print(f"emails after regex : {emails} \n")

                        except Exception as e:
                            print(f'Exception when getting email : {e} \n')
                            data['email'] = None
                            continue

                    unique_emails = list(set(emails))
                    print(unique_emails)
                    data['email'] = unique_emails if unique_emails else "tidak ada email"
                    print(f'Email scraped \n')
                except Exception as e:
                    print(f'Exception when visitting website : {e} \n')
                    data['email'] = None
                    pass

        results.append(data)
        print(f"scrapped {i} data \n ' '")

        #export json
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    #export excel and csv
    df = pd.DataFrame(results)
    df.to_excel('data.xlsx', index=False)
    df.to_csv('data.csv', index=False)

finally:
    print(f"Data berhasil di Scrape")
    time.sleep(30)
    driver.quit()