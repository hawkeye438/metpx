"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.
"""

"""
###########################################################
# Name: SearchObject.py
#
# Author: Dominik Douville-Belanger
#
# Description: Class containing the information needed in
#              order to perform a search.
#
# Date: 2006-05-15
#
###########################################################
"""

import sys
import time

# Local imports
sys.path.append("../")
import PXPaths; PXPaths.normalPaths()

class SearchObject(object):
    __slots__ = ["headerRegexes", "searchRegex", "searchType", "name", "logPath", "since", "fromdate", "todate"]

    def __init__(self):
        self.headerRegexes = {}
        self.searchRegex = ""
        self.searchType = ""
        self.name = "*"
        self.logPath = ""
        self.since = 0
        self.fromdate = ""
        self.todate = ""
        
        self.fillHeaderRegexes()

    def fillHeaderRegexes(self):
        alphanumeric = "[[:alnum:]-]" # Just an alias instead of typing it everytime
        digits = "[[:digit:]]"
        zeroOrMore = "*"
        oneOrMore = "+"
        
        self.headerRegexes["ttaaii"] = alphanumeric + oneOrMore
        self.headerRegexes["ccccxx"] = alphanumeric + oneOrMore
        self.headerRegexes["ddhhmm"] = digits + "{6}" # Repeats exactly six times
        self.headerRegexes["bbb"] = alphanumeric + zeroOrMore
        self.headerRegexes["stn"] = alphanumeric + zeroOrMore
        self.headerRegexes["target"] = alphanumeric + oneOrMore
        self.headerRegexes["seq"] = digits + "{5}"
        self.headerRegexes["prio"] = digits + "{1}"
    
    def compute(self):
        """
        Refresh the object based on its updated attributes.
        """

        self.logPath = "%s%s_%s.log*" % (PXPaths.LOG, self.getSearchType(), self.getSearchName())
        self.searchRegex = "%s_%s_%s_%s_%s_%s:%s:%s:%s:%s:%s:%s" % (self.getHeaderRegex("ttaaii"), self.getHeaderRegex("ccccxx"), self.getHeaderRegex("ddhhmm"), self.getHeaderRegex("bbb"), self.getHeaderRegex("stn"), self.getHeaderRegex("seq"), self.getHeaderRegex("target"), self.getHeaderRegex("ccccxx"), "[[:alnum:]]+", self.getHeaderRegex("prio"), "[[:alnum:]]+", "[[:digit:]]+")
    
    def getSearchRegex(self):
        return self.searchRegex

    def getLogPath(self):
        return self.logPath

    def getHeaderRegex(self, key):
        return self.headerRegexes[key]
    
    def setHeaderRegex(self, key, value):
        # If user enters a wildcard card, replace it with a regex wildcard
        # CAUTION: Does not distinguish between digits and alphanumeric field,
        #          that means that 98* could be 988 or 98A
        if "*" in value and value != self.headerRegexes[key]:
            value = value.replace("*", "[[:alnum:]-]*")
        self.headerRegexes[key] = value

    def getSearchType(self):
        return self.searchType

    def setSearchType(self, value):
        self.searchType = value

    def getSearchName(self):
        return self.name

    def setSearchName(self, value):
        self.name = value

    def getSince(self):
        return self.since

    def setSince(self, value):
        self.since = int(value)

    def getFrom(self):
        return self.fromdate

    def setFrom(self, value):
        self.fromdate = value

    def getTo(self):
        return self.todate

    def setTo(self, value):
        self.todate = value
