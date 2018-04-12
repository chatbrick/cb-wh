import smtplib
import logging
import os
import smtplib
from email.mime.text import MIMEText

import blueforge.apis.telegram as tg
from blueforge.apis.facebook import Message, GenericTemplate, TemplateAttachment, ImageAttachment, PostBackButton, \
    Element, QuickReply, QuickReplyTextItem

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
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyTextItem(
                                title='새 메일보내기',
                                payload='brick|mailerforset|get_started'
                            )
                        ]
                    )
                ))
        elif command == 'final':
            input_data = await self.brick_db.get()
            msg = MIMEText(input_data['store'][1]['value'])
            msg['Subject'] = '%s로부터 이메일입니다.' % input_data['store'][0]['value']
            msg['To'] = input_data['data']['to']
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.sender_email, self.sender_password)
            self.smtp.sendmail(self.sender_email, input_data['data']['to'], msg.as_string())
            await self.fb.send_message(
                message=Message(
                    text='메일 보내기가 완료되었어요.',
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyTextItem(
                                title='연속하여 메일보내기',
                                payload='brick|mailerforset|get_started'
                            )
                        ]
                    )
                ))
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
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='메일 보내기',
                                    callback_data='BRICK|mailerforset|get_started'
                                )
                            ]
                        ]
                    )
                )
            )
        elif command == 'final':
            input_data = await self.brick_db.get()
            msg = MIMEText(input_data['store'][1]['value'])
            msg['Subject'] = '%s로부터 이메일입니다.' % input_data['store'][0]['value']
            msg['To'] = input_data['data']['to']
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.sender_email, self.sender_password)
            self.smtp.sendmail(self.sender_email, input_data['data']['to'], msg.as_string())
            await self.fb.send_message(
                tg.SendMessage(
                    text='메일 보내기가 완료되었어요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='연속하여 메일보내기',
                                    callback_data='BRICK|mailerforset|get_started'
                                )
                            ]
                        ]
                    )
                )
            )

            await self.brick_db.delete()
        return None
