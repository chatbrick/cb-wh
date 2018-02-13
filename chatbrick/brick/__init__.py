import logging
import os
import requests
import time
import motor.motor_asyncio
from blueforge.apis.facebook import Recipient, RequestDataFormat

from .emergency import Emergency
from .holiday import Holiday
from .lotto import Lotto
from .luck import Luck
from .mailer import Mailer
from .send_email import SendEmail
from .broad_sos import BroadSos
from .broad_sos import BroadSos
from .icn import Icn
from .address import Address
from .country import Country
from .safe_journey import SafeJourney
from .epost import EPost
from .train import Train
from .elec import Electric
from .personality_insights import PersonalityInsight
from .whoami import Who
from .face import Face
from .emotion import Emotion

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
    'emotion': Emotion
}


class BrickFacebookAPIClient(object):
    def __init__(self, fb, rep):
        self.fb = fb
        self.rep = rep

    async def send_messages(self, messages):
        for idx, message in enumerate(messages):
            start = int(time.time() * 1000)

            await self.fb.send_message(RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE'))
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': '',
                'platform': 'facebook',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '페이스북,여러메시지호출,%s,%s' % (idx, self.rep.recipient_id),
                'data': RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE').get_data(),
                'remark': '페이스북 메시지호출'
            })

    async def send_message(self, message):
        start = int(time.time() * 1000)
        await self.fb.send_message(RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE'))
        requests.post('https://www.chatbrick.io/api/log/', data={
            'brick_id': '',
            'platform': 'facebook',
            'start': start,
            'end': int(time.time() * 1000),
            'tag': '페이스북,단건메시지호출,%s' % self.rep.recipient_id,
            'data': RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE').get_data(),
            'remark': '페이스북 메시지호출'
        })


class BrickTelegramAPIClient(object):
    def __init__(self, tg, rep):
        self.tg = tg
        self.rep = rep

    async def send_action(self, method):
        await self.tg.send_action(method, self.rep)

    async def send_messages(self, messages):
        for idx, message in enumerate(messages):

            if type(message) is not dict:
                dict_message = message.get_data()
                dict_message['chat_id'] = self.rep
                await self.tg.send_action(message.get_method(), self.rep)
                await self.tg.send_message(message.get_method(), dict_message)

            else:
                message['message']['chat_id'] = self.rep
                await self.tg.send_action(message.get_method(), self.rep)

    async def send_message(self, message):

        if type(message) is not dict:
            dict_message = message.get_data()
            dict_message['chat_id'] = self.rep
            await self.tg.send_action(message.get_method(), self.rep)
            await self.tg.send_message(message.get_method(), dict_message)
        else:
            message['message']['chat_id'] = self.rep
            await self.tg.send_action(message['method'], self.rep)
            await self.tg.send_message(message['method'], message['message'])


class BrickInputMessage(object):
    def __init__(self, platform, fb, rep, brick_data):
        self.db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
        self.platform = platform
        self.brick_data = brick_data
        self.fb = fb

        if self.platform == 'facebook':
            self.rep = rep.recipient_id
        else:
            self.rep = rep

    async def save(self, is_pass=False):
        await self.delete()
        input_data = {
            'brick_id': self.brick_data['id'],
            'id': self.rep,
            'data': self.brick_data.get('data', []),
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
                else:
                    input_data['store'].append({
                        'message': u_input['message'],
                        'key': u_input['key'],
                        'type': u_input.get('type', 'text'),
                        'value': ''
                    })

                if idx == 0 and is_pass is False:
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
                else:
                    input_data['store'].append({
                        'message': u_input['tg_message'],
                        'key': u_input['key'],
                        'type': u_input.get('type', 'text'),
                        'value': ''
                    })

                if idx == 0 and is_pass is False:
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


async def find_custom_brick(client, platform, brick_id, command, brick_data, msg_data, brick_config):
    if brick_config is not None:
        if brick_config.get(brick_id, False):
            brick_data['data'] = brick_config[brick_id]

    logger.info('find_custom_brick/brick_config')
    logger.info(brick_config)
    brick = BRICK.get(brick_id, False)

    if brick:
        if platform == 'facebook':
            fb = BrickFacebookAPIClient(fb=client, rep=Recipient(recipient_id=msg_data['sender']['id']))
            brick_input = BrickInputMessage(fb=fb, platform=platform, rep=fb.rep, brick_data=brick_data)
            if brick is SendEmail:
                email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
                return email.facebook(fb_token=client.access_token, psid=msg_data['sender']['id'])
            else:
                return await brick(fb=fb, brick_db=brick_input).facebook(command)

        elif platform == 'telegram':
            tg = BrickTelegramAPIClient(tg=client, rep=msg_data['from']['id'])
            brick_input = BrickInputMessage(fb=tg, platform=platform, rep=tg.rep, brick_data=brick_data)

            if brick_id == 'send_email':
                email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
                return email.telegram(sender=msg_data['from'])
            else:
                return await brick(fb=tg, brick_db=brick_input).telegram(command)
