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

import logging
import logging.handlers
import gzip
import os
import sys
import time
import glob
import codecs


class NewlineFormatter(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self._fmt % record.__dict__
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            try:
                s = s + record.exc_text
            except UnicodeError:
                s = s + record.exc_text.decode(sys.getfilesystemencoding(),
                                               'replace')
        s = s.replace('\n', ' ')
        return s


class CompressedTimedRotatingFileHandler(
        logging.handlers.TimedRotatingFileHandler
):
    def doRollover(self):
        self.stream.close()
        t = self.rolloverAt - self.interval
        timeTuple = time.localtime(t)
        tfn = '{0}.{1}'.format(
            self.baseFilename, time.strftime(self.suffix, timeTuple)
        )
        if os.path.exists(tfn):
            os.remove(tfn)
        os.rename(self.baseFilename, tfn)
        # Delete oldest log
        # TODO: clear multiple old logs
        if self.backupCount > 0:
            s = glob.glob('{0}.20*'.format(self.baseFilename))
            if len(s) > self.backupCount:
                s.sort()
                os.remove(s[0])
        if self.encoding:
            self.stream = codecs.open(self.baseFilename, 'w', self.encoding)
        else:
            self.stream = open(self.baseFilename, 'w')
        self.rolloverAt = self.rolloverAt + self.interval
        zfile = '{0}.gz'.format(tfn)
        if os.path.exists(zfile):
            os.remove(zfile)
        f_in = open(tfn, "rb")
        f_out = gzip.open(zfile, "wb")
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(tfn)
