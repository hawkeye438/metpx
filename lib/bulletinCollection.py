# -*- coding: UTF-8 -*-
"""D�finition des collections de bulletins"""

import traceback, sys, bulletin, time

__version__ = '2.0'

class bulletinCollection(bulletin.bulletin):
        __doc__ = bulletin.bulletin.__doc__ + \
	"""### Ajout de bulletinCollection ###

	   Gestion de 'collections' de bulletins.

	   header	String
			-Entete de la collection: TTAAii CCCC JJHHMM <BBB>[autre_data_faisant_partie_de_l'entete]
			-Le champ BBB est facultatif
			-Facultatif (l'on doit fournir mapCollection si non fourni)

	   mapData	Map
			-Utilis� pour instancier une collection qui est en cours,
			 lors du d�marage du programme, avec des collection � faire
			 suivre
			-Facultatif (l'on doit fournir header si non fourni)
			-'mapCollection':mapCollection
			-'errorBulletin':<type d'erreur>

	   mapCollection	Map
				-'header'=str(header)
				-'stations'=map{'station':[str(data)]}

	   mapStations	Map
			- Une entree par station doit �tre pr�sente dans le map,
			  et la valeur doit �tre �gale � None

	   writeTime	float
			- Nombre de sec depuis epoch quand l'�criture du fichier
			  devra �tre faite
			- Utiliser time.time()

	   Les informations suivantes sont sauv�es dans le fichier de statut:

		self.mapCollection, self.errorBulletin, self.writeTime

	   Auteur:	Louis-Philippe Th�riault
  	   Date:	Novembre 2004
  	"""

	def __init__(self,logger,mapStations,writeTime,header=None,lineSeparator='\n',mapData=None):
                self.logger = logger
		self.lineSeparator = lineSeparator
		self.writeTime = writeTime

		self.tokenIfNoData = ' NIL='
		self.bbb = None

		if header != None:
		# Cr�ation d'une nouvelle collection
			self.errorBulletin = None

			self.mapCollection = {}
			self.mapCollection['header'] = header
			self.mapCollection['mapStations'] = mapStations.copy()

                	self.logger.writeLog(self.logger.INFO,"Cr�ation d'une nouvelle collection: %s",header)
			self.logger.writeLog(self.logger.VERYVERBOSE,"writeTime de la collection: %s",time.asctime(time.gmtime(writeTime)))

		elif mapData != None:
		# Continuit� d'une collection
			self.errorBulletin = mapData['errorBulletin']
			self.mapCollection = mapData['mapCollection']
			self.writeTime = mapData['writeTime']
			self.tokenIfNoData = mapData['tokenIfNoData']

			self.logger.writeLog(self.logger.INFO,"Chargement d'une collection: %s",self.mapCollection['header'])
			self.logger.writeLog(self.logger.VERYVERBOSE,"mapData:\n" + str(mapData))

		else:
			raise bulletin.bulletinException('Aucune information d\'entr�e est fournie (header/mapData)')

	def getWriteTime(self):
		"""getWriteTime() -> nb_sec

		   nb_sec	float
				- Temps (en sec depuis epoch) quand la collection devra �tre
				  �crite

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		return self.writeTime

	def dataIsComplete(self):
		"""dataIsComplete() -> True/False

		   Informe si tout le data pour les stations est rentr�. Si tel est le 
		   cas la collection devrait �tre �crite.

		   Auteur:	Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		# Tout le data est rentr� si aucun station est � None 
		return not( None in [self.mapCollection['mapStations'][x] for x in self.mapCollection['mapStations']] )

	def getPersistentData(self):
		"""getPersistentData() -> Map

		   Retourne un map qui contiendra les informations � passer pour l'instanciation
		   d'une collection, l'�ventualit� de la fermeture du programme.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		return {'mapCollection':self.mapCollection,'errorBulletin':self.errorBulletin, \
			'writeTime':self.writeTime, 'tokenIfNoData':self.tokenIfNoData}


	def getHeader(self):
		"""getHeader() -> header

		   header	: String

		   Retourne l'ent�te du fichier de collection

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
		return self.mapCollection['header']

        def setHeader(self,header):
                """setHeader(header)

                   header       : String

                   Assigne l'ent�te du fichier de collection

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
                self.mapCollection['header'] = header

		self.logger.writeLog(self.logger.DEBUG,"Nouvelle ent�te du bulletin: %s",header)

	def getType(self):
                """getType() -> type

                   type         : String

                   Retourne le type (2 premieres lettres de l'ent�te) du bulletin (SA,FT,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
                return self.mapCollection['header'][:2]

	def getOrigin(self):
                """getOrigin() -> origine

                   origine	: String

                   Retourne l'origine (2e champ de l'ent�te) du bulletin (CWAO,etc...)

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
		"""
                return self.mapCollection['header'].split(' ')[1]

	def getBulletin(self,includeError=None):
		"""Utiliser self.getCollection()

		   N'inclut pas l'erreur
		"""
		return self.getCollection()

	def setBBB(self,newBBB):
		"""setBBB(newBBB)

		   Assigne le champ newBBB au bulletin. � �tre utilis� avant
		   getBulletin, pour fin de compatibilit�.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
                header = self.mapCollection['header']

                header = ' '.join(header.split()[:3] + [newBBB])

		self.mapCollection['header'] = header


        def setTokenIfNoData(self,tokenIfNoData):
                """setTokenIfNoData(tokenIfNoData)

                   Assigne le champ tokenIfNoData au bulletin. � �tre utilis� avant
                   getBulletin, pour fin de compatibilit�.

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
                """
                self.tokenIfNoData = tokenIfNoData

	def getCollection(self,tokenIfNoData="self.tokenIfNoData",bbb="self.bbb"):
		"""getCollection(tokenIfNoData,bbb) -> collection

		   tokenIfNoData	String/None
					- Si un �l�ment est � None pour une des stations,
					  au nom de la station est concat�n� ce champ
					- Si est mis � None, la station sans data associ�e
					  ne sera pas comprise dans la collection

					ex: CYUL n'a pas de data

					    "CYUL NIL=" sera la ligne associ�e pour 
					    cette station

		   bbb			String/None
					- Champ BBB qui sera retourn� pour la collection

		   collection		String
					- Fichier de collection, fusionn� en un bulletin

		   Auteur:	Louis-Philipe Th�riault
		   Date:	Novembre 2004
		"""
		# Assignement des valeurs par d�faut dynamiques, on ne peut les placer dans l'ent�te
		if tokenIfNoData == "self.tokenIfNoData":
			tokenIfNoData = self.tokenIfNoData

		if bbb == "self.bbb":
			bbb = self.bbb

		coll = []

		header = self.mapCollection['header']

		# On ins�re/remplace le champ BBB � la fin de l'ent�te
		if bbb != None:
			header = ' '.join(header.split()[:3] + [bbb])

		coll.append(header)
		# Ajout du header � la collection

		keys = self.mapCollection['mapStations'].keys()
		keys.sort()

		for station in keys:
			if self.mapCollection['mapStations'][station] == None:
				# Il n'y a pas de data pour la station courante
				if tokenIfNoData != None:
					coll.append(station+tokenIfNoData)

			else:
				# Ajout du data pour la station
				coll.append(self.mapCollection['mapStations'][station])

		return self.lineSeparator.join(coll) + self.lineSeparator

	def addData(self,station,data):
		"""addData(station,data)

		   station	String
				
		   data		String
				- Data associ� � la station

		   La station doit �tre d�finie dans mapStations, et si elle n'est pas
		   la, une exception sera lev�e. Si du data �tait d�ja associ�,
		   il est �cras�.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
		if not self.mapCollection['mapStations'].has_key(station):
		# La station n'est pas d�finie dans le fichier de stations
			self.logger.writeLog(self.logger.WARNING,\
				"Station inconnue (collection:%s, station:%s)" % (self.mapCollection['header'].splitlines()[0],station) )

			raise Exception("Station non d�finie")

		if self.mapCollection['mapStations'][station] == None:
			self.mapCollection['mapStations'][station] = data
		else:
			self.logger.writeLog(self.logger.WARNING,\
				"Du data est d�ja pr�sent pour la station (collection:%s, station:%s)" % (self.mapCollection['header'].splitlines()[0],station))
			# S'il y a d�ja du data de pr�sent, et que le nouveau data est
			# diff�rent
			if self.mapCollection['mapStations'][station] != data:
				self.mapCollection['mapStations'][station] += self.lineSeparator + data

	def getStation(rawBulletin):
		"""bulletinCollection.getStation(rawBulletin) -> station

		   rawBulletin		String
		  
		   station		String

		   Extrait la station du bulletin brut. Une exception est lev�e si l'on ne sait pas
		   comment extraire la station ou si le bulletin est erronn�.

		   M�thode statique.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Novembre 2004
		"""
                premiereLignePleine = ""

                # Cas special, il faut aller chercher la prochaine ligne pleine
                for ligne in rawBulletin.splitlines()[1:]:
	                premiereLignePleine = ligne

                        if len(premiereLignePleine) > 1 and premiereLignePleine.count('AAXX ') == 0:
	                        break

                # Embranchement selon les differents types de bulletins
                if rawBulletin.splitlines()[0][0:2] == "SA":
	        	if rawBulletin.splitlines()[1].split()[0] in ["METAR","LWIS"]:
	                	return premiereLignePleine.split()[1]
                        else:
                                return premiereLignePleine.split()[0]

                elif rawBulletin.splitlines()[0][0:2] in ["SI","SM"]:
                	return premiereLignePleine.split()[0]

		else:
			raise Exception('Station non trouv�e')

	getStation = staticmethod(getStation)

	def getData(rawBulletin):
                """bulletinCollection.getData(rawBulletin) -> data

                   rawBulletin          String

                   data                 String

		   Extrait la portion de donn�es du bulletin.

                   M�thode statique.

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Novembre 2004
                """
		splittedBulletin = rawBulletin.splitlines()

		# On enl�ve la premi�re ligne (ent�te)
		splittedBulletin.pop(0)

		while splittedBulletin[0] == '' or splittedBulletin[0].find('AAXX') != -1:
			splittedBulletin.pop(0)

		return '\n'.join(splittedBulletin)

        getData = staticmethod(getData)




