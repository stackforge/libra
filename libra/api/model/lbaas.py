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
from sqlalchemy import INTEGER, VARCHAR, TIMESTAMP, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from pecan import conf

# TODO replace this with something better
conn_string = '''mysql://%s:%s@%s/%s''' % (
    conf.database.username,
    conf.database.password,
    conf.database.host,
    conf.database.schema
)

engine = create_engine(conn_string)
DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata
metadata.bind = engine


class LibraDeclarativeBase(object):
    """overriding DeclarativeBase so that we can add our own default functions
    """
    add_to_json = []
    #TODO make this actually work .. needs some thought
    def update_from_json(self, input_json):
        """updates a record from an inputed json file"""
        for feild in input_json.iterkeys():
            self.feild = input_json[feild]

    def output_to_json(self):
        """serializes an objects data into json so that it can be used as the gearman
        client payload."""
        output = {}
        for col in self.add_to_json:
            output[col] = self.col
        return json.loads(output)

class Device(DeclarativeBase):
    """device model"""
    __tablename__ = 'devices'
    #column definitions
    az = Column(u'az', INTEGER(), nullable=False)
    created = Column(u'created', TIMESTAMP(), nullable=False)
    floatingIpAddr = Column(u'floatingIpAddr', VARCHAR(length=128), nullable=False)
    id = Column(u'id', BIGINT(), primary_key=True, nullable=False)
    loadbalancers = Column(u'loadbalancers', VARCHAR(length=128), nullable=False)
    name = Column(u'name', VARCHAR(length=128), nullable=False)
    publicIpAddr = Column(u'publicIpAddr', VARCHAR(length=128), nullable=False)
    status = Column(u'status', VARCHAR(length=128), nullable=False)
    type = Column(u'type', VARCHAR(length=128), nullable=False)
    updated = Column(u'updated', TIMESTAMP(), nullable=False)

    def find_free_device(self):
        """queries for free and clear device

        sql form java api
            SELECT * FROM devices WHERE loadbalancers = " + EMPTY_LBIDS + " AND status = '" + Device.STATUS_OFFLINE + "'" ;
        """
        return session.query(Device)\
                .filter_by(loadbalancers="",status="OFFLINE")\
                .first()

class LoadBalancer(DeclarativeBase):
    """load balancer model"""
    __tablename__ = 'loadbalancers'
    #column definitions
    algorithm = Column(u'algorithm', VARCHAR(length=80), nullable=False)
    created = Column(u'created', TIMESTAMP(), nullable=False)
    device = Column(u'device', BIGINT(), ForeignKey('devices.id'), nullable=False)
    errmsg = Column(u'errmsg', VARCHAR(length=128))
    id = Column(u'id', BIGINT(), primary_key=True, nullable=False)
    name = Column(u'name', VARCHAR(length=128), nullable=False)
    port = Column(u'port', INTEGER(), nullable=False)
    protocol = Column(u'protocol', VARCHAR(length=128), nullable=False)
    status = Column(u'status', VARCHAR(length=50), nullable=False)
    tenantid = Column(u'tenantid', VARCHAR(length=128), nullable=False)
    updated = Column(u'updated', TIMESTAMP(), nullable=False)
    nodes = relationship('Node', backref=backref('loadbalancers', order_by='Node.id'))

    add_to_json = [
        'id',
        'name',
        'device',
        'algorithm',
        'port',
        'protocal',
        'status',
        'tenantid',
        'updated',
        'created',
        'nodes'
    ]


class Node(DeclarativeBase):
    """node model"""
    __tablename__ = 'nodes'
    #column definitions
    address = Column(u'address', VARCHAR(length=128), nullable=False)
    enabled = Column(u'enabled', Integer(), nullable=False)
    id = Column(u'id', BIGINT(), primary_key=True, nullable=False)
    lbid = Column(u'lbid', BIGINT(), ForeignKey('loadbalancers.id'), nullable=False)
    port = Column(u'port', INTEGER(), nullable=False)
    status = Column(u'status', VARCHAR(length=128), nullable=False)
    weight = Column(u'weight', INTEGER(), nullable=False)

#    loadbalancers = relationship('LoadBalancer', backref=backref('node', order_by=LoadBalancer.id))

"""session"""
session = sessionmaker(bind=engine)()
