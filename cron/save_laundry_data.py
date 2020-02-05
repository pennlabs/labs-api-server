#!/usr/bin/env python
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if True:
    import server


server.laundry.save_data()
