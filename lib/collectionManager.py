# -*- coding: UTF-8 -*-
"""Gestionnaire de 'collections'"""

import re, os, time, string, gdbm, pickle
import bulletinManager, bulletinManagerAm, bulletinPlain, bulletinCollection
import fet

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
		   collectionParams[entete][include_all_stn]     = Si oui ou non inclure les stations avec aucun data
		                                                   (et mettre "<station> NIL=")

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
					- La cl� est l'entete du bulletin, l'objet point� est un map
					  vers le prochain token, et l'heure d'effacage du s�quencage

					nb: L'heure est simplement le temps pr�sent + le d�lai max. Fort
					    probable que le s�quencage sera encore en m�moire m�me
					    si le bulletin est flagu� en retard, tant qu'il soit effac�
					    avant de revenir au mois.

	   mainDataMap[sequenceWriteQueue]	Liste
						- Liste de Map, o� 'bull' est l'objet bulletin,
						  et 'writeTime' est l'heure quand il faudra
						  �crire le bulletin

	   L'�tat du programme est conserv� dans un fichier qui est 
	   dans <r�pertoire_temporaire>/<statusFile>, donc si le programme crash,
	   ce fichier est recharg� et il continue. Chaque modification � 
	   self.mainDataMap et ses objets point�s doivent �tres suivies
	   par la sauvegarde dans le fichier de statut (self.saveStatusFile())

           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """

        def __init__(self, \
		logger, \
		pathTemp=fet.FET_DATA + fet.FET_CL, \
		pathFichierCollection = fet.FET_ETC + 'collection_stations.conf', \
		collectParms = None, \
		ficCircuits= fet.FET_ETC + 'header2client.conf' , \
		delai= None, \
		pathSource=fet.FET_DATA + fet.FET_CL, \
		pathDest=None, \
		lineSeparator='\n', \
		extension =':', \
		statusFile='status', \
		opts=fet.options):

		if pathDest != None: # trigger FET
		   collectionParams = collectParms
		   opts.delaiMaxSeq = delai
		   opts.extension = extension 
				    
		self.options = opts
		self.pathTemp = self.__normalizePath(pathTemp)
		self.pathSource = self.__normalizePath(pathSource)
		self.pathDest = self.__normalizePath(pathDest)

                self.maxCompteur = 99999
                self.compteur = 0
		self.statusNeedToBeUpdated = False

		self.lineSeparator = lineSeparator
		self.logger = logger

		self.initMapEntetes(pathFichierCollection)
		self.statusFile = self.pathTemp + statusFile
		self.statusDb = None

		# Init du map des entetes/priorit�s		
                self.champsHeader2Circuit = 'entete:routing_groups:priority:'
		self.initMapCircuit(ficCircuits)

		# Si le fichier de statut existe d�ja, on le charge en m�moire
		if os.access(self.statusFile,os.F_OK):
		  self.loadStatusFile()
		else:
		  # Cr�ation des structures
	 	  self.mainDataMap = {'collectionMap':{},'sequenceMap':{},'sequenceWriteQueue':[]}

	def reload(self):
	   """ re-initialize collection parameters.
		intended to be triggerred when a SIGHUP is received.

	   """
	   reloadMapEntetes(self)

	def addBulletin(self,rawBulletin):
		"""addBulletin(rawBulletin)

		   rawBulletin:	String

		   Ajoute le bulletin au fichier de collection correspondant. Le bulletin
		   doit absolument �tre destin� pour les collections (utiliser 
		   needsToBeCollected). Le bulletin peut ne pas �tre collect� mais aussi
		   simplement 's�quenc�', il sera alors directement �crit sur le disque.

		   Utilisation:

			Envoyer le bulletin pour la collection

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		self.logger.writeLog(self.logger.DEBUG,"Ent�te: %s", rawBulletin.splitlines()[0])

		# Extraction du champ BBB
		bbb = self.getBBB(rawBulletin)

		if bbb == None:
		# Si aucun champ BBB

			# Si le bulletin est destin� a �tre collect� (entete + heure de collection)
			if (rawBulletin[:2] in self.collectionParams) and \
				(int(self.getBullTimestamp(rawBulletin)[2:4]) in self.collectionParams[rawBulletin[:2]]['h_collection']):
			
				try:
	
					if self.isInCollectionPeriod(rawBulletin):
					# Si dans la p�riode de collection
						self.logger.writeLog(self.logger.DEBUG,"Statut: [COLLECTE]")
						self.handleCollection(rawBulletin)
					else:
					# Sinon, retard
						self.logger.writeLog(self.logger.DEBUG,"Statut: [COLLECTE et RETARD]")
						self.handleLateCollection(rawBulletin)

				except bulletinManager.bulletinManagerException, e:
					self.logger.writeLog(self.logger.WARNING,"Erreur lors de la cr�ation de la collection: %s", e.args[0])

		                        # Flag du bulletin en erreur
	                                bull = bulletinPlain.bulletinPlain(rawBulletin,self.logger)
	                                bull.setError(e.args[0])

	                                writeTime = time.time()

		                        # -> Ajout � la queue
		                        self.mainDataMap['sequenceWriteQueue'].append({'writeTime':writeTime,'bull':bull})

			# Sinon, aucune modification, le bulletin sera d�plac�
			# *** Normalement aucun bulletin se rendra ici ***
			else:
				self.logger.writeLog(self.logger.DEBUG,"Statut: [AUCUNE MODIF]")
				bull = bulletinPlain.bulletinPlain(rawBulletin,self.logger)
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

					self.mainDataMap['sequenceMap'][header+bbbType] = \
						{'token':bbbType + 'B','deleteTime':time.time() + 60.0 * 60.0 * float(delaiMaxSeq)}
					newBBB = bbbType + 'A'
				elif bbb == 'COR':
					newBBB = 'COR'
				else:
					newBBB = self.mainDataMap['sequenceMap'][header+bbbType]['token']
					self.mainDataMap['sequenceMap'][header+bbbType]['token'] = self.incrementToken(newBBB)

				self.logger.writeLog(self.logger.DEBUG,"Nouveau champ BBB: %s", newBBB)

				# Changement du champ BBB, g�n�ration du writeTime, et ajout � la queue
				bull = bulletinPlain.bulletinPlain(rawBulletin,self.logger)

				# -> Changement de l'ent�te
				newHeader = ' '.join(bull.getHeader().split()[:-1]) + ' ' + newBBB
				bull.setHeader(newHeader)
				rawBulletin = bull.getBulletin()

				# -> G�n�ration du writeTime
				if newBBB[0] == 'C' and rawBulletin[:2] in self.collectionParams and \
						int(self.getBullTimestamp(rawBulletin)[2:4]) in self.collectionParams[rawBulletin[:2]]['h_collection']:
					writeTime = self.getWriteTime(self.getBullTimestamp(rawBulletin),self.collectionParams[rawBulletin[:2]]['m_primaire'])
				else:
					writeTime = time.time()

			else:
			# Sinon, flag du bulletin en erreur
				bull = bulletinPlain.bulletinPlain(rawBulletin,self.logger)
				bull.setError("Bulletin en retard, delai maximum depasse")
		
				writeTime = time.time()

			# -> Ajout � la queue
			self.mainDataMap['sequenceWriteQueue'].append({'writeTime':writeTime,'bull':bull})

		# MAJ du fichier de statut
		self.statusNeedToBeUpdated = True

	def getBBB(self,rawBulletin):
		"""getBBB(rawBulletin) -> champ

		   rawBulletin		String

		   champ		String/None
					- Champ BBB associ� au bulletin
					- None si le bulletin n'a pas
					  de champ BBB

		   Utilisation:

			Extraire le champ BBB du bulletin

		   Visibilit�:	Priv�e
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

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		# S'il n'y a pas de collections de retard en cours
		if not rawBulletin.splitlines()[0] in self.mainDataMap['collectionMap']:
			entete = ' '.join(rawBulletin.splitlines()[0].split()[:2])
			writeTime = time.time() + ( 60.0 * float(self.collectionParams[rawBulletin[:2]]['m_suppl']))

			# L'ent�te doit �tre d�finie dans le fichier d'ent�tes
                        if not entete in self.mapEntetes2mapStations:
                                raise bulletinManager.bulletinManagerException("Entete non d�finie dans le fichier de stations")

			self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]] = \
                                bulletinCollection.bulletinCollection(self.logger,self.mapEntetes2mapStations[entete],
                                                                      writeTime,rawBulletin.splitlines()[0])

			self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].setTokenIfNoData(None)

			# Ent�te doit inclure l'heure ici
			entete = ' '.join(rawBulletin.splitlines()[0].split()[:3])
                        if not self.mainDataMap['sequenceMap'].has_key(entete + ' ' + 'RR'):
	                        # Pas de s�quence de d�mar�e
                                self.mainDataMap['sequenceMap'][entete + ' ' + 'RR'] = \
					{'token':'RRA','deleteTime':time.time() + 60.0 * 60.0 * float(delaiMaxSeq)}
			
			# G�n�ration du RRx pour la collection en retard
			newBBB = self.mainDataMap['sequenceMap'][entete + ' ' + 'RR']['token']
			self.mainDataMap['sequenceMap'][entete + ' ' + 'RR']['token'] = self.incrementToken(newBBB)

			self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].setBBB(newBBB)

			self.logger.writeLog(self.logger.VERYVERBOSE,"S�quencage de la collection de retard: %s", newBBB)

		# Ajout du bulletin dans la collection
                station = bulletinCollection.bulletinCollection.getStation(rawBulletin)
                data = bulletinCollection.bulletinCollection.getData(rawBulletin)

                self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].addData(station,data)

	def isInCollectionPeriod(self,rawBulletin):
		"""isInCollectionPeriod(rawBulletin) -> bool

		   Retourne vrai si le bulletin est dans la p�riode de collection

		   Utilisation:

			Pour d�terminer si le bulletin est dans la p�riode de
			collection primaire, ou en retard.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		bullTime = self.getBullTimestamp(rawBulletin)[:-2] + string.zfill(self.collectionParams[rawBulletin[:2]]['m_primaire'],2)

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

		return nbMinNow < nbMinBullTime

        def handleCollection(self,rawBulletin):
                """handleCollection(rawBulletin)

                   Le bulletin doit �tre collect�, et une collection doit �tre
                   cr��e/continu�e pour le bulletin.

                   Le rawBulletin doit �tre dans la liste des bulletins �
                   collecter.

		   Visibilit�:	Priv�e
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
                """
                if not rawBulletin.splitlines()[0] in self.mainDataMap['collectionMap']:
		# Cr�ation d'une nouvelle collection
			entete = ' '.join(rawBulletin.splitlines()[0].split()[:2])
			writeTime = self.getWriteTime(self.getBullTimestamp(rawBulletin),self.collectionParams[rawBulletin[:2]]['m_primaire'])

			if not entete in self.mapEntetes2mapStations:
				raise bulletinManager.bulletinManagerException("Entete non d�finie dans le fichier de stations")

			self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]] = \
				bulletinCollection.bulletinCollection(self.logger,self.mapEntetes2mapStations[entete],
								      writeTime,rawBulletin.splitlines()[0])

			# On d�termine si pour le type de bulletin courant l'on veut inclure ou non les stations
			# manquantes pour la collection.
			if self.collectionParams[rawBulletin[:2]]['include_all_stn']:
				self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].setTokenIfNoData(" NIL=")
			else:
				self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].setTokenIfNoData(None)

		# Ajout du bulletin dans la collection
		station = bulletinCollection.bulletinCollection.getStation(rawBulletin)
		data = bulletinCollection.bulletinCollection.getData(rawBulletin)

		self.mainDataMap['collectionMap'][rawBulletin.splitlines()[0]].addData(station,data)

	def getWriteTime(self,timeStamp,nb_min):
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

		   Utilisation:

			Retourne le temps d'�criture, pour les collections, dans leur
			p�riode de collection primaire.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		mday = int(timeStamp[:2])
		hour = int(timeStamp[2:4])
		min = nb_min

		gmtime = time.gmtime()

		gmyear, gmmonth, gmday = gmtime.tm_year, gmtime.tm_mon, gmtime.tm_mday

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

		   Visibilit�:	Priv�e
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

		   G�re ici l'aspect de mise � jour par rapport au temps.

		   Utilisation:

			� �tre appel� � tout les passes, id�alement en un laps
			de temps assez court.

		   Visibilit�:	Publique
		   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		now = time.time()

		# Parcours des collections, et si la p�riode de collection 
		# est d�pass�e ou si le data de toutes les stations est rentr�,
		# on �crit la collection
		keys = self.mainDataMap['collectionMap'].keys()
		for k in keys:
			if now > self.mainDataMap['collectionMap'][k].getWriteTime() or self.mainDataMap['collectionMap'][k].dataIsComplete():
				if self.mainDataMap['collectionMap'][k].dataIsComplete():
					reason = "le data de toutes les stations est rentr�"
				else:
					reason = "la periode de collection est termin�e"

				self.logger.writeLog(self.logger.DEBUG,"�criture de la collection: %s", reason)

				fileName = self.getFileName(self.mainDataMap['collectionMap'][k],compteur=False)

				self.writeToDisk(fileName, self.mainDataMap['collectionMap'][k])

				del self.mainDataMap['collectionMap'][k]

				self.statusNeedToBeUpdated = True

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

				self.statusNeedToBeUpdated = True

				continue

			i += 1

		# Effacement des s�quences
		keys = self.mainDataMap['sequenceMap'].keys()
		for k in keys:
			if now > self.mainDataMap['sequenceMap'][k]['deleteTime']:
				del self.mainDataMap['sequenceMap'][k]
				self.logger.writeLog(self.logger.VERYVERBOSE,"Effacement de la s�quence %s", k)

				self.statusNeedToBeUpdated = True


		# MAJ du fichier de statut 
		if self.statusNeedToBeUpdated:
			self.saveStatusFile()

			self.statusNeedToBeUpdated = False

	def loadStatusFile(self):
		"""loadStatusFile()

		   Charge les structures contenues dans le fichier self.statusFile.

		   Le fichier est une database gdbm, avec comme �l�ments le 
		   'pickle dump' d'un objet, et la cl� de la DB est le nom
		   de l'objet.

		   Utilisation:

			Si le programme a �t� arr�t�, l'�tat est conserv� dans ce fichier 
			et les donn�es seront charg�es.

		   Visibilit�:	Priv�e
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		try:
			self.logger.writeLog(self.logger.INFO,"Chargement du fichier de statut...")

			self.statusDb = gdbm.open(self.statusFile,'cs')

			self.mainDataMap = {}

			self.mainDataMap['sequenceMap'] = pickle.loads(self.statusDb['sequenceMap'])

			self.mainDataMap['sequenceWriteQueue'] = pickle.loads(self.statusDb['sequenceWriteQueue'])

			# Initialisation du logger pour les bulletins
	                for m in self.mainDataMap['sequenceWriteQueue']:
	                        m['bull'].setLogger(self.logger)

			self.mainDataMap['collectionMap'] = pickle.loads(self.statusDb['collectionMap'])

	                # Initialisation du logger pour les bulletins
	                for m in self.mainDataMap['collectionMap']:
	                        self.mainDataMap['collectionMap'][m].setLogger(self.logger)
			
			self.logger.writeLog(self.logger.INFO,"Fichier de status correctement charg�")
		except Exception, e:
			self.logger.writeLog(self.logger.WARNING,"Erreur lors du chargement du fichier de statut: %s", str(e.args))

			self.statusDb = None
			self.mainDataMap = {'collectionMap':{},'sequenceMap':{},'sequenceWriteQueue':[]}

	def saveStatusFile(self):
		"""saveStatusFile()

		   Sauvegarde les informations que l'on doit recharger dans l'�ventualit�
		   d'un arr�t du programme.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		if self.statusDb == None:
			self.statusDb = gdbm.open(self.statusFile,'cs')

		self.statusDb['sequenceMap'] = pickle.dumps(self.mainDataMap['sequenceMap'])

		# Pour chaque bulletin 'pickle' le bulletin, sans l'objet log
		for m in self.mainDataMap['sequenceWriteQueue']:
			m['bull'].setLogger(None)

		self.statusDb['sequenceWriteQueue'] = pickle.dumps(self.mainDataMap['sequenceWriteQueue'])

		# On r�assigne le logger original
                for m in self.mainDataMap['sequenceWriteQueue']:
                        m['bull'].setLogger(self.logger)

                # Pour chaque bulletin 'pickle' le bulletin, sans l'objet log
                for m in self.mainDataMap['collectionMap']:
                        self.mainDataMap['collectionMap'][m].setLogger(None)

		self.statusDb['collectionMap'] = pickle.dumps(self.mainDataMap['collectionMap'])

                # On r�assigne le logger original
		for m in self.mainDataMap['collectionMap']:
                        self.mainDataMap['collectionMap'][m].setLogger(self.logger)

		self.statusDb.reorganize()

	def needsToBeCollected(self,rawBulletin):
		"""needsToBeCollected(rawBulletin) -> bool

		   Retourne TRUE si le bulletin doit �tre collect�,
		   false sinon.

		   Utilisation:

			Pour d�terminer si le bulletin non instanci� doit passer
			par l'�tape de collection. (Appel� par un gateway 
			probablement)

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		try:
			if self.getBullTimestamp(rawBulletin)[-2:] == '00':
			# Doit finir (l'heure) par 00
				bbb = self.getBBB(rawBulletin)

				return  rawBulletin[:2] in self.collectionParams or ( bbb != None and bbb[0] in ['C','R','A'] )
				# Si dans le type de bulletin a collecter OU si champ BBB :True
			else:
				return False
		except:
			# Si quelconque erreur, on retourne Faux
			return False

	def reloadMapEntetes(self, pathFichierStations):
		"""reloadMapEntetes(pathFichierStations)


                   pathFichierStations: String
                                        - Chemin d'acc�s vers le fichier de "collection"

		   Recharge le fichier d'ent�tes en m�moire.

		   Utilisation:

			Pour le rechargement lors d'un SIGHUP.

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	D�cembre 2004
		"""
                oldMapEntetes = self.mapEntetes

                try:

                        self.initMapEntetes(pathFichierStations)

                        self.logger.writeLog(self.logger.INFO,"Succ�s du rechargement du fichier d'ent�tes")

                except Exception,e :

                        self.mapEntetes = oldMapEntetes

                        self.logger.writeLog(self.logger.WARNING,"�chec du rechargement du fichier d'ent�tes")

                        raise


        def initMapEntetes(self, pathFichierStations):
                """initMapEntetes(pathFichierStations)

                   pathFichierStations: String
                                        - Chemin d'acc�s vers le fichier de "collection"

                   mapEntetes sera un map contenant les entete a utiliser avec
                   quelles stations. La cle se trouve a etre une concatenation des
                   2 premieres lettres du bulletin et de la station, la definition
                   est une string qui contient l'entete a ajouter au bulletin.

                   self.mapEntetes2mapStations sera un map, avec pour chaque entete
                   un map associ� des stations, dont la valeur sera None.

                        Ex.: mapEntetes["SPCZPC"] = "CN52 CWAO "

		   Note:

			C'est le m�me code que pour le managerAm.

		   Visibilit�:	Priv�e
                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
                """
                if pathFichierStations == None:
                        self.mapEntetes = None
                        return

                uneEntete = ""
                uneCle = ""
                unPrefixe = ""
                uneLigneParsee = ""
                self.mapEntetes = {}
                self.mapEntetes2mapStations = {}

	        if self.options.collector:
		   pathFichierStations= fet.FET_ETC + 'collection_stations.conf'

                # Construction des 2 map en m�me temps
                for ligne in self.lireFicTexte(pathFichierStations):
                        uneLigneParsee = ligne.split()

                        unPrefixe = uneLigneParsee[0][0:2]
                        uneEntete = uneLigneParsee[0][2:6] + ' ' + uneLigneParsee[0][6:] + ' '

                        # Ajout d'un map vide pour l'ent�te courante
                        if unPrefixe + uneEntete[:-1] not in self.mapEntetes2mapStations:
                                self.mapEntetes2mapStations[unPrefixe + uneEntete[:-1]] = {}

                        for station in uneLigneParsee[1:]:
                                uneCle = unPrefixe + station

                                self.mapEntetes[uneCle] = uneEntete

                                self.mapEntetes2mapStations[unPrefixe + uneEntete[:-1]][station] = None

	def writeToDisk(self,nomFichier,unBulletin):
		"""writeToDisk(nomFichier,unBulletin)

		   �crit l'objet data dans le fichier nomFichier.

		   Utilisation:

			Pour avoir un m�canisme d'�criture de fichiers/gestion
			d'erreur, mais qui ne fait pas le m�me tra�tement que
			bulletinManager.bulletinManager.writeBulletinToDisk().

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		if self.compteur >= self.maxCompteur:
			self.compteur = 0

		self.compteur += 1

                try:
                        unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

                except (OSError,TypeError), e:
                        # Le nom du fichier est invalide, g�n�ration d'un nouveau nom

                        self.logger.writeLog(self.logger.WARNING,"Manipulation du fichier impossible! (Ecriture avec un nom non standard)")
                        self.logger.writeLog(self.logger.EXCEPTION,"Exception: " + ''.join(traceback.format_exception(Exception,e,sys.exc_traceback)))

                        nomFichier = self.getFileName(unBulletin,error=True)
                        unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

                os.write( unFichier , unBulletin.getBulletin(includeError=True) )
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

                   Retourne un path avec un '/' � la fin

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
                if path != None:
                        if path != '' and path[-1] != '/':
                                path = path + '/'

                return path

	def close(self):
		"""close()

		   Tra�te le reste se l'information s'il y a lieu, puis mets
		   � jour le fichier de statut.

		   Utilisation:

			Pour permettre la fermeture 'propre' du manager.

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		self.writeCollection()
		self.saveStatusFile()

		self.logger.writeLog(self.logger.INFO,"Sauvegarde de l'�tat du manager de collections: [OK]")

	def incrementToken(self,token):
		"""incrementToken(token) -> incremented_token

		   token/incremented_token	String
						-Retourne le token suivant � utiliser

						Ex:
							incrementToken('AAB') -> 'AAC'

		   Utilisation:

			Pour g�n�rer le prochain token dans le s�quencage

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		return token[:-1] + chr(ord(token[-1]) + 1)
		
	def isLate(self,rawBulletin):
		"""isLate(rawBulletin) -> is_late

		   is_late		bool
					- Si l'heure d'arriv�e du bulletin
					  d�passe la limite permise, =True

		   Utilisation:

			Pour d�terminer si un bulletin est trop en retard
			pour le s�quencage.

		   Visibilit�:	Priv�e
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
                return abs(nbHourNow - nbHourBullTime) > delaiMaxSeq

	def setCollectionParams(self,colP):
		"""setCollectionParams(self,colP)

		   Doit avoir la m�me signification que dans le fichier de config.

		   Utilisation:

			Recharger cet �l�ment lors d'un �ventuel SIGHUP.

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	D�cembre 2004
		"""
		self.collectionParams = colP
