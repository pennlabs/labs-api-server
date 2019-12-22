#!/usr/bin/env python

# Add the following line into the labs crontab.
# 20,50 * * * * /home/labs/penn-mobile-server/cron/send_gsr_push_notifications.py

import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if True:
    import server


server.studyspaces.notifications.send_reminders()
