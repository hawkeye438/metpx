# -*- coding: UTF-8 -*-
"""ReceiverWmo: socketWmo -> disk, incluant traitement pour les bulletins"""

import gateway, bulletinManager, collectionManager

class collectionGateway(gateway.gateway):
	__doc__ = gateway.gateway.__doc__ + \
	"""
	Auteur:	Louis-Philippe Th�riault
	Date:	Octobre 2004
	"""

	def __init__(self,path,logger):
		gateway.gateway.__init__(self,path,logger)

		# Instanciation des collectionManager

		# Instanciation du bulletinManager

        def read(self):
		__doc__ =  gateway.gateway.read.__doc__ + \
		"""### Ajout de collectionGateway ###

		   Lecture des bulletins sur le disque par le bulletinManager.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		data = []

		while True:
			# Lecture du prochain rawBulletin

			if rawBulletin != '':
				data.append(rawBulletin)
			else:
				break

		self.logger.writeLog(self.logger.DEBUG,"%d nouveaux bulletins lus",len(data))

		return data

        def write(self,data):
        	"""
	        """

                self.logger.writeLog(self.logger.DEBUG,"%d nouveaux bulletins seront �crits",len(data))

		while True:
			if len(data) <= 0:
				break

			rawBulletin = data.pop(0)

			# Si le bulletin doit etre collect� 
			if self.collManager.needsToBeCollected(rawBulletin):

				# Envoi dans collManager 
				self.collManager.addBulletin(rawBulletin)

			else:

				# Parcours normal (non collect�) 
				self.bulletinManager.writeBulletinToDisk(rawBulletin)

		# Dans tous les cas, �crire les collection s'il y a lieu
		self.collManager.writeCollection()


