import logging

import blueforge.apis.telegram as tg
import requests
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_04_001.png'


class Lotto(object):
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
                    text='(주)나눔로또에서 제공하는 "로또당첨번호 서비스"에요.'
                )
            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            num = input_data['store'][0]['value']

            res = requests.get(url='http://www.nlotto.co.kr/common.do?method=getLottoNumber&drwNo=%s' % num)
            parsed_result = res.json()

            await self.brick_db.delete()
            await self.fb.send_message(
                message=Message(
                    text='두구두구두구 ~\n조회하신 {drwNo}회 당첨번호는 {drwtNo1},{drwtNo2},{drwtNo3},{drwtNo4},{drwtNo5},{drwtNo6} 에 보너스번호는 {bnusNo} 이에요.\n부디 1등이길!!'.format(
                        **parsed_result),
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyTextItem(
                                title='다른회차검색',
                                payload='brick|lotto|get_started'
                            )
                        ]
                    )
                ))

        return None

    async def telegram(self, command):
        if command == 'get_started':
            send_message = [
                tg.SendPhoto(
                    photo=BRICK_DEFAULT_IMAGE
                ),
                tg.SendMessage(
                    text='(주)나눔로또에서 제공하는 "로또당첨번호 서비스"에요.'
                )

            ]
            await self.fb.send_messages(send_message)
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            num = input_data['store'][0]['value']

            res = requests.get(url='http://www.nlotto.co.kr/common.do?method=getLottoNumber&drwNo=%s' % num)
            parsed_result = res.json()

            await self.brick_db.delete()
            await self.fb.send_message(
                tg.SendMessage(
                    text='두구두구두구 ~\n조회하신 {drwNo}회 당첨번호는 {drwtNo1},{drwtNo2},{drwtNo3},{drwtNo4},{drwtNo5},{drwtNo6} 에 보너스번호는 {bnusNo} 이에요.\n부디 1등이길!!'.format(
                        **parsed_result),
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='다른회차검색',
                                    callback_data='BRICK|lotto|get_started'
                                )
                            ]
                        ]
                    )
                ))
        return None
