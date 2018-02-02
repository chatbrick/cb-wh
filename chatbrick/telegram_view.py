import logging

from aiohttp import web
from chatbrick.brick import find_custom_brick

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def brick_payload(payload):
    temp = payload.split(sep='|')
    return {
        'command': temp[0],
        'value': temp[1],
        'seq': temp[2]
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
    logger.info(data)

    if tg:
        chat = chat_data['chat']['telegram']['bricks']

        request.app.loop.create_task(tg_message_poc(tg, chat, data))
    return web.Response(text='null', status=200)


async def tg_message_poc(tg, chat, data):
    commands = {}
    if 'message' in data:
        if 'entities' in data['message']:
            message = data['message']
            if message['entities'][0]['type'] == 'bot_command':
                command = message['text'][1:message['entities'][0]['length']]
                commands['value'] = command
                logger.info('Command: %s' % command)
                await find_brick(tg, chat, message, 'bot_command', **commands)
    elif 'callback_query' in data:
        callback = data['callback_query']
        command = callback['data']
        logger.info('Command: %s' % command)
        if command.startswith('EDIT|'):
            commands = brick_payload(command)
        else:
            commands['value'] = command

        await find_brick(tg, chat, callback, 'callback', **commands)


async def find_brick(tg, chat, raw_message, brick_type, **kwargs):
    logger.info(brick_type)
    logger.info(kwargs)
    for brick in chat:
        if brick['type'] == brick_type and brick['value'] == kwargs['value']:
            if kwargs.get('seq', False):
                action = brick['edits'][int(kwargs['seq'])]
                send_message = action['message']
                send_message['chat_id'] = raw_message['from']['id']
                send_message['message_id'] = raw_message['message']['message_id']
                logger.info(await tg.send_message(action['method'], send_message))
            else:
                for action in brick['actions']:
                    if 'message' in action:
                        send_message = action['message']
                        send_message['chat_id'] = raw_message['from']['id']
                        logger.info(await tg.send_message(action['method'], send_message))
                    elif 'brick' in action:
                        logger.info(find_custom_brick(client=tg, platform='telegram', brick_id=action['brick']['id'],
                                                      raw_data=action['brick'], msg_data=raw_message))
