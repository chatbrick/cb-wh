import logging

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem
from watson_developer_cloud import PersonalityInsightsV3
import time
from blueforge.apis.facebook import TemplateAttachment, Element, GenericTemplate

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_19_001.png'


class PersonalityInsight(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    async def get_data(brick_data, contents):
        personality_insights = PersonalityInsightsV3(
            version='2016-10-20',
            username=brick_data['username'],
            password=brick_data['password'])
        return personality_insights.profile(contents, content_type='text/plain',
                                            content_language='ko', raw_scores=False,
                                            consumption_preferences=False)

    async def facebook(self, command):
        if command == 'get_started':
            # send_message = [
            #     Message(
            #         attachment=ImageAttachment(
            #             url=BRICK_DEFAULT_IMAGE
            #         )
            #     ),
            #     Message(
            #         text='IBM Bluemix에서 제공하는 "자소서를 분석해주는 서비스"에요.'
            #     )
            # ]
            send_message = [
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(image_url=BRICK_DEFAULT_IMAGE,
                                        title='자소서를 분석해주는 서비스',
                                        subtitle='IBM Bluemix에서 제공하는 "자소서를 분석해주는 서비스"에요.')
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            contents = input_data['store'][0]['value']

            try:
                parsed_result = await PersonalityInsight.get_data(input_data['data'], contents)

                sending_message = '두구두구!\n자소서에 분석결과\n\n총 단어수 {word_count}\n'.format(
                    word_count=parsed_result.get('word_count', '0'))

                for item in parsed_result.get('personality', [])[:5]:
                    sending_message += '{name} : {percentile}\n'.format(**item)

                sending_message += '\n'

                for item in parsed_result.get('warnings', []):
                    sending_message += '\n{warning_id}\n{message}\n'.format(**item)

                send_message = [
                    Message(
                        text='조회된 결과에요.'
                    ),
                    Message(
                        text=sending_message,
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른 자소서분석',
                                    payload='brick|personality|get_started'
                                )
                            ]
                        )
                    )
                ]
            except Exception as ex:
                send_message = [
                    Message(
                        text='에러가 발생했습니다.\n최소 100단어 이상인 자소서 글을 입력하시거나 잠시 후에 다시 시도해주세요.\n\n에러 메시지: %s' % str(ex)
                    )]

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
                    text='IBM Bluemix에서 제공하는 "자소서를 분석해주는 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            contents = input_data['store'][0]['value']

            try:
                parsed_result = await PersonalityInsight.get_data(input_data['data'], contents)
                sending_message = '두구두구!\n자소서에 분석결과\n\n총 단어수 {word_count}\n'.format(
                    word_count=parsed_result.get('word_count', '0'))

                for item in parsed_result.get('personality', [])[:5]:
                    sending_message += '{name} : {percentile}\n'.format(**item)

                sending_message += '\n'

                for item in parsed_result.get('warnings', []):
                    sending_message += '\n{warning_id}\n{message}\n'.format(**item)

            except Exception as ex:
                sending_message = '에러가 발생했습니다.\n최소 100단어 이상인 자소서 글을 입력하시거나 잠시 후에 다시 시도해주세요.\n\n에러 메시지: %s' % str(ex)

            await self.fb.send_message(
                tg.SendMessage(
                    text=sending_message,
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='다른 자소서분석',
                                    callback_data='BRICK|personality|get_started'
                                )
                            ]
                        ]
                    )
                ))
            await self.brick_db.delete()
        return None
