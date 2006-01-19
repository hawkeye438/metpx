"""
#############################################################################################
# Name: CollectionManager.py
#
# Author:   Kaveh Afshar (National Software Development<nssib@ec.gc.ca>)
#           Travis Tiegs (National Software Development<nssib@ec.gc.ca>)
#
# Date: 2005-12-02
#
# Description:  This module gives us the ability to file reports and send out immediate
#               collections if necessary. Scheduled collections are not handled by this 
#               module.
#
# Revision History: 
#               2005-12-13 Daniel Lemay provided class stub
#############################################################################################
"""
__version__ = '1.0'

import sys, os, os.path, string, commands, re, signal, fnmatch
sys.path.insert(1,sys.path[0] + '/../lib/importedLibs')

import datetime 
import PXPaths
from Logger import Logger
import CollectionBuilder
import CollectionConfigParser
import time
import BulletinCollection
import BulletinWriter

PXPaths.normalPaths()              # Access to PX paths

class CollectionManager(object):
    """The CollectionManager class

           Files incoming reports, and sends out immediate collections
           if necessary.

           Author:      National Software Development<nssib@ec.gc.ca>
           Date:        December 2005
    """
    

    def __init__(self, source, logger=None):
        self.source = source   # Source object containing configuration infos about the collector
        self.logger = logger   # Logger object

        #-----------------------------------------------------------------------------------------
        # Creating CollectionBuilder object to give us access to CollectionBuilder methods
        #-----------------------------------------------------------------------------------------
        self.collectionBuilder = CollectionBuilder.CollectionBuilder(self.logger) 

        #-----------------------------------------------------------------------------------------
        # Creating CollectionConfig object to give us access and control over collection 
        # config parameters
        #-----------------------------------------------------------------------------------------
        self.collectionConfig = CollectionConfigParser.CollectionConfigParser(self.logger,self.source)

        #-----------------------------------------------------------------------------------------
        # A placeholder for the bulletin object that will be set for this class to use
        #-----------------------------------------------------------------------------------------
        self.bulletin = ''

        #-----------------------------------------------------------------------------------------
        # A BulletinWriter object to carry out disk-related tasks
        #-----------------------------------------------------------------------------------------
        self.bulletinWriter = BulletinWriter.BulletinWriter(self.logger,self.collectionConfig)


    def collectReport(self, fileName):
        """ collectReports (self, fileName)

            Read the content of filename and determine if the bulletin needs to be 
            sent immediately, or if it can be sent at the end of the collection
            interval. This method contains all of the business logic neede to 
            determine if a bulletin needs to be collected.  For more information
            about the business logic and the flow of this method, please see the 
            "Collection Process Flow diagram" document.

            Return values:
                newCollectionBulleti: BulletinCollection -  A collection object containing a
                                                            collection which needs to be 
                                                            transmitted immediately or nothing
                                                            if the collection does not need to
                                                            be transmitted immediately.
        """
        #-----------------------------------------------------------------------------------------
        # use collectionBuilder to create a bulletin object from the given file
        #-----------------------------------------------------------------------------------------
        self.bulletin = self.collectionBuilder.buildBulletinFromFile(fileName)
        print "\nREMOVEME: The incoming report: ",self.bulletin.bulletin
        
        #-----------------------------------------------------------------------------------------
        # Let's find out if the report arrived on time.  If so, write the report bulletin
        # to disk.  No mutex is needed because the on-time collection will only be processed
        # only after the on-time interval is over
        #-----------------------------------------------------------------------------------------
        if (self.isReportOnTime()):
            self.bulletinWriter.writeOnTimeBulletinToDisk(self.bulletin)
        else:
            #-----------------------------------------------------------------------------------------
            # In this section we'll attempt to determine the value of the Collection's B1 anb B2 
            # variables. 
            #-----------------------------------------------------------------------------------------
            if (self.doesReportHaveBbbField()):
                self.bulletin.setCollectionB1(self.bulletin.getReportB1())
                self.bulletin.setCollectionB2(self.bulletin.getReportB2())
            else:
                self.bulletin.setCollectionB1('R')
                self.bulletin.setCollectionB2('R')

            #-----------------------------------------------------------------------------------------
            # In this section we'll attempt to determine the value of the Collection's B3 variable
            # No mutex necessary because this immediate collection will always be sent with RRZ
            #-----------------------------------------------------------------------------------------
            if (self.isReportOlderThan24H()):
                self.bulletin.setCollectionB3('Z')

            else:
                #-----------------------------------------------------------------------------------------
                # Determining if B1B2W_sent exists. If yes, set B3 to "Xn".  If not, then 
                # increment B3 from A to W until we find an unused B3 character
                # The B3 value which we are about to determine will eventually determine the BBB of our
                # the outgoing collection, therefore we must have mutex to make sure that we don't 
                # duplicate a B3 value.  Race conditions could occur when:
                # - Two collecting rcvrs receive two immediate collections at the same time for the same
                #   origin and full header.  They should be sent CCA and CCB, but may both go out as CCA
                # - A rcvr goes to place an old RRx into a collection directory which is being read
                #   by a scheduled collection.
                #-----------------------------------------------------------------------------------------

                #-----------------------------------------------------------------------------------------
                # Locking semaphore
                #-----------------------------------------------------------------------------------------
                dirToLock = \
                    self.bulletinWriter.calculateBulletinDir(self.bulletin.getTwoLetterType(), \
                                                             self.bulletin.getTimeStampWithMinsSetToZero(), \
                                                             self.bulletin.getOrigin(), \
                                                             self.bulletin.getFullType())
                print"REMOVEME: Locking sem to check for B3. Locking:",dirToLock
                key = self.bulletinWriter.lockDirBranch(dirToLock)
                      
                if (self.bulletinWriter.doesSentCollectionWithB3Exist(self.bulletin, 'W')):
                    tempB3 = self._findNextXValue()
                    self.bulletin.setCollectionB3(tempB3)
                else:
                    tempB3 = self._findNextAvailableB3Value()
                    self.bulletin.setCollectionB3(tempB3)
                #-----------------------------------------------------------------------------------------
                # Unlocking semaphore
                #-----------------------------------------------------------------------------------------
                self.bulletinWriter.unlockDirBranch(key)
                
            #-----------------------------------------------------------------------------------------
            # Now that we've determined the BBB value for our collection, we need to write it to the 
            # collection directory (regardless of whether it's immediate or scheduled).
            #-----------------------------------------------------------------------------------------
            #-----------------------------------------------------------------------------------------
            # Locking semaphore
            #-----------------------------------------------------------------------------------------
            dirToLock = \
                self.bulletinWriter.calculateBulletinDir(self.bulletin.getTwoLetterType(), \
                                                         self.bulletin.getTimeStampWithMinsSetToZero(), \
                                                         self.bulletin.getOrigin(), \
                                                         self.bulletin.getFullType())
            print"REMOVEME: Locking sem to write the bulletin. Locking:",dirToLock
            key = self.bulletinWriter.lockDirBranch(dirToLock)

            self.bulletinWriter.writeReportBulletinToDisk(self.bulletin)

            #-----------------------------------------------------------------------------------------
            # Unlocking semaphore
            #-----------------------------------------------------------------------------------------
            self.bulletinWriter.unlockDirBranch(key)
            print "REMOVEME: The collection's BBB is now set to: ", self.bulletin.getCollectionBBB()
            #-----------------------------------------------------------------------------------------
            # At this point all collection worthy report bulletins have been written to disk.
            # Now we need to know which are immediate and which are scheduled.  Reports with BBB 
            # beginning with CC or AA are immediate.  Reports beginning with RR which are older 
            # than 1HR are also immediate. The difference between immediate and scheduled
            # is that immediate collections are returned to the caller by this method.
            #-----------------------------------------------------------------------------------------
            if (self.isAnImmediateCollection()):
                #-----------------------------------------------------------------------------------------
                # If we're dealing with immediate bulletins, change the minutes field to '00'.
                # I.e. 'SACN94 CWAO 080319' becomes 'SACN94 CWAO 080300'
                #-----------------------------------------------------------------------------------------
                self.bulletin.setBulletinMinutesField('00')

                #-----------------------------------------------------------------------------------------
                # Build a collection bulletin from a single report bulletin and return to caller
                # for immediate transmission
                #-----------------------------------------------------------------------------------------
                newCollectionBulletin = self.bulletin.buildImmediateCollectionFromReport()
                print "REMOVEME: Returning collection for xmission: ",newCollectionBulletin.bulletinAsString()
                return newCollectionBulletin

        
    def isReportOnTime(self):
        """ isReportOnTime() -> Boolean

            Given the bulletin, returns True if the bulletin is considered on time
            and an empty string if the bulletin is not considered on time.

            The incoming bulletin is considered on time if it is from less than
            futureDatedReportWindow mintues in the future and for hourly bulletins only,
            it is less than headerValidTime minutes late.

            Return Values:
                True: string    -Returned if bulletin is considered on time.
                False: string   -Returned if bulletin is not considered on time.
        """
        True = 'True'
        False = ''
        #-----------------------------------------------------------------------------------------
        # Only reports created for the top of the hour may be considered on time.
        #-----------------------------------------------------------------------------------------
        reportPeriodMins = self.bulletin.getBulletinMinutesField()
        if (reportPeriodMins == '00'):
            
            #-----------------------------------------------------------------------------------------
            # Find out how many minutes past the hour is considered on-time for this bulletin type
            #-----------------------------------------------------------------------------------------
            maxPastDateInMins = self.collectionConfig. \
            getReportValidTimeByHeader(self.bulletin.getTwoLetterType())

            #-----------------------------------------------------------------------------------------
            # Find out how far in the future an acceptable report may be
            #-----------------------------------------------------------------------------------------
            maxFutureDateInMins = self.collectionConfig. \
            getFutureDatedReportWindowByHeader(self.bulletin.getTwoLetterType())

            #-----------------------------------------------------------------------------------------
            # In order for this bulletin to be on time, it must fall in between the maximum past
            # date and the maximum future date
            #-----------------------------------------------------------------------------------------
            futureCheck = self.isBulletinWithinFutureWindow(maxFutureDateInMins)
            pastCheck = self.isBulletinWithinPastWindow(maxPastDateInMins)

            #-----------------------------------------------------------------------------------------
            # If bulletin falls in between both limits, then it is on time
            #-----------------------------------------------------------------------------------------
            if (futureCheck) and (pastCheck):
                return True
            else:
                return False
        else:
            return False

        
    def isBulletinWithinFutureWindow(self, maxFutureDateInMins):
        """ isBulletinWithinFutureWindow(maxFutureDateInMins) -> Boolean

            This method makes sure that the incoming bulletin does not exceed the 
            maximum future date.  It will return a boolean value of True or False
            based on the outcome
        """
        True = 'True'
        False = ''
        #-----------------------------------------------------------------------------------------
        # Produce time objects needed for comparisons.
        # The bulletin has no month or year, so assume present year and month
        #-----------------------------------------------------------------------------------------
        presentDateTime = datetime.datetime.now()
        maxFutureDateTime = presentDateTime + datetime.timedelta(minutes = long(maxFutureDateInMins))
        bulletinDateTime = datetime.datetime(presentDateTime.year, presentDateTime.month, \
                           int(self.bulletin.getBulletinDaysField()), \
                           int(self.bulletin.getBulletinHoursField()), \
                           int(self.bulletin.getBulletinMinutesField())) 

        #-----------------------------------------------------------------------------------------
        # If our maxFutureDateTime spans into a new year, then it is possible
        # that the bulletin may have the new year as its year
        #-----------------------------------------------------------------------------------------
        if (maxFutureDateTime.year > presentDateTime.year):
            bulletinDateTime = bulletinDateTime.replace(year = maxFutureDateTime.year)

        #-----------------------------------------------------------------------------------------
        # If our maxFutureDateTime spans into a new month, then it is possible
        # that the bulletin may have the new month as its month
        #-----------------------------------------------------------------------------------------
        if (maxFutureDateTime.month != presentDateTime.month):
            bulletinDateTime = bulletinDateTime.replace(month = maxFutureDateTime.month)

        #-----------------------------------------------------------------------------------------
        # If the bulletin is still more futuristic than the maxFutureDateTime, then it's from 
        # too far into the future to be considered on time.
        #-----------------------------------------------------------------------------------------
        if (bulletinDateTime > maxFutureDateTime):
            return False
        else:
            return True


    def isBulletinWithinPastWindow(self, maxPastDateInMins):
        """ isBulletinWithinPastWindow(maxPastDateInMins) -> Boolean

            This method accepts a variable in minutes and returns False 
            if the incoming bulletin is older than maxPastDateInMins.  
            It will return True if the bulletin is newer than the 
            maxPastDateInMins.
        """
        True = 'True'
        False = ''
        #-----------------------------------------------------------------------------------------
        # Produce time objects needed for comparisons.
        # The bulletin has no month or year, so assume present year and month
        #-----------------------------------------------------------------------------------------
        presentDateTime = datetime.datetime.now()
        maxPastDateTime = presentDateTime - datetime.timedelta(minutes = long(maxPastDateInMins))
        bulletinDateTime = datetime.datetime(presentDateTime.year, presentDateTime.month, \
                           int(self.bulletin.getBulletinDaysField()), \
                           int(self.bulletin.getBulletinHoursField()), \
                           int(self.bulletin.getBulletinMinutesField())) 

        #-----------------------------------------------------------------------------------------
        # If our maxPastDateTime spans into a previous year, then it is possible
        # that the bulletin may have the previous year as its year
        #-----------------------------------------------------------------------------------------
        if (maxPastDateTime.year < presentDateTime.year):
            bulletinDateTime = bulletinDateTime.replace(year = maxPastDateTime.year)

        #-----------------------------------------------------------------------------------------
        # If our maxPastDateTime spans into a previous month, then it is possible
        # that the bulletin may have the previous month as its month
        #-----------------------------------------------------------------------------------------
        if (maxPastDateTime.month != presentDateTime.month):
            bulletinDateTime = bulletinDateTime.replace(month = maxPastDateTime.month)

        #-----------------------------------------------------------------------------------------
        # If the bulletin is still older than the maxPastDateTime, then it's too old and 
        # cannot be considered on time.
        #-----------------------------------------------------------------------------------------
        if (bulletinDateTime < maxPastDateTime):
            return False
        else:
            return True


    def doesReportHaveBbbField(self):
        """ doesReportHaveBbbField() -> Boolean

            This method makes returns True if the incoming bulletin has a BBB field 
            specified.  It will return False if a BBB field is not specified
        """
        True = 'True'
        False = ''
        #-----------------------------------------------------------------------------------------
        # get the BBB field of the bulletin
        #-----------------------------------------------------------------------------------------
        bulletinBBB = self.bulletin.getReportBBB()

        #-----------------------------------------------------------------------------------------
        # The report has a BBB field if the returning string was not empty
        #-----------------------------------------------------------------------------------------
        if (bulletinBBB):
            return True
        else:
            return False


    def isReportOlderThan24H(self):
        """ isReportOlderThan24H -> Boolean

            This method returns True if the incoming bulletin is older than
            24 hours and False if it is not.
        """
        True = 'True'
        False = ''
        #-----------------------------------------------------------------------------------------
        # 24 hours equals 1440 minutes.  
        # A returned value of true from isBulletinWithinPastWindow means that the 
        # bulletin is not older than 24 hours
        #-----------------------------------------------------------------------------------------
        if (self.isBulletinWithinPastWindow(1440)):
            return False
        else:
            return True

    def isReportOlderThan1H(self):
        """ isReportOlderThan1H -> Boolean

            This method returns True if the incoming bulletin is older than
            1 hour and False if it is not.
        """
        True = 'True'
        False = ''
        #-----------------------------------------------------------------------------------------
        # 1 hour equals 60 minutes.  
        # A returned value of true from isBulletinWithinPastWindow means that the 
        # bulletin is not older than 24 hours
        #-----------------------------------------------------------------------------------------
        if (self.isBulletinWithinPastWindow(60)):
            return False
        else:
            return True


    def _findNextXValue (self):
        """ _findNextXValue() -> string

            This method returns the character 'X', or 'Xn' where n is a
            positive integer in the case where the directory B1B2X exists
        """
        #-----------------------------------------------------------------------------------------
        # In the simple case, the directory B1B2X_sent will not exists and we'll 
        # just return X.  Otherwise we need to return X1 or X2, or X3 ..
        #-----------------------------------------------------------------------------------------
        if not (self.bulletinWriter.doesSentCollectionWithB3Exist(self.bulletin, 'X')):
            return 'X'
        else:
            counter = 1
            while (self.bulletinWriter.doesSentCollectionWithB3Exist(self.bulletin, 'X'+str(counter))):
                counter = counter + 1
            else:
                return 'X'+str(counter)


    def _findNextAvailableB3Value(self):
        """ _findNextAvailableB3Value() -> Character

            This method looks for the next available alphabet character
            ranging from A to W to use as the collection's B3 value
        """
        charSet = 'ABCDEFGHIJKLMNOPQRSTUVW'
        #-----------------------------------------------------------------------------------------
        # Look for '_sent' in dir name
        #-----------------------------------------------------------------------------------------
        for char in charSet:
            if not (self.bulletinWriter.doesSentCollectionWithB3Exist(self.bulletin, char)):
                return char

                
    def markCollectionAsSent(self, collectionBulletin):
        """ markCollectionAsSent(fileName) 

            This is a wrapper for BulletinWriter.markCollectionAsSent().
            It's purpose is to indicate that a collection bulletin
            has been sent (queued for transmission).
        """
        #-----------------------------------------------------------------------------------------
        # call method to mark the appropriate collection as sent
        #-----------------------------------------------------------------------------------------
        self.bulletinWriter.markCollectionAsSent(collectionBulletin)


    def isAnImmediateCollection(self):
        """ isAnImmediateCollection()  

            This method returns True or False based on whether or not the
            current bulletin warrants immediate transmission. Reports beginning 
            with BBB = CC or AA are immediate.  Reports beginning with RR which are 
            older than 1HR are also immediate. 
        """
        True = 'True'
        False = ''
        if ((self.bulletin.getCollectionB1() in ('A', 'C')) or
            (self.bulletin.getCollectionB1() in ('R') and (self.isReportOlderThan1H()))):
            return True
        else:
            return False
        



if __name__ == '__main__':
    pass
