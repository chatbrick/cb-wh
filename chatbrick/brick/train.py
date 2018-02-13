import logging

import time
import blueforge.apis.telegram as tg
import requests
import dateutil.parser
from blueforge.apis.facebook import Message, ImageAttachment, QuickReply, QuickReplyTextItem, TemplateAttachment, \
    GenericTemplate, Element, PostBackButton

from chatbrick.util import get_items_from_xml

logger = logging.getLogger(__name__)

BRICK_DEFAULT_IMAGE = 'https://www.chatbrick.io/api/static/brick/img_brick_01_001.png'
STATION = {"가야": "NAT840051", "가평": "NAT140576", "각계": "NAT012054", "강경": "NAT030607", "강릉(올림픽)": "NAT601936",
           "강촌": "NAT140701", "개포": "NAT300733", "건천": "NAT023660", "검암": "NATC10325", "경산": "NAT013395",
           "경주": "NAT751123", "계릉": "NAT030254", "고한": "NAT650828", "곡성": "NAT041072", "공주": "NATH20438",
           "관촌": "NAT040496", "광명": "NATH10219", "광양": "NAT881708", "광운대": "NAT130182", "광주": "NAT883012",
           "광주송정": "NAT031857", "광천": "NAT080749", "구례구": "NAT041285", "구미": "NAT012775", "구포": "NAT014281",
           "국수": "NAT020430", "군북": "NAT880608", "군산": "NAT081388", "극락강": "NAT883086", "금곡": "NAT140163",
           "기장": "NAT750329", "김유정": "NAT140787", "김제": "NAT031056", "김천": "NAT012546", "김천구미": "NATH12383",
           "나전": "NAT610326", "나주": "NAT031998", "남성현": "NAT013542", "남원": "NAT040868", "남창": "NAT750560",
           "남춘천": "NAT140840", "남평": "NAT882847", "논산": "NAT030508", "능곡": "NAT110165", "능주": "NAT882666",
           "다시": "NAT032099", "단양": "NAT021784", "대광리": "NAT130844", "대구": "NAT013239", "대성리": "NAT140362",
           "대야": "NAT320130", "대전": "NAT011668", "대천": "NAT080952", "덕소": "NAT020178", "덕하": "NAT750653",
           "도계": "NAT601122", "도고온천": "NAT080309", "도담": "NAT021723", "도라산": "NAT110557", "동대구": "NAT013271",
           "동두천": "NAT130531", "동래": "NAT750106", "동백산": "NAT651053", "동산": "NAT040173", "동점": "NAT600830",
           "동탄": "NATH30326", "동해": "NAT601485", "동화": "NAT020986", "득량": "NAT882237", "마산": "NAT880345",
           "마석": "NAT140277", "망상": "NAT601605", "망상해변": "NAT601602", "매곡": "NAT020803", "명봉": "NAT882416",
           "목포": "NAT032563", "목행": "NAT050881", "몽탄": "NAT032313", "무안": "NAT032273", "묵호": "NAT601545",
           "문산": "NAT110460", "물금": "NAT014150", "민둥산": "NAT650722", "밀양": "NAT013841", "반곡": "NAT021175",
           "반성": "NAT880766", "백마고지": "NAT130944", "백양리": "NAT140681", "뱍양사": "NAT031486", "벌교": "NAT882034",
           "별어곡": "NAT610064", "보성": "NAT882328", "봉양": "NAT021478", "봉화": "NAT600147", "부강": "NAT011403",
           "부산": "NAT014445", "부전": "NAT750046", "부조": "NAT751354", "부천": "NAT060121", "북영천": "NAT023424",
           "북천": "NAT881269", "분천": "NAT600593", "불국사": "NAT751013", "비동": "NAT600635", "사곡": "NAT012821",
           "사릉": "NAT140133", "사방": "NAT751238", "사북": "NAT650782", "사상": "NAT014331", "삼랑진": "NAT013967",
           "삼례": "NAT040133", "삼산": "NAT020884", "삼탄": "NAT051006", "삽교": "NAT080492", "상동": "NAT013747",
           "상봉": "NAT020040", "상주": "NAT300360", "서경주": "NAT023821", "서광주": "NAT882936", "서대전": "NAT030057",
           "서빙고": "NAT130036", "서울": "NAT010000", "서정리": "NAT010670", "서천": "NAT081343", "석불": "NAT020717",
           "석포": "NAT600768", "선평": "NAT610137", "성환": "NAT010848", "소요산": "NAT130556", "소정리": "NAT011079",
           "송정": "NAT750254", "수서": "NATH30000", "수원": "NAT010415", "순천": "NAT041595", "승부": "NAT600692",
           "신경주": "NATH13421", "신기": "NAT601275", "신녕": "NAT023279", "신동": "NAT013067", "신례원": "NAT080353",
           "신리": "NAT040352", "신림": "NAT021357", "신망리": "NAT130774", "신창": "NAT080216", "신창원": "NAT810048",
           "신탄리": "NAT130888", "신탄진": "NAT011524", "신태인": "NAT031179", "심천": "NAT012016", "쌍룡": "NAT650177",
           "아산": "NAT080045", "아신": "NAT020471", "아우라지": "NAT610387", "아포": "NAT012700", "안강": "NAT751296",
           "안동": "NAT022557", "안양": "NAT010239", "약목": "NAT012903", "양동": "NAT020845", "양보": "NAT881323",
           "양수": "NAT020346", "양원": "NAT600655", "양자동": "NAT751325", "양평": "NAT020524", "여수EXPO": "NAT041993",
           "여천": "NAT041866", "연당": "NAT650253", "연무대": "NAT340090", "연산": "NAT030396", "연천": "NAT130738",
           "영동": "NAT012124", "영등포": "NAT010091", "영월": "NAT650341", "영주": "NAT022188", "영천": "NAT023449",
           "예당": "NAT882194", "예미": "NAT650515", "예산": "NAT080402", "예천": "NAT300850", "오근장": "NAT050215",
           "오산": "NAT010570", "오송": "NAT050044", "오수": "NAT040667", "옥곡": "NAT881584", "옥산": "NAT300200",
           "옥수": "NAT130070", "옥천": "NAT011833", "온양온천": "NAT080147", "완사": "NAT881168", "왕십리": "NAT130104",
           "왜관": "NAT012968", "용궁": "NAT300669", "용동": "NAT030667", "용문": "NAT020641", "용산": "NAT010032",
           "운천": "NAT110497", "울산": "NATH13717", "웅천": "NAT022373", "원동": "NAT014058", "원북": "NAT880644",
           "원주": "NAT021082", "월내": "NAT750446", "율촌": "NAT041710", "음성": "NAT050596", "의성": "NAT022844",
           "의정부": "NAT130312", "이양": "NAT882544", "이원": "NAT011916", "익산": "NAT030879", "일로": "NAT032422",
           "일산": "NAT110249", "일신": "NAT020760", "임기": "NAT600476", "임성리": "NAT032489", "임실": "NAT040536",
           "임진강": "NAT110520", "입실": "NAT750933", "자미원": "NAT650655", "장락": "NAT650050", "장성": "NAT031638",
           "장항": "NAT081318", "전곡": "NAT130652", "전의": "NAT011154", "전주": "NAT040257", "점촌": "NAT300600",
           "정동진": "NAT601774", "정선": "NAT610226", "정읍": "NAT031314", "제천": "NAT021549", "조성": "NAT882141",
           "조치원": "NAT011298", "좌천": "NAT750412", "주덕": "NAT050719", "주안": "NAT060231", "중리": "NAT880408",
           "증평": "NAT050366", "지제": "NATH30536", "지탄": "NAT011972", "지평": "NAT020677", "진례": "NAT880179",
           "진상": "NAT881538", "진성": "NAT880825", "진영": "NAT880177", "진주": "NAT881014", "진해": "NAT810195",
           "창원": "NAT880310", "창원중앙": "NAT880281", "천안": "NAT010971", "천안아산": "NATH10960", "철암": "NAT600870",
           "청도": "NAT013629", "청량리": "NAT130126", "청리": "NAT300271", "청소": "NAT080827", "청주": "NAT050114",
           "청주공항": "NAT050244", "청평": "NAT140436", "초성리": "NAT130597", "추전": "NAT650918", "추풍령": "NAT012355",
           "춘양": "NAT600379", "춘천": "NAT140873", "충주": "NAT050827", "탄현": "NAT110265", "탑리": "NAT022961",
           "태백": "NAT650978", "태화강": "NAT750726", "퇴계원": "NAT140098", "파주": "NAT110407", "판교": "NAT081240",
           "평내호평": "NAT140214", "평촌": "NAT880702", "평택": "NAT010754", "포항": "NAT8B0351", "풍기": "NAT022053",
           "하동": "NAT881460", "하양": "NAT830200", "한림정": "NAT880099", "한탄강": "NAT130627", "함백": "NAT650567",
           "함안": "NAT880520", "함열": "NAT030718", "함창": "NAT300558", "함평": "NAT032212", "행신": "NAT110147",
           "현동": "NAT600527", "호계": "NAT750822", "홍성": "NAT080622", "화명": "NAT014244", "화본": "NAT023127",
           "화순": "NAT882755", "황간": "NAT012270", "횡천": "NAT881386", "효문": "NAT750760", "효자": "NAT751418",
           "효천": "NAT882904", "흑석리": "NAT030173", "희방사": "NAT021992"}


