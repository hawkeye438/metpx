#! /usr/bin/env python
"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.
"""

#######################################################################################
##
## Name   : generateRRDGraphics.py 
##  
## Author : Nicholas Lemay  
##
## Date   : October 2nd 2006
##
## Goal   : This files contains all the methods needed to generate graphics using data  
##          found in RRD databases.
##          
##          
##          
#######################################################################################


import os, time, getopt, rrdtool  
import ClientStatsPickler, MyDateLib, pickleMerging, PXManager, PXPaths, transferPickleToRRD

from   ClientStatsPickler import *
from   optparse  import OptionParser
from   PXPaths   import *
from   PXManager import *
from   MyDateLib import *
from   Logger    import *     
from   Logger    import *       


PXPaths.normalPaths()   

if localMachine == "pds3-dev" or localMachine == "pds4-dev" or localMachine == "lvs1-stage" or localMachine == "logan1" or localMachine == "logan2":
    PATH_TO_LOGFILES = PXPaths.LOG + localMachine + "/"

else:#pds5 pds5 pxatx etc
    PATH_TO_LOGFILES = PXPaths.LOG


    
    
class _GraphicsInfos:

    def __init__( self, directory, fileType, types, totals, clientNames = None ,  timespan = 12, endDate = None, machines = ["pdsGG"], link = False  ):

            
        self.directory    = directory         # Directory where log files are located. 
        self.fileType     = fileType          # Type of log files to be used.    
        self.types        = types             # Type of graphics to produce. 
        self.clientNames  = clientNames or [] # Client name we need to get the data from.
        self.timespan     = timespan          # Number of hours we want to gather the data from. 
        self.endDate      = endDate           # Time when stats were queried.
        self.machines     = machines          # Machine from wich we want the data to be calculated.
        self.totals       = totals            # Make totals of all the specified clients 
        self.link         = link              # Whether or not to create symlinks for images. 
        
        
        
#################################################################
#                                                               #
#############################PARSER##############################
#                                                               #
#################################################################   
def getOptionsFromParser( parser ):
    """
        
        This method parses the argv received when the program was called
        It takes the params wich have been passed by the user and sets them 
        in the corresponding fields of the infos variable.   
    
        If errors are encountered in parameters used, it will immediatly terminate 
        the application. 
    
    """ 
    
    endDate   = []
    
    ( options, args )= parser.parse_args()        
    timespan         = options.timespan
    machines         = options.machines.replace( ' ','').split(',')
    clientNames      = options.clients.replace( ' ','' ).split(',')
    types            = options.types.replace( ' ', '').split(',')
    endDate          = options.endDate.replace('"','').replace("'",'')
    fileType         = options.fileType.replace("'",'')
    individual       = options.individual
    totals           = options.totals
    daily            = options.daily
    weekly           = options.weekly
    monthly          = options.monthly
    yearly           = options.yearly    
    link             = options.link
    
    counter = 0  
    specialParameters = [daily, monthly, weekly, yearly]
    for specialParameter in specialParameters:
        if specialParameter:
            counter = counter + 1 
            
    if counter > 1 :
        print "Error. Only one of the daily, weekly and yearly options can be use at a time " 
        print "Use -h for help."
        print "Program terminated."
        sys.exit()
    
    elif counter == 1 and timespan != None :
        print "Error. When using the daily, the weekly or the yearly options timespan cannot be specified. " 
        print "Use -h for help."
        print "Program terminated."
        sys.exit()
    
    elif counter == 0 and timespan == None :
        timespan = 12
    
    elif daily :
        timespan = 24
    elif weekly:
        timespan = 24 * 7
    elif monthly:
        timespan = 24 * 30     
    elif yearly:
        timespan = 24 * 365        
         
            
    try: # Makes sure date is of valid format. 
         # Makes sure only one space is kept between date and hour.
        t =  time.strptime( endDate, '%Y-%m-%d %H:%M:%S' )
        split = endDate.split()
        endDate = "%s %s" %( split[0], split[1] )

    except:    
        print "Error. The date format must be YYYY-MM-DD HH:MM:SS" 
        print "Use -h for help."
        print "Program terminated."
        sys.exit()
    
    
    try:    
        if int( timespan ) < 1 :
            raise 
                
    except:
        
        print "Error. The timespan value needs to be an integer one above 0." 
        print "Use -h for help."
        print "Program terminated."
        sys.exit()
        
        
  
    if fileType != "tx" and fileType != "rx":
        print "Error. File type must be either tx or rx."
        print 'Multiple types are not accepted.' 
        print "Use -h for additional help."
        print "Program terminated."
        sys.exit()            
        
        
    if clientNames[0] == "ALL":
        updateConfigurationFiles( machines[0], "pds" )
        #get rx tx names accordingly.         
        if fileType == "tx":    
            clientNames = getNames( "tx", machines[0] )  
        else:
            clientNames = getNames( "rx", machines[0] )      
            
    
    try :
        
        if fileType == "tx":       
        
            validTypes = [ "latency", "bytecount", "errors", "filesOverMaxLatency", "filecount" ]
            
            if types[0] == "All":
                types = validTypes
            else :
                for t in types :
                    if t not in validTypes:
                        raise Exception("")
                        
        else:      
            
            validTypes = [ "bytecount", "errors", "filecount" ]
            
            if types[0] == "All":
                types = validTypes
            
            else :
                for t in types :
                    if t not in validTypes:
                        raise Exception("")

    except:    

        print "Error. With %s fileType, possible data types values are : %s." %( fileType,validTypes )
        print 'For multiple types use this syntax : -t "type1,type2"' 
        print "Use -h for additional help."
        print "Program terminated."
        sys.exit()
  
            
    if individual != True :        
        combinedMachineName = ""
        for machine in machines:
            combinedMachineName = combinedMachineName + machine
                    
        machines = [ combinedMachineName ]              
                
    directory = PATH_TO_LOGFILES
    
    endDate = MyDateLib.getIsoWithRoundedHours( endDate )
    
    infos = _GraphicsInfos( endDate = endDate, clientNames = clientNames,  directory = directory , types = types, timespan = timespan, machines = machines, fileType = fileType, totals = totals, link = link  )   
            
    return infos 
       
    
                
def getNames( fileType, machine ):
    """
        Returns a tuple containing RXnames or TXnames that we've rsync'ed 
        using updateConfigurationFiles
         
    """    
                        
    pxManager = PXManager()
    
    remoteMachines = [ "pds3-dev", "pds4-dev","lvs1-stage", "logan1", "logan2" ]
    if localMachine in remoteMachines :#These values need to be set here.
        PXPaths.RX_CONF  = '/apps/px/stats/rx/%s/'  %machine
        PXPaths.TX_CONF  = '/apps/px/stats/tx/%s/'  %machine
        PXPaths.TRX_CONF = '/apps/px/stats/trx/%s/' %machine
    pxManager.initNames() # Now you must call this method  
    
    if fileType == "tx":
        names = pxManager.getTxNames()               
    else:
        names = pxManager.getRxNames()  

    return names 
        
    
    
def updateConfigurationFiles( machine, login ):
    """
        rsync .conf files from designated machine to local machine
        to make sure we're up to date.
    
    """  
    
    if not os.path.isdir( '/apps/px/stats/rx/%s/' %machine):
        os.makedirs(  '/apps/px/stats/rx/%s/' %machine, mode=0777 )
    if not os.path.isdir( '/apps/px/stats/tx/%s' %machine ):
        os.makedirs( '/apps/px/stats/tx/%s/' %machine , mode=0777 )
    if not os.path.isdir( '/apps/px/stats/trx/%s/' %machine ):
        os.makedirs(  '/apps/px/stats/trx/%s/' %machine, mode=0777 )       

        
    status, output = commands.getstatusoutput( "rsync -avzr --delete-before -e ssh %s@%s:/apps/px/etc/rx/ /apps/px/stats/rx/%s/"  %( login, machine, machine) ) 

    
    status, output = commands.getstatusoutput( "rsync -avzr --delete-before -e ssh %s@%s:/apps/px/etc/tx/ /apps/px/stats/tx/%s/"  %( login, machine, machine) )  



def createParser( ):
    """ 
        Builds and returns the parser 
    
    """
    
    usage = """

