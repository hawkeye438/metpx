# -*- coding: UTF-8 -*-
"""Gestionnaire de bulletins

   Auteur:      Louis-Philippe Th�riault
   Date:        Octobre 2004
"""
import math, string, os, bulletinPlain, traceback, sys, time
import PXPaths

PXPaths.normalPaths()

__version__ = '2.0'

class bulletinManagerException(Exception):
    """Classe d'exception sp�cialis�s relatives au bulletin managers"""
    pass

class bulletinManager:
    """Gestionnaire de bulletins g�n�ral. S'occupe de la manipulation
       des bulletins en tant qu'entit�s, mais ne fait pas de tra�tements
       � l'int�rieur des bulletins.

       pathTemp             path

                            - Obligatoire, doit �tre sur le m�me file system que
                              pathSource/pathDest

       pathSource           path

                            R�pertoire d�ou les fichiers sont lus.

       pathDest             path
                            R�pertoire ou les fichiers sont �crits.
                            en mode use_pds pathDest est necessaire.
                            Si le manager ne fait qu'�crire les fichier sur le disque,
                            seul pathDest est n�cessaire.
                            en mode fet, le fichier va etre directement ing�r�

       mapEnteteDelai       map

                            - Gestion pour la validit� des fichiers concernant les d�lais.

                            - Map d'ent�tes pointant sur des tuples, avec comme champ [0] le nombre de minutes
                              avant, et champ [1] le nombre de minutes apr�s, pour que le bulletin soit valide.

                            Nb: Mettre � None pour d�sactiver la fonction de validit� des fichiers
                                concernant les d�lais.

                            Ex: mapEnteteDelai = { 'CA':(5,20),'WO':(20,40)}

       SMHeaderFormat       Bool

                            - Ajout du champ "AAXX jjhh4\\n" aux bulletins SM/SI.

       ficCollection        path

                            - Path vers le fichier de collection correctement formatte
                              Doit etre mis a None si on veut garder les bulletins
                              intouch�s.

                            Nb: Mettre a None pour desactiver cette fonction

       pathFichierCircuit   path

                            - Remplace le -CIRCUIT dans l'extension par la liste de circuits
                              s�par�s par un point.

                            Nb: Mettre a None pour desactiver cette fonction

       maxCompteur          Int

                            - Compteur � ajouter � la fin des fichiers (dans le nom du fichier)

       Un bulletin manager est en charge de la lecture et �criture des
       bulletins sur le disque.

    """

    def __init__(self,
            pathTemp,
            logger,
            pathSource=None,
            pathDest=None,
            maxCompteur=99999, \
            lineSeparator='\n',
            extension=':',
            pathFichierCircuit=None,
            mapEnteteDelai=None,
            use_pds=0,
            source=None):

        self.logger = logger
        self.pathSource = self.__normalizePath(pathSource)
        self.pathDest = self.__normalizePath(pathDest)
        self.pathTemp = self.__normalizePath(pathTemp)
        self.maxCompteur = maxCompteur
        # FIXME: this should be read from a config file, haven't understood enough yet.
        self.use_pds = use_pds
        self.compteur = 0
        self.extension = extension
        self.lineSeparator = lineSeparator
        self.mapEnteteDelai = mapEnteteDelai
        self.source = source

        #map du contenu de bulletins en format brut
        #associe a leur arborescence absolue
        self.mapBulletinsBruts = {}

        # Init du map des circuits
        self.initMapCircuit(pathFichierCircuit)


    def effacerFichier(self,nomFichier):
        try:
            os.remove(nomFichier)
        except:
            self.logger.error("(BulletinManager.effacerFichier(): Erreur d'effacement d'un bulletin)")
            raise

    def writeBulletinToDisk(self,unRawBulletin,compteur=True,includeError=True):
        """writeBulletinToDisk(bulletin [,compteur,includeError])

           unRawBulletin        String

                                - Le unRawBulletin est un string, et il est instanci�
                                  en bulletin avane l'�criture sur le disque
                                - Les modifications sont effectu�es via
                                  unObjetBulletin.doSpecificProcessing() avant
                                  l'�criture

           compteur             Bool

                                - Si � True, le compteur est inclut dans le nom du fichier

           includeError         Bool

                                - Si � True et que le bulletin est erronn�, le message
                                  d'erreur est ins�r� au d�but du bulletin

           Utilisation:

                   �crit le bulletin sur le disque. Le bulletin est une simple string.

        """

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
        if not self.use_pds:
            nomFichier = nomFichier + ':' + time.strftime( "%Y%m%d%H%M%S", time.gmtime(time.time()) )

        tempNom = self.pathTemp + nomFichier
        try:
            unFichier = os.open( tempNom , os.O_CREAT | os.O_WRONLY )

        except (OSError,TypeError), e:
            # Le nom du fichier est invalide, g�n�ration d'un nouveau nom

            self.logger.warning("Manipulation du fichier impossible! (Ecriture avec un nom non standard)")
            self.logger.error("Exception: " + ''.join(traceback.format_exception(Exception,e,sys.exc_traceback)))

            nomFichier = self.getFileName(unBulletin,error=True,compteur=compteur)
            tempNom = self.pathTemp + nomFichier
            unFichier = os.open( tempNom, os.O_CREAT | os.O_WRONLY )

        os.write( unFichier , unBulletin.getBulletin(includeError=includeError) )
        os.close( unFichier )
        os.chmod(tempNom,0644)

        if self.use_pds:
            pathDest = self.getFinalPath(unBulletin)

            if not os.access(pathDest,os.F_OK):
                os.mkdir(pathDest, 0755)

            os.rename( tempNom , pathDest + nomFichier )
            self.logger.info("Ecriture du fichier <%s>",pathDest + nomFichier)
        else:
            entete = ' '.join(unBulletin.getHeader().split()[:2])

            # MG use filename for Pattern File Matching from source ...  (As Proposed by DL )
            if self.source.patternMatching:
                if not self.source.fileMatchMask(nomFichier) :
                    self.logger.warning("Bulletin file rejected because of RX mask: " + nomFichier)
                    os.unlink(tempNom)
                    return

                """
                transfo = self.source.getTransformation(nomFichier)
                if transfo:
                    newNames = Transformations.transfo(tempNom)

                    for name in newNames:
                        self.source.ingestor.ingest()
                """


            if self.mapCircuits.has_key(entete):
                clist = self.mapCircuits[entete]['routing_groups']
            else:
                clist = []

            if self.source.clientsPatternMatching:
                clist = self.source.ingestor.getMatchingClientNamesFromMasks(nomFichier, clist)

            #fet.directIngest( nomFichier, clist, tempNom, self.logger )
            self.source.ingestor.ingest(tempNom, nomFichier, clist)

            os.unlink(tempNom)


    def __generateBulletin(self,rawBulletin):
        """__generateBulletin(rawBulletin) -> objetBulletin

           Retourne un objetBulletin d'� partir d'un bulletin
           "brut".

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
                precedent appel, en format absolu
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
            map = self.getMapBulletinsBruts(listeFichiers)

            #return self.getMapBulletinsBruts(listeFichiers)
            return map

        except Exception, e:
            self.logger.error("bulletinManager.readBulletinFromDisk: Erreur de chargement des bulletins: %s",str(e.args))
            raise

    def getMapBulletinsBruts(self,listeFichiers):
        """
        Nom:
        getMapBulletinsBruts

        Parametres d'entree:
        -listeFichiers:
                les fichiers a lire
                en format absolu

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
                if os.access(fichier,os.F_OK|os.R_OK) !=1:
                    #raise bulletinManagerException("Fichier inexistant: " + fichier)
                    continue
                fic = open(fichier,'r')
                rawBulletin = fic.read()
                fic.close()
                self.mapBulletinsBruts[fichier]=rawBulletin

            return self.mapBulletinsBruts

        except Exception, e:
            self.logger.error("bulletinManager.getMapBulletinsBruts(): Erreur de lecture des bulletins: %s",str(e.args))
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
                precedent appel en format absolu

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
            listeFichiers = os.listdir(repertoire)

            #transformation en format absolu
            liste = []
            for fichier in listeFichiers:
            #seuls les fichiers avec les bonnes
            #permissions sont conserves
                if fichier[0] == '.':
                    continue
                data = repertoire+'/'+fichier
                liste.append(data)

            #listeFichiers = liste

            #Retrait des fichiers deja choisis
            listeFichiersChoisis = []
            listeFichiersChoisis = [fichier for fichier in liste if fichier not in listeFichiersDejaChoisis]

            return listeFichiersChoisis

        except Exception, e:
            self.logger.error("bulletinManager.getListeFichiers(): Liste des repertoires invalide: %s",str(e.args))
            return 1

    def ordonnancer(self,listeRepertoires):
        """
        Nom:
        ordonnancer

        Parametres d'entree:
        -listeRepertoires:      les repertoires susceptibles d'etre lus,
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
            self.logger.error("(Liste de repertoires invalide)")

    def getListeNomsFichiersAbsolus(self):
        return self.mapBulletinsBruts.keys()

    def __normalizePath(self,path):
        """normalizePath(path) -> path

           Retourne un path avec un '/' � la fin
        """

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

           Utilisation:

                G�n�rer le nom du fichier pour le bulletin concern�.
        """
        if compteur or bulletin.getError() != None or error:
            compteur = True
            strCompteur = ' ' + string.zfill(self.compteur, len(str(self.maxCompteur)))
        else:
            strCompteur = ''

        if bulletin.getError() == None and not error:
        # Bulletin normal
            try:
                return (bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')
            except Exception, e:
            # Une erreur est d�tect�e (probablement dans l'extension) et le nom est g�n�r� avec des erreurs

                # Si le compteur n'a pas �t� calcul�, c'est que le bulletin �tait correct,
                # mais si on est ici dans le code, c'est qu'il y a eu une erreur.
                if strCompteur == '':
                    strCompteur = ' ' + string.zfill(self.compteur, len(str(self.maxCompteur)))

                self.logger.warning(e)
                return ('PROBLEM_BULLETIN ' + bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error=True)).replace(' ','_')

        elif bulletin.getError() != None and not error:
            self.logger.warning("Le bulletin est erronn� " + bulletin.getError()[0] )
            return ('PROBLEM_BULLETIN ' + bulletin.getHeader() + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')
        else:
            self.logger.warning("L'ent�te n'est pas imprimable" )
            return ('PROBLEM_BULLETIN ' + 'UNPRINTABLE HEADER' + strCompteur + self.getExtension(bulletin,error)).replace(' ','_')

    def getExtension(self,bulletin,error=False):
        """getExtension(bulletin) -> extension

           Retourne l'extension � donner au bulletin. Si error est � True,
           les champs 'dynamiques' sont mis � 'PROBLEM'.

           -TT:         Type du bulletin (2 premieres lettres)
           -CCCC:       Origine du bulletin (2e champ dans l'ent�te
           -CIRCUIT:    Liste des circuits, s�par�s par des points,
                        pr�c�d�s de la priorit�.

           Exceptions possibles:
                bulletinManagerException:       Si l'extension ne peut �tre g�n�r�e
                                                correctement et qu'il n'y avait pas
                                                d'erreur � l'origine.

           Utilisation:

                G�n�rer la portion extension du nom du fichier.
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
            newExtension = newExtension.replace('-TT','PROBLEM')\
                                       .replace('-CCCC','PROBLEM')\
                                       .replace('-CIRCUIT','PROBLEM')

            return newExtension

    def lireFicTexte(self,pathFic):
        """
           lireFicTexte(pathFic) -> liste des lignes

           pathFic:        String
                           - Chemin d'acc�s vers le fichier texte

           liste des lignes:       [str]
                                   - Liste des lignes du fichier texte

        Utilisation:

                Retourner les lignes d'un fichier, utile pour lire les petites
                databases dans un fichier ou les fichiers de config.
        """
        if os.access(pathFic,os.R_OK):
            f = open(pathFic,'r')
            lignes = f.readlines()
            f.close
            return lignes
        else:
            raise IOError

    def reloadMapCircuit(self,pathHeader2circuit):
        """reloadMapCircuit(pathHeader2circuit)

           pathHeader2circuit:  String
                                - Chemin d'acc�s vers le fichier de circuits


           Recharge le fichier de mapCircuits.

           Utilisation:

                Rechargement lors d'un SIGHUP.
        """
        oldMapCircuits = self.mapCircuits

        try:

            self.initMapCircuit(pathHeader2circuit)

            self.logger.info("Succ�s du rechargement du fichier de Circuits")

        except Exception, e:

            self.mapCircuits = oldMapCircuits

            self.logger.warning("bulletinManager.reloadMapCircuit(): �chec du rechargement du fichier de Circuits")

            raise


    def initMapCircuit(self,pathHeader2circuit):
        """initMapCircuit(pathHeader2circuit)

           pathHeader2circuit:  String
                                - Chemin d'acc�s vers le fichier de circuits

           Charge le fichier de header2circuit et assigne un map avec comme cle
           champs:
                'routing_groups' -- list of clients to which the messages 
'                priority'       -- priority to assign to the message.

           FIXME: Peter a fix� le chemin a /apps/px/etc/header2circuit.conf
                donc le parametre choisi simplement si on s�en sert ou pas.
        """
        if pathHeader2circuit == None:
        # Si l'option est � OFF
            self.mapCircuits = None
            return

        self.mapCircuits = {}

        # Test d'existence du fichier
        try:
            pathHeader2circuit = PXPaths.ETC + 'header2client.conf'

            fic = os.open( pathHeader2circuit, os.O_RDONLY )
        except Exception:
            raise bulletinManagerException('Impossible d\'ouvrir le fichier d\'entetes ' + pathHeader2circuit + ' (fichier inaccessible)' )

        lignes = os.read(fic,os.stat(pathHeader2circuit)[6])

        #self.logger.info("Validating header2client.conf, clients:" + string.join(self.source.ingestor.clientNames))
        bogus=[]
        routable=[] # sub group of the clients, only ones for which we can route bulletins
        for ligne in lignes.splitlines():
            uneLigneSplitee = ligne.split(':')
            ahl = uneLigneSplitee[0]
            self.mapCircuits[uneLigneSplitee[0]] = {}
            try:
                self.mapCircuits[ahl] = {}
                self.mapCircuits[ahl]['entete'] = ahl
                self.mapCircuits[ahl]['routing_groups'] = ahl
                self.mapCircuits[ahl]['priority'] = uneLigneSplitee[2]
                gs=[]
                for g in uneLigneSplitee[1].split() :
                    #if g in fet.clients.keys():
                    if g in self.source.ingestor.clientNames:
                        gs = gs + [ g ]
                        if g not in routable: routable.append(g)
                    else:
                        if g not in bogus:
                            bogus = bogus + [ g ]
                            #self.logger.warning("client (%s) invalide, ignor�e ", g )
                            self.logger.warning("Client '%s' is in header2client.conf but inexistant in px", g )
                self.mapCircuits[ahl]['routing_groups'] =  gs
                
            except IndexError:
                raise bulletinManagerException('Les champs ne concordent pas dans le fichier header2circuit',ligne)
        self.logger.info("From header2client.conf we learn that we can route bulletins to: %s" % routable)

    def getMapCircuits(self):
        """getMapCircuits() -> mapCircuits

           � utiliser pour que plusieurs instances utilisant la m�me
           map.
        """
        return self.mapCircuits

    def setMapCircuits(self,mapCircuits):
        """setMapCircuits(mapCircuits)

           � utiliser pour que plusieurs instances utilisant la m�me
           map.
        """
        self.mapCircuits = mapCircuits

    def getCircuitList(self,bulletin):
        """circuitRename(bulletin) -> Circuits

           bulletin:    Objet bulletin

           Circuits:    String
                        -Circuits formatt�s correctement pour �tres ins�r�s dans l'extension

           Retourne la liste des circuits pour le bulletin pr�c�d�s de la priorit�, pour �tre ins�r�
           dans l'extension.

              Exceptions possibles:
                   bulletinManagerException:       Si l'ent�te ne peut �tre trouv�e dans le
                                                   fichier de circuits
        """
        if self.mapCircuits == None:
            raise bulletinManagerException("Le mapCircuit n'est pas charg�")

        entete = ' '.join(bulletin.getHeader().split()[:2])

        if not self.mapCircuits.has_key(entete):
            bulletin.setError('Entete +' +entete+ ' non trouv�e dans fichier de circuits')
            raise bulletinManagerException('Entete non trouv�e dans fichier de circuits')

        # Check ici, si ce n'est pas une liste, en faire une liste
        if not type(self.mapCircuits[entete]['routing_groups']) == list:
            self.mapCircuits[entete]['routing_groups'] = [ self.mapCircuits[entete]['routing_groups'] ]

        if self.use_pds:
            return self.mapCircuits[entete]['priority'] + '.' + '.'.join(self.mapCircuits[entete]['routing_groups']) + '.'
        else:
            return self.mapCircuits[entete]['priority']

    def getFinalPath(self,bulletin):
        """getFinalPath(bulletin) -> path

           path         String
                        - R�pertoire o� le fichier sera �crit

           bulletin     objet bulletin
                        - Pour aller chercher l'ent�te du bulletin

           Utilisation:

                Pour g�n�rer le path final o� le bulletin sera �crit. G�n�re
                le r�pertoire incluant la priorit�.
        """
        # Si le bulletin est erronn�
        if bulletin.getError() != None:
            return self.pathDest.replace('-PRIORITY','PROBLEM')

        try:
            entete = ' '.join(bulletin.getHeader().split()[:2])
        except Exception:
            self.logger.error("Ent�te non standard, priorit� impossible � d�terminer(%s)",bulletin.getHeader())
            return self.pathDest.replace('-PRIORITY','PROBLEM')

        if self.mapCircuits != None:
            # Si le circuitage est activ�
            if not self.mapCircuits.has_key(entete):
                    # Ent�te est introuvable
                self.logger.error("Ent�te introuvable, priorit� impossible � d�terminer")
                return self.pathDest.replace('-PRIORITY','PROBLEM')

            return self.pathDest.replace('-PRIORITY',self.mapCircuits[entete]['priority'])
        else:
            return self.pathDest.replace('-PRIORITY','NONIMPLANTE')

    def getPathSource(self):
        """getPathSource() -> Path_source

           Path_source:         String
                                -Path source que contient le manager
        """
        return self.pathSource

    def verifyDelay(self,unBulletin):
        """verifyDelay(unBulletin)

           V�rifie que le bulletin est bien dans les d�lais (si l'option
           de d�lais est activ�e). Flag le bulletin en erreur si le delai
           n'est pas respect�.

           Ne peut v�rifier le d�lai que si self.mapEnteteDelai n'est
           pas � None.

           Utilisation:

                Pouvoir v�rifier qu'un bulletin soit dans les d�lais
                acceptables.
        """
        if (self.mapEnteteDelai == None):
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
            self.logger.warning("D�lai en dehors des limites permises bulletin: "+unBulletin.getHeader()+', heure pr�sente '+now)
            unBulletin.setError('Bulletin en dehors du delai permis')
