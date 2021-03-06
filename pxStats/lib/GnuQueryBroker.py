#! /usr/bin/env python
"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.


##############################################################################
##
##
## @Name   : GnuQueryBroker.py 
##
##
## @author :  Nicholas Lemay
##
## @since  : 2007-06-28, last updated on 2008-04-02
##
##
## @summary : This class implements the GraphicsQueryBrokerInterface
##            and allows to execute queries towards the gnuplot graphics
##            creator from a web interface.     
##
##            
##
## @requires: GraphicsQueryBrokerInterface, wich it implements. 
##            
##
##############################################################################
"""


import cgi, os, sys
import cgitb; cgitb.enable()
sys.path.insert(1,  os.path.dirname( os.path.abspath(__file__) ) + '/../../')


from pxStats.lib.StatsDateLib import StatsDateLib
from pxStats.lib.GeneralStatsLibraryMethods import GeneralStatsLibraryMethods
from pxStats.lib.StatsConfigParameters import StatsConfigParameters
from pxStats.lib.GraphicsQueryBrokerInterface import GraphicsQueryBrokerInterface
from pxStats.lib.GnuGraphicProducer import GnuGraphicProducer
from pxStats.lib.LanguageTools import LanguageTools

LOCAL_MACHINE = os.uname()[1]

CURRENT_MODULE_ABS_PATH =  os.path.abspath(__file__).replace( ".pyc", ".py" )


class GnuQueryBroker(GraphicsQueryBrokerInterface):
    """    
        @summary: This class implements the GraphicsQueryBrokerInterface
                  and allows to execute queries towards the gnuplot graphics
                  creator from a web interface.          
    
    """    
    
    def __init__(self,  querierLanguage, queryParameters = None, replyParameters = None,\
                 graphicProducer = None ):
        """
            @summary: GnuQueryBroker constructor.
            
            @param querierLanguage : Language spoken by the qerier at the time of the query.
            
            @param queryParameters: _QueryParameters instance wich 
                                    contains the query parameters. 
            
            @param replyParameters :
            
            @param graphicProducer :  
            
           
            
        """
        
        self.queryParameters = queryParameters
        self.graphicProducer = graphicProducer
        self.replyParameters = replyParameters
        self.querierLanguage = querierLanguage 
        
        if self.querierLanguage not in LanguageTools.getSupportedLanguages():
            raise Exception( "Error. Unsupported language detected in GnuQueryBroker. %s is not a supported language."%( self.querierLanguage ) )
        else:#language is supposed to be supported 
            global _
            _ = self.getTranslatorForModule( CURRENT_MODULE_ABS_PATH, self.querierLanguage )
    
    
      
    class _QueryParameters(object):
       
        def __init__( self, fileType, sourLients, groupName, machines, combine, endTime,\
                      products, statsTypes,  span, language ):
            """
                @summary : _QueryParameters parameters class constructor.                
                
                @param fileType: rx or tx                
                @param sourLients: list of sour or clients for wich to produce graphic(s).                
                @param groupName: Group name tag to give to a group of clients.      
                @param machines : List of machine on wich the data resides.           
                @param combine: Whether or not( true or false ) to combine the sourlients.                
                @param endTime: time of query of the graphics                
                @param products: List of specific products for wich to plot graphics.                
                @param statsTypes : List of stats types for wich to create the graphics.
                @param span: span in hoursof the graphic(s).          
                @param : Language in which the querier is expecting the graphic(s) to be.  
            
            """
            
            self.fileType   = fileType
            self.sourLients = sourLients
            self.groupName  = groupName
            self.machines   = machines
            self.combine    = combine
            self.endTime    = endTime
            self.products   = products
            self.statsTypes = statsTypes
            self.span       = span
            self.language   = language
        
            
    class _ReplyParameters( _QueryParameters ):   
        
        def __init__( self, querier, plotter, image, fileType, sourLients, groupName, machines, combine,\
                      endTime,  products, statsTypes,  span, error, language ):    
            """
                @summary : _ReplyParameters parameters class constructor.                
                
                @param querier: Path to the program that sent out the query.
                @param plotter: Type of plotter that was selected.
                @param image:   Path to the image that was created. 
                @param fileType: rx or tx                
                @param sourLients: list of sour or clients for wich to produce graphic(s).                
                @param groupName: Group name tag to give to a group of clients.      
                @param machines : List of machine on wich the data resides.           
                @param combine: Whether or not( true or false ) to combine the sourlients.                
                @param endTime: time of query of the graphics                
                @param products: List of specific products for wich to plot graphics.                
                @param statsTypes : List of stats types for wich to create the graphics.
                @param span: span in hoursof the graphic(s). 
                @param error  : error that has occured during query.
                @param language : Language in which the graphic whould have been plotted.
                
            """           
            
            self.querier    = querier
            self.plotter    = plotter
            self.image      = image
            self.fileType   = fileType
            self.sourLients = sourLients
            self.groupName  = groupName
            self.machines   = machines
            self.combine    = combine
            self.endTime    = endTime
            self.products   = products
            self.statsTypes = statsTypes
            self.span       = span
            self.error      = error        
      
       
    def getParametersFromParser( self, parser ):
        """
            @summary : Uses the parser to gather the 
                       parameters from a call from the
                       command line.
        """  
        x =2 
        
    
    #----------------------------------- def translateStatsTypes( statsTypes ) :
        #------------------------------------------------------------------- """
            #------------------------------- @summary : Takes a list of statypes
