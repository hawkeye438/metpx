"""Gestion des bulletins "WMO" """

import bulletinManager, bulletinWmo, os, string

__version__ = '2.0'

class bulletinManagerWmo(bulletinManager.bulletinManager):
        __doc__ = bulletinManager.bulletinManager.__doc__ + \
        """### Ajout de bulletinManagerWmo ###

           Sp�cialisation et implantation du bulletinManager.

	   Pour l'instant, un bulletinManagerWmo est pratiquement
	   la m�me chose que le bulletinManager.

           Auteur:      Louis-Philippe Th�riault
           Date:        Octobre 2004
        """

        def __init__(self,pathTemp,logger,pathSource=None, \
                        pathDest=None,maxCompteur=99999,lineSeparator='\n',extension=':', \
                        pathFichierCircuit=None):

                bulletinManager.bulletinManager.__init__(self,pathTemp,logger, \
                                                pathSource,pathDest,maxCompteur,lineSeparator,extension,pathFichierCircuit)

        def _bulletinManager__generateBulletin(self,rawBulletin):
                __doc__ = bulletinManager.bulletinManager._bulletinManager__generateBulletin.__doc__ + \
                """### Ajout de bulletinManagerWmo ###

                   Overriding ici pour passer les bons arguments au bulletinWmo

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
                """
                return bulletinWmo.bulletinWmo(rawBulletin,self.logger,self.lineSeparator)


