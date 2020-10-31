import shutil
import os
import sys
import filecmp
import logging
import json

from bs4 import BeautifulSoup

import requests

from linebot import LineBotApi
from linebot import WebhookHandler
from linebot.models import MessageEvent
from linebot.models import TextMessage
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
from linebot.exceptions import InvalidSignatureError

# 赤坂焼肉 KINTAN コースメニューページ
URL = 'https://tabelog.com/tokyo/A1308/A130801/13177732/party/'
CHANNEL_ACCESS_TOKEN = 'jV91aUy1HupqZT6Uy6fYEmT/6Q1hPZuzIEVVrL/TweqwbIYqPDxJ90vXer59rGs/HU7p3jaXxBT34nomyIf5AxZDYuwvu1a3En+g5DS0Un9zZKqPmWBLNi8m+ydB28WQgPjMAXvlVdZZr3X4jDohJgdB04t89/1O/w1cDnyilFU='
TO_ID = 'Ueef2a5eb2fdc3cd18d88b9b14ecd4da1'
MSG = 'Hello, world!'


logger = logging.getLogger()
logger.setLevel(logging.ERROR)

channel_secret = os.getenv('CHANNEL_SECRET', None)
channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    logger.error('Specify CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    logger.error('Specify CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


def lambda_handler(event, context):
    signature = event["headers"]["X-Line-Signature"]
    body = event["body"]

    ok_json = os.environ["ok_json"]
    error_json = os.environ["error_json"]

    @handler.add(MessageEvent, message=TextMessage)
    def message(line_event):
        text = line_event.message.text
        line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=text))

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json
    return ok_json


class LineClient():
    def __init__(self, id, message, token):
        self.id = id
        self.message = message
        self.token = token

    def send(self):
        line_bot_api = LineBotApi(self.token)
        try:
            line_bot_api.push_message(self.id, TextSendMessage(text=self.message))
        except LineBotApiError as e:
            pass

class Checker(object):
    def __init__(self, old_file, new_file):
        self.old_file = old_file
        self.new_file = new_file

    def get_diff(self):
        return filecmp.cmp(self.old_file, self.new_file)

class Client(object):
    def __init__(self, url):
        self.url = url

    def get_html(self):
        return requests.get(self.url).content


if __name__ == "__main__":
    if os.path.exists(TODAY_FILE):
        shutil.copy(TODAY_FILE, YESTERDAY_FILE)
        os.remove(TODAY_FILE)

    client = Client(URL)
    html = client.get_html()
    soup = BeautifulSoup(html, 'html.parser')
    cource_list = soup.find(class_='course-list__items')

    with open(TODAY_FILE, 'w') as f:
        f.write(str(cource_list))

    checker = Checker(TODAY_FILE, YESTERDAY_FILE)
    if checker.get_diff():
        send_to_line(CHANNEL_ACCESS_TOKEN, TO_ID, MSG)