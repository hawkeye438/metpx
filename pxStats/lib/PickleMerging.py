#! /usr/bin/env python
"""
##############################################################################
##
##
## @name   : pickleMerging.py 
##
##
## @author : Nicholas Lemay
##
## @since : 06-07-2006 , last update on 2008-02-28
##
## @license: MetPX Copyright (C) 2004-2006  Environment Canada
##           MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
##           named COPYING in the root of the source directory tree.
##
##
## @summary :    Used to merge pickles created by StatsPickler. 
##
##               Very usefull for pickles treating the same client/source
##             
##               over different machines over the same hour.  
##
##               Also usefull for merging pickles form different hours.
##
##
##############################################################################
"""
import os,sys, time

sys.path.insert(1,  os.path.dirname( os.path.abspath(__file__) ) + '/../../')

from   pxStats.lib.StatsPickler         import StatsPickler
from   pxStats.lib.CpickleWrapper       import CpickleWrapper
from   pxStats.lib.FileStatsCollector   import _FileStatsEntry, FileStatsCollector
from   pxStats.lib.PickleVersionChecker import PickleVersionChecker
from   pxStats.lib.StatsDateLib         import StatsDateLib
from   pxStats.lib.LanguageTools        import LanguageTools


CURRENT_MODULE_ABS_PATH =  os.path.abspath(__file__).replace( ".pyc", ".py" )


