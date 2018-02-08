import logging
from xml.etree.ElementTree import fromstring

logger = logging.getLogger(__name__)


def get_items_from_xml(res):
    parsed_result = fromstring(res.text)
    items = []
    for item in parsed_result.getchildren():
        if item.tag == 'body':
            for sub_item in item.getchildren():
                if sub_item.tag == 'items':
                    for hospital in sub_item.getchildren():
                        hospital_inform = {}
                        for attr in hospital.getchildren():
                            hospital_inform[attr.tag] = attr.text

                        items.append(hospital_inform)

    return items
