#!/usr/bin/env python
# -*- coding:utf-8 -*-
# 模块名不能为email.py，不然导入email库会报错。

import smtplib
from email.header import Header
from email.mime.text import MIMEText
import logging

LOG = logging.getLogger(__name__)


class Mail(object):
    def __init__(self, kwargs):
        # 第三方 SMTP 服务

        self.mail_host = kwargs["host"]  # 设置服务器:这个是qq邮箱服务器，直接复制就可以
        self.mail_pass = kwargs["pass"]  # 刚才我们获取的授权码
        self.sender = kwargs["sender"]  # 你的邮箱地址
        self.receivers = kwargs["receivers"]  # 收件人的邮箱地址，可设置为你的QQ邮箱或者其他邮箱，可多个

    def send(self, content, subject=u'主题', from_name=u'发件人名字', to_name=u'收件人名字'):

        content = content
        message = MIMEText(content, 'plain', 'utf-8')

        message['From'] = Header(from_name, 'utf-8')
        message['To'] = Header(to_name, 'utf-8')

        subject = subject  # 发送的主题，可自由填写
        message['Subject'] = Header(subject, 'utf-8')
        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, 465)
            smtpObj.login(self.sender, self.mail_pass)
            smtpObj.sendmail(self.sender, self.receivers, message.as_string())
            smtpObj.quit()
            LOG.info(u'邮件发送成功。message: {}'.format(message))
        except smtplib.SMTPException as e:
            LOG.exception(u'邮件发送失败。message: {}'.format(message))


if __name__ == "__main__":
    mail_conf = {
        "host": "",
        "pass": "",
        "sender": "",
        "receivers": []
    }
    mail = Mail(kwargs=mail_conf)
    mail.receivers = ['xx@xx.com']
    mail.send(u'测试邮件，不用在意')
