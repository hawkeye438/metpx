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
  	"""

	def __init__(self,stringBulletin,lineSeparator='\n'):
		self.bulletin = stringBulletin.splitlines()
		self.dataType = None
		self.lineSeparator = lineSeparator
		self.errorBulletin = None

	def getBulletin(self):
		"""getBulletin() -> bulletin

		   bulletin	: String

		   Retourne le bulletin en texte"""
		return string.join(self.bulletin,self.lineSeparator)

	def setBulletin(self,bulletin):
                """setBulletin(bulletin) 

                   bulletin     : String

                   Assigne le bulletin en texte"""
		self.bulletin = bulletin.splitlines()

	def getLength(self):
                """getLength() -> longueur

                   longueur	: int

                   Retourne la longueur du bulletin avec le lineSeparator"""
		return len(self.getBulletin())

	def getHeader(self):
		"""getHeader() -> header

		   header	: String

		   Retourne la premi�re ligne du bulletin"""
		return self.bulletin[0]

        def setHeader(self,header):
                """setHeader(header)

                   header       : String

                   Assigne la premi�re ligne du bulletin"""
                self.bulletin[0] = header

	def getType(self):
                """getType() -> type

                   type         : String

                   Retourne le type (2 premieres lettres de l'ent�te) du bulletin (SA,FT,etc...)"""
                return self.bulletin[0][:2]

	def getSource(self):
                """getSource() -> source

                   source	: String

                   Retourne la source (2e champ de l'ent�te) du bulletin (CWAO,etc...)"""
                return self.bulletin[0].split(' ')[1]

	def doSpecificProcessing(self):
		"""doSpecificProcessing()

		   Modifie le bulletin s'il y a lieu, selon le tra�tement d�sir�."""
		raise bulletinException('M�thode non implant�e (m�thode abstraite doSpecificProcessing)')

	def getError(self):
		"""getError()

		   Retourne None si aucune erreur d�tect�e dans le bulletin,
		   sinon un tuple avec comme premier �l�ment la description 
		   de l'erreur. Les autres champs sont laiss�s libres"""
		return self.errorBulletin

