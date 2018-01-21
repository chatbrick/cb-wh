from chatbrick.brick.send_email import SendEmail


def find_custom_brick(fb, platform, brick_id, raw_data, msg_data):
    if platform == 'facebook':
        if brick_id == 'send_email':
            brick_config = raw_data['data']
            email = SendEmail(receiver_email=brick_config['receiver_email'], title=brick_config['title'])
            return email.facebook(fb_token=fb.access_token, psid=msg_data['sender']['id'])
