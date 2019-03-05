import logging
import asyncio
import traceback
import datetime
import dateutil.parser
import motor.motor_asyncio
import os
import json
import requests
import time

from bson.json_util import dumps
from blueforge.apis.facebook import RequestDataFormat, Recipient
from aiohttp import web
from chatbrick.brick import find_custom_brick
from .util import save_a_log_to_server, detect_log_type

logger = logging.getLogger('aiohttp.access')
loop = asyncio.get_event_loop()


async def send_message_profile(access_token, send_message):
    logger.debug(send_message)
    requests.post(url='https://graph.facebook.com/v2.6/me/messenger_profile?access_token=%s' % access_token,
                  data=json.dumps(send_message),
                  headers={'Content-Type': 'application/json'})


class CreateFacebookApiClient(object):
    def __init__(self, access_token):
        self.access_token = access_token

    async def send_message(self, message):
        req = requests.post(url='https://graph.facebook.com/v2.6/me/messages?access_token=%s' % self.access_token,
                            data=json.dumps(message.get_data()),
                            headers={'Content-Type': 'application/json'},
                            timeout=30)

        return req.json()

    async def __send_action(self, recipient_id, action):
        return await self.send_message(RequestDataFormat(recipient=recipient_id, sender_action=action))

    async def set_typing_on(self, recipient_id):
        return await self.__send_action(recipient_id, 'typing_on')

    async def set_typing_off(self, recipient_id):
        return await self.__send_action(recipient_id, 'typing_off')

    async def set_mark_seen(self, recipient_id):
        return await self.__send_action(recipient_id, 'mark_seen')


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
                                    timeout=15)

                logger.debug(req.json())

    async def send_message(self, method, message):
        req = requests.post(url='https://api.telegram.org/bot%s/%s' % (self.token, method),
                            data=json.dumps(message),
                            headers={'Content-Type': 'application/json'},
                            timeout=15)
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


async def refresh_post_async(request):
    name = request.match_info.get('name', None)

    if name:
        db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).facebook
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


async def refresh_post(request):
    request.app.loop.create_task(refresh_post_async(request))
    return web.Response(text='Hello World', status=200)


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
        start = int(time.time() * 1000)
        log_id = 'FBSendMessage|%d' % start

        for messaging in entry['messaging']:
            rep = Recipient(recipient_id=messaging['sender']['id'])
            if 'postback' in messaging:
                await find_brick(fb, chat, messaging, rep, 'postback', messaging['postback']['payload'], log_id)
            elif 'message' in messaging:
                db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).facebook
                text_input = await db.message_store.find_one({'id': rep.recipient_id,
                                                              'platform': 'facebook'})
                is_not_find = True
                if 'quick_reply' in messaging['message']:
                    await find_brick(fb, chat, messaging, rep, 'postback',
                                     messaging['message']['quick_reply']['payload'], log_id)
                elif 'text' in messaging['message']:
                    logger.info('text_input')
                    logger.info(text_input)
                    if text_input:
                        is_final = False
                        final_store_idx = None
                        is_go_on = False
                        store_len = len(text_input['store'])
                        for idx, store in enumerate(text_input['store']):
                            logger.info(store)
                            if store['value'] == '':
                                if store.get('type', 'text') == 'text':
                                    is_not_find = False
                                    logger.info(db.message_store.update_one({'_id': text_input['_id']}, {
                                        '$set': {'store.%d.value' % idx: messaging['message']['text'].strip()}}))
                                    if store_len == 1 or ((idx + 1) == store_len):
                                        is_final = True
                                    else:
                                        final_store_idx = idx + 1
                                        logger.info(final_store_idx)
                                        is_go_on = True
                                        break

                        if is_go_on:
                            if text_input['store'][final_store_idx]['value'] != '':
                                is_final = True

                        if is_final:
                            messaging['command'] = 'final'
                            await find_brick(fb, chat, messaging, rep, 'brick', text_input['brick_id'], log_id)
                        elif is_go_on:
                            if log_id is None:
                                log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
                            await fb.send_message(RequestDataFormat(recipient=rep,
                                                                    message=text_input['store'][final_store_idx][
                                                                        'message'], message_type='RESPONSE'))
                            log_id = save_a_log_to_server({
                                'log_id': log_id,
                                'user_id': rep.recipient_id,
                                'os': '',
                                'application': 'facebook',
                                'task_code': detect_log_type(text_input['store'][final_store_idx]['message']),
                                'origin': 'webhook_server',
                                'end': int(time.time() * 1000),
                                'remark': '메시지 보냈습니다.'

                            })

                    else:
                        await find_brick(fb, chat, messaging, rep, 'text',
                                         messaging['message']['text'], log_id)
                elif 'attachments' in messaging['message']:
                    for attachment in messaging['message']['attachments']:
                        if attachment['type'] == 'image':
                            logger.info('text_input')
                            logger.info(text_input)
                            if text_input:
                                is_final = False
                                final_store_idx = None
                                is_go_on = False
                                store_len = len(text_input['store'])
                                logger.info(store_len)
                                for idx, store in enumerate(text_input['store']):
                                    if store['value'] == '':
                                        if store.get('type', '') == 'image':
                                            logger.info(db.message_store.update_one({'_id': text_input['_id']}, {
                                                '$set': {
                                                    'store.%d.value' % idx: attachment['payload']['url'].strip()}}))

                                            logger.info(idx)
                                            logger.info(store_len)
                                            if store_len == 1 or ((idx + 1) == store_len):
                                                is_final = True
                                            else:
                                                final_store_idx = idx + 1
                                                logger.info(final_store_idx)
                                                is_go_on = True
                                                break

                                if is_final:
                                    messaging['command'] = 'final'
                                    await find_brick(fb, chat, messaging, rep, 'brick', text_input['brick_id'], log_id)
                                elif is_go_on:
                                    if log_id is None:
                                        log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
                                    await fb.send_message(RequestDataFormat(recipient=rep,
                                                                            message=
                                                                            text_input['store'][final_store_idx][
                                                                                'message'], message_type='RESPONSE'))
                                    log_id = save_a_log_to_server({
                                        'log_id': log_id,
                                        'user_id': rep.recipient_id,
                                        'os': '',
                                        'application': 'facebook',
                                        'task_code': detect_log_type(text_input['store'][final_store_idx]['message']),
                                        'origin': 'webhook_server',
                                        'end': int(time.time() * 1000),
                                        'remark': '메시지 보냈습니다.'

                                    })

    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        logger.debug('에러 발생')


