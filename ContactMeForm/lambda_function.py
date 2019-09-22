import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import boto3
import os
import requests
import json

logging.basicConfig(level=logging.DEBUG)


def get_secret(secret_name):
    """
    Gets secret from Secret Manager. The secret should be a string.

    :param secret_name: Name of string.
    :return: Secret string value.
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    # Decrypts secret using the associated KMS CMK.
    return get_secret_value_response['SecretString']


def captcha_validation(token: str):
    """
    Checks for validity of user recaptcha token,

    :param token: token string to be validate.
    :return: True if valid, False otherwise.
    """
    url = "https://www.google.com/recaptcha/api/siteverify"
    secret = json.loads(get_secret("CAPTCHA_SECRET"))['CAPTCHA_SECRET']
    payload = {
        "secret": secret,
        "response": token
    }
    response_raw = requests.post(url, data=payload)
    response_text = response_raw.text
    logging.debug(response_text)
    response = json.loads(response_text)
    return response['success']


def create_multipart_message(
        sender: str, recipients: list, title: str, text: str = None, html: str = None, attachments: list = None) \
        -> MIMEMultipart:
    """
    Creates a MIME multipart message object.
    Uses only the Python `email` standard library.
    Emails, both sender and recipients, can be just the email string or have the format 'The Name <the_email@host.com>'.
    Copied from https://stackoverflow.com/a/52105406

    :param sender: The sender.
    :param recipients: List of recipients. Needs to be a list, even if only one recipient.
    :param title: The title of the email.
    :param text: The text version of the email body (optional).
    :param html: The html version of the email body (optional).
    :param attachments: List of files to attach in the email.
    :return: A `MIMEMultipart` to be used to send the email.
    """
    multipart_content_subtype = 'alternative' if text and html else 'mixed'
    msg = MIMEMultipart(multipart_content_subtype)
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Record the MIME types of both parts - text/plain and text/html.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    if text:
        part = MIMEText(text, 'plain')
        msg.attach(part)
    if html:
        part = MIMEText(html, 'html')
        msg.attach(part)

    # Add attachments
    for attachment in attachments or []:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read())
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
            msg.attach(part)

    return msg


def send_mail(
        sender: str, recipients: list, title: str, text: str = None, html: str = None,
        attachments: list = None) -> dict:
    """
    Send email to recipients. Sends one mail to all recipients.
    The sender needs to be a verified email in SES.
    Copied from https://stackoverflow.com/a/52105406

    :param sender: The sender.
    :param recipients: List of recipients. Needs to be a list, even if only one recipient.
    :param title: The title of the email.
    :param text: The text version of the email body (optional).
    :param html: The html version of the email body (optional).
    :param attachments: List of files to attach in the email.
    :return: Response of ses_client.
    """
    msg = create_multipart_message(sender, recipients, title, text, html, attachments)
    ses_client = boto3.client('ses')  # Use your settings here
    return ses_client.send_raw_email(
        Source=sender,
        Destinations=recipients,
        RawMessage={'Data': msg.as_string()}
    )


def get_s3_object_text(s3_resource: boto3.session.Session.resource, bucket_name: str, key: str) -> str:
    """
    Downloads the given s3 object and converts the bytes to a string.

    :param s3_resource: Boto3 resource object for s3 bucket.
    :param bucket_name: Name of s3 bucket.
    :param key: Object key in bucket.
    :return: Contents of a s3 object as a string, assuming utf-8 encoding.
    """
    obj = s3_resource.Object(bucket_name, key)
    return obj.get()['Body'].read().decode('utf-8')


def format_mail(template: str, event: dict, ishtml: bool):
    """
    Formats the email template according to lambda triggering event.

    :param template: Email template.
    :param event: Event which triggered Lambda. Contains form fields.
    :param ishtml: True if template is HTML. Linebreaks are changed accordingly.
    :return: Formatted email template.
    """
    if ishtml:
        linebreak = '<br>'
    else:
        linebreak = '\n'
    header = "Someone filled the contact form"
    subtext = ""
    # uuid.uuid4().hex
    unsubscribe_key = "f4bd5dd85908487b904ea189fb81e753"  # Not actually applicable for Admin email ID
    keys = ['firstName', 'lastName', 'email', 'subject', 'message']
    for key in keys:
        subtext += "{}: {}{}".format(key, event[key], linebreak)
    template = template.replace('{{header}}', header)
    template = template.replace('{{subtext}}', subtext)
    template = template.replace('{{unsubscribe-key}}', unsubscribe_key)
    return template


def lambda_handler(event, context):
    logging.info(event)
    if captcha_validation(event['recaptcha']):
        s3_resource = boto3.resource('s3')
        sender = os.environ['SENDER']  # 'The Sender <the_sender@email.com>'
        recipients = [os.environ['ADMIN_EMAIL']]
        title = "Contact form filled by {} {}".format(event['firstName'], event['lastName'])
        # Text and HTML email templates are stored in S3 buckets.
        text = get_s3_object_text(s3_resource, os.environ['BUCKET_NAME'], os.environ['TEXT_TEMPLATE'])
        formatted_text = format_mail(text, event, False)
        html = get_s3_object_text(s3_resource, os.environ['BUCKET_NAME'], os.environ['HTML_TEMPLATE'])
        formatted_html = format_mail(html, event, True)
        try:
            response = send_mail(sender, recipients, title, formatted_text, formatted_html)
            logging.debug(response)
        except Exception as e:
            logging.exception("There was an exception while sending the mail")
        return {
            'message': 'Successful'
        }
    else:
        raise Exception("Malformed input")
