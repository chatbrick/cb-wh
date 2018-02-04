import requests
import smtplib
import logging
import os
import blueforge.apis.telegram as tg

from blueforge.apis.facebook import Message, GenericTemplate, TemplateAttachment, ImageAttachment, PostBackButton, \
    Element, QuickReply, QuickReplyTextItem
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = [
    'https://www.chatbrick.io/api/static/img_brick_02_slide.png',
    'https://www.chatbrick.io/api/static/img_brick_01_slide.png'
]


class Mailer(object):
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
            send_message = [
                Message(
                    attachment=ImageAttachment(
                        url=BRICK_DEFAULT_IMAGE[1]
                    )
                ),
                Message(
                    text='블루핵에서 제공하는 "메일보내기 서비스"예요.'
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(title='메일전송',
                                        subtitle='챗봇에서 메일을 보낼 수 있어요',
                                        buttons=[
                                            PostBackButton(
                                                title='메일보내기',
                                                payload='brick|mailer|show_data'
                                            )
                                        ])
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'show_data':
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
                                payload='brick|mailer|show_data'
                            )
                        ]
                    )
                ))
        elif command == 'final':
            input_data = await self.brick_db.get()
            msg = MIMEText(input_data['store'][2]['value'])
            msg['Subject'] = '%s로부터 이메일입니다.' % input_data['store'][0]['value']
            msg['To'] = input_data['store'][1]['value']
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.sender_email, self.sender_password)
            self.smtp.sendmail(self.sender_email, input_data['store'][1]['value'], msg.as_string())
            await self.fb.send_message(
                message=Message(
                    text='메일 보내기가 완료되었어요.',
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyTextItem(
                                title='연속하여 메일보내기',
                                payload='brick|mailer|show_data'
                            )
                        ]
                    )
                ))
            await self.brick_db.delete()

        return None

    async def telegram(self, command):
        if command == 'get_started':
            send_message = [
                tg.SendPhoto(
                    photo=BRICK_DEFAULT_IMAGE[0]
                ),
                tg.SendMessage(
                    text='블루핵에서 제공하는 "메일보내기 서비스"예요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='메일 보내기',
                                    callback_data='BRICK|mailer|show_data'
                                )
                            ]
                        ]
                    )
                )

            ]
            await self.fb.send_messages(send_message)
        elif command == 'show_data':
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
                                    callback_data='BRICK|mailer|show_data'
                                )
                            ]
                        ]
                    )
                )
            )
        elif command == 'final':
            input_data = await self.brick_db.get()
            msg = MIMEText(input_data['store'][2]['value'])
            msg['Subject'] = '%s로부터 이메일입니다.' % input_data['store'][0]['value']
            msg['To'] = input_data['store'][1]['value']
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.sender_email, self.sender_password)
            self.smtp.sendmail(self.sender_email, input_data['store'][1]['value'], msg.as_string())
            await self.fb.send_message(
                tg.SendMessage(
                    text='메일 보내기가 완료되었어요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='연속하여 메일보내기',
                                    callback_data='BRICK|mailer|show_data'
                                )
                            ]
                        ]
                    )
                )
            )

            await self.brick_db.delete()
        return None
