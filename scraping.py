from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import re
import pandas as pd


def get_speaker_details(text: str):
    pattern = re.compile(r"(.+)\s\((.+)\)")
    if 'היו"ר' in text:
        name, party, is_chairman = text[6:-2], -1, 1
    elif re.search(pattern, text) is None:
        name, party, is_chairman = text[:-2], -1, 0
    else:
        name, party, is_chairman = re.search(pattern, text).group(1), re.search(pattern, text).group(2), 0

    return name, party, is_chairman


def get_protocol_id(text: str) -> int:
    match = re.search(r'(?s)מס.\s(\d+){1,3}', text).group(1)
    return int(match)


def get_protocol_date(text: str) -> str:
    match = re.search(r'(?s)\d{2}\/\d{2}\/\d{4}', text)
    match = match.group(0) if match is not None else '-1'
    return str(match)


def get_protocols(url: str) -> pd.DataFrame:
    """Gathers protocols as a dataframe, scraped from Open Knesset

    Arguments:
        url {str} -- url address for scraping

    Returns:
        pd.DataFrame -- pandas dataframe of the scraped committee protocols
        (e.g. 'protocol_id': 186,
              'committee_type' : 'ועדת החינוך, התרבות והספורט' ,
              'date': '16/08/2022',
              'speaker_name': 'אמילי חיה מואטי',
              'is_chairman': 0,
              'party_name': 'העבודה',
              'text': 'כל הכבוד לך, אני רק הקשבתי.')
    """

    # Initializing the webdriver
    options = webdriver.ChromeOptions()
    path = "/Users/guybarel/chromedriver"
    driver = webdriver.Chrome(
        executable_path=path, options=options)
    driver.set_window_size(1120, 1000)

    driver.get(url)
    protocols = []

    time.sleep(2)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "content-main")))
    except:
        driver.quit()

    protocols_list = driver.find_elements(By.XPATH, "//*[@id='content-main']/div[2]/div/div[1]/section/ul/li")
    for i, protocol in enumerate(protocols_list):
        a1 = protocol.find_element(
            By.XPATH, f"//*[@id='content-main']/div[2]/div/div[1]/section/ul/li[{i+1}]/p/a").get_attribute('href')
        p_id = re.search(r'\d{7}', a1).group(0)

        # protocol.click()
        protocol.find_element(By.XPATH, f"//*[@id='content-main']/div[2]/div/div[1]/section/ul/li[{i+1}]/p/a").click()

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@class='speech-{p_id} speech-container row']"))
            )
        except:
            driver.back()
            continue

        speakers_list = driver.find_elements(By.XPATH, f"//*[@class='speech-{p_id} speech-container row']")
        p_text = driver.find_element(
            By.XPATH, '/html/body/section/div/div[2]/div/div/section/div[1]/div[2]/blockquote').text

        for j in range(9, len(speakers_list)):

            committee_type = 'ועדת החינוך, התרבות והספורט'
            name, party, is_chairman = get_speaker_details(driver.find_element(
                By.XPATH, f'/html/body/section/div/div[2]/div/div/section/div[{j}]/div[1]').text)
            protocol_id = get_protocol_id(p_text)
            date = get_protocol_date(p_text)
            text = driver.find_element(
                By.XPATH, f'/html/body/section/div/div[2]/div/div/section/div[{j}]/div[2]/blockquote').text

            protocols.append({"protocol_id": protocol_id,
                              "committee_type": committee_type,
                              "date": date,
                              "name": name,
                              "is_chairman": is_chairman,
                              "party_name": party,
                              "text": text
                              })

        print(protocols[-1])
        driver.back()
        time.sleep(5)

    # print(protocols)
    return pd.DataFrame(protocols)  # converts the dictionary object into a pandas DataFrame.


if __name__ == '__main__':

    df = get_protocols(url='https://oknesset.org/committees/2221.html')
    df.to_csv("knesset_protocols.csv", index=False)
    # print(df)
