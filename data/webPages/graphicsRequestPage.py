#!/usr/bin/env python

print """Content-Type: text/html"""

"""
MetPX Copyright (C) 1604-1606  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.


##############################################################################
##
##
## @Name   : graphicsRequestPage.py 
##
##
## @author :  Nicholas Lemay
##
## @since  : 2007-06-28, last updated on  2007-07-16
##
##
## @summary : This is to be used to generate a dynamic web page where users 
##            are to be albe to fill out forms and get an appropriate graphic
##            based on the parameters filled within the forms.
##
##
## @requires: graphicsRequestBroker, wich handles all the requests coming 
##            from this page.
##
##
##############################################################################
"""

""" IMPORTS """

import os, time, sys
import cgi, cgitb; cgitb.enable()
sys.path.insert(1, sys.path[0] + '/../../../')

try:
    pxlib = os.path.normpath( os.environ['PXROOT'] ) + '/lib/'
except KeyError:
    pxlib = '/apps/px/lib/'
sys.path.append(pxlib)

from PXManager import *
from pxStats.lib.StatsPaths import StatsPaths
from pxStats.lib.StatsDateLib import StatsDateLib
from pxStats.lib.GeneralStatsLibraryMethods import GeneralStatsLibraryMethods
from pxStats.lib.StatsConfigParameters import StatsConfigParameters

"""
   Define constants to be used for filling out the different select boxes. 
"""

SUPPORTED_PLOTTERS = [ "gnuplot", "rrd" ]

SUPPORTED_FILETYPES = [ "rx","tx"]

RX_DATATYPES = { "gnuplot" : [ "bytecount", "errors","bytecout,errors"], "rrd" : [ "bytecount", "filecount","errors"] }

TX_DATATYPES ={ "gnuplot" : [ "bytecount", "errors", "latency", "bytecout,errors", "bytecout,latency", "errors,latency", "bytecout, errors, latency"] ,
                "rrd": [ "bytecount", "errors", "filecount", "latency", "filesOverMaxLatency"]}


FIXED_TIMESPANS = { "gnuplot" : [ "N/A"], "rrd" : [ "daily" , "weekly", "monthly", "yearly" ] }

FIXED_PARAMETERS = { "gnuplot" : [ "N/A" ], "rrd" : [ "fixedCurrent", "fixedPrevious" ] }

PRE_DETERMINED_SPANS = [ 'daily', 'monthly', 'weekly', 'yearly' ]

FIXED_SPANS = [ 'fixedCurrent', 'fixedPrevious' ]

AVAILABLE_MACHINES   = []


""" """




def getAvailableMachines():
    """    
        @summary : Based on the list of machines found within the 
                   config files, returns the list of avaiable machines.
                   
        @return: returns the list of avaiable machines.             
    
    """
    
        
    configParameters = StatsConfigParameters()
    configParameters.getAllParameters()
    
    for tag in configParameters.detailedParameters.sourceMachinesForTag:
        machines = configParameters.detailedParameters.sourceMachinesForTag[tag]
        for i in range( len( machines ) ):
            AVAILABLE_MACHINES.append( machines[i] )
            combinedNames = machines[i]
            for j in range( i+1, len( machines ) ) :
                combinedNames = combinedNames + ',' + machines[j]
                AVAILABLE_MACHINES.append( combinedNames )
                
    AVAILABLE_MACHINES.sort()
    
    print AVAILABLE_MACHINES
    
                
                    
def getCurrentTimeForCalendar( ):
    """
        @summary : Returns the current time in a format 
                   that's appropriate for use with calendar.
        
        @return: : Returns the currrent time.              
    
    """
    
    currentDay, currentHour = StatsDateLib.getIsoFromEpoch( time.time() ).split( " " )  
    
    splitDay = currentDay.split( "-" )
    
    currentDay = splitDay[2] + "-" + splitDay[1] + "-" + splitDay[0] 
    
    return currentDay + " " + currentHour
    
    
    
    
def printEndOfBody():
    """
        @summary: Prints the closing items of the HTML file.
    """
    
    print """    
        </body>
    </html>
    """


