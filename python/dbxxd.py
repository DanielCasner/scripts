#!/usr/bin/python
import os, pyinotify, subprocess

wm = pyinotify.WatchManager()
mask = pyinotify.EventsCodes.IN_DELETE | pyinotify.EventsCodes.IN_CREATE | pyinotify.EventsCodes.IN_MODIFY

class PTmp(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Create: %s " % os.path.join(event.path, event.name)
    def process_IN_DELETE(self, event):
        print "Delete: %s " % os.path.join(event.path, event.name)
    def process_IN_MODIFY(self, event):
        print "Modify: ", event


notifier = pyinotify.Notifier(wm, PTmp())

wdd = wm.add_watch('/home/casnerd/tmp', mask, rec=True)

while True:
    try:
        notifier.process_events()
        if notifier.check_events(timeout=None):
            notifier.read_events()
    except KeyboardInterrupt:
        notifier.stop()
        break