#------------------------------------------------------------------------------ 
            #--------------------- @return : The list of translated stats types.
#------------------------------------------------------------------------------ 
        #------------------------------------------------------------------- """
#------------------------------------------------------------------------------ 
        #---------------------------------------------- translatedStatTypes = []
#------------------------------------------------------------------------------ 
        # statsTypesTranslations = { _("latency"):"latency", _("bytecount"):"bytecount", _("filecount"):"filecount", _("errors"):"errors" }
#------------------------------------------------------------------------------ 
        #--------------------------------- for i in range( len( statsTypes ) ) :
            # translatedStatTypes.append( statsTypesTranslations[ statsTypes[i] ] )
#------------------------------------------------------------------------------ 
        #-------------------------------------------- return translatedStatTypes
        
        
        
    def getParametersFromForm( self, form ):
        """
            @summary: Initialises the queryParameters
                      based on the form received as 
                      parameter.        
                     
           @note :   Absent parameters will be set to default values( [] or '' )
                     and will NOT raise exceptions. Use the searchForParameterErrors
                     function to search for errors           
                       
           
        """
        global _
        #print form
        
        image       = None  #No image was produced yet
        
        #Every param is received  in an array, use [0] to get first item, nothing for array.
        try:
            querier = form["querier"].replace("'", "").replace('"','')
        except:
            querier = ''
                
        try:
            plotter = form["plotter"].replace("'", "").replace('"','') 
        except:
            plotter = ''
             
        
        try:
            fileTypes = form["fileType"].replace("'", "").replace('"','')
        except:
            fileTypes = ''
        
        
        try:
            sourLients = form["sourLients"].split(',')
        except:
            sourLients = []
        
        
        try:
            groupName = form["groupName"].replace("'", "").replace('"','')
        except:
            groupName = ''

        try:
            machines = form["machines"].split(',')
        except:
            machines = []
        

        if groupName != '' and ( sourLients == [] or sourLients == [''] ) :
            configParameters = StatsConfigParameters( )
            configParameters.getAllParameters()
            
            if groupName in configParameters.groupParameters.groups:
                if configParameters.groupParameters.groupFileTypes[groupName] == fileTypes and configParameters.groupParameters.groupsMachines[groupName] == machines:
                    sourLients = configParameters.groupParameters.groupsMembers[groupName]
        
        try:
            combine = form["combineSourlients"].replace(",", "").replace('"','')
            
            if combine == 'false' or combine == 'False':
                combine = False
            elif combine == 'true' or combine == 'True':
                combine = True
            else:
                raise    
            
        except:
            combine = False
        
        
        
        try:
            endTime = form["endTime"].replace("'", "").replace('"','')
            hour      = endTime.split(" ")[1]
            splitDate = endTime.split(" ")[0].split( '-' )
            endTime = "%s" %( splitDate[2] + '-' + splitDate[1]  + '-' + splitDate[0]  + " " + hour )       
            
            if _("current") in str(form["fixedSpan"]).lower():
                start, endTime = StatsDateLib.getStartEndFromCurrentDay(endTime)
                
            elif _("previous") in str(form["fixedSpan"]).lower():    
                start, endTime = StatsDateLib.getStartEndFromPreviousDay( endTime )
                
        except:
            endTime = ''
        
        try:
            products = form["products"].split(',')
            if products == [""]:
                raise
        except:
            products = ["*"]
            
        try:    
            statsTypes = form["statsTypes"].split(',')
        except:
            statsTypes = []
       
        #statsTypes = translateStatsTypes( statsTypes )      
            
        try:
            span        = form["span"].replace("'", "").replace('"','')
            if str(span).replace( ' ', '' ) == '':
                raise 
            span = int(span)
                
        except:
            span = 24
        
        try:
            language = form["lang"].replace("'", "").replace('"','')
        
        except:
            language = ""
                
        sourLients = GeneralStatsLibraryMethods.filterClientsNamesUsingWilcardFilters( endTime, span, sourLients, machines, [fileTypes])    
            
        self.queryParameters = GnuQueryBroker._QueryParameters( fileTypes, sourLients, groupName, machines, combine, endTime,  products, statsTypes,  span, language )
        
        self.replyParameters = GnuQueryBroker._ReplyParameters( querier, plotter, image, fileTypes, sourLients, groupName, machines, combine, endTime, products, statsTypes,  
                                                                span, '', language )
        
        
        
    def getParameters( self, querier, form , parser ):
        """
            @summary : Get parameters from either a form or a parser. 
                       Both need to have parameter names wich are the 
                       same as the ones used in the _QueryParameters
                       class.  
        
        """        
        
        if form != None: 
            self.getParametersFromForm( form )
        elif parser != None :
            self.getParametersFromParser( parser )
    
    
    
    def searchForParameterErrors(self):
        """
            @summary : Validates parameters.
           
            @return  : Returns the first error 
                       found within the current
                       query parameters. 
        """
        
        global _ 
        
        error = ""
        
        try :
            
            if self.queryParameters.plotter != "gnuplot":
                error = _("Internal error. GnuQueryBroker was not called to plota gnuplot graphic.")
                raise
        
            for fileType in self.queryParameters.fileTypes :
                if fileType != "tx" and fileType != "rx":
                    error = _("Error. FileType needs to be either rx or tx.")
                    raise
            
            if self.queryParameters.sourLients == []:
                if self.queryParameters.groupName == "":
                    error = _("Error. At least one sourlient name needs to be specified.")
                else:
                    error = _("Error. When specifying a group name without any sourlients names, the group must be a pre-existing group.")
                        
            if self.queryParameters.machines == []:
                error = _("Error. At least one machine name needs to be specified.")
            
            if self.queryParameters.combine != 'true' and self.queryParameters.combine != 'false':
                error = _("Error. Combine sourlients option needs to be either true or false."  )
            
            if self.queryParameters.statsTypes == []:
                error = _("Error. At Leat one statsType needs to be specified.")
            
            try:
                int(self.queryParameters.span)
            except:
                error = _("Error. Span(in hours) value needs to be numeric.")          
    
            if self.queryParameters.language == "" :
                error = _("Error. No language was specified by the querier. Please speciffy a language. Ex : lang=fr")
            elif self.queryParameters.language not in LanguageTools.getSupportedLanguages() :
                error = _("Error. Unsupported language detected in GnuQueryBroker. %s is not a supported language.")%( self.queryParameters.language) 
    
        except:
            
            pass
        
        
        return error  


    
    def prepareQuery(self):
        """
            @summary:  Buildup the query  to be executed.
        """
        
        directory = GeneralStatsLibraryMethods.getPathToLogFiles( LOCAL_MACHINE, self.queryParameters.machines[0] )
        
        self.queryParameters.sourLients.reverse()
        
        self.graphicProducer = GnuGraphicProducer( directory = directory, fileType = self.queryParameters.fileType,\
                                                      clientNames = self.queryParameters.sourLients, \
                                                      groupName = self.queryParameters.groupName, \
                                                      timespan = int(self.queryParameters.span), currentTime = self.queryParameters.endTime,\
                                                      productTypes = self.queryParameters.products, logger= None, logging = False,\
                                                      machines = self.queryParameters.machines, workingLanguage = self.queryParameters.language,\
                                                      outputLanguage = self.queryParameters.language )
        

         
        #------------------------------- print """directory = %s, fileType = %s,
                 #-------------------------------------------- clientNames = %s,
                 #---------------------------------------------- groupName = %s,
                 #------------------------ timespan = int(%s), currentTime = %s,
                 #------------------------------- productTypes = %s, logger= %s,
                 #------------------------------------------------ machines = %s
        # """ %( directory, self.queryParameters.fileType, self.queryParameters.sourLients, self.queryParameters.groupName, self.queryParameters.span, self.queryParameters.endTime, self.queryParameters.products, None, self.queryParameters.machines )
