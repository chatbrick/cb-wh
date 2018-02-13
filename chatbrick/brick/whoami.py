import logging
import time
import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_20_001.png'


class Who(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    async def get_data(brick_data, url):
        raw_image = requests.get(url)
        face_detection = requests.post(
            'https://openapi.naver.com/v1/vision/celebrity',
            files={
                'image': raw_image.content
            },
            headers={
                'X-Naver-Client-Id': brick_data['client_id'],
                'X-Naver-Client-Secret': brick_data['client_secret']
            }
        )

        return face_detection.json()

    async def facebook(self, command):
        if command == 'get_started':
            send_message = [
                Message(
                    attachment=ImageAttachment(
                        url=BRICK_DEFAULT_IMAGE
                    )
                ),
                Message(
                    text='Naver Developers에서 제공하는 "사진속 유명인 찾기 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            contents = input_data['store'][0]['value']
            start = int(time.time() * 1000)
            parsed_result = await Who.get_data(input_data['data'], contents)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'who',
                'platform': 'facebook',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '페이스북,네이버,API,누구냐넌',
                'data': parsed_result,
                'remark': '누구냐넌 네이버 API 호출'
            })
            logger.debug(parsed_result)

            if parsed_result.get('faces', False):
                if len(parsed_result['faces']) == 0:
                    send_message = [
                        Message(
                            text='탐지된 얼굴이 없습니다.'
                        )
                    ]
                else:
                    send_message = [
                        Message(
                            text='조회된 결과에요.\n1이 만점이에요.\n예) 0.37508 은 37% 확률을 말하는거에요. 56%정도면 거의 동일인이라고 볼 수 있어요.'
                        ),
                        Message(
                            text='두구두구!!\n사진 속의 사람은 {celebrity[confidence]}의 확률로 {celebrity[value]}이네요.'.format(
                                **parsed_result['faces'][0]),
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 사진분석',
                                        payload='brick|who|get_started'
                                    )
                                ]
                            )
                        )
                    ]
            else:
                send_message = [
                    Message(
                        text='에러코드: {errorCode}\n에러메시지: {errorMessage}'.format(**parsed_result),
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 사진분석',
                                    payload='brick|who|get_started'
                                )
                            ]
                        )
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
                    text='Naver Developers에서 제공하는 "사진속 유명인 찾기 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            logger.info(self.fb.send_action('goSendMessage'))
            input_data = await self.brick_db.get()
            contents = input_data['store'][0]['value']
            start = int(time.time() * 1000)
            parsed_result = await Who.get_data(input_data['data'], contents)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'who',
                'platform': 'telegram',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '텔레그램,네이버,API,누구냐넌',
                'data': parsed_result,
                'remark': '누구냐넌 네이버 API 호출'
            })
            logger.debug(parsed_result)

            if parsed_result.get('faces', False):
                if len(parsed_result['faces']) == 0:
                    send_message = [
                        tg.SendMessage(
                            text='탐지된 얼굴이 없습니다.'
                        )
                    ]
                else:
                    send_message = [
                        tg.SendMessage(
                            text='조회된 결과에요.\n1이 만점이에요.\n예) 0.37508 은 37% 확률을 말하는거에요. 56%정도면 거의 동일인이라고 볼 수 있어요.'
                        ),
                        tg.SendMessage(
                            text='두구두구!!\n사진 속의 사람은 {celebrity[confidence]}의 확률로 {celebrity[value]}이네요.'.format(
                                **parsed_result['faces'][0]),
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 사진분석',
                                            callback_data='BRICK|who|get_started'

                                        )
                                    ]
                                ]
                            )
                        )
                    ]
            else:
                send_message = [
                    tg.SendMessage(
                        text='에러코드: {errorCode}\n에러메시지: {errorMessage}'.format(**parsed_result),
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다른 사진분석',
                                        callback_data='BRICK|who|get_started'

                                    )
                                ]
                            ]
                        )
                    )
                ]
            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
