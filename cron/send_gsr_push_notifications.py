#!/usr/bin/env python

# Add the following line into the labs crontab.
# 20,50 * * * * /home/labs/penn-mobile-server/cron/send_gsr_push_notifications.py

import server


server.studyspaces.notifications.send_reminders()
