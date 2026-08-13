import json
from urllib import parse
from urllib import request

from ...exceptions import CloudFusionException


ISSUER = "aws-console-python-script"
SESSION_DURATION_IN_SECONDS = 43200
_HTTP_TIMEOUT_SECONDS = 60


class AwsFederationException(CloudFusionException):
    """Exception for AWS console federation API call"""
    pass


def signin_url(creds, region_name, logout=True):
    login_request_url = __aws_login_url(
        creds.access_key, creds.secret_key, creds.token, region_name)
    if logout:
        return 'https://us-east-1.signin.aws.amazon.com/oauth?Action=logout' \
            f'&redirect_uri={parse.quote_plus(login_request_url)}'
    return login_request_url


def __aws_signin_token(access_key, secret_key, session_token) -> str:
    url_credentials = dict(sessionId=access_key,
                           sessionKey=secret_key, sessionToken=session_token)
    credentials_encoded = parse.quote_plus(json.dumps(url_credentials))
    request_url = 'https://signin.aws.amazon.com/federation?Action=getSigninToken' \
                  f'&Session={credentials_encoded}'  # f'&SessionDuration={SESSION_DURATION_IN_SECONDS}'

    with request.urlopen(request_url, timeout=_HTTP_TIMEOUT_SECONDS) as response:
        if not response.status == 200:
            raise AwsFederationException(f'Failed to get federation token: HTTP {response.status}')
        return json.loads(response.read())["SigninToken"]


def __aws_login_url(access_key, secret_key, session_token, region_name) -> str:
    destination_url_encoded = parse.quote_plus(
        "https://{}.console.aws.amazon.com/".format(region_name))
    signin_token_encoded = parse.quote_plus(
        __aws_signin_token(access_key, secret_key, session_token))
    return 'https://us-east-1.signin.aws.amazon.com/federation?Action=login' \
           f'&Issuer={ISSUER}' \
           f'&Destination={destination_url_encoded}' \
           f'&SigninToken={signin_token_encoded}'
