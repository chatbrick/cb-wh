import requests
import smtplib
import os
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class SendEmail(object):
    def __init__(self, receiver_email, title):
        self.receiver_email = receiver_email
        self.sender_email = os.environ['SENDER_EMAIL']
        self.sender_password = os.environ['SENDER_PASSWORD']
        self.title = title
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtp.ehlo()
        self.smtp.starttls()
        logger.info(self.smtp.login(self.sender_email, self.sender_password))

    def __del__(self):
        self.smtp.close()

    def facebook(self, fb_token, psid):
        req = requests.get(
            'https://graph.facebook.com/v2.6/%s?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token=%s' % (
                psid, fb_token))
        res = req.json()
        html = '''<p>조회 알림</p>
                    <img src="{profile_pic}" style="width:200px">
                    
                    <table style="font-family: arial, sans-serif;border-collapse: collapse;width: 100%;">
                      <tr>
                        <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;">값</th>
                        <th style="border: 1px solid #dddddd;text-align: left;padding: 8px;">내용</th>
                      </tr>
                      <tr>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">성</td>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">{last_name}</td>
                      </tr>
                      <tr>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">이름</td>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">{first_name}</td>
                      </tr>
                      <tr>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">성별</td>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">{gender}</td>
                      </tr>
                      <tr>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">언어</td>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">{locale}</td>
                      </tr>
                      <tr>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">시간대</td>
                        <td style="border: 1px solid #dddddd;text-align: left;padding: 8px;">{timezone}</td>
                      </tr>
                    </table>'''.format(profile_pic=res['profile_pic'], last_name=res['last_name'],
                                       first_name=res['first_name'], gender=res['gender'], locale=res['locale'],
                                       timezone=res['timezone'])

        msg = MIMEText(html, 'html')
        msg['Subject'] = self.title
        msg['To'] = self.receiver_email
        return self.smtp.sendmail(self.sender_email, self.receiver_email, msg.as_string())