def printChoiceOfSourlients( plotter, form ):
    """  
        @summary : Prints the list of available  source or clients
        
        @param plotter: Plotter that<s currently chosen on the web page. 
        
        @param form: Form with whom this page was called. 
                     Need to know if any clients were previously
                     selected. 
                    
    """    
    
    try:
        sourLients = form["sourLients"]
    except KeyError:
        sourLients = None
        
        
    if sourLients is not None and sourLients != "":
        
        print """
                     
                            <td>
                                 <label for="sourlientList">Client(s)/Source(s) :</label><br>
                                 <select size=5 name="sourlientList" style="width: 300px;"height: 25px;"" multiple>
        """
        
        for sourlient in sourLients:
            print """                 
                                          
                                    <option value="%s">%s</option>                          
            """%( sourlient, sourlient )
            
        
        print """               
                                </select>
                                                            
                                <br>   
                        
                                <input type=button class="button" value="Add Clients" onclick =" javascript:popupAddingWindow('popupAdder.html');">    
                                <input type=button class="button" value="Delete client" onclick ="javascript:deleteFromList(sourlientList);">
                                   
            """
    else:
        
        
        print """

                    <td>
                          <label for="sourlientList">Client(s)/Source(s) :</label><br>
                         <select size=5 name="sourlientList" style="width: 300px;" multiple>
                        </select>                   
               
                        <br>               
                    
                        <input type=button name="addButton" class="button" value="Add Sourlients" onclick ="javascript:popupAddingWindow( document.inputForm.fileType[ document.inputForm.fileType.selectedIndex ].value + (document.inputForm.machines[ document.inputForm.machines.selectedIndex ].value).replace(',','') + 'PopUpSourlientAdder.html' );">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        <input type=button name="deleteButton" class="button" value="Delete Sourlients" onclick ="javascript:deleteFromList(sourlientList);">
    """
    
    if plotter == "gnuplot":
        printCombineSourlientsCheckbox(form)
      
    print """    
                    </td>
    """
  
  
    
def printAjaxRequestsScript():
    """    
        @summary : prints out the section that will contain the javascript 
                   functions that will allow us to make queries 
                   to the request broker and to display the query results 
                   without having to refresh the page.

        @author:   Java script functions were originaly found here :
                   http://wikipython.flibuste.net/moin.py/AJAX
                   
                   They were modified to fit our specific needs. 
    """
    print """
    
            <script language="JavaScript">

                function getHTTPObject() {
                  var xmlhttp;
                  /*@cc_on
                  @if (@_jscript_version >= 5)
                    try {
                      xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
                      } catch (e) {
                      try {
                        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
                        } catch (E) {
                        xmlhttp = false;
                        }
                      }
                  @else
                  xmlhttp = false;
                  @end @*/
                
                  if (!xmlhttp && typeof XMLHttpRequest != 'undefined') {
                    try {
                      xmlhttp = new XMLHttpRequest();
                      } catch (e) {
                      xmlhttp = false;
                      }
                    }
                  return xmlhttp;
               }
                               
                
                var http = getHTTPObject();
                                
                
                function executeAjaxRequest( strURL, plotter ) {                  
                   
                   var parameters = ''; 
                   
                   if( strURL == 'popupSourlientAdder.py'){ 
                        parameters = getParametersForPopups();
                   }else if( strURL == 'graphicsRequestBroker.py' ){
                        parameters = getParametersForGraphicsRequests( plotter );
                   }                   
                   
                  
                  http.open("GET", strURL + parameters, true );
                  http.onreadystatechange = handleHttpResponse;
                  http.send(null);
                
                }
                
                
                function handleHttpResponse() {
                  
                  if (http.readyState == 4) {                    
                    var response = http.responseText;
                  
                    if( response.match('images') != null && response.match('error') != null){ 
                        //document.getElementById("errorLabel").innerHTML = str;
                        var image = response.split(";")[0];
                        var error = response.split(";")[1];
                        image = image.split("=")[1];
                        error = error.split("=")[1];
    
                        document.getElementById("errorLabel").innerHTML = '<font color="#C11B17">' + error + '</font>';
                        document.getElementById("photoslider").src = image;                  
                                                       
                    }
                  }
               }     
                    
                function getParametersForGraphicsRequests( plotter ){
                    
                    var qstr = '';
                    
                    if( plotter == 'gnuplot'){
                        qstr = getParametersForGnuplotRequests();
                    }else if( plotter == 'rrd'){
                        qstr = getParametersForRRDRequests();
                    }
                    
                    return qstr;
                                      
                }
                
                                
                function getParametersForGnuplotRequests(){
                    
                     var qstr = '?plotter=gnuplot&querier=graphicsRequestPage.py&endTime=' + document.forms['inputForm'].elements['endTime'].value +'&groupName='+ (document.forms['inputForm'].elements['groupName'].value) +'&products='+ (document.forms['inputForm'].elements['products'].value) +'&span=' + (document.forms['inputForm'].elements['span'].value) +'&fileType=' + (document.inputForm.fileType[document.inputForm.fileType.selectedIndex].value) +'&machines=' + (document.inputForm.machines[document.inputForm.machines.selectedIndex].value) +'&combineSourlients='  + (document.inputForm.combineSourlients.checked) + '&statsTypes='  + (document.inputForm.statsTypes[document.inputForm.statsTypes.selectedIndex].value);
                        
                      return qstr;
                
                }
                
                
                function getParametersForRRDRequests(  ){
                    
                    var qstr = '';

                    var plotter    = 'rrd';
                    var endTime    = document.forms['inputForm'].elements['endTime'].value;
                    var groupName  = document.forms['inputForm'].elements['groupName'].value;
                    var products   = document.forms['inputForm'].elements['products'].value;
                    var span       = document.forms['inputForm'].elements['span'].value;
                    var fileType   = document.inputForm.fileType[ document.inputForm.fileType.selectedIndex ].value;
                    var machines   = document.inputForm.machines[ document.inputForm.machines.selectedIndex ].value;
                    var statsTypes = document.inputForm.statsTypes[ document.inputForm.statsTypes.selectedIndex ].value;
                    var preDeterminedSpan= document.inputForm.preDeterminedSpan[ document.inputForm.preDeterminedSpan.selectedIndex ].value;
                    var fixedSpan = document.inputForm.fixedSpan[ document.inputForm.fixedSpan.selectedIndex ].value;

                    var sourlients= document.inputForm.sourlientList.options;

                    qstr = '?plotter=rrd&querier=graphicsRequestPage.py&endTime=' + escape(endTime) + '&groupName=' + escape(groupName) + '&products=' + escape(products) + '&span=' + escape(span);
                    qstr = qstr + '&fileType=' + escape(fileType) + '&machines=' + escape(machines) +'&statsTypes=' + escape(statsTypes);
                    qstr = qstr + '&preDeterminedSpan=' + escape(preDeterminedSpan) + '&fixedSpan=' + escape(fixedSpan);
                    qstr = qstr + '&sourlients=' + escape(sourlients);

                    
                    return qstr;

                    
                }  
                    
                
                function getParametersForPopups() {
    
                    var fileType     = document.inputForm.fileType[document.inputForm.fileType.selectedIndex].value;
                    
                    var machines     = document.inputForm.machines[document.inputForm.machines.selectedIndex].value;
                                                   
                    var qstr = '?fileType=' + escape(fileType) + '&machines=' + escape(machines);  // NOTE: no '?' before querystring
        
                
                    return qstr;
                
                }    
            
            
            </script> 
                              
    """
    
    
    
