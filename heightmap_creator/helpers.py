# -*- coding: utf-8 -*-

import sys
import time


class ProgressOutputter(object):

    def __init__(self, total):
        self.done = 0
        self.total = total
        print "Querying {0} points.".format(total)
        self.on_progress(0)
        self.start = time.time()

    def on_progress(self, count):
        self.done += count
        sys.stdout.write("{0:.2f}%...\r".format((float(self.done)/self.total)*100))
        sys.stdout.flush()

    def on_done(self):
        start, self.start = self.start, None
        print "Done in {:.2f} sec.".format(time.time() - start)
