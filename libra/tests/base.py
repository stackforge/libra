# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
# Copied verbatim

"""Base classes for our unit tests.

Allows overriding of config for use of fakes, and some black magic for
inline callbacks.

"""

import eventlet
eventlet.monkey_patch(os=False)

import copy
import os
import shutil
import tempfile
import sys

import fixtures
import testtools

from oslo.config import cfg

#from libra.db import migration

from libra.openstack.common import log as logging
from libra.openstack.common import test
from libra.openstack.common.fixture import config
from libra.openstack.common.fixture import moxstubout


test_opts = [
    cfg.StrOpt('sqlite_clean_db',
               default='clean.sqlite',
               help='File name of clean sqlite db'),
    cfg.BoolOpt('fake_tests',
                default=True,
                help='should we use everything for testing'), ]

CONF = cfg.CONF

CONF.set_override('use_stderr', False)

logging.setup('libra')

_DB_CACHE = None


class Database(fixtures.Fixture):
    def __init__(self, db_session, db_migrate, sql_connection,
                 sqlite_db, sqlite_clean_db):
        self.sql_connection = sql_connection
        self.sqlite_db = sqlite_db
        self.sqlite_clean_db = sqlite_clean_db

        self.engine = db_session.get_engine()
        self.engine.dispose()
        conn = self.engine.connect()
        if sql_connection == "sqlite://":
            if db_migrate.db_version() > db_migrate.INIT_VERSION:
                return
        else:
            testdb = os.path.join(CONF.state_path, sqlite_db)
            if os.path.exists(testdb):
                return
        db_migrate.db_sync()
#        self.post_migrations()
        if sql_connection == "sqlite://":
            conn = self.engine.connect()
            self._DB = "".join(line for line in conn.connection.iterdump())
            self.engine.dispose()
        else:
            cleandb = os.path.join(CONF.state_path, sqlite_clean_db)
            shutil.copyfile(testdb, cleandb)

    def setUp(self):
        super(Database, self).setUp()

        if self.sql_connection == "sqlite://":
            conn = self.engine.connect()
            conn.connection.executescript(self._DB)
            self.addCleanup(self.engine.dispose)
        else:
            shutil.copyfile(
                os.path.join(CONF.state_path, self.sqlite_clean_db),
                os.path.join(CONF.state_path, self.sqlite_db))


class TestCase(test.BaseTestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.CONF = self.useFixture(config.Config())

    def path_get(self, project_file=None):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '..',
                                            '..',
                                            )
                               )
        if project_file:
            return os.path.join(root, project_file)
        else:
            return root
