import logging
import urllib.parse
import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

from chatbrick.util import get_items_from_xml, UNKNOWN_ERROR_MSG

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_14_001.png'


class Electric(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    async def facebook(self, command):
        if command == 'get_started':
            send_message = [
                Message(
                    attachment=ImageAttachment(
                        url=BRICK_DEFAULT_IMAGE
                    )
                ),
                Message(
                    text='한국전력공사에서 제공하는 "전기차충전소 조회 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            place = input_data['store'][0]['value']
            res = requests.get(
                url='http://openapi.kepco.co.kr/service/evInfoService/getEvSearchList?serviceKey=%s&numOfRows=100&pageSize=100&pageNo=1&startPage=1&addr=%s' % (
                    input_data['data']['api_key'], urllib.parse.quote_plus(place)))

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
                                        title='다른 지역검색',
                                        payload='brick|electric|get_started'
                                    )
                                ]
                            )
                        )
                    ]
                else:
                    sending_message = ''
                    for item in items:
                        sending_message += '충전소명 : {csNm}\n충전소ID : {cpId}\n충전타입 : {cpNm}\n상태 : {cpStat}\n주소 : {addr}\n\n'.format(
                            **item)

                    send_message = [
                        Message(
                            text=sending_message,
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 충전소 검색',
                                        payload='brick|electric|get_started'
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
                    text='한국전력공사에서 제공하는 "전기차충전소 조회 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            place = input_data['store'][0]['value']
            res = requests.get(
                url='http://openapi.kepco.co.kr/service/evInfoService/getEvSearchList?serviceKey=%s&numOfRows=100&pageSize=100&pageNo=1&startPage=1&addr=%s' % (
                    input_data['data']['api_key'], urllib.parse.quote_plus(place)))

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
                    sending_message = ''
                    for item in items:
                        sending_message += '*{csNm}*\n충전소ID : {cpId}\n충전타입 : {cpNm}\n상태 : {cpStat}\n주소 : {addr}\n[구글지도](https://www.google.com/maps/?q={lat},{longi})\n\n'.format(
                            **item)
                    send_message = [
                        tg.SendMessage(
                            text=sending_message,
                            parse_mode='Markdown',
                            disable_web_page_preview=True,
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 충전소 검색',
                                            callback_data='BRICK|electric|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]

            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
