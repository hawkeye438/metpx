# -*- coding: iso-8859-1 -*-
"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.
"""

"""
#############################################################################################
# Name: senderAm.py
#
# Author: Pierre Michaud
#
# Date: Janvier 2005
#
# Contributors: Daniel Lemay   reformat the code in object oriented way
#               Michel Grenier added segmentation of bulletin if needed
#
# Description:
#
#############################################################################################
"""
import sys, os.path, time
import gateway
import socketManagerAm
import bulletinAm

from MultiKeysStringSorter import MultiKeysStringSorter
from DiskReader import DiskReader
from CacheManager import CacheManager
import PXPaths

from TextSplitter import TextSplitter

PXPaths.normalPaths()

class senderAm(gateway.gateway):

    def __init__(self,path, client,logger):
        gateway.gateway.__init__(self,path, client,logger)
        self.client = client
        self.establishConnection()

        self.reader = DiskReader(PXPaths.TXQ + self.client.name,
                                 self.client.batch,           # Number of files we read each time
                                 self.client.validation,      # name validation (Bool)
                                 self.client.patternMatching, # pattern matching (Bool)
                                 self.client.mtime,           # check modification time (integer)
                                 True,                        # priority tree
                                 self.logger,
                                 eval(self.client.sorter),
                                 self.client)

        # Mechanism to eliminate multiple copies of a bulletin

        self.cacheManager = CacheManager(maxEntries=120000, timeout=8*3600)

        # AM's maximum bulletin size is 32K
        self.set_maxLength( self.client.maxLength )

    def set_maxLength(self,value):
        if value <= 0  : value = 32 * 1024
        self.maxLength = value

    def shutdown(self):
        gateway.gateway.shutdown(self)

        resteDuBuffer, nbBullEnv = self.unSocketManagerAm.closeProperly()

        self.write(resteDuBuffer)

        self.logger.info("Le senderAm est mort.  Traitement en cours reussi.")

    def establishConnection(self):
        # Instanciation du socketManagerAm
        self.logger.debug("Instanciation du socketManagerAm")

        self.unSocketManagerAm = \
                 socketManagerAm.socketManagerAm(
                         self.logger,type='master', \
                         port=self.client.port,\
                         remoteHost=self.client.host,
                         timeout=self.client.timeout)

    def read(self):
        if self.igniter.reloadMode == True:
            # We assign the defaults and reread the configuration file (in __init__)
            self.client.__init__(self.client.name, self.client.logger)
            self.set_maxLength( self.client.maxLength )
            self.resetReader()
            self.cacheManager.clear()
            self.logger.info("Cache has been cleared")
            self.logger.info("Sender AM has been reloaded")
            self.igniter.reloadMode = False
        self.reader.read()
        return self.reader.getFilesContent(self.client.batch)

    # MG modified from its original design to keep readable and
    #    to add segmentation... 

    def write(self,data):

        #self.logger.debug("%d nouveaux bulletins seront envoyes",len(data))
        self.logger.info("%d new bulletins will be sent", len(data))

        for index in range(len(data)):

            # try sending it
            try:

                tosplit = self.need_split( data[index] )

                # need to be segmented...
                if tosplit :
                   succes, nbBytesSent = self.write_segmented_data( data[index], self.reader.sortedFiles[index] )
                   # all parts were cached... nothing to do
                   if succes and nbBytesSent == 0 :
                      self.unlink_file( self.reader.sortedFiles[index] )
                      continue

                # send the entire bulletin
                else :

                   # if in cache than it was already sent... nothing to do
                   if self.client.nodups and self.in_cache( data[index], True, self.reader.sortedFiles[index] ) :
                      # PEter... in_cache already deletes the file, no need for second call.
                      #self.unlink_file( self.reader.sortedFiles[index] )
                      continue
                   succes, nbBytesSent = self.write_data( data[index] )

                #si le bulletin a ete envoye correctement, le fichier est efface
                if succes:
                   basename = os.path.basename(self.reader.sortedFiles[index])
                   self.logger.info("(%i Bytes) Bulletin %s  delivered" % (nbBytesSent, basename))
                   self.unlink_file( self.reader.sortedFiles[index] )
                else:
                   self.logger.info("%s: Sending problem" % self.reader.sortedFiles[index])

            except Exception, e:
            # e==104 or e==110 or e==32 or e==107 => connexion rompue
                (type, value, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s" % (type, value))

        # Log infos about tx speed
        if (self.totBytes > 1000000):
            self.logger.info(self.printSpeed() + " Bytes/sec")
            # Log infos about caching
            (stats, cached, total) = self.cacheManager.getStats()
            if total:
               percentage = "%2.2f %% of the last %i requests were cached (implied %i files were deleted)" % (cached/total * 100,  total, cached)
            else:
               percentage = "No entries in the cache"
            self.logger.info("Caching stats: %s => %s" % (str(stats), percentage))

    # check if data in cache... if not it is added automatically
    def in_cache(self,data,unlink_it,path) :
        already_in = False

        # If data is already in cache, we don't send it
        if self.cacheManager.find(data, 'md5') is not None:
           already_in = True
           if unlink_it :
              try:
                   os.unlink(path)
                   self.logger.info("suppressed duplicate send %s", os.path.basename(path))
              except OSError, e:
                   (type, value, tb) = sys.exc_info()
                   self.logger.info("In_cache unable to unlink %s ! Type: %s, Value: %s"
                                   % (path, type, value))

        return already_in

    # MG define if the data needs to be segmented
    def need_split(self,data) :

        # check if the bulletin needs to be segmented
        # AM bulletin has the following form : 128 bytes for a struct 
        # followed by the bulletin.

        unBulletinAm = bulletinAm.bulletinAm(data,self.logger,lineSeparator='\r\r\n')
        limit   = self.maxLength - 128
        header  = unBulletinAm.getHeader()
        lheader = len(header) + 1

        tosplit = False
        if  len(data) > limit :
            tosplit = True

        return tosplit

    # MG write data (isolated to clear code when segmentation was added)
    def write_data(self,data):
        unBulletinAm = bulletinAm.bulletinAm(data,self.logger,lineSeparator='\r\r\n')

        # C'est dans l'appel a sendBulletin que l'on verifie si la connexion doit etre reinitialisee ou non
        succes, nbBytesSent = self.unSocketManagerAm.sendBulletin(unBulletinAm)

        #si le bulletin a ete envoye correctement, le fichier est efface
        if succes:
           self.tallyBytes(nbBytesSent)

        return (succes, nbBytesSent)

    # MG unlink file (isolated to clear code when segmentation was added)
    def unlink_file(self,path):
        try:
               os.unlink(path)
               self.logger.debug("%s has been erased", os.path.basename(path))
        except OSError, e:
               (type, value, tb) = sys.exc_info()
               self.logger.error("unlink_file failed %s ! Type: %s, Value: %s" % (path, type, value))

    # MG  segmenting and writing data if possible
    def write_segmented_data(self,data,path):

        unBulletinAm = bulletinAm.bulletinAm(data,self.logger,lineSeparator='\r\r\n')
        limit   = self.maxLength - 128
        header  = unBulletinAm.getHeader()
        lheader = len(header) + 1

        # SHOULD SEGMENT BUT : At the moment BUFR are not segmented but discarded
        if data[lheader:lheader+4] == "BUFR" :
           self.logger.error("Unable to segment and send %s ! Reason : type %s, Size: %s" % (path, "BUFR", len(data) ))
           self.unlink_file(path)
           return ( False, 0 )

        # SHOULD SEGMENT BUT : At the moment GRIB are not segmented but discarded
        if data[lheader:lheader+4] == "GRIB" :
           self.logger.error("Unable to segment and send %s ! Reason : type %s, Size: %s" % (path, "GRIB", len(data) ))
           self.unlink_file(path)
           return ( False, 0 )

        # SHOULD SEGMENT BUT : the bulletin already have a BBB group -> not segmented but discarded
        # FIXME should validate that the 4th token is realy a BBB (AAa-z CCa-z RRa-z Pa-za-z AMD COR RTM)
        tokn = header.split()
        if len(tokn) == 4 :
           self.logger.error("Unable to send %s Segmented ! Reason : BBB = %s, Size: %s" % (path, tokn[3], len(data) ))
           self.unlink_file(path)
           return ( False, 0 )

        # Perform segmentation
        # segmentation the block size is computed like this :
        # maxLength - 128 (Am struct size) - (len(header) + '\n\ + ' ' + BBB  )

        limit   = self.maxLength - 128 - (lheader + 4)
        blocks  = TextSplitter(data[lheader:], limit ).breakMarker()
        self.logger.info("Bulletin %s segmented in %d parts" % (path,len(blocks)))
                    
        i       =  0
        totSent =  0

        alpha=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

        for part in blocks :
            rawSegment  = header + " P" + alpha[i/24] + alpha[i%24] + '\n' + part
            i = i + 1

            if self.client.nodups and self.in_cache( rawSegment, False, None ) :
               continue

            succes, nbBytesSent = self.write_data(rawSegment)
            if succes :
               tallyBytes(nbBytesSent)
               self.logger.info("(%i Bytes) Bulletin Segment number %d sent" % (nbBytesSent,i))
            else :
               return (False, totSent)

        return (True, totSent)