import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from socket import gaierror

from injector import inject

from ..configuration.services import ConfigService
from ..dependency import IScoped
from ..logging.loggers.database import SqlLogger


class EmailProvider(IScoped):
    @inject
    def __init__(self, config_service: ConfigService, sql_logger: SqlLogger):
        super().__init__()
        self.sql_logger = sql_logger
        self.config_service = config_service

    def send(self, to, subject, body):
        smtp = None
        try:
            host = self.config_service.get_config_by_name("EMAIL_HOST")
            port = self.config_service.get_config_by_name("EMAIL_PORT")
            smtp_address = self.config_service.get_config_by_name("EMAIL_SMTP")
            from_address = self.config_service.get_config_by_name("EMAIL_FROM")
            user = self.config_service.get_config_by_name("EMAIL_USER")
            password = self.config_service.get_config_by_name("EMAIL_PASSWORD")

            if host is None:
                self.sql_logger.error("Email not configured")
                return
            if smtp_address is None:
                self.sql_logger.error("Email smtp not configured")
                return
            if from_address is None:
                self.sql_logger.error("Email from_address not configured")
                return

            # Create the root message and fill in the from, to, and subject headers
            msg_root = MIMEMultipart('related')
            msg_root[
                'Subject'] = subject
            msg_root['From'] = from_address
            recipients = ""
            if isinstance(to, list):
                recipients = ", ".join(to)
            msg_root['To'] = recipients
            msg_root.preamble = 'This is a multi-part message in MIME format.'

            # Encapsulate the plain and HTML versions of the message body in an
            # 'alternative' part, so message agents can decide which they want to display.
            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)
            html = body

            # msgText = MIMEText('<b>Some <i>HTML</i> text</b> and an image.<br><img src="cid:image1"><br>Nifty!',
            # 'html') msgAlternative.attach(msgText)
            msg_text = MIMEText(html, "html")
            msg_alternative.attach(msg_text)

            # # This example assumes the image is in the current directory
            # file_path_1 = os.path.join(root_directory, 'image1.jpg')
            # fp_1 = open(file_path_1, 'rb')
            # msgImage_1 = MIMEImage(fp_1.read())
            # fp_1.close()
            # msgImage_1.add_header('Content-ID', '<image1>')
            # msgRoot.attach(msgImage_1)
            try:
                smtp = smtplib.SMTP(host, port)
                # smtp.connect(host, port)
                if user is not None and user != '' and password is not None and password != '':
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.login(user, password)
                smtp.sendmail(smtp_address, to, msg_root.as_string())
            finally:
                if smtp is not None:
                    smtp.quit()

        except (gaierror, ConnectionRefusedError)as ex:
            # tell the script to report if your message was sent or which errors need to be fixed
            self.sql_logger.error('Failed to connect to the server. Bad connection settings? Error:' + str(ex))
        except smtplib.SMTPServerDisconnected as ex:
            self.sql_logger.error('Failed to connect to the server. Wrong user/password? Error:' + str(ex))
        except smtplib.SMTPException as ex:
            self.sql_logger.error('SMTP error occurred: ' + str(ex))
        else:
            self.sql_logger.info('Email sent successfully')
        finally:
            if smtp is not None:
                smtp.close()
