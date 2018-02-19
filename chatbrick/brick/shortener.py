import logging
import time
import blueforge.apis.telegram as tg
import requests
import urllib.parse
import json

from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, \
    GenericTemplate, Element, PostBackButton, ButtonTemplate, UrlButton

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_20_001.png'


class Shortener(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    async def get_short_url(api_key, long_url):
        face_detection = requests.post(
            'https://www.googleapis.com/urlshortener/v1/url?%s' % urllib.parse.urlencode({
                'key': api_key
            }),
            data=json.dumps({
                'longUrl': long_url
            }),
            headers={
                'Content-Type': 'application/json',
            }
        )

        return face_detection.json()

    @staticmethod
    async def get_long_url(api_key, short_url):
        face_detection = requests.get(
            'https://www.googleapis.com/urlshortener/v1/url?%s' % urllib.parse.urlencode({
                'key': api_key,
                'shortUrl': short_url
            }),
            headers={
                'Content-Type': 'application/json',
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
                    text='Google에서 제공하는 "URL 단축 서비스"에요.'
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_02_002.png',
                                    title='URL 단축',
                                    subtitle='긴 URL을 짧은 URL로 변경해줍니다.',
                                    buttons=[
                                        PostBackButton(
                                            title='선택하기',
                                            payload='brick|shortener|short'
                                        )
                                    ]
                                ),
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_02_002.png',
                                    title='단축 URL 정보보기',
                                    subtitle='단축된 URL의 본래의 주소를 조회합니다.',
                                    buttons=[
                                        PostBackButton(
                                            title='선택하기',
                                            payload='brick|shortener|long'
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'short' or command == 'long':
            await self.brick_db.save()
            await self.brick_db.update({'$set': {'store.1.value': command}})
        elif command == 'final':
            input_data = await self.brick_db.get()
            url = input_data['store'][0]['value']
            request_type = input_data['store'][1]['value']

            if request_type == 'short':
                result = await Shortener.get_short_url(input_data['data']['api_key'], url)
            elif request_type == 'long':
                result = await Shortener.get_long_url(input_data['data']['api_key'], url)

            if 'error' in result:
                send_message = [
                    Message(
                        text='에러가 발생했습니다.\n다시 시도해주세요.'
                    )
                ]

                logger.error(result)
            else:
                if request_type == 'short':
                    send_message = [
                        Message(
                            attachment=TemplateAttachment(
                                payload=ButtonTemplate(
                                    text='단축된 URL은 %s 입니다.' % result['id'],
                                    buttons=[
                                        UrlButton(
                                            title='바로가기',
                                            url=result['id']
                                        )
                                    ]
                                )
                            ),
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 URL 단축하기',
                                        payload='brick|shortener|short'
                                    )
                                ]
                            )
                        )
                    ]
                elif request_type == 'long':
                    send_message = [
                        Message(
                            attachment=TemplateAttachment(
                                payload=ButtonTemplate(
                                    text='본래의 URL은 %s 입니다.' % result['longUrl'],
                                    buttons=[
                                        UrlButton(
                                            title='바로가기',
                                            url=result['longUrl']
                                        )
                                    ]
                                )
                            ),
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 단축 URL 정보보기',
                                        payload='brick|shortener|long'
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
