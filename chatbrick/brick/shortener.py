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
    async def get_short_url(client_id, client_secret, long_url):
        face_detection = requests.get(
            'https://openapi.naver.com/v1/util/shorturl?%s' % urllib.parse.urlencode({
                'url': long_url
            }),
            headers={
                'Content-Type': 'application/json',
                'X-Naver-Client-Id': client_id,
                'X-Naver-Client-Secret': client_secret,
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
            #         text='Naver Developers에서 제공하는 "URL 줄이기 서비스"에요.'
            #     ),
            #     Message(
            #         attachment=TemplateAttachment(
            #             payload=GenericTemplate(
            #                 elements=[
            #                     Element(
            #                         image_url='https://www.chatbrick.io/api/static/brick/img_brick_23_002.png',
            #                         title='URL 줄이기',
            #                         subtitle='너무 길었던 URL을 줄여드려요.',
            #                         buttons=[
            #                             PostBackButton(
            #                                 title='줄이기',
            #                                 payload='brick|shortener|short'
            #                             )
            #                         ]
            #                     )
            #                 ]
            #             )
            #         )
            #     )
            # ]
            send_message = [
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(image_url=BRICK_DEFAULT_IMAGE,
                                        title='URL 줄이기 서비스',
                                        subtitle='Naver Developers에서 제공하는 "URL 줄이기 서비스"에요.')
                            ]
                        )
                    )
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
                                )
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'short':
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            url = input_data['store'][0]['value']

            result = await Shortener.get_short_url(input_data['data']['client_id'],
                                                   input_data['data']['client_secret'], url)

            if result.get('errorCode', False):
                send_message = [
                    Message(
                        text='에러가 발생했습니다.\n다시 시도해주세요.'
                    )
                ]

                logger.error(result)
            else:
                send_message = [
                    Message(
                        text='줄여진 URL 결과에요.'
                    ),
                    Message(
                        text='%s' % result['result'].get('url', ''),
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
                    text='Naver Developers에서 제공하는 "URL 줄이기 서비스"에요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='URL 줄이기',
                                    callback_data='BRICK|shortener|short'
                                )
                            ]
                        ]
                    )
                )

            ]
            await self.fb.send_messages(send_message)
        elif command == 'short':
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            url = input_data['store'][0]['value']

            result = await Shortener.get_short_url(input_data['data']['client_id'],
                                                   input_data['data']['client_secret'], url)

            if result.get('errorCode', False):
                send_message = [
                    tg.SendMessage(
                        text='에러가 발생했습니다.\n다시 시도해주세요.'
                    )
                ]

                logger.error(result)
            else:
                send_message = [
                    tg.SendMessage(
                        text='줄여진 URL 결과에요.'
                    ),
                    tg.SendMessage(
                        text='%s' % result['result'].get('url', ''),
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

            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
