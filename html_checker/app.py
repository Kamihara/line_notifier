import os
import re
import logging

from chalice import Chalice
from chalice import BadRequestError

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

logger = logging.getLogger()
app = Chalice(app_name='line-api')
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
linebot = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))

@app.route('/callback', methods=['POST'])
def callback():
    try:
        request = app.current_request

        # get X-Line-Signature header value
        signature = request.headers['x-Line-Signature']

        # get request body as text
        body = request.raw_body.decode('utf8')

        # handle webhook body
        handler.handle(body, signature)
    except Exception as err:
        logger.exception(err)
        raise BadRequestError('Invalid signature. Please check your channel access token/channel secret.')

    return 'OK'


def _valid_reply_token(event):
    '''
    Webhook のテスト時には reply token が 0 のみで構成されているので、
    その時に False を返します
    '''
    return not re.match('^0+$', event.reply_token)


@handler.add(MessageEvent, message=TextMessage)
def reply_for_text_message(event):
    ''' テキストメッセージを受け取った場合の応答 '''
    if not _valid_reply_token(event):
        return

    linebot.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))
