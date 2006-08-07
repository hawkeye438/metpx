"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file 
named COPYING in the root of the source directory tree.

#############################################################################################
# Name  : pickleUpdater
#
# Author: Nicholas Lemay
#
# Date  : 2006-06-15
#
# Description: 
#
#   Usage:   This program can be called from a crontab or from command-line. 
#
#   For informations about command-line:  PickleUpdater -h | --help
#
#
##############################################################################################
"""


#important files 
import os, pwd, sys,getopt, commands, fnmatch,pickle
import PXPaths 
from optparse import OptionParser
from ConfigParser import ConfigParser
from MyDateLib import *
from ClientStatsPickler import ClientStatsPickler


PXPaths.normalPaths()


class _UpdaterInfos: 
    


    def __init__( self, clients, directories, types, startTimes,collectUpToNow, fileType, currentDate = '2005-06-27 13:15:00', interval = 1, hourlyPickling = True, machine = ""   ):
        
        """
            Data structure used to contain all necessary info for a call to ClientStatsPickler. 
            
        """ 
        
        systemsCurrentDate  = MyDateLib.getIsoFromEpoch( time.time() )
        self.clients        = clients                            # Client for wich the job is done.
        self.machine        = machine                            # Machine on wich update is made. 
        self.types          = types                              # Data types to collect ex:latency 
        self.fileType       = fileType                           # File type to use ex :tx,rx etc  
        self.directories    = directories                        # Get the directory containing files  
        self.interval       = interval                           # Interval.
        self.startTimes     = startTimes                         # Time of last crontab job.... 
        self.currentDate    = currentDate or  systemsCurrentDate # Time of the cron job.
        self.collectUpToNow = collectUpToNow                     # Wheter or not we collect up to now or 
        self.hourlyPickling = hourlyPickling                     # whether or not we create hourly pickles.
        self.endTime        = self.currentDate                   # Will be currentDate if collectUpTo                                                                             now is true, start of the current                                                                               hour if not 



def setLastCronJob( client, currentDate, collectUpToNow = False    ):
    """
        This method set the clients lastcronjob to the date received in parameter. 
        Creates new key if key doesn't exist.
        Creates new PICKLED-TIMES file if it doesn't allready exist.   
        
        In final version this will need a better filename and a stable path....
        
    """
    
    times = {}
    lastCronJob = {}
    fileName = PXPaths.STATS + "PICKLED-TIMES"  
    
    if collectUpToNow == False :
        currentDate = MyDateLib.getIsoWithRoundedHours( currentDate ) 
    
    
    if os.path.isfile( fileName ):
        
        fileHandle  = open( fileName, "r" )
        times       = pickle.load( fileHandle )
        fileHandle.close()
        
        times[ client ] = currentDate
        
        fileHandle  = open( fileName, "w" )
        pickle.dump( times, fileHandle )
        fileHandle.close()
    
    
    else:#create a new pickle file  
         
        fileHandle  = open( fileName, "w" )
        
        times[ client ] = currentDate          
        
        pickle.dump( times, fileHandle )
        
        fileHandle.close()



def getLastCronJob( client, currentDate, collectUpToNow = False ):
    """
        This method gets the dictionnary containing all the last cron job list.
        From that dictionnary it returns the right value. 
        
        Note : pickled-times would need a better path..... 
        
    """ 
    
    times = {}
    lastCronJob = {}
    fileName = PXPaths.STATS +  "PICKLED-TIMES"  
    
    if os.path.isfile( fileName ):
        
        fileHandle  = open( fileName, "r" )
        times       = pickle.load( fileHandle )
        
        try :
            lastCronJob = times[ client ]
        except:
            lastCronJob = MyDateLib.getIsoWithRoundedHours( MyDateLib.getIsoFromEpoch( MyDateLib.getSecondsSinceEpoch(currentDate ) - MyDateLib.HOUR) )
            
            
        fileHandle.close()      
            
    
    else:#create a new pickle file.Set start of the pickle as last cron job.   
         
        fileHandle  = open( fileName, "w" )
        
    
        lastCronJob = MyDateLib.getIsoWithRoundedHours( MyDateLib.getIsoFromEpoch( MyDateLib.getSecondsSinceEpoch(currentDate ) - MyDateLib.HOUR) )


        times[ client ] = lastCronJob    
         
        pickle.dump( times, fileHandle )
        fileHandle.close()
       

    return lastCronJob

    
            
#################################################################
#                                                               #
#############################PARSER##############################
#                                                               #
#################################################################   
def getOptionsFromParser( parser ):
    """
        
        This method parses the argv received when the program was called
        It takes the params wich have been passed by the user and sets them 
        in the corresponding fields of the hlE variable.   
    
        If errors are encountered in parameters used, it will immediatly terminate 
        the application. 
    
    """ 
    
    directories  = []
    startTimes   = []
    
    ( options, args ) = parser.parse_args()        
    
    interval      = options.interval
    collectUpToNow= options.collectUpToNow 
    currentDate   = options.currentDate.replace( '"','' ).replace( "'",'' )
    fileType      = options.fileType.replace( "'",'' )
    machine       = options.machine.replace( " ","" )
    clients       = options.clients.replace(' ','' ).split( ',' )
    types         = options.types.replace( ' ', '' ).split( ',' )
   
     
    try:    
        if int( interval ) < 1 :
            raise 
    
    except:
        
        print "Error. The interval value needs to be an integer one above 0." 
        print "Use -h for help."
        print "Program terminated."
        sys.exit()
        
    
    if fileType != "tx" and fileType != "rx":
        print "Error. File type must be either tx or rx."
        print 'Multiple types are not accepted.' 
        print "Use -h for additional help."
        print "Program terminated."
        sys.exit()    
        
    
    if fileType == "tx":       
        validTypes = ["errors","latency","bytecount"]

    else:
        validTypes = ["errors","bytecount"]
           
    try :
        for t in types :
            if t not in validTypes:
                raise 

    except:    
        
        print "Error. With %s fileType, possible data types values are : %s." %(fileType,validTypes )
        print 'For multiple types use this syntax : -t "type1,type2"' 
        print "Use -h for additional help."
        print "Program terminated."
        sys.exit()
    
        
    for client in clients :
        directories.append( PXPaths.LOG )
        startTimes.append( getLastCronJob( client = client, currentDate =  currentDate , collectUpToNow = collectUpToNow ) )
        
        
    infos = _UpdaterInfos( currentDate = currentDate, clients = clients, startTimes = startTimes, directories = directories ,types = types, collectUpToNow = collectUpToNow, fileType = fileType, machine = machine )
    
    if collectUpToNow == False:
        infos.endTime = MyDateLib.getIsoWithRoundedHours( infos.currentDate ) 
    
    
        
    return infos 

    
    
def createParser( ):
    """ 
        Builds and returns the parser 
    
    """
    
    usage = """

