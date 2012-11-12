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

import eventlet


def stats_manager(logger, driver, stats_poll):
    logger.debug("[stats] Statistics gathering process started.")
    logger.debug("[stats] Polling interval: %d" % stats_poll)

    while True:
        try:
            http_stats = driver.get_stats('http')
            tcp_stats = driver.get_stats('tcp')
        except NotImplementedError:
            logger.warn(
                "[stats] Driver does not implement statisics gathering."
            )
            break

        logger.debug("[stats] HTTP bytes in/out: (%d, %d)" %
                     (http_stats.bytes_in, http_stats.bytes_out))
        logger.debug("[stats] TCP bytes in/out: (%d, %d)" %
                     (tcp_stats.bytes_in, tcp_stats.bytes_out))
        eventlet.sleep(stats_poll)

    logger.info("[stats] Statistics gathering process terminated.")
