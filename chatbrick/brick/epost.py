import logging

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_06_001.png'


class EPost(object):
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
                    text='과학기술정보통신부 우정사업본부에서 제공하는 "우체국택배조회 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()

        elif command == 'final':
            input_data = await self.brick_db.get()
            delivery_tracking_code = input_data['store'][0]['value']

            res = requests.get(
                url='http://openapi.epost.go.kr/trace/retrieveLongitudinalService/retrieveLongitudinalService/getLongitudinalDomesticList?_type=json&serviceKey=%s&rgist=%s' % (
                    input_data['data']['api_key'], delivery_tracking_code))

            parsed_data = res.json()
            items = []
            if parsed_data.get('LongitudinalDomesticListResponse', False):

                if parsed_data['LongitudinalDomesticListResponse']['cmmMsgHeader']['successYN'] == 'Y':
                    if parsed_data['LongitudinalDomesticListResponse'].get('longitudinalDomesticList', False):
                        if type(parsed_data['LongitudinalDomesticListResponse']['longitudinalDomesticList']) is dict:
                            items.append(parsed_data['LongitudinalDomesticListResponse']['longitudinalDomesticList'])
                        else:
                            items = parsed_data['LongitudinalDomesticListResponse']['longitudinalDomesticList']
                    tracking_status = '받는분: {addrseNm} / 보내는분: {applcntNm}\n배송상태: {dlvySttus} ({dlvyDe})\n진행상황:\n'.format(
                        **parsed_data['LongitudinalDomesticListResponse'])

                    if len(items) == 0:
                        tracking_status += '상태 기록 없음'
                    else:
                        for item in items:
                            tracking_status += '{dlvyDate}  {dlvyTime}  {nowLc} {processSttus}  {detailDc}\n'.format(
                                **item)
                    send_message = [
                        Message(
                            text=tracking_status,
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 운송장번호조회',
                                        payload='brick|epost|get_started'
                                    )
                                ]
                            )
                        )
                    ]
                else:
                    send_message = [
                        Message(
                            text='에러코드: {returnCode}\n에러메시지: {errMsg}'.format(
                                **parsed_data['LongitudinalDomesticListResponse']['cmmMsgHeader'],
                            ),
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 운송장번호조회',
                                        payload='brick|epost|get_started'
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
                    text='과학기술정보통신부 우정사업본부에서 제공하는 "우체국택배조회 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            delivery_tracking_code = input_data['store'][0]['value']

            res = requests.get(
                url='http://openapi.epost.go.kr/trace/retrieveLongitudinalService/retrieveLongitudinalService/getLongitudinalDomesticList?_type=json&serviceKey=%s&rgist=%s' % (
                    input_data['data']['api_key'], delivery_tracking_code))

            parsed_data = res.json()
            items = []


            if parsed_data.get('LongitudinalDomesticListResponse', False):

                if parsed_data['LongitudinalDomesticListResponse']['cmmMsgHeader']['successYN'] == 'Y':
                    if parsed_data['LongitudinalDomesticListResponse'].get('longitudinalDomesticList', False):
                        if type(parsed_data['LongitudinalDomesticListResponse']['longitudinalDomesticList']) is dict:
                            items.append(parsed_data['LongitudinalDomesticListResponse']['longitudinalDomesticList'])
                        else:
                            items = parsed_data['LongitudinalDomesticListResponse']['longitudinalDomesticList']
                    tracking_status = '받는분: {addrseNm} / 보내는분: {applcntNm}\n배송상태: *{dlvySttus}* ({dlvyDe})\n진행상황:\n'.format(
                        **parsed_data['LongitudinalDomesticListResponse'])

                    if len(items) == 0:
                        tracking_status += '상태 기록 없음'
                    else:
                        for item in items:
                            tracking_status += '{dlvyDate}  {dlvyTime}  {nowLc} {processSttus}  {detailDc}\n'.format(
                                **item)

                        send_message = [
                            tg.SendMessage(
                                text=tracking_status,
                                parse_mode='Markdown',
                                reply_markup=tg.MarkUpContainer(
                                    inline_keyboard=[
                                        [
                                            tg.CallbackButton(
                                                text='다른 운송장번호조회',
                                                callback_data='BRICK|epost|get_started'
                                            )
                                        ]
                                    ]
                                )
                            )
                        ]
                else:
                    send_message = [
                        tg.SendMessage(
                            text='에러코드: {returnCode}\n에러메시지: {errMsg}'.format(
                                **parsed_data['LongitudinalDomesticListResponse']['cmmMsgHeader']),
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 운송장번호조회',
                                            callback_data='BRICK|epost|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]

            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