%prog [options]
********************************************
* See doc.txt for more details.            *
********************************************
Notes :
- Update request for a client with no history means it's data will be collected 
  from xx:00:00 to xx:59:59 of the hour of the request.    

Defaults :

- Default Client name does not exist.
- Default Date of update is current system time.  
- Default interval is 1 minute. 
- Default Now value is False.
- Default Types value is latency.
- Accepted values for types are : errors,latency,bytecount
  -To use mutiple types, use -t|--types "type1,type2"


Options:
 
    - With -c|--clients you can specify the clients names on wich you want to collect data. 
    - With -d|--date you can specify the time of the update.( Usefull for past days and testing. )
    - With -f|--fileType you can specify the file type of the log fiels that will be used.  
    - With -i|--interval you can specify interval in minutes at wich data is collected. 
    - With -n|--now you can specify that data must be collected right up to the minute of the call. 
    - With -t|--types you can specify what data types need to be collected
    
      
WARNING: - Client name MUST be specified,no default client exists. 
         - Interval is set by default to 1 minute. If data pickle here is to be used with 
           ClientGraphicProducer, default value will need to be used since current version only 
           supports 1 minute long buckets. 
          
            
Ex1: %prog                                   --> All default values will be used. Not recommended.  
Ex2: %prog -c satnet                         --> All default values, for client satnet. 
Ex3: %prog -c satnet -d '2006-06-30 05:15:00'--> Client satnet, Date of call 2006-06-30 05:15:00.
Ex4: %prog -c satnet -t "errors,latency"     --> Uses current time, client satnet and collect those 2 types.
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
    
    parser.add_option( "-c", "--clients", action="store", type="string", dest="clients", default="satnet",
                        help="Clients' names" )

    parser.add_option( "-d", "--date", action="store", type="string", dest="currentDate", default=MyDateLib.getIsoFromEpoch( time.time() ), help="Decide current time. Usefull for testing." ) 
                                            
    parser.add_option( "-i", "--interval", type="int", dest="interval", default=1,
                        help="Interval (in minutes) for which a point will be calculated. Will 'smooth' the graph" )
    
    parser.add_option( "-f", "--fileType", action="store", type="string", dest="fileType", default='tx', help="Type of log files wanted." )                     
   
    parser.add_option( "-m", "--machine", action="store", type="string", dest="machine", default=localMachine, help = "Machine on wich the update is run." ) 
    
    parser.add_option( "-n", "--now", action="store_true", dest = "collectUpToNow", default=False, help="Collect data up to current second." )
       
    parser.add_option( "-t", "--types", type="string", dest="types", default="latency,errors,bytecount",
                        help="Types of data to look for." )          





