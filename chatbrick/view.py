import logging
import asyncio
import traceback

from blueforge.apis.facebook import RequestDataFormat, Recipient
from aiohttp import web

logger = logging.getLogger('aiohttp.access')
loop = asyncio.get_event_loop()


class TempMessage(object):
    def __init__(self, recipient, message):
        self.recipient = recipient
        self.message = message

    def get_data(self):
        data = {}

        if self.recipient:
            data['recipient'] = self.recipient.get_data()

        if self.message:
            data['message'] = self.message

        return data

async def facebook_get(request):
    name = request.match_info.get('name', None)
    chat = request.app['chat'].get(name, None)
    data = request.query
    logger.debug(chat)
    if data and chat:
        chat = chat['chat']
        logger.info(data['hub.verify_token'])
        logger.info(chat['verify_token'])

        if data['hub.verify_token'] == chat['verify_token']:
            return web.Response(text=data['hub.challenge'])
    return web.Response(text='null', status=404)

async def facebook_post(request):
    name = request.match_info.get('name', None)
    chat_data = request.app['chat'].get(name, None)
    if chat_data is None:
        return web.Response(text='null', status=404)

    chat = chat_data['chat']
    fb = chat_data['fb']
    data = await request.json()
    logger.info(data)
    request.app.loop.create_task(fb_message_poc(chat, fb, data))

    return web.Response(text='Hello World')


async def fb_message_poc(chat, fb, data):
    try:
        for entry in data['entry']:
            for messaging in entry['messaging']:
                rep = Recipient(recipient_id=messaging['sender']['id'])
                if 'postback' in messaging:
                    await find_brick(fb, chat, rep, 'postback', messaging['postback']['payload'])
                elif 'message' in messaging:
                    if 'quick_reply' in messaging['message']:
                        await find_brick(fb, chat, rep, 'postback', messaging['message']['quick_reply']['payload'])
                    else:
                        await find_brick(fb, chat, rep, 'text', messaging['message']['text'])

    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        logger.debug('에러 발생')

async def find_brick(fb, chat, rep, brick_type, value):
    logger.debug(brick_type)
    logger.debug(value)
    await fb.set_typing_on(rep)
    for brick in chat['bricks']:
        if brick['type'] == brick_type and brick['value'] == value:
            for send_action in brick['actions']:
                logger.info(await fb.send_message(TempMessage(recipient=rep, message=send_action['message'])))
            break

    await fb.set_mark_seen(rep)
    await fb.set_typing_off(rep)


