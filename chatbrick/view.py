import logging
import asyncio
import traceback
import datetime
import dateutil.parser
import motor.motor_asyncio
import os
import json
import requests

from bson.json_util import dumps
from blueforge.apis.facebook import RequestDataFormat, Recipient
from aiohttp import web
from chatbrick.brick import find_custom_brick
from blueforge.apis.facebook import CreateFacebookApiClient


logger = logging.getLogger('aiohttp.access')
loop = asyncio.get_event_loop()


async def send_message_profile(access_token, send_message):
    logger.debug(send_message)
    res = requests.post(url='https://graph.facebook.com/v2.6/me/messenger_profile?access_token=%s' % access_token,
                        data=json.dumps(send_message),
                        headers={'Content-Type': 'application/json'})

    logger.debug(res.json())


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


def brick_payload(payload):
    temp = payload.split(sep='|')
    return {
        'type': temp[0],
        'brick_id': temp[1],
        'command': temp[2]
    }

async def refresh_post(request):
    name = request.match_info.get('name', None)
    if name:
        db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
        chat = await db.facebook.find_one({'id': name})
        logger.info(chat)

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
        logger.info(request.app['chat'])
        return web.Response(text='Hello World')

    return web.Response(text='null', status=404)


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
                    text_input = await db.message_store.find_one({'id': rep.recipient_id,
                                                                  'platform': 'facebook'})
                    logger.info('text_input')
                    logger.info(text_input)
                    if text_input:
                        is_final = False
                        final_store_idx = None
                        store_len = len(text_input['store'])
                        logger.info(store_len)
                        for idx, store in enumerate(text_input['store']):
                            if store['value'] == '':
                                logger.info(db.message_store.update_one({'_id': text_input['_id']}, {
                                    '$set': {'store.%d.value' % idx: messaging['message']['text']}}))

                                logger.info(idx)
                                logger.info(store_len)
                                if store_len == 1 or ((idx + 1) == store_len):
                                    is_final = True
                                else:
                                    final_store_idx = idx + 1
                                    logger.info(final_store_idx)
                                    break

                        if is_final:
                            messaging['command'] = 'final'
                            await find_brick(fb, chat, messaging, rep, 'brick', text_input['brick_id'])
                        else:
                            await fb.send_message(RequestDataFormat(recipient=rep,
                                                                    message=text_input['store'][final_store_idx]['message'], message_type='RESPONSE'))
                    else:
                        await find_brick(fb, chat, messaging, rep, 'text',
                                         messaging['message']['text'])
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        logger.debug('에러 발생')


async def find_brick(fb, chat, raw_msg_data, rep, brick_type, value):
    logger.info(brick_type)
    logger.info(value)
    await fb.set_typing_on(rep)
    # 브릭을 통한 진행은 여기서 진행함
    if brick_type == 'brick':
        await find_custom_brick(client=fb, platform='facebook', brick_id=value,
                                command='final', brick_data={'id': value},
                                msg_data=raw_msg_data, brick_config=chat.get('brick_data', None))

    # payload가 브릭과 관련된 경우인지 확인하는 부분
    if brick_type == 'postback' and value.startswith('brick|'):
        brick_payalod_cmd = brick_payload(value)
        await find_custom_brick(client=fb, platform='facebook', brick_id=brick_payalod_cmd['brick_id'],
                                command=brick_payalod_cmd['command'], brick_data={'id': brick_payalod_cmd['brick_id']},
                                msg_data=raw_msg_data, brick_config=chat.get('brick_data', None))

    # 일반적인 경우에는 여기서 진행함 - 미리 만들어진 시나리오를 통해 동작하는 경우
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

                # Actions에서 브릭이 있으면 호출
                elif 'brick' in send_action:
                    logger.info(
                        await find_custom_brick(client=fb, platform='facebook', brick_id=send_action['brick']['id'],
                                                command='get_started', brick_data=send_action['brick'],
                                                msg_data=raw_msg_data, brick_config=chat.get('brick_data', None)))
            break

    await fb.set_mark_seen(rep)
    await fb.set_typing_off(rep)
