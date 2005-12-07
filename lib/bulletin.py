# -*- coding: UTF-8 -*-
"""D�finition de la classe principale pour les bulletins."""

import time
import string, traceback, sys

__version__ = '2.0'

class bulletinException(Exception):
    """Classe d'exception sp�cialis�s relatives aux bulletins"""
    pass

class bulletin:
    """Classe abstraite regroupant tout les traits communs des bulletins
    quels que soient les protocoles utilis�s. Les m�thodes
    qui ne retournent qu'une exception doivent �tres red�finies
    dans les sous-classes (il s'agit de m�thodes abstraites).

    Le bulletin est repr�sent� � l'interne comme une liste de strings,
    d�coup�s par l'attribut lineSeparator.

    V�rifie l'ent�te du bulletin lors de l'instanciation. Pour sauter
    cette v�rification dans une des classes sp�cialis�es, overrider
    la m�thode par une m�thode vide.

            * Param�tres � passer au constructeur

            stringBulletin          String

                                    - Le bulletin lui-m�me en String

            logger                  Objet log

                                    - Log principal pour les bulletins

            finalLineSeparator      String

                                    - S�parateur utilis� comme fin de ligne
                                      lors de l'appel du get

            lineSeparator           String

                                    - Marqueur utilise pour separer les lignes
                                      du bulletin source

            * Attributs (usage interne seulement)

            errorBulletin           tuple (default=None)

                                    - Est modifi� une fois que le
                                      tra�tement sp�cifique est
                                      effectu�.
                                    - Si une erreur est d�tect�e,
                                      errorBulletin[0] est le message
                                      relatif � l'erreur
                                    - errorBulletin[1:] est laiss�
                                      libre pour la sp�cialisation
                                      de la classe

            bulletin                liste de strings [str]

                                    - Lors d'un getBulletin, le
                                      bulletin est fusionn� avec
                                      lineSeparator comme caract�re
                                      d'union

    Statut: Abstraite
    Auteur: Louis-Philippe Th�riault
    Date:   Octobre 2004
    Modifications: Decembre 2004, Louis-Philippe et Pierre
    """

    def __init__(self,stringBulletin,logger,lineSeparator='\n',finalLineSeparator='\n'):
        self.logger = logger
        self.errorBulletin = None
        self.lineSeparator = lineSeparator
        self.finalLineSeparator = finalLineSeparator
        self.bulletin = self.splitlinesBulletin(stringBulletin.lstrip(lineSeparator))
        self.dataType = None

        # Normalization du header ici (enlever les espaces au d�but et a la fin)
        self.setHeader(self.getHeader().strip())

        # V�rification du header du bulletin
        # pour ne pas l'effectuer, simplement overrider la m�thode
        # dans la classe sp�cialis�e, par une m�thode qui ne fait rien
        self.verifyHeader()

        self.logger.veryverbose("newBulletin: %s" % stringBulletin)

    def splitlinesBulletin(self,stringBulletin):
        """splitlinesBulletin(stringBulletin) -> listeLignes

           stringBulletin       : String
           listeLignes          : Liste

           Retourne la liste de lignes des bulletins. Ne pas utiliser .splitlines()
           (de string) car il y a possibilit� d'un bulletin en binaire.

           Les bulletins binaires (jusqu'� pr�sent) commencent par GRIB/BUFR et
           se terminent par 7777 (la portion binaire).

           Utilisation:

                Pour d�coupage initial du bulletin, ou si l'on ins�re un self.linseparator
                dans le bulletin, pour le red�couper (faire un getBulletin() puis le red�couper).

           Nb.: Les bulletins GRIB/BUFR sont normalis�s en enlevant tout data apr�s le '7777'
                (d�limiteur de fin de portion de data) en en ajoutant un lineSeparator.

           Visibilit�:  Priv�e
           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """
        try:
            estBinaire = False

            # On d�termine si le bulletin est binaire
            for ligne in stringBulletin.splitlines():
                if ligne.lstrip()[:4] == 'BUFR' or ligne.lstrip()[:4] == 'GRIB':
                    # Il faut que le BUFR/GRIB soit au d�but d'une ligne
                    estBinaire = True
                    break

            if estBinaire:
                if stringBulletin.find('GRIB') != -1:
                # Type de bulletin GRIB, d�coupage sp�cifique
                    b = stringBulletin[:stringBulletin.find('GRIB')].split(self.lineSeparator)

                    # Si le dernier token est un '', c'est qu'il y avait
                    # un \n � la fin, et on enl�ve puisque entre 2 �l�ments de la liste,
                    # on ins�re un \n
                    if b[-1] == '':
                        b.pop(-1)

                    b = b + [stringBulletin[stringBulletin.find('GRIB'):stringBulletin.find('7777')+len('7777')]] + ['']

                    return b

                elif stringBulletin.find('BUFR') != -1:
                # Type de bulletin BUFR, d�coupage sp�cifique
                    b = stringBulletin[:stringBulletin.find('BUFR')].split(self.lineSeparator)

                    # Si le dernier token est un '', c'est qu'il y avait
                    # un \n � la fin, et on enl�ve puisque entre 2 �l�ments de la liste,
                    # on ins�re un \n
                    if b[-1] == '':
                        b.pop(-1)

                    b = b + [stringBulletin[stringBulletin.find('BUFR'):stringBulletin.find('7777')+len('7777')]] + ['']

                    return b
            else:
                # Le bulletin n'est pas binaire
                return stringBulletin.split(self.lineSeparator)
        except Exception, e:
            self.logger.exception('Erreur lors du decoupage du bulletin:\n'+''.join(traceback.format_exception(Exception,e,sys.exc_traceback)))
            self.setError('Erreur lors du d�coupage de lignes')
            return stringBulletin.split(self.lineSeparator)

    def replaceChar(self,oldchars,newchars):
        """replaceChar(oldchars,newchars)

           oldchars,newchars    : String

           Remplace oldchars par newchars dans le bulletin. Ne touche pas � la portion Data
           des GRIB/BUFR

           Utilisation:

                Pour des remplacements dans doSpecifiProcessing.

           Visibilit�:  Priv�e
           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """
        for i in range(len(self.bulletin)):
            if self.bulletin[i].lstrip()[:4] != 'GRIB' and self.bulletin[i].lstrip()[:4] != 'BUFR':

                self.bulletin[i] = self.bulletin[i].replace(oldchars,newchars)

    def getBulletin(self,includeError=False,useFinalLineSeparator=True):
        """getBulletin([includeError]) -> bulletin

           bulletin     : String

           includeError:        Bool
                                - Si est � True, inclut l'erreur dans le corps du bulletin

           useFinalLineSeparator:       Bool
                                - Si est a True, utilise le finalLineSeparator

           Retourne le bulletin en texte

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
           Modifications: Decembre 2004, Louis-Philippe et Pierre
        """
        if useFinalLineSeparator:
            marqueur = self.finalLineSeparator
        else:
            marqueur = self.lineSeparator

        if self.errorBulletin == None:
            return string.join(self.bulletin,marqueur)
        else:
            if includeError:
                return ("### " + self.errorBulletin[0] + marqueur + "PROBLEM BULLETIN" + marqueur) + string.join(self.bulletin,marqueur)
            else:
                return string.join(self.bulletin,marqueur)

    def getLength(self):
        """getLength() -> longueur

           longueur     : int

           Retourne la longueur du bulletin avec le lineSeparator

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        return len(self.getBulletin())

    def getHeader(self):
        """getHeader() -> header

           header       : String

           Retourne l'ent�te (premi�re ligne) du bulletin

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        return self.bulletin[0]

    def setHeader(self,header):
        """setHeader(header)

           header       : String

           Assigne l'ent�te du bulletin

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        self.bulletin[0] = header

        self.logger.debug("Nouvelle ent�te du bulletin: %s",header)

    def getStation(self):
        """getStation() -> station

           station      : String

           Retourne la station associ�e au bulletin,
           retourne None si elle est introuvable.

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """


        #print(" ********************* BULLETIN GET STATION APPELE ")

        station = None
        try:
            premiereLignePleine = ""
            deuxiemeLignePleine = ""
            bulletin = self.bulletin

            # Cas special, il faut aller chercher la prochaine ligne pleine
            i = 0
            for ligne in bulletin[1:]:
                i += 1
                premiereLignePleine = ligne
                if len(premiereLignePleine) > 1:
                   if len(bulletin) > i+1 : deuxiemeLignePleine = bulletin[i+1]
                   break

            #print " ********************* header = ", bulletin[0][0:7]
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
                if station == "AAXX" :
                   if deuxiemeLignePleine != "" :
                      station = deuxiemeLignePleine.split()[0]
                   else :
                      station = None

            elif bulletin[0][0:6] in "SRCN40":
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

        except Exception:
            station = None

        if station != None :
           while station[0] == '?' :
                 station = station[1:]
           station = station.split('?')[0]
           if station[-1] == '=' : station = station[:-1]

        self.station = station

        return station

    def getType(self):
        """getType() -> type

           type         : String

           Retourne le type (2 premieres lettres de l'ent�te) du bulletin (SA,FT,etc...)

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        return self.getHeader()[:2]

    def getOrigin(self):
        """getOrigin() -> origine

           origine      : String

           Retourne l'origine (2e champ de l'ent�te) du bulletin (CWAO,etc...)

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        return self.getHeader().split(' ')[1]

    def doSpecificProcessing(self):
        """doSpecificProcessing()

           Modifie le bulletin s'il y a lieu, selon le tra�tement d�sir�.

           Utilisation:

                Inclure les modifications � effectuer sur le bulletin, qui
                sont propres au type de bulletin en question.

           Statut:      Abstraite
           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        raise bulletinException('M�thode non implant�e (m�thode abstraite doSpecificProcessing)')

    def getError(self):
        """getError() -> (TypeErreur)

           Retourne None si aucune erreur d�tect�e dans le bulletin,
           sinon un tuple avec comme premier �l�ment la description
           de l'erreur. Les autres champs sont laiss�s libres

           Visitilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        return self.errorBulletin

    def setError(self,msg):
        """setError(msg)

           msg: String
                - Message relatif � l'erreur

           Flag le bulletin comme erron�. L'utilisation du message est propre
           au type de bulletin.

           Visitilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        if self.errorBulletin == None:
            self.errorBulletin = [msg]


    def getDataType(self):
        """getDataType() -> dataType

           dataType:    String �l�ment de ('BI','AN')
                        - Type de la portion de donn�es du bulletin

           Visitilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """
        if self.dataType != None:
            return self.dataType

        for ligne in self.bulletin:
            if ligne.lstrip()[:4] == 'BUFR' or ligne.lstrip()[:4] == 'GRIB':
                # Il faut que le BUFR/GRIB soit au d�but d'une ligne
                self.dataType = 'BI'
                break

        # Si le bulletin n'est pas binaire, il est alphanum�rique
        if self.dataType == None: self.dataType = 'AN'

        return self.dataType

    def getLogger(self):
        """getLogger() -> objet_logger

           Retourne l'attribut logger du bulletin

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """
        return self.logger

    def setLogger(self,logger):
        """setLogger(logger)

           Assigne l'attribut logger du bulletin

           Visibilit�:  Publique
           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """
        self.logger = logger

    def verifyHeader(self):
        """verifyHeader()

           V�rifie l'ent�te du bulletin et le flag en erreur s'il y a erreur.

           Utilisation:

                Est appel� � l'instance, masquer pour ne pas faire l'appel.

           Visibilit�:  Priv�e
           Auteur:      Louis-Philippe Th�riault
           Date:        Novembre 2004
        """
        header = self.getHeader()

        # remove duplicate spaces
        tokens = header.split()
        header = ' '.join(tokens)
        self.setHeader(header)

        if header=='':
            self.setError('Entete vide')
            return

        # Changement qui doit �tre fait avant de v�rifier l'ent�te,
        # le tandem enl�ve le 'z' ou 'Z' � la fin de l'ent�te
        # s'il y a lieu.
        if header[-1]  in ['z','Z']:
            header = header[:-1]
            self.setHeader(header)

        tokens = header.split()

        if len(tokens) < 3:
            self.setError('Entete non conforme (moins de 3 champs)')
            return

        if len(tokens[2]) > 6: # On enleve les ['z', 'Z'] ou ['utc', 'UTC'] s'ils sont presents dans le groupe JJHHMM
            tokens[2] = tokens[2][0:5]
            self.logger.info("Entete corrigee: le groupe JJHHMM a ete tronque (plus de 6 caracteres)")
            self.setHeader(' '.join(tokens))
            tokens = self.getHeader().split()

        if not tokens[0].isalnum() or len(tokens[0]) not in [4,5,6] or \
           not tokens[1].isalnum() or len(tokens[1]) not in [4,5,6] or \
           not tokens[2].isdigit() or len(tokens[2]) != 6 or \
           not (0 <= int(tokens[2][:2]) <= 31) or not(00 <= int(tokens[2][2:4]) <= 23) or \
           not(00 <= int(tokens[2][4:]) <= 59):

            self.setError('Entete non conforme (format des 3 premiers champs incorrects)')
            return

        if len(tokens) == 3:
            # put an empty BBB
            parts = self.getHeader().split()
            self.setHeader(' '.join(parts) + ' ')
            return

        if not tokens[3].isalpha() or len(tokens[3]) != 3 or tokens[3][0] not in ['C','A','R','P']:
            #self.setError('Entete non conforme (champ BBB incorrect')
            self.logger.info("Entete corrigee: 4ieme champ (et les suivants) enleve du header") 
            parts = self.getHeader().split()
            del parts[3:]
            self.setHeader(' '.join(parts) + ' ')
            return

        if len(tokens) == 5 and \
                (not tokens[4].isalpha() or len(tokens[4]) != 3 or tokens[4][0] not in ['C','A','R','P']):

            #self.setError('Entete non conforme4 (champ BBB no2 incorrect')
            self.logger.info("Entete corrigee: 5ieme champ (et les suivants) enleve du header")
            parts = self.getHeader().split()
            del parts[4:]
            self.setHeader(' '.join(parts))
            return

        if len(tokens) > 5:

            #self.setError('Entete non conforme (plus de 5 champs')
            self.logger.info("Entete corrigee: 6ieme champ (et les suivants) enleve du header")
            parts = self.getHeader().split()
            del parts[5:]
            self.setHeader(' '.join(parts))
            return


if __name__ == '__main__':
 pass
