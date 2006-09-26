"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.
"""

"""
#################################################################
# Name: NCSClientMerger.py
#
# Author: Dominik Douville-Belanger
#
# Date: 2005-01-26
#
# Description: Merges informations from all the PDS about the
#              circuits. Very similar to ClientMerger.py 
#              but the methods are changed a bit.
#
#################################################################
"""

import pickle
from ColumboPath import *
from CompositeNCSCircuit import CompositeNCSCircuit
import errorLog

class CircuitMerger:
    
    def __init__(self, logger, machines):
        self.logger = logger
        self.machines = machines
        self.circuitDictDict = {}
        self.compositeNCSCircuitDict = {}

    def unarchiveInfos(self, filename, machine):
        file = open(filename, "rb")
        self.circuitDictDict[machine] = pickle.load(file)
        file.close()

    def archiveResults(self, filename):
        file = open(filename, "wb")
        pickle.dump(self.compositeNCSCircuitDict, file)
        file.close()
    
    def mergeCircuit(self):
        circuits = self.circuitDictDict[self.machines[0]].keys()
        circuits.sort()
        for circuit in circuits:
            compositeCircuit = CompositeNCSCircuit(circuit)
            for machine in self.machines:
                # Add informations from each PDSs to the composite circuit
                compositeCircuit.addHost(machine)
                compositeCircuit.setStatus(machine, self.circuitDictDict[machine][circuit].status)
                compositeCircuit.setQueue(machine, self.circuitDictDict[machine][circuit].queue)
                compositeCircuit.setLastLog(machine, self.circuitDictDict[machine][circuit].logline)
                compositeCircuit.setSocket(machine, self.circuitDictDict[machine][circuit].socket)
                compositeCircuit.setType(machine, self.circuitDictDict[machine][circuit].type)
                compositeCircuit.setLastRcv(machine, self.circuitDictDict[machine][circuit].lastRcv)
                compositeCircuit.setLastTrans(machine, self.circuitDictDict[machine][circuit].lastTrans)
            # Calculate global values for display in the main page
            compositeCircuit.setCompositeQueue()
            compositeCircuit.setBestLog()
            compositeCircuit.setSocketState()
            compositeCircuit.setAllStatus()
            compositeCircuit.setGlobalLastRcv()
            compositeCircuit.setGlobalLastTrans()
            # Add the composite circuit to the main dictionnary
            self.compositeNCSCircuitDict[circuit] = compositeCircuit
    
    def auditCircuit(self, logger, logname, wams):
        errorLog.errorCheck(logger, logname, wams, self.compositeNCSCircuitDict)
    
    # Only used when debugging
    def printCircuitDict(self, machine):
        print "****************************************************************************************"
        print "*  CircuitDict         " + machine + "                                                 *" 
        print "****************************************************************************************"
        for key, value  in self.circuitDictDict[machine].items():
            print "%20s => %60s" % (key, value)
