import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv('.env')


def scrape_page():
    req = requests.get('https://users.sellpro.net/en/promotions').text
    soup = BeautifulSoup(req, 'html.parser')

    # titles scraped from website
    titles = soup.find_all('a', class_='single-product-info-title')
    titles.reverse()
    with open('promos.txt', 'r+') as file:
        saved_promo_titles = file.read().splitlines()
        list_of_promo_titles = [i.text for i in titles]
        list_of_promo_links = [f"https://users.sellpro.net{link.get('href')}" for link in titles]

        message_body = []
        for title, link in zip(list_of_promo_titles, list_of_promo_links):
            if title not in saved_promo_titles:
                file.write(f'{title}\n')
                message_body.append(f'{title} {link}')
        return message_body


def send_sms(phone_number, text_message):
    account_sid = os.environ.get("ACCOUNT_SID")
    auth_token = os.environ.get('AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    for number, msg in zip(phone_number, text_message):
        message = client.messages \
            .create(
            body=msg,
            from_=os.environ.get('TWILIO_NUMBER'),
            to=f'+1{number}'
        )

    print(f"There are {len(text_message)} new promotions!")


msg_list = scrape_page()


if len(msg_list) > 0:
    send_sms([os.environ.get('NUMBER_1'), os.environ.get('NUMBER_2')], msg_list)
