# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

# pecan imports
import ConfigParser
import socket
from pecan import expose, response, request, conf
from pecan.rest import RestController
from libra.common.api.lbaas import Device, db_session
from libra.common.api.lbaas import Vip, Limits
from libra.openstack.common import log
from libra.admin_api.acl import tenant_is_admin, tenant_is_user

from sqlalchemy import create_engine
from sqlalchemt.orm import sessionmaker
from oslo.config import cfg

LOG = log.getLogger(__name__)


class LimitsController(RestController):
    """ a sub-controller for StatusController """
    @expose('json')
    def get(self):
        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        ret = {}
        with db_session() as session:
            limits = session.query(Limits.name, Limits.value).all()
            if limits is None:
                response.status = 500
                return dict(
                    faultcode="Server",
                    faultstring="Error obtaining limits"
                )
            for limit in limits:
                ret[limit.name] = limit.value
            session.commit()
        return ret

    @expose('json')
    def put(self):
        # PUT data stored in "request" variable
        if not tenant_is_admin(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        if type(request) is not dict:
            response.status = 400
            return dict(
                faultcode="Client",
                faultstring="Invalid JSON received"
            )


class StatusController(RestController):
    def pool(self):
        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        NULL = None  # For pep8
        with db_session() as session:
            dev_use = session.query(Device).\
                filter(Device.status == 'ONLINE').count()
            dev_free = session.query(Device).\
                filter(Device.status == 'OFFLINE').count()
            dev_error = session.query(Device).\
                filter(Device.status == 'ERROR').count()
            dev_pending = session.query(Device).\
                filter(Device.status == 'DELETED').count()
            vips_use = session.query(Vip).\
                filter(Device.status > 0)
            vips_free = session.query(Vip).\
                filter(Device.status == NULL)
            status = {
                "devices": {
                    "used": dev_use,
                    "available": dev_free,
                    "error": dev_error,
                    "pendingDelete": dev_pending
                },
                "vips": {
                    "used": vips_use,
                    "available": vips_free
                }
            }
            session.commit()
        return status

    @expose('json')
    def service(self):
        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )

        ret = {
            'mysql': [],
            'gearman': []
        }
        config = ConfigParser.SafeConfigParser()
        config.read(cfg.CONF['config_file'])

        # Connect to all MySQL servers and test
        for section in conf.database:
            db_conf = config._sections[section]
            conn_string = '''mysql+mysqlconnector://%s:%s@%s:%s/%s''' % (
                db_conf['username'],
                db_conf['password'],
                db_conf['host'],
                db_conf['port'],
                db_conf['schema']
            )

            if 'ssl_key' in db_conf:
                ssl_args = {'ssl': {
                    'cert': db_conf['ssl_cert'],
                    'key': db_conf['ssl_key'],
                    'ca': db_conf['ssl_ca']
                }}

                engine = create_engine(
                    conn_string, isolation_level="READ COMMITTED",
                    pool_size=20, connect_args=ssl_args, pool_recycle=3600
                )
            else:
                engine = create_engine(
                    conn_string, isolation_level="READ COMMITTED",
                    pool_size=20, pool_recycle=3600
                )
            session = sessionmaker(bind=engine)
            try:
                session.execute("SELECT 1")
                session.close()
                ret['mysql'].append({db_conf['host']: 'ONLINE'})
            except:
                ret['mysql'].append({db_conf['host']: 'OFFLINE'})

        # Socket connect to all gearman servers, TODO: a better gearman test
        for server in conf.gearman.server:
            ghost, gport = server.split(':')
            try:
                sock = socket.socket()
                sock.settimeout(5)
                sock.connect(ghost, int(gport))
                sock.close()
                ret['gearman'].append({ghost: 'ONLINE'})
            except socket.error:
                ret['gearman'].append({ghost: 'OFFLINE'})
                try:
                    sock.close()
                except:
                    pass

        return ret

    @expose('json')
    def counters(self):
        if not tenant_is_user(request.headers):
            response.status = 401
            return dict(
                faultcode="Client",
                faultstring="Client not authorized to access this function"
            )
        with db_session() as session:
            counters = session.query(Counters.name, Counters.value).all()
            return counters

    limits = LimitsController()
