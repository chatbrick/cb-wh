import logging
import urllib.parse
from datetime import datetime

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem
import time

from blueforge.apis.facebook import TemplateAttachment, Element, GenericTemplate

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_22_001.png'
CURRENCY_UNIT = {
    '01': 'USD',
    '02': 'JPY(100)',
    '03': 'CNH',
    '04': 'EUR',
    '05': 'GBP',
    '06': 'HKD',
    '07': 'SGD',
    '08': 'THB',
    '09': 'AUD',
    '10': 'CAD',
    '11': 'CHF',
    '12': 'NZD'
}


class Currency(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    async def get_data(api_key):
        today = datetime.today()
        face_detection = requests.post(
            'https://www.koreaexim.go.kr/site/program/financial/exchangeJSON?%s' % urllib.parse.urlencode({
                'authkey': api_key,
                'searchdate': '%d%02d%02d' % (today.year, today.month, today.day),
                'data': 'AP01'
            }),
            headers={
                'Content-Type': 'application/json',
            }
        )

        return face_detection.json()

    async def facebook(self, command):
        if command == 'get_started':
            # send_message = [
            #     Message(
            #         attachment=ImageAttachment(
            #             url=BRICK_DEFAULT_IMAGE
            #         )
            #     ),
            #     Message(
            #         text='한국수출입은행에서 제공하는 "환율정보 서비스"에요.'
            #     ),
            #     Message(
            #         text='chatbrick에서 제공하는 금융정보는 한국수출입은행으로부터 받는 정보로 투자 참고사항이며, 오류가 발생하거나 지연될 수 있습니다.\nchatbrick은 제공된 정보에 의한 투자결과에 법적책임을 지지 않습니다. 게시된 정보는 무단으로 배포할 수 없습니다.'
            #     )
            # ]
            send_message = [
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(image_url=BRICK_DEFAULT_IMAGE,
                                        title='환율정보 서비스',
                                        subtitle='한국수출입은행에서 제공하는 "환율정보 서비스"에요.')
                            ]
                        )
                    )
                ),
                Message(
                    text='chatbrick에서 제공하는 금융정보는 한국수출입은행으로부터 받는 정보로 투자 참고사항이며, 오류가 발생하거나 지연될 수 있습니다.\nchatbrick은 제공된 정보에 의한 투자결과에 법적책임을 지지 않습니다. 게시된 정보는 무단으로 배포할 수 없습니다.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            currency = input_data['store'][0]['value']

            rslt = await Currency.get_data(input_data['data']['api_key'])

            if len(rslt) == 0:
                send_message = [
                    Message(
                        text='금일의 통화 정보가 없습니다.'
                    )
                ]
            else:
                send_message = []
                for money in rslt:
                    try:
                        if money['cur_unit'] == CURRENCY_UNIT['%02d' % int(currency)]:
                            send_message = [
                                Message(
                                    text='국가/통화명 : {cur_nm}\n통화코드 : {cur_unit}\n송금 받을 때 (1 {cur_nm} 기준) : {ttb}원\n송금 보낼 때 (1 {cur_nm} 기준) : {tts}원\n매매 기준율 : {deal_bas_r} 원\n장부가격 : {bkpr}\n\n년환가료율 : {yy_efee_r}\n10일환가료율 : {ten_dd_efee_r}\n서울외국환중계 매매기준율 : {kftc_deal_bas_r}\n서울외국환중계 장부가격 : {kftc_bkpr}'.format(
                                        **money),
                                    quick_replies=QuickReply(
                                        quick_reply_items=[
                                            QuickReplyTextItem(
                                                title='다른 환율정보조회',
                                                payload='brick|currency|get_started'
                                            )
                                        ]
                                    )
                                )
                            ]
                            break
                    except ValueError as ex:
                        send_message = [
                            Message(
                                text='숫자만 입력하셔야 되요.\n에러 메시지: %s' % str(ex),
                                quick_replies=QuickReply(
                                    quick_reply_items=[
                                        QuickReplyTextItem(
                                            title='다른 환율정보조회',
                                            payload='brick|currency|get_started'
                                        )
                                    ]
                                )
                            )
                        ]

                if len(send_message) == 0:
                    send_message = [
                        Message(
                            text='검색된 결과가 없습니다.'
                        )
                    ]

            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None

    async def telegram(self, command):
        if command == 'get_started':
            send_message = [
                tg.SendPhoto(
                    photo=BRICK_DEFAULT_IMAGE
                ),
                tg.SendMessage(
                    text='한국수출입은행에서 제공하는 "환율정보 서비스"에요.',
                ),
                tg.SendMessage(
                    text='chatbrick에서 제공하는 금융정보는 한국수출입은행으로부터 받는 정보로 투자 참고사항이며, 오류가 발생하거나 지연될 수 있습니다.\nchatbrick은 제공된 정보에 의한 투자결과에 법적책임을 지지 않습니다. 게시된 정보는 무단으로 배포할 수 없습니다.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            currency = input_data['store'][0]['value']

            rslt = await Currency.get_data(input_data['data']['api_key'])

            if len(rslt) == 0:
                send_message = [
                    tg.SendMessage(
                        text='금일의 통화 정보가 없습니다.'
                    )
                ]
            else:
                send_message = []
                for money in rslt:
                    try:
                        if money['cur_unit'] == CURRENCY_UNIT['%02d' % int(currency)]:
                            send_message = [
                                tg.SendMessage(
                                    text='국가/통화명 : {cur_nm}\n통화코드 : {cur_unit}\n송금 받을 때 (1 {cur_nm} 기준) : {ttb}원\n송금 보낼 때 (1 {cur_nm} 기준) : {tts}원\n매매 기준율 : {deal_bas_r} 원\n장부가격 : {bkpr}\n\n년환가료율 : {yy_efee_r}\n10일환가료율 : {ten_dd_efee_r}\n서울외국환중계 매매기준율 : {kftc_deal_bas_r}\n서울외국환중계 장부가격 : {kftc_bkpr}'.format(
                                        **money),
                                    reply_markup=tg.MarkUpContainer(
                                        inline_keyboard=[
                                            [
                                                tg.CallbackButton(
                                                    text='다른 환율정보조회',
                                                    callback_data='BRICK|currency|get_started'
                                                )
                                            ]
                                        ]
                                    )
                                )
                            ]
                            break
                    except ValueError as ex:
                        send_message = [
                            tg.SendMessage(
                                text='숫자만 입력해야 되요.\n에러 메시지: %s' % str(ex),
                                reply_markup=tg.MarkUpContainer(
                                    inline_keyboard=[
                                        [
                                            tg.CallbackButton(
                                                text='다른 환율정보조회',
                                                callback_data='BRICK|currency|get_started'
                                            )
                                        ]
                                    ]
                                )
                            )]

                if len(send_message) == 0:
                    send_message = [
                        tg.SendMessage(
                            text='검색된 결과가 없습니다.'
                        )
                    ]

            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
