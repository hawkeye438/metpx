"""D�finition de la classe principale pour les bulletins."""

import time
import string

__version__ = '2.0'

class bulletinException(Exception):
        """Classe d'exception sp�cialis�s relatives aux bulletins"""
        pass

class bulletin:
	"""Classe abstraite regroupant tout les traits communs des bulletins
        quels que soient les protocoles utilis�s.Les m�thodes
        qui ne retournent qu'une exception doivent �tres red�finies
 	dans les sous-classes (il s'agit de m�thodes abstraites).

	Le bulletin est repr�sent� � l'interne comme une liste de strings,
	d�coup�s par l'attribut lineSeparator.

		* Param�tres � passer au constructeur

		stringBulletin		String

					- Le bulletin lui-m�me en String

		logger			Objet log

					- Log principal pour les bulletins

		lineSeparator		String

					- S�parateur utilis� comme fin de ligne
					  lors de l'appel du get

		* Attributs (usage interne seulement)

		errorBulletin		tuple (default=None)

					- Est modifi� une fois que le 
					  tra�tement sp�cifique est
					  effectu�. 
					- Si une erreur est d�tect�e,
					  errorBulletin[0] est le message
					  relatif � l'erreur
					- errorBulletin[1:] est laiss�
					  libre pour la sp�cialisation
					  de la classe

		bulletin		liste de strings [str]

					- Lors d'un getBulletin, le 
					  bulletin est fusionn� avec
					  lineSeparator comme caract�re
					  d'union

	Statut:	Abstraite
	Auteur:	Louis-Philippe Th�riault
	Date:	Octobre 2004
  	"""

	def __init__(self,stringBulletin,logger,lineSeparator='\n'):
		self.bulletin = stringBulletin.splitlines()
		self.dataType = None
		self.lineSeparator = lineSeparator
		self.errorBulletin = None
		self.logger = logger

                self.logger.writeLog(self.logger.VERYVERBOSE,"newBulletin: %s",stringBulletin)


	def getBulletin(self):
		"""getBulletin() -> bulletin

		   bulletin	: String

		   Retourne le bulletin en texte

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004"""
		return string.join(self.bulletin,self.lineSeparator)

	def setBulletin(self,bulletin):
                """setBulletin(bulletin) 

                   bulletin     : String

                   Assigne le bulletin en texte

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
		self.bulletin = bulletin.splitlines()

		self.log.writeLog(self.log.VERYVERBOSE,"setBulletin: bulletin = %s",bulletin)

	def getLength(self):
                """getLength() -> longueur

                   longueur	: int

                   Retourne la longueur du bulletin avec le lineSeparator

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
		return len(self.getBulletin())

	def getHeader(self):
		"""getHeader() -> header

		   header	: String

		   Retourne la premi�re ligne du bulletin

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
		return self.bulletin[0]

        def setHeader(self,header):
                """setHeader(header)

                   header       : String

                   Assigne la premi�re ligne du bulletin

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
                self.bulletin[0] = header

		self.logger.writeLog(self.logger.DEBUG,"Nouvelle ent�te du bulletin: %s",header)

	def getType(self):
                """getType() -> type

                   type         : String

                   Retourne le type (2 premieres lettres de l'ent�te) du bulletin (SA,FT,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
                return self.bulletin[0][:2]

	def getOrigin(self):
                """getOrigin() -> origine

                   origine	: String

                   Retourne l'origine (2e champ de l'ent�te) du bulletin (CWAO,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
                return self.bulletin[0].split(' ')[1]

	def doSpecificProcessing(self):
		"""doSpecificProcessing()

		   Modifie le bulletin s'il y a lieu, selon le tra�tement d�sir�.

		   Statut:	Abstraite
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
		raise bulletinException('M�thode non implant�e (m�thode abstraite doSpecificProcessing)')

	def getError(self):
		"""getError()

		   Retourne None si aucune erreur d�tect�e dans le bulletin,
		   sinon un tuple avec comme premier �l�ment la description 
		   de l'erreur. Les autres champs sont laiss�s libres

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004"""
		return self.errorBulletin