def printSlideShowScript( images ):
    """    
        @summary : Prints out the javascript required 
                   by the image slide show
    
        @credits : This code was heavily inspired by the 
                   freely avaiable code found here : 
                   http://www.dynamicdrive.com/dynamicindex14/dhtmlslide_dev.htm  
           
                   This code was modified according to the terms of use found here:
                   http://dynamicdrive.com/notice.htm    
    """
    
    print """
    
            <script type="text/javascript">
        
                /***********************************************
                * DHTML slideshow script-  Dynamic Drive DHTML code library (www.dynamicdrive.com)
                * This notice must stay intact for legal use
                * Visit http://www.dynamicdrive.com/ for full source code
                ***********************************************/
                
                var photos=new Array();
                var photoslink=new Array();
                var which=0;
    """
    
    for i in range(  len( images ) ):
        print """
                photos[%s]="%s";
        
        """ %(i, images[i])

    
    print """            
                //Specify whether images should be linked or not (1=linked)
                var linkornot=0;
                
                //Set corresponding URLs for above images. Define ONLY if variable linkornot equals "1"
                photoslink[0]="";
                photoslink[1]="";
                photoslink[2]="";
                
                //do NOT edit pass this line
                
                var preloadedimages=new Array();
                for (i=0;i<photos.length;i++){
                preloadedimages[i]=new Image();
                preloadedimages[i].src=photos[i];
                }
                
                
                function applyeffect(){
                    if (document.all && photoslider.filters){
                        photoslider.filters.revealTrans.Transition=Math.floor(Math.random()*23);
                        photoslider.filters.revealTrans.stop();
                        photoslider.filters.revealTrans.apply();
                    }
                }
                
                
                
                function playeffect(){
                    if (document.all && photoslider.filters)
                        photoslider.filters.revealTrans.play();
                }
                
                function keeptrack(){
                    window.status="Image "+(which+1)+" of "+photos.length;
                }
                
                
                function backward(){
                    if (which>0){
                        which--;
                        applyeffect();
                        document.images.photoslider.src=photos[which];
                        playeffect();
                        keeptrack();
                    }
                }
                
                function forward(){
                    if (which<photos.length-1){
                        which++;
                        applyeffect();
                        document.images.photoslider.src=photos[which];
                        playeffect();
                        keeptrack();
                    }
                }
                
                function transport(){
                    window.location=photoslink[which];
                }
            
        </script>

    
    """


