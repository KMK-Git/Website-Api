import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import boto3
import os
import datetime
import html

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)


def create_multipart_message(sender: str, recipient_mail: str, bcc_mail: str, title: str, text: str = None,
                             html_text: str = None, attachments: list = None) -> MIMEMultipart:
    """
    Creates a MIME multipart message object.
    Uses only the Python `email` standard library.
    Emails, both sender and recipients, can be just the email string or have the format 'The Name <the_email@host.com>'.
    Copied from https://stackoverflow.com/a/52105406

    :param sender: The sender.
    :param recipient_mail: Mail will be sent To.
    :param bcc_mail: Mail will be sent Bcc.
    :param title: The title of the email.
    :param text: The text version of the email body (optional).
    :param html_text: The html version of the email body (optional).
    :param attachments: List of files to attach in the email.
    :return: A `MIMEMultipart` to be used to send the email.
    """
    multipart_content_subtype = 'alternative' if text and html_text else 'mixed'
    msg = MIMEMultipart(multipart_content_subtype)
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = recipient_mail
    msg['Bcc'] = bcc_mail

    # Record the MIME types of both parts - text/plain and text/html.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    if text:
        part = MIMEText(text, 'plain')
        msg.attach(part)
    if html_text:
        part = MIMEText(html_text, 'html')
        msg.attach(part)

    # Add attachments
    for attachment in attachments or []:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read())
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
            msg.attach(part)

    return msg


def send_mail(sender: str, recipient_mail: str, bcc_mail: str, title: str, text: str = None, html_text: str = None,
              attachments: list = None) -> dict:
    """
    Send email to recipients. Sends one mail to all recipients.
    The sender needs to be a verified email in SES.
    Copied from https://stackoverflow.com/a/52105406

    :param sender: The sender.
    :param recipient_mail: Mail will be sent To.
    :param bcc_mail: Mail will be sent Bcc.
    :param title: The title of the email.
    :param text: The text version of the email body (optional).
    :param html_text: The html version of the email body (optional).
    :param attachments: List of files to attach in the email.
    :return: Response of ses_client.
    """
    msg = create_multipart_message(sender, recipient_mail, bcc_mail, title, text, html_text, attachments)
    ses_client = boto3.client('ses')  # Use your settings here
    return ses_client.send_raw_email(
        Source=sender,
        Destinations=[recipient_mail, bcc_mail],
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


def format_mail(template: str, birthday: dict, ishtml: bool):
    """
    Formats the email template according to lambda triggering event.

    :param template: Email template.
    :param birthday: DynamoDB query result dict.
    :param ishtml: True if template is HTML. Linebreaks are changed accordingly.
    :return: Formatted email template.
    """
    header = "Happy birthday {}, from Kaustubh Khavnekar!".format(birthday['FirstName']['S'])
    subtext = birthday['Subtext']['S']
    if ishtml:
        subtext = html.escape(subtext).replace('\n', '<br/>')
    else:
        subtext = subtext.replace('\n', '\r\n')
    # uuid.uuid4().hex
    unsubscribe_key = birthday['UnsubscribeKey']['S']
    template = template.replace('{{header}}', header)
    template = template.replace('{{subtext}}', subtext)
    template = template.replace('{{unsubscribe-key}}', unsubscribe_key)
    return template


def get_birthday_list() -> list:
    """
    Queries DynamoDB to get list of people whose birthdays are now midnight.

    :return: List of DynamoDB query result dict.
    """
    dynamodb_client = boto3.client('dynamodb')

    current_datetime = datetime.datetime.utcnow()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_time = current_datetime.strftime('%H:%M')

    results = dynamodb_client.query(
        ExpressionAttributeValues={
            ':dateValue': {
                'S': current_date,
            }
        },
        KeyConditionExpression='DateKey = :dateValue',
        TableName='BirthdaysTable',
    )
    logger.debug(results)

    birthday_list = []
    for birthday in results['Items']:
        birthday_time = birthday['TimeName']['S'].split('-')[0]
        if birthday_time == current_time:
            birthday_list.append(birthday)
    return birthday_list


def lambda_handler(event, context):
    birthday_list = get_birthday_list()

    s3_resource = boto3.resource('s3')
    sender = os.environ['SENDER']  # 'The Sender <the_sender@email.com>'
    bcc_mail = os.environ['ADMIN_EMAIL']

    for birthday in birthday_list:
        title = "Happy birthday {}, from Kaustubh Khavnekar!".format(birthday['FirstName']['S'])
        recipient_mail = birthday['Email']['S']
        # Text and HTML email templates are stored in S3 buckets.
        text = get_s3_object_text(s3_resource, os.environ['BUCKET_NAME'], os.environ['TEXT_TEMPLATE'])
        formatted_text = format_mail(text, birthday, False)
        html_text = get_s3_object_text(s3_resource, os.environ['BUCKET_NAME'], os.environ['HTML_TEMPLATE'])
        formatted_html = format_mail(html_text, birthday, True)
        try:
            response = send_mail(sender, recipient_mail, bcc_mail, title, formatted_text, formatted_html)
            logger.debug(response)
        except Exception:
            logging.exception("There was an exception while sending the mail")
