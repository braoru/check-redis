#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2015:
#     Sébastien Pasche, sebastien.pasche@leshop.ch
#     Benoit Chalut, benoit.chalut@leshop.ch
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

author = "Sebastien Pasche"
maintainer = "Sebastien Pasche"
version = "0.0.1"

import optparse
import sys
import traceback
import os
import redis
from datetime import datetime
import base64
from math import ceil

# Ok try to load our directory to load the plugin utils.
my_dir = os.path.dirname(__file__)
sys.path.insert(0, my_dir)

try:
    from redis_checks import \
        RedisCheckHelpers, OutputFormatHelpers
except ImportError:
    print "ERROR : this plugin needs the local redis_checks lib. Please install it"
    sys.exit(2)

#DEFAULT LIMITS
#--------------
DEFAULT_WARNING = 50
DEFAULT_CRITICAL = 100

# OPT parsing
# -----------
parser = optparse.OptionParser(
    "%prog [options]", version="%prog " + version)

# add default parser
parser = RedisCheckHelpers.add_default_parser_options(parser)

parser.add_option('-w', '--warning',
                  dest="warning", type="int",
                  help='Warning value for connection. In [ms]. Default : {d} [ms]'.format(d=DEFAULT_WARNING)
)
parser.add_option('-c', '--critical',
                  dest="critical", type="int",
                  help='Critical value for connection. In [ms]. Default : {d} [ms]'.format(d=DEFAULT_CRITICAL)
)

if __name__ == '__main__':
    # Ok first job : parse args
    opts, args = parser.parse_args()
    if args:
        parser.error("Does not accept any argument.")

    # connection parameters
    port = opts.port
    hostname = opts.hostname
    password = opts.password
    database = opts.database
    debug = opts.debug

    # Try to get nermic warning/critical values
    s_warning = opts.warning or DEFAULT_WARNING
    s_critical = opts.critical or DEFAULT_CRITICAL

    try:

        #start timming
        start_time = datetime.now()

        #connect to redis
        redis = redis.StrictRedis(
            port=port,
            password=password,
            host=hostname,
            db=database
        )

        #create a test string
        test_string = "May I walk on the green side of the blue moon"
        test_string_b64 = base64.urlsafe_b64encode(test_string)

        if debug:
            print("Original string")
            print("---------------")
            print(test_string)
            print("Base64 string")
            print("-------------")
            print(test_string_b64)

        #get the echo
        test_string_echo_b64 = redis.echo(test_string_b64)
        test_string_echo = base64.urlsafe_b64decode(test_string_echo_b64)

        if debug:
            print("Echo Base64 string")
            print("------------------")
            print(test_string_echo_b64)
            print("Echo string")
            print("-----------")
            print(test_string_echo)

        #get request time
        stop_time = datetime.now()
        elapsed_time = (stop_time - start_time)
        elapsed_time_ms = int(
            ceil(
                elapsed_time.microseconds * 0.001
            )
        )

        #Format perf data string
        con_perf_data_string = OutputFormatHelpers.perf_data_string(
            label="connection_delay",
            value=elapsed_time_ms,
            warn=s_warning,
            crit=s_critical,
            UOM='ms'
        )

        #check logic
        if test_string == test_string_echo:
            status = "OK"
            message = "Redis connection successful"
            if elapsed_time_ms > s_warning:
                status = "Warning"
                message = "Redis connection with too slow"
            if elapsed_time_ms > s_critical:
                status = "Critical"
                message = "Redis connection too slow"
        else:
            status = "Critical"
            message = "Echo does not match"

        output = OutputFormatHelpers.check_output_string(
            status,
            message,
            [con_perf_data_string]
        )

        print(output)

    except Exception as e:
        if debug:
            print(e)
            the_type, value, tb = sys.exc_info()
            traceback.print_tb(tb)
        print("Error: {m}".format(m=e))
        sys.exit(2)

    finally:
        if status == "Critical":
            sys.exit(2)
        if status == "Warning":
            sys.exit(1)
        sys.exit(0)
