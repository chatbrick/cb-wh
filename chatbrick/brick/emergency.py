import logging

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

from chatbrick.util import get_items_from_xml

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_10_001.png'


class Emergency(object):
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
                    text='중앙응급의료센터에서 제공하는 "응급실검색 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            state = input_data['store'][0]['value']
            town = input_data['store'][1]['value']
            res = requests.get(
                url='http://apis.data.go.kr/B552657/ErmctInfoInqireService/getEgytListInfoInqire?serviceKey=%s&Q0=%s&Q1=%s&ORD=NAME&pageNo=1&startPage=1&numOfRows=3&pageSize=3' % (
                    input_data['data']['api_key'], state, town))

            items = get_items_from_xml(res)

            if len(items) == 0:
                send_message = [
                    Message(
                        text='조회된 결과가 없습니다.',
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 지역검색',
                                    payload='brick|emergency|get_started'
                                )
                            ]
                        )
                    )
                ]
            else:
                send_message = [
                    Message(
                        text='조회된 결과에요'
                    ),
                    Message(
                        text='{dutyName}\n{dutyEmclsName}\n{dutyAddr}\n{dutyTel1}\n{dutyTel3}'.format(
                            **items[0]),
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 지역검색',
                                    payload='brick|emergency|get_started'
                                )
                            ]
                        )
                    )
                ]
                if len(items) > 1:
                    for surplus_item in items[1:]:
                        send_message.insert(1, Message(
                            text='{dutyName}\n{dutyEmclsName}\n{dutyAddr}\n{dutyTel1}\n{dutyTel3}'.format(
                                **surplus_item)
                        )
                                            )

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
                    text='중앙응급의료센터에서 제공하는 "응급실검색 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            state = input_data['store'][0]['value']
            town = input_data['store'][1]['value']
            res = requests.get(
                url='http://apis.data.go.kr/B552657/ErmctInfoInqireService/getEgytListInfoInqire?serviceKey=%s&Q0=%s&Q1=%s&ORD=NAME&pageNo=1&startPage=1&numOfRows=3&pageSize=3' % (
                    input_data['data']['api_key'], state, town))

            items = get_items_from_xml(res)

            if len(items) == 0:
                send_message = [
                    tg.SendMessage(
                        text='조회된 결과가 없습니다.'
                    )
                ]
            else:
                send_message = [
                    tg.SendMessage(
                        text='조회된 결과에요.'
                    ),
                    tg.SendMessage(
                        text='*{dutyName}*\n{dutyEmclsName}\n{dutyAddr}\n{dutyTel1}\n{dutyTel3}'.format(
                            **items[0]),
                        parse_mode='Markdown',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다른 지역검색',
                                        callback_data='BRICK|emergency|get_started'
                                    )
                                ]
                            ]
                        )
                    )
                ]
                if len(items) > 1:
                    for surplus_item in items[1:]:
                        send_message.insert(1, tg.SendMessage(
                            text='*{dutyName}*\n{dutyEmclsName}\n{dutyAddr}\n{dutyTel1}\n{dutyTel3}'.format(
                                **surplus_item),
                            parse_mode='Markdown'
                        )
                                            )
            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
