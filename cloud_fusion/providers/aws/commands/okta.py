import logging
from argparse import ArgumentParser

from ..assume_role import AssumeRoleWithSamlCache
from ..okta.api import device_auth
from ..okta.api import saml_assertion
from ..okta.api import session_and_token
from ..okta.api import verification_and_token


LOG = logging.getLogger(__name__)


def setup(subparsers, parent_parser):
    summary = 'Generate AWS session credentials from Okta.'
    parser: ArgumentParser = subparsers.add_parser('okta', description=summary, help=summary, parents=[parent_parser])
    okta_subparsers = parser.add_subparsers(dest='okta_command', required=True, help='Available Okta commands')

    device_auth_summary = 'Generate AWS session credentials using SAML assertion from Okta device authentication.'
    device_auth_parser = okta_subparsers.add_parser('device-auth', description=device_auth_summary, help=device_auth_summary, parents=[parent_parser])
    device_auth_parser.set_defaults(func=run_device_auth)
    device_auth_parser.add_argument('--org-domain', required=True, help="Full domain hostname of the Okta org e.g. example.okta.com")
    device_auth_parser.add_argument('--oidc-client-id', required=True, help="The ID is the identifier of the client is Okta app acting as the IdP for AWS")
    device_auth_parser.add_argument('--aws-acct-fed-app-id', required=True, help="The ID for the AWS Account Federation integration app")
    device_auth_parser.add_argument('--aws-iam-role', required=True, help="The AWS IAM Role ARN to assume")
    device_auth_parser.add_argument('--credential-process', action='store_true', help='Output the credential in AWS credential process syntax')


def run_device_auth(args):
    assume_role_with_cache = AssumeRoleWithSamlCache(args.aws_iam_role)

    if not assume_role_with_cache.does_valid_token_cache_exists():
        LOG.debug('Credential cache not found, invoking SAML')
        device_code, expires_in = device_auth(args.org_domain, args.oidc_client_id)
        access_token, id_token = verification_and_token(args.org_domain, args.oidc_client_id, device_code, expires_in)
        session_token = session_and_token(args.org_domain, args.oidc_client_id, access_token, id_token, args.aws_acct_fed_app_id)
        saml_response, roles, session_duration = saml_assertion(args.org_domain, session_token)
        assume_role_with_cache.assume_role_with_saml(saml_response, roles, session_duration)

    if args.credential_process:
        print(assume_role_with_cache.credential_process())
    else:
        print(assume_role_with_cache.environment_variable())


