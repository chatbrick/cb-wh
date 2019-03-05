import json
import logging
import os
import time

import motor.motor_asyncio
from blueforge.apis.facebook import Recipient, RequestDataFormat

from chatbrick.util import save_a_log_to_server, detect_log_type
from .address import Address
from .broad_sos import BroadSos
from .broad_sos import BroadSos
from .country import Country
from .currency import Currency
from .elec import Electric
from .emergency import Emergency
from .emotion import Emotion
from .epost import EPost
from .face import Face
from .holiday import Holiday
from .icn import Icn
from .location_test import LocationTest
from .lotto import Lotto
from .luck import Luck
from .mailer import Mailer
from .mailer_for_brick import MailerForSet
from .personality_insights import PersonalityInsight
from .public_jobs import PublicJobs
from .safe_journey import SafeJourney
from .send_email import SendEmail
from .shortener import Shortener
from .train import Train
from .tts import Tts
from .whoami import Who

# FILE_DIR = '/home/ec2-user/app/chatbrick_main/src'
FILE_DIR = '/home/ec2-user/app/cb-wh'

logger = logging.getLogger(__name__)

BRICK = {
    'mailer': Mailer,
    'lotto': Lotto,
    'luck': Luck,
    'emergency': Emergency,
    'safe_journey': SafeJourney,
    'holiday': Holiday,
    'broad_sos': BroadSos,
    'icn': Icn,
    'address': Address,
    'country': Country,
    'epost': EPost,
    'train': Train,
    'electric': Electric,
    'personality': PersonalityInsight,
    'who': Who,
    'face': Face,
    'emotion': Emotion,
    'tts': Tts,
    'public_jobs': PublicJobs,
    'shortener': Shortener,
    'currency': Currency,
    'mailerforset': MailerForSet,
    'location_test': LocationTest,
}
BRICK_DEFAULT_CONFIG = {}

if len(BRICK_DEFAULT_CONFIG.keys()) == 0:
    with open(os.path.join(os.path.join(FILE_DIR, 'data'), 'default_api.json')) as file:
        brick_data = json.loads(file.read())
        BRICK_DEFAULT_CONFIG = brick_data


