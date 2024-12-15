import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import logging

from constants import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION

load_dotenv()


def send_email_with_attachment(sender, recipient, subject, body_text, attachment_path):
    logging.info("Sending email.")
    ses_client = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY,
                              aws_secret_access_key=AWS_SECRET_KEY)
    file_name = 'spread.xlsx'

    # Tworzenie obiektu wiadomości
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # Dodanie treści wiadomości
    msg.attach(MIMEText(body_text, 'plain'))

    # Dodanie załącznika
    with open(attachment_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=file_name)
        part['Content-Disposition'] = f'attachment; filename={file_name}'
        msg.attach(part)

    try:
        # Wysyłanie wiadomości
        response = ses_client.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={
                'Data': msg.as_string()
            }
        )
    except ClientError as e:
        logging.error(e.response['Error']['Message'])
    else:
        logging.info(f"Email sent! Id: {response['MessageId']}")
