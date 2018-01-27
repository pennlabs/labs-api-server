#!/usr/bin/env python

# Add the following line into the labs crontab.
# */15 * * * * /home/labs/penn-mobile-server/cron/save_laundry_data.py

import server

server.laundry.save_data()
