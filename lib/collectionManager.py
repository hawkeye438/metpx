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

	   collectionParams		Map

		   Map des  param�tres pour la gestion de temps des collections.

		   collectionParams[entete][h_collection]        = Liste d'heures o� la collection devra s'effectuer
		   collectionParams[entete][m_primaire]          = Nombre de minutes apr�s l'heure o� la p�riode
		                                                   de collection primaire se terminera
		   collectionParams[entete][m_suppl]             = Si la p�riode de collection primaire est termin�e,
		                                                   une nouvelle p�riode commence, et elle sera de cette
		                                                   dur�e (une collection pour les retards...)
	   delaiMaxSeq			Int
					- D�lai maximum avant de ne plus "compter" les s�quences.
					- Le programme 'oublie' la s�quence apr�s ce temps,
					  et les bulletins sont flaggu�s en erreur

	   includeAllStn		Bool
					- Si � True, les fichiers de collection qui n'ont pas
					  toutes les stations, compl�tent le data des stations
					  manquantes par une valeur nulle

	   L'�tat du programme est conserv� dans un fichier qui est 
	   dans <r�pertoire_temporaire>/<statusFile>, donc si le programme crash,
	   ce fichier est recharg� et il continue.

           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """

        def __init__(self,pathTemp,logger,pathFichierStations,collectionParams,delaiMaxSeq, \
			includeAllStn,pathSource=None,pathDest=None,lineSeparator='\n', \
			extension=':',statusFile='ncsCollection.status'):

		self.pathTemp = self.__normalizePath(pathTemp)
		self.pathSource = self.__normalizePath(pathSource)
		self.pathDest = self.__normalizePath(pathDest)

		self.collectionParams = collectionParams
		self.delaiMaxSeq = delaiMaxSeq
		self.includeAllStn = includeAllStn

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
			self.mainDataMap = {'collectionMap':{},'sequenceMap':{}}

	def addBulletin(self,rawBulletin,path):
		"""addBulletin(rawBulletin)

		   rawBulletin:	String

		   path:	String
				- Path vers le bulletin

		   Ajoute le bulletin au fichier de collection correspondant. Le bulletin
		   doit absolument �tre destin� pour les collections.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		# Extraction du champ BBB
		bbb = self.getBBB(rawBulletin)

		if bbb == None:
		# Si aucun champ BBB

			# Si le bulletin est destin� a �tre collect� (entete + heure de collection)
			if rawBulletin[:2] in self.collectionParams and \
				int(self.getBullTimestamp(rawBulletin)[2:4]) in self.collectionParams[rawBulletin[:2]]['h_collection']:
				
				if isInCollectionPeriod(rawBulletin):
				# Si dans la p�riode de collection
					self.handleCollection(rawBulletin)
				else:
				# Sinon, retard
					self.handleLateCollection(rawBulletin)

			# Sinon, aucune modification, le bulletin sera d�plac�
			else:
				os.rename(path,self.pathDest + path.split('/')[-1])
		else:
		# Le bulletin a un champ BBB

			# V�rification que ca ne fait pas plus de temps que la limite permise
			if not self.isLate(rawBulletin):
				# Si dans les temps, fetch du prochain token, et modification 
				# de l'ent�te
				#fetch du prochain token dans le map de tokens, cr�ation si aucun token

			else:
			# Sinon, flag du bulletin en erreur
				#G�n�rer l'objet bulletin, flag en erreur, �criture

	def getBBB(self,rawBulletin):
		"""getBBB(rawBulletin) -> champ

		   rawBulletin		String

		   champ		String/None
					- Champ BBB associ� au bulletin
					- None si le bulletin n'a pas
					  de champ BBB

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		if rawBulletin.splitlines()[0].split()[-1].isalpha():
			return rawBulletin.splitlines()[0].split()[-1]
		else:
			return None

	def handleLateCollection(self,rawBulletin):
		"""handleLateCollection(rawBulletin)

		   Le bulletin est en retard, et une collection doit �tre
		   cr��e/continu�e pour le bulletin.

		   Le rawBulletin doit �tre dans la liste des bulletins �
		   collecter.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		# S'il n'y a pas de collections de retard en cours
		if not rawBulletin.splitlines()[0] in self.mainDataMap['collectionMap']:
			entete = ' '.join(rawBulletin.splitlines()[0].split()[:2])
			writeTime = time.time() + ( 60.0 * float(self.collectionParams[rawBulletin[:2]]['m_suppl']))

                        if not entete in self.mapEntetes2mapStations:
                                raise bulletinManagerException("Entete non d�finie dans le fichier de stations")

			self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]] = \
                                bulletinCollection.bulletinCollection(self.logger,self.mapEntetes2mapStations[entete],
                                                                      writeTime,rawBulletin.splitlines()[0])

		# Ajout du bulletin dans la collection
                station = bulletinCollection.bulletinCollection.getStation(rawBulletin)
                data = bulletinCollection.bulletinCollection.getData(rawBulletin)

                self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].addData(station,data)

	def isInCollectionPeriod(self,rawBulletin):
		"""isInCollectionPeriod(rawBulletin) -> bool

		   Retourne vrai si le bulletin est dans la p�riode de collection

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		bullTime = self.getBullTimestamp(rawBulletin)[:-2] + string.zfill(self.collectionParams[rawBulletin[:2]]['m_primaire'0],2)

                now = time.strftime("%d%H%M",time.localtime())
	
                # D�tection si wrap up et correction pour le calcul
                if abs(int(now[:2]) - int(bullTime[:2])) > 10:
                        if now > bullTime:
                        # Si le temps pr�sent est plus grand que le temps du bulletin
                        # (donc si le bulletin est g�n�r� le mois suivant que pr�sentement),
                        # On ajoute une journ�e au temps pr�sent pour faire le temps du bulletin
                                bullTime = str(int(now[:2]) + 1) + bullTime[2:]
                        else:
                        # Contraire (...)
                                now = str(int(bullTime[:2]) + 1) + now[2:]

                # Conversion en nombre de minutes
                nbMinNow = 60 * 24 * int(now[0:2]) + 60 * int(now[2:4]) + int(now[4:])
                nbMinBullTime = 60 * 24 * int(bullTime[0:2]) + 60 * int(bullTime[2:4]) + int(bullTime[4:])

		return nbMinNow <= nbMinBullTime

        def handleCollection(self,rawBulletin):
                """handleCollection(rawBulletin)

                   Le bulletin doit �tre collect�, et une collection doit �tre
                   cr��e/continu�e pour le bulletin.

                   Le rawBulletin doit �tre dans la liste des bulletins �
                   collecter.

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
                """
                if not rawBulletin.splitlines()[0] in self.mainDataMap['collectionMap']:
		# Cr�ation d'une nouvelle collection
			entete = ' '.join(rawBulletin.splitlines()[0].split()[:2])
			writeTime = self.getWriteTime(self.getBullTimestamp(rawBulletin),self.collectionParams[rawBulletin[:2]]['m_primaire'])

			if not entete in self.mapEntetes2mapStations:
				raise bulletinManagerException("Entete non d�finie dans le fichier de stations")

			self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]] = \
				bulletinCollection.bulletinCollection(self.logger,self.mapEntetes2mapStations[entete],
								      writeTime,rawBulletin.splitlines()[0])

		# Ajout du bulletin dans la collection
		station = bulletinCollection.bulletinCollection.getStation(rawBulletin)
		data = bulletinCollection.bulletinCollection.getData(rawBulletin)

		self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].addData(station,data)

	def getWriteTime(self,timeStamp,nb_min)
		"""getWriteTime(timeStamp,nb_min) -> writeTime

		   timeStamp:		String
					- jjhhmm de l'ent�te de la collection

		   nb_min:		Int
					- Nombre de minutes apr�s l'heure jusqu'� ce que l'on doit 
					  effectuer la collection

		   writeTime:		Float
					- Valeur de time.time() lorsque la collection devra �tre ferm�e

		   Gestion des wrap ups. Si un bulletin est re�u � 23h55 le 31 d�cembre 2005, le write
		   time devra �tre g�n�r� en cons�quence.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		mday = int(timeStamp[:2])
		hour = int(timeStamp[2:4])
		min = nb_min

		gmtime = time.gmtime()

		gmyear, gmmonth, gmday = gmtime.tm_mon, gmtime.tm_mon, gmtime.tm_mday

		if mday < gmday:
		# Si le jour du bulletin est plus petit que le jour courant,
		# donc si le bulletin est re�u aujourd'hui et qu'il doit �tre
		# collect� demain, et que demain est le premier jour du mois,
		# on doit faire un wrap du mois/ann�e.
			gmmonth += 1

			if gmmonth == 13:
				gmmonth = 1
				gmyear += 1

		# G�n�ration du temps d'� partir des informations
		return time.mktime((gmyear,gmmonth,mday,hour,min,0,0,0,0))

	def getBullTimestamp(self,rawBulletin):
		"""getBullTimestamp(rawBulletin) -> jjhhmm

		   jjhhmm		String
					- Date de cr�ation du bulletin

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		if rawBulletin.splitlines()[0].split()[-1].isdigit():
			return rawBulletin.splitlines()[0].split()[-1]
		else:
			return rawBulletin.splitlines()[0].split()[-2]

	def writeBulletinToDisk(self, bulletin=None):
		"""Redirection pour masquer celui de la superclasse"""
		self.writeCollection()

	def writeCollection(self):
		"""writeCollection()

		   �crit les fichiers de collections (s'il y a lieu).

		   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		# Parcours des collections, et si la p�riode de collection 
		# est d�pass�e ou si le data de toutes les stations est rentr�,
		# on �crit la collection
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
		if self.getBullTimestamp(rawBulletin)[-2:] == '00':
		# Doit finir (l'heure) par 00

			return  rawBulletin[:2] in self.collectionParams or self.getBBB(rawBulletin) != None
			# Si dans le type de bulletin a collecter OU si champ BBB :True
		else:
			return False

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

	def incrementToken(self,token):
		"""incrementToken(token) -> incremented_token

		   token/incremented_token	String
						-Retourne le token suivant � utiliser

						Ex:
							incrementToken('AAB') -> 'AAC'

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		return token[:-1] + chr(ord(token[-1]) + 1)
		
	def isLate(self,rawBulletin):
		"""isLate(rawBulletin) -> is_late

		   is_late		bool
					- Si l'heure d'arriv�e du bulletin
					  d�passe la limite permise, =True

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		now = time.strftime("%d%H%M",time.localtime())
		bullTime = rawBulletin.splitlines()[0].split()[2]

                # D�tection si wrap up et correction pour le calcul
                if abs(int(now[:2]) - int(bullTime[:2])) > 10:
                        if now > bullTime:
                        # Si le temps pr�sent est plus grand que le temps du bulletin
                        # (donc si le bulletin est g�n�r� le mois suivant que pr�sentement),
                        # On ajoute une journ�e au temps pr�sent pour faire le temps du bulletin
                                bullTime = str(int(now[:2]) + 1) + bullTime[2:]
                        else:
                        # Contraire (...)
                                now = str(int(bullTime[:2]) + 1) + now[2:]

                # Conversion en nombre d'heures
                nbHourNow = 24 * int(now[0:2]) + int(now[2:4])
                nbHourBullTime = 24 * int(bullTime[0:2]) + int(bullTime[2:4]) 

                # Si la diff�rence est plus grande que le maximum permis
                return abs(nbHourNow - nbHourBullTime) > self.delaiMaxSeq
