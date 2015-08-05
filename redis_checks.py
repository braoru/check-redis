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

import redis
from hurry.filesize import size, alternative
from pprint import pprint

class RedisCheckHelpers(object):
    @classmethod
    def add_default_parser_options(
            cls,
            parser
    ):
        parser.add_option('-H', '--hostname',type="str", default="localhost",
                          dest="hostname",
                          help='Hostname to connect to. Default : locahost')
        parser.add_option('-p', '--port',
                          dest="port", type="int", default=6379,
                          help='Redis port to connect to. Default : 6379')
        parser.add_option('-P', '--password',
                          dest="password", type="str", default=None,
                          help='Redis password used for connection. Default : None')
        parser.add_option('--db',
                          dest="database", type="int", default=0,
                          help='Redis database to connect to. Default : 0')
        parser.add_option('--debug',
                          dest="debug", default=False, action="store_true",
                          help='Enable debug')

        return parser

    @classmethod
    def get_info(
            cls,
            redis_con=None,
            debug=False
    ):
        if not isinstance(redis_con, redis.StrictRedis):
            raise Exception("Cannot get informations if not connected to redis")

        info = redis_con.info('all')

        if debug:
            print("info")
            print("----")
            pprint(info)

        return info

    @classmethod
    def get_maxmemory(
            cls,
            redis_con=None,
            debug=False
    ):
        if not isinstance(redis_con, redis.StrictRedis):
            raise Exception("Cannot get maxmemory if not connected to redis")

        maxmemory = long(redis_con.config_get('maxmemory')['maxmemory'])

        if debug:
            print("Current maxmemory")
            print("-----------------")
            print(
                "maxmemory: {m}".format(
                    m=size(
                        maxmemory,
                        alternative
                    )
                )
            )

        if maxmemory == 0:
            raise Exception("maxmemory = 0 cannot evaluate usage")

        return maxmemory

class OutputFormatHelpers(object):
    @classmethod
    def perf_data_string(
            cls,
            label,
            value,
            warn='',
            crit='',
            UOM='',
            min='',
            max=''

    ):
        """
        Generate perf data string from perf data input
        http://docs.icinga.org/latest/en/perfdata.html#formatperfdata
        :param label: Name of the measured data
        :type label: str
        :param value: Value of the current measured data
        :param warn: Warning level
        :param crit: Critical level
        :param UOM: Unit of the value
        :param min: Minimal value
        :param max: maximal value
        :return: formated perf_data string
        """
        if UOM:
            perf_data_template = "'{label}'={value}[{UOM}];{warn};{crit};{min};{max};"
        else:
            perf_data_template = "'{label}'={value};{warn};{crit};{min};{max};"

        return perf_data_template.format(
            label=label,
            value=value,
            warn=warn,
            crit=crit,
            UOM=UOM,
            min=min,
            max=max
        )

    @classmethod
    def check_output_string(
            cls,
            state,
            message,
            perfdata=None
    ):
        """
        Generate check output string with perf data
        :param state: State of the check in  ['Critical', 'Warning', 'OK', 'Unknown']
        :type state: str
        :param message: Output message
        :type message: str
        :param perfdata: Array of perf data string
        :type perfdata: Array
        :return: check output formated string
        """
        if state not in ['Critical', 'Warning', 'OK', 'Unknown']:
            raise Exception("bad check output state")

        if not message:
            message = '-'

        if perfdata is not None:
            if not hasattr(perfdata, '__iter__'):
                raise Exception("Submited perf data list is not iterable")

            perfdata_string = ''.join(' {s} '.format(s=data) for data in perfdata)
            output_template = "{s}: {m} |{d}"
        else:
            output_template = "{s}: {m} "
            perfdata_string = ''

        return output_template.format(
            s=state,
            m=message,
            d=perfdata_string
        )
