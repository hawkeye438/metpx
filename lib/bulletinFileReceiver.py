#! /usr/bin/env python2
# -*- coding: UTF-8 -*-
"""
#############################################################################################
# Name: bulletinFileReceiver
# Author: Daniel Lemay (99% of the code is from LPT)
# Date: December 2004
#
# Description: Reads bulletins from disk, compose a valid name, write them to disk and
#              erase the originals. We had to do this this way if we want to use the
#              existing API.
#############################################################################################

 2005/02 PSilva
        thwacked into a lib to convert to 'options' method for
"""
import sys, os, os.path, signal, time
sys.path.insert(1,sys.path[0] + '/../lib')
sys.path.insert(1,sys.path[0] + '/../lib/importedLibs')

import bulletinManager
from DiskReader import DiskReader
from Source import Source
import PXPaths

PXPaths.normalPaths()

def run(source, igniter, logger, badLogger):
    bullManager = bulletinManager.bulletinManager(
         PXPaths.RXQ + source.name,
         badLogger,
         PXPaths.RXQ + source.name,
         '/apps/pds/RAW/-PRIORITY',
         9999,
         '\n',
         source.extension,
         PXPaths.ETC + 'header2client.conf',
         source.mapEnteteDelai,
         source.use_pds,
         source)

    while True:
        # If a SIGHUP signal is received ...
        if igniter.reloadMode == True: 
            source = Source(source.name, logger)
            bullManager = bulletinManager.bulletinManager(
                               PXPaths.RXQ +source.name,
                               badLogger,
                               PXPaths.RXQ + source.name,
                               '/apps/pds/RAW/-PRIORITY',
                               9999,
                               '\n',
                               source.extension,
                               PXPaths.ETC + 'header2client.conf',
                               source.mapEnteteDelai,
                               source.use_pds,
                               source)

            logger.info("%s has been reload" % igniter.direction)
            igniter.reloadMode = False

        # We put the bulletins (read from disk) in a dict (key = absolute filename)
        #bulletinsBrutsDict = bullManager.readBulletinFromDisk([bullManager.pathSource])
        # If a file has been modified in less than mtime (3 seconds now), we don't touch it
        reader = DiskReader(bullManager.pathSource, batch=1000, validation=False, mtime=3, prioTree=False, logger=logger)
        reader.sort()
        data = reader.getFilesContent(reader.batch)

        if len(data) == 0:
            time.sleep(1)
            continue

        # Write (and name correctly) the bulletins to disk, erase them after
        for index in range(len(data)):
            nb_bytes = len(data[index])
            logger.info("Lecture de %s: %d bytes" % (reader.sortedFiles[index], nb_bytes))
            bullManager.writeBulletinToDisk(data[index], True, True)
            try:
                os.unlink(reader.sortedFiles[index])
                logger.debug("%s has been erased", os.path.basename(reader.sortedFiles[index]))
            except OSError, e:
                (type, value, tb) = sys.exc_info()
                logger.error("Unable to unlink %s ! Type: %s, Value: %s" % (reader.sortedFiles[index], type, value))
