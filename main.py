import os
import certifi
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from twilio.rest import Client
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv('.env')
today = datetime.today().strftime('%m/%d/%Y')

cluster = MongoClient(os.environ.get('CLUSTER_INFO'), tlsCAFile=certifi.where())
db = cluster['promoDB']
collection = db['past_promos']


def scrape_page():
    req = requests.get('https://users.sellpro.net/en/promotions').text
    soup = BeautifulSoup(req, 'html.parser')

    # titles scraped from website
    titles = soup.find_all('a', class_='single-product-info-title')
    titles.reverse()

    list_of_promo_titles = [i.text for i in titles]
    list_of_promo_links = [f"https://users.sellpro.net{link.get('href')}" for link in titles]
    titles_in_db = [i['title'] for i in collection.find({})]

    message_body = []
    for title, link in zip(list_of_promo_titles, list_of_promo_links):
        if title not in titles_in_db:
            message_body.append(f'{title} {link}')
            collection.insert_one({'_id': int(collection.count_documents({}) + 1), 'date': today, 'title': title, 'link': link})
    return message_body


def send_sms(msg):
    account_sid = os.environ.get("ACCOUNT_SID")
    auth_token = os.environ.get('AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    for number in [os.environ.get('NUMBER_1'), os.environ.get('NUMBER_2')]:
        message = client.messages \
            .create(
            body=msg,
            from_=os.environ.get('TWILIO_NUMBER'),
            to=f'+1{number}'
        )
    return


# returns a list of new promos with title & link
msg_list = scrape_page()

if len(msg_list) > 0:
    for i in msg_list:
        send_sms(i)
if len(msg_list) == 0 or len(msg_list) > 1:
    print(f"There are {len(msg_list)} new promotions!")
else:
    print(f"There is {len(msg_list)} new promotion!")