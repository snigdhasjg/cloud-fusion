from .commands import init, open_browser, iam_user_credentials, okta, config_switch


def setup(subparsers, parent_parser):
    summary = 'AWS authentication and convenience commands.'
    parser = subparsers.add_parser('aws', description=summary, help=summary, parents=[parent_parser])
    aws_subparsers = parser.add_subparsers(dest='aws_command', required=True, help='Available AWS commands')

    _commands = [
        init,
        open_browser,
        iam_user_credentials,
        okta,
        config_switch
    ]
    [command.setup(aws_subparsers, parent_parser) for command in _commands]
