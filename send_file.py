import os
import pickle
import base64
import logging
from typing import Any
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build
from constants import JSON
from dotenv import load_dotenv

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.metadata',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
    ]
json_path = os.path.join(os.getcwd(), JSON)

load_dotenv()


def get_services() -> Any:
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            logging.info("Using existing token to authenticate.")

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logging.info("Token is expired. Refreshing token.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                json_path, SCOPES, access_type='offline')
            creds = flow.run_local_server(port=8080)
            logging.info("No token detected. Generating new token.")
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return {
        "gmail": build('gmail', 'v1', credentials=creds),
    }


def create_message(sender: str, to: str, subject: str, body: str, file_path: str):
    """Create a message for an email."""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(body)
    message.attach(msg)

    # Attach the file
    try:
        attachment = open(file_path, "rb")  # Open the file in binary mode
    except Exception as e:
        logging.error(f"Could not open file {file_path}: {e}")
        return None

    # Create the attachment MIMEBase object
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
    message.attach(part)

    attachment.close()

    # Encode the message in base64 (URL-safe encoding)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def send_email(service, sender, to, subject, body, file_path):
    """Send an email using the Gmail API."""
    try:
        message = create_message(sender, to, subject, body, file_path)
        send_message = service.users().messages().send(userId="me", body=message).execute()
        logging.info(f'Message Id: {send_message["id"]}')
        return send_message
    except HttpError as error:
        logging.error(f'An error occurred: {error}')
