# -*- coding: UTF-8 -*-
"""Gestionnaire de bulletins"""

import math, string, os, bulletinPlain, traceback, sys, time

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
	   bulletins sur le disque. 

	   #FIXME: DOCUMENTATION A COMPLETER SVP"""

	def __init__(self,pathTemp,logger,pathSource=None,pathDest=None,maxCompteur=99999, \
					lineSeparator='\n',extension=':',pathFichierCircuit=None,mapEnteteDelai=None):

		self.logger = logger
		self.pathSource = self.__normalizePath(pathSource)
		self.pathDest = self.__normalizePath(pathDest)
		self.pathTemp = self.__normalizePath(pathTemp)
		self.maxCompteur = maxCompteur
		self.compteur = 0
		self.extension = extension
		self.lineSeparator = lineSeparator
		self.champsHeader2Circuit = 'entete:routing_groups:priority:'
		self.mapEnteteDelai = mapEnteteDelai

		#map du contenu de bulletins en format brut
		#associe a leur arborescence absolue
		self.mapBulletinsBruts = {}

		# Init du map des circuits
		self.initMapCircuit(pathFichierCircuit)

	def writeBulletinToDisk(self,unRawBulletin,compteur=True):
		"""writeBulletinToDisk(bulletin)

		   �crit le bulletin sur le disque. Le bulletin est une simple string."""
		if self.pathDest == None:
			raise bulletinManagerException("op�ration impossible, pathDest n'est pas fourni")

		if self.compteur > self.maxCompteur:
				self.compteur = 0

		self.compteur += 1

		unBulletin = self.__generateBulletin(unRawBulletin)
		unBulletin.doSpecificProcessing()

		# V�rification du temps d'arriv�e
		self.verifyDelay(unBulletin)

		# G�n�ration du nom du fichier
		nomFichier = self.getFileName(unBulletin,compteur=compteur)

		try:
			unFichier = os.open( self.pathTemp + nomFichier , os.O_CREAT | os.O_WRONLY )

		except (OSError,TypeError), e:
			# Le nom du fichier est invalide, g�n�ration d'un nouveau nom

	                self.logger.writeLog(self.logger.WARNING,"Manipulation du fichier impossible! (Ecriture avec un nom non standard)")
			self.logger.writeLog(self.logger.EXCEPTION,"Exception: " + ''.join(traceback.format_exception(Exception,e,sys.exc_traceback)))

                        nomFichier = self.getFileName(unBulletin,error=True,compteur=compteur)
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

	def __generateBulletin(self,rawBulletin):
		"""__generateBulletin(rawBulletin) -> objetBulletin

		   Retourne un objetBulletin d'� partir d'un bulletin
		   "brut".

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		return bulletinPlain.bulletinPlain(rawBulletin,self.logger,self.lineSeparator)

	def readBulletinFromDisk(self,listeRepertoires,listeFichiersDejaChoisis=[],priorite=False):
		"""
                Nom:
                readBulletinFromDisk

                Parametres d'entree:
		-listeRepertoires:
                        les repertoires susceptibles d'etre lus,
                        en format absolu
                -listeFichiersDejaChoisis (optionnel):
                        les fichiers choisis lors du
                        precedent appel
		-priorite (optionnel):
			si priorite = 1 ou True, la methode ordonnancer()
			est executee

                Parametres de sortie:
                -mapBulletinsBruts: 
			dictionnaire du contenu brut des bulletins lus associe
			a leur arborescence absolue

                Description:
                Lit le contenu des fichiers contenus dans le repertoire
		voulu et retourne des bulletins bruts, ainsi que leur
		origine absolue.  Si besoin est, un ordonnancement est effectue
		pour choisir un repertoire prioritaire, de meme qu'une validation
		des fichiers a lire en fonction de ceux deja lus.

                Auteur:
                Pierre Michaud

                Date:
                Novembre 2004
		"""

		try:
			#par defaut, le premier repertoire est choisi
			repertoireChoisi = listeRepertoires[0]

			#determination du repertoire a lire
			if priorite:
                        	repertoireChoisi = self.ordonnancer(listeRepertoires)

			#determination des fichiers a lire
			listeFichiers = self.getListeFichiers(repertoireChoisi,listeFichiersDejaChoisis)
		
			#lecture du contenu des fichiers et
			#chargement de leur contenu
			return self.getMapBulletinsBruts(listeFichiers,repertoireChoisi)

		except:
			self.logger.writeLog(self.logger.ERROR,"(Erreur de chargement des bulletins)")
			raise

	def getMapBulletinsBruts(self,listeFichiers,repertoireChoisi):
                """
                Nom:
		getMapBulletinsBruts

                Parametres d'entree:
                -listeFichiers:
                        les fichiers a lire
		-repertoireChoisi:
			chemin absolu du repertoire a consulter

                Parametres de sortie:
                -mapBulletinsBruts:
                        dictionnaire du contenu brut des bulletins lus associe
                        a leur arborescence absolue

                Description:
                Lit le contenu des fichiers contenus dans le repertoire
                voulu et retourne des bulletins bruts, ainsi que leur
                origine absolue.

                Auteur:
                Pierre Michaud

                Date:
                Novembre 2004
                """

		try:
			#vidange du map de l'etat precedent
			self.mapBulletinsBruts = {}
			#lecture et mapping du contenu brut des fichiers
                        for fichier in listeFichiers:
                                if os.access(repertoireChoisi+'/'+fichier,os.F_OK|os.R_OK) !=1:
                                        raise bulletinManagerException("Fichier inexistant")
                                fic = open(repertoireChoisi+'/'+fichier,'r')
                                rawBulletin = fic.read()
                                fic.close()
                                self.mapBulletinsBruts[repertoireChoisi+'/'+fichier]=rawBulletin

                        return self.mapBulletinsBruts

		except:
                        self.logger.writeLog(self.logger.ERROR,"(Erreur de lecture des bulletins)")
                        raise

	def getListeFichiers(self,repertoire,listeFichiersDejaChoisis):
                """
                Nom:
              	getListeFichiers 

                Parametres d'entree:
                -repertoire: 	
			le repertoire a consulter
			en format absolu
                -listeFichiersDejaChoisis:
			les fichiers choisis lors du
                	precedent appel	

                Parametres de sortie:
                -listeFichiersChoisis: 
			liste des fichiers choisis

                Description:
                Lit les bulletins contenus dans un repertoire choisi selon la priorite
		courante.  Le repertoire contient les bulletins de la priorite courante.
		Les fichiers deja lus ne sont pas relus, ils sont mis de cote.

                Auteur:
                Pierre Michaud

                Date:
                Novembre 2004
                """
		try:
			#lecture du contenu du repertoire
			listeFichiersChoisis = os.listdir(repertoire)

			#validation avec les fichiers deja lus
			i=0
			while True:
				if i>=len(listeFichiersChoisis):
					break
				if listeFichiersChoisis[i] in listeFichiersDejaChoisis:
					listeFichiersChoisis.pop(i)
					continue
				i+=1

			return listeFichiersChoisis
		
		except:
			self.logger.writeLog(self.logger.ERROR,"(Liste de repertoires invalide)")
			return 1

	def ordonnancer(self,listeRepertoires):
                """
                Nom:
		ordonnancer

                Parametres d'entree:
                -listeRepertoires:	les repertoires susceptibles d'etre lus,
					en format absolu

                Parametres de sortie:
                -repertoireChoisi: repertoire contenant les bulletins a lire
				selon la priorite courante, en format absolu

                Description:
		Determine, parmi une liste de repertoires, lequel
		doit etre consulte pour obtenir les bulletins prioritaires.
		Dans la classe de base, la methode ne fait que retourner le
		premier repertoire de la liste passee en parametre.  Donc,
		cette methode doit etre redefinie dans les classes derivees.

                Auteur:
                Pierre Michaud

                Date:
                Novembre 2004
                """
		try:
			sourceChoisie = listeRepertoires[0]
			return sourceChoisie

		except:
			self.logger.writeLog(self.logger.ERROR,"(Liste de repertoires invalide)")

	def effacerFichier(self,nomFichier):
		pass

	def __normalizePath(self,path):
		"""normalizePath(path) -> path

		   Retourne un path avec un '/' � la fin"""
		if path != None:
		        if path != '' and path[-1] != '/':
		                path = path + '/'

	        return path

	def getFileName(self,bulletin,error=False, compteur=True):
		"""getFileName(bulletin[,error, compteur]) -> fileName

		   Retourne le nom du fichier pour le bulletin. Si error
		   est � True, c'est que le bulletin a tent� d'�tre �crit
		   et qu'il y a des caract�re "ill�gaux" dans le nom,
		   un nom de fichier "safe" est retourn�. Si le bulletin semble �tre
		   correct mais que le nom du fichier ne peut �tre g�n�r�,
		   les champs sont mis � ERROR dans l'extension.

		   Si compteur est � False, le compteur n'est pas ins�r� 
		   dans le nom de fichier.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if compteur:
			strCompteur = ' ' + string.zfill(self.compteur, len(str(self.maxCompteur)))
		else:
			strCompteur = ''

		if bulletin.getError() == None and not error:
		# Bulletin normal
			try:
				return (bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')
			except Exception, e:
			# Une erreur est d�tect�e (probablement dans l'extension) et le nom est g�n�r� avec des erreurs
				self.logger.writeLog(self.logger.WARNING,e)
				return ('ERROR_BULLETIN ' + bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error=True)).replace(' ','_')
		elif bulletin.getError() != None and not error:
		# Le bulletin est erronn� mais l'ent�te est "imprimable"
			return ('ERROR_BULLETIN ' + bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')
		else:
		# L'ent�te n'est pas imprimable
			return ('ERROR_BULLETIN ' + 'UNPRINTABLE HEADER' + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')

	def getExtension(self,bulletin,error=False):
		"""getExtension(bulletin) -> extension

		   Retourne l'extension � donner au bulletin. Si error est � True,
		   les champs 'dynamiques' sont mis � 'ERROR'.

		   -TT:		Type du bulletin (2 premieres lettres)
		   -CCCC:	Origine du bulletin (2e champ dans l'ent�te
		   -CIRCUIT:	Liste des circuits, s�par�s par des points, 
				pr�c�d�s de la priorit�.

		   Exceptions possibles:
			bulletinManagerException:	Si l'extension ne peut �tre g�n�r�e 
							correctement et qu'il n'y avait pas
							d'erreur � l'origine.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		newExtension = self.extension

		if not error and bulletin.getError() == None:
			newExtension = newExtension.replace('-TT',bulletin.getType())\
					     	   .replace('-CCCC',bulletin.getOrigin())

			if self.mapCircuits != None:
			# Si les circuits sont activ�s 
			# NB: L�ve une exception si l'ent�te est introuvable
				newExtension = newExtension.replace('-CIRCUIT',self.getCircuitList(bulletin))

			return newExtension
		else:
			# Une erreur est d�tect�e dans le bulletin
			newExtension = newExtension.replace('-TT','ERROR')\
                                                   .replace('-CCCC','ERROR')\
						   .replace('-CIRCUIT','ERROR')

			return newExtension
			
        def lireFicTexte(self,pathFic):
                """
                lireFicTexte(pathFic) -> liste des lignes

                pathFic:        String
                                - Chemin d'acc�s vers le fichier texte

                liste des lignes:       [str]
                                        - Liste des lignes du fichier texte

                Auteur: Louis-Philippe Th�riault
                Date:   Octobre 2004
                """
                if os.access(pathFic,os.R_OK):
                        f = open(pathFic,'r')
                        lignes = f.readlines()
                        f.close
                        return lignes
                else:
                        raise IOError

	def initMapCircuit(self,pathHeader2circuit):
	        """initMapCircuit(pathHeader2circuit)

		   pathHeader2circuit:	String
					- Chemin d'acc�s vers le fichier de circuits

		   Charge le fichier de header2circuit et assigne un map avec comme cle
	           le premier champ de champsHeader2Circuit (premier token est la cle,
	           le reste des tokens sont les cles d'un map contenant les valeurs
	           associes. Le nom du map sera self.mapCircuits et s'il est � None,
		   C'est que l'option est � OFF.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if pathHeader2circuit == None:
		# Si l'option est � OFF
			self.mapCircuits = None
			return

	        self.mapCircuits = {}

		# Test d'existence du fichier
	        try:
	                fic = os.open( pathHeader2circuit, os.O_RDONLY )
	        except Exception:
	                raise bulletinManagerException('Impossible d\'ouvrir le fichier d\'entetes (fichier inaccessible)')
	
	        champs = self.champsHeader2Circuit.split(':')
	
	        lignes = os.read(fic,os.stat(pathHeader2circuit)[6])
	
		# Pour chaque ligne du fichier, on associe l'ent�te avec un map, qui est le nom des autres champs
		# associ�s avec leur valeurs.
	        for ligne in lignes.splitlines():
	                uneLigneSplitee = ligne.split(':')
	
	                self.mapCircuits[uneLigneSplitee[0]] = {}
	
	                try:
	                        for token in range( max( len(champs)-2,len(uneLigneSplitee)-2 ) ):
	                                self.mapCircuits[uneLigneSplitee[0]][champs[token+1]] = uneLigneSplitee[token+1]
	
	                                if len(self.mapCircuits[uneLigneSplitee[0]][champs[token+1]].split(' ')) > 1:
	                                        self.mapCircuits[uneLigneSplitee[0]][champs[token+1]] = self.mapCircuits[uneLigneSplitee[0]][champs[token+1]].split(' ')
	                except IndexError:
	                        raise bulletinManagerException('Les champs ne concordent pas dans le fichier header2circuit',ligne)

	def getMapCircuits(self):
		"""getMapCircuits() -> mapCircuits

		   � utiliser pour que plusieurs instances utilisant la m�me
		   map.

		   Auteur: Louis-Philippe Th�riault
	           Date:   Octobre 2004
		"""
		return self.mapCircuits

        def setMapCircuits(self,mapCircuits):
                """setMapCircuits(mapCircuits)

                   � utiliser pour que plusieurs instances utilisant la m�me
                   map.

                   Auteur: Louis-Philippe Th�riault
                   Date:   Octobre 2004
                """
                self.mapCircuits = mapCircuits
	
	def getCircuitList(self,bulletin):
	        """
		circuitRename(bulletin) -> Circuits

		bulletin:	Objet bulletin

		Circuits:	String
				-Circuits formatt�s correctement pour �tres ins�r�s dans l'extension

		Retourne la liste des circuits pour le bulletin pr�c�d�s de la priorit�, pour �tre ins�r�
		dans l'extension.

                   Exceptions possibles:
                        bulletinManagerException:       Si l'ent�te ne peut �tre trouv�e dans le
							fichier de circuits

		Auteur:	Louis-Philippe Th�riault
		Date:	Octobre 2004
		"""
		entete = ' '.join(bulletin.getHeader().split()[:2])

	        if not self.mapCircuits.has_key(entete):
			bulletin.setError('Entete non trouv�e dans fichier de circuits')
	                raise bulletinManagerException('Entete non trouv�e dans fichier de circuits')

		# Check ici, si ce n'est pas une liste, en faire une liste
		if not type(self.mapCircuits[entete]['routing_groups']) == list:
			self.mapCircuits[entete]['routing_groups'] = [ self.mapCircuits[entete]['routing_groups'] ]
	
	        return self.mapCircuits[entete]['priority'] + '.' + '.'.join(self.mapCircuits[entete]['routing_groups']) + '.'

	def getFinalPath(self,bulletin):
		"""getFinalPath(bulletin) -> path

		   path		String
				- R�pertoire o� le fichier sera �crit

		   bulletin	objet bulletin
				- Pour aller chercher l'ent�te du bulletin

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		# Si le bulletin est erronn�
		if bulletin.getError() != None:
			return self.pathDest.replace('-PRIORITY','ERROR')

		try:
			entete = ' '.join(bulletin.getHeader().split()[:2])
		except Exception:
			self.logger.writeLog(self.logger.ERROR,"Ent�te non standard, priorit� impossible � d�terminer(%s)",bulletin.getHeader())
			return self.pathDest.replace('-PRIORITY','ERROR')

		if self.mapCircuits != None:
			# Si le circuitage est activ�
			if not self.mapCircuits.has_key(entete):
				# Ent�te est introuvable
				self.logger.writeLog(self.logger.ERROR,"Ent�te introuvable, priorit� impossible � d�terminer")
				return self.pathDest.replace('-PRIORITY','ERROR')

			return self.pathDest.replace('-PRIORITY',self.mapCircuits[entete]['priority'])
		else:
			return self.pathDest.replace('-PRIORITY','NONIMPLANTE')

	def getPathSource(self):
		"""getPathSource() -> Path_source 

		   Path_source:		String
					-Path source que contient le manager

		   Auteur:	Louis-Philippe Th�riault
                   Date:	Novembre 2004
		"""
		return self.pathSource

	def verifyDelay(self,unBulletin):
		"""verifyDelay(unBulletin)

		   V�rifie que le bulletin est bien dans les d�lais (si l'option
		   de d�lais est activ�e). Flag le bulletin en erreur si le delai
		   n'est pas respect�.

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if self.mapEnteteDelai == None:
			return

		now = time.strftime("%d%H%M",time.localtime())

		try:
			bullTime = unBulletin.getHeader().split()[2]
			header = unBulletin.getHeader()

			minimum,maximum = None,None

			for k in self.mapEnteteDelai.keys():
			# Fetch de l'intervalle valide dans le map
				if k == header[:len(k)]:
					(minimum,maximum) = self.mapEnteteDelai[k]
					break

			if minimum == None:
			# Si le cas n'est pas d�fini, consid�r� comme correct
				return

		except Exception:
			unBulletin.setError('D�coupage d\'ent�te impossible')
			return

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

		# Calcul de l'interval de validit�
		if not( -1 * abs(minimum) < nbMinNow - nbMinBullTime < maximum ):
			# La diff�rence se situe en dehors de l'intervale de validit�
				self.logger.writeLog(self.logger.WARNING,"D�lai en dehors des limites permises bulletin: "+unBulletin.getHeader()+', heure pr�sente '+now)
				unBulletin.setError('Bulletin en dehors du delai permis')
