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

	def __init__(self,connectionManager,pathTemp,pathSource=None,pathDest=None,maxCompteur=99999):

		self.connectionManager = connectionManager
		self.pathSource = bulletinManager.normalizePath(pathSource)
		self.pathDest = bulletinManager.normalizePath(pathDest)
		self.pathTemp = bulletinManager.normalizePath(pathTemp)
		self.maxCompteur = maxCompteur
		self.compteur = 0
		self.bulletinList = []

	def writeBulletinToDisk(self):
		"""writeBulletinToDisk() -> nbBulletinsEcrits

		   nbBulletinsEcrits	: int

		   �crit tous les bulletins dans la liste des bulletins sur le disque"""
		if self.pathDest == None:
			raise bulletinManagerException("op�ration impossible, pathDest n'est pas fourni")

		nbBulletinsEcrits = 0

		while len(self.bulletinList) > 0:
			if self.compteur > self.maxCompteur:
				self.compteur = 1

			self.compteur += 1

			unBulletin = self.bulletinList.pop(0)

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

			nbBulletinsEcrits += 1

                        # Le transfert du fichier est un succes FIXME
#                        utils.writeLog(log,'Ecriture du fichier <' + destDir + nomFic + '>')

		return nbBulletinsEcrits

	def readBulletinFromDisk(self):
		pass

	def normalizePath(path):
		"""normalizePath(path) -> path

		   Retourne un path avec un '/' � la fin"""
	        if path != '' and path[-1] != '/':
	                path = path + '/'

	        return path

	normalizePath = staticmethod(normalizePath)

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
