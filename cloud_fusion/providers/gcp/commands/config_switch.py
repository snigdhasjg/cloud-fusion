import logging

import inquirer

from ....exceptions import CloudFusionException
from ..gcloud import configurations, regions, activate_configuration, set_property, set_adc_quota_project, GcloudCommandException


LOG = logging.getLogger(__name__)

REGION_PROPERTY = 'compute/region'


def setup(subparsers, parent_parser):
    summary = 'Switching between GCP config.'
    parser = subparsers.add_parser('config-switch', description=summary, help=summary, parents=[parent_parser])
    switch_subparsers = parser.add_subparsers(dest='config_switch_command', required=True, help='Available GCP config switch commands')

    configuration_switch_summary = "Switch between available gcloud configuration."
    configuration_switch_parser = switch_subparsers.add_parser('configuration', description=configuration_switch_summary, help=configuration_switch_summary, parents=[parent_parser])
    configuration_switch_parser.add_argument('--skip-quota-project', action='store_true', help="Skip updating the application-default credentials quota project after switching")
    configuration_switch_parser.set_defaults(func=switch_configuration)

    region_switch_summary = "Switch between available gcloud compute region."
    region_switch_parser = switch_subparsers.add_parser('region', description=region_switch_summary, help=region_switch_summary, parents=[parent_parser])
    region_switch_parser.set_defaults(func=switch_region)


def switch_configuration(args):
    available_configurations = configurations()
    if not available_configurations:
        raise CloudFusionException('No gcloud configuration found. Create one with `gcloud config configurations create <name>`')

    active = __active(available_configurations)
    choices = [each.get('name') for each in available_configurations]

    configuration_inquiry = inquirer.List("configuration", message="Choose a configuration", choices=choices, default=active.get('name') if active else None, carousel=True)
    answers = inquirer.prompt([configuration_inquiry], theme=inquirer.themes.GreenPassion(), raise_keyboard_interrupt=True)

    chosen = next(each for each in available_configurations if each.get('name') == answers.get('configuration'))
    name = chosen.get('name')

    activate_configuration(name)
    LOG.debug(f'Activated configuration [{name}]')

    if args.skip_quota_project:
        return

    project = (chosen.get('properties') or {}).get('core', {}).get('project')
    if project is None:
        LOG.debug(f'Configuration [{name}] has no project set - skipped updating the application-default quota project')
        return

    try:
        set_adc_quota_project(project)
        LOG.debug(f'Updated application-default quota project to [{project}]')
    except GcloudCommandException:
        LOG.warning(f'Could not update the application-default quota project', exc_info=args.debug)


def switch_region(args):
    active = __active(configurations())
    if active is None:
        raise CloudFusionException('No active gcloud configuration found. Activate one with `cloud-fusion gcp config-switch configuration`')

    properties = active.get('properties') or {}
    if (properties.get('core') or {}).get('project') is None:
        raise CloudFusionException(f"No project set on configuration [{active.get('name')}]. Listing compute regions needs one - set it with `gcloud config set project <project-id>`")

    current_region = (properties.get('compute') or {}).get('region')
    available_regions = regions()
    if not available_regions:
        raise CloudFusionException('No compute region returned by gcloud')

    region_inquiry = inquirer.List("region", message="Choose a region", choices=available_regions, default=current_region, carousel=True)
    answers = inquirer.prompt([region_inquiry], theme=inquirer.themes.GreenPassion(), raise_keyboard_interrupt=True)

    region = answers.get('region')
    set_property(REGION_PROPERTY, region)
    LOG.debug(f'Updated region to [{region}] on configuration [{active.get("name")}]')


def __active(available_configurations):
    return next((each for each in available_configurations if each.get('is_active')), None)
