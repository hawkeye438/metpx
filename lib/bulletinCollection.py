# -*- coding: UTF-8 -*-
"""D�finition des collections de bulletins"""

import time
import string, traceback, sys, bulletin

__version__ = '2.0'

class bulletinCollection(bulletin.bulletin):
        __doc__ = bulletin.bulletin.__doc__ + \
	"""### Ajout de bulletinCollection ###

	   Gestion de 'collections' de bulletins.

	   header	String
			-Entete de la collection: TTAAii CCCC JJHHMM <BBB>
			-Le champ BBB est facultatif
			-Facultatif (l'on doit fournir mapCollection si non fourni)

	   mapData	Map
			-Utilis� pour instancier une collection qui est en cours,
			 lors du d�marage du programme, avec des collection � faire
			 suivre
			-Facultatif (l'on doit fournir header si non fourni)
			-'mapCollection':mapCollection
			-'errorBulletin':<type d'erreur>

	   mapCollection	Map
				-'header'=str(header)
				-'stations'=map{'station':str(data)}

	   mapStations	Map
			- Une entree par station doit �tre pr�sente dans le map,
			  et la valeur doit �tre �gale � None

	   Les informations suivantes sont sauv�es dans le fichier de statut:

		self.mapCollection, self.errorBulletin

	   Auteur:	Louis-Philippe Th�riault
  	   Date:	Novembre 2004
  	"""

	def __init__(self,logger,mapStations,header=None,lineSeparator='\n',mapData=None):
                self.logger = logger
		self.lineSeparator = lineSeparator

		if header != None:
		# Cr�ation d'une nouvelle collection
			self.errorBulletin = None

			self.mapCollection = {}
			self.mapCollection['header'] = header
			self.mapCollection['stations'] = {}

                	self.logger.writeLog(self.logger.INFO,"Cr�ation d'une nouvelle collection: %s",header)

		elif mapData != None:
		# Continuit� d'une collection
			self.errorBulletin = mapData['errorBulletin']
			self.mapCollection = mapData['mapCollection']

			self.logger.writeLog(self.logger.INFO,"Chargement d'une collection: %s",self.mapCollection['header'])
			self.logger.writeLog(self.logger.DEBUG,"mapData:\n" + str(mapData))

		else:
			raise bulletin.bulletinException('Aucune information d\'entr�e est fournie (header/mapData)')

	def getPersistentData(self):
		"""getPersistentData() -> Map

		   Retourne un map qui contiendra les informations � passer pour l'instanciation
		   d'une collection, l'�ventualit� de la fermeture du programme.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		return {'mapCollection':self.mapCollection,'errorBulletin':self.errorBulletin}


	def getHeader(self):
		"""getHeader() -> header

		   header	: String

		   Retourne l'ent�te du fichier de collection

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		return self.mapCollection['header']

        def setHeader(self,header):
                """setHeader(header)

                   header       : String

                   Assigne l'ent�te du fichier de collection

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
                self.mapCollection['header'] = header

		self.logger.writeLog(self.logger.DEBUG,"Nouvelle ent�te du bulletin: %s",header)

	def getType(self):
                """getType() -> type

                   type         : String

                   Retourne le type (2 premieres lettres de l'ent�te) du bulletin (SA,FT,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
                return self.mapCollection['header'][:2]

	def getOrigin(self):
                """getOrigin() -> origine

                   origine	: String

                   Retourne l'origine (2e champ de l'ent�te) du bulletin (CWAO,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
                return self.mapCollection['header'].split(' ')[1]


