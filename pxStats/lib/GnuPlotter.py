#!/usr/bin/env python2
"""

#############################################################################################
#
# @name: GnuPlotter.py f.k.a StatsPlotter.py f.k.a Plotter.py
#
# @author      : Nicholas Lemay, but the code is highly inspired by previously created file 
#                named Plotter.py written by Daniel Lemay. This file can be found in the lib
#                folder of this application. 
#
# @since        : 2006-06-06, last updated on 2008-05-09
#
#
# @license: MetPX Copyright (C) 2004-2008  Environment Canada
#           MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
#           named COPYING in the root of the source directory tree.
#
#
#
# @summary : This class contain the data structure and the methods used to plot a graphic 
#            using previously collected data through the Gnuplot library. The data should
#            have been collected using  the data collecting class' and methods found in 
#            the stats library. 
# 
#
#@requires: Requires the gnuplot library to have been installed.
#
#
#
#############################################################################################


"""
# General imports
import os, sys, shutil, statvfs

# Requires the gnuplot library to be installed.
import Gnuplot, Gnuplot.funcutils 


"""
    - Small function that adds pxStats to sys path.  
"""
sys.path.insert(1,  os.path.dirname( os.path.abspath(__file__) ) + '/../../')

# These imports require pxStats.
from pxStats.lib.StatsDateLib import StatsDateLib
from pxStats.lib.StatsPaths import StatsPaths
from pxStats.lib.LanguageTools import LanguageTools
from pxStats.lib.Translatable import Translatable

"""
    - Small function that adds pxLib to sys path.
"""
STATSPATHS = StatsPaths( )
STATSPATHS.setBasicPaths()
sys.path.append( STATSPATHS.PXLIB )

"""
    These imports require pxlib 
"""
from   Logger  import Logger


"""
    Globals
"""
CURRENT_MODULE_ABS_PATH =  os.path.abspath(__file__).replace( ".pyc", ".py" )
LOCAL_MACHINE = os.uname()[1]


