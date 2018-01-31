import logging
import asyncio
import traceback
import datetime
import dateutil.parser
import motor.motor_asyncio
import os

from blueforge.apis.facebook import RequestDataFormat, Recipient
from aiohttp import web
from chatbrick.brick import find_custom_brick

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
    data = request.query

    if data['hub.verify_token'] == 'this_is_for_chat_brick_application':
        return web.Response(text=data['hub.challenge'])

    return web.Response(text='null', status=404)


async def facebook_post(request):
    data = await request.json()
    try:
        for entry in data['entry']:
            bot_id = request.app['page'].get(entry['id'], None)
            chat_data = request.app['chat'].get(bot_id, None)
            if chat_data is None:
                return web.Response(text='null', status=200)

            request.app.loop.create_task(fb_message_poc(chat_data['chat'], chat_data['fb'], entry))
    except Exception as e:
        logger.error(e)

    logger.info(data)
    return web.Response(text='Hello World')


async def fb_message_poc(chat, fb, entry):
    try:
        for messaging in entry['messaging']:
            rep = Recipient(recipient_id=messaging['sender']['id'])
            if 'postback' in messaging:
                await find_brick(fb, chat, messaging, rep, 'postback', messaging['postback']['payload'])
            elif 'message' in messaging:
                if 'quick_reply' in messaging['message']:
                    await find_brick(fb, chat, messaging, rep, 'postback',
                                     messaging['message']['quick_reply']['payload'])
                elif 'text' in messaging['message']:

                    db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
                    text_input = await db.message_store.find_one({"id": rep.recipient_id})
                    if text_input:
                        store_len = len(text_input['store'])
                        is_final = False
                        final_store_idx = None
                        for idx, store in enumerate(text_input['store']):

                            if store['value'] == '':
                                logger.info(db.message_store.update_one({'_id': text_input['_id']}, {
                                    '$set': {'store.%d.value' % idx: messaging['message']['text']}}))

                                if idx == store_len:
                                    is_final = True
                                else:
                                    final_store_idx = idx
                                    break

                        if is_final:
                            await find_brick(fb, chat, messaging, rep, 'brick', messaging['message']['text'])
                        else:
                            await fb.send_message(TempMessage(recipient=rep, message={
                                "text": text_input['store'][final_store_idx]['text']
                            }))
                            # await find_brick(fb, chat, messaging, rep, 'text', messaging['message']['text'])

    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        logger.debug('에러 발생')


async def find_brick(fb, chat, raw_msg_data, rep, brick_type, value):
    logger.info(brick_type)
    logger.info(value)
    await fb.set_typing_on(rep)
    for brick in chat['bricks']:
        if brick['type'] == brick_type and brick['value'] == value:
            is_pass = False
            if brick.get('conditions', False) and len(brick['conditions']):
                for brick_condition in brick['conditions']:
                    now = int(datetime.datetime.now().timestamp())
                    if brick_condition['type'] == 'date_between':
                        start = int(dateutil.parser.parse(brick_condition['data']['start_date']).timestamp())
                        end = int(dateutil.parser.parse(brick_condition['data']['end_data']).timestamp())
                        if now < start or now > end:
                            is_pass = True
                    elif brick_condition['type'] == 'date_not_between':
                        start = int(dateutil.parser.parse(brick_condition['data']['start_date']).timestamp())
                        end = int(dateutil.parser.parse(brick_condition['data']['end_data']).timestamp())
                        if start <= now <= end:
                            is_pass = True

            if is_pass:
                continue

            for send_action in brick['actions']:
                logger.info(send_action)
                if 'message' in send_action:
                    logger.info(await fb.send_message(TempMessage(recipient=rep, message=send_action['message'])))
                elif 'brick' in send_action:
                    logger.info(find_custom_brick(client=fb, platform='facebook', brick_id=send_action['brick']['id'],
                                                  raw_data=send_action['brick'], msg_data=raw_msg_data))
            break

    await fb.set_mark_seen(rep)
    await fb.set_typing_off(rep)