#------------------------------------------------------------------------------ 
        
        
    def executeQuery(self):
        """
            @summary: Execute the built-up query on the needed plotter.
            
            @side-effect : Will set the name of the produced image in the reply parameters.
        
        """
        
        #print "sourlients : %s" %self.queryParameters.sourLients
        
        self.queryParameters.statsTypes.reverse()#reverse temporarily.
         
        imageName = self.graphicProducer.produceGraphicWithHourlyPickles( types = self.queryParameters.statsTypes , now = False, 
                                                              createCopy = False, combineClients = self.queryParameters.combine )
    
        self.queryParameters.statsTypes.reverse()#undo reverse.
    
        #-------------------------------------- print """ types = %s , now = %s,
             #----------------------------- createCopy = %s, combineClients = %s
#------------------------------------------------------------------------------ 
        # """%( self.queryParameters.statsTypes, False, False, self.queryParameters.combine  )
        
        
        
        self.replyParameters.image = imageName
    
    
    
    def getReplyToSendToquerier(self):
        """
            @summary : Builds the reply to send to the querier.
            
            @return: The reply.
        
        """
        
        params = self.replyParameters
                
        reformatedImageLocation = '../../pxStats' + params.image.split( 'pxStats' )[-1:][0]
                        
        reply = "images=%s;error=%s"%( reformatedImageLocation, params.error   )

         
        return reply
    
    
    
    
       