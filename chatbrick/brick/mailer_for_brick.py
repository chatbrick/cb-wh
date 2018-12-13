import logging
import os
import smtplib
import time
from email.mime.text import MIMEText

import blueforge.apis.telegram as tg
from blueforge.apis.facebook import Message, QuickReply, QuickReplyTextItem

from chatbrick.util import save_a_log_to_server

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_03_001.png'
BRICK_GENERIC_TEMPLATE_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_03_002.png'


class MailerForSet(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587)
        self.sender_email = os.environ['SENDER_EMAIL']
        self.sender_password = os.environ['SENDER_PASSWORD']

    def __del__(self):
        self.smtp.close()

    async def facebook(self, command):
        if command == 'get_started':
            await self.brick_db.save()
        elif command == 'cancel':
            await self.brick_db.delete()
            await self.fb.send_message(
                message=Message(
                    text='메일 보내기를 취소했어요.',
                ))
        elif command == 'final':
            input_data = await self.brick_db.get()

            await self.fb.send_message(
                message=Message(
                    text='메일전송 요청이 완료되었습니다'
                ))

            msg = MIMEText(input_data['store'][1]['value'])
            msg['Subject'] = '%s로부터 이메일입니다.' % input_data['store'][0]['value']
            msg['To'] = input_data['data']['to']
            # if self.fb.log_id is None:
            #     self.fb.log_id = 'FBSendMessage|%d' % int(time.time() * 1000)
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.sender_email, self.sender_password)
            self.smtp.sendmail(self.sender_email, input_data['data']['to'], msg.as_string())
            # save_a_log_to_server({
            #     'log_id': self.fb.log_id,
            #     'user_id': self.fb.user_id,
            #     'os': '',
            #     'application': 'facebook',
            #     'api_code': 'mail',
            #     'api_provider_code': 'chatbrick',
            #     'origin': 'webhook_server',
            #     'end': int(time.time() * 1000),
            #     'remark': 'SMTP 통신으로 이메일 전송함'
            # })

            await self.brick_db.delete()

        return None

    async def telegram(self, command):
        if command == 'get_started':
            await self.brick_db.save()
        elif command == 'cancel':
            await self.brick_db.delete()
            await self.fb.send_message(
                tg.SendMessage(
                    text='메일보내기를 취소했습니다.',
                )
            )

        elif command == 'final':
            input_data = await self.brick_db.get()
            await self.fb.send_message(
                tg.SendMessage(
                    text='메일전송 요청이 완료되었습니다.'
                )
            )

            msg = MIMEText(input_data['store'][1]['value'])
            msg['Subject'] = '%s로부터 이메일입니다.' % input_data['store'][0]['value']
            msg['To'] = input_data['data']['to']
            # if self.fb.log_id is None:
            #     self.fb.log_id = 'SendMessage|%d' % int(time.time() * 1000)
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.sender_email, self.sender_password)
            self.smtp.sendmail(self.sender_email, input_data['data']['to'], msg.as_string())
            # save_a_log_to_server({
            #     'log_id': self.fb.log_id,
            #     'user_id': self.fb.user_id,
            #     'os': '',
            #     'application': 'telegram',
            #     'api_code': 'mail',
            #     'api_provider_code': 'chatbrick',
            #     'origin': 'webhook_server',
            #     'end': int(time.time() * 1000),
            #     'remark': 'SMTP 통신으로 이메일 전송함'
            # })

            await self.brick_db.delete()
        return None