class BrickFacebookAPIClient(object):
    def __init__(self, fb, rep, log_id, user_id):
        self.fb = fb
        self.rep = rep
        self.log_id = log_id
        self.user_id = user_id

    async def send_messages(self, messages):
        for idx, message in enumerate(messages):
            if self.log_id is None:
                self.log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
            await self.fb.send_message(RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE'))
            self.log_id = save_a_log_to_server({
                'log_id': self.log_id,
                'user_id': self.user_id,
                'os': '',
                'application': 'facebook',
                'task_code': detect_log_type(message),
                'origin': 'webhook_server',
                'end': int(time.time() * 1000),
                'remark': '%d번째 브릭 메시지 보냈습니다.' % idx

            })

    async def send_message(self, message):
        if self.log_id is None:
            self.log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
        await self.fb.send_message(RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE'))
        self.log_id = save_a_log_to_server({
                'log_id': self.log_id,
                'user_id': self.user_id,
                'os': '',
                'application': 'facebook',
                'task_code': detect_log_type(message),
                'origin': 'webhook_server',
                'end': int(time.time() * 1000),
                'remark': '단건 브릭 메시지 보냈습니다.'

            })


class BrickTelegramAPIClient(object):
    def __init__(self, tg, rep, log_id, user_id):
        self.tg = tg
        self.rep = rep
        self.log_id = log_id
        self.user_id = user_id
    #
    # async def send_action(self, method):
    #     await self.tg.send_action(method, self.rep)

    async def send_messages(self, messages):
        for idx, message in enumerate(messages):
            if type(message) is not dict:
                dict_message = message.get_data()
                dict_message['chat_id'] = self.rep

                if self.log_id is None:
                    self.log_id = 'SendMessage|%d' % int(time.time() * 1000)
                await self.tg.send_message(message.get_method(), dict_message)
                self.log_id = save_a_log_to_server({
                    'log_id': self.log_id,
                    'user_id': self.rep,
                    'os': '',
                    'application': 'telegram',
                    'task_code': message.get_method(),
                    'origin': 'webhook_server',
                    'end': int(time.time() * 1000),
                    'remark': '%d번째 브릭 메시지 보냈습니다.' % idx
                })

            # else:
            #     message['message']['chat_id'] = self.rep
            #     await self.tg.send_action(message.get_method(), self.rep)

    async def send_message(self, message):
        if type(message) is not dict:
            dict_message = message.get_data()
            dict_message['chat_id'] = self.rep

            if self.log_id is None:
                self.log_id = 'SendMessage|%d' % int(time.time() * 1000)
            await self.tg.send_message(message.get_method(), dict_message)
            self.log_id = save_a_log_to_server({
                'log_id': self.log_id,
                'user_id': self.rep,
                'os': '',
                'application': 'telegram',
                'task_code': message.get_method(),
                'origin': 'webhook_server',
                'end': int(time.time() * 1000),
                'remark': '단건 브릭 메시지 보냈습니다.'
            })
        else:
            message['message']['chat_id'] = self.rep
            if self.log_id is None:
                self.log_id = 'SendMessage|%d' % int(time.time() * 1000)
            await self.tg.send_message(message['method'], message['message'])
            self.log_id = save_a_log_to_server({
                'log_id': self.log_id,
                'user_id': self.rep,
                'os': '',
                'application': 'telegram',
                'task_code': message['method'],
                'origin': 'webhook_server',
                'end': int(time.time() * 1000),
                'remark': '단건 브릭 메시지 보냈습니다.'
            })


class BrickInputMessage(object):
    def __init__(self, platform, fb, rep, brick_data, log_id, user_id=None):
        self.db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).facebook
        self.platform = platform
        self.brick_data = brick_data
        self.fb = fb
        self.log_id = log_id
        self.user_id = user_id
        if self.platform == 'facebook':
            self.rep = rep.recipient_id
        else:
            self.rep = rep

    async def save(self, is_pass=False, show_msg=True):
        await self.delete()
        input_data = {
            'brick_id': self.brick_data['id'],
            'id': self.rep,
            'data': self.brick_data.get('data', {}),
            'platform': self.platform,
            'store': []
        }
        logger.info('Very Important things::')
        logger.info(input_data)

        if self.platform == 'facebook':
            brick_data = await self.db.brick.find_one({'id': self.brick_data['id']})
            for idx, u_input in enumerate(brick_data.get('user_input', [])):
                if is_pass:
                    input_data['store'].append({
                        'message': u_input['message'],
                        'key': u_input['key'],
                        'type': u_input.get('type', 'text'),
                        'value': 'pass'
                    })
                elif show_msg is False:
                    input_data['store'].append({
                        'message': u_input['message'],
                        'key': u_input['key'],
                        'type': 'postback',
                        'value': ''
                    })
                else:
                    input_data['store'].append({
                        'message': u_input['message'],
                        'key': u_input['key'],
                        'type': u_input.get('type', 'text'),
                        'value': ''
                    })

                if idx == 0 and is_pass is False and show_msg:
                    await self.fb.send_message(u_input['message'])

            logger.info(await self.db.message_store.insert_one(input_data))
        elif self.platform == 'telegram':
            brick_data = await self.db.brick.find_one({'id': self.brick_data['id']})
            for idx, u_input in enumerate(brick_data.get('user_input', [])):
                if is_pass:
                    input_data['store'].append({
                        'message': u_input['tg_message'],
                        'key': u_input['key'],
                        'type': u_input.get('type', 'text'),
                        'value': 'pass'
                    })
                elif show_msg is False:
                    input_data['store'].append({
                        'message': u_input['message'],
                        'key': u_input['key'],
                        'type': 'postback',
                        'value': ''
                    })
                else:
                    input_data['store'].append({
                        'message': u_input['tg_message'],
                        'key': u_input['key'],
                        'type': u_input.get('type', 'text'),
                        'value': ''
                    })

                if idx == 0 and is_pass is False and show_msg:
                    await self.fb.send_message(u_input['tg_message'])

            logger.info(await self.db.message_store.insert_one(input_data))

    async def update(self, set_data):
        rslt_data = await self.db.message_store.update_one({
            'brick_id': self.brick_data['id'],
            'id': self.rep,
            'platform': self.platform
        }, set_data)
        return rslt_data

    async def get(self):
        message_data = await self.db.message_store.find_one({
            'brick_id': self.brick_data['id'],
            'id': self.rep,
            'platform': self.platform
        })
        return message_data

    async def delete(self):
        await self.db.message_store.delete_many({'id': self.rep,
                                                 'platform': self.platform})


async def find_custom_brick(client, platform, brick_id, command, brick_data, msg_data, brick_config, log_id):
    if brick_config is not None:
        if brick_config.get(brick_id, False):
            brick_data['data'] = brick_config[brick_id]

    if BRICK_DEFAULT_CONFIG.get(brick_id, False):
        logger.info('기본 API Key로 변경')
        brick_default_data = BRICK_DEFAULT_CONFIG[brick_id]
        for key in brick_default_data.keys():
            if brick_data['data'][key] == '':
                brick_data['data'][key] = brick_default_data[key]

    brick = BRICK.get(brick_id, False)

    if brick:
        if platform == 'facebook':
            user_id = msg_data['sender']['id']
            fb = BrickFacebookAPIClient(fb=client, rep=Recipient(recipient_id=user_id), log_id=log_id, user_id=user_id)
            brick_input = BrickInputMessage(fb=fb, platform=platform, rep=fb.rep, brick_data=brick_data, log_id=log_id,
                                            user_id=user_id)
            if brick is SendEmail:
                email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
                return email.facebook(fb_token=client.access_token, psid=msg_data['sender']['id'])
            else:
                return await brick(fb=fb, brick_db=brick_input).facebook(command)

        elif platform == 'telegram':
            user_id = msg_data['from']['id']
            tg = BrickTelegramAPIClient(tg=client, rep=user_id, log_id=log_id, user_id=user_id)
            brick_input = BrickInputMessage(fb=tg, platform=platform, rep=tg.rep, brick_data=brick_data, log_id=log_id,
                                            user_id=user_id)

            if brick_id == 'send_email':
                email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
                return email.telegram(sender=msg_data['from'])
            else:
                return await brick(fb=tg, brick_db=brick_input).telegram(command)