class Train(object):
    def __init__(self, fb, brick_db):
        self.brick_db = brick_db
        self.fb = fb

    @staticmethod
    def days_hours_minutes(td):
        return td.seconds // 3600, (td.seconds // 60) % 6

    async def facebook(self, command):
        if command == 'get_started':
            send_message = [
                Message(
                    attachment=ImageAttachment(
                        url=BRICK_DEFAULT_IMAGE
                    )
                ),
                Message(
                    text='국토교통부에서 제공하는 "열차조회 서비스"에요. 코레일/SRT 모두 조회 가능해요.'
                ),
                Message(
                    attachment=TemplateAttachment(
                        payload=GenericTemplate(
                            elements=[
                                Element(
                                    image_url='https://www.chatbrick.io/api/static/brick/img_brick_01_002.png',
                                    title='열차조회',
                                    subtitle='코레일/SRT 모두 조회할 수 있어요',
                                    buttons=[
                                        PostBackButton(
                                            title='조회하기',
                                            payload='brick|train|show_data'
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )
            ]
            await self.fb.send_messages(send_message)
        elif command == 'show_data':
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            departure_station = input_data['store'][0]['value'].strip()
            destination_station = input_data['store'][1]['value'].strip()
            departure_date = input_data['store'][2]['value']
            train_type = input_data['store'][3]['value']
            start = int(time.time() * 1000)

            res = requests.get(
                url='http://openapi.tago.go.kr/openapi/service/TrainInfoService/getStrtpntAlocFndTrainInfo?serviceKey=%s&numOfRows=500&pageSize=500&pageNo=1&startPage=1&depPlaceId=%s&arrPlaceId=%s&depPlandTime=%s&trainGradeCode=%s' % (
                    input_data['data']['api_key'], STATION[departure_station], STATION[destination_station],
                    departure_date, train_type))

            items = get_items_from_xml(res)
            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'train',
                'platform': 'facebook',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '페이스북,철도,시간,조회,API',
                'data': items,
                'remark': '철도 시간표 조회 API 호출'
            })

            if len(items) == 0:
                send_message = [
                    Message(
                        text='조회된 결과가 없습니다.',
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다시 검색하기',
                                    payload='brick|train|show_data'
                                )
                            ]
                        )
                    )
                ]
            else:
                result_message = '{depplacename} -> {arrplacename}\n\n'.format(**items[0])
                for item in items:
                    departure_train_datetime = dateutil.parser.parse(item['depplandtime'])
                    arrive_train_datetime = dateutil.parser.parse(item['arrplandtime'])
                    gap = Train.days_hours_minutes(arrive_train_datetime - departure_train_datetime)

                    item['fromtodatetime'] = '%02d:%02d -> %02d:%02d' % (
                        departure_train_datetime.hour, departure_train_datetime.minute, arrive_train_datetime.hour,
                        arrive_train_datetime.minute)
                    item['time_delta'] = '%02d:%02d' % (gap[0], gap[1])
                    item['adultcharge_formmated'] = format(int(item['adultcharge']), ',')
                    result_message += '{traingradename} {fromtodatetime}    {time_delta}    {adultcharge_formmated}\n'.format(
                        **item)

                send_message = [
                    Message(
                        text=result_message,
                        quick_replies=QuickReply(
                            quick_reply_items=[
                                QuickReplyTextItem(
                                    title='다시 검색하기',
                                    payload='brick|train|get_started'
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
                    text='국토교통부에서 제공하는 "열차조회 서비스"에요. 코레일/SRT 모두 조회 가능해요.',
                    reply_markup=tg.MarkUpContainer(
                        inline_keyboard=[
                            [
                                tg.CallbackButton(
                                    text='열차 조회하기',
                                    callback_data='BRICK|train|show_data'
                                )
                            ]
                        ]
                    )
                )

            ]
            await self.fb.send_messages(send_message)
        elif command == 'show_data':
            await self.brick_db.save()
        elif command == 'final':
            input_data = await self.brick_db.get()
            departure_station = input_data['store'][0]['value'].strip()
            destination_station = input_data['store'][1]['value'].strip()
            departure_date = input_data['store'][2]['value']
            train_type = input_data['store'][3]['value']
            start = int(time.time() * 1000)

            res = requests.get(
                url='http://openapi.tago.go.kr/openapi/service/TrainInfoService/getStrtpntAlocFndTrainInfo?serviceKey=%s&numOfRows=500&pageSize=500&pageNo=1&startPage=1&depPlaceId=%s&arrPlaceId=%s&depPlandTime=%s&trainGradeCode=%s' % (
                    input_data['data']['api_key'], STATION[departure_station], STATION[destination_station],
                    departure_date, train_type))

            items = get_items_from_xml(res)

            requests.post('https://www.chatbrick.io/api/log/', data={
                'brick_id': 'train',
                'platform': 'telegram',
                'start': start,
                'end': int(time.time() * 1000),
                'tag': '페이스북,철도,시간,조회,API',
                'data': items,
                'remark': '철도 시간표 조회 API 호출'
            })

            if len(items) == 0:
                send_message = [
                    tg.SendMessage(
                        text='조회된 결과가 없습니다.',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다시 조회하기',
                                        callback_data='BRICK|train|show_data'
                                    )
                                ]
                            ]
                        )
                    )
                ]
            else:
                result_message = '*{depplacename} -> {arrplacename}*\n\n'.format(**items[0])
                for item in items:
                    departure_train_datetime = dateutil.parser.parse(item['depplandtime'])
                    arrive_train_datetime = dateutil.parser.parse(item['arrplandtime'])
                    gap = Train.days_hours_minutes(arrive_train_datetime - departure_train_datetime)

                    item['fromtodatetime'] = '%02d:%02d -> %02d:%02d' % (
                        departure_train_datetime.hour, departure_train_datetime.minute, arrive_train_datetime.hour,
                        arrive_train_datetime.minute)
                    item['time_delta'] = '%02d:%02d' % (gap[0], gap[1])
                    item['adultcharge_formmated'] = format(int(item['adultcharge']), ',')
                    result_message += '{traingradename} {fromtodatetime}    {time_delta}    {adultcharge_formmated}\n'.format(
                        **item)

                send_message = [
                    tg.SendMessage(
                        text=result_message,
                        parse_mode='Markdown',
                        reply_markup=tg.MarkUpContainer(
                            inline_keyboard=[
                                [
                                    tg.CallbackButton(
                                        text='다시 조회하기',
                                        callback_data='BRICK|train|show_data'
                                    )
                                ]
                            ]
                        )
                    )
                ]
            await self.brick_db.delete()
            await self.fb.send_messages(send_message)
        return None
