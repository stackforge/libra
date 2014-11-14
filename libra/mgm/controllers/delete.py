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

import random
from datetime import datetime
from oslo.config import cfg
from libra.mgm.nova import Node, NotFound
from libra.openstack.common import log
from libra.common.api.lbaas import db_session


LOG = log.getLogger(__name__)


class DeleteController(object):

    RESPONSE_FIELD = 'response'
    RESPONSE_SUCCESS = 'PASS'
    RESPONSE_FAILURE = 'FAIL'

    def __init__(self, msg):
        self.msg = msg

    def run(self):

        with db_session() as session:

            num_tries = 0
            period = cfg.CONF['mgm']['rate_limit_delete_device_period']
            max_count = cfg.CONF['mgm']['rate_limit_delete_device_max_count']
            sleep_time_base = look_back_time / (max_count * 10)
            have_lock = False
            period_delta = datetime.timedelta(seconds=period)

            while not have_lock:
                # Add a row for this delete action.
                action = RateLimitedAction(resource='DELETE_DEVICE',
                    use_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
                session.add(action)
                session.commit()
                action_pkid = action.id
                # Including that row, are there more actions per time period
                # than allowed?
                period_min = datetime.utcnow() - period_delta
                period_mintime = period_min.strftime(%Y-%m-%d %H:%M:%S')
                recent_count = session.query(RateLimitedAction).\
                    filter(RateLimitedAction.use_time >= period_mintime).count()
                if recent_count <= max_count:
                    # No, so let that row persist, and proceed.
                    have_lock = True
                else:
                    # Yes, so delete the row, sleep a random time, then retry.
                    # The time starts at 10% of the expected average estimate,
                    # then backs off from there.
                    session.delete(action)
                    session.commit()
                    num_tries = num_tries + 1
                    if num_tries >= 100:
                        LOG.exception('Cannot get rate_limit lock for DELETE_DEVICE, aborting')
                        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
                        return self.msg
                    actual_sleep_time = random.uniform( sleep_time_base * 0.5, sleep_time_base * 1.5 )
                    LOG.info('waiting to DELETE_DEVICE, sleeping {0:.3f}'.format(actual_sleep_time))
                    time.sleep( actual_sleep_time )
                    sleep_time_base = sleep_time_base * 1.1

        try:
            nova = Node()
        except Exception:
            LOG.exception("Error initialising Nova connection")
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg

        LOG.info(
            "Deleting a requested Nova instance {0}".format(self.msg['name'])
        )
        try:
            node_id = nova.get_node(self.msg['name'])
        except NotFound:
            LOG.error(
                "No node found for {0}".format(self.msg['name'])
            )
            self.msg[self.RESPONSE_FIELD] = self.RESPONSE_FAILURE
            return self.msg
        nova.delete(node_id)
        self.msg[self.RESPONSE_FIELD] = self.RESPONSE_SUCCESS
        LOG.info(
            'Deleted node {0}, id {1}'.format(self.msg['name'], node_id)
        )
        return self.msg
