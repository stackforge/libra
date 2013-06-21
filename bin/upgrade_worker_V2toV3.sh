#!/bin/bash
##############################################################################
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################


##############################################################################
# DESCRIPTION
#   This script is used to manually upgrade a worker node running a 2.0
#   version of Libra to the 3.0 version. This is specifically targeted to
#   Ubuntu nodes, but may work on other distributions, though that is
#   untested. It makes some assumptions about the current setup.
#
#   This script is designed to be safe to run multiple times, in case an
#   error is encountered and it must be run again.
#
# EXIT VALUES
#   0 on success, 1 on error
##############################################################################

if [ $USER != "root" ]
then
  echo "Must be run as root user."
  exit 1
fi

LOG="/tmp/update_node.log"

if [ -e ${LOG} ]
then
  rm -f ${LOG}
fi

#################################################
# Update sudo privs by inserting '/usr/bin/chown'
#################################################
file="/etc/sudoers"
echo "Updating SUDO file $file" | tee -a ${LOG}

sed -i.bak -e '/^%haproxy/ c\
%haproxy ALL = NOPASSWD: /usr/sbin/service, /bin/cp, /bin/mv, /bin/rm, /bin/chown' ${file}
if [ $? -ne 0 ]
then
  echo "Edit of ${file} failed." | tee -a ${LOG}
  exit 1
fi

if [ -e ${file}.bak ]
then
  rm ${file}.bak
fi

#########################
# Chown on haproxy socket
#########################
haproxysock="/var/run/haproxy-stats.socket"
echo "Doing chown of haproxy socket ${haproxysock}" | tee -a ${LOG}

if [ -e ${haproxysock} ]
then
  chown haproxy:haproxy ${haproxysock}
  if  [ $? -ne 0 ]
  then
    echo "chown on ${haproxysock} failed." | tee -a ${LOG}
    exit 1
  fi
fi


##########################
# Edit current haproxy.cfg
##########################
haproxycfg="/etc/haproxy/haproxy.cfg"
echo "Updating HAProxy config file ${haproxycfg}" | tee -a ${LOG}

if [ -e ${haproxycfg} ]
then
  sed -i.bak -e '/stats socket/ c\
    stats socket /var/run/haproxy-stats.socket user haproxy group haproxy mode operator' ${haproxycfg}
  if  [ $? -ne 0 ]
  then
    echo "Editing ${haproxycfg} failed." | tee -a ${LOG}
    exit 1
  fi
fi

if [ -e ${haproxycfg}.bak ]
then
  rm -f ${haproxycfg}.bak
fi


#################
# Restart haproxy
#################
echo "Restarting haproxy" | tee -a ${LOG}
service haproxy restart 2>&1 >> ${LOG}
if [ $? -ne 0 ]; then echo "haproxy restart failed" | tee -a ${LOG}; exit 1; fi


exit 0