class GnuPlotter( Translatable ):


    def __init__( self, timespan,  stats = None, clientNames = None, groupName = "", type='lines',           \
                  interval=1, imageName="gnuplotOutput", title = "Stats", currentTime = "",now = False,      \
                  statsTypes = None, productTypes = None, logger = None, logging = True, fileType = "tx", \
                  machines = "", entryType = "minute", maxLatency = 15, workingLanguage = None, outputLanguage = None ):
        """
        
            @summary : GnuPlotter constructor. 
            
        """                                                                    
        
        #TODO Verify if all theses fileds are really necessary.    
        machines = "%s" %machines
        machines = machines.replace( "[","").replace( "]","" ).replace( "'", "" )
        
        self.now         = now                     # False means we round to the top of the hour, True we don't
        self.stats       = stats or []             # ClientStatsPickler instance.
        self.clientNames = clientNames or []       # Clients for wich we are producing the graphics. 
        self.groupName   = groupName               # Group name used when combining data of numerous client/sources.
        self.timespan    = timespan                # Helpfull to build titles 
        self.currentTime = currentTime             # Time of call
        self.type        = 'impulses'              # Must be in: ['linespoint', 'lines', 'boxes', 'impulses'].
        self.fileType    = fileType                # Type of file for wich the data was collected
        self.imageName   = imageName               # Name of the image file.
        self.nbFiles     = []                      # Number of files found in the data collected per server.
        self.nbErrors    = []                      # Number of errors found per server
        self.graph       = Gnuplot.Gnuplot()       # The gnuplot graphic object itself. 
        self.timeOfMax   = [[]]                    # Time where the maximum value occured.  
        self.machines    = machines                # List of machine where we collected info.
        self.entryType   = entryType               # Entry type :  minute, hour, week, month
        self.clientName  = ""                      # Name of the client we are dealing with 
        self.maxLatency  = maxLatency              # Maximum latency 
        self.maximums    = [[]]                    # List of all maximum values 1 for each graphic.
        self.minimums    = [[]]                    # Minimum value of all pairs.
        self.means       = [[]]                    # Mean of all the pairs.
        self.maxFileNames= [[]]                    # Name of file where value is the highest .
        self.filesWhereMaxOccured = [[]]           # List of files for wich said maximums occured.  
        self.statsTypes  = statsTypes or []        # List of data types to plot per client.
        self.totalNumberOfBytes    = []            # Total of bytes for each client 
        self.nbFilesOverMaxLatency = []            # Numbers of files for wich the latency was too long.
        self.ratioOverLatency      = []            # % of files for wich the latency was too long. 
        self.const = len( self.stats ) -1          # Usefull constant
        self.productTypes = productTypes           # Type of product for wich the graph is being generated.  
        self.initialiseArrays()
        self.loggerName       = 'gnuPlotter'
        self.logger           = logger
        self.logging          = logging
        self.workingLanguage  = workingLanguage   # Language with whom we are currently working, in which the string parameters were specified.
        self.outputLanguage  = outputLanguage    # Language in which the graphics will be produced.
        
        if self.logging == True:
            if self.logger == None: # Enable logging
                self.logger = Logger( StatsPaths.STATSLOGGING +  'stats_' + self.loggerName + '.log',\
                                      'INFO', 'TX' + self.loggerName, bytes = True  ) 
                self.logger = self.logger.getLogger()
        
        if self.workingLanguage == None:
            self.workingLanguage = LanguageTools.getMainApplicationLanguage()
        
        if self.outputLanguage == None:    
            self.outputLanguage = LanguageTools.getMainApplicationLanguage()
            
        if self.workingLanguage not in LanguageTools.getSupportedLanguages():
            if self.logging == True:
                _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )
                self.logger.error( _("Error. %s is not a supported working language.") %( self.workingLanguage )  )
                sys.exit()
                
        if self.outputLanguage not in LanguageTools.getSupportedLanguages():
            if self.logging == True:
                _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )
                self.logger.error( _("Error. %s is not a supported output language.") %( self.outputLanguage )  )        
                sys.exit()
                
        
        _ = self.getTranslatorForModule(CURRENT_MODULE_ABS_PATH, self.workingLanguage)
        
        self.productTypes = productTypes or [ _( "All" ) ]
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )        
        
        
        
        if self.fileType == 'tx':
            self.sourlient = _("Client")
        else:
            self.sourlient = _("Source")

        self.xtics       = self.getXTics( )        # Seperators on the x axis.
            


    def initialiseArrays( self ):
        """
            @summary : Used to set the size of the numerous arrays needed in GnuPlotter
        """
        
        #TODO Verify if really necessary
        nbClients = len( self.clientNames )
        nbTypes   = len( self.statsTypes )
        
        self.nbFiles = [0] * nbClients
        self.nbErrors = [0] * nbClients
        self.nbFilesOverMaxLatency = [0] * nbClients
        self.totalNumberOfBytes    = [0] * nbClients
        self.ratioOverLatency      = [0.0] * nbClients
        self.timeOfMax   = [ [0]*nbTypes  for x in range( nbClients ) ]
        self.maximums    = [ [0.0]*nbTypes  for x in range( nbClients ) ] 
        self.minimums    = [ [0.0]*nbTypes  for x in range( nbClients ) ]
        self.means       = [ [0.0]*nbTypes  for x in range( nbClients ) ]
        self.maxFileNames= [ [0.0]*nbTypes  for x in range( nbClients ) ]
        self.filesWhereMaxOccured =  [ [0.0]*nbTypes  for x in range( nbClients ) ] 
            

        
    def buildImageName( self ):
        """
            @summary : Builds and returns the absolute fileName so that it can be saved 
            
                       If folder to file does not exists creates it.
        
        """ 
        
        statsPaths = StatsPaths()
        statsPaths.setPaths(self.outputLanguage)
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )

        entityName = ""
        
        if len( self.clientNames ) == 0:
            entityName = self.clientNames[0]
        else:
            if self.groupName == "" :
                for name in self.clientNames :
                    entityName = entityName + name  
                    if name != self.clientNames[ len(self.clientNames) -1 ] :
                        entityName = entityName + "-"  
            else:
                entityName = self.groupName 
                
        date = self.currentTime.replace( "-","" ).replace( " ", "_")
        
        if self.productTypes[0] == _("All") or self.productTypes[0] == "*":
            
            formattedProductName = LanguageTools.translateTerm(_("All"), self.workingLanguage, self.outputLanguage, CURRENT_MODULE_ABS_PATH)
            
        else:
            combinedProductsName = ""
            for product in self.productTypes:
                combinedProductsName = combinedProductsName + str(product) + "_"
            
            formattedProductName = combinedProductsName[ :-1 ] #remove trailing _ character.    
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
        
        folder =   statsPaths.STATSGRAPHS + _("others/gnuplot/%.50s/") %( entityName )     
        
        translatedStatsTypes = [ LanguageTools.translateTerm(statsType, self.workingLanguage, self.outputLanguage, CURRENT_MODULE_ABS_PATH)\
                                 for statsType in self.statsTypes ] 
        
        fileName = folder + _("%s_%s_%s_%s_%shours_on_%s_for_%s_products.png") %(  self.fileType, entityName, date, translatedStatsTypes,\
                                                                                   self.timespan, self.machines, formattedProductName )
        
        fileName = fileName.replace( '[', '').replace(']', '').replace(" ", "").replace( "'","" )     
        
        
        if not os.path.isdir( folder ):
            os.makedirs( folder, 0777 )  
            os.chmod(folder, 0777)
       
        if len( os.path.basename(fileName) ) > (os.statvfs( folder )[statvfs.F_NAMEMAX]): # length of file too long 
            maximumLength = (os.statvfs( folder )[statvfs.F_NAMEMAX]) - ( 30 + len(date) + len( str(translatedStatsTypes)) + len( str( self.timespan ) ) )
            maxIndyLength = maximumLength / 3 
            #reduce entityname, machine names and products wich are the only parts wich can cause us to bust the maximum filename size.
            fileName = folder + ( "%s_%." + str( maxIndyLength )+ _("s_%s_%s_%shours_on_%.") + str( maxIndyLength ) + \
                                 _("s_for_%.") + str( maxIndyLength ) + _("s_products.png") )  \
                                 %(  self.fileType, entityName, date, translatedStatsTypes, self.timespan,\
                                     self.machines, formattedProductName ) 
            
        
        return fileName 
    
    
        
    def getXTics( self ):
        """
           
           @summary : This method builds all the xtics used to seperate data on the x axis.
            
                      Xtics values will are used in the plot method so they will be drawn on 
                      the graphic. 
           
           @note:     All xtics will be devided hourly. This means a new xtic everytime 
                      another hour has passed since the starting point.  
            
            
        """
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )
        #print "get x tics"
        if self.logger != None :
            self.logger.debug( _("Call to getXtics received") )
        
        nbBuckets = ( len( self.stats[0].statsCollection.timeSeperators ) )
        xtics = ''
        startTime = StatsDateLib.getSecondsSinceEpoch( self.stats[0].statsCollection.timeSeperators[0] )
        
        if nbBuckets != 0 :
            
            for i in range(0, nbBuckets ):
                 
                   
                if ( (  StatsDateLib.getSecondsSinceEpoch(self.stats[0].statsCollection.timeSeperators[i]) - ( startTime  ) ) %(60*60)  == 0.0 ): 
                    
                    hour = StatsDateLib.getHoursFromIso( self.stats[0].statsCollection.timeSeperators[i] )
                    
                    xtics += '"%s" %i, '%(  hour , StatsDateLib.getSecondsSinceEpoch(self.stats[0].statsCollection.timeSeperators[i] ) )

        
        #print nbBuckets
        #print "len xtics %s" %len(xtics) 
        return xtics[:-2]
         
        
        
    def getPairs( self, clientCount , statType, typeCount  ):
        """
           
           @summary : This method is used to create the data couples used to draw the graphic.
                      Couples are a combination of the data previously gathered and the time
                      at wich data was produced.  
           
           @note:    One point per pair will generally be drawn on the graphic but
                     certain graph types might combine a few pairs before drawing only 
                     one point for the entire combination.
                  
           @warning: If illegal statype is found program will be terminated here.       
           
           @todo: Using dictionaries instead of arrays might speed thinga up a bit.
            
        """
        
        if self.logger != None: 
            _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
            self.logger.debug( _("Call to getPairs received.") )
        
        k = 0 
        pairs = []
        total = 0
        self.nbFiles[clientCount]  = 0
        self.nbErrors[clientCount] = 0
        self.nbFilesOverMaxLatency[clientCount] = 0
        nbEntries = len( self.stats[clientCount].statsCollection.timeSeperators )-1 
        
        translatedStatType = LanguageTools.translateTerm(statType, self.workingLanguage, "en", CURRENT_MODULE_ABS_PATH)
        
        if nbEntries !=0:
            
            total = 0
                            
            self.minimums[clientCount][typeCount] = 100000000000000000000 #huge integer
            self.maximums[clientCount][typeCount] = None
            self.filesWhereMaxOccured[clientCount][typeCount] =  "" 
            self.timeOfMax[clientCount][typeCount] = ""
            
            for k in range( 0, nbEntries ):
                
                try :
                    
                    if len( self.stats[clientCount].statsCollection.fileEntries[k].means ) >=1 :
                            
                        #special manipulation for each type                    
                        if translatedStatType == "latency":
                            self.nbFilesOverMaxLatency[clientCount] = self.nbFilesOverMaxLatency[ clientCount ] + self.stats[clientCount].statsCollection.fileEntries[k].filesOverMaxLatency    
                    
                        elif translatedStatType == "bytecount":
                            self.totalNumberOfBytes[clientCount] =  self.totalNumberOfBytes[clientCount] +    self.stats[clientCount].statsCollection.fileEntries[k].totals[translatedStatType]
                        
                        
                        elif translatedStatType == "errors":
                                                    #calculate total number of errors
                            self.nbErrors[clientCount] = self.nbErrors[clientCount] + self.stats[clientCount].statsCollection.fileEntries[k].totals[translatedStatType] 
                        
                          
                        #add to pairs    
                        if translatedStatType == "errors" or translatedStatType == "bytecount": #both use totals     
                            pairs.append( [StatsDateLib.getSecondsSinceEpoch(self.stats[clientCount].statsCollection.timeSeperators[k]), self.stats[clientCount].statsCollection.fileEntries[k].totals[translatedStatType]] )
                                               
                            #print    StatsDateLib.getSecondsSinceEpoch(self.stats[clientCount].statsCollection.timeSeperators[k]), self.stats[clientCount].statsCollection.fileEntries[k].totals[translatedStatType]                        
                        
                        elif translatedStatType == "filecount":
                            pairs.append( [StatsDateLib.getSecondsSinceEpoch(self.stats[clientCount].statsCollection.timeSeperators[k]), self.stats[clientCount].statsCollection.fileEntries[k].nbFiles ]  )
                        
                        else:#latency uses means
                            
                            pairs.append( [ StatsDateLib.getSecondsSinceEpoch(self.stats[clientCount].statsCollection.timeSeperators[k]), self.stats[clientCount].statsCollection.fileEntries[k].means[translatedStatType]] )
                            
                            #print self.stats[clientCount].statsCollection.timeSeperators[k], self.stats[clientCount].statsCollection.fileEntries[k].means[translatedStatType]
                        
                        if translatedStatType == "filecount":
                            
                            if self.stats[clientCount].statsCollection.fileEntries[k].nbFiles > self.maximums[clientCount][typeCount] :
                                self.maximums[clientCount][typeCount] =  self.stats[clientCount].statsCollection.fileEntries[k].nbFiles
                                self.timeOfMax[clientCount][typeCount] = self.stats[clientCount].statsCollection.fileEntries[k].startTime
                            
                            elif self.stats[clientCount].statsCollection.fileEntries[k].nbFiles < self.minimums[clientCount][typeCount] :                           
                                self.minimums[clientCount][typeCount] = self.stats[clientCount].statsCollection.fileEntries[k].nbFiles
                        
                        
                        elif( self.stats[clientCount].statsCollection.fileEntries[k].maximums[translatedStatType]  > self.maximums[clientCount][typeCount] ) :
                            
                            self.maximums[clientCount][typeCount] =  self.stats[clientCount].statsCollection.fileEntries[k].maximums[translatedStatType]
                            
                            self.timeOfMax[clientCount][typeCount] = self.stats[clientCount].statsCollection.fileEntries[k].timesWhereMaxOccured[translatedStatType]
                            
                            self.filesWhereMaxOccured[clientCount][typeCount] = self.stats[clientCount].statsCollection.fileEntries[k].filesWhereMaxOccured[translatedStatType]
                        
                            
                        elif self.stats[clientCount].statsCollection.fileEntries[k].minimums[translatedStatType] < self.minimums[clientCount][typeCount] :      
                            
                            if not ( translatedStatType == "bytecount" and  self.stats[clientCount].statsCollection.fileEntries[k].minimums[translatedStatType] == 0 ):
                                self.minimums[clientCount][typeCount] = self.stats[clientCount].statsCollection.fileEntries[k].minimums[translatedStatType]
                                                    
                        self.nbFiles[clientCount]  = self.nbFiles[clientCount]  + self.stats[clientCount].statsCollection.fileEntries[k].nbFiles   
                   
                              
                    else:
                   
                        pairs.append( [ StatsDateLib.getSecondsSinceEpoch(self.stats[clientCount].statsCollection.timeSeperators[k]), 0.0 ] )
                
                
                except KeyError, instance:
                    #print instance
                    _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )
                    self.logger.error( _("Error in getPairs.") )
                    self.logger.error( _("The %s stat type was not found in previously collected data.") %statType )    
                    pairs.append( [ StatsDateLib.getSecondsSinceEpoch(self.stats[clientCount].statsCollection.timeSeperators[k]), 0.0 ] )
                    pass    
                
                
                total = total + pairs[k][1]            
            
            self.means[clientCount][typeCount] = (total / (k+1) ) 
            
            
            if self.nbFiles[clientCount] != 0 :
                self.ratioOverLatency[clientCount]  = float( float(self.nbFilesOverMaxLatency[clientCount]) / float(self.nbFiles[clientCount]) ) *100.0
            
            if self.minimums[clientCount][typeCount] == 100000000000000000000 :
                self.minimums[clientCount][typeCount] = None
            
            #print pairs 
                       
            return pairs    



    def getMaxPairValue( self, pairs ):
        """
            @summary : Returns the maximum value of a list of pairs. 
        
        """
        
        maximum = None
        
        if len( pairs) != 0 :
            
            for pair in pairs:
                if pair[1] > maximum:    
                    maximum = pair[1] 
                    
                    
        return  maximum 
        
        
        
    def getMinPairValue( self, pairs ):
        """
            @summary : Returns the maximum value of a list of pairs. 
        """     
            
        minimum = None 
        
        if len( pairs ) != 0 :
            minimum = pairs[0][1]
            for pair in pairs:
                if pair[1] < minimum:    
                    minimum = pair[1] 
                    
                    
        return  minimum         
    
    
            
    def buildTitle( self, clientIndex, statType, typeCount, pairs ):
        """
            @summary : This method is used to build the title we'll print on the graphic.
                       
                       Title is built with the current time and the name of the client where
                       we collected the data. Also contains the mean and absolute min and max 
                       found in the data used to build the graphic.          
               
        """  
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )
        
        maximum = self.getMaxPairValue( pairs )
               
        minimum = self.getMinPairValue( pairs )
        
        if maximum != None :
            if statType == _("latency"):
                maximum = "%.2f" %maximum
            else:
                maximum = int(maximum)
            
        if minimum != None :
            if statType == _("latency"):
                minimum = "%.2f" %minimum
            else:
                minimum = int(minimum)
                
        if statType == _("latency"):
            _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
            explanation = _("With values rounded for every minutes.")
        else:
            _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
            explanation = _("With the total value of every minutes.")
                        
        
        statType = LanguageTools.translateTerm(statType, self.workingLanguage, self.outputLanguage, CURRENT_MODULE_ABS_PATH)                
        statType = statType[0].upper() + statType[1:]             
              
        if self.groupName == "":
            entityName = self.clientNames[clientIndex]
        else:          
            entityName = self.groupName
        
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )    
        title =  _("%s for %s for a span of %s hours ending at %s")\
                 %( statType, entityName, self.timespan, self.currentTime) + "\\n%s\\n\\n" %explanation +_("MAX: ") + str(maximum) + " " +\
                    _("MEAN: ") + "%3.2f"%(self.means[clientIndex][typeCount]) + " " + _("MIN: ") +str(minimum)     
        
        return title
        
    
    
    def createCopy( self, copyToArchive = True , copyToColumbo = True ):
        """
            @summary : Creates a copy of the created image file so that it
                       easily be used in px's columbo or other daily image program. 
            
            @summary : If copies are to be needed for graphcis other than daily graphs, 
                       please modify this method accordingly!
            
        """
        
        statsPaths = StatsPaths()
        statsPaths.setPaths(self.outputLanguage)
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
        
        src = self.imageName
        
        if self.groupName != "":            
            
            clientName = self.groupName 
                
        else:   
                
            clientName = ""
                   
            if len( self.clientNames ) == 0:
                clientName = self.clientNames[0]
            else:
                for name in self.clientNames :
                    clientName = clientName + name  
                    if name != self.clientNames[ len(self.clientNames) -1 ] :
                        clientName = clientName + "-" 
        
        
        StatsDateLib.setLanguage( self.outputLanguage ) # Makes sure month is in the right language.
        year, month, day = StatsDateLib.getYearMonthDayInStrfTime( StatsDateLib.getSecondsSinceEpoch( self.currentTime ) - 60 ) # -60 means that a graphic ending at midnight
        StatsDateLib.setLanguage( self.workingLanguage )# Sets language back to working language.                               # would be named after the rpevious day.
            
                                        
        if copyToArchive == True : 
            destination = statsPaths.STATSGRAPHSARCHIVES + _("daily/%s/%s/") %( self.fileType, clientName ) + str(year) + "/" + str(month) + "/" + str(day) + ".png"
                        
            if not os.path.isdir( os.path.dirname( destination ) ):
                os.makedirs(  os.path.dirname( destination ), 0777 )   
                dirname = os.path.dirname( destination )                                                  
                
                while( dirname != statsPaths.STATSGRAPHSARCHIVES[:-1] ):#[:-1] removes the last / character 
                    
                    try:
                        os.chmod( dirname, 0777 )
                    except:
                        pass
                    
                    dirname = os.path.dirname(dirname)
                    
                            
            shutil.copy( src, destination ) 
            
            try:
                os.chmod( destination, 0777 )
            except:
                pass
            #print "cp %s %s  "  %( src, destination )
        
        
        
        if copyToColumbo == True : 
            destination = statsPaths.STATSGRAPHS + _("webGraphics/columbo/%s_%s.png") %(clientName,self.outputLanguage)
            if not os.path.isdir( os.path.dirname( destination ) ):
                os.makedirs(  os.path.dirname( destination ), 0777 )                                                      
                os.chmod( os.path.dirname( destination ), 0777 )
            
            shutil.copy( src, destination ) 
            try:
                os.chmod( destination, 0777 )
            except:
                pass
            #print "cp %s %s  "  %( src, destination )



       
    def plot( self, createCopy = False  ):
        """
            @summary : To be used to plot gnuplot graphics. Settings used are
                       slighly modified but mostly based on sundew's Plotter.py's    
                       plot function. 
            
        """
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage ) 
        
        if self.logger != None:
            self.logger.debug( _("Call to plot received") )
        
        #Set general settings for graphs 
        color = 1
        nbGraphs = 0
         
        totalSize  = ( 0.40 * len( self.stats )  * len( self.statsTypes ) )
        #totalHeight = ( 342 * len( self.stats )  * len( self.statsTypes ) )
        
        self.graph( 'set terminal png size 1280,768 xffffff x000000 x404040 \
                      xff0000 x4169e1 x228b22 xa020f0 \
                      xadd8e6 x0000ff xdda0dd x9500d3' )
 
        self.graph( 'set size 1.0, %2.1f' % ( totalSize ) )
        
        self.graph( 'set linestyle 4 ')
        
        self.graph.xlabel( _('time (hours)') ) #, offset = ( "0.0"," -2.5" )
        
        self.graph( 'set grid')
        self.graph( 'set format y "%10.0f"' )
        self.graph( 'set xtics (%s)' % self.xtics)
        #self.graph( "set xtics rotate" )
        
        if self.type == 'lines':
            self.graph( 'set data style lines' )  
        elif self.type == 'impulses':
            self.graph( 'set data style impulses' )  
        elif self.type == 'boxes':
            self.graph( 'set data style boxes' )  
        elif self.type == 'linespoints':
            self.graph( 'set data style linespoints' )  
            
        
        #self.graph( 'set terminal png size 800,600' )
       
        self.imageName = self.buildImageName()

        #self.graph( "set autoscale" )
        self.graph( 'set output "%s"' % (  self.imageName ) )
        self.graph( 'set multiplot' ) 
        
        
        for clientIndex in range( len( self.stats ) ) :            
                       
            for statsTypeIndex in range ( len ( self.statsTypes ) ):
                
                pairs        = self.getPairs( clientCount = clientIndex , statType= self.statsTypes[statsTypeIndex],\
                                             typeCount = statsTypeIndex )
                maxPairValue = self.getMaxPairValue( pairs )
                self.maxLatency = self.stats[clientIndex].statsCollection.maxLatency
                
                if self.statsTypes[statsTypeIndex] == _("errors") :
                    color =4 #purple                    
                    self.addErrorsLabelsToGraph(  clientIndex , statsTypeIndex, nbGraphs, maxPairValue )
                
                elif self.statsTypes[statsTypeIndex] == _("latency") :
                    color =1 #red                    
                    self.addLatencyLabelsToGraph(  clientIndex , statsTypeIndex, nbGraphs,  maxPairValue )
                
                elif self.statsTypes[statsTypeIndex] == _("bytecount") :
                    color =2 #blue 
                    self.addBytesLabelsToGraph(  clientIndex , statsTypeIndex, nbGraphs,  maxPairValue )
                
                elif self.statsTypes[statsTypeIndex] == _("filecount") :
                    color =3 #green
                    self.addFilecountLabelsToGraph(clientIndex, statsTypeIndex, nbGraphs, maxPairValue)
                     
                self.graph.title( "%s" %self.buildTitle( clientIndex, self.statsTypes[statsTypeIndex] , statsTypeIndex, pairs) )
                
                self.graph.plot( Gnuplot.Data( pairs , with="%s %s 1" % ( self.type, color) ) )
                
                nbGraphs = nbGraphs + 1 
        
                
        try:
            #print self.imageName
            os.chmod( self.imageName, 0777 )            
        except:
            pass
        if createCopy :
            del self.graph
            self.createCopy( )     
         
         
         
    def getFormatedProductTypesForLabel(self):
        """
            @summary : Returns the product type in a format that can be displayed
                       on of of the graphcis labels.
                       
            @note    : If Productype is * or _("All") it will be translated.
            
            @return : the product type in a format that can be displayed
                      on of of the graphcis labels.
                      
        """
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.workingLanguage )
        formattedProductType = ""
                
        if self.productTypes[0] == _("All") or self.productTypes[0] == "*":
            formattedProductType = LanguageTools.translateTerm(_("All"), self.workingLanguage, self.outputLanguage, CURRENT_MODULE_ABS_PATH)
        else:
            formattedProductType = self.productTypes[0]
        
        formattedProductType = "%-25s" %( (str)( formattedProductType  ) ).replace('[','' ).replace( ']', '' ).replace("'","")
        
        return formattedProductType
                
            
            
    def addLatencyLabelsToGraph( self, clientIndex, statsTypeIndex, nbGraphs, maxPairValue ):
        """
            @summary : Used to set proper labels for a graph relating to latencies. 
             
        """            
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
        
        if self.maximums[clientIndex][statsTypeIndex] != None and self.maximums[clientIndex][statsTypeIndex] !=0 :
            
            timeOfMax = self.timeOfMax[clientIndex][statsTypeIndex] 
            
            if maxPairValue < 5 :
                self.graph( 'set format y "%7.2f"' )
            else:
                self.graph( 'set format y "%7.0f"' )
            
            maximum = self.maximums[clientIndex][statsTypeIndex]
        
        else:
            timeOfMax = ""
            maximum = ""       
            
            
        if self.groupName == "" :
            entityType = self.sourlient
            if len( self.stats ) ==1:
                entityName = str(self.clientNames).replace("[","").replace("]","").replace("'","")  
            else:
                entityName = self.clientNames[clientIndex]        
        else:
            entityType = "Group"
            entityName = self.groupName
                        
        
        formatedProductTypes =  self.getFormatedProductTypesForLabel()
                
        self.graph( 'set size .545, .37' )
        
        self.graph( 'set origin 0, %3.2f' %( ((nbGraphs)*.40)  ) )

        self.graph.ylabel( _('latency (seconds)') )
        
        self.graph( 'set label ' + _( '"%s : %s"' )%( entityType, entityName) + ' at screen .545, screen %3.2f' % ((.26+(nbGraphs) *.40)  ))
        
        self.graph( 'set label ' + _( '"Machines : %s"' )%(self.machines) + ' at screen .545, screen %3.2f' % ( (.24+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label ' + _( '"Product type(s) : %s"' )%(formatedProductTypes) + ' at screen .545, screen %3.2f' % ( (.22+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label ' + _( '"Absolute max. lat. : %s seconds"' )%(maximum) + ' at screen .545, screen %3.2f' % (  (.20+(nbGraphs) *.40) ) )
        
        self.graph( 'set label ' + _( '"Time of max. lat. : %s"' )%(timeOfMax) +  ' at screen .545, screen %3.2f' % ( ( (.18+(nbGraphs) *.40)  )))
        
        if len ( self.filesWhereMaxOccured[clientIndex][statsTypeIndex] ) <= 50 :
            self.graph( 'set label ' + _( '"File with max. lat. :%s"' )%(self.filesWhereMaxOccured[clientIndex][statsTypeIndex]) + ' at screen .545, screen %3.2f' % (  (.16+(nbGraphs) *.40) ))     
        
        else:
            self.graph( 'set label ' + _( '"File with max. lat. :"' ) + ' at screen .545, screen %3.2f' % ( (.16+(nbGraphs) *.40) ))  
            
            self.graph( 'set label "%s" at screen .545, screen %3.2f' % ( self.filesWhereMaxOccured[clientIndex][statsTypeIndex], (.14+(nbGraphs) *.40 ) ))          
        
        self.graph( 'set label ' + _( '"# of files : %s "' )% self.nbFiles[clientIndex] + ' at screen .545, screen %3.2f' % ( (.12+(nbGraphs) *.40) ) )
        
        self.graph( 'set label ' +  _( '"# of files over %s seconds: %s "' )%(self.maxLatency, self.nbFilesOverMaxLatency[clientIndex]) + ' at screen .545, screen %3.2f' % (  ( .10+(nbGraphs) *.40 ) ) )
        
        self.graph( 'set label '  + _( '"%% of files over %s seconds: %3.2f %%"' )%(self.maxLatency, self.ratioOverLatency[clientIndex] ) + ' at screen .545, screen %3.2f' % (  ( .08 + (nbGraphs) *.40 ) ) )
        
                
    
            
    def addBytesLabelsToGraph( self, clientIndex, statsTypeIndex, nbGraphs, maxPairValue ):
        """
            @summary : Used to set proper labels for a graph relating to bytes. 
             
        """            
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )
        
        if self.maximums[clientIndex][statsTypeIndex] != None and self.maximums[clientIndex][statsTypeIndex] != 0 :
            
            timeOfMax = self.timeOfMax[clientIndex][statsTypeIndex] 
            
            if maxPairValue < 5 :
                self.graph( 'set format y "%7.2f"' )
            else:
                self.graph( 'set format y "%7.0f"' )    
                
            maximum = self.maximums[clientIndex][statsTypeIndex]
        
        else:
            timeOfMax = ""
            maximum = ""
       
        
        if self.groupName == "" :
            entityType = self.sourlient
                        
            if self.groupName == "" :
                entityType = self.sourlient
                if len( self.stats ) ==1:
                    entityName = str(self.clientNames).replace("[","").replace("]","").replace("'","")  
                else:
                    entityName = self.clientNames[clientIndex]   
        else:
            entityType = "Group"
            entityName = self.groupName
        
       
        if self.totalNumberOfBytes[clientIndex] < 1000:#less than a k
            totalNumberOfBytes = _("%s Bytes") %int( self.totalNumberOfBytes[clientIndex] )
            
        elif self.totalNumberOfBytes[clientIndex] < 1000000:#less than a meg 
            totalNumberOfBytes =  _("%.2f kiloBytes")  %( self.totalNumberOfBytes[clientIndex]/1000.0 )
        
        elif self.totalNumberOfBytes[clientIndex] < 1000000000:#less than a gig      
            totalNumberOfBytes =  _("%.2f MegaBytes")  %( self.totalNumberOfBytes[clientIndex]/1000000.0 )
        else:#larger than a gig
            totalNumberOfBytes =  _("%.2f GigaBytes")  %( self.totalNumberOfBytes[clientIndex]/1000000000.0 )
         
        formatedProductTypes =  self.getFormatedProductTypesForLabel()
            
        self.graph( 'set size .545, .37' )
        
        self.graph( 'set origin 0, %3.2f' %( ((nbGraphs)*.40)  ))
        
        self.graph.ylabel( _('Bytes/Minute') )
        
        self.graph( 'set label "%s : %s" at screen .545, screen %3.2f' % ( entityType, entityName,(.26+(nbGraphs) *.40)  ))
        
        self.graph( 'set label ' + _('"Machines : %s"')%self.machines + ' at screen .545, screen %3.2f' % ( (.24+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label '+ _('"Product type(s) : %s"')%formatedProductTypes + ' at screen .545, screen %3.2f' % ((.22+(nbGraphs) *.40)  ) )
        
        
        if len ( self.filesWhereMaxOccured[clientIndex][statsTypeIndex] ) <= 65 :            
            self.graph( 'set label ' + _('"Largest file : %s"')%self.filesWhereMaxOccured[clientIndex][statsTypeIndex] + ' at screen .545, screen %3.2f' % (  (.20+(nbGraphs) *.40) ))
            x = .20
        else:
            self.graph( 'set label ' + _('"Largest file : "') + ' at screen .545, screen %3.2f' % ( ( .20 + ( nbGraphs ) *.40) ) )
            
            self.graph( 'set label "%s" at screen .545, screen %3.2f' % ( self.filesWhereMaxOccured[clientIndex][statsTypeIndex], (.18+(nbGraphs) *.40) ))
            x = .18
                    
        self.graph( 'set label ' + _('"Size of largest file : %s Bytes"')%maximum + ' at screen .545, screen %3.2f' % (  (x -.02+(nbGraphs) *.40) ) )       
                
        self.graph( 'set label ' + _('"Time of largest file : %s"')%timeOfMax + ' at screen .545, screen %3.2f' % ( (  (x -.04+(nbGraphs) *.40)  )))     
        
        self.graph( 'set label ' + _('"# of files : %s "')%self.nbFiles[clientIndex] + ' at screen .545, screen %3.2f' % (  ( x-.06+(nbGraphs) *.40) ) )
    
        self.graph( 'set label ' + _('"# of Bytes: %s "')%totalNumberOfBytes + ' at screen .545, screen %s' % (  ( x -.08 +(nbGraphs) *.40 ) ) )
                

    
    
    def addErrorsLabelsToGraph( self, clientIndex, statsTypeIndex, nbGraphs, maxPairValue ):
        """
            @summary : Used to set proper labels for a graph relating to bytes. 
             
        """   
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )         
        
        if self.maximums[clientIndex][statsTypeIndex] !=None and self.maximums[clientIndex][statsTypeIndex] != 0 :
            
            timeOfMax =  self.timeOfMax[clientIndex][statsTypeIndex]
            timeOfMax =  StatsDateLib.getIsoWithRoundedSeconds( timeOfMax )
            
            if maxPairValue < 5 :
                self.graph( 'set format y "%7.2f"' )
            else:
                self.graph( 'set format y "%7.0f"' )
        
            maximum = self.maximums[clientIndex][statsTypeIndex]
        
        else:
            timeOfMax = ""
            maximum = ""
               
        if self.groupName == "" :
            entityType = self.sourlient
            
            if self.groupName == "" :
                entityType = self.sourlient
                if len( self.stats ) ==1:
                    entityName = str(self.clientNames).replace("[","").replace("]","").replace("'","")  
                else:
                    entityName = self.clientNames[clientIndex]   
                    
        else:
            entityType = "Group"
            entityName = self.groupName    
        
        formatedProductTypes =  self.getFormatedProductTypesForLabel()
        
        self.graph( 'set size .545, .37' )
        
        self.graph( 'set origin 0, %3.2f' %( ((nbGraphs)*.40)  ))
        
        self.graph.ylabel( _('Errors/Minute') )
        
        self.graph( 'set label "%s : %s" at screen .545, screen %3.2f' % ( entityType, entityName,(.26+(nbGraphs) *.40)  ))
        
        self.graph( 'set label ' + _('"Machines : %s"')%self.machines + ' at screen .545, screen %3.2f' % ((.24+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label ' + _('"Product type(s) : %s"')%formatedProductTypes + ' at screen .545, screen %3.2f' % ( (.22+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label ' + _('"Max error/%s : %s"') %( self.entryType, maximum) + ' at screen .545, screen %3.2f' % ( (.20+(nbGraphs) *.40) ))        
        
        self.graph( 'set label ' + _('"Time of max. : %s"')%timeOfMax + ' at screen .545, screen %3.2f' % ( (  (.18+(nbGraphs) *.40)  )))
        
        self.graph( 'set label ' + _('"# of errors : %.f"')%self.nbErrors[clientIndex] + ' at screen .545, screen %3.2f' % (  (.16+(nbGraphs) *.40) ) )
      
      
                
    def addFilecountLabelsToGraph( self, clientIndex, statsTypeIndex, nbGraphs, maxPairValue ):
        """
            @summary: Used to set proper labels for a graph relating to bytes. 
             
        """   
        
        _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.outputLanguage )         
        
        if self.maximums[clientIndex][statsTypeIndex] !=None and self.maximums[clientIndex][statsTypeIndex] != 0 :
            
            timeOfMax =  self.timeOfMax[clientIndex][statsTypeIndex]
            timeOfMax =  StatsDateLib.getIsoWithRoundedSeconds( timeOfMax )
            
            if maxPairValue < 5 :
                self.graph( 'set format y "%7.2f"' )
            else:
                self.graph( 'set format y "%7.0f"' )
        
            maximum = self.maximums[clientIndex][statsTypeIndex]
        
        else:
            timeOfMax = ""
            maximum = ""
               
        if self.groupName == "" :
            entityType = self.sourlient
            
            if self.groupName == "" :
                entityType = self.sourlient
                if len( self.stats ) ==1:
                    entityName = str(self.clientNames).replace("[","").replace("]","").replace("'","")  
                else:
                    entityName = self.clientNames[clientIndex]   
                    
        else:
            entityType = "Group"
            entityName = self.groupName    
        
        formatedProductTypes =  self.getFormatedProductTypesForLabel()
        
        self.graph( 'set size .545, .37' )
        
        self.graph( 'set origin 0, %3.2f' %( ((nbGraphs)*.40)  ))
        
        self.graph.ylabel( _('Files/Minute') )
        
        self.graph( 'set label "%s : %s" at screen .545, screen %3.2f' % ( entityType, entityName,(.26+(nbGraphs) *.40)  ))
        
        self.graph( 'set label '+_('"Machines : %s"')%self.machines + ' at screen .545, screen %3.2f' % ( (.24+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label '+_('"Product type(s) : %s"')%formatedProductTypes +' at screen .545, screen %3.2f' % ( (.22+(nbGraphs) *.40)  ) )
        
        self.graph( 'set label '+_('"Max files/%s : %s"')%(self.entryType, maximum) +' at screen .545, screen %3.2f' % (  (.20+(nbGraphs) *.40) ))        
        
        self.graph( 'set label '+_('"Time of max. : %s"')%timeOfMax +' at screen .545, screen %3.2f' % ( (  (.18+(nbGraphs) *.40)  )))
        
        self.graph( 'set label '+_('"# of files : %s"')%self.nbFiles[clientIndex] + ' at screen .545, screen %3.2f' % (   (.16+(nbGraphs) *.40) ) )                
            




    
    
    
