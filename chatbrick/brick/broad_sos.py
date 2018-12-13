import logging

import blueforge.apis.telegram as tg
import urllib.parse
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, GenericTemplate, Element

from chatbrick.util import get_items_from_xml, remove_html_tag, UNKNOWN_ERROR_MSG
import time

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_05_001.png'


class BroadSos(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    async def facebook(self, command):
        if command == 'get_started':
            # send_message = [
            #     Message(
            #         attachment=ImageAttachment(
            #             url=BRICK_DEFAULT_IMAGE
            #         )
            #     ),
            #     Message(
            #         text='외교부에서 제공하는 "해외에서 SOS 서비스"에요.'
            #     )
            # ]
            send_message = [
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(image_url=BRICK_DEFAULT_IMAGE,
                                        title='해외에서 SOS 서비스',
                                        subtitle='외교부에서 제공하는 "해외에서 SOS 서비스"에요.')
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            country = input_data['store'][0]['value']
            res = requests.get(
                url='http://apis.data.go.kr/1262000/ContactService/getContactList?serviceKey=%s&numOfRows=10&pageSize=10&pageNo=1&startPage=1&countryName=%s' % (
                    input_data['data']['api_key'], urllib.parse.quote_plus(country)))

            items = get_items_from_xml(res)

            if type(items) is dict:
                if items.get('code', '00') == '99' or items.get('code', '00') == '30':
                    send_message = [
                        Message(
                            text='chatbrick 홈페이지에 올바르지 않은 API key를 입력했어요. 다시 한번 확인해주세요.',
                        )
                    ]
                else:
                    send_message = [
                        Message(
                            text=UNKNOWN_ERROR_MSG
                        )
                    ]
            else:
                if len(items) == 0:
                    send_message = [
                        Message(
                            text='조회된 결과가 없습니다.',
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 국가조회',
                                        payload='brick|broad_sos|get_started'
                                    )
                                ]
                            )
                        )
                    ]
                else:
                    sending_message = []
                    for item in items:
                        item['contact'] = remove_html_tag(item['contact'])
                        sending_message.append('국가 : {countryName}\n구분 : {continent}\n내용 : \n{contact}'.format(**item))

                    send_message = [
                        Message(
                            text='조회된 결과에요'
                        ),
                        Message(
                            text='\n\n'.join(sending_message),
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 국가조회',
                                        payload='brick|broad_sos|get_started'
                                    )
                                ]
                            )
                        )
                    ]

            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None

    async def telegram(self, command):
        if command == 'get_started':
            send_message = [
                tg.SendPhoto(
                    photo=BRICK_DEFAULT_IMAGE
                ),
                tg.SendMessage(
                    text='외교부에서 제공하는 "해외에서 SOS 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            country = input_data['store'][0]['value']

            res = requests.get(
                url='http://apis.data.go.kr/1262000/ContactService/getContactList?serviceKey=%s&numOfRows=10&pageSize=10&pageNo=1&startPage=1&countryName=%s' % (
                    input_data['data']['api_key'], urllib.parse.quote_plus(country)))

            items = get_items_from_xml(res)

            if type(items) is dict:
                if items.get('code', '00') == '99' or items.get('code', '00') == '30':
                    send_message = [
                        tg.SendMessage(
                            text='chatbrick 홈페이지에 올바르지 않은 API key를 입력했어요. 다시 한번 확인해주세요.',
                        )
                    ]
                else:
                    send_message = [
                        tg.SendMessage(
                            text=UNKNOWN_ERROR_MSG
                        )
                    ]
            else:
                if len(items) == 0:
                    send_message = [
                        tg.SendMessage(
                            text='조회된 결과가 없습니다.'
                        )
                    ]
                else:
                    sending_message = []
                    for item in items:
                        item['contact'] = remove_html_tag(item['contact'])
                        sending_message.append('*{countryName}*\n구분 : {continent}\n내용 : \n{contact}'.format(**item))

                    send_message = [
                        tg.SendMessage(
                            text='\n\n'.join(sending_message),
                            parse_mode='Markdown',
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 국가조회',
                                            callback_data='BRICK|broad_sos|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
