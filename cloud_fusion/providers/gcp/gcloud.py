import json
import logging
import shutil
import subprocess

from ...exceptions import CloudFusionException


LOG = logging.getLogger(__name__)

GCLOUD = 'gcloud'


class GcloudNotFoundException(CloudFusionException):
    """Exception for gcloud CLI missing from PATH"""
    pass


class GcloudCommandException(CloudFusionException):
    """Exception for a gcloud invocation failing"""
    pass


def run(*args, timeout=60):
    """Run `gcloud <args> --quiet` and return stripped stdout. gcloud's own chatter goes to stderr."""
    executable = shutil.which(GCLOUD)
    if executable is None:
        raise GcloudNotFoundException(f'`{GCLOUD}` not found on PATH.')

    command = [executable, *args, '--quiet']
    LOG.debug(f'Running {command}')
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise GcloudNotFoundException(f'`{GCLOUD}` not found on PATH.') from e
    except subprocess.TimeoutExpired as e:
        raise GcloudCommandException(f'`{GCLOUD} {" ".join(args)}` timed out after {timeout}s') from e

    stderr = completed.stderr.strip()
    if stderr:
        LOG.debug(f'stderr: {stderr}')

    if completed.returncode != 0:
        raise GcloudCommandException(stderr or f'`{GCLOUD} {" ".join(args)}` exited with {completed.returncode}')

    return completed.stdout.strip()


def __run_json(*args, timeout=60):
    output = run(*args, timeout=timeout)
    if not output:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        raise GcloudCommandException(f'Unable to parse `{GCLOUD} {" ".join(args)}` output as json') from e


def configurations():
    """All named configurations with active flag, project and region of each."""
    return __run_json('config', 'configurations', 'list',
                       '--format=json(name,is_active,properties.core.project,properties.compute.region)') or []


def regions():
    """Compute Engine regions available to the active configuration's project."""
    return run('compute', 'regions', 'list', '--format=value(name)', timeout=120).splitlines()


def activate_configuration(name):
    run('config', 'configurations', 'activate', name)


def set_property(name, value):
    run('config', 'set', name, value)


def set_adc_quota_project(project):
    run('auth', 'application-default', 'set-quota-project', project)
