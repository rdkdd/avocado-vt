import logging
import os
import json

from avocado.core.settings import settings

# Avocado's plugin interface module has changed location. Let's keep
# compatibility with old for at, least, a new LTS release
try:
    from avocado.core.plugin_interfaces import JobPre, JobPost
except ImportError:
    from avocado.plugins.base import JobPre, JobPost


class ParamsCreationError(Exception):
    """
    Represents any error situation when attempting to create a params file
    """
    pass


class VTJobParams(JobPre, JobPost):

    name = 'vt-jobparams'
    description = 'Avocado-VT Job output params'

    def __init__(self):
        self.log = logging.getLogger("avocado.app")
        self.params_dir = os.path.expanduser(settings.get_value(
            section="plugins.vtparams",
            key="dir",
            key_type=str,
            default='/tmp'))

    def _create_params_file(self, job, prepost):
        """
        Creates the params file for this job process

        :param job: the currently running job
        :type job: :class:`avocado.core.job.Job`
        :raises: :class:`LockCreationError`
        :returns: the full path for the params file created
        :rtype: str
        """
        pattern = 'avocado-vt-params-%(jobid)s-%(uid)s-%(pp)s.json'
        path = pattern % {'jobid': job.unique_id,
                          'uid': os.getuid(),
                          'pp': prepost}
        path = os.path.join(self.params_dir, path)
        try:
            if prepost == 'pre':
                status = job.status
            else:
                status = self._parse_log_for_status(
                    os.path.join(job.logdir, 'results.json'))
            with open(path, 'w') as paramsfile:
                paramsfile.write('Test name: %s \nStatus: %s' %
                                 (job.test_suite[0][1]['name'], status))
            return path
        except Exception as e:
            raise ParamsCreationError(e)

    @staticmethod
    def _parse_log_for_status(result_log):
        """
        Get status of test from result_log file

        :param result_log: destination of results.json file
        :returns: test status
        :rtype: str
        """
        with open(result_log, 'r') as result_f:
            data = json.load(result_f)
        return data['tests'][0]['status']

    def pre(self, job):
        self._create_params_file(job, 'pre')

    def post(self, job):
        self._create_params_file(job, 'post')
