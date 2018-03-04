import logging
import time
import blueforge.apis.telegram as tg
import requests
import urllib.parse
import json

from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, \
    GenericTemplate, Element, PostBackButton, ButtonTemplate, UrlButton

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_23_001.png'


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
                    text='Google에서 제공하는 "URL 줄이기 서비스"에요.'
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_23_002.png',
                                    title='URL 줄이기',
                                    subtitle='너무 길었던 URL을 줄여드려요.',
                                    buttons=[
                                        PostBackButton(
                                            title='줄이기',
                                            payload='brick|shortener|short'
                                        )
                                    ]
                                ),
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_23_002.png',
                                    title='줄여진 URL 확인',
                                    subtitle='압축된 URL을 처음 URL로 복구해드려요.',
                                    buttons=[
                                        PostBackButton(
                                            title='복구하기',
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
                            text='줄여진 URL 결과에요.'
                        ),
                        Message(
                            text='%s' % result['id'],
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 URL 줄이기',
                                        payload='brick|shortener|short'
                                    )
                                ]
                            )
                        )
                    ]
                elif request_type == 'long':
                    send_message = [
                        Message(
                            text='복구된 URL 결과에요.'
                        ),
                        Message(
                            text='%s' % result['longUrl'],
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 URL 복구하기',
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
                    text='Google에서 제공하는 "URL 줄이기 서비스"에요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='URL 줄이기',
                                    callback_data='BRICK|shortener|short'
                                ),
                                tg.CallbackButton(
                                    text='URL 복구하기',
                                    callback_data='BRICK|shortener|long'
                                )
                            ]
                        ]
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
                    tg.SendMessage(
                        text='에러가 발생했습니다.\n다시 시도해주세요.'
                    )
                ]

                logger.error(result)
            else:
                if request_type == 'short':
                    send_message = [
                        tg.SendMessage(
                            text='줄여진 URL 결과에요.'
                        ),
                        tg.SendMessage(
                            text='%s' % result['id'],
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 URL 줄이기',
                                            callback_data='BRICK|shortener|short'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
                elif request_type == 'long':
                    send_message = [
                        tg.SendMessage(
                            text='복구된 URL 결과에요.'
                        ),
                        tg.SendMessage(
                            text='%s' % result['longUrl'],
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 URL 복구하기',
                                            callback_data='BRICK|shortener|long'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]

            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
