import logging
import os

import boto3
import inquirer


LOG = logging.getLogger(__name__)


def setup(subparsers, parent_parser):
    summary = 'Switching between AWS config.'
    parser = subparsers.add_parser('config-switch', description=summary, help=summary, parents=[parent_parser])
    switch_subparsers = parser.add_subparsers(dest='config_switch_command', required=True, help='Available AWS config switch commands')

    profile_switch_summary = "Switch between available aws profile."
    profile_switch_parser = switch_subparsers.add_parser('profile', description=profile_switch_summary, help=profile_switch_summary, parents=[parent_parser])
    profile_switch_parser.set_defaults(func=switch_profile)

    region_switch_summary = "Switch between available aws region."
    region_switch_parser = switch_subparsers.add_parser('region', description=region_switch_summary, help=region_switch_summary, parents=[parent_parser])
    region_switch_parser.set_defaults(func=switch_region)


def switch_profile(args):
    session = boto3.Session(region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION")), profile_name=os.getenv("AWS_PROFILE"))
    available_profiles = session.available_profiles

    profile_inquiry = inquirer.List("profile", message="Choose a profile", choices=available_profiles, default=session.profile_name, carousel=True)
    answers = inquirer.prompt([profile_inquiry], theme=inquirer.themes.GreenPassion(), raise_keyboard_interrupt=True)

    profile = answers.get('profile') if answers.get('profile') != 'default' else None
    __update_file('profile', profile)


def switch_region(args):
    session = boto3.Session(region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION")), profile_name=os.getenv("AWS_PROFILE"))
    available_regions = session.get_available_regions('ec2')

    region_inquery = inquirer.List("region", message="Choose a region", choices=available_regions, default=session.region_name, carousel=True)
    answers = inquirer.prompt([region_inquery], theme=inquirer.themes.GreenPassion(), raise_keyboard_interrupt=True)

    region = answers.get('region') if answers.get('region') != session.region_name else None
    __update_file('region', region)


def __update_file(file_name, value):
    config_dir = os.path.expanduser(os.path.join('~', '.aws', 'fusion'))

    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    full_key = os.path.join(config_dir, file_name)

    with os.fdopen(os.open(full_key, os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
        f.truncate()
        if value is not None:
            f.write(value)
