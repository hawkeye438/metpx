# -*- coding: UTF-8 -*-
"""D�finition d'une sous-classe pour les bulletins "AM" """

import time
import struct
import string
import curses
import curses.ascii
import bulletin

__version__ = '2.0'

class bulletinAm(bulletin.bulletin):
	__doc__ = bulletin.bulletin.__doc__ + \
	"""
	## Ajouts de bulletinAm ##

	Implantation pour un usage concret de la classe bulletin

		* Informations � passer au constructeur

		mapEntetes		dict (default=None)

					- Si autre que None, le reformattage 
					  d'ent�tes est effectu�
					- Une map contenant les ent�tes � utiliser
					  avec quelles stations. La cl� se trouve �
					  �tre une concat�nation des 2 premi�res 
					  lettres du bulletin et de la station, la 
					  d�finition est une string qui contient 
					  l'ent�te � ajouter au bulletin.

					  Ex.: TH["SPCZPC"] = "CN52 CWAO "
					- Si est � None, aucun tra�tement sur 
					  l'ent�te est effectu�

		SMHeaderFormat		bool (default=False)

					- Si True, ajout de la ligne "AAXX jjhhmm4\\n"
					  � la 2i�me ligne du bulletin

	Auteur:	Louis-Philippe Th�riault
	Date:	Octobre 2004
	"""


	def __init__(self,stringBulletin,logger,lineSeparator='\n',mapEntetes=None,SMHeaderFormat=False):
		bulletin.bulletin.__init__(self,stringBulletin,logger,lineSeparator='\n')
		self.mapEntetes = mapEntetes
		self.SMHeaderFormat = SMHeaderFormat

		self.station = "PASCALCULE"		# None veut dire qu'elle n'est pas trouv�e.
							# C'est pour ca qu'elle est initialis�e comme
							# ca.
		self.station = self.getStation()

		# Print de la station pour le debug
		self.logger.writeLog(logger.DEBUG,"Station: %s",str(self.station))

        def getBulletin(self):
                __doc__ = bulletin.bulletin.getBulletin.__doc__ + \
		"""
		   ### Ajout de bulletinAm ###

                   Si une erreur est d�tect�e, self.errorBulletin[1] 
		   pr�c�de le bulletin.

		   Auteur: 	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if self.errorBulletin == None:
	                return string.join(self.bulletin,self.lineSeparator)
		else:
			return self.errorBulletin[1] + string.join(self.bulletin,self.lineSeparator)

        def getStation(self):
                """getStation() -> station

                   station      : String

                   Retourne la station associ�e au bulletin,
                   retourne None si elle est introuvable.

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		if self.station == "PASCALCULE" and len(self.getHeader().split()[0]) == 2:

        		try:
				station  = ""
			        premiereLignePleine = ""
				bulletin = self.bulletin

			        # Cas special, il faut aller chercher la prochaine ligne pleine
			        for ligne in bulletin[1:]:
			                premiereLignePleine = ligne
	
	                		if len(premiereLignePleine) > 1:
			                        break
	
			        # Embranchement selon les differents types de bulletins
			        if bulletin[0][0:2] == "SA":
			                if bulletin[1].split()[0] in ["METAR","LWIS"]:
			                        station = premiereLignePleine.split()[1]
	                		else:
			                        station = premiereLignePleine.split()[0]
	
			        elif bulletin[0][0:2] == "SP":
			                station = premiereLignePleine.split()[1]
	
			        elif bulletin[0][0:2] in ["SI","SM"]:
			                station = premiereLignePleine.split()[0]
	
			        elif bulletin[0][0:2] in ["FC","FT"]:
			                if premiereLignePleine.split()[1] == "AMD":
			                        station = premiereLignePleine.split()[2]
			                else:
			                        station = premiereLignePleine.split()[1]
	
			        elif bulletin[0][0:2] in ["UE","UG","UK","UL","UQ","US"]:
	                		station = premiereLignePleine.split()[2]
	
			        elif bulletin[0][0:2] in ["RA","MA","CA"]:
			                station = premiereLignePleine.split()[0].split('/')[0]
	
			                if station[0] == '?':
			                        station = station[1:]
			        else:
			                station = None

			except Exception:
				station = None

		        self.station = station
		
		elif self.station == "PASCALCULE" and len(self.getHeader().split()[0]) != 2:
			self.station = "PASDESTATION"

		return self.station


        def doSpecificProcessing(self):
		__doc__ = bulletin.bulletin.doSpecificProcessing.__doc__ + \
                """### Ajout de bulletinAm ###

		   (D�finition de la m�thode abstraite)

                   Modifie les bulletins provenant de stations, transmis 
		   par protocole Am, nomm�s "Bulletins Am"

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		unBulletin = self.bulletin

                # Si le bulletin est � modifier et que l'ent�te doit �tre renom�e
                if self.mapEntetes != None and len(self.getHeader().split()[0]) == 2:
			# Si le premier token est 2 lettres de long

			uneEnteteDeBulletin = None

                        premierMot = self.getType()

			station = self.getStation()			

			# Fetch de l'ent�te
			if station != None:
	                	# Construction de la cle
	                	if premierMot != "SP":
	                        	uneCle = premierMot + station
	                        else:
	                        	uneCle = "SA" + station

	       	                # Fetch de l'entete a inserer
	                        if premierMot in ["CA","MA","RA"]:
	                        	uneEnteteDeBulletin = "CN00 CWAO "
	                        else:
					try:
		                                uneEnteteDeBulletin = self.mapEntetes[uneCle]
					except KeyError:
					# L'ent�te n'a pu �tre trouv�e
						uneEnteteDeBulletin = None

			# Construction de l'ent�te
			if station != None and uneEnteteDeBulletin != None:
	                        if len(unBulletin[0].split()) == 1:
	                                uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + self.getFormattedSystemTime()
	                        elif len(unBulletin[0].split()) == 2:
	                                uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + unBulletin[0].split()[1]
	                        else:
	                                uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + unBulletin[0].split()[1] + ' ' + unBulletin[0].split()[2]

	                	# Assignement de l'entete modifiee
		                self.setHeader(uneEnteteDeBulletin)

		                # Si le bulletin est � modifier et que l'on doit tra�ter les SM/SI
		                # (l'ajout de "AAXX jjhhmm4\n")
		                if self.SMHeaderFormat and self.getType() in ["SM","SI"]:
		                        self.bulletin.insert(1, "AAXX " + self.getHeader().split()[2][0:4] + "4")

			if station == None or uneEnteteDeBulletin == None:
				if station == None:
					self.errorBulletin = ("station non trouv�e","### Pattern de station non trouve ou non specifie" + self.lineSeparator + "ERROR BULLETIN" + self.lineSeparator)

					self.logger.writeLog(self.logger.WARNING,"Pattern de station non trouve")
                                        self.logger.writeLog(self.logger.WARNING,"Bulletin:\n"+self.getBulletin())

                                # L'ent�te n'a pu �tre trouv�e dans le fichier de collection, erreur
                                elif uneEnteteDeBulletin == None:
                                        self.errorBulletin = ("ent�te non trouv�e","### Entete non trouvee dans le fichier de collection" + self.lineSeparator  + "ERROR BULLETIN" + self.lineSeparator)

                                	self.logger.writeLog(self.logger.WARNING,"Station <" + station + "> non trouvee avec prefixe <" + premierMot + ">")
                                        self.logger.writeLog(self.logger.WARNING,"Bulletin:\n"+self.getBulletin())

	def getFormattedSystemTime(self):
	        """getFormattedSystemTime() -> heure

		   heure:	String

		   Retourne une string de l'heure locale du systeme, selon
	           jjhhmm : jour/heures(24h)/minutes

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre
		"""
	        return time.strftime("%d%H%M",time.localtime())

        def setError(self,msg):
		"""### Ajout de bulletinAm ###

		   Le message est ajout� au d�but du bulletin

		   Auteur:	Louis-Philippe Th�riault
		   Date:	Octobre 2004
		"""
		if self.errorBulletin == None:
			self.errorBulletin = (msg,"### " + msg + self.lineSeparator + "ERROR BULLETIN" + self.lineSeparator)
