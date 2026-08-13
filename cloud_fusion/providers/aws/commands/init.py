import configparser
import logging
import os
import sys


LOG = logging.getLogger(__name__)


def setup(subparsers, parent_parser):
    summary = 'Initialize fusion app with creation of aws fusion alias.'
    parser = subparsers.add_parser('init', description=summary, help=summary, parents=[parent_parser])
    parser.set_defaults(func=run)


def run(args):
    cli_dir = os.path.expanduser(os.path.join('~', '.aws', 'cli'))

    def create_alias(config: configparser.ConfigParser):
        LOG.debug('Creating fusion aws alias')
        if not config.has_section('toplevel'):
            config.add_section('toplevel')
        config['toplevel']['fusion'] = f'!"{sys.executable}" -m cloud_fusion.app aws'

    def update_aws_cli_alias_file():
        if not os.path.isdir(cli_dir):
            LOG.debug(f"Path {cli_dir} doesn't exists, creating")
            os.makedirs(cli_dir)
        cli_alias_full_path = os.path.join(cli_dir, 'alias')
        config = configparser.ConfigParser()

        if os.path.isfile(cli_alias_full_path):
            LOG.debug(f'Found alias file {cli_alias_full_path}')
            config.read(cli_alias_full_path)

        create_alias(config)

        with os.fdopen(os.open(cli_alias_full_path, os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
            f.truncate()
            config.write(f)
            LOG.debug(f'Updated alias file {cli_alias_full_path}')

    update_aws_cli_alias_file()
