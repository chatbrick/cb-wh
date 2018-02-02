import logging
import motor.motor_asyncio
import os

from chatbrick.brick.send_email import SendEmail
from chatbrick.brick.mailer import Mailer
from chatbrick.brick.lotto import Lotto
from blueforge.apis.facebook import Recipient, RequestDataFormat, Message

logger = logging.getLogger(__name__)


class BrickFacebookAPIClient(object):
    def __init__(self, fb, rep):
        self.fb = fb
        self.rep = rep

    async def send_messages(self, messages):
        for message in messages:
            await self.fb.send_message(RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE'))

    async def send_message(self, message):
        await self.fb.send_message(RequestDataFormat(recipient=self.rep, message=message, message_type='RESPONSE'))


class BrickInputMessage(object):
    def __init__(self, fb, rep, brick_data):
        self.db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['DB_CONFIG']).chatbrick
        self.rep = rep
        self.brick_data = brick_data
        self.fb = fb

    async def save(self):
        await self.delete()
        input_data = {
            'brick_id': self.brick_data['id'],
            'id': self.rep.recipient_id,
            'data': self.brick_data.get('data', []),
            'platform': 'facebook',
            'store': []
        }
        brick_data = await self.db.brick.find_one({'id': self.brick_data['id']})
        for idx, u_input in enumerate(brick_data.get('user_input', [])):
            input_data['store'].append({
                'message': u_input['message'],
                'key': u_input['key'],
                'value': ''
            })

            if idx == 0:
                await self.fb.send_message(u_input['message'])

        logger.info(await self.db.message_store.insert_one(input_data))

    async def get(self):
        message_data = await self.db.message_store.find_one({
            'brick_id': self.brick_data['id'],
            'id': self.rep.recipient_id,
            'platform': 'facebook'
        })
        return message_data

    async def delete(self):
        await self.db.message_store.delete_many({'id': self.rep.recipient_id,
                                                 'platform': 'facebook'})


async def find_custom_brick(client, platform, brick_id, command, brick_data, msg_data):
    brick_config = brick_data.get('data', [])

    if platform == 'facebook':
        fb = BrickFacebookAPIClient(fb=client, rep=Recipient(recipient_id=msg_data['sender']['id']))
        brick_input = BrickInputMessage(fb=fb, rep=fb.rep, brick_data=brick_data)
        if brick_id == 'send_email':
            email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
            return email.facebook(fb_token=client.access_token, psid=msg_data['sender']['id'])
        elif brick_id == 'lotto':
            lotto = Lotto(
                fb=fb,
                brick_db=brick_input
            )

            return await lotto.facebook(command)
        elif brick_id == 'mailer':
            mailer = Mailer(
                fb=fb,
                brick_db=brick_input
            )

            return await mailer.facebook(command)
    elif platform == 'telegram':
        if brick_id == 'send_email':
            email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
            return email.telegram(sender=msg_data['from'])
