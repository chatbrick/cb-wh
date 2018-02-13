import logging
import re

from xml.etree.ElementTree import fromstring

logger = logging.getLogger(__name__)


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
