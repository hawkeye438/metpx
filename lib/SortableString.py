"""
#############################################################################################
# Name: SortableString.py
#
# Author: Daniel Lemay
#
# Date: 2004-02-01
#
# Description:
#
#############################################################################################

"""

import os.path

class SortableString:
   # Structure des strings:
   # testfileXXXX_PRI
   # SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:3.A.I.E.C.M.N.H.K.X.S.D.O.Q.::20050201200339
  
   def __init__(self, string):
      self.data = string
      self.basename = os.path.basename(string)
      self.priority = None
      self.timestamp = None
      self.concatenatedKeys = None
      self._getKeys()

   def _getKeys(self):
      parts = self.basename.split(":")
      self.priority = parts[4].split(".")[0]
      self.timestamp = parts[6]
      self.concatenatedKeys = self.priority + self.timestamp

if __name__ == '__main__':

   #ss = SortableString("toto99_2")
   ss = SortableString("SACN43_CWAO_012000_CYOJ_41613:ncp1:CWAO:SA:3.A.I.E.C.M.N.H.K.X.S.D.O.Q.::20050201200339")
   print ss.data
   print ss.basename
   print ss.priority  
   print ss.timestamp
   print ss.concatenatedKeys
      