def printRRDImageFieldSet( form ):
    """
        @summary : Prints out the image field set that allows 
                   the display of rrd generated graphics. 
                   
                   Will use the image slideshow script to diplay 
                   the images when numerous ones need to be 
                   displayed.  
                   
                   
        @requires: Requires the  printSlideShowScript(images)            
                   method to have been run. 
        
    """
  
    width  = 875
    height = 250     
    
    print """
         <fieldset>
            <legend>Resulting graphic(s)</legend>
            <table border="0" cellspacing="0" cellpadding="0">
                <tr>
                    <td>
                        <script>
                                if (linkornot==1)
                                document.write('<a href="javascript:transport()">')
                                 document.write('<img src="'+photos[0]+'" name="photoslider" style="filter:revealTrans(duration=2,transition=23)" border=0>')
                                if (linkornot==1)
                                document.write('</a>')
                        </script>
                    </td>
                </tr>
            </table>        
        </fieldset>

        <fieldset>
             <input type=button value="Previous image result." onclick ="backward();return false;">
             <input type=button value="View original size"     onclick ="wopen( photoslider.src, 'popup', %s, %s); return false;">
             <input type=button value="Next image result."     onclick ="forward();return false;" >
        </fieldset>

    """%(  width, height )



def printGnuPlotImageFieldSet(form):
    """
       @summary : Prints the  section where the image will be displayed.
       
       @param from: Form with whom this program was called.
      
       @todo: Receive variable imaghe size as a parameter.
        
    """
    
    try:
        image = form["image"][0].split(',')[0]
    except:
        image = ""
            
    width  = 1160
    height = 1160        
    
        
    print """
         <fieldset>
            <legend>Resulting graphic</legend>
            <img src="%s">            
        </fieldset>    
        <fieldset>                
            <input type=button class="button" value="View original size" onclick =" wopen('%s', 'popup', %s, %s); return false;">            
        </fieldset>    
    
    """%( image, image, width, height )


    
def printImageFieldSet( plotter, form ):
    """
       
       @summary : Prints the  section where the image will be displayed.
       
       @param from: Form with whom this program was called.
       
       @param plotter : Plotter wich was used to created image. Output image size will be 
                        based on plotter used.
       
       @todo: Receive variable imaghe size as a parameter.
       
    """
    
    if plotter == "gnuplot":
        printGnuPlotImageFieldSet(form)
    elif plotter == "rrd":
        printRRDImageFieldSet(form)    


    
def printGroupTextBox( form ):
    """
        @Summary : Prints out the group text box.
                   If form contains a group value, 
                   the text box will be set to this value.
                   
        @param form: Form with whom this program was called.      
              
    """
    
    try:
        groupName = form["groupName"][0]
    except:
        groupName = ""    
    
    print """
                        <td width = 210 >
                            <label for="groupName">Group name:</label>
                            <INPUT TYPE=TEXT class="text" NAME="groupName" value = "%s">
                        </td>      
    """%( groupName )



def printProductsTextBox( form ):
    """
        @Summary : Prints out the products text box.
                   If form contains a products value, 
                   the text box will be set to this value.
                   
        @param form: Form with whom this program was called.     
    
    """
    try:
        products = form["products"][0]
    except:
        products = ""    
    
    print """
                        <td width = 210>    
                            <label for="products">Products:</label><br>
                            <INPUT TYPE=TEXT class="text" NAME="products" value = "%s">
                        </td>  
    """%( products ) 
   
   
   
def printSpanTextBox( form ):
    """        
        @Summary : Prints out the span text box.
                   If form contains a span value, 
                   the text box will be set to this value.
                   
        @param form: Form with whom this program was called.         
    """
    
    try:
        span = form["span"][0]
    except:
        span = ""    
    
    print """
                        <td width = 210>    
                            <label for="span">Span(in hours):</label><br>
                            <INPUT TYPE=TEXT class="text" NAME="span" value = "%s">     
                        </td>    
    """%( span ) 



