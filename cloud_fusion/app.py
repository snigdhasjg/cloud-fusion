import argparse
import logging
from . import __version__

from .providers import aws, gcp
from .exceptions import handle_cli_errors


def main():
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument('-v', '--version', action='version', help="Display the version of this tool", version=__version__)
    global_parser.add_argument('--debug', action='store_true', help='Turn on debug logging')

    main_parser = argparse.ArgumentParser(prog='cloud-fusion', description='Unified CLI tool for streamlined cloud operations, enhancing developer productivity', parents=[global_parser])
    subparsers = main_parser.add_subparsers(dest='command', required=True, help='Available commands')

    commands = [
        aws,
        gcp
    ]
    [command.setup(subparsers, global_parser) for command in commands]

    args = main_parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not hasattr(args, 'func'):
        return

    with handle_cli_errors(debug=args.debug):
        args.func(args)


if __name__ == '__main__':
    main()