%prog [options]
********************************************
* See doc.txt for more details.            *
********************************************

Defaults :

- Default Client is the entire tx/rx list that corresponds to the list of machine passed in parameter.
- Default Date is current system time.  
- Default Types value is "bytecount", "errors", "filecount" for rx and 
  "latency", "bytecount", "errors", "filesOverMaxLatency", "filecount"
  for tx.
- Default span is 12 hours.
- Accepted values for types are the same as default types.
- To use mutiple types, use -t|--types "type1,type2"
 

Options:
 
    - With -c|--clients you can specify the clients names on wich you want to collect data. 
    - With -d|--daily you can specify you want daily graphics.
    - With -e|--endDate you can specify the time of the request.( Usefull for past days and testing. )
    - With -f|--fileType you can specify the file type of the log fiels that will be used.  
    - With -m|--monthly you can specify you want monthly graphics.
    - With   |--machines you can specify from wich machine the data is to be used.
    - With -s|--span you can specify the time span to be used to create the graphic 
    - With -t|--types you can specify what data types need to be collected
    - With -y|--yearly you can specify you want yearly graphics.
            
    
Ex1: %prog                                   --> All default values will be used. Not recommended.  
Ex2: %prog -e "2006-10-10 15:13:00" -s 12 
     --machines "pds1" -f tx                 --> Generate all avaibable graphic types for every tx 
                                                 client found on the machine named pds1. Graphics will
                                                 be 12 hours wide and will end at 15:00:00.  
