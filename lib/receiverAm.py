"""ReceiverAm: socketAm -> disk, incluant traitement pour les bulletins"""

import gateway
import socketManagerAm
import bulletinManagerAm

class receiverAm(gateway.gateway):
	""""""

	def __init__(self,path):
		gateway.gateway.__init__(self,path)

#		self.unSocketManagerAm = socketManagerAm.socketManagerAm() FIXME

		# Instanciation du bulletinManagerAm avec la panoplie d'arguments.
		self.unBulletinManagerAm = \ 
			bulletinManagerAm.bulletinManagerAm(	self.config.pathTemp, \
								pathDest = self.config.pathDestination, \
								pathFichierCircuit = self.config.ficCircuits, \
								SMHeaderFormat = self.config.SMHeaderFormat, \
								pathFichierStations = self.config.ficCollection \
								) 

        def read(self):
        """read() -> data

           data : Liste d'objets

           Cette m�thode retourne une liste d'objets, qui peut �tre
           ing�r�e par l'�crivain. Elle l�ve une exception si
           une erreur est d�tect�e.
           """
		data = []

		while True
			# FIXME test ici si une erreur
	                rawBulletin = self.unSocketManagerAm.getNextBulletin()

			if rawBulletin != '':
				data.append(rawBulletin)
			else:
				break

        def write(self,data):
        """write(data)

           data : Liste d'objets

           Cette m�thode prends le data lu par read, et fait le tra�tement
           appropri�.
           """
		while True:
			if len(data) <= 0:
				break

			rawBulletin = data.pop(0)

			# FIXME test ici si une erreur
			self.unBulletinManagerAm.writeBulletinToDisk(rawBulletin)
