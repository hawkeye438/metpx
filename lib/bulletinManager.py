"""Gestionnaire de bulletins"""

__version__ = '2.0'

class bulletinManagerException(Exception):
        """Classe d'exception sp�cialis�s relatives au bulletin
managers"""
        pass

class bulletinManager:
	"""Gestionnaire de bulletins g�n�ral. S'occupe de la manipulation
	   des bulletins en tant qu'entit�s, mais ne fait pas de tra�tements
	   � l'int�rieur des bulletins"""

	def __init__(self,connectionManager,pathTemp,pathSource=None,pathDest=None):

		self.connectionManager = connectionManager
		self.pathSource = pathSource
		self.pathDest = pathDest
		self.pathTemp = pathTemp
