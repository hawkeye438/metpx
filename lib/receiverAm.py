# -*- coding: UTF-8 -*-
"""ReceiverAm: socketAm -> disk, incluant traitement pour les bulletins"""

import gateway
import socketManagerAm
import bulletinManagerAm
import socketManager
from socketManager import socketManagerException

class receiverAm(gateway.gateway):
	__doc__ = gateway.gateway.__doc__ + \
	"""
	### Ajout de receiver AM ###

	Implantation du receiver pour un feed AM. Il est constitu�
	d'un socket manager AM et d'un bulletin manager AM.

	Auteur:	Louis-Philippe Th�riault
	Date:	Octobre 2004
	"""

	def __init__(self,path,options,logger):
		gateway.gateway.__init__(self,path,options,logger)

		self.establishConnection()

                self.logger.writeLog(logger.DEBUG,"Instanciation du bulletinManagerAm")

		# Instanciation du bulletinManagerAm avec la panoplie d'arguments.
		if not options.source:
		   self.unBulletinManagerAm = \
			bulletinManagerAm.bulletinManagerAm(	
				self.config.pathTemp,logger, \
				pathDest = self.config.pathDestination, \
				pathFichierCircuit = self.config.ficCircuits, \
				SMHeaderFormat = self.config.SMHeaderFormat, \
				pathFichierStations = self.config.ficCollection, \
				extension = self.config.extension, \
				mapEnteteDelai = self.config.mapEnteteDelai, \
                                use_pds = self.config.use_pds
								) 
                else:
                  self.unBulletinManagerWmo = \
                        bulletinManagerWmo.bulletinManagerWmo(
                           FET_DATA + FET_RX + options.source, logger, \
                           pathDest = '/dev/null', \
                           pathFichierCircuit = '/dev/null', \
                           extension = options.extension, \
                           mapEnteteDelai = options.mapEnteteDelai )



        def shutdown(self):
		__doc__ = gateway.gateway.shutdown.__doc__ + \
		"""### Ajout de receiverAm ###

		   Fermeture du socket et finalisation du tra�tement du
		   buffer.

		   Utilisation:

			Fermeture propre du programme via sigkill/sigterm

		   Visibilit�:	Publique
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
                gateway.gateway.shutdown(self)

		if self.unSocketManagerAm.isConnected():
			resteDuBuffer, nbBullEnv = self.unSocketManagerAm.closeProperly()

			self.write(resteDuBuffer)

		self.logger.writeLog(self.logger.INFO,"Succ�s du tra�tement du reste de l'info")

	def establishConnection(self):
		__doc__ = gateway.gateway.establishConnection.__doc__ + \
		"""### Ajout de receiverAm ###

		   establishConnection ne fait que initialiser la connection
		   socket. 

		   Utilisation:

			En encapsulant la connection r�seau par cette m�thode, il est plus
			facile de g�rer la perte d'une connection et sa reconnection.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""

                self.logger.writeLog(self.logger.DEBUG,"Instanciation du socketManagerAm")

                # Instanciation du socketManagerAm
                if self.options.source:
                    self.unSocketManagerAm = \
                        socketManagerAm.socketManagerAm(self.logger,type='slave', \
                                localPort=self.options.port)
                else:
                    self.unSocketManagerAm = \
                        socketManagerAm.socketManagerAm(self.logger,type='slave', \
                                localPort=self.config.localPort)

        def read(self):
		__doc__ =  gateway.gateway.read.__doc__ + \
		"""### Ajout de receiverAm ###

		   Le lecteur est le socket tcp, g�r� par socketManagerAm.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004


		   Modification le 25 janvier 2005: getNextBulletins()
		   retourne une liste de bulletins.

		   Auteur:      Louis-Philippe Th�riault
		"""
		if self.unSocketManagerAm.isConnected():
			try:
		                data = self.unSocketManagerAm.getNextBulletins()
			except socketManager.socketManagerException, e:
				if e.args[0] == "la connexion est brisee":
					self.logger.writeLog(self.logger.ERROR,"Perte de connection, tra�tement du reste du buffer")
					data, nbBullEnv = self.unSocketManagerAm.closeProperly()
				else:
					raise
		else:
			raise gateway.gatewayException("Le lecteur ne peut �tre acc�d�")

		self.logger.writeLog(self.logger.VERYVERYVERBOSE,"%d nouveaux bulletins lus",len(data))

		return data

        def write(self,data):
                __doc__ =  gateway.gateway.write.__doc__ + \
                """### Ajout de receiverAm ###

                   L'�crivain est un bulletinManagerAm.

                   Visibilit�:  Priv�e
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
                """

                self.logger.writeLog(self.logger.VERYVERYVERBOSE,"%d nouveaux bulletins seront �crits",len(data))

		while True:
			if len(data) <= 0:
				break

			rawBulletin = data.pop(0)

			self.unBulletinManagerAm.writeBulletinToDisk(rawBulletin,includeError=True)

        def reloadConfig(self):
                __doc__ = gateway.gateway.reloadConfig.__doc__
                self.logger.writeLog(self.logger.INFO,'Demande de rechargement de configuration')

                try:

                        newConfig = gateway.gateway.loadConfig(self.pathToConfigFile)

                        ficCircuits = newConfig.ficCircuits
                        ficCollection = newConfig.ficCollection

                        # Reload du fichier de circuits
                        # -----------------------------
                        self.unBulletinManagerAm.reloadMapCircuit(ficCircuits)

                        self.config.ficCircuits = ficCircuits

                        # Reload du fichier de stations
                        # -----------------------------
                        self.unBulletinManagerAm.reloadMapEntetes(ficCollection)

                        self.config.ficCollection = ficCollection

                        self.logger.writeLog(self.logger.INFO,'Succ�s du rechargement de la config')

                except Exception, e:

                        self.logger.writeLog(self.logger.ERROR,'�chec du rechargement de la config!')

                        self.logger.writeLog(self.logger.DEBUG,"Erreur: %s", str(e.args))


