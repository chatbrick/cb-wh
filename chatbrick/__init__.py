import asyncio
import motor.motor_asyncio
import json
import logging
import requests
import os
import time

from blueforge.apis.facebook import CreateFacebookApiClient
from bson.json_util import dumps
from aiohttp import web
from chatbrick.routes import setup_routes

logger = logging.getLogger('aiohttp.access')
logging.basicConfig(level=logging.DEBUG)


class CreateTelegramApiClient(object):
    def __init__(self, token):
        self.token = token

    async def send_action(self, method, chat_id):
        action = None
        if method is not None:
            if method == 'sendPhoto':
                action = 'upload_photo'
            elif method == 'goSendMessage':
                action = 'typing'
            elif method == 'sendAudio':
                action = 'upload_audio'
            elif method == 'sendVideo':
                action = 'upload_video'
            elif method == 'sendDocument':
                action = 'upload_document'
            elif method == 'sendVideoNote':
                action = 'record_video_note'
            # elif method == 'sendLocation':
            #     action = 'find_location'

            if action is not None:
                req = requests.post(url='https://api.telegram.org/bot%s/sendChatAction' % self.token,
                                    data=json.dumps({
                                        'chat_id': chat_id,
                                        'action': action
                                    }),
                                    headers={'Content-Type': 'application/json'},
                                    timeout=10)

                logger.debug(req.json())

    async def send_message(self, method, message):
        start = int(time.time() * 1000)
        req = requests.post(url='https://api.telegram.org/bot%s/%s' % (self.token, method),
                            data=json.dumps(message),
                            headers={'Content-Type': 'application/json'},
                            timeout=100)

        requests.post('https://www.chatbrick.io/api/log/', data={
            'brick_id': '',
            'platform': 'telegram',
            'start': start,
            'end': int(time.time() * 1000),
            'tag': '텔레그램,단건,%s' % method,
            'data': json.dumps(message),
            'remark': '텔레그램 브릭외에서 단건 메시지호출'
        })
        return req.json()

    @property
    def get_token(self):
        return self.token


async def send_message_profile(access_token, send_message):
    logger.debug(send_message)
    res = requests.post(url='https://graph.facebook.com/v2.6/me/messenger_profile?access_token=%s' % access_token,
                        data=json.dumps(send_message),
                        headers={'Content-Type': 'application/json'})

    logger.debug(res.json())


async def setup_db():
    db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
    chats = await db.facebook.find({}).to_list(length=1000)
    page_data = {}
    chat_data = {}

    for chat in chats:
        formed_chat = {
            'chat': json.loads(dumps(chat))
        }

        if chat.get('page_id', False):
            page_data[chat['page_id']] = chat['id']

        if chat.get('access_token', False):
            for menu in chat['persistent_menu']:
                await send_message_profile(chat['access_token'], {'whitelisted_domains': menu['whitelisted_domains']})

            await send_message_profile(chat['access_token'], chat['persistent_menu'][0])

            formed_chat['fb'] = CreateFacebookApiClient(access_token=chat['access_token'])

        if chat.get('telegram', False):
            if chat.get('telegram').get('token', False):
                formed_chat['tg'] = CreateTelegramApiClient(chat['telegram']['token'])

        chat_data[chat['id']] = formed_chat
    return db, chat_data, page_data


loop = asyncio.get_event_loop()

db = loop.run_until_complete(setup_db())
app = web.Application()
app['db'], app['chat'], app['page'] = db
setup_routes(app)
