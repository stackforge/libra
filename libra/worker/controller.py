# Copyright 2012 Hewlett-Packard Development Company, L.P.
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

import socket

from oslo.config import cfg

from libra import __version__ as libra_version
from libra import __release__ as libra_release
from libra.common.exc import DeletedStateError
from libra.common.faults import BadRequest
from libra.openstack.common import log
from libra.worker.drivers import base

LOG = log.getLogger(__name__)


class LBaaSController(object):

    NODE_OK = "ENABLED"
    NODE_ERR = "DISABLED"
    RESPONSE_FAILURE = "FAIL"
    RESPONSE_SUCCESS = "PASS"
    ACTION_FIELD = 'hpcs_action'
    RESPONSE_FIELD = 'hpcs_response'
    ERROR_FIELD = 'hpcs_error'
    LBLIST_FIELD = 'loadBalancers'
    OBJ_STORE_TYPE_FIELD = 'hpcs_object_store_type'
    OBJ_STORE_BASEPATH_FIELD = 'hpcs_object_store_basepath'
    OBJ_STORE_ENDPOINT_FIELD = 'hpcs_object_store_endpoint'
    OBJ_STORE_TOKEN_FIELD = 'hpcs_object_store_token'

    def __init__(self, driver, json_msg):
        self.driver = driver
        self.msg = json_msg

    def run(self):
        """
        Process the JSON message and return a JSON response.
        """

        if self.ACTION_FIELD not in self.msg:
            LOG.error("Missing `%s` value" % self.ACTION_FIELD)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        action = self.msg[self.ACTION_FIELD].upper()

        try:
            if action == 'UPDATE':
                return self._action_update()
            elif action == 'SUSPEND':
                return self._action_suspend()
            elif action == 'ENABLE':
                return self._action_enable()
            elif action == 'DELETE':
                return self._action_delete()
            elif action == 'DISCOVER':
                return self._action_discover()
            elif action == 'ARCHIVE':
                return self._action_archive()
            elif action == 'METRICS':
                return self._action_metrics()
            elif action == 'STATS':
                return self._action_stats()
            elif action == 'DIAGNOSTICS':
                return self._action_diagnostic()
            else:
                LOG.error("Invalid `%s` value: %s", self.ACTION_FIELD, action)
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
        except Exception as e:
            LOG.error("Controller exception: %s, %s", e.__class__, e)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

    def _action_diagnostic(self):
        """
        Returns the results of a diagnostic run

        This message is used to see if the worker that was built will actually
        function as a load balancer
        """
        # Gearman test
        self.msg['gearman'] = []
        for host_port in cfg.CONF['gearman']['servers']:
            host, port = host_port.split(':')
            try:
                self._check_host(host, int(port))
            except:
                self.msg['gearman'].append(
                    {'host': host, 'status': self.RESPONSE_FAILURE}
                )
            else:
                self.msg['gearman'].append(
                    {'host': host, 'status': self.RESPONSE_SUCCESS}
                )
        # Outgoing network test
        try:
            # TODO: make this configurable
            self._check_host('google.com', 80)
        except:
            self.msg['network'] = self.RESPONSE_FAILURE
        else:
            self.msg['network'] = self.RESPONSE_SUCCESS

        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _check_host(self, ip, port):
        # TCP connect check to see if floating IP was assigned correctly
        sock = socket.socket()
        sock.settimeout(5)
        try:
            sock.connect((ip, port))
            sock.close()
            return True
        except socket.error:
            LOG.error(
                "TCP connect error to gearman server {0}"
                .format(ip)
            )
            raise

    def _set_lb_options(self, protocol, options):
        """
        Parse load balancer options.

        options
            Dictionary of load balancer options.

        Returns: True on success, False otherwise
        """

        # Default timeout values in milliseconds
        client_val = 30000
        server_val = 30000
        connect_val = 30000
        retries_val = 3

        if 'client_timeout' in options:
            client_val = options['client_timeout']
        if 'server_timeout' in options:
            server_val = options['server_timeout']
        if 'connect_timeout' in options:
            connect_val = options['connect_timeout']
        if 'connect_retries' in options:
            retries_val = options['connect_retries']

        try:
            self.driver.set_timeouts(protocol, client_val, server_val,
                                     connect_val, retries_val)
        except NotImplementedError:
            pass
        except Exception as e:
            error = "Failed to set timeout values: %s" % e
            LOG.error(error)
            self.msg[self.ERROR_FIELD] = error
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return False

        return True

    def _action_discover(self):
        """
        Return service discovery information.

        This message type is currently used to report the Libra version,
        which can be used to determine which messages are supported.
        """
        self.msg['version'] = libra_version
        self.msg['release'] = libra_release
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_update(self):
        """
        Create/Update a Load Balancer.

        This is the only method (so far) that actually parses the contents
        of the JSON message (other than the ACTION_FIELD field). Modifying
        the JSON message structure likely means this method will need to
        be modified, unless the change involves fields that are ignored.
        """

        try:
            self.driver.init()
        except NotImplementedError:
            pass
        except Exception as e:
            LOG.error("Selected driver failed initialization.")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        if self.LBLIST_FIELD not in self.msg:
            return BadRequest(
                "Missing '%s' element" % self.LBLIST_FIELD
            ).to_json()

        lb_list = self.msg[self.LBLIST_FIELD]

        for current_lb in lb_list:
            if 'nodes' not in current_lb:
                return BadRequest("Missing 'nodes' element").to_json()

            if 'protocol' not in current_lb:
                return BadRequest(
                    "Missing required 'protocol' value."
                ).to_json()
            else:
                port = None
                if 'port' in current_lb:
                    port = current_lb['port']
                try:
                    self.driver.add_protocol(current_lb['protocol'], port)
                except NotImplementedError:
                    LOG.error(
                        "Selected driver does not support setting protocol."
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
                except Exception as e:
                    LOG.error(
                        "Failure trying to set protocol: %s, %s" %
                        (e.__class__, e)
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg

            if 'algorithm' in current_lb:
                algo = current_lb['algorithm'].upper()
                if algo == 'ROUND_ROBIN':
                    algo = base.LoadBalancerDriver.ROUNDROBIN
                elif algo == 'LEAST_CONNECTIONS':
                    algo = base.LoadBalancerDriver.LEASTCONN
                else:
                    LOG.error("Invalid algorithm: %s" % algo)
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
            else:
                algo = base.LoadBalancerDriver.ROUNDROBIN

            try:
                self.driver.set_algorithm(current_lb['protocol'], algo)
            except NotImplementedError:
                LOG.error(
                    "Selected driver does not support setting algorithm."
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            except Exception as e:
                LOG.error(
                    "Selected driver failed setting algorithm."
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg

            if 'monitor' in current_lb:
                monitor = current_lb['monitor']
                for opt in ['type', 'delay', 'timeout', 'attempts']:
                    if opt not in monitor:
                        return BadRequest("Missing monitor value '%s'" %
                                          opt).to_json()
                if 'path' not in monitor:
                    monitor['path'] = '/'

                try:
                    self.driver.add_monitor(current_lb['protocol'],
                                            monitor['type'],
                                            monitor['delay'],
                                            monitor['timeout'],
                                            monitor['attempts'],
                                            monitor['path'])
                except NotImplementedError:
                    LOG.error(
                        "Selected driver does not support adding healthchecks."
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
                except Exception as e:
                    LOG.error(
                        "Selected driver failed adding healthchecks: %s, %s" %
                        (e.__class__, e)
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg

            if 'options' in current_lb:
                lb_options = current_lb['options']
            else:
                lb_options = {}

            # Always call _set_lb_options() since it sets sensible defaults
            if not self._set_lb_options(current_lb['protocol'], lb_options):
                return self.msg

            for lb_node in current_lb['nodes']:
                port = None
                address = None
                node_id = None
                weight = None
                backup = False

                if 'port' in lb_node:
                    port = lb_node['port']
                else:
                    return BadRequest("Missing node 'port'").to_json()

                if 'address' in lb_node:
                    address = lb_node['address']
                else:
                    return BadRequest("Missing node 'address'").to_json()

                if 'id' in lb_node and lb_node['id'] != '':
                    node_id = lb_node['id']
                else:
                    return BadRequest("Missing node 'id'").to_json()

                if 'weight' in lb_node:
                    weight = lb_node['weight']

                if 'backup' in lb_node and lb_node['backup'].lower() == 'true':
                    backup = True

                try:
                    self.driver.add_server(current_lb['protocol'],
                                           node_id,
                                           address,
                                           port,
                                           weight,
                                           backup)
                except NotImplementedError:
                    lb_node['condition'] = self.NODE_ERR
                    error = "Selected driver does not support adding a server"
                    LOG.error(error)
                    self.msg[self.ERROR_FIELD] = error
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
                except Exception as e:
                    lb_node['condition'] = self.NODE_ERR
                    error = "Failure adding server %s: %s" % (node_id, e)
                    LOG.error(error)
                    self.msg[self.ERROR_FIELD] = error
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
                else:
                    LOG.debug("Added server: %s:%s" % (address, port))
                    lb_node['condition'] = self.NODE_OK

        try:
            self.driver.create()
        except NotImplementedError:
            LOG.error(
                "Selected driver does not support CREATE action."
            )
            for current_lb in lb_list:
                for lb_node in current_lb['nodes']:
                    lb_node['condition'] = self.NODE_ERR
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            LOG.error("CREATE failed: %s, %s" % (e.__class__, e))
            for lb_node in current_lb['nodes']:
                lb_node['condition'] = self.NODE_ERR
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            LOG.info("Activated load balancer changes")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS

        return self.msg

    def _action_suspend(self):
        """ Suspend a Load Balancer. """
        try:
            self.driver.suspend()
        except NotImplementedError:
            LOG.error(
                "Selected driver does not support SUSPEND action."
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            LOG.error("SUSPEND failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_enable(self):
        """ Enable a suspended Load Balancer. """
        try:
            self.driver.enable()
        except NotImplementedError:
            LOG.error(
                "Selected driver does not support ENABLE action."
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            LOG.error("ENABLE failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_delete(self):
        """ Delete a Load Balancer. """
        try:
            self.driver.delete()
        except NotImplementedError:
            LOG.error(
                "Selected driver does not support DELETE action."
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            LOG.error("DELETE failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_archive(self):
        """ Archive LB log files. """

        valid_methods = ['swift']
        method = None
        params = {}

        if self.OBJ_STORE_TYPE_FIELD not in self.msg:
            return BadRequest(
                "Missing '%s' element" % self.OBJ_STORE_TYPE_FIELD
            ).to_json()
        else:
            method = self.msg[self.OBJ_STORE_TYPE_FIELD].lower()

        # Validate method type
        if method not in valid_methods:
            return BadRequest(
                "'%s' is not a valid store type" % method
            ).to_json()

        # Get parameters for Swift storage
        if method == 'swift':
            if self.OBJ_STORE_BASEPATH_FIELD not in self.msg:
                return BadRequest(
                    "Missing '%s' element" % self.OBJ_STORE_BASEPATH_FIELD
                ).to_json()
            if self.OBJ_STORE_ENDPOINT_FIELD not in self.msg:
                return BadRequest(
                    "Missing '%s' element" % self.OBJ_STORE_ENDPOINT_FIELD
                ).to_json()
            if self.OBJ_STORE_TOKEN_FIELD not in self.msg:
                return BadRequest(
                    "Missing '%s' element" % self.OBJ_STORE_TOKEN_FIELD
                ).to_json()
            if self.LBLIST_FIELD not in self.msg:
                return BadRequest(
                    "Missing '%s' element" % self.LBLIST_FIELD
                ).to_json()

            lb_list = self.msg[self.LBLIST_FIELD]
            params['proto'] = lb_list[0]['protocol']
            params['lbid'] = lb_list[0]['id']
            params['basepath'] = self.msg[self.OBJ_STORE_BASEPATH_FIELD]
            params['endpoint'] = self.msg[self.OBJ_STORE_ENDPOINT_FIELD]
            params['token'] = self.msg[self.OBJ_STORE_TOKEN_FIELD]

        try:
            self.driver.archive(method, params)
        except NotImplementedError:
            error = "Selected driver does not support ARCHIVE action."
            LOG.error(error)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
        except Exception as e:
            LOG.error("ARCHIVE failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = str(e)
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_stats(self):
        """
        Get load balancer and node status.

        We push responsibility for knowing what state a load balancer
        current is in to the driver. Trying to get status for a LB that
        has been deleted is an error.
        """

        try:
            nodes = self.driver.get_status()
        except NotImplementedError:
            error = "Selected driver does not support STATS action."
            LOG.error(error)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
        except DeletedStateError:
            error = "Invalid operation STATS on a deleted LB."
            LOG.error(error)
            self.msg['status'] = 'DELETED'
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
        except Exception as e:
            LOG.error("STATS failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = str(e)
        else:
            self.msg['nodes'] = []
            for node, status in nodes:
                self.msg['nodes'].append({'id': node, 'status': status})
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS

        return self.msg

    def _action_metrics(self):
        """
        Get load balancer metrics

        This type of request gets the number of bytes out for each load
        balancer defined on the device. If both a TCP and HTTP load
        balancer exist, we report on each in a single response.
        """

        try:
            start, end, statistics = self.driver.get_statistics()
        except NotImplementedError:
            error = "Selected driver does not support METRICS action."
            LOG.error(error)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
            return self.msg
        except DeletedStateError:
            error = "Invalid operation METRICS on a deleted LB."
            LOG.error(error)
            self.msg['status'] = 'DELETED'
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
            return self.msg
        except Exception as e:
            LOG.error("METRICS failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = str(e)
            return self.msg

        self.msg['utc_start'] = start
        self.msg['utc_end'] = end
        self.msg['loadBalancers'] = []

        # We should have a list of tuples pairing the number of bytes
        # out with the protocol/LB.
        for proto, bytes_out in statistics:
            self.msg['loadBalancers'].append({'protocol': proto,
                                              'bytes_out': bytes_out})

        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg
