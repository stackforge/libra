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
#   This script is used to manually upgrade a worker node running a 1.0
#   version of Libra to the 2.0 version. This is specifically targeted to
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

# Uncomment below if you run the libra_worker process as the 'haproxy' user.

#sed -i.bak -e '/^%haproxy/ c\
#%haproxy ALL = NOPASSWD: /usr/sbin/service, /bin/cp, /bin/mv, /bin/rm, /usr/bin/socat, /bin/chown' ${file}
#if [ $? -ne 0 ]
#then
#  echo "1st edit of ${file} failed." | tee -a ${LOG}
#  exit 1
#fi

sed -i.bak -e '/^%libra/ c\
%libra ALL = NOPASSWD: /usr/sbin/service, /bin/cp, /bin/mv, /bin/rm, /usr/bin/socat, /bin/chown' ${file}
if [ $? -ne 0 ]
then
  echo "2nd edit of ${file} failed." | tee -a ${LOG}
  exit 1
fi

if [ -e ${file}.bak ]
then
  rm ${file}.bak
fi


########################
# Make new log directory
########################
logdir="/mnt/log"
echo "Creating ${logdir}" | tee -a ${LOG}

if [ ! -e ${logdir} ]
then
  mkdir ${logdir}
  if [ $? -ne 0 ]
  then
    echo "Making log directory ${logdir} failed" | tee -a ${LOG}
    exit 1
  fi
fi


#######################################
# Create /etc/rsyslog.d/10-haproxy.conf
#######################################
haproxy_syslog="/etc/rsyslog.d/10-haproxy.conf"
echo "Creating ${haproxy_syslog}" | tee -a ${LOG}

cat > ${haproxy_syslog} <<'EOF'
$template Haproxy,"%TIMESTAMP% %msg%\n"
local0.* -/mnt/log/haproxy.log;Haproxy
# don't log anywhere else
local0.* ~
EOF

if [ $? -ne 0 ]
then
  echo "Creating ${haproxy_syslog} failed." | tee -a ${LOG}
  exit 1
fi


#################################
# Create /etc/logrotate.d/haproxy
#################################
haproxy_logrotate="/etc/logrotate.d/haproxy"
echo "Creating ${haproxy_logrotate}" | tee -a ${LOG}

cat > ${haproxy_logrotate} <<'EOF'
/mnt/log/haproxy.log {
       weekly
       missingok
       rotate 7
       compress
       delaycompress
       notifempty
       create 640 syslog adm
       sharedscripts
       postrotate
               /etc/init.d/haproxy reload > /dev/null
       endscript
}
EOF

if [ $? -ne 0 ]
then
  echo "Creating ${haproxy_logrotate} failed." | tee -a ${LOG}
  exit 1
fi


##########################
# Edit current haproxy.cfg
##########################
haproxycfg="/etc/haproxy/haproxy.cfg"
echo "Updating HAProxy config file ${haproxycfg}" | tee -a ${LOG}

if [ -e ${haproxycfg} ]
then
  sed -i.bak -e '/local1 notice/d' ${haproxycfg}
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


##############
# Update Libra
##############
pkglocation="/home/ubuntu"
pkgversion="libra-2.0"
echo "Updating Libra to ${pkgversion}" | tee -a ${LOG}

cd $pkglocation
if [ $? -ne 0 ]; then echo "cd to ${pkglocation} failed" | tee -a ${LOG}; exit 1; fi
tar zxf ${pkgversion}.tar.gz 2>&1 >> ${LOG}
if [ $? -ne 0 ]; then echo "tar failed" | tee -a ${LOG}; exit 1; fi
cd ${pkgversion}
if [ $? -ne 0 ]; then echo "cd to ${pkgversion} failed" | tee -a ${LOG}; exit 1; fi
python setup.py install --install-layout=deb 2>&1 >> ${LOG}
if [ $? -ne 0 ]; then echo "python install failed" | tee -a ${LOG}; exit 1; fi


##################
# Restart rsyslogd
##################
echo "Restarting rsyslogd" | tee -a ${LOG}
service rsyslog restart 2>&1 >> ${LOG}
if [ $? -ne 0 ]; then echo "rsyslog restart failed" | tee -a ${LOG}; exit 1; fi


#################
# Restart haproxy
#################
echo "Restarting haproxy" | tee -a ${LOG}
service haproxy restart 2>&1 >> ${LOG}
if [ $? -ne 0 ]; then echo "haproxy restart failed" | tee -a ${LOG}; exit 1; fi


######################
# Restart libra_worker
######################
echo "Stopping libra_worker" | tee -a ${LOG}
killall libra_worker 2>&1 >> ${LOG}
#if [ $? -ne 0 ]; then echo "killing libra_worker failed" | tee -a ${LOG}; exit 1; fi

echo "Starting libra_worker" | tee -a ${LOG}
/usr/bin/libra_worker -c /etc/libra.cfg 2>&1 >> ${LOG}
if [ $? -ne 0 ]; then echo "starting libra_worker failed" | tee -a ${LOG}; exit 1; fi

exit 0