def printFileTypeComboBox( form ):
    """    
        @Summary : Prints out the file type combo box.
                   If form contains a file type value, 
                   the combo will be set to this value.
                   
        @param form: Form with whom this program was called.  
    """
    
    try:
        selectedFileType = form["fileType"]
    except:
        selectedFileType = ""
    
    
    print """
                        <td width = 210>
                            <label for="fileType">FileType:</label><br>
                            <select name="fileType" OnChange="JavaScript:executeAjaxRequest( 'popupSourlientAdder.py', '' );Javascript:updateButtons();">
                                <option>Select a file type...</option>
    """
    
    
    for fileType in SUPPORTED_FILETYPES:
        if fileType == selectedFileType:            
            print """                               
                                <option selected value="%s">%s</option>                              
            """ %( fileType, fileType )
        else:
            print """
                                <option  value="%s">%s</option>
            """%( fileType, fileType )
 

      
def printSpecificSpanComboBox( form ):
    """    
        @Summary : Prints out the specific span combo box.
                   If form contains a specific span value, 
                   the combo will be set to this value.
                   
        @param form: Form with whom this program was called.  
    """
    
    try:
        selectedPreDeterminedSpan = form["preDeterminedSpan"][0]
    except:
        selectedPreDeterminedSpan = ""
    
    
    print """
                        <td width = 210px> 
                            <label for="preDeterminedSpan">Determined spans : </label><br>
                            <select name="preDeterminedSpan" >     
                            <option>Pre-determined spans...</option>               
    """
    for span in PRE_DETERMINED_SPANS:
        if span == selectedPreDeterminedSpan:            
            print """                               
                                <option selected value="%s">%s</option>                              
            """ %( span, span )
        else:
            print """
                                <option  value="%s">%s</option>
            """%( span, span )



def printFixedSpanComboBox( form ):
    """    
        @Summary : Prints out the fixed span combo box.
                   If form contains a fixed span value, 
                   the combo will be set to this value.
                   
        @param form: Form with whom this program was called.  
    """
    
    try:
        selectedFixedSpan = form["fixedSpan"][0]
    except:
        selectedFixedSpan = ""
    
    
    print """
                        <td width = 210px> 
                            <label for="fixedSpan">Fixed spans : </label><br>
                            <select name="fixedSpan" >     
                            <option>Select fixed span...</option>               
    """
    
    for span in FIXED_SPANS:
        if span == selectedFixedSpan:            
            print """                               
                                <option selected value="%s">%s</option>                              
            """ %( span, span )
        else:
            print """
                                <option  value="%s">%s</option>
            """%( span, span )



def printMachinesComboBox( form ):
    """    
        @Summary : Prints out the machines combo box.
                   If form contains a machines value, 
                   the combo will be set to this value.
                   
        @param form: Form with whom this program was called.  
    
    """
    
    try:
        selectedMachines = form["machines"][0]
    except:
        selectedMachines = ""
    
    
    print """
                        <td width = 210px> 
                            <label for="machines">Machine(s):</label><br>
                            <select class="dropDownBox" name="machines" OnChange="JavaScript:executeAjaxRequest( 'popupSourlientAdder.py', '' ) ">     
                            <option>Select a machine name...</option>               
    """
    for machines in AVAILABLE_MACHINES:
        if machines == selectedMachines:            
            print """                               
                                <option selected value="%s">%s</option>                              
            """ %( machines, machines )
        else:
            print """
                                <option  value="%s">%s</option>
            """%( machines, machines )


    
def printStatsTypesComboBox( plotter, form ):
    """    
        @Summary : Prints out the machines combo box.
                   If form contains a machines value, 
                   the combo will be set to this value.
                   
        @param form: Form with whom this program was called.  
        
    """
    
    rrdRxTypes     = [ 'bytecount', 'errors', 'bytecount, errors' ]
    rrdTxTypes     = [ 'bytecount', 'errors', 'latency', 'bytecout,errors', 'bytecount,latency', 'errors,latency','bytecount,errors,latency' ]    
    gnuplotRxTypes = [ 'bytecount', 'errors', 'bytecount, errors' ]
    gnuplotTxTypes = [ 'bytecount', 'errors', 'latency', 'bytecout,errors', 'bytecount,latency', 'errors,latency','bytecount,errors,latency' ]  
         
    
    try:
        selectedStatsTypes = form["statsTypes"][0]
    except:
        selectedStatsTypes = ""
    
    try:
        filetype = form["filetype"][0]
    except:    
        filetype = "rx"
        
    if plotter == "rrd" and filetype == "rx":    
        listOfChoices = rrdRxTypes
    elif plotter == "rrd" and filetype == "tx":
        listOfChoices = rrdTxTypes 
    elif plotter == "gnuplot" and filetype == "rx":
        listOfChoices = gnuplotRxTypes
    elif plotter == "gnuplot" and filetype == "tx":            
        listOfChoices = gnuplotTxTypes
    else:
        listOfChoices = []    
        
        
    print """
                        <td width = 210px> 
                            <label for="statsTypes">Stats type(s):</label><br>
                            <select name="statsTypes" >     
                            <option>Select stats types.</option>               
    """
    
    for choice in listOfChoices:
    
        if choice == selectedStatsTypes:            
            print """                               
                                <option selected value="%s">%s</option>                              
            """ %( choice, choice )
     
        else:
            print """
                                <option  value="%s">%s</option>
            """%( choice, choice )    



