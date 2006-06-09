# -*- coding: iso-8859-1 -*-
"""
MetPX Copyright (C) 2004-2006  Environment Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.
"""

"""Gestion des bulletins "AM" """

import bulletinManager, bulletinAm, os, string
import StationParser

__version__ = '2.0'

class bulletinManagerAm(bulletinManager.bulletinManager):
    __doc__ = bulletinManager.bulletinManager.__doc__ + \
    """### Ajout de bulletinManagerAm ###

       Sp�cialisation et implantation du bulletinManager

       Auteur:      Louis-Philippe Th�riault
       Date:        Octobre 2004
    """

    def __init__(self,pathTemp,logger,pathSource=None,\
                    maxCompteur=99999,lineSeparator='\n',extension=':', \
                    pathFichierCircuit=None, SMHeaderFormat=False, \
                    pathFichierStations=None, mapEnteteDelai=None, source=None):

        bulletinManager.bulletinManager.__init__(self,pathTemp,logger, \
                                        pathSource,maxCompteur,lineSeparator,extension,pathFichierCircuit,mapEnteteDelai,source)

        self.initMapEntetes(pathFichierStations)
        self.SMHeaderFormat = SMHeaderFormat

    def __isSplittable(self,rawBulletin):
        """__isSplittable(rawBulletin) -> bool

           Retourne vrai si le bulletin courant contient plus d'un bulletin

           Utilisation:

                D�terminer si un bulletin est s�parable, avant de l'instancier.

           Visibilit�:  Priv�e
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        # Si c'est un bulletin FC/FT, possibilite de plusieurs bulletins,
        # donc d�coupage en fichiers et reste du traitement saute (il
        # sera effectue lors de la prochaine passe.

        # Si une erreur est d�tect�e
        try:
            premierMot = rawBulletin.splitlines()[0].split()[0]
        except Exception, e:
            self.logger.error("Erreur lors du d�coupage d'ent�te\nBulletin:\n%s",rawBulletin)
            return False

        if len(premierMot) == 2 and premierMot in ["FC","FT"]:
            motCle = 'TAF'
            i = 0

            for ligne in rawBulletin.split(self.lineSeparator)[1:]:
                if len(ligne.split()) > 0 and ligne.split()[0] == motCle:
                    i += 1

            return i > 1

        return False

    def __splitBulletin(self,rawBulletin):
        """__splitBulletin(rawBulletin) -> liste bulletins

           Retourne une liste de rawBulletins, s�par�s

           Utilisation:

                S�parer les bulletins FC/FT qui contiennent plus d'un bulletin
                par bulletin.

           Visibilit�:  Priv�e
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        entete = rawBulletin.split(self.lineSeparator)[0]

        listeBulletins = []
        unBulletin = []
        motCle = 'TAF'

        # Les bulletins FC/FT ont une ent�te commune, et le data de chaque
        # station commence par 'TAF'
        for ligne in rawBulletin.split(self.lineSeparator)[1:]:
            if len(ligne.split()) > 0 and ligne.split()[0] == motCle:
                listeBulletins.append(string.join(unBulletin,self.lineSeparator))

                unBulletin = list()
                unBulletin.append(entete)

            unBulletin.append(ligne)

        listeBulletins.append(string.join(unBulletin,self.lineSeparator))
        return listeBulletins[1:]

    def _bulletinManager__generateBulletin(self,rawBulletin):
        __doc__ = bulletinManager.bulletinManager._bulletinManager__generateBulletin.__doc__ + \
        """### Ajout de bulletinManagerAm ###

           Overriding ici pour passer les bons arguments au bulletinAm

           Visibilit�:  Priv�e
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        return bulletinAm.bulletinAm(rawBulletin,self.logger,self.lineSeparator,self.mapEntetes,self.SMHeaderFormat)


    def writeBulletinToDisk(self,unRawBulletin,includeError=False):
        bulletinManager.bulletinManager.writeBulletinToDisk.__doc__ + \
        """### Ajout de bulletin manager AM ###

           Les bulletins en AM peuvent �tres divisibles, donc
           une division est effectu�e et est pass�e � la m�thode
           de la superclasse.

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        if self.__isSplittable(unRawBulletin):
            for rawBull in self.__splitBulletin(unRawBulletin):
                bulletinManager.bulletinManager.writeBulletinToDisk(self,rawBull,includeError=includeError)
        else:
            bulletinManager.bulletinManager.writeBulletinToDisk(self,unRawBulletin,includeError=includeError)

    def reloadMapEntetes(self, pathFichierStations):
        """reloadMapEntetes(pathFichierStations)


           pathFichierStations: String
                                - Chemin d'acc�s vers le fichier de "collection"

           Recharge le fichier d'ent�tes en m�moire.

           Utilisation:

                Pour le rechargement lors d'un SIGHUP.

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        D�cembre 2004
        """
        oldMapEntetes = self.mapEntetes

        try:

            self.initMapEntetes(pathFichierStations)

            self.logger.info("Succ�s du rechargement du fichier d'ent�tes")

        except Exception,e :

            self.mapEntetes = oldMapEntetes

            self.logger.warning("�chec du rechargement du fichier d'ent�tes")

            raise

    def initMapEntetes(self, pathFichierStations):
        """initMapEntetes(pathFichierStations)

           pathFichierStations: String
                                - Chemin d'acces vers le fichier de "collection"

           mapEntetes sera un map contenant les entete a utiliser avec
           quelles stations. La cle se trouve a etre une concatenation des
           2 premieres lettres du bulletin et de la station, la definition
           est une string qui contient l'entete a ajouter au bulletin.

           self.mapEntetes2mapStations sera un map, avec pour chaque entete
           un map associe des stations, dont la valeur sera None.

                Ex.: mapEntetes["SPCZPC"] = "CN52 CWAO "

           Visibilite:  Privee
           Auteur:      Louis-Philippe Theriault
           Date:        Octobre 2004
        """
        if pathFichierStations == None:
            self.mapEntetes = None
            return

        sp = StationParser.StationParser(pathFichierStations)
        sp.parse()

        uneEntete = ""
        uneCle = ""
        unPrefixe = ""
        uneLigneParsee = ""
        self.mapEntetes = {}
        self.mapEntetes2mapStations = {}

        # Construction des 2 map en meme temps
        for key in sp.stations :
            unPrefixe = key[0:2]
            uneEntete = key[2:] + ' '

            # Ajout d'un map vide pour l'entete courante
            if unPrefixe + uneEntete[:-1] not in self.mapEntetes2mapStations:
                self.mapEntetes2mapStations[unPrefixe + uneEntete[:-1]] = {}

            for station in sp.stations[key]:
                uneCle = unPrefixe + station

                self.mapEntetes[uneCle] = uneEntete

                self.mapEntetes2mapStations[unPrefixe + uneEntete[:-1]][station] = None

    def print_debug(self):

        keys = self.mapEntetes.keys()
        keys.sort()
        for key in keys :
            print(" mapEntetes key (%s) = (%s) " % (key,self.mapEntetes[key]) )

        keys = self.mapEntetes2mapStations.keys()
        keys.sort()
        for key in keys :
            print(" mapEntetes2mapStations key (%s) = (%s) " % (key,self.mapEntetes2mapStations[key]) )
