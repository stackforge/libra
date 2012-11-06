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

from libra.common.faults import BadRequest
from libra.worker.drivers.base import LoadBalancerDriver


class LBaaSController(object):

    NODE_OK = "ENABLED"
    NODE_ERR = "DISABLED"
    RESPONSE_FAILURE = "FAIL"
    RESPONSE_SUCCESS = "PASS"
    ACTION_FIELD = 'hpcs_action'
    RESPONSE_FIELD = 'hpcs_response'
    LBLIST_FIELD = 'loadbalancers'

    def __init__(self, logger, driver, json_msg):
        self.logger = logger
        self.driver = driver
        self.logger.debug("Entered LBaaSController")
        # Standardize case on JSON elements
        self.msg = dict((k.lower(), v) for k, v in json_msg.iteritems())

    def run(self):
        """
        Process the JSON message and return a JSON response.
        """

        if self.ACTION_FIELD not in self.msg:
            self.logger.error("Missing `%s` value" % self.ACTION_FIELD)
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        action = self.msg[self.ACTION_FIELD].upper()
        self.logger.info("Requested action: %s" % action)
        if action == 'CREATE':
            return self._action_create()
        elif action == 'UPDATE':
            return self._action_update()
        elif action == 'SUSPEND':
            return self._action_suspend()
        elif action == 'ENABLE':
            return self._action_enable()
        elif action == 'DELETE':
            return self._action_delete()
        else:
            self.logger.error("Invalid `%s` value: %s" %
                              (self.ACTION_FIELD, action))
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

    def _action_create(self):
        """
        Create a Load Balancer.

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

        lb_list = self.msg['loadbalancers']

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

            for lb_node in current_lb['nodes']:
                port, address = None, None

                if 'port' in lb_node:
                    port = lb_node['port']
                else:
                    return BadRequest("Missing 'port' element.").to_json()

                if 'address' in lb_node:
                    address = lb_node['address']
                else:
                    return BadRequest("Missing 'address' element.").to_json()

                try:
                    self.driver.add_server(current_lb['protocol'],
                                           address,
                                           port)
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

    def _action_update(self):
        """ Update a Load Balancer. """
        # NOTE(shrews): We would need to know the current configuration of
        # the load balancer to do an update. Note sure this is really feasible,
        # so for now we just do the same as CREATE.
        return self._action_create()

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
