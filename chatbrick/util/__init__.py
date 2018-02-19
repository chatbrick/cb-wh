import logging
import re
import requests
import uuid

from xml.etree.ElementTree import fromstring

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_FOLDER = '/home/ec2-user/app/chatbrick_admin/src/static/country/'
DEFAULT_IMAGE_URL = 'https://www.chatbrick.io/api/static/country/'


def get_items_from_xml(res):
    items = []
    try:
        parsed_result = fromstring(res.text)
        for item in parsed_result.getchildren():
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
    res = requests.get(url)
    file_name = res.headers['Content-Disposition'].split(sep='=')[-1].strip()
    with open(DEFAULT_IMAGE_FOLDER+file_name, 'wb') as file:
        file.write(res.content)
    return DEFAULT_IMAGE_URL + file_name


def save_voice(response):
    file_name = str(uuid.uuid4())+'.mp3'
    with open(DEFAULT_IMAGE_FOLDER+file_name, 'wb') as file:
        file.write(response.content)

    return DEFAULT_IMAGE_URL + file_name
