"""Gestion des bulletins "AM" """

import bulletinManager, bulletinAm, os

__version__ = '2.0'

class bulletinManagerAm(bulletinManager.bulletinManager):
	"""pas d�f"""

	def __init__(self,pathTemp,logger,pathSource=None, \
			pathDest=None,maxCompteur=99999,lineSeparator='\n',extension=':', \
			pathFichierCircuit=None, SMHeaderFormat=False, pathFichierStations=None):

		bulletinManager.bulletinManager.__init__(self,pathTemp,logger, \
						pathSource,pathDest,maxCompteur,lineSeparator,extension)

		self.__initMapEntetes(pathFichierStations)

		self.mapCircuits = None
		self.lineSeparator = lineSeparator
#		self.pathFichierCircuit = pathFichierCircuit		# calcul du map de fichiers circuits
		self.SMHeaderFormat = SMHeaderFormat

	def __isSplittable(self,rawBulletin):
		"""__isSplittable(rawBulletin) -> bool

		   Retourne vrai si le bulletin courant contien plus d'un bulletin"""
        	# Si c'est un bulletin FC/FT, possibilite de plusieurs bulletins,
                # donc d�coupage en fichiers et reste du traitement saute (il
                # sera effectue lors de la prochaine passe
		premierMot = rawBulletin.splitlines()[0].split()[0]

                if len(premierMot) == 2 and premierMot == "FC" or premierMot == "FT":
                	if string.count(string.join(contenuDeBulletin,'\n'),'TAF') > 1:
				return True

		return False

	def __splitBulletin(self,rawBulletin):
                """__isSplittable(rawBulletin) -> bool

		Retourne une liste de rawBulletins, s�par�s """
		entete = rawBulletin.splitlines()[0]

	        listeBulletins = []
	        unBulletin = []

	        for ligne in bulletinOriginal[1:]:
	                if ligne.split()[0] == motCle:
	                        listeBulletins.append(string.join(unBulletin,self.lineSeparator))

        	                unBulletin = list()
	                        unBulletin.append(entete)

        	        unBulletin.append(ligne)
	
	        listeBulletins.append(string.join(unBulletin,self.lineSeparator))

	        return listeBulletins[1:]

        def _bulletinManager__generateBulletin(self,rawBulletin):
		__doc__ = bulletinManager.bulletinManager._bulletinManager__generateBulletin.__doc__ + \
		"""
		### Ajout de bulletinManagerAm ###

		Overriding ici pour passer les bons arguments au bulletinAm
		"""
                return bulletinAm.bulletinAm(rawBulletin,self.logger,self.lineSeparator,self.mapEntetes,self.SMHeaderFormat)


        def writeBulletinToDisk(self,unRawBulletin):
		bulletinManager.bulletinManager.writeBulletinToDisk.__doc__ + \
		"""
		### Ajout de bulletin manager AM ###

		Les bulletins en AM peuvent �tres divisibles, donc
		une division est effectu�e et est pass�e � la m�thode
		de la superclasse.
		"""
		if self.__isSplittable(unRawBulletin):
			for rawBull in self.__splitBulletin(rawBulletin):
				bulletinManager.bulletinManager.writeBulletinToDisk(self,rawBull)
		else:
			bulletinManager.bulletinManager.writeBulletinToDisk(self,unRawBulletin)

	def __initMapEntetes(self, pathFichierStations):
		"""
		__initMapEntetes(pathFichierStations)

		pathFichierStations:	String
					- Chemin d'acc�s vers le fichier de "collection"

            	mapEntetes sera un map contenant les entete a utiliser avec
            	quelles stations. La cle se trouve a etre une concatenation des
            	2 premieres lettres du bulletin et de la station, la definition
	        est une string qui contient l'entete a ajouter au bulletin.
            
            		Ex.: mapEntetes["SPCZPC"] = "CN52 CWAO "
		"""
		if pathFichierStations == None:
			self.mapEntetes = None
			return

	        uneEntete = ""
	        uneCle = ""
	        unPrefixe = ""
	        uneLigneParsee = ""
	        self.mapEntetes = {}

        	for ligne in self.lireFicTexte(pathFicCollection):
	                uneLigneParsee = ligne.split()
	
	                unPrefixe = uneLigneParsee[0][0:2]
	                uneEntete = uneLigneParsee[0][2:6] + ' ' + uneLigneParsee[0][6:] + ' '
	
	                for station in uneLigneParsee[1:]:
	                        uneCle = unPrefixe + station
	
	                        self.mapEntetes[uneCle] = uneEntete

	        


	