def printCombineHavingrunCheckbox( form ):
    """    
        @Summary : Prints out the having run check box.
                   If form contains an having run value, 
                   the check box will be checked.
                   
        @param form: Form with whom this program was called.     
        
    """
    
    try:
        havingRun = form["havingRun"][0]
    except:
        havingRun = "False" 
    
    
    if havingRun == "true" :
            print """
                                    
                            <INPUT TYPE="checkbox" NAME="havingRun"  CHECKED>Having run.
                         
            """  
    else:
        print """                                    
                            <INPUT TYPE="checkbox" NAME="havingRun">Having run.                          
        """    
     

def printIndividualCheckbox( form ):
    """    
        @Summary : Prints out the Individual check box.
                   If form contains an Individual value, 
                   the check box will be checked.
                   
        @param form: Form with whom this program was called.   
          
    """
    
    try:
        individual = form["individual"][0]
    except:
        individual = "False" 
    
    
    if individual == "true" :
            print """
                            <td>        
                                <INPUT TYPE="checkbox" NAME="individual"  CHECKED>Individual.
                            </td. 
            """  
    else:
        print """               
                            <td>
                                <INPUT TYPE="checkbox" NAME="individual">Individual.                          
                            </td>
        """     



def printTotalCheckbox( form ):
    """    
        @Summary : Prints out the total check box.
                   If form contains an total value, 
                   the check box will be checked.
                   
        @param form: Form with whom this program was called.     
        
    """
    
    try:
        total = form["total"][0]
    except:
        total = "False" 
    
    
    if total == "true" :
            print """
                            <td>        
                                <INPUT TYPE="checkbox" NAME="total"  CHECKED>Total.
                             </td>
            """  
    else:
        print """           <td>                         
                                <INPUT TYPE="checkbox" NAME="total">Total.                          
                            </td>
        """ 


     
def printCombineSourlientsCheckbox( form ):
    """    
        @Summary : Prints out the check box.
                   If form contains a checkbox value, 
                   the check box will be checked.
                   
        @param form: Form with whom this program was called.     
    """
    
    try:
        combineSourlients = form["combineSourlients"][0]
    except:
        combineSourlients = "False" 
    
    
    if combineSourlients == "true" :
            print """
                                    
                            <INPUT TYPE="checkbox" NAME="combineSourlients"  CHECKED>Combine the sourLients.
                         
            """  
    else:
        print """
                                    
                            <INPUT TYPE="checkbox" NAME="combineSourlients">Combine the source(s)/client(s).
                          
        """    
    
    
def printEndTime( form ):
    """
        @summary : Prints end time calendar into the 
                   inputform
        
        @param   : The parameter form with whom this program was called. 
    
    """
    
    try:
        endTime = form["endTime"][0]
    except:
        endTime = getCurrentTimeForCalendar() 
        
    print """         
                        <td bgcolor="#ffffff" valign="top" width = 210>
                            <label for="endTime">End Time Date:</label><br>
                            <input type="Text" class="text" name="endTime"  value="%s" width = 150>
                            <a href="javascript:cal1.popup();"><img src="images/cal.gif" width="16" height="16" border="0" alt="Click Here to Pick up the date"></a>
                        
                            <script language="JavaScript">
                                <!-- // create calendar object(s) just after form tag closed -->
                                // specify form element as the only parameter (document.forms['formname'].elements['inputname']);
                                // note: you can have as many calendar objects as you need for your application
                                var cal1 = new calendar1(document.forms['inputForm'].elements['endTime']);
                                cal1.year_scroll = true;
                                cal1.time_comp = true;
                            </script>                            
                        </td>
                
    """ %( endTime )     
    
   
    
