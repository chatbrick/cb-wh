import logging
import time
import blueforge.apis.telegram as tg
import requests
import json
import operator

from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem
import urllib.parse
from blueforge.apis.facebook import TemplateAttachment, Element, GenericTemplate

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_16_001.png'

EMOTION = {
    'neutral': '중성적',
    'sadness': '슬픔',
    'contempt': '멸시',
    'surprise': '놀람',
    'anger': '분노',
    'happiness': '행복',
    'disgust': '혐오',
    'fear': '공포'
}


class Emotion(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    # @staticmethod
    # async def get_data(brick_data, url):
    #     raw_image = requests.get(url)
    #     req = requests.post(
    #         'https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize',
    #         headers={
    #             'Content-Type': 'application/octet-stream',
    #             'Ocp-Apim-Subscription-Key': brick_data['subscription']
    #
    #         },
    #         data=raw_image.content)
    #     return req.json()

    @staticmethod
    async def get_data(brick_data, url):
        raw_image = requests.get(url)
        req = requests.post(
            'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect?%s' % urllib.parse.urlencode({
                'returnFaceId': 'false',
                'returnFaceLandmarks': 'false',
                'returnFaceAttributes': 'emotion'
            }),
            headers={
                'Content-Type': 'application/octet-stream',
                'Ocp-Apim-Subscription-Key': brick_data['subscription']

            },
            data=raw_image.content)
        return req.json()

    async def facebook(self, command):
        if command == 'get_started':
            # send_message = [
            #     Message(
            #         attachment=ImageAttachment(
            #             url=BRICK_DEFAULT_IMAGE
            #         )
            #     ),
            #     Message(
            #         text='Microsoft Azure-AI Cognitive에서 제공하는 "사진속 감정을 읽어드리는 서비스"에요.'
            #     )
            # ]
            send_message = [
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(image_url=BRICK_DEFAULT_IMAGE,
                                        title='사진속 감정을 읽어드리는 서비스',
                                        subtitle='Microsoft Azure-AI Cognitive에서 제공하는 "사진속 감정을 읽어드리는 서비스"에요.')
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            face_1 = input_data['store'][0]['value']

            res = await Emotion.get_data(input_data['data'], face_1)

            if type(res) is dict and res.get('error', False):
                send_message = [
                    Message(
                        text='[에러발생]\nCode: {code}\nMessage: {message}\n\n관리자에게 문의 바랍니다.\ndevops@bluehack.net'.format(
                            **res['error']),
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 사진분석',
                                    payload='brick|emotion|get_started'
                                )
                            ]
                        )
                    )
                ]
            else:
                if len(res) == 0:
                    send_message = [
                        Message(
                            text='감정을 알 수 없어요 ㅜㅜ\n다시 시도해주세요.',
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 사진분석',
                                        payload='brick|emotion|get_started'
                                    )
                                ]
                            )
                        )
                    ]
                else:
                    res_face = res[0]['faceAttributes']['emotion']
                    sorted_score = sorted(res_face.items(), key=operator.itemgetter(1), reverse=True)

                    send_message = [
                        Message(
                            text='조회된 결과에요.'
                        ),
                        Message(
                            text='두구두구!!\n사진 속의 사람의 감정은 %s이네요.' % EMOTION[sorted_score[0][0]],
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 사진분석',
                                        payload='brick|emotion|get_started'
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
                    text='Microsoft Azure-AI Cognitive에서 제공하는 "사진속 감정을 읽어드리는 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':

            input_data = await self.brick_db.get()
            face_1 = input_data['store'][0]['value']

            res = await Emotion.get_data(input_data['data'], face_1)

            if type(res) is dict and res.get('error', False):
                send_message = [
                    tg.SendMessage(
                        text='*[에러발생]*\nCode: {code}\nMessage: {message}\n\n관리자에게 문의 바랍니다.\ndevops@bluehack.net'.format(
                            **res['error']),
                        parse_mode='Markdown',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다른 사진분석',
                                        callback_data='BRICK|emotion|get_started'
                                    )
                                ]
                            ]
                        )
                    )
                ]
            else:
                if len(res) == 0:
                    send_message = [
                        tg.SendMessage(
                            text='감정을 알 수 없어요 ㅜㅜ\n다시 시도해주세요.',
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 사진분석',
                                            callback_data='BRICK|emotion|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
                else:
                    res_face = res[0]['faceAttributes']['emotion']
                    sorted_score = sorted(res_face.items(), key=operator.itemgetter(1), reverse=True)

                    send_message = [
                        tg.SendMessage(
                            text='조회된 결과에요.'
                        ),
                        tg.SendMessage(
                            text='두구두구!!\n사진 속의 사람의 감정은 %s이네요.' % EMOTION[sorted_score[0][0]],
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 사진분석',
                                            callback_data='BRICK|emotion|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]

            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
