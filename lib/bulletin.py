# -*- coding: UTF-8 -*-
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
		self.bulletin = self.splitlinesBulletin(stringBulletin.lstrip(lineSeparator))
		self.dataType = None
		self.lineSeparator = lineSeparator
		self.errorBulletin = None
		self.logger = logger

                self.logger.writeLog(self.logger.VERYVERBOSE,"newBulletin: %s",stringBulletin)

	def splitlinesBulletin(self,stringBulletin):
		"""splitlinesBulletin(stringBulletin) -> listeLignes

		   stringBulletin	: String
		   listeLignes		: Liste

		   Retourne la liste de lignes des bulletins. Ne pas utiliser .splitlines()
		   (de string) car il y a possibilit� d'un bulletin en binaire.

		   Les bulletins binaires (jusqu'� pr�sent) commencent par GRIB/BUFR et
		   se terminent par 7777 (la portion binaire).

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		if stringBulletin.find('GRIB') != -1:
		# Type de bulletin GRIB, d�coupage sp�cifique
			b = stringBulletin[:stringBulletin.find('GRIB')].splitlines() + [stringBulletin[stringBulletin.find('GRIB'):stringBulletin.find('7777')+len('7777')]] 
			b_fin = stringBulletin[stringBulletin.find('7777')+len('7777'):].splitlines()

			if len(b_fin) > 0 and b_fin[0] == '':
			# Si le premier �l�ment est un '', c'est qu'il y avait un s�parateur de ligne apr�s le 7777
				return b + b_fin[1:]
			else:
				return b + b_fin

		elif stringBulletin.find('BUFR') != -1:
                # Type de bulletin BUFR, d�coupage sp�cifique
                        b = stringBulletin[:stringBulletin.find('BUFR')].splitlines() + [stringBulletin[stringBulletin.find('BUFR'):stringBulletin.find('7777')+len('7777')]]
                        b_fin = stringBulletin[stringBulletin.find('7777')+len('7777'):].splitlines()

                        if len(b_fin) > 0 and b_fin[0] == '':
                        # Si le premier �l�ment est un '', c'est qu'il y avait un s�parateur de ligne apr�s le 7777
                                return b + b_fin[1:]
                        else:
                                return b + b_fin
		else:
			return stringBulletin.splitlines()

	def replaceChar(self,oldchars,newchars):
		"""replaceChar(oldchars,newchars) 

		   oldchars,newchars	: String

		   Remplace oldchars par newchars dans le bulletin. Ne touche pas � la portion Data
		   des GRIB/BUFR

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		for i in range(len(self.bulletin)):
			if self.bulletin[i].find('GRIB') == -1 and self.bulletin[i].find('BUFR') == -1:

				self.bulletin[i] = self.bulletin[i].replace(oldchars,newchars)

	def getBulletin(self):
		"""getBulletin() -> bulletin

		   bulletin	: String

		   Retourne le bulletin en texte

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		return string.join(self.bulletin,self.lineSeparator)

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

	def doSpecificProcessing(self):
		"""doSpecificProcessing()

		   Modifie le bulletin s'il y a lieu, selon le tra�tement d�sir�.

		   Statut:	Abstraite
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		raise bulletinException('M�thode non implant�e (m�thode abstraite doSpecificProcessing)')

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


	def getDataType(self):
		"""getDataType() -> dataType

		   dataType:	String �l�ment de ('BI','AN')
				- Type de pa portion de donn�es du bulletin

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if self.dataType != None:
			return self.dataType

		bull = self.lineSeparator.join(self.bulletin)

		if bull.find('BUFR') != -1 and bull.find('GRIB') != -1:
			self.dataType = 'BI'
		else:
			self.dataType = 'AN'

		return self.dataType