def printGnuPlotInputForm(  form   ):
    """
        @summary: Prints a form containing all the 
                  the avaiable field for a graph to
                  be plotted with gnu. 
    """
    
    #Start of form
    print """
        <form name="inputForm"  method="post" class="fieldset legend">
            <fieldset>
                <legend>Gnuplot fields</legend>
                
                <table>
                    <tr>
                
    """         
    
    #Print first table row
    printEndTime(form)
    printGroupTextBox(form)
    printProductsTextBox(form)
    printSpanTextBox(form)
    
    
    #Jump a table row.
    print """
                    </tr>   
                    <tr>
                    </tr> 
                    <tr>
    """
    
    printFileTypeComboBox(form)
    printMachinesComboBox(form)
    printStatsTypesComboBox( "gnuplot", form )    
    printChoiceOfSourlients( 'gnuplot', form )

    #printCombineSourlientsCheckbox(form)  
   
    #End of fieldSet
    print """       
                     </tr>                                                        
                </table>             
            </fieldset>  
    """
    
    #Add fieldset for submit button 
    print """
            <fieldset>                             
                <input type="button"  name="generateGraphics" value="Generate graphic(s)" 
                 onclick="JavaScript:executeAjaxRequest('graphicsRequestBroker.py', 'gnuplot')" >
                <input type=button  name="help "value="Get Help" onclick ="wopen( document.plotterChoiceForm.plotterChoice[document.plotterChoiceForm.plotterChoice.selectedIndex].value + 'Help.html', 'popup', 800, 670 );">                                
            
    """        
    
    
    
    print"""
        
            <div id="errorLabel"></div>
        
    """
    
    print """        
            
            </fieldset>    
    """
    
    #End of form.
    print """
        </form>        
    """
    



def printRRDInputForm(  form   ):
    """
        @summary: Prints a form containing all the 
                  the avaiable field for a graph to
                  be plotted with gnu. 
    """
    
    #Start of form
    print """
        <form name="inputForm"  method="post" class="fieldset legend">
            <fieldset>
                <legend>RRD fields</legend>
                
                <table>
                    <tr>
                
    """         
    
    #Print first table row
    printEndTime(form)
    printGroupTextBox(form)
    printProductsTextBox(form)
    printSpanTextBox(form)
    printIndividualCheckbox(form)
    printTotalCheckbox(form)
    
    #Jump a table row.
    print """
                    </tr>   
                    <tr>
                    </tr> 
                    <tr>
    """
    
    printFileTypeComboBox(form)
    printMachinesComboBox(form)
    printStatsTypesComboBox( "rrd", form )     
    printSpecificSpanComboBox(form)
    printFixedSpanComboBox(form)
    printChoiceOfSourlients( 'rrd', form )

    #printCombineSourlientsCheckbox(form)  
   
    #End of fieldSet
    print """       
                     </tr>                                                        
                </table>             
            </fieldset>  
    """
    
    #Add fieldset for submit button 
    print """
            <fieldset>                             
                <input type="button"  name="generateGraphics" value="Generate graphic(s)" 
                 onclick="JavaScript:executeAjaxRequest('graphicsRequestBroker.py', 'rrd')">
                <input type=button  name="help "value="Get Help" onclick ="wopen( document.plotterChoiceForm.plotterChoice[document.plotterChoiceForm.plotterChoice.selectedIndex].value + 'Help.html', 'popup', 830, 1100 );">                                
    """
    
    
    print"""
        
            <div id="errorLabel"></div>
        
    """
            
    print """        
            </fieldset>    
    """
    
    #End of form.
    print """
        </form>        
    """
    
    
     
def printInputForm( plotter, form ):
    """
        @summary: Prints the form based 
                  on the plotter that was chosen
                  
    """
    
    if plotter == "gnuplot" :
        printGnuPlotInputForm( form )
    
    elif plotter == "rrd":
        printRRDInputForm( form )    
    


def printPlottersChoice( plotter ):
    """    
        @summary : Prints the section relative to the available choice
                   of plotters.
        
        @param plotter: The plotter name that was used as a parameter 
                        when this page was called.            
    """
    
    
    print """
        <body text=black link="#FFFFFF" vlink="000000" bgcolor=#99FF99 >
            <form name="plotterChoiceForm">                
                <select name="plotterChoice"
                    OnChange="location.href='graphicsRequestPage.py?plotter='+(plotterChoiceForm.plotterChoice.options[selectedIndex].value)" >                
                
    """
    
    for supportedPlotter in  SUPPORTED_PLOTTERS :
        if supportedPlotter == plotter:
            
            print """
                        <option selected value="%s">%s</option>
             """ %( supportedPlotter,supportedPlotter )    
        else:
            print """
                        <option value="%s">%s</option>
             """ %( supportedPlotter,supportedPlotter )            
             
    print """   
                </select>
            </form>
    """
    
    
