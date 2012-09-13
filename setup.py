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

import setuptools
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest.main(self.test_args)


setuptools.setup(
    name="lbaas_worker",
    description="Python LBaaS Gearman Worker",
    version="1.0",
    author="David Shrewsbury",
    author_email="shrewsbury.dave@gmail.com",
    packages=setuptools.find_packages(exclude=["*.tests"]),
    entry_points={
        'console_scripts': [
            'lbaas_worker = lbaas_worker.worker:main'
        ]
    },
    cmdclass={'test': PyTest},
    tests_require=['pytest-pep8'],
    install_requires=['gearman', 'python-daemon'],
)