Ex3: %prog -e "2006-10-10 15:13:00" -y 
     --machines "pds1"                       --> Generate all yearly graphics for all tx and rx clients
                                                 associated with the machine named pds1. 
                                                                                                
********************************************
* See /doc.txt for more details.           *
********************************************"""   
    
    parser = OptionParser( usage )
    addOptions( parser )
    
    return parser     
        
        

def addOptions( parser ):
    """
        This method is used to add all available options to the option parser.
        
    """
    
    localMachine = os.uname()[1]
    
    parser.add_option("-c", "--clients", action="store", type="string", dest="clients", default="ALL",
                        help="Clients' names")
    
    parser.add_option("-d", "--daily", action="store_true", dest = "daily", default=False, help="Create daily graph(s).")
    
    parser.add_option("-e", "--endDate", action="store", type="string", dest="endDate", default=MyDateLib.getIsoFromEpoch( time.time() ), help="Decide end time of graphics. Usefull for testing.")
    
    parser.add_option("-f", "--fileType", action="store", type="string", dest="fileType", default='tx', help="Type of log files wanted.")                     
    
    parser.add_option("-i", "--individual", action="store_true", dest = "individual", default=False, help="Dont combine data from specified machines. Create graphs for every machine independently")
    
    parser.add_option("-l", "--link", action="store_true", dest = "link", default=False, help="Create a link file for the generated image.")
        
    parser.add_option("-m", "--monthly", action="store_true", dest = "monthly", default=False, help="Create monthly graph(s).")
     
    parser.add_option( "--machines", action="store", type="string", dest="machines", default=localMachine, help = "Machines for wich you want to collect data." )   
    
    parser.add_option("-s", "--span", action="store",type ="int", dest = "timespan", default=None, help="timespan( in hours) of the graphic.")
       
    parser.add_option("-t", "--types", type="string", dest="types", default="All",help="Types of data to look for.")   
    
    parser.add_option("--totals", action="store_true", dest = "totals", default=False, help="Create graphics based on the totals of all the values found for all specified clients or for a specific file type( tx, rx ).")
    
    parser.add_option("-w", "--weekly", action="store_true", dest = "weekly", default=False, help="Create weekly graph(s).")
    
    parser.add_option("-y", "--yearly", action="store_true", dest = "yearly", default=False, help="Create yearly graph(s).")
    
    
        
def buildTitle( type, client, endDate, timespan, minimum, maximum, mean  ):
    """
        Returns the title of the graphic based on infos. 
    
    """
    
    span = timespan
    timeMeasure = "hours"
    
    if span%(365*24) == 0 :
        span = span/(365*24)
        timeMeasure = "year(s)" 
    
    elif span%(30*24) == 0 :
        span = span/(30*24)
        timeMeasure = "month(s)" 
    
    elif span%24 == 0 :
        span = span/24
        timeMeasure = "day(s)" 
    
    type = type[0].upper() + type[1:] 
       
    return  "%s for %s for a span of %s %s ending at %s." %( type, client, span, timeMeasure, endDate )    

    
 
def getAbsoluteMin( databaseName, startTime, endTime, logger = None ):
    """
        This methods returns the minimum of the entire set of data found between 
        startTime and endTime within the specified database name.
        
        In most case this will be a different min than the visible min found
        on the graphic since the drawn points usually show the total or average of 
        numerous data entries.
        
    
    """
    
    minimum = None 
    
    try :  
    
        output = rrdtool.fetch( databaseName, 'MIN', '-s', "%s" %startTime, '-e', '%s' %endTime )
        minTuples = output[2]
        
        i = 0 
        while i < len( minTuples ):
            if minTuples[i][0] != 'None' and minTuples[i][0] != None  :       
                                
                if minTuples[i][0] < minimum or minimum == None : 
                    minimum = minTuples[i][0]
                    #print minimum
            i = i + 1 
       
         
    except :
        if logger != None:
            logger.error( "Error in generateRRDGraphics.getOverallMin. Unable to read %s" %databaseName )
        pass    
        
    return minimum
    
    
    
def getAbsoluteMax( databaseName, startTime, endTime, logger = None ):
    """
        This methods returns the max of the entire set of data found between 
        startTime and endTime within the specified database name.        
                
        In most case this will be a different max than the visible max found
        on the graphic since the drawn points usually show the total or average of 
        numerous data entries.
        
    """  
    
    maximum = None
    
    try:
    
        output = rrdtool.fetch( databaseName, 'MAX', '-s', "%s" %startTime, '-e', '%s' %endTime )      
        
        maxTuples = output[2]
        
        for maxTuple in maxTuples :
            if maxTuple[0] != 'None' and maxTuple[0] != None :
                if maxTuple[0] > maximum : 
                    maximum = maxTuple[0]

    
    except :
        if logger != None:
            logger.error( "Error in generateRRDGraphics.getOverallMin. Unable to read %s" %databaseName )
        pass    
    
    return maximum 
 
    
       
def getAbsoluteMean( databaseName, startTime, endTime, logger = None  ):
    """
        This methods returns the mean of the entire set of data found between 
        startTime and endTime within the specified database name.
        
                
        In most case this will be a different mean than the visible mean found
        on the graphic since the drawn points usually show the total or average of 
        numerous data entries.
        
    """
    
    sum = 0 
    avg = 0
    
    try :
        
        output = rrdtool.fetch( databaseName, 'AVERAGE', '-s', "%s" %startTime, '-e', '%s' %endTime )

        meanTuples = output[2]
        i = 0
        for meanTuple in meanTuples :            
            if meanTuple[0] != 'None' and meanTuple[0] != None :
                sum = sum + meanTuple[0]
                i = i + 1         
        
        avg = sum / len( meanTuples )  
        
    
    except :
        if logger != None:
            logger.error( "Error in generateRRDGraphics.getOverallMin. Unable to read %s" %databaseName )
        pass    
            
    return avg 


        
def getGraphicsMinMaxMean( databaseName, startTime, endTime, interval, logger = None  ):
    """
        This methods returns the min max and mean of the entire set of data that is drawn 
        on the graphic.
                
    """
    
    min = None
    max = None
    sum = 0 
    avg = 0
    
    try :
        
        output = rrdtool.fetch( databaseName, 'AVERAGE', '-s', "%s" %startTime, '-e', '%s' %endTime )
        meanTuples = output[2]

        for meanTuple in meanTuples :            
            if meanTuple[0] != 'None' and meanTuple[0] != None :
                realValue = ( float(meanTuple[0]) * float(interval) ) 
                if  realValue > max:
                    max = realValue
                if realValue < min or min == None :
                    min = realValue 
                sum = sum + realValue
            
        avg = sum / len( meanTuples )  
    
    except :
        if logger != None:
            logger.error( "Error in generateRRDGraphics.getOverallMin. Unable to read %s" %databaseName )
        pass    
            
    
    return min, max, avg
    
    
    
def buildImageName(  type, client, machine, infos, logger = None ):
    """
        Builds and returns the image name to be created by rrdtool.
        
    """

    span = infos.timespan
    timeMeasure = "hours"
    
    if infos.timespan%(365*24) == 0 :
        span = infos.timespan/(365*24)
        timeMeasure = "years" 
    
    elif infos.timespan%(30*24) == 0 :
        span = infos.timespan/(30*24)
        timeMeasure = "months" 
    
    elif infos.timespan%24 == 0 :
        span = infos.timespan/24
        timeMeasure = "days" 
       
                    
    date = infos.endDate.replace( "-","" ).replace( " ", "_")
    
    fileName = PXPaths.GRAPHS + "%s/rrdgraphs/%s_%s_%s_%s_%s%s_on_%s.png" %( client, infos.fileType, client, date, type, span, timeMeasure, machine )
    
    
    fileName = fileName.replace( '[', '').replace(']', '').replace(" ", "").replace( "'","" )               
    
    splitName = fileName.split( "/" ) 
    
    if fileName[0] == "/":
        directory = "/"
    else:
        directory = ""
    
    for i in range( 1, len(splitName)-1 ):
        directory = directory + splitName[i] + "/"
    
        
    if not os.path.isdir( directory ):
        os.makedirs( directory, mode=0777 ) 
           
    return fileName 


    
def getDatabaseTimeOfUpdate( client, machine, fileType ):
    """
        If present in DATABASE-UPDATES file, returns the time of the last 
        update associated with the databse name.      
        
        Otherwise returns None 
        
    """ 
    
    lastUpdate = 0
    folder   = PXPaths.STATS + "DATABASE-UPDATES/%s/" %fileType
    fileName = folder + "%s_%s" %( client, machine )
    
    if os.path.isfile( fileName ):
        
        fileHandle  = open( fileName, "r" )
        lastUpdate  = pickle.load( fileHandle )           
        fileHandle.close()     
        
            
    return lastUpdate      


        
def formatMinMaxMean( minimum, maximum, mean, type ):
    """
        Formats min, max and median so that it can be used 
        properly as a label on the produced graphic.
        
    """    
    
    values = [ minimum, maximum, mean]
    
    if type == "bytecount" :
        
        for i in range( len(values) ):
            
            if values[i] != None :
                
                if values[i] < 1000:#less than a k
                    values[i] = "%s Bytes" %int( values[i] )
                    
                elif values[i] < 1000000:#less than a meg 
                    values[i] = "%.2f KiloBytes"  %( values[i]/1000.0 )
                
                elif values[i] < 1000000000:#less than a gig      
                    values[i] = "%.2f MegaBytes"  %( values[i]/1000000.0 )
                
                else:#larger than a gig
                    values[i] = "%.2f GigaBytes"  %( values[i]/1000000000.0 )                 
    
    else:
    
        if minimum != None :
            if type == "latency":
                minimum = "%.2f" %minimum                
            else:
                minimum = "%s" %int(minimum)
                   
        if maximum != None :
            if type == "latency":    
                maximum = "%.2f" %maximum
            else:
                maximum = "%s" %int(maximum)
                
        if mean != None :
            mean = "%.2f" %mean 
        values = [ minimum, maximum, mean]
            
    return values[0], values[1], values[2]            
    
    
            
def getInterval( startTime, timeOfLastUpdate, dataType  ):    
    """
        Returns the interval that was used for data consolidation 
        distance between starTTime being used and the time of the 
        last update of the database. Usefull when using totals
        and and not means.
    
        Will always return 1 if dataType = "latency" because latencies
        cannot be used as totals, only as means.
        
    """    

    if dataType == "latency" :
        interval = 1.0 #No need to multiply average by interval. It's the mean we want in the case of latency.
    elif ( timeOfLastUpdate - startTime ) < (7200 * 60):#less than a week 
        interval = 1.0
    elif ( timeOfLastUpdate - startTime ) < (20160 * 60):#less than two week
        interval = 60.0
    elif (timeOfLastUpdate - startTime) < (1460*240*60):
        interval = 240.0 
    else:
        interval = 1440.0    
        
    return interval


    
def getLinkDestination( type, client, infos ):
    """
       This method returns the absolute path to the symbolic 
       link to create based on the time of creation of the 
       graphic and the span of the graphic.
    
    """
    graphicType = "weekly"
    endDateInSeconds = MyDateLib.getSecondsSinceEpoch( infos.endDate )
    
    
    if infos.timespan >= 365*24:
        graphicType = "yearly"
    elif infos.timespan >= 28*24:
        graphicType = "monthly"    

    if graphicType == "weekly":
        fileName =  time.strftime( "%W", time.gmtime( endDateInSeconds ) )
    elif graphicType == "monthly":
        fileName =  time.strftime( "%b", time.gmtime( endDateInSeconds ) )
    elif graphicType == "yearly":
        fileName =  time.strftime( "%Y", time.gmtime( endDateInSeconds ) )
    
    
    destination = PXPaths.GRAPHS + "symlinks/%s/%s/%s/%.50s.png" %( graphicType, type , client, fileName )
    
    return destination    
    
         
    
def createLink( client, type, imageName, infos ):
    """
        Create a symbolic link in the appropriate 
        folder to the file named imageName.
        
    """ 
   
    src         = imageName
    destination = getLinkDestination( type, client, infos )

    if not os.path.isdir( os.path.dirname( destination ) ):
        os.makedirs( os.path.dirname( destination ), mode=0777 )                                                      
    
    if os.path.isfile( destination ):
        os.remove( destination )
    
    print "src : %s dest : %s" %(src,destination)    
    os.symlink( src, destination )    
    
    
    
def plotRRDGraph( databaseName, type, fileType, client, machine, infos, lastUpdate = None, logger = None ):
    """
        This method is used to produce a rrd graphic.
        
    """
    
    
    imageName  = buildImageName( type, client, machine, infos, logger )     
    end        = int ( MyDateLib.getSecondsSinceEpoch ( infos.endDate ) )  
    start      = end - ( infos.timespan * 60 * 60 ) 
    
    if lastUpdate == None :
        lastUpdate = getDatabaseTimeOfUpdate( client, machine, fileType )
    
    print "lastUpdate : %s" %lastUpdate
    interval = getInterval( start, lastUpdate, type  )
        
    minimum, maximum, mean = getGraphicsMinMaxMean( databaseName, start, end, interval )
    minimum, maximum, mean = formatMinMaxMean( minimum, maximum, mean, type )            
            
    if type == "latency" or type == "filesOverMaxLatency":
        innerColor = "cd5c5c"
        outerColor = "8b0000"
    elif type == "bytecount" or type == "filecount" :
        innerColor = "019EFF"
        outerColor = "4D9AA9"  
    else:
        innerColor = "54DE4F"
        outerColor = "1C4A1A"     
                   
    title = buildTitle( type, client, infos.endDate, infos.timespan, minimum, maximum, mean )

#     try:
    rrdtool.graph( imageName,'--imgformat', 'PNG','--width', '800','--height', '200','--start', "%i" %(start) ,'--end', "%s" %(end), '--vertical-label', '%s' %type,'--title', '%s'%title,'COMMENT: Minimum: %s     Maximum: %s     Mean: %s\c' %( minimum, maximum, mean), '--lower-limit','0','DEF:%s=%s:%s:AVERAGE'%( type,databaseName,type), 'CDEF:realValue=%s,%i,*' %(type,interval), 'AREA:realValue#%s:%s' %( innerColor, type ),'LINE1:realValue#%s:%s'%( outerColor, type ) )

    if infos.link == True:
        createLink( client, type, imageName, infos )
    
    print "Plotted : %s" %imageName
    if logger != None:
        logger.info(  "Plotted : %s" %imageName )
       
    
#     except :
#         if logger != None:
#             logger.error( "Error in generateRRDGraphics.plotRRDGraph. Unable to generate %s" %imageName )
#         pass     

        
        
def createNewDatabase( fileType, type, machine, start, infos, logger ):       
    """
        Creates a brand new database bases on fileType,type and machine.
        
        If a database with the same name allready exists, it will be removed.
        
        Databases are created with rras that are identical to those found in the 
        transferPickleToRRD.py file. If databases are to change there they must be
        changed here also.  
    
    """
    
    combinedDatabaseName = PXPaths.STATS + "databases/combined/%s_%s_%s" %( fileType, type, machine )
     
        
    if os.path.isfile( combinedDatabaseName ):
        status, output = commands.getstatusoutput("rm %s " %combinedDatabaseName )
        
    elif not os.path.isdir( PXPaths.STATS + "databases/combined/" ):
        os.makedirs( PXPaths.STATS + "databases/combined/" )       
    
    if infos.timespan <(5*24):#daily :
        start = start - 60
        rrdtool.create( combinedDatabaseName, '--start','%s' %( start ), '--step', '60', 'DS:%s:GAUGE:60:U:U' %type,'RRA:AVERAGE:0:1:7200','RRA:MIN:0:1:7200', 'RRA:MAX:0:1:7200' )
             
    
    elif infos.timespan >(5*24) and infos.timespan <(14*24):# weekly :  
        start = start - (60*60)
        rrdtool.create( combinedDatabaseName, '--start','%s' %( start ), '--step', '3600', 'DS:%s:GAUGE:3600:U:U' %type,'RRA:AVERAGE:0:1:336','RRA:MIN:0:1:336', 'RRA:MAX:0:1:336' )               
                   
    
    elif infos.timespan <(365*24):#monthly
        start = start - (240*60)
        rrdtool.create( combinedDatabaseName, '--start','%s' %( start ), '--step', '14400', 'DS:%s:GAUGE:14400:U:U' %type, 'RRA:AVERAGE:0:1:1460','RRA:MIN:0:1:1460','RRA:MAX:0:1:1460' )  
        
    
    else:#yearly
        start = start - (1440*60)
        rrdtool.create( combinedDatabaseName, '--start','%s' %( start ), '--step', '86400', 'DS:%s:GAUGE:86400:U:U' %type, 'RRA:AVERAGE:0:1:3650','RRA:MIN:0:1:3650','RRA:MAX:0:1:3650' ) 
        
    
    return combinedDatabaseName
    
    
    
def getPairsFromAllDatabases( type, machine, start, end, infos, logger=None ):
    """
        This method gathers all the needed between start and end from all the
        databases wich are of the specifed type and from the specified machine.
        
        It then makes only one entry per timestamp, and returns the 
        ( timestamp, combinedValue ) pairs.
        
    """
    
    i = 0
    pairs = []
    typeData = {}
    nbEntries = 0    
    lastUpdate =0     
    
    
    for client in infos.clientNames:#Gather all pairs for that type
        
        databaseName = transferPickleToRRD.buildRRDFileName( type, client, machine )
        status, output = commands.getstatusoutput("rrdtool fetch %s  'AVERAGE' -s %s  -e %s" %( databaseName, start, end) )
        output = output.split( "\n" )[2:]
        typeData[client] = output
    
 
    while lastUpdate ==0 and i < len( infos.clientNames ) : # in case some databases dont exist
        lastUpdate = getDatabaseTimeOfUpdate( infos.clientNames[i], machine, infos.fileType )        
        interval  =  getInterval( start, lastUpdate, "other" )           
        nbEntries = int(( end-start ) / (interval * 60)) + 1 
        i = i + 1
        
        
    for i in range( nbEntries ) :#make total of all clients for every timestamp
        
        total = 0.0
        
        for client in infos.clientNames:
            
            try : 
                data = typeData[client][i].split( ":" )[1].replace(" ", "")
                
                if data != None and data != 'None' and data!= 'nan':
                    total = total + float( data )
                    
#                     if type == "errors":#for test
#                        print "%s: %s %s" %( client, MyDateLib.getIsoFromEpoch( start + ( i * interval * 60) ),float(data)*24*60 )
                
                elif logger != None: 
                    logger.warning( "Could not find data for %s for present timestamp." %(client) )
                         
            except:
                
                if logger != None :                    
                    logger.warning( "Could not find data for %s for present timestamp." %(client) )
                             
        
        if type == "latency":#latency is always an average
            total = total / ( len( output ) )
                     
        
        pairs.append( [typeData[client][i].split( " " )[0].replace( ":", "" ), total] )   
        
#         if type == "errors":#for test
#             print "Will update with : %s    %s" %(typeData[client][i].split( " " )[0].replace( ":", "" ), total)
    
    return pairs
    
    
    
def createMergedDatabases( infos, logger = None ):
    """
        Gathers data from all needed databases.
        
        Creates new databases to hold merged data.
        
        Feeds new databases with merged data. 
        
        Returns the list of created databases names.
         
    """            

    dataPairs  = {}
    typeData   = {}
    end        = int ( MyDateLib.getSecondsSinceEpoch ( infos.endDate ) )  
    start      = end - ( infos.timespan * 60 * 60 ) 
    databaseNames = {}
    

    for machine in infos.machines:
        
        for type in infos.types :         
            typeData[type] = {}
            pairs = getPairsFromAllDatabases( type, machine, start, end, infos, logger )                        
            
            combinedDatabaseName = createNewDatabase( infos.fileType, type, machine, start, infos, logger )
                                                     
            databaseNames[type] = combinedDatabaseName                            
                
            for pair in pairs:
                rrdtool.update( combinedDatabaseName, '%s:%s' %( int(pair[0]), pair[1] ) )
                 
                
    return databaseNames
                    
            
            
def generateRRDGraphics( infos, logger = None ):
    """
        This method generates all the graphics. 
                
    """    
        
    if infos.totals: #Graphics based on total values from a group of clients.
        #todo : Make 2 title options
        
        databaseNames = createMergedDatabases( infos, logger )
                
        for machine in infos.machines:
            for type in infos.types:
                plotRRDGraph( databaseNames[type], type, infos.fileType, infos.fileType, machine, infos, lastUpdate =  MyDateLib.getSecondsSinceEpoch(infos.endDate), logger =logger )
                
    else:
        for machine in infos.machines:
            
            for client in infos.clientNames:
                
                for type in infos.types : 
                    databaseName = transferPickleToRRD.buildRRDFileName( type, client, machine ) 
                    plotRRDGraph( databaseName, type, infos.fileType, client, machine, infos,lastUpdate =  MyDateLib.getSecondsSinceEpoch(infos.endDate), logger = logger )
                


def main():
    """
        Gathers options, then makes call to generateRRDGraphics   
    
    """    
    
    localMachine = os.uname()[1] # /apps/px/log/ logs are stored elsewhere at the moment.
    
    if not os.path.isdir( PXPaths.LOG  ):
        os.makedirs( PXPaths.LOG , mode=0777 )
    
    logger = Logger( PXPaths.LOG  + 'stats_'+'rrd_graphs' + '.log.notb', 'INFO', 'TX' + 'rrd_transfer', bytes = True  ) 
    
    logger = logger.getLogger()
       
    parser = createParser() 
   
    infos = getOptionsFromParser( parser )

    generateRRDGraphics( infos, logger = logger )
    
    
    
if __name__ == "__main__":
    main()    
    