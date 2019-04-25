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



html = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /></head><body style="font-size:10pt; font-family:Verdana, Geneva, sans-serif;"><style>.top_text h3{ line-height:30px; margin-top: 5px;}</style><table width="100%" border="0" cellspacing="0"  cellpadding="0"   style="background-color:#f0eeef; color:#58443d;"><tr><td valign="top"><table width="600" border="0" cellspacing="0"  cellpadding="15" align="center"     style="background-color:#ffffff; color:#58443d;"><tr>
            <td valign="top" style="line-height:30px; font-size:16px;  text-align:center;">Chez Moi - Feliz Aniversário - Venho Comemorar com a gente</td>
        </tr><tr><td valign="top" style="height: 150px;"><img src="https://www.wi5admin.com/new/Files/colabore/images/1513050408_chezmoi.jpg" width="600" /></td></tr><tr><td valign="top"><div class="top_text"><a href="http://www.wi5admin.com/manager/survey/36/1/" target="_blank"><img src="https://www.wi5admin.com/images/welcome_email.png"  /></a></div></td></tr><tr><td valign="top"><div style="line-height:30px; font-size:16px;" class="top_text">Desejamos que o seu aniversário que está por vir seja repleto de alegrias e com muita saúde, paz e sucesso.

Aproveitamos para convidá-lo a comemorar com a gente.  Nossa equipe está pronta para atendê-lo e a seus convidados com toda a qualidade e atenção que vocês merecem.

Entre em contato, estamos a sua disposição.
</div></td></tr><tr><td valign="top"><a href="http://www.meurestaurante.com.br"><img src="https://www.wi5admin.com/new/Files/colabore/images/1549634244_bannerfacebook.jpg"  width="600" /></a></td></tr><tr><td valign="top"><div style="line-height:30px; font-size:14px;" class="top_text">Aqui entra o texto inferior, por exemplo, o seu endereço e informações de contato.
</div></td></tr> <tr><td valign="top"><table  style="table-layout:fixed;width:100%" border="0" cellspacing="0" cellpadding="0"><tbody><tr><td style="padding:0px 0px 30px 0px" bgcolor="">&nbsp;</td></tr></tbody></table></td></tr></table></td></tr></table></body></html>"""


if __name__ == '__main__':
    mailer  = Mailer('mail_server', 465, 'email', 'password', True)
    mailer.send('pythonica','stevobujica91@gmail.com', 'test', html)