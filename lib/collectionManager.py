# -*- coding: UTF-8 -*-
"""Gestionnaire de 'collections'"""

import bulletinManager, bulletinManagerAm
import os, time

__version__ = '2.0'

class collectionManager(bulletinManager.bulletinManager):
        __doc__ = bulletinManager.bulletinManager.__doc__ + \
        """### Ajout de collectionManager ###

	   Gestion des fichiers de collection. Les bulletins fournis
	   sont pour but d'�tres collect�s, si les bulletins n'ont
	   pas � �tres collect�s, utiliser un bulletinManager.

	   L'�tat du programme est conserv� dans un fichier qui est 
	   dans <r�pertoire_temporaire>/<statusFile>, donc si le programme crash,
	   ce fichier est recharg� et il continue.

           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """

        def __init__(self,pathTemp,logger,pathFichierStations,pathSource=None, \
                        pathDest=None,lineSeparator='\n',extension=':',statusFile='ncsCollection.status'):

		self.pathTemp = self.__normalizePath(pathTemp)
		self.pathSource = self.__normalizePath(pathSource)
		self.pathDest = self.__normalizePath(pathDest)

		self.lineSeparator = lineSeparator
		self.extension = extension
		self.logger = logger

		self.initMapEntetes(pathFichierStations)
		self.statusFile = statusFile

		# Si le fichier de statut existe d�ja, on le charge en m�moire
		if os.access(self.pathTemp+self.statusFile,os.F_OK):
			self.loadStatusFile(self.pathTemp+self.statusFile)
		else:
		# Cr�ation des structures
			self.collectionMap = {}

	def addBulletin(self,rawBulletin):
		"""addBulletin(rawBulletin)

		   rawBulletin:	String

		   Ajoute le bulletin au fichier de collection correspondant. Le bulletin
		   doit absolument �tre destin� pour les collections.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		pass

	def writeBulletinToDisk(self, bulletin=None):
		"""Redirection pour masquer celui de la superclasse"""
		self.writeCollection()

	def writeCollection(self):
		"""writeCollection()

		   �crit les fichiers de collections (s'il y a lieu).

		   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		pass

	def loadStatusFile(self,pathFicStatus):
		"""loadStatusFile(pathFicStatus)

		   Charge les structures contenues dans le fichiers pathFicStatus.

		   Le fichier est une database gdbm, avec comme �l�ments le 
		   'pickle dump' d'un objet, et la cl� de la DB est le nom
		   de l'objet.

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		pass

	def needsToBeCollected(self,rawBulletin):
		"""needsToBeCollected(rawBulletin) -> bool

		   Retourne TRUE si le bulletin doit �tre collect�,
		   false sinon.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		pass

        def initMapEntetes(self, pathFichierStations):
		"""M�me m�thode que pour le bulletinManagerAm
		"""
		bulletinManagerAm.bulletinManagerAm.initMapEntetes(self, pathFichierStations)		

        def __normalizePath(self,path):
                """normalizePath(path) -> path

                   Retourne un path avec un '/' � la fin"""
                if path != None:
                        if path != '' and path[-1] != '/':
                                path = path + '/'

                return path

	def close(self):
		"""close()

		   Tra�te le reste se l'information s'il y a lieu, puis mets
		   � jour le fichier de statut.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		pass
