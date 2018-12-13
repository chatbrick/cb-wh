import logging
import time
import urllib.parse

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

from chatbrick.util import get_items_from_xml, download_and_save_image, UNKNOWN_ERROR_MSG
from blueforge.apis.facebook import TemplateAttachment, Element, GenericTemplate

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_05_001.png'


class SafeJourney(object):
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
            #         text='외교부에서 제공하는 "여행경보 조회 서비스"에요.'
            #     )
            # ]
            send_message = [
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(image_url=BRICK_DEFAULT_IMAGE,
                                        title='여행경보 조회 서비스',
                                        subtitle='외교부에서 제공하는 "여행경보 조회 서비스"에요.')
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
                url='http://apis.data.go.kr/1262000/TravelWarningService/getTravelWarningList?serviceKey=%s&numOfRows=10&pageSize=10&pageNo=1&startPage=1&countryName=%s' % (
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
                                        title='다른 국가검색',
                                        payload='brick|safe_journey|get_started'
                                    )
                                ]
                            )
                        )
                    ]
                else:
                    try:
                        send_message = [
                            Message(
                                attachment=ImageAttachment(
                                    url=download_and_save_image(items[0]['imgUrl2'])
                                ),
                                quick_replies=QuickReply(
                                    quick_reply_items=[
                                        QuickReplyTextItem(
                                            title='다른 국가검색',
                                            payload='brick|safe_journey|get_started'
                                        )
                                    ]
                                )
                            )
                        ]
                    except:
                        send_message = [
                            Message(
                                text='이미지 전송 중 오류가 발생했습니다.',
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
                    text='외교부에서 제공하는 "여행경보 조회 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            country = input_data['store'][0]['value']
            res = requests.get(
                url='http://apis.data.go.kr/1262000/TravelWarningService/getTravelWarningList?serviceKey=%s&numOfRows=10&pageSize=10&pageNo=1&startPage=1&countryName=%s' % (
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
                            text='조회된 결과가 없습니다.',
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 국가검색',
                                            callback_data='BRICK|safe_journey|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
                else:
                    try:
                        send_message = [
                            tg.SendPhoto(
                                photo=download_and_save_image(items[0]['imgUrl2']),
                                reply_markup=tg.MarkUpContainer(
                                    inline_keyboard=[
                                        [
                                            tg.CallbackButton(
                                                text='다른 국가검색',
                                                callback_data='BRICK|safe_journey|get_started'
                                            )
                                        ]
                                    ]
                                )
                            )
                        ]
                    except:
                        send_message = [
                            tg.SendMessage(
                                text='이미지 전송 중 오류가 발생했습니다.'
                            )
                        ]

            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
