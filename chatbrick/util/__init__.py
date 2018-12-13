import logging
import re
import requests
import uuid

from xml.etree.ElementTree import fromstring

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_FOLDER = '/home/ec2-user/app/chatbrick_admin/src/static/country/'
DEFAULT_IMAGE_URL = 'https://www.chatbrick.io/api/static/country/'
UNKNOWN_ERROR_MSG = '에러가 발생하였어요.\n잠시후 다시 시도해주세요.'


def get_items_from_xml(res):
    is_error = False
    items = []
    error_item = {}
    try:
        parsed_result = fromstring(res.text)
        for item in parsed_result.getchildren():
            try:
                if item.tag == 'cmmMsgHeader':
                    is_error = True
                    for sub_item in item.getchildren():
                        if sub_item.tag == 'returnReasonCode':
                            error_item['code'] = sub_item.text
                        elif sub_item.tag == 'returnAuthMsg':
                            error_item['msg'] = sub_item.text

                if item.tag == 'header':
                    for sub_item in item.getchildren():
                        if sub_item.tag == 'resultCode':
                            if sub_item.text != '00':
                                is_error = True
                            error_item['code'] = sub_item.text
                        elif sub_item.tag == 'resultMsg':
                            error_item['msg'] = sub_item.text

            except Exception as ex:
                logger.error(ex)

            if is_error:
                requests.post('https://www.chatbrick.io/api/log/error/', json={
                    'type': 'brick',
                    'service': 'data.go.kr',
                    'url': res.url,
                    'data': error_item
                })

                return error_item

            if item.tag == 'body':
                for sub_item in item.getchildren():
                    if sub_item.tag == 'items':
                        for hospital in sub_item.getchildren():
                            hospital_inform = {}
                            for attr in hospital.getchildren():
                                hospital_inform[attr.tag] = attr.text

                            items.append(hospital_inform)
    except Exception as ex:
        logger.error(ex)

    return items


def remove_html_tag(raw_html):
    html_filter = re.compile('<.*?>')
    refined_text = raw_html.replace('<br>', '\n')
    refined_text = refined_text.replace('&nbsp;', ' ')
    refined_text = re.sub(html_filter, '', refined_text)
    return refined_text


def download_and_save_image(url):
    res = requests.get(url, timeout=100)
    file_name = res.headers['Content-Disposition'].split(sep='=')[-1].strip()
    with open(DEFAULT_IMAGE_FOLDER + file_name, 'wb') as file:
        file.write(res.content)
    return DEFAULT_IMAGE_URL + file_name


def save_voice(response):
    file_name = str(uuid.uuid4()) + '.mp3'
    with open(DEFAULT_IMAGE_FOLDER + file_name, 'wb') as file:
        file.write(response.content)

    return DEFAULT_IMAGE_URL + file_name


def save_a_log_to_server(log_data):
    try:
        if log_data['log_id'] is not None:
            _, log_data['start'] = log_data['log_id'].split(sep='|')
            requests.put('https://www.chatbrick.io/api/log_new/', json=log_data)
            return None
    except Exception as ex:
        logger.error(ex)

    return log_data['log_id']


def detect_log_type(log_data):
    if type(log_data) is not dict:
        log_data = log_data.get_data()

    try:
        print(log_data)
        if 'message' in log_data:
            log_data = log_data['message']

        if 'text' in log_data:
            return 'facebook_text'
        elif 'attachment' in log_data:
            log_data = log_data['attachment']
            if log_data['type'] == 'template':
                template_type = log_data['payload']['template_type']
                if template_type == 'generic':
                    return 'facebook_generic'
                elif template_type == 'list':
                    return 'facebook_list'
                elif template_type == 'button':
                    return 'facebook_textbtn'
                else:
                    return 'UNKNOWN_TEMPLATE'
            elif log_data['type'] == 'image':
                return 'facebook_image'
            elif log_data['type'] == 'audio':
                return 'facebook_audio'
            else:
                return 'UNKNOWN_ATTACHMENT'
        else:
            return 'UNKNOWN'
    except Exception as ex:
        logger.error(ex)
    return 'FAILED_TO_DETECT_MESSAGE_TYPE'
