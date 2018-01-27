import asyncio
import motor.motor_asyncio
import json
import logging
import requests
import os

from blueforge.apis.facebook import CreateFacebookApiClient
from bson.json_util import dumps
from aiohttp import web
from chatbrick.routes import setup_routes

logger = logging.getLogger('aiohttp.access')
logging.basicConfig(level=logging.DEBUG)


class CreateTelegramApiClient(object):
    def __init__(self, token):
        self.token = token

    async def send_message(self, method, message):
        req = requests.post(url='https://api.telegram.org/bot%s/%s' % (self.token, method),
                            data=json.dumps(message),
                            headers={'Content-Type': 'application/json'},
                            timeout=5)

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
        if chat['page_id']:
            page_data[chat['page_id']] = chat['id']

        for menu in chat['persistent_menu']:
            await send_message_profile(chat['access_token'], {'whitelisted_domains': menu['whitelisted_domains']})

        await send_message_profile(chat['access_token'], chat['persistent_menu'][0])

        formed_chat = {
            'fb': CreateFacebookApiClient(access_token=chat['access_token']),
            'chat': json.loads(dumps(chat))
        }

        if chat.get('telegram', False):
            if chat.get('telegram').get('token', False):
                formed_chat['tg'] = CreateTelegramApiClient(chat['telegram']['token'])

        chat_data[chat['id']] = formed_chat
    logger.info(page_data)
    return db, chat_data, page_data


loop = asyncio.get_event_loop()

db = loop.run_until_complete(setup_db())
app = web.Application()
app['db'], app['chat'], app['page'] = db
setup_routes(app)
