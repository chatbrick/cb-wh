import logging

import blueforge.apis.telegram as tg
import requests
import datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, \
    Element, GenericTemplate, PostBackButton, ButtonTemplate

from chatbrick.util import get_items_from_xml

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_11_001.png'


class Holiday(object):
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
                    text='한국천문연구원에서 제공하는 "쉬는날 조회 서비스"에요.'
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_11_002.png',
                                    title='이번달에 쉬는날',
                                    subtitle='이번달에 공휴일을 알려드려요.',
                                    buttons=[
                                        PostBackButton(
                                            title='이번달조회',
                                            payload='brick|holiday|this_month'
                                        )
                                    ]
                                ),
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_11_002.png',
                                    title='지정한 년/월에 쉬는날',
                                    subtitle='입력하신 년/월의 공휴일을 알려드려요.',
                                    buttons=[
                                        PostBackButton(
                                            title='조회할 년/월 입력',
                                            payload='brick|holiday|specify_month'
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'specify_month':
            await self.brick_db.save()

        elif command == 'final' or command == 'next_month' or command == 'prev_month' or command == 'this_month':
            if command == 'this_month':
                await self.brick_db.save(is_pass=True)

            input_data = await self.brick_db.get()
            year = input_data['store'][0]['value']
            month = input_data['store'][1]['value']

            if year.strip() == 'pass' or month.strip() == 'pass':
                today = datetime.datetime.today()
                year = today.year
                month = today.month

            if command == 'next_month':
                plus_month = dateutil.parser.parse('%s %s 01' % (year, month)) + relativedelta(months=1)
                year = plus_month.year
                month = plus_month.month

            elif command == 'prev_month':
                plus_month = dateutil.parser.parse('%s %s 01' % (year, month)) - relativedelta(months=1)
                year = plus_month.year
                month = plus_month.month

            if command == 'next_month' or command == 'prev_month':
                rslt = await self.brick_db.update({
                    '$set':
                        {
                            'store.0.value': str(year),
                            'store.1.value': str(month)
                        }
                })
                logger.info(rslt)

            res = requests.get(
                url='http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?serviceKey=%s&solYear=%s&solMonth=%s' % (
                    input_data['data']['api_key'], year, str(month).rjust(2, '0')))

            items = get_items_from_xml(res)

            if len(items) == 0:
                if command == 'prev_month' or command == 'this_month':
                    send_message = [
                        Message(
                            attachment=TemplateAttachment(
                                payload=ButtonTemplate(
                                    text='%s-%s\n조회된 결과가 없습니다.' % (year, month),
                                    buttons=[
                                        PostBackButton(
                                            title='이전달 조회',
                                            payload='brick|holiday|prev_month'
                                        ),
                                        PostBackButton(
                                            title='다음달 조회',
                                            payload='brick|holiday|next_month'
                                        )
                                    ]
                                )
                            )
                        )
                    ]
                else:
                    send_message = [
                        Message(
                            text='조회된 결과가 없습니다.',
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 달 조회하기',
                                        payload='brick|holiday|get_started'
                                    )
                                ]
                            )
                        )
                    ]

            else:
                sending_message = []
                for item in items:
                    sending_message.append('날짜: {locdate}\n공휴일 유무: {isHoliday}\n공휴일 내용: {dateName}'.format(**item))

                send_message = [
                    Message(
                        attachment=TemplateAttachment(
                            payload=ButtonTemplate(
                                text='\n\n'.join(sending_message),
                                buttons=[
                                    PostBackButton(
                                        title='이전달 조회',
                                        payload='brick|holiday|prev_month'
                                    ),
                                    PostBackButton(
                                        title='다음달 조회',
                                        payload='brick|holiday|next_month'
                                    )
                                ]
                            )
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
                    text='한국천문연구원에서 제공하는 "쉬는날 조회 서비스"에요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='이번달에 쉬는날',
                                    callback_data='BRICK|holiday|this_month'
                                ),
                                tg.CallbackButton(
                                    text='조회할 년/월 입력',
                                    callback_data='BRICK|holiday|specify_month'
                                )
                            ]
                        ]
                    )
                )

            ]
            await self.fb.send_messages(send_message)
        elif command == 'specify_month':
            await self.brick_db.save()
        elif command == 'final' or command == 'next_month' or command == 'prev_month' or command == 'this_month':
            if command == 'this_month':
                await self.brick_db.save(is_pass=True)

            input_data = await self.brick_db.get()
            year = input_data['store'][0]['value']
            month = input_data['store'][1]['value']

            if year.strip() == 'pass' or month.strip() == 'pass':
                today = datetime.datetime.today()
                year = today.year
                month = today.month

            if command == 'next_month':
                plus_month = dateutil.parser.parse('%s %s 01' % (year, month)) + relativedelta(months=1)
                year = plus_month.year
                month = plus_month.month

            elif command == 'prev_month':
                plus_month = dateutil.parser.parse('%s %s 01' % (year, month)) - relativedelta(months=1)
                year = plus_month.year
                month = plus_month.month

            if command == 'next_month' or command == 'prev_month':
                rslt = await self.brick_db.update({
                    '$set':
                        {
                            'store.0.value': str(year),
                            'store.1.value': str(month)
                        }
                })
                logger.info(rslt)

            res = requests.get(
                url='http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?serviceKey=%s&solYear=%s&solMonth=%s' % (
                    input_data['data']['api_key'], year, str(month).rjust(2, '0')))

            items = get_items_from_xml(res)

            if len(items) == 0:
                if command == 'prev_month' or command == 'this_month':
                    send_message = [
                        tg.SendMessage(
                            text='*%s년 %s월*\n조회된 결과가 없습니다.' % (year, month),
                            parse_mode='Markdown',
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='이전달 조회',
                                            callback_data='BRICK|holiday|prev_month'
                                        ),
                                        tg.CallbackButton(
                                            text='이전달 조회',
                                            callback_data='BRICK|holiday|next_month'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
                else:
                    send_message = [
                        tg.SendMessage(
                            text='*%s년 %s월*\n조회된 결과가 없습니다.' % (year, month),
                            parse_mode='Markdown',
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 달 조회하기',
                                            callback_data='BRICK|holiday|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
            else:
                sending_message = []
                for item in items:
                    sending_message.append('*{locdate}*\n공휴일 유무: {isHoliday}\n공휴일 내용: {dateName}'.format(**item))


                send_message = [
                    tg.SendMessage(
                        text='\n\n'.join(sending_message),
                        parse_mode='Markdown',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='이전달 조회',
                                        callback_data='BRICK|holiday|prev_month'
                                    )
                                ],
                                [
                                    tg.CallbackButton(
                                        text='다음달 조회',
                                        callback_data='BRICK|holiday|next_month'
                                    )
                                ]
                            ]
                        )
                    )
                ]

            await self.fb.send_messages(send_message)
        return None