def printHead( plotter, form ):
    """
        @summary : Print the head of the html file. 
            
    """
        
    print """
    
    <html>
        <head>
            <meta name="Author" content="Nicholas Lemay">
            <meta name="Description" content="graphic requests">
            <meta name="Keywords" content="">
            <title>Graphic requests.</title>
            <link rel="stylesheet" type="text/css" href="/css/style.css">
            
            <style type="text/css">                
                fieldset { 
                    border:2px solid; 
                    border-color: #3b87a9;
                    background-color:white; 
                }

                legend {
                    padding: 0.2em 0.5em;
                    border:2px solid;
                    border-color:#3b87a9;
                    color:black;
                    font-size:90%;
                    text-align:right;
                }
                
                img{ 
                    max-height: 325px;
                    height: expression(this.height > 325 ? 325: true);
                }
                
                input.button{
                
                    width: 125px
                
                }
                
                input.text{
                    width: 160px
                }
                
                input.endtime{
                    width = 100px;
                }
                
                
                select.dropDownBox{
                    max-width: 160px;
                    width: expression(this.width > 160 ? 160: true);
                }
                
                
                
                div.left { float: left; }
                div.right {float: right; }
                <!--
                A{text-decoration:none}
                -->
                <!--
                td {
                    white-space: pre-wrap; /* css-3 */

                }
                // -->
            </style>  
            
    """
    
        
    print """
            <!--Java scripts sources -->
            <script src="js/calendar1.js"></script>
            <script src="js/calendar2.js"></script>
            <script src="js/windowUtils.js"></script>
            <script src="js/popupListAdder.js"></script>
            <script>
                counter =0;             
                function wopen(url, name, w, h){
                // This function was taken on www.boutell.com
                    
                    w += 32;
                    h += 96;
                    counter +=1; 
                    var win = window.open(url,
                    counter,
                    'width=' + w + ', height=' + h + ', ' +
                    'location=no, menubar=no, ' +
                    'status=no, toolbar=no, scrollbars=no, resizable=no');
                    win.resizeTo(w, h);
                    win.focus();
                }   
            </script>  
            
            
            <script language="Javascript">
            
                function updateButtons(){
                
                    if ( document.inputForm.fileType[document.inputForm.fileType.selectedIndex].value == 'rx' ){
                        
                       document.inputForm.addButton.value    = 'Add Sources   ';
                       document.inputForm.deleteButton.value = 'Delete Sources';
                        
                    }else if( document.inputForm.fileType[document.inputForm.fileType.selectedIndex].value == 'tx' ){
                        
                        document.inputForm.addButton.value    = 'Add Clients   ';
                        document.inputForm.deleteButton.value = 'Delete Clients';
                    
                    }else{
                        document.inputForm.addButton.value    = 'Add ';
                        document.inputForm.deleteButton.value = 'Delete';
                    
                    }
                }
                
            </script>
            
            
    """
    
    
    if plotter == "rrd":
        try:
            printSlideShowScript( form["image"][0].split(',') )
        except:#no specified image 
            printSlideShowScript( [] )
    printAjaxRequestsScript()         
    print """        
        </head>
    """


def startCGI():
    """
        @summary : Start of cgi script printing.
        
    """
    print "Content-Type: text/html"
    print
    
    
def getPlotter( form ):
    """
        @summary: Gets the plotter that was specified when calling this page
                  or the default plotter if no plotter was specified. 
        
        @param form: The form that was received when the page was called.
        
        @return : Returns the plotter. 
         
    """
    
    plotter = SUPPORTED_PLOTTERS[0]
    
    try:    
        plotter = form["plotter"][0]
        
    except:
        pass
    
    return plotter 



def buildWebPageBasedOnReceivedForm( form ):
    """
        
        @summary: Buils up the graphics query page. Fields will be filled with the values
                  that were set in the form. If no parameters was received, we use defaults.
       
        @param form:
         
    """
    
    plotter = getPlotter( form )
    startCGI()
    printHead( plotter, form )
    printPlottersChoice( plotter )
    printInputForm(plotter, form )
    printImageFieldSet( plotter, form )
    printEndOfBody()

        

def getForm():
    """
        @summary: Returns the form with whom this page was called. 
        @return:  Returns the form with whom this page was called. 
    """

    form = cgi.FormContent()
    
    for key in form.keys():
        if "?" in key:
            form[key.replace("?","")]= form[key]
            
    print form
    
    return  form
    


def main():
    """
        @summary : Displays the content of the p[age based 
                   on selected plotter.  
    """    
    
    getAvailableMachines()
    
    form = getForm()
    
    buildWebPageBasedOnReceivedForm( form )
    
    
    
   
    
if __name__ == '__main__':
    main()