async def find_brick(fb, chat, raw_msg_data, rep, brick_type, value, log_id):
    logger.info(brick_type)
    logger.info(value)
    is_not_find = True

    try:
        user_id = raw_msg_data['sender']['id']
    except:
        user_id = None

    # 브릭을 통한 진행은 여기서 진행함
    if brick_type == 'brick':
        is_not_find = False
        await find_custom_brick(client=fb, platform='facebook', brick_id=value,
                                command='final', brick_data={'id': value},
                                msg_data=raw_msg_data, brick_config=chat.get('brick_data', None), log_id=log_id)

    # payload가 브릭과 관련된 경우인지 확인하는 부분
    if brick_type == 'postback' and value.startswith('brick|'):
        is_not_find = False
        brick_payalod_cmd = brick_payload(value)
        await find_custom_brick(client=fb, platform='facebook', brick_id=brick_payalod_cmd['brick_id'],
                                command=brick_payalod_cmd['command'], brick_data={'id': brick_payalod_cmd['brick_id']},
                                msg_data=raw_msg_data, brick_config=chat.get('brick_data', None), log_id=log_id)

    # 일반적인 경우에는 여기서 진행함 - 미리 만들어진 시나리오를 통해 동작하는 경우
    for brick in chat['bricks']:
        if brick['type'] == brick_type and brick['value'] == value:
            is_not_find = False
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
                    if log_id is None:
                        log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
                    logger.info(await fb.send_message(TempMessage(recipient=rep, message=send_action['message'])))
                    log_id = save_a_log_to_server({
                        'log_id': log_id,
                        'user_id': rep.recipient_id,
                        'os': '',
                        'application': 'facebook',
                        'task_code': detect_log_type(send_action['message']),
                        'origin': 'webhook_server',
                        'end': int(time.time() * 1000),
                        'remark': '메시지 보냈습니다.'

                    })
                # Actions에서 브릭이 있으면 호출
                elif 'brick' in send_action:
                    logger.info(
                        await find_custom_brick(client=fb, platform='facebook', brick_id=send_action['brick']['id'],
                                                command='get_started', brick_data=send_action['brick'],
                                                msg_data=raw_msg_data, brick_config=chat.get('brick_data', None),
                                                log_id=log_id))

            break

    if is_not_find:
        if log_id is None:
            log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
        logger.info(await fb.send_message(TempMessage(recipient=rep, message={
            'text': chat['settings']['data']['custom_settings'].get('error_msg', '알수가 없네요.')
        })))
        save_a_log_to_server({
            'log_id': log_id,
            'user_id': rep.recipient_id,
            'os': '',
            'application': 'facebook',
            'task_code': 'facebook_text',
            'origin': 'webhook_server',
            'end': int(time.time() * 1000),
            'remark': '메시지 보냈습니다.'

        })
