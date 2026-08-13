import base64
import json
import logging
import time
import webbrowser

import requests
from bs4 import BeautifulSoup

from ....exceptions import CloudFusionException


LOG = logging.getLogger(__name__)

_HTTP_TIMEOUT_SECONDS = 60

class OktaApiException(CloudFusionException):
    """Exception for Okta API call"""
    pass


def device_auth(org_domain, oidc_client_id):
    LOG.debug('Started device auth')
    url = f'https://{org_domain}/oauth2/v1/device/authorize'
    payload = {
        'client_id': oidc_client_id,
        'scope': 'openid okta.apps.sso okta.apps.read'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload, timeout=_HTTP_TIMEOUT_SECONDS)
    response_body = response.json()
    if response.status_code >= 300:
        LOG.error(f'Got {response.status_code} error in getting device code: {json.dumps(response_body)}')
        raise OktaApiException(f'Device code request failed with status {response.status_code}')

    LOG.debug(f'Device code response: {json.dumps(response_body)}')

    verification_url = response_body['verification_uri_complete']
    webbrowser.open_new_tab(verification_url)

    return response_body['device_code'], response_body['expires_in']


def verification_and_token(org_domain, oidc_client_id, device_code, expires_in):
    LOG.debug('Started verification of device code')
    url = f'https://{org_domain}/oauth2/v1/token'
    payload = {
        'client_id': oidc_client_id,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    time_passed = 0
    waiting_time_each_iteration = 5
    while True:
        response = requests.post(url, headers=headers, data=payload, timeout=_HTTP_TIMEOUT_SECONDS)
        response_body = response.json()

        # Check for authorization pending
        if response.status_code == 400 and response_body['error'] == 'authorization_pending':
            LOG.debug('Waiting for verification')
            time.sleep(waiting_time_each_iteration)
            time_passed += waiting_time_each_iteration
            if time_passed >= expires_in:
                LOG.error(f'Maximum waiting ({expires_in}s) for verification has exhausted')
                raise OktaApiException(f'Device verification timed out after {expires_in}s')
            continue

        # Check for successful verification
        if response.status_code == 200:
            break

        # Unexpected state. Die.
        LOG.error(f'Got {response.status_code} error during verification of device code: {json.dumps(response_body)}')
        raise OktaApiException(f'Device code verification failed with status {response.status_code}')

    LOG.debug(f'Token response: {json.dumps(response_body)}')
    return response_body['access_token'], response_body['id_token']


def session_and_token(org_domain, oidc_client_id, access_token, id_token, aws_acct_fed_app_id):
    LOG.debug('Started getting of session token')
    url = f'https://{org_domain}/oauth2/v1/token'
    payload = {
        'client_id': oidc_client_id,
        'actor_token': access_token,
        'actor_token_type': 'urn:ietf:params:oauth:token-type:access_token',
        'subject_token': id_token,
        'subject_token_type': 'urn:ietf:params:oauth:token-type:id_token',
        'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
        'requested_token_type': 'urn:okta:oauth:token-type:web_sso_token',
        'audience': f'urn:okta:apps:{aws_acct_fed_app_id}'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, headers=headers, data=payload, timeout=_HTTP_TIMEOUT_SECONDS)
    response_body = response.json()
    if response.status_code >= 300:
        LOG.error(f'Got {response.status_code} error in session token: {json.dumps(response_body)}')
        raise OktaApiException(f'Session token exchange failed with status {response.status_code}')

    LOG.debug(f'Session token response: {json.dumps(response_body)}')
    return response_body['access_token']


def saml_assertion(org_domain, session_token):
    LOG.debug('Started SAML assertion')
    # Get SAML assertion
    url = f'https://{org_domain}/login/token/sso'
    query_params = {
        'token': session_token
    }
    response = requests.get(url, params=query_params, timeout=_HTTP_TIMEOUT_SECONDS)
    if response.status_code >= 300:
        LOG.error(f'Got {response.status_code} error while getting SAML response')
        raise OktaApiException(f'SAML assertion request failed with status {response.status_code}')

    # Extract response value from SAML assertion call
    parser = BeautifulSoup(response.text, "html.parser")
    saml_response = parser.find("input", {"name": "SAMLResponse"})['value']
    parser = BeautifulSoup(base64.b64decode(saml_response), features="xml")

    # Retrieve list of Roles from the SAML assertion
    roles = {}
    role_xml = parser.find("saml2:Attribute", {"Name": "https://aws.amazon.com/SAML/Attributes/Role"})
    for role in role_xml.find_all("saml2:AttributeValue"):
        idp_and_role = role.text.split(',')
        roles[idp_and_role[1]] = idp_and_role[0]

    session_duration_xml = parser.find("saml2:Attribute", {"Name": "https://aws.amazon.com/SAML/Attributes/SessionDuration"})
    session_duration = session_duration_xml.find("saml2:AttributeValue").text

    LOG.debug(f'Got valid SAML response: {saml_response}')
    return saml_response, roles, int(session_duration)
