import logging
import datetime

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_09_001.png'


class Luck(object):
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
                    text='geniecontents에서 제공하는 "띠별 오늘의 운세 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            num = input_data['store'][0]['value']
            now = datetime.datetime.today()
            res = requests.get(
                url='https://www.geniecontents.com/fortune/internal/v1/daily?birthYear=%s&targetYear=%s&targetMonth=%s&targetDay=%s' % (
                    num, now.year, now.month, now.day))

            parsed_result = res.json()
            parsed_result.update(parsed_result['list'][0])
            send_message = [
                Message(
                    text='조회된 결과에요'
                ),
                Message(
                    attachment=ImageAttachment(
                        url='https:%s' % parsed_result['animalImgUrl']
                    )
                ),
                Message(
                    text='출생년도 : {year}\n운세 : {summary}\n자세한 내용 : {description}'.format(
                        **parsed_result),
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyTextItem(
                                title='다른 운세검색',
                                payload='brick|luck|get_started'
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
                    text='geniecontents에서 제공하는 "띠별 오늘의 운세 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            num = input_data['store'][0]['value']

            now = datetime.datetime.today()
            res = requests.get(
                url='https://www.geniecontents.com/fortune/internal/v1/daily?birthYear=%s&targetYear=%s&targetMonth=%s&targetDay=%s' % (
                    num, now.year, now.month, now.day))
            parsed_result = res.json()
            parsed_result.update(parsed_result['list'][0])
            send_message = [
                tg.SendMessage(
                    text='조회된 결과에요'
                ),
                tg.SendPhoto(
                    photo='https:%s' % parsed_result['animalImgUrl']
                ),
                tg.SendMessage(
                    text='출생년도 : {year}\n운세 : {summary}\n자세한 내용 : {description}'.format(
                        **parsed_result),
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='다른 운세검색',
                                    callback_data='BRICK|luck|get_started'
                                )
                            ]
                        ]
                    )
                )
            ]
            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
