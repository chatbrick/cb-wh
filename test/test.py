from blueforge.apis.facebook import *
import json

template = []

# 유니톤 참가(예정)
register_menu = [Element(title='참가신청 및 변경', subtitle='유니톤 참가신청 관련내용입니다.',
                         image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                         buttons=[PostBackButton(title='일정 및 참여요건', payload='REGISTER_CONDITION_MENU'),
                                  PostBackButton(title='참가 신청하기', payload='REGISTER_MENU'),
                                  PostBackButton(title='신청 내용 변경', payload='MODIFY_REGISTERED_DOCUMENT_MENU')]),
                 Element(title='사전모임세미나 참가신청 및 변경', subtitle='사전모임/세미나 안내입니다.',
                         image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                         buttons=[PostBackButton(title='일정안내', payload='INFORM_SEMINAR_MENU'),
                                  PostBackButton(title='참가 신청하기', payload='SEMINAR_REGISTER_MENU'),
                                  PostBackButton(title='신청 내용변경', payload='MODIFY_REGISTERED_SEMINAR_DOCUMENT_MENU')]),
                 Element(title='팀빌딩', subtitle='팀빌딩 관련 안내입니다.',
                         image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                         buttons=[PostBackButton(title='팀빌딩 방식', payload='THE_WAYS_TO_MAKE_TEAMBUILDING_MENU'),
                                  PostBackButton(title='팀빌딩 발표일', payload='THE_DATE_TEAMBUILDING_ANNOUNCEMENT_MENU')]),
                 Element(title='유니톤 7회', subtitle='유니톤 본행사 안내입니다.',
                         image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                         buttons=[PostBackButton(title='일정안내', payload='7TH_INFORM_SEMINAR_MENU'),
                                  PostBackButton(title='행사내용', payload='7TH_EVENT_INFORM_MENU'),
                                  PostBackButton(title='시상내용', payload='7TH_AWARDS_INFORM_MENU')]),
                 Element(title='유니톤 참가 증명/발급', subtitle='증명/발급 안내입니다.',
                         image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                         buttons=[
                             PostBackButton(title='증명발급안내', payload='THE_WAYS_INFORM_OF_CERTIFICATE_DOCUMENT_MENU')]),
                 Element(title='자주하는질문', subtitle='자주하는 질문 안내입니다.',
                         image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                         buttons=[PostBackButton(title='질문 찾아보기', payload='FIND_Q_AND_A_MENU')])
                 ]

promotion_menu = [Element(title='흥보요청', subtitle='흥보요청 안내입니다.',
                          image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                          buttons=[PostBackButton(title='흥보 요청하기', payload='REQUEST_PROMOTION_MENU')]),
                  Element(title='기타문의', subtitle='기타 문의와 관련된 안내입니다.',
                          image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                          buttons=[PostBackButton(title='기타문의하기', payload='CONTACT_MENU')])]

template = [Element(title='', subtitle='흥보요청 안내입니다.',
                    image_url='https://www.sc.or.kr/webPub/0_sck2014/images/marathon/14_over.gif',
                    buttons=[PostBackButton(title='흥보 요청하기', payload='REQUEST_PROMOTION_MENU')]), ]
abc = []
for plate in template:
    abc.append(plate.get_data())

button_payload = {
    'text': '초대장이 발송된 동아리에 소속된 사람은 아래의 "참가신청하기"를 클릭하시고\n등록되지 않은 동아리의 경우는 "동아리등록하기"를 클릭하여 주시기 바랍니다.',
    'buttons': [PostBackButton(title='참가신청하기', payload='REQUEST_JOIN_MENU').get_data(),
                PostBackButton(title='동아리등록하기', payload='REQUEST_REGISTERING_CIRCLE_MENU').get_data()]
}

payload = {
    'template_type': 'button',
    'elements': [button_payload]
}



attachment = {
    'type': 'template',
    'payload': payload
}

message = {
    'attachment': attachment
}

final_message = {
    'type': 'postback',
    'value': 'REGISTER_CONDITION_MENU',
    'conditions': [],
    'actions': [{'message': {
        'text': '유니톤 참가 신청은 x월 xx일 00시까지이며\n사전에 등록되어 초대장이 발송된 동아리에 소속된 사람으로 제한됩니다.'
    }}, {'message': message}]
}

print(json.dumps(final_message, ensure_ascii=False))
