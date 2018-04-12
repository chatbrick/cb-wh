import logging

import blueforge.apis.telegram as tg
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyLocationItem

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_19_001.png'


class LocationTest(object):
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
                    text='안녕하세요. 장소 테스트입니다.'
                ),
                Message(
                    text='현재위치를 보내주세요.',
                    quick_replies=QuickReply(
                        quick_reply_items=[
                            QuickReplyLocationItem()
                        ]
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        return None

    async def telegram(self, command):
        if command == 'get_started':
            send_message = [
                tg.SendPhoto(
                    photo=BRICK_DEFAULT_IMAGE
                ),
                tg.SendMessage(
                    text='안녕하세요. 장소 테스트입니다.'
                ),
                tg.SendMessage(
                    text='위치를 보내주세요.'
                )

            ]

            await self.fb.send_messages(send_message)

        return None
