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
DEFAULT_WARNING = 2000
DEFAULT_CRITICAL = 5000

# OPT parsing
# -----------
parser = optparse.OptionParser(
    "%prog [options]", version="%prog " + version)

# add default parser
parser = RedisCheckHelpers.add_default_parser_options(parser)

parser.add_option('-w', '--warning',
                  dest="warning", type="float",
                  help='Warning value for connected clients. Default : {d}'.format(d=DEFAULT_WARNING)
)
parser.add_option('-c', '--critical',
                  dest="critical", type="float",
                  help='Critical value for connected clients. Default : {d}'.format(d=DEFAULT_CRITICAL)
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

        redis_connected_clients = long(redis_info['connected_clients'])
        redis_maxclients = RedisCheckHelpers.get_mmaxclients(
            redis_con=redis,
            debug=debug
        )
        if debug:
            print("connected clients")
            print("-----------")
            print(
                "connected_clients: {m}".format(
                    m=size(
                        redis_connected_clients,
                        alternative
                    )
                )
            )
            print(
                "maxclients: {m}".format(
                    m=size(
                        maxclients,
                        alternative
                    )
                )
            )

        #Format perf data string
        con_perf_data_string = OutputFormatHelpers.perf_data_string(
            label="connected_clients",
            value=redis_connected_clients,
            warn=s_warning,
            crit=s_critical,
            min=0,
            max=redis_maxclients
        )

        #check logic
        status = "OK"

        if redis_connected_clients >= s_warning:
            status = "Warning"
        if redis_connected_clients >= s_critical:
            status = "Critical"

        #output formating
        memory_usage_message = '{n} connected clients'.format(
            n=redis_connected_clients
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
