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

from hurry.filesize import size, alternative
from decimal import Decimal, ROUND_UP

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
DEFAULT_WARNING = 80.00
DEFAULT_CRITICAL = 90.00

# OPT parsing
# -----------
parser = optparse.OptionParser(
    "%prog [options]", version="%prog " + version)

# add default parser
parser = RedisCheckHelpers.add_default_parser_options(parser)

parser.add_option('-w', '--warning',
                  dest="warning", type="float",
                  help='Warning value for used memory. In [%]. Default : {d} [%]'.format(d=DEFAULT_WARNING)
)
parser.add_option('-c', '--critical',
                  dest="critical", type="float",
                  help='Critical value ued memory. In [%]. Default : {d} [%]'.format(d=DEFAULT_CRITICAL)
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

        #connect to redis
        redis = redis.StrictRedis(
            port=port,
            password=password,
            host=hostname,
            db=database
        )

        #get data
        #--------

        #get redis_info
        redis_info = RedisCheckHelpers.get_info(
            redis_con=redis,
            debug=debug
        )

        #get current redis max memory config
        redis_maxmemory = RedisCheckHelpers.get_maxmemory(
            redis_con=redis,
            debug=debug
        )

        redis_memory_used = long(redis_info['used_memory'])

        if debug:
            print("memory used")
            print("-----------")
            print(
                "used_memory: {m}".format(
                    m=size(
                        redis_memory_used,
                        alternative
                    )
                )
            )

        #process data
        current_redis_memory_usage = (float(redis_memory_used))/(float(redis_maxmemory))
        current_redis_memory_usage = Decimal(current_redis_memory_usage).quantize(
            Decimal('1.01'),
            rounding=ROUND_UP
        )

        if debug:
            print("current memory usage")
            print("--------------------")
            print("memory usage : {u}%".format(u=current_redis_memory_usage))

        #Format perf data string
        con_perf_data_string = OutputFormatHelpers.perf_data_string(
            label="redis_memory_usage",
            value=current_redis_memory_usage,
            warn=s_warning,
            crit=s_critical,
            UOM='%'
        )

        #check logic
        status = "OK"

        if current_redis_memory_usage >= s_warning:
            status = "Warning"
        if current_redis_memory_usage >= s_critical:
            status = "Critical"

        #output formating
        memory_usage_message = '{used}% of {max}'.format(
            used=current_redis_memory_usage,
            max=size(redis_maxmemory, alternative)
        )

        output = OutputFormatHelpers.check_output_string(
            status,
            memory_usage_message,
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
