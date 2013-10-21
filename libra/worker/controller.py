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
from libra import __version__ as libra_version
from libra import __release__ as libra_release
from libra.common.exc import DeletedStateError
from libra.common.faults import BadRequest
from libra.worker.drivers.base import LoadBalancerDriver


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

    def __init__(self, logger, driver, json_msg, gearman):
        self.logger = logger
        self.driver = driver
        self.msg = json_msg
        self.gearman = gearman

    def run(self):
        """
        Process the JSON message and return a JSON response.
        """

        if self.ACTION_FIELD not in self.msg:
            self.logger.error("Missing `%s` value" % self.ACTION_FIELD)
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
            elif action == 'STATS':
                return self._action_stats()
            elif action == 'DIAGNOSTICS':
                return self._action_diagnostic()
            else:
                self.logger.error("Invalid `%s` value: %s" %
                                  (self.ACTION_FIELD, action))
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
        except Exception as e:
            self.logger.error("Controller exception: %s, %s" %
                              (e.__class__, e))
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
        for host_port in self.gearman:
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
            self.logger.error(
                "TCP connect error to gearman server {0}"
                .format(ip)
            )
            raise

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
            self.logger.error("Selected driver failed initialization.")
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
                    self.logger.error(
                        "Selected driver does not support setting protocol."
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
                except Exception as e:
                    self.logger.error(
                        "Failure trying to set protocol: %s, %s" %
                        (e.__class__, e)
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg

            if 'algorithm' in current_lb:
                algo = current_lb['algorithm'].upper()
                if algo == 'ROUND_ROBIN':
                    algo = LoadBalancerDriver.ROUNDROBIN
                elif algo == 'LEAST_CONNECTIONS':
                    algo = LoadBalancerDriver.LEASTCONN
                else:
                    self.logger.error("Invalid algorithm: %s" % algo)
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
            else:
                algo = LoadBalancerDriver.ROUNDROBIN

            try:
                self.driver.set_algorithm(current_lb['protocol'], algo)
            except NotImplementedError:
                self.logger.error(
                    "Selected driver does not support setting algorithm."
                )
                self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                return self.msg
            except Exception as e:
                self.logger.error(
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
                    self.logger.error(
                        "Selected driver does not support adding healthchecks."
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg
                except Exception as e:
                    self.logger.error(
                        "Selected driver failed adding healthchecks: %s, %s" %
                        (e.__class__, e)
                    )
                    self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                    return self.msg

            for lb_node in current_lb['nodes']:
                port, address, node_id, weight = None, None, None, None

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

                try:
                    self.driver.add_server(current_lb['protocol'],
                                           node_id,
                                           address,
                                           port,
                                           weight)
                except NotImplementedError:
                    self.logger.error(
                        "Selected driver does not support adding a server."
                    )
                    lb_node['condition'] = self.NODE_ERR
                except Exception as e:
                    self.logger.error("Failure trying adding server: %s, %s" %
                                      (e.__class__, e))
                    lb_node['condition'] = self.NODE_ERR
                else:
                    self.logger.debug("Added server: %s:%s" % (address, port))
                    lb_node['condition'] = self.NODE_OK

        try:
            self.driver.create()
        except NotImplementedError:
            self.logger.error(
                "Selected driver does not support CREATE action."
            )
            for current_lb in lb_list:
                for lb_node in current_lb['nodes']:
                    lb_node['condition'] = self.NODE_ERR
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            self.logger.error("CREATE failed: %s, %s" % (e.__class__, e))
            for lb_node in current_lb['nodes']:
                lb_node['condition'] = self.NODE_ERR
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            self.logger.info("Activated load balancer changes")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS

        return self.msg

    def _action_suspend(self):
        """ Suspend a Load Balancer. """
        try:
            self.driver.suspend()
        except NotImplementedError:
            self.logger.error(
                "Selected driver does not support SUSPEND action."
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            self.logger.error("SUSPEND failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_enable(self):
        """ Enable a suspended Load Balancer. """
        try:
            self.driver.enable()
        except NotImplementedError:
            self.logger.error(
                "Selected driver does not support ENABLE action."
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            self.logger.error("ENABLE failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_delete(self):
        """ Delete a Load Balancer. """
        try:
            self.driver.delete()
        except NotImplementedError:
            self.logger.error(
                "Selected driver does not support DELETE action."
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            self.logger.error("DELETE failed: %s, %s" % (e.__class__, e))
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
            self.logger.error(error)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
        except Exception as e:
            self.logger.error("ARCHIVE failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = str(e)
        else:
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        return self.msg

    def _action_stats(self):
        """
        Get load balancer statistics.

        We push responsibility for knowing what state a load balancer
        current is in to the driver. Trying to get statistics for a LB that
        has been deleted is an error.
        """

        try:
            # TODO: Do something with the returned statistics
            stats = self.driver.get_stats()
        except NotImplementedError:
            error = "Selected driver does not support STATS action."
            self.logger.error(error)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = error
        except DeletedStateError:
            self.logger.info("Invalid operation STATS on a deleted LB")
            self.msg['status'] = 'DELETED'
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
        except Exception as e:
            self.logger.error("STATS failed: %s, %s" % (e.__class__, e))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            self.msg[self.ERROR_FIELD] = str(e)
        else:
            node_status = stats.node_status_map()
            self.msg['nodes'] = []
            for node in node_status.keys():
                self.msg['nodes'].append({'id': node,
                                          'status': node_status[node]})
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS

        return self.msg
