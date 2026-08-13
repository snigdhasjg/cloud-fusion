import argparse
import json
import sys

import keyring


def setup(subparsers, parent_parser):
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--access-key', required=True, help='AWS access key')
    common_parser.add_argument('--account-id', required=False, help='AWS Account ID for the name')
    common_parser.add_argument('--username', required=False, help='Username of a AWS user associated with the access key for the name')

    summary = 'IAM User credential helper.'
    parser = subparsers.add_parser('iam-user-credentials', description=summary, help=summary, parents=[parent_parser])
    credential_subparsers = parser.add_subparsers(dest='iam_user_credential_command', required=True, help='Available IAM User credential commands')

    store_summary = 'Store IAM user access key and secret key securely for streamlined authentication.'
    store_parser = credential_subparsers.add_parser('store', description=store_summary, help=store_summary, parents=[parent_parser, common_parser])
    store_parser.set_defaults(func=run_store)
    store_parser.add_argument('--secret-key', required=True, help='AWS secret key')

    get_summary = 'Retrieve IAM user credentials for AWS CLI profiles or application authentication.'
    get_parser = credential_subparsers.add_parser('get', description=get_summary, help=get_summary, parents=[parent_parser, common_parser])
    get_parser.set_defaults(func=run_get)
    get_parser.add_argument('--credential-process', action='store_true', help='Output the credential in AWS credential process syntax')


def run_store(args):
    service_name = '-'.join(filter(None, ['aws', args.account_id, args.username]))
    keyring.set_password(service_name, args.access_key, args.secret_key)


def run_get(args):
    service_name = '-'.join(filter(None, ['aws', args.account_id, args.username]))
    secret_key = keyring.get_password(service_name, args.access_key)

    if args.credential_process:
        # https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html
        print(json.dumps({
            "Version": 1,
            "AccessKeyId": args.access_key,
            "SecretAccessKey": secret_key
        }))
    else:
        command = '$env:' if sys.platform == 'win32' else 'export '

        print('\n'.join([
            f'{command}AWS_ACCESS_KEY_ID="{args.access_key}"',
            f'{command}AWS_SECRET_ACCESS_KEY="{secret_key}"'
        ]))
