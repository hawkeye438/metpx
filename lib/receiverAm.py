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
				socketManagerAm.socketManagerAm(logger,type='slave', \
								localPort=self.config.localPort)

                self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManagerAm")

		# Instanciation du bulletinManagerAm avec la panoplie d'arguments.
		self.unBulletinManagerAm = \
			bulletinManagerAm.bulletinManagerAm(	self.config.pathTemp,logger, \
								pathDest = self.config.pathDestination, \
								pathFichierCircuit = self.config.ficCircuits, \
								SMHeaderFormat = self.config.SMHeaderFormat, \
								pathFichierStations = self.config.ficCollection, \
								extension = self.config.extension \
								) 

        def read(self):
		__doc__ =  gateway.gateway.read.__doc__ + \
		"""### Ajout de receiverAm ###

		   Le lecteur est le socket tcp, g�r� par socketManagerAm.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		data = []

		while True:
			if self.socketManager.isConnected():
				try:
			                rawBulletin = self.unSocketManagerAm.getNextBulletin()
				except socketManagerException, e:
					if e == "La connection est bris�e":
						self.logger.writeLog(self.logger.ERROR,"Perte de connection, tra�tement du reste du buffer"
						resteDuBuffer, nbBullEnv = self.unSocketManagerAm.closeProperly()
						data = data + resteDuBuffer
						break
			else:
				raise gatewayException("Le lecteur ne peut �tre acc�d�")

			if rawBulletin != '':
				data.append(rawBulletin)
			else:
				break

		self.logger.writeLog(self.logger.DEBUG,"%d nouveaux bulletins lus",len(data))

		return data

        def write(self,data):
        	"""write(data)

	           data : Liste d'objets
	
	           Cette m�thode prends le data lu par read, et fait le tra�tement
	           appropri�.
	        """

                self.logger.writeLog(self.logger.DEBUG,"%d nouveaux bulletins seront �crits",len(data))



		while True:
			if len(data) <= 0:
				break

			rawBulletin = data.pop(0)

			# FIXME test ici si une erreur
			self.unBulletinManagerAm.writeBulletinToDisk(rawBulletin)


