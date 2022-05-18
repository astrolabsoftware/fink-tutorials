#!/usr/bin/env python
# Copyright 2022 AstroLab Software
# Author: Julien Peloton
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Poll Early SN Ia from the last day using the Fink REST API
"""
import requests
import pandas as pd
import numpy as np

from astropy.time import Time, TimeDelta

import io
import os

APIURL = "https://fink-portal.org"

def classsearch(classname='Early SN Ia candidate', n=1000, startdate=None, stopdate=None, output_format='json', cols=None):
    """ Perform a class search in the Science Portal using the Fink REST API

    Parameters
    ----------
    classname: str
        Fink class name
    n: int
        Maximum number of candidates. Default is 1000.
    startdate: str
        Start date in UTC. Optional.
    stopdate: str
        Start date in UTC. Optional.
    cols: None or str
        If None, all columns for each alert are transfered. Otherwise,
        specify a comma separated string of column names,
        e.g. "i:objectId,i:jd,i:magpsf".
    """
    payload = {
        'class': classname,
        'n': n,
        'output-format': output_format
    }

    if startdate is not None:
        payload.update(
            {
                'startdate': startdate,
                'stopdate': stopdate
            }
        )

    if cols is not None:
        payload.update({'columns': cols})

    r = requests.post(
        '{}/api/v1/latests'.format(APIURL),
        json=payload
    )

    pdf = pd.read_json(io.BytesIO(r.content))

    return pdf

def main():
    classname = 'Early SN Ia candidate'

    # N day(s) in the past from now
    n_last_days = 3

    # Time boundaries
    startdate = Time.now().iso
    stopdate = (Time.now() - TimeDelta(3600 * 24 * n_last_days, format='sec')).iso

    pdf = classsearch(
        classname=classname,
        startdate=startdate,
        stopdate=stopdate,
        cols='i:objectId'
    )

    if not pdf.empty:
        # post to slack
        slacktxt = ' \n '.join(['https://fink-portal.org/{}'.format(i) for i in pdf['i:objectId']])
        slacktxt = '{} - {} \n '.format(stopdate, startdate) + slacktxt
        r = requests.post(
            os.environ['FINKWEBHOOK'],
            json={'text': slacktxt, "username": "Fink {}".format(classname)},
            headers={'Content-Type': 'application/json'}
        )
        print(r.status_code)
    else:
        slacktxt = '{} - {} \n No new sources'.format(stopdate, startdate)
        r = requests.post(
            os.environ['FINKWEBHOOK'],
            json={'text': slacktxt, "username": "Fink {}".format(classname)},
            headers={'Content-Type': 'application/json'}
        )


if __name__ == "__main__":
    main()
