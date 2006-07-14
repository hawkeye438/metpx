"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.
"""

#######################################################################################
##
## Name   : FileStatsCollector.py 
##  
## Author : Nicholas Lemay  
##
## Date   : May 19th 2006
##
## Goal   : This file contains all the usefull classes and methods needed to build stats  
##          regarding latencies text files.   
##          
##          For performance puposes, users of this class can get stats from as many
##          datatypes as desired. For exemple, if they choose ['latency','bytecount'] 
##          all the entries will have the following values
##          means = [latencyMean, bytecountMean ]
##          max   = [maxLatency, max bytecount ] etc...  
##          
##          
#######################################################################################



import array,time,sys,os #important files 
import copy
from   array     import *
import MyDateLib
from   MyDateLib import *
import commands
import copy 

MINUTE = 60
HOUR   = 60 * MINUTE
DAY    = 24 * HOUR

class _Matrix:
    """
        This class is usefull to deal with two dimensional arrays. 
    
    """
    
    def __init__( self, columns =0, rows=0 ):
        """ 
           Constructor.
           By default builds a 0*0 dictionary.
           dictionary is always empty, values need to be added after creation.  
        
        """
        self.columns = columns       #number of columns of the dictionary 
        self.rows    = rows          #number of rows 
        self.dictionary  = {}        #
        self.productTypes = []       # For each line read, we save up what product type it was   


class _FileStatsEntry:
    """
        This class is used to contain all the info on a particular file entry.     
    
    """
    
    def __init__( self, values = _Matrix() , means = None , medians = None, totals = None, minimums =None, maximums = None, startTime = 0, endTime = 0 ):
        
        
        self.startTime = startTime       # Start time IN SECONDS SINCE EPOCH.
        self.endTime   = endTime         # End time IN SECONDS SINCE EPOCH.                      
        self.values    = values          # List of values from all the types. 
        self.minimums  = minimums or {}  # List of the minimums of all types.
        self.nbFiles   = 0               # Number of files dealt with during this entry.
        self.filesWhereMinOccured =  {}  # Dict of files where min appened for each type  
        self.timesWhereMinOccured =  {}  # Dict of times where min appened for each type 
        self.maximums  = maximums or {}  # Maximum of all types.   
        self.filesWhereMaxOccured =  {}  # Dict of files where max appened for each type
        self.timesWhereMaxOccured =  {}  # Dict of times where max appened for each type 
        self.filesOverMaxLatency  =  0   # Number of files per entry whos latency are too long.  
        self.means     = means    or {}  # Means for all the values of all the files.
        self.medians   = medians  or {}  # Medians for all the values of all the files.
        self.totals    = totals   or {}  # Total for all values of each files.                
        self.files     = []              # Files to be read for data collection. 
        self.times     = []              # Time of departure of an entry 
        

class FileStatsCollector:
    """
       This class contains the date structure and the functions needed to collect stats from 
       a certain file.
    
    """
    
    def __init__(self, files = None , statsTypes = None, startTime = '2005-08-30 20:06:59', width = DAY, interval=20*MINUTE, totalWidth = 24*HOUR, lastEntryCalculated = 0, lastFilledEntry = 0, maxLatency = 15,fileEntries = None ):
        """ 
            Constructor. All values can be set from the constructor by the user but recommend usage
            is to set sourceFile and statsType. The class contains other methods to set the other values
            properly.  
            
            constructor receives date in an iso format wich is conveniant for users but transforms is in a seconds since epoch format for ease of use during the program.   
            
            Precondition : Interval should be smaller than width !
        
        """    
        
        startTimeInSeconds = MyDateLib.getSecondsSinceEpoch( startTime )
        if fileEntries == None :
            fileEntries = []    
         
        self.files          = files or {}        # Source files we will use. 
        self.statsTypes     = statsTypes or []   # List of types we need to manage.
        self.fileEntries    = copy.deepcopy(fileEntries)# list of all entries wich are parsed using time seperators.
        self.startTime      = startTimeInSeconds # Beginning of the timespan used to collect stats.
        self.width          = width              # Width of said timespan.
        self.interval       = interval           # Interval at wich we separate stats entries .
        self.totalWidth     = totalWidth         # used to build timesperators.
        self.maxLatency     = maxLatency         # Acceptable limit for a latency.  
        self.timeSeperators = (MyDateLib.getSeparatorsWithStartTime( self.startTime, self.totalWidth, self.interval ) )
        
        self.nbEntries            = len ( self.timeSeperators )# Nb of "buckets" or entries  
        self.lastEntryCalculated  = lastEntryCalculated        # Last entry for wich we calculated mean max etc....
        self.lastFilledEntry      = lastFilledEntry            # Last entry we filled with data. 
        
        if fileEntries == []:
            self.createEmptyEntries()                              # Create all empty buckets right away
         



    
    
    def setMinMaxMeanMedians( self, productType = "", startingBucket = 0 , finishingBucket = 0  ):
        """
            This method takes all the values set in the values dictionary, finds the media for every
            types found and sets them in a list of medians. This means if statsTypes = [latency, bytecount]
            we will store the medians in the same order :[ latencyMedian, bytecountMedian ] 
            
            All values are set in the same method as to enhance performances slightly.
           
            Product type starting bucket and finishing bucket can be quite usefull to recalculate a days data 
            for only selected products names.  
            
            Pre-condition : Values dictionary should have been built and filled prior to using this method.
        
        """
        
        total   = 0  # Total of the values of acertain field within an entry.
        mean    = 0  # Mean of a certain field within an entry.
        minimum = 0  # Minimum of a certain field within an entry.  
        maximum = 0  # Maximum of a certain field within an entry.
        median  = 0  # Median of a certain field within a entry.
        values  = [] # Used to sort value to find median. 
        files   = [] # Used to browse all files of an entry
        times   = [] # Used to browse all times of an entry 
        
        if startingBucket != 0 :
            self.lastEntryCalculated  = startingBucket
        if finishingBucket !=0 :    
            self.lastFilledEntry = finishingBucket -1
                         
        
        for i in xrange( self.lastEntryCalculated , self.lastFilledEntry + 1 ): #for each entries we need to deal with 
            
            
            self.fileEntries[i].medians  = {}
            self.fileEntries[i].minimums = {}
            self.fileEntries[i].maximums = {}
            
            
            for aType in self.statsTypes :#for each datatype        
                
                self.fileEntries[i].minimums[aType] =  0.0    
                self.fileEntries[i].filesWhereMinOccured[aType] =  ""
                self.fileEntries[i].timesWhereMinOccured[aType]= 0 
                self.fileEntries[i].maximums[aType]= 0.0    
                self.fileEntries[i].filesWhereMaxOccured[aType] = "" 
                self.fileEntries[i].timesWhereMaxOccured[aType] = 0 
                                        
                
                if self.fileEntries[i].values.rows != 0:
                    #set values for each bucket..... 
                    for row in xrange( 0, self.fileEntries[i].values.rows ) : # for each line in the entry 
                        
                        if productType in self.fileEntries[i].values.productTypes[row] :
                            values.append(self.fileEntries[i].values.dictionary[aType][row] )#add to new array
                            files.append( self.fileEntries[i].files[row]  )
                            times.append( self.fileEntries[i].times[row]  )
                        else:
                            self.fileEntries[i].nbFiles = self.fileEntries[i].nbFiles -1 #one less interesting file
                            if aType == "latency":
                                if self.fileEntries[i].values.dictionary[aType][row] > self.maxLatency:  
                                    self.fileEntries[i].filesOverMaxLatency = self.fileEntries[i].filesOverMaxLatency - 1  
                            
                    if len( values ) != 0 :
                        minimum = values[0]
                        maximum = values[0]
                    else:
                        minimum =0
                        maximum =0
                    
                    for k in range( len( values ) ) :
                        
                        if values[k] < minimum:
                            minimum = values[k]
                            self.fileEntries[i].minimums[aType] = values[k]
                            self.fileEntries[i].filesWhereMinOccured[aType] = files[k]    
                            self.fileEntries[i].timesWhereMinOccured[aType] = times[k]
                        
                        elif values[k] > maximum:
                            maximum = values[k]
                            self.fileEntries[i].maximums[aType]= values[k]
                            self.fileEntries[i].filesWhereMaxOccured[aType] = files[k]    
                            self.fileEntries[i].timesWhereMaxOccured[aType] = times[k]  
   
                    
                                        
                    #median  = values[ int( int(self.fileEntries[i].values.rows) / 2 ) ]    
                    median  = 0 
                    total   = sum( values )
                    if len(values) != 0 :
                        mean    = float( total / len(values) )
                    else:
                        mean = 0
                        
                        
                    if aType == "errors" :
                        if total > maximum :
                            maximum = total
                            self.fileEntries[i].maximums[aType] = total
                            self.fileEntries[i].filesWhereMaxOccured[aType] = files[k]    
                            self.fileEntries[i].timesWhereMaxOccured[aType] = times[k]
                            
                         
                else: #this entry has no values 
                    minimum = 0
                    median  = 0
                    maximum = 0
                    total   = 0
                    mean    = 0
                    
                self.fileEntries[i].medians[aType]= median     # appending values to a list    
                self.fileEntries[i].means[aType] = mean         
                self.fileEntries[i].totals[aType] =  float(total)
                
                values = []
                files  = []
                times  = []
                    
        self.lastEntryCalculated = self.lastFilledEntry
    
    
    
    def findValue( self, statsType, line = "", lineType = "[INFO]" ):
        """
            This method is used to find a particular entry within a line. 
            Used with line format used in tx_satnet.logxxxxxxxxxx
        
            To be modified once line format is decided upon. 
            
        """
        
        value = "" #in case of an unknown type
        
        if line != "" and line != "\n" :
            
            if lineType == "[INFO]" :
            
                parsedLine = line.split( " " )
                
                if statsType == "latency":
                    
                    try:
                        lastPart  = parsedLine[6] 
                        lastPart  = lastPart.split(":") 
                        arrival   = MyDateLib.isoDateDashed( lastPart[6] )
                        departure = line.split( ",")
                        departure = departure[0]
                        value     = MyDateLib.getSecondsSinceEpoch( departure ) - MyDateLib.getSecondsSinceEpoch( arrival)
                        
                    except Exception,e:
                        print line 
                        print e 
                        sys.exit()
                        
                elif statsType == "arrival":
                    
                    try : # for debugging....lines passed should always be valid in final versions.      
                        
                        lastPart = parsedLine[6] 
                        lastPart = lastPart.split(":") 
                        arrival  = MyDateLib.isoDateDashed( lastPart[6] )
                        value    = MyDateLib.getSecondsSinceEpoch( arrival)    
                    
                    except Exception,e :
                        print line 
                        print e 
                        sys.exit()
                        
                elif statsType == "bytecount":
                    value = parsedLine[3]
                    value = value.replace( '(', '' )
                    value = int(value)
                    
                elif statsType == "fileName":
                    value = parsedLine[6]
                    value = value.split( ":" )
                    value = value[0]
                
                elif statsType == "departure":
                    departure = line.split( ",")
                    departure = departure[0] 
                    value     = MyDateLib.getSecondsSinceEpoch( departure )
                
                elif statsType == "productType":
                    splitLine = line.split( " " )
                    value = splitLine[6]
                    
                elif statsType == "errors" :
                    value = 0    
                
            elif lineType == "[ERROR]":
            
                if statsType == "errors" :
                    value = 1
                    
                elif statsType == "departure":
                    departure = line.split( ",")
                    departure = departure[0] 
                    value     = MyDateLib.getSecondsSinceEpoch( departure )     
                
                elif statsType == "productType" :     
                    value = ""
                else:
                    value = 0
                    
                    
        if value == "":
            print statsType
            print lineType 
            print "line has no value : %s" %line 
              
        return value


    
    def containsUsefullInfo( self, file, endTime = ""  ):
        """
            This method returns whether or not a certain file contain any data wich is within 
            the range we want.
            
        """
        
        usefull = False 
            
        
        if endTime == "" :                                        
            endTime = self.width + self.startTime
        else:
            endTime = MyDateLib.getSecondsSinceEpoch( endTime )
            
        entryCount,line,fileHandle,offset,lineType  = self.findFirstInterestingLine( file, endTime  )    
        
        
        if line != "" :    
            departure = self.findValue( "departure", line, lineType )
            
            if departure >= self.startTime  and departure <= endTime  :
                usefull = True
        
                        
        return usefull, entryCount, line , fileHandle, offset , lineType           
        
    
    
    def isInterestingLine( self, line ):
        """
            This method returns whether or not the line is interesting 
            according to the types ask for in parameters. 
            
            Also returns for what type it's interesting.   
            
            To be modified when new log file format comes in.   
        
        """
        
        isInteresting = False 
        lineType = ""
        
        if line != "" :
            
            if "errors" in self.statsTypes and "[ERROR]" in line:
                isInteresting = True
                lineType = "[ERROR]" 
            
            elif "[INFO]" in line and "Bytes" in line and "/sec" not in line and " Segment " not in line : 
                isInteresting = True             
                lineType = "[INFO]"
                
        return isInteresting,lineType
    
    
    
    def findFirstInterestingLine( self, file, endtime  ):
        """
            Finds the first interesting line in a file.
            Search starts where we last read the file.
            If file was never read starts from start of file. 
            
            Returns last entrycount treated, line where we're at in the file, 
            fileHandle of the file if we still need it and offset of the file meaning where 
            we ast read the file.
            
            Warning -> This method leaves the fileHandle wich is returned opened to decrease 
                       the overall number of open/close file operations. Method wich receives the 
                       fileHandle has the responsability to close it.   
        
        """
        
        #if file was previously read, we'll know where we last stopped
        
        offset = self.files[file][0]
        entryCount = self.files[file][1]

        fileHandle = open( file , 'rb' )
            
        fileHandle.seek( offset , 0 )
        
        line = fileHandle.readline()# we need first line 
        isInteresting ,lineType = self.isInterestingLine( line )          
        
        while isInteresting == False or ( self.findValue( "departure" , line, lineType ) < self.startTime ) :
            line = fileHandle.readline()# we read again 
            isInteresting ,lineType = self.isInterestingLine( line ) 
              
        
        return entryCount, line, fileHandle, offset, lineType
    
    
    
    def setValues( self, endTime = "" ):
        """
            This method opens a file and sets all the values found in the file in the appropriate entry's value dictionary.
            -Values searched depend on the datatypes asked for by the user.
            -Number of entries is based on the time separators wich are found with the startTime, width and interval.  -Only entries with arrival time comprised between startTime and startTime + width will be saved in matrixes
            -Entries wich have no values will have 0 as value for means, minimum maximum and median     
        
            -Finding a way to speed up file reading even more would be nice....
        
        """
        
        #try:
    
        value = []
        files =  self.files.keys()
        nbErrors = 0 
        
        if endTime == "" :                                        
            endTime = self.width + self.startTime
        else:
            endTime = MyDateLib.getSecondsSinceEpoch( endTime )
        
        for file in files :#read everyfile and append data found to matrixes 
            
            usefull, entryCount, line , fileHandle, offset, lineType  = self.containsUsefullInfo( file )
            
            for statType in self.statsTypes:
                self.fileEntries[ entryCount ].values.dictionary[statType] = []
            
            if  usefull == True :    
                
                departure   = self.findValue( "departure" , line, lineType )
                productType = self.findValue( "productType",line, lineType )
                
                while str( departure ) != "" and float( departure ) < float( endTime ) : 
                    
                    while long( departure ) > long(self.timeSeperators[ entryCount ]):
                        entryCount = entryCount + 1 
                        for statType in self.statsTypes:
                            self.fileEntries[ entryCount ].values.dictionary[statType] = []

                    if departure <= self.timeSeperators[ entryCount ]:                    
                        
                        #find values to append 
                        for statType in self.statsTypes :   
                            
                            newValue = self.findValue( statType , line, lineType )
                            
                            if statType == "latency":
                                if newValue > self.maxLatency :      
                                    self.fileEntries[ entryCount ].filesOverMaxLatency = self.fileEntries[entryCount ].filesOverMaxLatency + 1                          
                            self.fileEntries[ entryCount ].values.productTypes.append( productType )
                            self.fileEntries[ entryCount ].values.dictionary[statType].append( newValue )                                  
                            
                        #add values at the right place  
                        self.fileEntries[ entryCount ].files.append( self.findValue( "fileName" , line ) )
                        self.fileEntries[ entryCount ].times.append( self.findValue( "departure" , line ) )
                        self.fileEntries[ entryCount ].values.rows = self.fileEntries[ entryCount ].values.rows + 1
                    
                    
                    if lineType != "[ERROR]" :
                         self.fileEntries[ entryCount ].nbFiles = self.fileEntries[ entryCount ].nbFiles + 1        
                    
                    offset  = fileHandle.tell()
                    line    = fileHandle.readline()
                    isInteresting,lineType = self.isInterestingLine( line )
                    
                    while isInteresting == False :
                        line = fileHandle.readline()# we read again 
                        isInteresting,lineType = self.isInterestingLine( line )
                        
                        
                    departure   = self.findValue( "departure" , line, lineType )
                    productType = self.findValue( "productType",line, lineType )
                    value     = [] 
                
                    
                # We won't change offset if last line read isnt within range or else we'll lose it 
                # in the next reading.
                if departure == "" or departure < endTime:
                    offset = fileHandle.tell()
                    
                
                self.files[file][0]  = offset         
                self.files[file][1]  = entryCount + 1 
                
                if entryCount > self.lastFilledEntry : # in case of numerous files....
                    self.lastFilledEntry = entryCount                  
                
                fileHandle.close()                  
                                    
            
            else:
            
                print "useless file : %s" %file 
                fileHandle.close()
                
                    
#         
#         except Exception,e:
#             
#             print "*************************************************************************"
#             print "Exception : %s" %e
#             print "Error. There was an error reading source file named %s" %( self.files )
#             print "Program terminated."
#             sys.exit()                     
            
    
    
    def createEmptyEntries( self ):    
        """
            We fill up fileEntries with empty entries with proper time labels 
        
        """
        
        if len ( self.timeSeperators ) > 0 : 
            
            #treat special 0 case apart
            self.fileEntries.append( _FileStatsEntry() )
            self.fileEntries[0].startTime = self.startTime 
            self.fileEntries[0].endTime   = self.timeSeperators[0] 
            self.fileEntries[0].values    = _Matrix( len( self.statsTypes ), 0 )
            
            
            #other cases     
            for i in xrange( 1, len ( self.timeSeperators ) ):
            
                self.fileEntries.append( _FileStatsEntry() )       
                self.fileEntries[i].startTime =  self.timeSeperators[ i-1 ] 
                self.fileEntries[i].endTime   =  self.timeSeperators[ i ]  
                self.fileEntries[i].values    = _Matrix( len( self.statsTypes ), 0 )

    
    
    def collectStats( self, endTime = "" ):
        """
            This is the main method to use with a FileStatsCollector. 
            It will collect the values from the file and set them in a dictionary.
            It will use that dictionary to find the totals and means of each data types wanted. 
            It will also use that dictionary to find the minimum max andmedians of 
            each data types wanted. 
               
        """
        
        self.setValues( endTime )   #fill dictionary with values
        self.setMinMaxMeanMedians() #use values to find these values.   


                         

if __name__ == "__main__":
    """
        small test case. Tests if everything works plus gives an idea on proper usage.
    """
    
    types = [ 'latency']
    filename = '/a/lib/stats/files/log'
     
    stats = FileStatsCollector( files = dict( [("/apps/px/lib/stats/files/log", [0,0]) ] ), statsTypes = types , startTime = '2006-05-18 00:00:00', width = 1*HOUR, interval = 1*MINUTE  )
    
    stats.collectStats()   
      
