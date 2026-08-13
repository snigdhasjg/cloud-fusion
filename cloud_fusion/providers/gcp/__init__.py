from .commands import config_switch


def setup(subparsers, parent_parser):
    summary = 'GCP convenience commands.'
    parser = subparsers.add_parser('gcp', description=summary, help=summary, parents=[parent_parser])
    gcp_subparsers = parser.add_subparsers(dest='gcp_command', required=True, help='Available GCP commands')

    _commands = [
        config_switch
    ]
    [command.setup(gcp_subparsers, parent_parser) for command in _commands]
