import datetime
import hashlib
import json
import logging
import os
import sys

import boto3
from botocore.exceptions import ClientError
from botocore.utils import JSONFileCache


LOG = logging.getLogger(__name__)


class AssumeRoleWithSamlCache:
    __CACHE_DIR = os.path.expanduser(os.path.join('~', '.aws', 'saml', 'cache'))
    __jsonFileCache = JSONFileCache(__CACHE_DIR)

    def __init__(self, role) -> None:
        LOG.debug('Initialize AssumeRoleWithSamlCache')
        self.__role = role
        self.__cache_key = hashlib.sha1(role.encode('utf-8')).hexdigest()
        self.__response = None

    def does_valid_token_cache_exists(self):
        if self.__cache_key in self.__jsonFileCache:
            response = self.__jsonFileCache[self.__cache_key]
            expiration = (datetime.datetime
                          .strptime(response['Credentials']['Expiration'], '%Y-%m-%dT%H:%M:%S%Z')
                          .replace(tzinfo=datetime.timezone.utc))
            current_utc_time = datetime.datetime.now(tz=datetime.timezone.utc)

            if expiration - current_utc_time >= datetime.timedelta(minutes=1):
                response['Credentials']['Expiration'] = expiration
                self.__response = response
                LOG.debug('Valid token exists. Can use cache')
                return True
        LOG.debug('No valid token exists')
        return False

    def credential_process(self):
        credentials = self.__response['Credentials']
        LOG.debug(f'Giving credential as aws credential process format')

        # https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html
        return json.dumps({
            "Version": 1,
            "AccessKeyId": credentials['AccessKeyId'],
            "SecretAccessKey": credentials['SecretAccessKey'],
            "SessionToken": credentials['SessionToken'],
            "Expiration": credentials['Expiration'].isoformat()
        })

    def environment_variable(self):
        credentials = self.__response['Credentials']
        LOG.debug(f'Giving credential as environment variable format')

        command = '$env:' if sys.platform == 'win32' else 'export '

        return '\n'.join([
            f'{command}AWS_ACCESS_KEY_ID="{credentials["AccessKeyId"]}"',
            f'{command}AWS_SECRET_ACCESS_KEY="{credentials["SecretAccessKey"]}"',
            f'{command}AWS_SESSION_TOKEN="{credentials["SessionToken"]}"'
        ])

    def assume_role_with_saml(self, saml_response, roles, session_duration):
        LOG.debug(f'Started assuming role with SAML')
        # Just need a dummy sts session client object to call assume role with saml
        client = boto3.Session(aws_access_key_id='dummy', aws_secret_access_key='dummy').client('sts')
        selected_role = self.__role
        try:
            response = client.assume_role_with_saml(
                RoleArn=selected_role,
                PrincipalArn=roles[selected_role],
                SAMLAssertion=saml_response,
                DurationSeconds=session_duration
            )
            LOG.debug('Got assume role response')
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code != 'ValidationError':
                raise
            LOG.debug(f'Retrying assume role with 3600s duration after {error_code}: {e}')
            response = client.assume_role_with_saml(
                RoleArn=selected_role,
                PrincipalArn=roles[selected_role],
                SAMLAssertion=saml_response,
                DurationSeconds=3600
            )
            LOG.debug('Got assume role fallback response')

        self.__jsonFileCache[self.__cache_key] = response

        self.__response = response
