import logging

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, \
    GenericTemplate, Element, PostBackButton

from chatbrick.util import get_items_from_xml

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_13_001.png'
GATE_INFO = {
    '0': '원할',
    '1': '보통',
    '2': '혼잡',
    '3': '매우혼잡',
    '9': '종료'
}


class Icn(object):
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
                    text='인천국제공항공사에서 제공하는 "출국장 대기인원 조회 서비스"에요.'
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_13_002.png',
                                    title='제 1여객터미널',
                                    subtitle='제 1여객터미널의 게이트별 대기인원을 알려드려요.',
                                    buttons=[
                                        PostBackButton(
                                            title='1여객터미널 조회',
                                            payload='brick|icn|1'
                                        )
                                    ]
                                ),
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_13_002.png',
                                    title='제 2여객터미널',
                                    subtitle='제 2여객터미널의 게이트별 대기인원을 알려드려요.',
                                    buttons=[
                                        PostBackButton(
                                            title='2여객터미널 조회',
                                            payload='brick|icn|2'
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == '1' or command == '2':
            input_data = await self.brick_db.get()
            res = requests.get(
                url='http://openapi.airport.kr/openapi/service/StatusOfDepartures/getDeparturesCongestion?serviceKey=%s&terno=%s' % (
                    input_data['data']['api_key'], command), headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'})

            items = get_items_from_xml(res)
            if command == '1':
                the_other = '2'
            else:
                the_other = '1'

            raw_data = items[0]
            sending_message = '제 {terno} 여객터미널\n조회날짜 : {cgtdt}\n조회시간 : {cgthm}'.format(**raw_data)

            if command == '1':
                sending_message += '\n2번 출국장: %s명 (%s)' % (raw_data['gateinfo1'], GATE_INFO[raw_data['gate1']])
                sending_message += '\n3번 출국장: %s명 (%s)' % (raw_data['gateinfo2'], GATE_INFO[raw_data['gate2']])
                sending_message += '\n4번 출국장: %s명 (%s)' % (raw_data['gateinfo3'], GATE_INFO[raw_data['gate3']])
                sending_message += '\n5번 출국장: %s명 (%s)' % (raw_data['gateinfo4'], GATE_INFO[raw_data['gate4']])
            elif command == '2':
                sending_message += '\n1번 출국장: %s명 (%s)' % (raw_data['gateinfo1'], GATE_INFO[raw_data['gate1']])
                sending_message += '\n2번 출국장: %s명 (%s)' % (raw_data['gateinfo2'], GATE_INFO[raw_data['gate2']])

            send_message = [
                Message(
                    text=sending_message,
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyTextItem(
                                title='새로고침',
                                payload='brick|icn|%s' % command
                            ),
                            QuickReplyTextItem(
                                title='제%s여객터미널 조회' % the_other,
                                payload='brick|icn|%s' % the_other
                            )
                        ]
                    )
                )
            ]

            await self.fb.send_messages(send_message)
        return None

    async def telegram(self, command):
        if command == 'get_started':
            send_message = [
                tg.SendPhoto(
                    photo=BRICK_DEFAULT_IMAGE
                ),
                tg.SendMessage(
                    text='인천국제공항공사에서 제공하는 "출국장 대기인원 조회 서비스"에요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='제1여객터미널',
                                    callback_data='BRICK|icn|1'
                                ),
                                tg.CallbackButton(
                                    text='제2여객터미널',
                                    callback_data='BRICK|icn|2'
                                )
                            ]
                        ]
                    )
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == '1' or command == '2':
            input_data = await self.brick_db.get()
            res = requests.get(
                url='http://openapi.airport.kr/openapi/service/StatusOfDepartures/getDeparturesCongestion?serviceKey=%s&terno=%s' % (
                    input_data['data']['api_key'], command), headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'})

            items = get_items_from_xml(res)
            if command == '1':
                the_other = '2'
            else:
                the_other = '1'

            raw_data = items[0]
            sending_message = '*제 {terno} 여객터미널*\n조회날짜 : {cgtdt}\n조회시간 : {cgthm}'.format(**raw_data)

            if command == '1':
                sending_message += '\n2번 출국장: %s명 (%s)' % (raw_data['gateinfo1'], GATE_INFO[raw_data['gate1']])
                sending_message += '\n3번 출국장: %s명 (%s)' % (raw_data['gateinfo2'], GATE_INFO[raw_data['gate2']])
                sending_message += '\n4번 출국장: %s명 (%s)' % (raw_data['gateinfo3'], GATE_INFO[raw_data['gate3']])
                sending_message += '\n5번 출국장: %s명 (%s)' % (raw_data['gateinfo4'], GATE_INFO[raw_data['gate4']])
            elif command == '2':
                sending_message += '\n1번 출국장: %s명 (%s)' % (raw_data['gateinfo1'], GATE_INFO[raw_data['gate1']])
                sending_message += '\n2번 출국장: %s명 (%s)' % (raw_data['gateinfo2'], GATE_INFO[raw_data['gate2']])

            send_message = [
                tg.SendMessage(
                    text=sending_message,
                    parse_mode='Markdown',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='새로고침',
                                    callback_data='BRICK|icn|%s' % command
                                )
                            ],
                            [
                                tg.CallbackButton(
                                    text='제%s여객터미널 조회' % the_other,
                                    callback_data='BRICK|icn|%s' % the_other
                                )
                            ]
                        ]
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        return None
