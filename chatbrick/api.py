import json
import logging
import os
import traceback

import motor.motor_asyncio
import requests
from aiohttp import web
from .view import CreateFacebookApiClient
from bson.json_util import dumps
from .view import send_message_profile, CreateTelegramApiClient

logger = logging.getLogger(__name__)


async def telegram_chatbot(request, api, telegram_token, name):
    if api == 'delete':
        requests.post(url='https://api.telegram.org/bot%s/deleteWebhook' % telegram_token)
        requests.get('https://api.telegram.org/bot%s/getMe' % telegram_token)
    elif api == 'register':
        requests.post(url='https://api.telegram.org/bot%s/setWebhook' % telegram_token, data={
            'url': 'https://www.chatbrick.io/webhooks/%s/tg/' % name
        })

    if name:
        db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
        chat = await db.facebook.find_one({'id': name})

        formed_chat = None
        if chat:
            formed_chat = {
                'chat': json.loads(dumps(chat))
            }

            if chat.get('page_id', False):
                request.app['page'][chat['page_id']] = chat['id']

            if chat.get('access_token', False):
                for menu in chat['persistent_menu']:
                    await send_message_profile(chat['access_token'],
                                               {'whitelisted_domains': menu['whitelisted_domains']})

                await send_message_profile(chat['access_token'], chat['persistent_menu'][0])
                formed_chat['fb'] = CreateFacebookApiClient(access_token=chat['access_token'])

            if chat.get('telegram', False):
                if chat.get('telegram').get('token', False):
                    formed_chat['tg'] = CreateTelegramApiClient(chat['telegram']['token'])

        request.app['chat'][name] = formed_chat


async def request_api(request):
    api = request.match_info.get('api', None)
    brick_id = request.query.get('brick_id')

    token = request.query.get('token')

    try:
        request.app.loop.create_task(telegram_chatbot(request, api, token, brick_id))

    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()

    return web.Response(text='null', status=200)
