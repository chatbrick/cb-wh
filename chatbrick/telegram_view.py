import logging
import motor.motor_asyncio
import os
import requests

import time
from aiohttp import web
from chatbrick.brick import find_custom_brick
import traceback

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def update_payload(payload):
    temp = payload.split(sep='|')
    return {
        'command': temp[0],
        'value': temp[1],
        'seq': temp[2]
    }


def brick_payload(payload):
    temp = payload.split(sep='|')
    return {
        'command': temp[0],
        'brick': temp[1],
        'sub_command': temp[2]
    }


async def telegram_get(request):
    data = request.query
    logger.info(data)
    return web.Response(text='null', status=200)


async def telegram_post(request):
    name = request.match_info.get('name', None)
    chat_data = request.app['chat'].get(name, None)
    tg = chat_data.get('tg', None)
    data = await request.json()

    try:
        if tg:
            chat = chat_data['chat']

            request.app.loop.create_task(tg_message_poc(tg, chat, data))
    except Exception as ex:
        logger.error(ex)
        traceback.print_exc()

    return web.Response(text='null', status=200)


async def tg_message_poc(tg, chat, data):
    start = int(time.time() * 1000)

    commands = {
        'log_id': 'SendMessage%d' % start,
        'user_id': None
    }
    if 'message' in data:
        message = data['message']
        is_go = True

        if 'entities' in data['message']:
            if message['entities'][0]['type'] == 'bot_command':
                is_go = False
                command = message['text'][1:message['entities'][0]['length']]
                commands['value'] = command
                logger.info('Command: %s' % command)
                await find_brick(tg, chat, message, 'bot_command', **commands)

        db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
        text_input = await db.message_store.find_one({'id': message['from']['id'],
                                                      'platform': 'telegram'})
        if 'text' in data['message'] and is_go:
            logger.info('only text')
            logger.info(text_input)
            if text_input:
                is_final = False
                is_go_on = False
                final_store_idx = None
                store_len = len(text_input['store'])

                for idx, store in enumerate(text_input['store']):
                    if store['value'] == '':
                        if store.get('type', 'text') == 'text':
                            logger.info(db.message_store.update_one({'_id': text_input['_id']}, {
                                '$set': {'store.%d.value' % idx: data['message']['text']}}))

                            logger.info(idx)
                            logger.info(store_len)
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
                    await find_brick(tg, chat, message, None, brick=text_input['brick_id'], sub_command='final')
                elif is_go_on:
                    action_message = text_input['store'][final_store_idx]['message']['message']
                    action_message['chat_id'] = message['from']['id']
                    logger.info(await tg.send_message(text_input['store'][final_store_idx]['message']['method'],
                                                      action_message))

                if not is_go_on and not is_final:
                    commands['value'] = data['message']['text']
                    await find_brick(tg, chat, message, 'text', **commands)

        elif 'photo' in data['message'] and is_go:
            logger.info('Photo!!')

            if text_input:
                is_final = False
                is_go_on = False
                final_store_idx = None
                store_len = len(text_input['store'])
                logger.info(store_len)
                for idx, store in enumerate(text_input['store']):
                    if store['value'] == '':
                        if store.get('type', 'text') == 'image':
                            last_photo = data['message']['photo'][-2]

                            if last_photo.get('file_path', False):
                                image_url = last_photo['file_path']
                            else:
                                parsed_file = await tg.send_message('getFile', {
                                    'file_id': data['message']['photo'][-2]['file_id']
                                })
                                logger.info(parsed_file)
                                image_url = parsed_file['result']['file_path']

                            logger.info(db.message_store.update_one({'_id': text_input['_id']}, {
                                '$set': {
                                    'store.%d.value' % idx: 'https://api.telegram.org/file/bot{token}/{file_path}'.format(
                                        token=tg.token, file_path=image_url)}}))

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
                    await find_brick(tg, chat, message, None, brick=text_input['brick_id'], sub_command='final')
                elif is_go_on:
                    action_message = text_input['store'][final_store_idx]['message']['message']
                    action_message['chat_id'] = message['from']['id']
                    logger.info(await tg.send_message(text_input['store'][final_store_idx]['message']['method'],
                                                      action_message))

        # if 'attatchments' in data['message'] and

    elif 'callback_query' in data:
        callback = data['callback_query']
        command = callback['data']
        logger.info('Command: %s' % command)
        if command.startswith('EDIT|'):
            commands = update_payload(command)
        elif command.startswith('BRICK|'):
            commands = brick_payload(command)
        else:
            commands['value'] = command

        if commands.get('value', False) and commands['value'] == 'start':
            brick_type = 'bot_command'
        else:
            brick_type = 'callback'
        await find_brick(tg, chat, callback, brick_type, **commands)

    requests.put('https://www.chatbrick.io/api/log/', json={
        'log_id': commands['log_id'],
        'user_id': commands['user_id'],
        'os': '',
        'application': 'telegram',
        'task_code': 'SendMessage',
        'start': start,
        'end': int(time.time() * 1000),
        'remark': ''

    })


async def find_brick(tg, chat, raw_message, brick_type, **kwargs):
    logger.info(brick_type)
    logger.info(kwargs)
    brick_data = chat.get('brick_data', None)
    is_not_find = True
    if 'brick' in kwargs:
        is_not_find = False
        await find_custom_brick(client=tg, platform='telegram', brick_id=kwargs['brick'],
                                command=kwargs['sub_command'], brick_data={'id': kwargs['brick']},
                                msg_data=raw_message, brick_config=brick_data, log_id=kwargs['log_id'])
    else:
        for brick in chat['telegram']['bricks']:
            if brick['type'] == brick_type and brick['value'] == kwargs['value']:
                is_not_find = False
                if kwargs.get('seq', False):
                    action = brick['edits'][int(kwargs['seq'])]
                    send_message = action['message']
                    send_message['chat_id'] = raw_message['from']['id']
                    send_message['message_id'] = raw_message['message']['message_id']
                    await tg.send_action(action['method'], send_message['chat_id'])
                    logger.info(await tg.send_message(action['method'], send_message))
                else:
                    for action in brick['actions']:
                        if 'message' in action:
                            send_message = action['message']
                            send_message['chat_id'] = raw_message['from']['id']
                            await tg.send_action(action['method'], send_message['chat_id'])
                            logger.info(await tg.send_message(action['method'], send_message))
                        elif 'brick' in action:
                            logger.info(
                                await find_custom_brick(client=tg, platform='telegram',
                                                        brick_id=action['brick']['id'],
                                                        command='get_started', brick_data=action['brick'],
                                                        msg_data=raw_message, brick_config=brick_data,
                                                        log_id=kwargs['log_id']))

    if is_not_find:
        send_message = {
            'chat_id': raw_message['from']['id'],
            'text': chat['settings']['data']['custom_settings'].get('error_msg', '알수가 없네요.')
        }
        await tg.send_message('sendMessage', send_message)
