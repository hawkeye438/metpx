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
	
	"""

	def __init__(self,logger,type='slave',localPort=9999,remoteHost=None,timeout=None):
		socketManager.socketManager.__init__(self,logger,type,localPort,remoteHost,timeout)

		# La taille du amRec est prise d'a partir du fichier ytram.h, � l'origine dans
		# amtcp2file. Pour la gestion des champs l'on se refere au module struct
		# de Python.
		self.patternAmRec = '80sLL4sii4s4s20s'
		self.sizeAmRec = struct.calcsize(self.patternAmRec)

        def unwrapBulletin(self):
                """unwrapBulletin() -> (bulletin,longBuffer)

                   bulletin     : String
                   longBuffer   : int

                   Retourne le prochain bulletin contenu dans le buffer,
                   apr�s avoir v�rifi� son int�grit�, sans modifier le buffer.
                   longBuffer sera �gal � la longueur de ce que l'on doit enlever
                   au buffer pour que le prochain bulletin soit en premier.

                   Retourne une cha�ne vide s'il n'y a pas assez de donn�es
                   pour compl�ter le prochain bulletin."""
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
                """checkNextMsgStatus() -> status

                   status       : String �l�ment de ('OK','INCOMPLETE','CORRUPT')

                   Statut du prochain bulletin dans le buffer.
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

