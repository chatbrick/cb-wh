import logging
import time
import blueforge.apis.telegram as tg
import urllib.parse
import requests
from chatbrick.util import save_voice
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, AudioAttachment, \
    TemplateAttachment, GenericTemplate, Element, PostBackButton, UrlButton

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_20_001.png'


class Tts(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    async def get_data(brick_data, speaker, speed, text):
        face_detection = requests.post(
            'https://openapi.naver.com/v1/voice/tts.bin',
            data={
                'speaker': speaker,
                'speed': speed,
                'text': text
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Naver-Client-Id': brick_data['client_id'],
                'X-Naver-Client-Secret': brick_data['client_secret']
            }
        )
        url = save_voice(face_detection)
        logger.info(url)
        return url

    @staticmethod
    async def get_news_data(brick_data, keyword):
        news_res = requests.get(
            'https://openapi.naver.com/v1/search/news.json?query=%s' % urllib.parse.quote_plus(keyword),
            headers={
                'X-Naver-Client-Id': brick_data['client_id'],
                'X-Naver-Client-Secret': brick_data['client_secret']
            }
        )
        return news_res.json()

    async def facebook(self, command):
        if command == 'get_started':
            # send_message = [
            #     Message(
            #         attachment=ImageAttachment(
            #             url=BRICK_DEFAULT_IMAGE
            #         )
            #     ),
            #     Message(
            #         text='Naver Developers에서 제공하는 "입력한 키워드와 관련된 뉴스의 제목을 읽어주는 서비스"에요.'
            #     ),
            #     Message(
            #         attachment=TemplateAttachment(
            #             payload=GenericTemplate(
            #                 elements=[
            #                     Element(
            #                         title='목소리선택',
            #                         subtitle='뉴스제목을 읽어줄 목소리 선택해주세요.',
            #                         buttons=[
            #                             PostBackButton(
            #                                 title='남성',
            #                                 payload='brick|tts|jinho'
            #                             ),
            #                             PostBackButton(
            #                                 title='여성',
            #                                 payload='brick|tts|mijin'
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
                                        title='입력한 키워드와 관련된 뉴스의 제목을 읽어주는 서비스',
                                        subtitle='Naver Developers에서 제공하는 "입력한 키워드와 관련된 뉴스의 제목을 읽어주는 서비스"에요.')
                            ]
                        )
                    )
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(
                                    title='목소리선택',
                                    subtitle='뉴스제목을 읽어줄 목소리 선택해주세요.',
                                    buttons=[
                                        PostBackButton(
                                            title='남성',
                                            payload='brick|tts|jinho'
                                        ),
                                        PostBackButton(
                                            title='여성',
                                            payload='brick|tts|mijin'
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'jinho' or command == 'mijin':
            await self.brick_db.save()
            await self.brick_db.update({'$set': {'store.1.value': command}})
        elif command == 'final':
            input_data = await self.brick_db.get()
            keyword = input_data['store'][0]['value']
            sex = input_data['store'][1]['value']

            news_res = await Tts.get_news_data(input_data['data'], keyword)

            if 'errorCode' in news_res:
                send_message = [
                    Message(
                        text='에러가 발생했습니다.\n에러코드: {errorCode}\n에러 메시지: {errorMessage}'.format(**news_res),
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다시하기',
                                    payload='brick|tts|%s' % sex
                                )
                            ]
                        )
                    )
                ]
            else:
                news_title = []
                news_elements = []
                for news in news_res['items']:
                    news_t = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '')

                    news_elements.append(Element(
                        image_url='https://www.chatbrick.io/api/static/brick/img_brick_21_003.png',
                        title=news_t,
                        subtitle=news['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', ''),
                        buttons=[
                            UrlButton(
                                url=news['link'],
                                title='뉴스보기'
                            )
                        ]
                    ))
                    news_title.append(news_t)
                mp3_url = await self.get_data(input_data['data'], sex, '0', '\n'.join(news_title))

                send_message = [
                    Message(
                        text='뉴스를 녹음하고 있어요.\n잠시 기다려 주세요.'
                    ),
                    Message(
                        attachment=TemplateAttachment(
                            payload=GenericTemplate(
                                elements=news_elements
                            )
                        )
                    ),
                    Message(
                        attachment=AudioAttachment(
                            url=mp3_url
                        )
                    ),
                    Message(
                        text='다른 뉴스를 검색하고 싶으신가요?',
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다른뉴스검색',
                                    payload='brick|tts|%s' % sex
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
                    text='Naver Developers에서 제공하는 "입력한 키워드와 관련된 뉴스의 제목을 읽어주는 서비스"에요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='남성',
                                    callback_data='BRICK|tts|jinho'
                                ),
                                tg.CallbackButton(
                                    text='여성',
                                    callback_data='BRICK|tts|mijin'
                                )
                            ]
                        ]
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'jinho' or command == 'mijin':
            await self.brick_db.save()
            await self.brick_db.update({'$set': {'store.1.value': command}})
        elif command == 'final':
            input_data = await self.brick_db.get()
            keyword = input_data['store'][0]['value']
            sex = input_data['store'][1]['value']

            news_res = await Tts.get_news_data(input_data['data'], keyword)

            if 'errorCode' in news_res:
                send_message = [
                    tg.SendMessage(
                        text='에러가 발생했습니다.\n에러코드: {errorCode}\n에러 메시지: {errorMessage}'.format(**news_res),
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다시하기',
                                        callback_data='BRICK|tts|%s' % sex
                                    )
                                ]
                            ]
                        )
                    )
                ]
            else:
                news_title = []
                news_markdown = ''

                for news in news_res['items']:
                    news_t = news['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '').replace('[', '').replace(']', '')
                    news_title.append(news_t)
                    news_markdown += '%s\n%s\n%s\n\n' % (
                        news_t, news['description'].replace('<b>', '').replace('</b>', '').replace('&quot;', ''),
                        news['link'])

                mp3_url = await self.get_data(input_data['data'], sex, '0', '\n'.join(news_title))


                send_message = [
                    tg.SendMessage(
                        text='뉴스를 녹음하고 있어요.\n잠시 기다려 주세요.'
                    ),
                    tg.SendMessage(
                        text=news_markdown,
                        disable_web_page_preview=True
                    ),
                    tg.SendAudio(
                        audio=mp3_url,
                        title='%s의 뉴스 음성' % keyword,
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다른뉴스검색',
                                        callback_data='BRICK|tts|%s' % sex
                                    )
                                ]
                            ]
                        )
                    )
                ]

            await self.fb.send_messages(send_message)
            await self.brick_db.delete()
        return None
