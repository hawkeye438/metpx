# -*- coding: UTF-8 -*-
"""Gestionnaire de sockets g�n�rique"""

import socket
import time
import string

__version__ = '2.0'

class socketManagerException(Exception):
	"""Classe d'exception sp�cialis�s relatives au socket managers"""
	pass

class socketManager:
	"""Classe abstraite regroupant toutes les fonctionnalit�es 
	   requises pour un gestionnaire de sockets. Les m�thodes 
	   qui ne retournent qu'une exception doivent �tres red�finies 
	   dans les sous-classes (il s'agit de m�thodes abstraites).
	
	   Les arguments � passer pour initialiser un socketManager sont les
	   suivants:
	
		type		'master','slave' (default='slave')
	
				- Si master est fourni, le programme se 
				  connecte � un h�te distant, si slave,
				  le programme �coute pour une 
				  connection.
	
		localPort	int (default=9999)
	
				- Port local ou se 'bind' le socket.
	
		remoteHost	(str hostname,int port)
	
				- Couple de (hostname,port) pour la 
				  connection. Lorsque timeout secondes
				  est atteint, un socketManagerException
				  est lev�.
	
				- Doit �tre absolument fourni si type='master',
				  et non fourni si type='slave'.
	
		timeout		int (default=None)
				
				- Lors de l'�tablissement d'une connection 
				  � un h�te distant, d�lai avant de dire 
				  que l'h�te de r�ponds pas.
	
		log		Objet Log (default=None)
	
				- Objet de la classe Log
	
	   Auteur:	Louis-Philippe Th�riault
	   Date:	Septembre 2004
	"""
	def __init__(self,logger,type='slave',localPort=9999,remoteHost=None,timeout=None):
		self.type = type
		self.localPort = localPort
		self.remoteHost = remoteHost
		self.timeout = timeout
		self.logger = logger

		self.inBuffer = ""
		self.outBuffer = []
		self.connected = False

		# �tablissement de la connection
		self.__establishConnection()

	def __establishConnection(self):
		"""__establishConnection()

		   �tablit la connection selon la valeur des attributs de l'objet.

		   self.socket sera, apr�s l'ex�cution, la connection.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.logger.writeLog(self.logger.INFO,"Binding du socket avec le port %d",self.localPort)

		# Binding avec le port local
	        while True:
	                try:
	                        self.socket.bind(('',self.localPort))
	                        break
	                except socket.error:
	                        time.sleep(1)

		# KEEP_ALIVE � True, pour que si la connection tombe, la notification
		# soit imm�diate
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)

		# Snapshot du temps
		then = time.time()

		# Tentative de connection
		if self.type == 'master':
			# La connection doit se faire a un h�te distant
	                if self.remoteHost == None:
	                        raise socketManagerException('remoteHost (host,port) n\'est pas sp�cifi�')

			self.logger.writeLog(self.logger.INFO,"Tentative de connection � l'h�te distant %s", str(self.remoteHost) )

	                while True:
	                        if self.timeout != None and (time.time() - then) > self.timeout:
	                                self.socket.close()
	                                raise socketManagerException('timeout d�pass�')

	                        try:
	                                self.socket.connect(self.remoteHost)
	                                break
	                        except socket.error:
	                                time.sleep(5)
		else:
			# En attente de connection
	                self.socket.listen(1)

			self.logger.writeLog(self.logger.INFO,"En attente de connection (mode listen)")

        	        while True:
	                        if self.timeout != None and (time.time() - then) > self.timeout:
	                                self.socket.close()
	                                raise socketManagerException('timeout d�pass�')

        	                try:
	                                conn, self.remoteHost = self.socket.accept()
	                                break
	                        except TypeError:
	                                time.sleep(1)

        	        self.socket.close()
	                self.socket = conn

		# Pour que l'interrogation du buffer ne fasse attendre le syst�me
		self.socket.setblocking(False)

		self.logger.writeLog(self.logger.INFO,"Connection �tablie avec %s",str(self.remoteHost))
		self.connected = True

	def closeProperly(self):
		"""closeProperply() -> ([bulletinsRe�us],nbBulletinsEnvoy�s)

		   [bulletinsRe�us]:	liste de str
					- Retourne les bulletins dans le buffer lors
					  de la fermeture

		   Ferme le socket et finit de tra�ter le socket d'arriv�e et de
		   sortie.

		   Utilisation:

			Tra�ter l'information restante, puis �liminer le socket
			proprement.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		self.logger.writeLog(self.logger.INFO,"Fermeture du socket et copie du reste du buffer")

		# Coupure de la connection
		try:
		        self.socket.shutdown(2)
			self.logger.writeLog(self.logger.DEBUG,"Shutdown du socket: [OK]")
		except Exception, e:
			self.logger.writeLog(self.logger.DEBUG,"Shutdown du socket: [ERREUR]\n %s",str(e))

		# Copie du reste du buffer entrant apr�s la connection
		try:
			self.__syncInBuffer(onlySynch = True)
		except Exception:
			pass

		# Fermeture du socket
                try:
                        self.socket.close()
                except Exception:
                        pass

		self.connected = False

		# Tra�tement du reste du buffer pour d�couper les bulletins
		bulletinsRecus = []
		
		while True:
			bull = self.getNextBulletin()

			if bull != '':
				bulletinsRecus.append(bull)
			else:
				break

		self.logger.writeLog(self.logger.INFO,"Succ�s de la fermeture de la connection socket")
		self.logger.writeLog(self.logger.DEBUG,"Nombre de bulletins dans le buffer : %d",len(bulletinsRecus))

		return (bulletinsRecus, 0)

	def getNextBulletin(self):
		"""getNextBulletin() -> bulletin

		   bulletin	: String

		   Retourne le prochain bulletin re�u, une cha�ne vide sinon.

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if self.connected:
			self.__syncInBuffer()

		status = self.checkNextMsgStatus()

		self.logger.writeLog(self.logger.DEBUG,"Statut du prochain bulletin dans le buffer: %s", status )

		if status ==  'OK':
			(bulletin,longBuffer) = self.unwrapBulletin()

			self.inBuffer = self.inBuffer[longBuffer:]

			return bulletin
		elif status == 'INCOMPLETE':
			return ''
		elif status == 'CORRUPT':
			raise socketManagerException('corruption dans les donn�es','CORRUPT',self.inBuffer)
		else:
			raise socketManagerException('status de buffer inconnu',status,self.inBuffer)

	def sendBulletin(self):
		raise socketManagerException('notDefinedYet')

	def __syncInBuffer(self,onlySynch=False):
		"""__syncInBuffer()

		   onlySynch:	Booleen
				- Si est � True, ne v�rifie pas que la connection fonctionne,
				  Ne fait que syncher le buffer

		   Copie l'information du buffer du socket s'il y a lieu

		   L�ve une exception si la connection est perdue.

		   Utilisation:

			Copier le nouveau data re�u du socket dans l'attribut
			du socketManager.

		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
	        while True:
	                try:
	                        temp = self.socket.recv(32768)

				if temp == '':
					if not onlySynch:
						self.logger.writeLog(self.logger.ERROR,"La connection est bris�e")
						raise socketManagerException('la connection est brisee')

				self.logger.writeLog(self.logger.VERYVERBOSE,"Data re�u: %s",temp)

        	                self.inBuffer = self.inBuffer + temp
	                        break

	                except socket.error, inst:
				if not onlySynch:
		                        if inst.args[0] == 11:
					# Le buffer du socket est vide
		                                break
		                        elif inst.args[0] == 104 or inst.args[0] == 110:
					# La connection est bris�e
						self.logger.writeLog(self.logger.ERROR,"La connection est bris�e")
		                                raise socketManagerException('la connection est brisee')
		                        else:
		                                raise

	def __transmitOutBuffer(self):
		pass

	def wrapBulletin(self,bulletin):
		"""wrapbulletin(bulletin) -> wrappedBulletin

		   bulletin		: String
		   wrappedBulletin	: String
		   
		   Retourne le bulletin avec les entetes/informations relatives
		   au protocole sous forme de string. Le bulletin doit etre un
		   objet Bulletin. Wrap bulletin doit �tre appel� seulement si
		   ce bulletin est s�r d'�tre envoy�, �tant donn� la possibilit�
		   d'un compteur qui doit se suivre.

		   Statut:	Abstraite
		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		raise socketManagerException("M�thode non implant�e (m�thode abstraite wrapBulletin)")

	def unwrapBulletin(self):
		"""unwrapBulletin() -> (bulletin,longBuffer)

		   bulletin	: String
		   longBuffer	: int

		   Retourne le prochain bulletin contenu dans le buffer,
		   apr�s avoir v�rifi� son int�grit�, sans modifier le buffer.
		   longBuffer sera �gal � la longueur de ce que l'on doit enlever
		   au buffer pour que le prochain bulletin soit en premier.

		   Retourne une cha�ne vide s'il n'y a pas assez de donn�es
		   pour compl�ter le prochain bulletin.

		   Statut:	Abstraite
		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		raise socketManagerException("M�thode non implant�e (m�thode abstraite unwrapBulletin)")

	def isConnected(self):
		"""isConnected() -> bool

		   Retourne True si la connection est �tablie.

		   Visibilit�:	Publique
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		return self.connected

	def checkNextMsgStatus(self):
		"""checkNextMsgStatus() -> status

		   status	: String �l�ment de ('OK','INCOMPLETE','CORRUPT')

		   Statut du prochain bulletin dans le buffer.

		   Statut:	Abstraite
		   Visibilit�:	Priv�e
		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
                raise socketManagerException("M�thode non implant�e (m�thode abstraite checkNextMsgStatus)")


