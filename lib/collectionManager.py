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

	   mainDataMap			Map
					- Les informations persistentes sont stock�es dans ce
					  map.

	   mainDataMap[collectionMap]	Map
					- La cl� est l'ent�te de la collection, et l'objet point�
					  en est un objet bulletinCollection

	   mainDataMap[sequenceMap]	Map
					- La cl� est l'entete du bulletin, l'objet point� est le 
					  prochain champ bbb pour l'ent�te en question

	   mainDataMap[sequenceWriteQueue]	Liste
						- Liste de Map, o� 'bull' est l'objet bulletin,
						  et 'writeTime' est l'heure quand il faudra
						  �crire le bulletin

	   L'�tat du programme est conserv� dans un fichier qui est 
	   dans <r�pertoire_temporaire>/<statusFile>, donc si le programme crash,
	   ce fichier est recharg� et il continue.

           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """

        def __init__(self,pathTemp,logger,pathFichierStations,collectionParams,delaiMaxSeq, \
			includeAllStn,ficCircuits,pathSource=None,pathDest=None,lineSeparator='\n', \
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

		# Init du map des entetes/priorit�s		
                self.champsHeader2Circuit = 'entete:routing_groups:priority:'
		self.initMapCircuit(pathFichierCircuit)

		# Si le fichier de statut existe d�ja, on le charge en m�moire
		if os.access(self.pathTemp+self.statusFile,os.F_OK):
			self.loadStatusFile(self.pathTemp+self.statusFile)
		else:
		# Cr�ation des structures
			self.mainDataMap = {'collectionMap':{},'sequenceMap':{},'sequenceWriteQueue':[]}

	def addBulletin(self,rawBulletin,path):
		"""addBulletin(rawBulletin)

		   rawBulletin:	String

		   path:	String
				- Path vers le bulletin

		   Ajoute le bulletin au fichier de collection correspondant. Le bulletin
		   doit absolument �tre destin� pour les collections (utiliser 
		   needsToBeCollected). Le bulletin peut ne pas �tre collect� mais aussi
		   simplement 's�quenc�', il sera alors directement �crit sur le disque.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		self.logger.writeLog(self.logger.DEBUG,"Ent�te: %s", rawBulletin.splitlines()[0])

		# Extraction du champ BBB
		bbb = self.getBBB(rawBulletin)

		if bbb == None:
		# Si aucun champ BBB

			# Si le bulletin est destin� a �tre collect� (entete + heure de collection)
			if rawBulletin[:2] in self.collectionParams and \
				int(self.getBullTimestamp(rawBulletin)[2:4]) in self.collectionParams[rawBulletin[:2]]['h_collection']:
				
				if isInCollectionPeriod(rawBulletin):
				# Si dans la p�riode de collection
					self.logger.writeLog(self.logger.DEBUG,"Statut: [COLLECTE]")
					self.handleCollection(rawBulletin)
				else:
				# Sinon, retard
					self.logger.writeLog(self.logger.DEBUG,"Statut: [COLLECTE et RETARD]")
					self.handleLateCollection(rawBulletin)

			# Sinon, aucune modification, le bulletin sera d�plac�
			else:
				self.logger.writeLog(self.logger.DEBUG,"Statut: [AUCUNE MODIF]")
				bull = bulletin.bulletin(rawBulletin,self.logger)
				writeTime = time.time()

				self.mainDataMap['sequenceWriteQueue'].append({'writeTime':writeTime,'bull':bull})
		else:
		# Le bulletin a un champ BBB
			header = ' '.join(rawBulletin.splitlines()[0].strip().split()[:-1]) + ' '
			bbbType = bbb[:-1]

			# V�rification que ca ne fait pas plus de temps que la limite permise
			if not self.isLate(rawBulletin):
				# Si dans les temps, fetch du prochain token, et modification 
				# de l'ent�te
				self.logger.writeLog(self.logger.DEBUG,"Statut: [SEQUENCAGE]")

				if bbb != "COR" and not self.mainDataMap['sequenceMap'].has_key(header+bbbType):
					# Pas de s�quence de d�mar�e
					self.logger.writeLog(self.logger.DEBUG,"Cr�ation de la s�quence: %s", bbbType)

					self.mainDataMap['sequenceMap'][header+bbbType] = bbbType + 'B'
					newBBB = bbbType + 'A'
				elif bbb == "COR":
					# Pas de s�quencage pour les COR
					newBBB = 'COR'
				else:
					newBBB = self.mainDataMap['sequenceMap'][header+bbbType]
					self.mainDataMap['sequenceMap'][header+bbbType] = self.incrementToken(newBBB)

				self.logger.writeLog(self.logger.DEBUG,"Nouveau champ BBB: %s", newBBB)

				# Changement du champ BBB, g�n�ration du writeTime, et ajout � la queue
				bull = bulletin.bulletin(rawBulletin,self.logger)

				# -> Changement de l'ent�te
				newHeader = bull.getHeader().split()[:-1] + ' ' + newBBB
				bull.setHeader(newHeader)
				rawBulletin = bull.getBulletin()

				# -> G�n�ration du writeTime
				if rawBulletin[:2] in self.collectionParams:
					writeTime = self.getWriteTime(self.getBullTimestamp(rawBulletin),self.collectionParams[rawBulletin[:2]]['m_primaire'])
				else:
					writeTime = time.time()

			else:
			# Sinon, flag du bulletin en erreur
				bull = bulletin.bulletin(rawBulletin,self.logger)
				bull.setError("Bulletin en retard, delai maximum depasse")
		
				writeTime = time.time()

			# -> Ajout � la queue
			self.mainDataMap['sequenceWriteQueue'].append({'writeTime':writeTime,'bull':bull})

		# MAJ du fichier de statut
				

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
		now = time.time()

		# Parcours des collections, et si la p�riode de collection 
		# est d�pass�e ou si le data de toutes les stations est rentr�,
		# on �crit la collection
		keys = self.mainDataMap['collectionMap'].keys()
		for k in keys:
			if now > self.mainDataMap['collectionMap'][k].getWriteTime():
				fileName = self.getFileName(self.mainDataMap['collectionMap'][k],compteur=False)

				self.writeToDisk(fileName, self.mainDataMap['collectionMap'][k])

				del self.mainDataMap['collectionMap'][k]

		# Parcours des fichiers non collect�s (s�quencage) puis �criture
		# sur le disque
		i = 0
		while True:
			if i >= len(self.mainDataMap['sequenceWriteQueue']):
				break

			m = self.mainDataMap['sequenceWriteQueue'][i]

			if now > m['writeTime']:
				fileName = self.getFileName(m['bull'],compteur=False)

				self.writeToDisk(fileName,m['bull'])
				self.mainDataMap['sequenceWriteQueue'].pop(i)

				continue

			i += 1


		# MAJ du fichier de statut FIXME

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

	def writeToDisk(self,nomFichier,unBulletin):
		"""writeToDisk(nomFichier,unBulletin)

		   �crit l'objet data dans le fichier nomFichier.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
                try:
                        unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

                except (OSError,TypeError), e:
                        # Le nom du fichier est invalide, g�n�ration d'un nouveau nom

                        self.logger.writeLog(self.logger.WARNING,"Manipulation du fichier impossible! (Ecriture avec un nom non standard)")
                        self.logger.writeLog(self.logger.EXCEPTION,"Exception: " + ''.join(traceback.format_exception(Exception,e,sys.exc_traceback)))

                        nomFichier = self.getFileName(unBulletin,error=True)
                        unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

                os.write( unFichier , unBulletin.getBulletin() )
                os.close( unFichier )
                os.chmod(self.pathTemp + nomFichier,0644)

                # Fetch du path de destination
                pathDest = self.getFinalPath(unBulletin)

                # Si le r�pertoire n'existe pas, le cr�er
                if not os.access(pathDest,os.F_OK):
                        os.mkdir(pathDest, 0755)

                # D�placement du fichier vers le r�pertoire final
                os.rename( self.pathTemp + nomFichier , pathDest + nomFichier )

                # Le transfert du fichier est un succes
                self.logger.writeLog(self.logger.INFO, "Ecriture du fichier <%s>",pathDest + nomFichier)

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
