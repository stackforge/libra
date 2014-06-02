# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import gear
import json

from time import sleep
from novaclient import exceptions
from oslo.config import cfg
from libra.openstack.common import log
from libra.mgm.nova import Node, BuildError, NotFound

POLL_COUNT = 10
POLL_SLEEP = 60

LOG = log.getLogger(__name__)


class DisconnectClient(gear.Client):
    def handleDisconnect(self, job):
        job.disconnect = True


class DisconnectJob(gear.Job):
    def __init__(self, name, arguments):
        super(DisconnectJob, self).__init__(name, arguments)
        self.disconnect = False


class BuildController(object):
    RESPONSE_FIELD = 'response'
    RESPONSE_SUCCESS = 'PASS'
    RESPONSE_FAILURE = 'FAIL'

    def __init__(self, msg):
        self.msg = msg

    def run(self):
        try:
            nova = Node()
        except Exception:
            LOG.exception("Error initialising Nova connection")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        LOG.info("Building a requested Nova instance")
        try:
            node_id = nova.build()
            LOG.info("Build command sent to Nova")
        except BuildError as exc:
            LOG.exception(
                "{0}, node {1}".format(exc.msg, exc.node_name)
            )
            name = exc.node_name
            # Node may have built despite error
            try:
                node_id = nova.get_node(name)
            except NotFound:
                LOG.error(
                    "No node found for {0}, giving up on it".format(name)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            except exceptions.ClientException:
                LOG.exception(
                    'Error getting failed node info from Nova for {0}'
                    .format(name)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
        if node_id > 0:
            self._wait_until_node_ready(nova, node_id)
            if self.msg[self.RESPONSE_FIELD] == self.RESPONSE_SUCCESS:
                status = self._test_node(self.msg['name'])
                if not status:
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg
        else:
            LOG.error(
                'Node build did not return an ID, cannot find it'
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

    def _wait_until_node_ready(self, nova, node_id):
        for x in xrange(1, 10):
            try:
                resp, status = nova.status(node_id)
            except NotFound:
                LOG.error(
                    'Node {0} can no longer be found'.format(node_id)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            except exceptions.ClientException:
                LOG.exception(
                    'Error getting status from Nova'
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            if resp.status_code not in (200, 203):
                LOG.error(
                    'Error geting status from Nova, error {0}'
                    .format(resp.status_code)
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            status = status['server']
            if status['status'] == 'ACTIVE':
                self.msg['name'] = status['name']
                addresses = status['addresses'].itervalues().next()
                for address in addresses:
                    if not address['addr'].startswith('10.'):
                        break
                self.msg['addr'] = address['addr']
                self.msg['type'] = "basename: {0}, image: {1}".format(
                    cfg.CONF['mgm']['node_basename'],
                    cfg.CONF['mgm']['nova_image']
                )
                self.msg['az'] = cfg.CONF['mgm']['az']
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
                LOG.info('Node {0} returned'.format(status['name']))
                return self.msg
            sleep(60)

        LOG.error(
            "Node {0} didn't come up after 10 minutes".format(node_id)
        )
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        return self.msg

    def _test_node(self, name):
        """ Run diags on node, blow it away if bad """

        client = DisconnectClient()

        for server in cfg.CONF['gearman']['servers']:
            host, port = server.split(':')
            client.addServer(host,
                             int(port),
                             cfg.CONF['gearman']['ssl_key'],
                             cfg.CONF['gearman']['ssl_cert'],
                             cfg.CONF['gearman']['ssl_ca'])

        client.waitForServer()

        job_data = {'hpcs_action': 'DIAGNOSTICS'}

        job = DisconnectJob(str(name), json.dumps(job_data))

        client.submitJob(job)

        pollcount = 0
        # Would like to make these config file settings
        while not job.complete\
                and pollcount < POLL_COUNT\
                and not job.disconnect:
            sleep(POLL_SLEEP)
            pollcount += 1

        if job.disconnect:
            LOG.error('Gearman Job server fail - disconnect')
            return False

        # We timed out waiting for the job to finish
        if not job.complete:
            LOG.warning('Timeout getting diags from {0}'.format(name))
            return False

        result = json.loads(job.data[0])

        LOG.debug(result)

        # Would only happen if DIAGNOSTICS call not supported
        if result['hpcs_response'] == 'FAIL':
            return True

        if result['network'] == 'FAIL':
            return False

        gearman_count = 0
        gearman_fail = 0
        for gearman_test in result['gearman']:
            gearman_count += 1
            if gearman_test['status'] == 'FAIL':
                LOG.info(
                    'Device {0} cannot talk to gearman {1}'
                    .format(name, gearman_test['host'])
                )
                gearman_fail += 1
        # Need 2/3rds gearman up
        max_fail_count = gearman_count / 3
        if gearman_fail > max_fail_count:
            return False
        return True
