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
""" Poll the Fink servers only once at a time """
import sys, os
import requests
from fink_client.consumer import AlertConsumer

def poll_single_alert(myconfig, topics) -> None:
    """ Connect to and poll fink servers once.
    """
    maxtimeout = 5

    # Instantiate a consumer
    consumer = AlertConsumer(topics, myconfig)

    try:
        # Poll the servers
        topic, alert, _ = consumer.poll(maxtimeout)

        # Analyse output
        if topic is not None:
            # post to slack
            slacktxt = 'https://fink-portal.org/{}'.format(alert['objectId'])
            slacktxt = '{} \n '.format(alert['timestamp']) + slacktxt
            print(os.environ['FINKWEBHOOK'], topic)
            r = requests.post(
                os.environ['FINKWEBHOOK'],
                json={'text': slacktxt, "username": "Fink {}".format(topic)},
                headers={'Content-Type': 'application/json'}
            )
            # print(slacktxt)
        else:
            print(
                'No alerts received in the last {} seconds'.format(
                    maxtimeout
                )
            )

        keep_going = True
    except KeyboardInterrupt:
        sys.stderr.write('%% Aborted by user\n')
        keep_going = False
    finally:
        # Close the connection to the servers
        consumer.close()

    return keep_going



if __name__ == "__main__":
    """ Poll the servers only once at a time """

    # to fill
    myconfig = {
        'username': '',
        'bootstrap.servers': '',
        'group_id': '',
    }

    topics = ['']

    keep_going = True
    while keep_going:
        keep_going = poll_single_alert(myconfig, topics)
