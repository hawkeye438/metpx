"""Sp�cialisation pour gestion de sockets "AM" """

__version__ = '2.0'

import struct
import socketManager

class socketManagerAm(socketManager.socketManager):

	def __init__(self,type='slave',localPort=9999,remoteHost=None,timeout=None,log=None):
		socketManager.__init__(self,type='slave',localPort=9999,remoteHost=None,timeout=None,log=None)

		# La taille du amRec est prise d'a partir du fichier ytram.h, � l'origine dans
		# amtcp2file. Pour la gestion des champs l'on se refere au module struct
		# de Python.
		self.patternAmRec = '80sLL4sii4s4s20s'
		self.sizeAmRec = struct.calcsize(patternAmRec)

        def __unwrapBulletin(self):
                """unwrapBulletin() -> (bulletin,longBuffer)

                   bulletin     : String
                   longBuffer   : int

                   Retourne le prochain bulletin contenu dans le buffer,
                   apr�s avoir v�rifi� son int�grit�, sans modifier le buffer.
                   longBuffer sera �gal � la longueur de ce que l'on doit enlever
                   au buffer pour que le prochain bulletin soit en premier.

                   Retourne une cha�ne vide s'il n'y a pas assez de donn�es
                   pour compl�ter le prochain bulletin."""
                statut = self.__checkNextMsgStatus() 

		if statut == 'OK':
	                (header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
	                         struct.unpack(self.patternAmRec,self.inBuffer[0:self.sizeAmRec])

        	        length = socket.ntohl(length)

	                bulletin = self.inBuffer[self.sizeAmRec:self.sizeAmRec + length]

	                return (bulletin,self.sizeAmRec + length)
	        else:
	                return ''


	def
