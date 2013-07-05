# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from sqlalchemy import Table, Column, Integer, ForeignKey, create_engine
from sqlalchemy import INTEGER, VARCHAR, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, Session
import sqlalchemy.types as types
import random
import ConfigParser
from pecan import conf


config = ConfigParser.SafeConfigParser()
config.read([conf.conffile])
engines = []
for section in conf.database:
    db_conf = config._sections[section]

    conn_string = '''mysql://%s:%s@%s:%d/%s''' % (
        db_conf['username'],
        db_conf['password'],
        db_conf['host'],
        db_conf.get('port', 3306),
        db_conf['schema']
    )

    if 'ssl_key' in db_conf:
        ssl_args = {'ssl': {
            'cert': db_conf['ssl_cert'],
            'key': db_conf['ssl_key'],
            'ca': db_conf['ssl_ca']
        }}

        engine = create_engine(
            conn_string, isolation_level="READ COMMITTED", pool_size=20,
            connect_args=ssl_args, pool_recycle=3600
        )
    else:
        engine = create_engine(
            conn_string, isolation_level="READ COMMITTED", pool_size=20,
            pool_recycle=3600
        )
    engines.append(engine)

DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata

loadbalancers_devices = Table(
    'loadbalancers_devices',
    metadata,
    Column('loadbalancer', Integer, ForeignKey('loadbalancers.id')),
    Column('device', Integer, ForeignKey('devices.id'))
)


class FormatedDateTime(types.TypeDecorator):
    '''formats date to match iso 8601 standards
    '''

    impl = types.DateTime

    def process_result_value(self, value, dialect):
        return value.strftime('%Y-%m-%dT%H:%M:%S')


class Limits(DeclarativeBase):
    __tablename__ = 'global_limits'
    id = Column(u'id', Integer, primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=128), nullable=False)
    value = Column(u'value', BIGINT(), nullable=False)


class Device(DeclarativeBase):
    """device model"""
    __tablename__ = 'devices'
    #column definitions
    az = Column(u'az', INTEGER(), nullable=False)
    created = Column(u'created', FormatedDateTime(), nullable=False)
    floatingIpAddr = Column(
        u'floatingIpAddr', VARCHAR(length=128), nullable=False
    )
    id = Column(u'id', BIGINT(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=128), nullable=False)
    publicIpAddr = Column(u'publicIpAddr', VARCHAR(length=128), nullable=False)
    status = Column(u'status', VARCHAR(length=128), nullable=False)
    type = Column(u'type', VARCHAR(length=128), nullable=False)
    updated = Column(u'updated', FormatedDateTime(), nullable=False)


class LoadBalancer(DeclarativeBase):
    """load balancer model"""
    __tablename__ = 'loadbalancers'
    #column definitions
    algorithm = Column(u'algorithm', VARCHAR(length=80), nullable=False)
    errmsg = Column(u'errmsg', VARCHAR(length=128))
    id = Column(u'id', BIGINT(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=128), nullable=False)
    port = Column(u'port', INTEGER(), nullable=False)
    protocol = Column(u'protocol', VARCHAR(length=128), nullable=False)
    status = Column(u'status', VARCHAR(length=50), nullable=False)
    tenantid = Column(u'tenantid', VARCHAR(length=128), nullable=False)
    updated = Column(u'updated', FormatedDateTime(), nullable=False)
    created = Column(u'created', FormatedDateTime(), nullable=False)

    nodes = relationship(
        'Node', backref=backref('loadbalancers', order_by='Node.id')
    )
    devices = relationship(
        'Device', secondary=loadbalancers_devices, backref='loadbalancers',
        lazy='joined'
    )


class Node(DeclarativeBase):
    """node model"""
    __tablename__ = 'nodes'
    #column definitions
    address = Column(u'address', VARCHAR(length=128), nullable=False)
    enabled = Column(u'enabled', Integer(), nullable=False)
    id = Column(u'id', BIGINT(), primary_key=True, nullable=False)
    lbid = Column(
        u'lbid', BIGINT(), ForeignKey('loadbalancers.id'), nullable=False
    )
    port = Column(u'port', INTEGER(), nullable=False)
    status = Column(u'status', VARCHAR(length=128), nullable=False)
    weight = Column(u'weight', INTEGER(), nullable=False)


class RoutingSession(Session):
    """ If an engine is already in use, re-use it.  Otherwise we can end up
        with deadlocks in Galera, see http://tinyurl.com/9h6qlly """
    last_engine = None

    def get_bind(self, mapper=None, clause=None):
        if (
            RoutingSession.last_engine
            and RoutingSession.last_engine.pool.checkedout() > 0
        ):
            return RoutingSession.last_engine
        engine = random.choice(engines)
        RoutingSession.last_engine = engine
        return engine


class db_session(object):
    def __init__(self):
        self.session = None

    def __enter__(self):
        self.session = sessionmaker(class_=RoutingSession)()
        return self.session

    def __exit__(self, type, value, traceback):
        self.session.close()
        return False
