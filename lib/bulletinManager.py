"""Gestionnaire de bulletins"""

import math, string, os

__version__ = '2.0'

class bulletinManagerException(Exception):
        """Classe d'exception sp�cialis�s relatives au bulletin
managers"""
        pass

class bulletinManager:
	"""Gestionnaire de bulletins g�n�ral. S'occupe de la manipulation
	   des bulletins en tant qu'entit�s, mais ne fait pas de tra�tements
	   � l'int�rieur des bulletins.

	   Un bulletin manager est en charge de la lecture et �criture des
	   bulletins sur le disque."""

	def __init__(self,pathTemp,pathSource=None,pathDest=None,maxCompteur=99999,lineSeparator='\n'):

		self.pathSource = self.__normalizePath(pathSource)
		self.pathDest = self.__normalizePath(pathDest)
		self.pathTemp = self.__normalizePath(pathTemp)
		self.maxCompteur = maxCompteur
		self.compteur = 0
		self.extension = None
		self.lineSeparator = lineSeparator

	def writeBulletinToDisk(self,unRawBulletin):
		"""writeBulletinToDisk(bulletin)

		   �crit le bulletin sur le disque. Le bulletin est une simple string."""
		if self.pathDest == None:
			raise bulletinManagerException("op�ration impossible, pathDest n'est pas fourni")

		if self.compteur > self.maxCompteur:
				self.compteur = 1

		self.compteur += 1

		unBulletin = self.__generateBulletin(unRawBulletin)
		unBulletin.doSpecificProcessing()

		nomFichier = self.__getFileName(unBulletin)

		try:
			unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

		except OSError:
			# Le nom du fichier est invalide, g�n�ration d'un nouveau nom

#				FIXME
#   		                utils.writeLog(log,"*** Erreur : Manipulation du fichier impossible! (Ecriture avec un nom non standard)")
#               	        utils.writeLog(log,"*** Exception: " + str(inst.args[0]))
#                       	utils.writeLog(log,"Bulletin :\n" + unBulletin, sync=True)

                        nomFichier = self.__getFileName(unBulletin,error=True)
			unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

                os.write( unFichier , unBulletin.getBulletin() )
                os.close( unFichier )
                os.chmod(self.pathTemp + nomFichier,0644)

                os.rename( self.pathTemp + nomFichier , self.pathDest + nomFichier )

                       # Le transfert du fichier est un succes FIXME
#                        utils.writeLog(log,'Ecriture du fichier <' + destDir + nomFic + '>')

	def __generateBulletin(self,rawBulletin):
	"""__generateBulletin(rawBulletin) -> objetBulletin

	   Retourne un objetBulletin d'� partir d'un bulletin
	   "brut" """
		raise bulletinManagerException('M�thode non implant�e (m�thode abstraite __generateBulletin)')


	def readBulletinFromDisk(self):
		pass

	def __normalizePath(path):
		"""normalizePath(path) -> path

		   Retourne un path avec un '/' � la fin"""
		if path != None:
		        if path != '' and path[-1] != '/':
		                path = path + '/'

	        return path

	def __getFileName(self,bulletin,error=False):
		"""__getFileName(bulletin[,error]) -> fileName

		   Retourne le nom du fichier pour le bulletin. Si error
		   est � True, c'est que le bulletin a tant� d'�tre �crit
		   et qu'il y a des caract�re "ill�gaux" dans le nom,
		   un nom de fichier "safe" est retourn�."""
		pass

	def __getExtension(self,bulletin):
		"""__getExtension(bulletin) -> extension

		   Retourne l'extension � donner au bulletin."""
		pass
