"""ReceiverAm: socketAm -> disk, incluant traitement pour les bulletins"""

import gateway
import socketManagerAm
import bulletinManagerAm

class receiverAm(gateway.gateway):
	__doc__ = gateway.gateway.__doc__ + \
	"""
	### Ajout de receiver AM ###

	Implantation du receiver pour un feed AM. Il est constitu�
	d'un socket manager AM et d'un bulletin manager AM.

	Auteur:	Louis-Philippe Th�riault
	Date:	Octobre 2004
	"""

	def __init__(self,path,logger):
		gateway.gateway.__init__(self,path,logger)

		self.logger.writeLog(logger.DEBUG,"Instanciation du socketManagerAm")

		# Instanciation du socketManagerAm
		self.unSocketManagerAm = \
				socketManagerAm.socketManagerAm(type='slave', \
								localPort=self.config.localPort)

                self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManagerAm")

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

		while True:
			# FIXME test ici si une erreur
	                rawBulletin = self.unSocketManagerAm.getNextBulletin()

			if rawBulletin != '':
				data.append(rawBulletin)
			else:
				break

		self.logger(logger.DEBUG,"%d nouveaux bulletins lus",len(data))

		return data

        def write(self,data):
        	"""write(data)

	           data : Liste d'objets
	
	           Cette m�thode prends le data lu par read, et fait le tra�tement
	           appropri�.
	           """

                self.logger(logger.DEBUG,"%d nouveaux bulletins seront �crits",len(data))

		while True:
			if len(data) <= 0:
				break

			rawBulletin = data.pop(0)

			# FIXME test ici si une erreur
			self.unBulletinManagerAm.writeBulletinToDisk(rawBulletin)


