# -*- coding: UTF-8 -*-
"""Sp�cialisation pour gestion de sockets "AM" """

__version__ = '2.0'

import struct, socket
import socketManager

class socketManagerAm(socketManager.socketManager):
	__doc__ = socketManager.socketManager.__doc__ + \
	"""
	--- Sp�cialisation concr�te pour la gestion de sockets AM ---

	### Ajout de socketManagerAm ###

	* Attributs

	patternAmRec		str

				- Pattern pour le d�coupage d'ent�te
				  par struct

	sizeAmRec		int

				- Longueur de l'ent�te (en octets) 
				  calcul�e par struct
	
	Auteur:	Louis-Philippe Th�riault
	Date:	Octobre 2004
	"""

	def __init__(self,logger,type='slave',localPort=9999,remoteHost=None,timeout=None):
		socketManager.socketManager.__init__(self,logger,type,localPort,remoteHost,timeout)

		# La taille du amRec est prise d'a partir du fichier ytram.h, � l'origine dans
		# amtcp2file. Pour la gestion des champs l'on se refere au module struct
		# de Python.
		self.patternAmRec = '80sLL4sii4s4s20s'
		self.sizeAmRec = struct.calcsize(self.patternAmRec)

        def unwrapBulletin(self):
		__doc__ = socketManager.socketManager.unwrapBulletin.__doc__ + \
		"""### Ajout de socketManagerAm ###

		   D�finition de la m�thode

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
                status = self.checkNextMsgStatus()

		if status == 'OK':
	                (header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
	                         struct.unpack(self.patternAmRec,self.inBuffer[0:self.sizeAmRec])

        	        length = socket.ntohl(length)

	                bulletin = self.inBuffer[self.sizeAmRec:self.sizeAmRec + length]

	                return (bulletin,self.sizeAmRec + length)
	        else:
	                return '',0

        def checkNextMsgStatus(self):
                __doc__ = socketManager.socketManager.checkNextMsgStatus.__doc__ + \
                """### Ajout de socketManagerAm ###

                   D�finition de la m�thode

		   Ne d�tecte pas si les donn�es sont corrompues, limitations du 
		   protocole AM ?

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
                """
                if len(self.inBuffer) >= self.sizeAmRec:
                        (header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                                struct.unpack(self.patternAmRec,self.inBuffer[0:self.sizeAmRec])
                else:
                        return 'INCOMPLETE'

                length = socket.ntohl(length)

                if len(self.inBuffer) >= self.sizeAmRec + length:
                        return 'OK'
                else:
                        return 'INCOMPLETE'