class PickleMerging: 
    
    global _
    
    _ =  LanguageTools.getTranslatorForModule( CURRENT_MODULE_ABS_PATH ) 
     
    def entryListIsValid( entryList ):
        """
            @summary : Returns whether or not an entry
                       list of pickles contains 
                       a list of pickles that can be merged. 
            
            @return : True or False 
        
        """
         
        isValid = True    
         
        if entryList != [] :
            
            i = 0 
            startTime  = entryList[0].startTime
            totalWidth = entryList[0].totalWidth
            interval   = entryList[0].interval    
            statsTypes = entryList[0].statsTypes  
            
            while i < len(entryList) and isValid == True  :  
                
                if startTime != entryList[i].startTime or totalWidth != entryList[i].totalWidth or interval != entryList[i].interval :
                    isValid = False 
                
                else:
                    
                    for type in statsTypes:
                        if type not in entryList[i].statsTypes:
                            isValid = False 
                i = i + 1                      
    
        
        else:
            isValid = False         
        
        return isValid 
    
    
    entryListIsValid = staticmethod( entryListIsValid )
    
    
    
    def fillWithEmptyEntries( nbEmptyEntries, entries ):
        """
            
            @summary : Append certain number of empty entries to the entry list. 
            
            
        """            
        
        for i in xrange( nbEmptyEntries ): 
            entries[i] = _FileStatsEntry() 
               
       
        return entries
    
    fillWithEmptyEntries = staticmethod( fillWithEmptyEntries  )
    
    
    
    def mergePicklesFromDifferentHours( logger = None , startTime = "2006-07-31 13:00:00",\
                                        endTime = "2006-07-31 19:00:00", client = "satnet",\
                                        machine = "pdsPM", fileType = "tx" ):
        """
            @summary : This method merges entire hourly pickles files together. 
            
            @None    : This does not support merging part of the data of pickles.   
        
        """
        
        if logger != None :
            logger.debug( _("Call to mergeHourlyPickles received.") )
            logging = True
        else:
            logging = False
                
        pickles = []
        entries = {}
        width = StatsDateLib.getSecondsSinceEpoch( endTime ) - StatsDateLib.getSecondsSinceEpoch( startTime )
        startTime = StatsDateLib.getIsoWithRoundedHours( startTime )
        
        seperators = [startTime]
        seperators.extend( StatsDateLib.getSeparatorsWithStartTime( startTime = startTime , width=width, interval=60*StatsDateLib.MINUTE )[:-1])
            
        for seperator in seperators :
            pickles.append( StatsPickler.buildThisHoursFileName(  client = client, offset = 0, currentTime = seperator, machine = machine, fileType = fileType ) )        
        
        
        startingNumberOfEntries = 0
        #print "prior to loading and merging pickles : %s " %( StatsDateLib.getIsoFromEpoch( time.time() ) ) 
        for pickle in pickles : 
            
            if os.path.isfile( pickle ) :
                
                    
                tempCollection = CpickleWrapper.load( pickle )
                if tempCollection != None :
                    for i in xrange( len( tempCollection.fileEntries )  ):
                        entries[startingNumberOfEntries + i] = tempCollection.fileEntries[i]
                    startingNumberOfEntries = startingNumberOfEntries + len( tempCollection.fileEntries ) 
                else:                    
                    sys.exit()
            else:
                           
                emptyEntries =  PickleMerging.fillWithEmptyEntries( nbEmptyEntries = 60, entries = {} )
                for i in xrange( 60 ):
                    entries[i + startingNumberOfEntries ] = emptyEntries [i]
                startingNumberOfEntries = startingNumberOfEntries + 60
        
        #print "after the  loading and merging og pickles : %s " %( StatsDateLib.getIsoFromEpoch( time.time() ) )        
        
        statsCollection = FileStatsCollector(  startTime = startTime , endTime = endTime, interval = StatsDateLib.MINUTE, totalWidth = width, fileEntries = entries,fileType= fileType, logger = logger, logging = logging )
           
                
        return statsCollection        
    
    
    mergePicklesFromDifferentHours = staticmethod( mergePicklesFromDifferentHours )
    
    
    
    def mergePicklesFromSameHour( logger = None , pickleNames = None, mergedPickleName = "",\
                                  clientName = "" , combinedMachineName = "", currentTime = "",\
                                  fileType = "tx" ):
        """
            @summary: This methods receives a list of filenames referring to pickled FileStatsEntries.
            
                      After the merger pickles get saved since they might be reused somewhere else.
            
            @precondition:  Pickle should be of the same timespan and bucket width.
                            If not no merging will occur.  
            
        """
        
        
        if logger != None : 
            logger.debug( _("Call to mergePickles received.") )
            logging = True
        else:
            logging = False
                
        entryList = []
        
        
        for pickle in pickleNames:#for every pickle we eneed to merge
            
            if os.path.isfile( pickle ):
                
                entryList.append( CpickleWrapper.load( pickle ) )
                            
            else:#Use empty entry if there is no existing pickle of that name
                
                endTime = StatsDateLib.getIsoFromEpoch( StatsDateLib.getSecondsSinceEpoch( currentTime ) + StatsDateLib.HOUR ) 
                entryList.append( FileStatsCollector( startTime = currentTime, endTime = endTime,logger =logger, logging =logging   ) )         
                
                if logger != None :
                    logger.warning( _("Pickle named %s did not exist. Empty entry was used instead.") %pickle )    
        
        
        #start off with a carbon copy of first pickle in list.
        newFSC = FileStatsCollector( files = entryList[0].files , statsTypes =  entryList[0].statsTypes, startTime = entryList[0].startTime,\
                                     endTime = entryList[0].endTime, interval=entryList[0].interval, totalWidth = entryList[0].totalWidth,\
                                     firstFilledEntry = entryList[0].firstFilledEntry, lastFilledEntry = entryList[0].lastFilledEntry,\
                                     maxLatency = entryList[0].maxLatency, fileEntries = entryList[0].fileEntries,logger = logger,\
                                     logging = logging )
                 
        if PickleMerging.entryListIsValid( entryList ) == True :
            
            for i in range ( 1 , len( entryList ) ): #add other entries 
                
                for file in entryList[i].files :
                    if file not in newFSC.files :
                        newFSC.files.append( file ) 
                
                for j in range( len( newFSC.fileEntries ) ) : # add all entries                        
                    
                    newFSC.fileEntries[j].values.productTypes.extend( entryList[i].fileEntries[j].values.productTypes )
                    newFSC.fileEntries[j].files.extend( entryList[i].fileEntries[j].files )
                    newFSC.fileEntries[j].times.extend( entryList[i].fileEntries[j].times )  
                    newFSC.fileEntries[j].nbFiles = newFSC.fileEntries[j].nbFiles + ( newFSC.fileEntries[ j ].nbFiles)                    
                    
                    for type in newFSC.statsTypes :
                        newFSC.fileEntries[j].values.dictionary[type].extend( entryList[i].fileEntries[j].values.dictionary[type] ) 
                                               
                    newFSC.fileEntries[j].values.rows = newFSC.fileEntries[j].values.rows + entryList[i].fileEntries[j].values.rows
                
            newFSC = newFSC.setMinMaxMeanMedians( startingBucket = 0 , finishingBucket = newFSC.nbEntries -1 )
                 
               
        else:#Did not merge pickles named. Pickle list was not valid."
            
            if logger != None :
                logger.warning( _("Did not merge pickles named : %s. Pickle list was not valid.") %pickleNames )
                logger.warning( _("Filled with empty entries instead.") %pickleNames )
                
            newFSC.fileEntries = PickleMerging.fillWithEmptyEntries( nbEmptyEntries = 60 , entries = {} )    
        
        
        #prevents us from having ro remerge file later on.    
        temp = newFSC.logger
        del newFSC.logger
        CpickleWrapper.save( newFSC, mergedPickleName )
        try:
            os.chmod( mergedPickleName, 0777 )
        except:
            pass    
        
        #print "saved :%s" %mergedPickleName
        newFSC.logger = temp
        
        return newFSC
            
    
    mergePicklesFromSameHour = staticmethod( mergePicklesFromSameHour )
    
    
    
    def createNonMergedPicklesList( currentTime, machines, fileType, clients ):
        """
            @summary : Create a list of all pickles names concerning different machines for a certain hour.
        """    
        
        pickleList = []
        #print machines 
        #print clients 
        
        for machine in machines:
            for client in clients: 
                pickleList.append( StatsPickler.buildThisHoursFileName(  client = client, currentTime = currentTime, fileType = fileType, machine = machine ) )
                          
        return pickleList
    
    createNonMergedPicklesList = staticmethod( createNonMergedPicklesList )
    
    
    
    def createMergedPicklesList( startTime, endTime, clients, groupName, fileType, machines, seperators ):
        """
            
            @param machines: Machines must be an array containing the list of machines to use. 
                             If only one machine is to be used still use an array containing a single item. 
        
        """   
       
        pickleList = [] 
        combinedMachineName = ""
        
        
        combinedMachineName = combinedMachineName.join( [machine for machine in machines] )
        if groupName == "" or groupName is None:            
            groupName = groupName.join( [client for client in clients]) 
                       
        for seperator in seperators:
            pickleList.append( StatsPickler.buildThisHoursFileName(  client = groupName, currentTime = seperator, fileType = fileType, machine = combinedMachineName ) )
         
        return pickleList
        
    createMergedPicklesList = staticmethod( createMergedPicklesList )    
            
            
            
    def mergePicklesFromDifferentSources( logger = None , startTime = "2006-07-31 13:00:00",\
                                          endTime = "2006-07-31 19:00:00", clients = ["someclient"],\
                                          fileType = "tx", machines = [], groupName = "" ):
        """
            @summary : This method allows user to merge pickles coming from numerous machines
                       covering as many hours as wanted, into a single FileStatsCollector entry.
            
                       Very usefull when creating graphics on a central server with pickle files coming from 
                       remote locations.
            
        """          
           
        combinedMachineName = ""
        combinedClientName  = ""
        
        
        combinedMachineName = combinedMachineName.join( [machine for machine in machines ] )
        combinedClientName  = combinedClientName.join( [client for client in clients] )
        
        if groupName !="":
            clientsForVersionManagement = groupName 
        else:
            clientsForVersionManagement = clients
        
        vc  = PickleVersionChecker()    
           
        vc.getClientsCurrentFileList( clients )    
            
        vc.getSavedList( user = combinedMachineName, clients = clientsForVersionManagement )           
       
        width = StatsDateLib.getSecondsSinceEpoch( endTime ) - StatsDateLib.getSecondsSinceEpoch( startTime )
        startTime = StatsDateLib.getIsoWithRoundedHours( startTime )
        
        seperators = [startTime]
        seperators.extend( StatsDateLib.getSeparatorsWithStartTime( startTime = startTime , width=width, interval=60*StatsDateLib.MINUTE )[:-1])
            
        mergedPickleNames =  PickleMerging.createMergedPicklesList(  startTime = startTime, endTime = endTime, machines = machines,\
                                                                     fileType = fileType, clients = clients, groupName = groupName,\
                                                                     seperators = seperators ) #Resulting list of the merger.
           
        
        for i in xrange( len( mergedPickleNames ) ) : #for every merger needed
                
                needToMergeSameHoursPickle = False 
                pickleNames = PickleMerging.createNonMergedPicklesList( currentTime = seperators[i], machines = machines, fileType = fileType, clients = clients )
                
                if not os.path.isfile( mergedPickleNames[i] ):                
                    needToMergeSameHoursPickle = True 
                else:    
                    
                    for pickle in pickleNames : #Verify every pickle implicated in merger.
                        # if for some reason pickle has changed since last time                    
                        if vc.isDifferentFile( file = pickle, user = combinedMachineName, clients = clientsForVersionManagement ) == True :                                
                           
                            needToMergeSameHoursPickle = True 
                            break
                            
                
                if needToMergeSameHoursPickle == True :#First time or one element has changed   
                    
                    PickleMerging.mergePicklesFromSameHour( logger = logger , pickleNames = pickleNames , clientName = combinedClientName,\
                                                            combinedMachineName = combinedMachineName, currentTime = seperators[i],\
                                                            mergedPickleName = mergedPickleNames[i], fileType = fileType  )
                                        
                    for pickle in pickleNames :
                        vc.updateFileInList( file = pickle )                                               
                    
                    vc.saveList( user = combinedMachineName, clients = clientsForVersionManagement )
                    
                    
                            
        # Once all machines have merges the necessary pickles we merge all pickles 
        # into a single file stats entry. 
        if groupName !="":
            nameToUseForMerger = groupName 
        else:
            nameToUseForMerger = ""
            nameToUseForMerger = nameToUseForMerger.join( [ client for client in clients] )
        
        newFSC =  PickleMerging.mergePicklesFromDifferentHours( logger = logger , startTime = startTime, endTime = endTime, client = nameToUseForMerger,\
                                                                machine = combinedMachineName,fileType = fileType  )
       
        return newFSC
    
    mergePicklesFromDifferentSources = staticmethod( mergePicklesFromDifferentSources )
        
       
     
def main():
    """
        Small test case. Tests if everything works plus gives an idea on proper usage.
    """    
    import time
    timea = time.time()
    PickleMerging.mergePicklesFromSameHour(logger = None, pickleNames=["/apps/px/pxStats/data/pickles/1", "/apps/px/pxStats/data/pickles/2","/apps/px/pxStats/data/pickles/1", "/apps/px/pxStats/data/pickles/2","/apps/px/pxStats/data/pickles/1", "/apps/px/pxStats/data/pickles/2"], mergedPickleName = "/apps/px/data/pickles/testResultatsNew", clientName="myTest", combinedMachineName="someMachine", currentTime = "2007-06-04 18:00:00", fileType = 'tx')
    timeb = time.time()
    #print timeb-timea

if __name__ == "__main__":
    main()
    
    
    
    
    