def updateHourlyPickles( infos ):
    """
        This method is to be used when hourly pickling is done. -1 pickle per hour per client. 
        
        This method needs will update the pickles by collecting data from the time of the last 
        pickle up to the current date.(System time or the one specified by the user.)
        
        If for some reason data wasnt collected for one or more hour since last pickle,pickles
        for the missing hours will be created and filled with data. 
        
        If no entries are found for this client in the pickled-times file, we take for granted that
        this is a new client. In that case data will be collected from the top of the hour up to the 
        time of the call.
        
        If new client has been producing data before the day of the first call, user can specify a 
        different time than system time to specify the first day to pickle. He can then call this 
        method with the current system time, and data between first day and current time will be 
        collected so that pickling can continue like the other clients can.
        
        
    """  
    
    for i in range( len (infos.clients) ) :
        
        cs = ClientStatsPickler( client = infos.clients[i] )
        
        width = MyDateLib.getSecondsSinceEpoch(infos.endTime) - MyDateLib.getSecondsSinceEpoch( MyDateLib.getIsoWithRoundedHours(infos.startTimes[i] ) ) 
        
        if width > MyDateLib.HOUR :#In case pickling didnt happen for a few hours for some reason...   
            #"pickles for numerous hours"
            hours = [infos.startTimes[i]]
            hours.extend( MyDateLib.getSeparatorsWithStartTime( infos.startTimes[i], interval = MyDateLib.HOUR, width = width ))
            
            for j in range( len(hours)-1 ): #Covers hours where no pickling was done.                               
                
                startOfTheHour = MyDateLib.getIsoWithRoundedHours( hours[j] )
                if j == ( 0 ):#Hour where last pickle occured. No need to pickle all hour no rounding is made 
                    startTime = infos.startTimes[j]  
                else:
                    startTime = startOfTheHour
                
                
                endTime = MyDateLib.getIsoFromEpoch( MyDateLib.getSecondsSinceEpoch( MyDateLib.getIsoWithRoundedHours(hours[j+1] ) ))
                
                if startTime >= endTime :
                    raise Exception("Startime used in updateHourlyPickles was greater or equal to end time.")    
                    
                    
                
                cs.pickleName =  ClientStatsPickler.buildThisHoursFileName( client = infos.clients[i], currentTime =  startOfTheHour, machine = infos.machine  )
                 
                cs.collectStats( types = infos.types, startTime = startTime , endTime = endTime, interval = infos.interval * MyDateLib.MINUTE,  directory = PXPaths.LOG, fileType = "tx"  )                              
                    
        else:      
            
            startTime = infos.startTimes[i]
            endTime   = infos.endTime             
            startOfTheHour = MyDateLib.getIsoWithRoundedHours( infos.startTimes[i] )
                            
            if startTime >= endTime :
                raise Exception("Startime used in updateHourlyPickles was greater or equal to end time.")    
                
                
            cs.pickleName =   ClientStatsPickler.buildThisHoursFileName( client = infos.clients[i], currentTime = startOfTheHour, machine = infos.machine )            
              
            cs.collectStats( infos.types, startTime = startTime, endTime = endTime, interval = infos.interval * MyDateLib.MINUTE, directory = PXPaths.LOG, fileType = "tx"   )

        
        setLastCronJob( client = infos.clients[i], currentDate = infos.currentDate, collectUpToNow = infos.collectUpToNow )
                        
            

def main():
    """
        Gathers options, then makes call to ClientStatsPickler to collect the stats based 
        on parameters received.  
    
    """
    
   
    parser = createParser( )  #will be used to parse options 
    infos = getOptionsFromParser( parser )
    updateHourlyPickles( infos )
     


if __name__ == "__main__":
    main()
                              
