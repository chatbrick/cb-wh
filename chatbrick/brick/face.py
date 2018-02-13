import logging
import time
import blueforge.apis.telegram as tg
import urllib.parse
import requests
import json

from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_16_001.png'


class Face(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    async def get_face_id(brick_data, url):
        raw_image = requests.get(url)
        req = requests.post(
            'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect?%s' % urllib.parse.urlencode({
                'returnFaceId': 'true',
                'returnFaceLandmarks': 'false',
                'returnFaceAttributes': ''
            }),
            headers={
                'Content-Type': 'application/octet-stream',
                'Ocp-Apim-Subscription-Key': brick_data['subscription']

            },
            data=raw_image.content)
        return req.json()

    @staticmethod
    async def get_data(brick_data, first_id, second_id):
        req = requests.post(
            'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/findsimilars',
            headers={
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': brick_data['subscription']

            },
            data=json.dumps({
                'faceId': first_id,
                'faceIds': [second_id],
                'maxNumOfCandidatesReturned': 2,
                'mode': 'matchFace'
            }))
        return req.json()

    async def facebook(self, command):
        if command == 'get_started':
            send_message = [
                Message(
                    attachment=ImageAttachment(
                        url=BRICK_DEFAULT_IMAGE
                    )
                ),
                Message(
                    text='Microsoft Azure-AI Cognitive에서 제공하는 "두장의 사진이 얼마나 닮았는지 알려드리는 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            face_1 = input_data['store'][0]['value']
            face_2 = input_data['store'][1]['value']
            start = int(time.time() * 1000)
            face_1_res = await Face.get_face_id(input_data['data'], face_1)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'face',
                'platform': 'facebook',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '페이스북,페이스,API,얼마나닮았지,얼굴감지',
                'data': json.dumps(face_1_res),
                'remark': '얼마나닮았지 블루믹스 얼굴감지 API 호출'
            })

            start = int(time.time() * 1000)
            face_2_res = await Face.get_face_id(input_data['data'], face_2)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'face',
                'platform': 'facebook',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '페이스북,페이스,API,얼마나닮았지,얼굴감지',
                'data': json.dumps(face_2_res),
                'remark': '얼마나닮았지 블루믹스 얼굴감지 API 호출'
            })

            if len(face_1_res) == 0 or len(face_2_res) == 0:
                send_message = [
                    Message(
                        text='얼굴 감지를 실패했습니다.\n다시 시도해주세요.',
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 얼굴비교',
                                    payload='brick|face|get_started'
                                )
                            ]
                        )
                    )
                ]
            else:
                start = int(time.time() * 1000)
                face_compare = await Face.get_data(input_data['data'], face_1_res[0]['faceId'], face_2_res[0]['faceId'])
                requests.post('https://www.chatbrick.io/api/log/', data={
                    'brick_id': 'face',
                    'platform': 'facebook',
                    'start': start,
                    'end': int(time.time() * 1000),
                    'tag': '페이스북,페이스,API,얼마나닮았지,얼굴비교',
                    'data': json.dumps(face_compare),
                    'remark': '얼마나닮았지 블루믹스 얼굴비교 API 호출'
                })

                if len(face_compare) == 0:
                    send_message = [
                        Message(
                            text='도대체 닮은 구석을 찾으려야 찾을 수가 없네요.',
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 얼굴비교',
                                        payload='brick|face|get_started'
                                    )
                                ]
                            )
                        )
                    ]
                else:

                    send_message = [
                        Message(
                            text='조회된 결과에요.\n1이 만점이에요.\n예) 0.37508 은 37% 닮은거에요.'
                        ),
                        Message(
                            text='두구두구!! 딱 이정도 닮았네요.\n닮음수치: {confidence}'.format(
                                **face_compare[0]),
                            quick_replies=QuickReply(
                                quick_reply_items=[
                                    QuickReplyTextItem(
                                        title='다른 얼굴비교',
                                        payload='brick|face|get_started'
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
                    text='Microsoft Azure-AI Cognitive에서 제공하는 "두장의 사진이 얼마나 닮았는지 알려드리는 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            face_1 = input_data['store'][0]['value']
            face_2 = input_data['store'][1]['value']
            start = int(time.time() * 1000)
            face_1_res = await Face.get_face_id(input_data['data'], face_1)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'face',
                'platform': 'telegram',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '텔레그램,페이스,API,얼마나닮았지,얼굴감지',
                'data': json.dumps(face_1_res),
                'remark': '얼마나닮았지 블루믹스 얼굴감지 API 호출'
            })

            start = int(time.time() * 1000)
            face_2_res = await Face.get_face_id(input_data['data'], face_2)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'face',
                'platform': 'telegram',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '텔레그램,페이스,API,얼마나닮았지,얼굴감지',
                'data': json.dumps(face_2_res),
                'remark': '얼마나닮았지 블루믹스 얼굴감지 API 호출'
            })

            if len(face_1_res) == 0 or len(face_2_res) == 0:
                send_message = [
                    tg.SendMessage(
                        text='얼굴 감지를 실패했습니다.\n다시 시도해주세요.',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다른 얼굴비교',
                                        callback_data='BRICK|face|get_started'
                                    )
                                ]
                            ]
                        )
                    )
                ]
            else:
                start = int(time.time() * 1000)
                face_compare = await Face.get_data(input_data['data'], face_1_res[0]['faceId'], face_2_res[0]['faceId'])
                requests.post('https://www.chatbrick.io/api/log/', data={
                    'brick_id': 'face',
                    'platform': 'telegram',
                    'start': start,
                    'end': int(time.time() * 1000),
                    'tag': '텔레그램,페이스,API,얼마나닮았지,얼굴비교',
                    'data': json.dumps(face_compare),
                    'remark': '얼마나닮았지 블루믹스 얼굴비교 API 호출'
                })

                if len(face_compare) == 0:
                    send_message = [
                        tg.SendMessage(
                            text='도대체 닮은 구석을 찾으려야 찾을 수가 없네요.',
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 얼굴비교',
                                            callback_data='BRICK|face|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
                else:

                    send_message = [
                        tg.SendMessage(
                            text='조회된 결과에요.\n1이 만점이에요.\n예) 0.37508 은 37% 닮은거에요.'
                        ),
                        tg.SendMessage(
                            text='두구두구!! 딱 이정도 닮았네요.\n닮음수치: {confidence}'.format(
                                **face_compare[0]),
                            reply_markup=tg.MarkUpContainer(
                                inline_keyboard=[
                                    [
                                        tg.CallbackButton(
                                            text='다른 얼굴비교',
                                            callback_data='BRICK|face|get_started'
                                        )
                                    ]
                                ]
                            )
                        )
                    ]
            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
