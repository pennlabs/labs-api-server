#!/usr/bin/env python

# Add the following line into the labs crontab.
# */15 * * * * /home/labs/penn-mobile-server/cron/save_laundry_data.py

import os
import sys

import server


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # noqa


server.laundry.save_data()
