# -*- coding: UTF-8 -*-
"""D�finition des collections de bulletins"""

import time
import string, traceback, sys

__version__ = '2.0'

class bulletinCollection(bulletin.bulletin):
        __doc__ = bulletin.bulletin.__doc__ + \
	"""### Ajout de bulletinCollection ###

	   Gestion de 'collections' de bulletins.

	   header	String
			-Entete de la collection: TTAAii CCCC JJHHMM <BBB>
			-Le champ BBB est facultatif

	   mapStations	Map
			- Une entree par station doit �tre pr�sente dans le map,
			  et la valeur doit �tre �gale � None

	   Auteur:	Louis-Philippe Th�riault
  	   Date:	Novembre 2004
  	"""

	def __init__(self,header,logger,mapStations,lineSeparator='\n'):
                self.logger = logger
		self.lineSeparator = lineSeparator

		self.errorBulletin = None
                self.logger.writeLog(self.logger.VERYVERBOSE,"Cr�ation d'une nouvelle collection: %s",header)


	def getLength(self):
                """getLength() -> longueur

                   longueur	: int

                   Retourne la longueur du bulletin avec le lineSeparator

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		return len(self.getBulletin())

	def getHeader(self):
		"""getHeader() -> header

		   header	: String

		   Retourne la premi�re ligne du bulletin

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		return self.bulletin[0]

        def setHeader(self,header):
                """setHeader(header)

                   header       : String

                   Assigne la premi�re ligne du bulletin

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
                self.bulletin[0] = header

		self.logger.writeLog(self.logger.DEBUG,"Nouvelle ent�te du bulletin: %s",header)

	def getType(self):
                """getType() -> type

                   type         : String

                   Retourne le type (2 premieres lettres de l'ent�te) du bulletin (SA,FT,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
                return self.bulletin[0][:2]

	def getOrigin(self):
                """getOrigin() -> origine

                   origine	: String

                   Retourne l'origine (2e champ de l'ent�te) du bulletin (CWAO,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
                return self.bulletin[0].split(' ')[1]

	def getError(self):
		"""getError() -> (TypeErreur)

		   Retourne None si aucune erreur d�tect�e dans le bulletin,
		   sinon un tuple avec comme premier �l�ment la description 
		   de l'erreur. Les autres champs sont laiss�s libres

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		return self.errorBulletin

        def setError(self,msg):
                """setError(msg)

		   msg:	String
			- Message relatif � l'erreur

		   Flag le bulletin comme erron�. L'utilisation du message est propre
		   au type de bulletin.


                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		if self.errorBulletin == None:
	                self.errorBulletin = (msg)


