import requests
from huey.contrib.djhuey import task
from django.conf import settings
from django.core.mail import EmailMessage
from mhackspace.feeds.helper import import_feeds


@task()
def update_homepage_feeds():
    import_feeds()
    return {"result": "Homepage feeds imported"}


matrix_url = "https://matrix.org/_matrix/client/r0"
matrix_login_url = matrix_url + "/login"
matrix_join_room_alias_url = (
    matrix_url + "/join/{room}?access_token={access_token}"
)
matrix_join_room_id_url = (
    matrix_url + "rooms/%21{room}/join?access_token={access_token}"
)
matrix_send_msg_url = (
    matrix_url
    + "/rooms/%21{room}/send/m.room.message?access_token={access_token}"
)


@task()
def send_email(
    email_to,
    subject,
    message,
    email_from="no-reply@maidstone-hackspace.org.uk",
    reply_to="no-reply@maidstone-hackspace.org.uk",
):

    if settings.EMAIL_NOTIFY is False:
        return
    email = EmailMessage(
        "[%s] - %s" % (settings.MSG_PREFIX, subject),
        message,
        "no-reply@maidstone-hackspace.org.uk",
        to=[email_to],
        headers={"Reply-To": "no-reply@maidstone-hackspace.org.uk"},
    )
    email.send()
    return {"result", "Email sent to %s" % email_to}


@task()
def matrix_message(message, prefix="", room="default"):
    # we dont rely on theses, so ignore if it goes wrong
    # TODO at least log that something has gone wrong
    try:
        # login
        details = {
            "type": "m.login.password",
            "user": settings.MATRIX_USER,
            "password": settings.MATRIX_PASSWORD,
        }
        r0 = requests.post(matrix_login_url, json=details)
        access_token = r0.json().get("access_token")

        # join room by id
        url_params = {
            "room": settings.MATRIX_ROOM.get(room),
            "access_token": access_token,
        }
        url = matrix_join_room_id_url.format(**url_params)
        r1 = requests.post(url)

        # send message
        url_params = {
            "room": settings.MATRIX_ROOM.get(room),
            "access_token": access_token,
        }
        url = matrix_send_msg_url.format(**url_params)
        details = {
            "msgtype": "m.text",
            "body": "[%s%s] %s" % (settings.MSG_PREFIX, prefix, message),
        }
        r2 = requests.post(url, json=details)
    except:
        pass
    return {"result", "Matrix message sent successfully"}


@task()
def twitter_message(message, prefix=""):
    import twitter

    api = twitter.Api(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token_key=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_SECRET,
    )
    try:
        status = api.PostUpdate(prefix + message)
        return {"result", "Twitter message sent successfully"}
    except UnicodeDecodeError:
        return {
            "result",
            "Your message could not be encoded. "
            "Perhaps it contains non-ASCII characters? "
            "Try explicitly specifying the encoding with the --encoding flag",
        }
    return {"result": "Twitter message sent successfully"}
