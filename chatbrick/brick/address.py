import logging

import blueforge.apis.telegram as tg
import requests
import urllib.parse
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, \
    GenericTemplate, Element, PostBackButton

from chatbrick.util import get_items_from_xml

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_08_001.png'


class Address(object):
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
                    text='인터넷우체국팀에서 제공하는 "우편번호찾기 서비스"에요.'
                )
                # ),
                # Message(
                #     attachment=TemplateAttachment(
                #         payload=GenericTemplate(
                #             elements=[
                #                 Element(
                #                     image_url='https://www.chatbrick.io/api/static/brick/img_brick_08_002.png',
                #                     title='도로명주소로 찾기',
                #                     subtitle='도로명주소로 우편번호를 찾을 수 있어요.',
                #                     buttons=[
                #                         PostBackButton(
                #                             title='도로명주소로 검색',
                #                             payload='brick|address|road'
                #                         )
                #                     ]
                #                 ),
                #                 Element(
                #                     image_url='https://www.chatbrick.io/api/static/brick/img_brick_08_002.png',
                #                     title='지번주소로 찾기',
                #                     subtitle='지번주소로 우편번호를 찾을 수 있어요.',
                #                     buttons=[
                #                         PostBackButton(
                #                             title='지번주소로 검색',
                #                             payload='brick|address|old'
                #                         )
                #                     ]
                #                 )
                #             ]
                #         )
                #     )
                # )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()

        elif command == 'final':
            input_data = await self.brick_db.get()
            add_type = input_data['store'][0]['value']
            address = input_data['store'][1]['value']

            if add_type == '지번':
                a_type = 'dong'
            else:
                a_type = 'road'

            res = requests.get(
                url='http://openapi.epost.go.kr/postal/retrieveNewAdressAreaCdService/retrieveNewAdressAreaCdService/getNewAddressListAreaCd?_type=json&serviceKey=%s&searchSe=%s&srchwrd=%s&countPerPage=10&currentPage=1' % (
                    input_data['data']['api_key'], a_type, urllib.parse.quote_plus(address)))

            parsed_data = res.json()
            items = []
            if parsed_data.get('NewAddressListResponse', False):
                if parsed_data['NewAddressListResponse'].get('newAddressListAreaCd', False):
                    if type(parsed_data['NewAddressListResponse']['newAddressListAreaCd']) is dict:
                        items.append(parsed_data['NewAddressListResponse']['newAddressListAreaCd'])
                    else:
                        items = parsed_data['NewAddressListResponse']['newAddressListAreaCd']

            logger.info(items)
            items.reverse()
            if len(items) == 0:
                send_message = [
                    Message(
                        text='조회된 결과가 없습니다.',
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다시 검색하기',
                                    payload='brick|address|get_started'
                                )
                            ]
                        )
                    )
                ]
            else:
                sending_message = []
                for item in items:
                    sending_message.append('{zipNo}\n{lnmAdres}\n{rnAdres}'.format(**item))

                send_message = [
                    Message(
                        text='조회된 결과에요'
                    ),
                    Message(
                        text='\n\n'.join(sending_message),
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 우편번호검색',
                                    payload='brick|address|get_started'
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
                    text='인터넷우체국팀에서 제공하는 "우편번호찾기 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            add_type = input_data['store'][0]['value']
            address = input_data['store'][1]['value']

            if add_type == '지번':
                a_type = 'dong'
            else:
                a_type = 'road'

            res = requests.get(
                url='http://openapi.epost.go.kr/postal/retrieveNewAdressAreaCdService/retrieveNewAdressAreaCdService/getNewAddressListAreaCd?_type=json&serviceKey=%s&searchSe=%s&srchwrd=%s&countPerPage=10&currentPage=1' % (
                    input_data['data']['api_key'], a_type, urllib.parse.quote_plus(address)))

            parsed_data = res.json()
            items = []
            if parsed_data.get('NewAddressListResponse', False):
                if parsed_data['NewAddressListResponse'].get('newAddressListAreaCd', False):
                    if type(parsed_data['NewAddressListResponse']['newAddressListAreaCd']) is dict:
                        items.append(parsed_data['NewAddressListResponse']['newAddressListAreaCd'])
                    else:
                        items = parsed_data['NewAddressListResponse']['newAddressListAreaCd']

            logger.info(items)
            items.reverse()

            if len(items) == 0:
                send_message = [
                    tg.SendMessage(
                        text='조회된 결과가 없습니다.'
                    )
                ]
            else:
                sending_message = []
                for item in items:
                    sending_message.append('*{zipNo}*\n{lnmAdres}\n{rnAdres}'.format(**item))

                send_message = [
                    tg.SendMessage(
                        text='조회된 결과에요.'
                    ),
                    tg.SendMessage(
                        text='\n\n'.join(sending_message),
                        parse_mode='Markdown',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다른 우편번호검색',
                                        callback_data='BRICK|address|get_started'
                                    )
                                ]
                            ]
                        )
                    )
                ]
            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
