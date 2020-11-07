import requests
import os
import json
import smtplib
import logging

from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)

logging.info("Starting script")
# Sender credentials
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# Receiver address
MY_EMAIL = "krzysztof.soltysiak27@gmail.com"

URL_CORE = "https://www.ceneo.pl"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
}


class Offer:
    def __init__(self, name, price, url):
        self.name = name
        self.price = price
        self.url = url


# Getting all offers from product page
def get_all_offers(soup):
    return soup.find_all(
        "li", class_="product-offers-2020__list__item js_productOfferGroupItem"
    )


# Getting specific text element
def get_element_text(offer, tag, class_name):
    return (offer.find(tag, class_name).text).strip()


# Getting link to product in shop
def get_element_link(offer, tag, class_name):
    return URL_CORE + offer.find(tag, class_name)["href"]


# Sending email with infomration about good price
def send_mail(sender, receiver, subject, body):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.ehlo()

    server.login(EMAIL_USER, EMAIL_PASS)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver

    html = body
    content = MIMEText(html, "html")
    message.attach(content)

    server.sendmail(sender, receiver, message.as_string())
    logging.info("Email sent!")
    server.quit()


# Reading watch_list file with specified products to watching
with open("watch_list.json") as json_file:
    data = json.load(json_file)

    for el in data["products"]:
        page = requests.get(URL_CORE + "/" + str(el["product_id"]), headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")
        all_offers = get_all_offers(soup)

        offers_list = []
        for offer in all_offers:
            offers_list.append(
                Offer(
                    get_element_text(
                        offer, "div", "product-offer-details__others-list__item__title"
                    ),
                    get_element_text(offer, "span", "price"),
                    get_element_link(
                        offer, "a", "button button--primary button--flex go-to-shop"
                    ),
                )
            )
        # Array with all product prices
        all_product_prices = [el.price for el in offers_list]
        # Array with all product prices (float)
        f_all_product_prices = [
            float(el.replace(",", ".")) for el in all_product_prices
        ]
        # Best offer object
        best_offer = offers_list[f_all_product_prices.index(min(f_all_product_prices))]
        # Best offer price
        f_best_price = float((best_offer.price).replace(",", "."))

        # Comparing best price with user defined price
        if f_best_price < el["max_price"]:
            logging.info("Discount found - {}".format(best_offer.name))

            mail_body = ""
            with open("index.html", "r") as f:
                mail_body = str(f.read())
                mail_body = mail_body.format(
                    best_offer.name, el["max_price"], best_offer.price, best_offer.url
                )

            send_mail(
                EMAIL_USER,
                MY_EMAIL,
                "Cena {} jest w zasiegu Twoich mozliwosci finansowych!".format(
                    el["name"]
                ),
                mail_body,
            )
        else:
            logging.info("No discount found")
