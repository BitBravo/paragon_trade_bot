from email.headerregistry import Address
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import os
import smtplib
import traceback

class Mailer(object):
    def __init__(self, smtp_server, smtp_port, email_address, email_password, ssl):
        super(Mailer, self).__init__()
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address =  email_address
        self.email_password = email_password
        self.ssl = ssl
    def contains_non_ascii_characters(self,str):
        return not all(ord(c) < 128 for c in str)   
    def add_header(self, message, header_name, header_value):
        if self.contains_non_ascii_characters(header_value):
            h = Header(header_value, 'utf-8')
            message[header_name] = h
        else:
            message[header_name] = header_value    
        return message
    def send(self, sender_name, to_address, subject, body):
        msg = MIMEMultipart('alternative')
        msg = self.add_header(msg, 'Subject', subject)
        msg['From'] = "{} <{}>".format(sender_name, self.email_address)
        msg['To'] = to_address
        html_text = MIMEText(body.encode('utf-8'), 'html','utf-8')
        msg.attach(html_text)
        if self.ssl:
            smtp_server = smtplib.SMTP_SSL('{}:{}'.format(self.smtp_server, self.smtp_port))
        else :
            smtp_server = smtplib.SMTP('{}:{}'.format(self.smtp_server, self.smtp_port))
            smtp_server.starttls() 
        smtp_server.login(self.email_address, self.email_password)
        smtp_server.send_message(msg)