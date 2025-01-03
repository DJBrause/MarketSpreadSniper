import boto3
import os
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import logging

from constants import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION

load_dotenv()


def send_email_with_attachment(sender, recipient, subject, body_text, file_name):
    logging.info("Sending email.")
    ses_client = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY,
                              aws_secret_access_key=AWS_SECRET_KEY)
    current_directory = os.getcwd()
    attachment_path = os.path.join(current_directory, file_name)

    # Message content creation
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # Adding body text
    msg.attach(MIMEText(body_text, 'plain'))

    # Adding attachment
    with open(attachment_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=file_name)
        part['Content-Disposition'] = f'attachment; filename={file_name}'
        msg.attach(part)

    try:
        # Sending email
        response = ses_client.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={
                'Data': msg.as_string()
            }
        )
    except ClientError as e:
        logging.error(f"Error while sending email to {recipient}: {e.response['Error']['Message']}")
    else:
        logging.info(f"Email sent to {recipient}! Id: {response['MessageId']}")
