"""Superclasse pour un gateway de transfert de bulletins"""
import imp

__version__ = '2.0'

class gatewayException(Exception):
        """Classe d'exception sp�cialis�s relatives aux gateways"""
	pass

class gateway:
	"""Regroupe les traits communs d'un gateway.

	   De cette classe sera sp�cialis� les receivers, senders, etc.
	   Un module self.config sera accessible qui contiendra les
	   �l�ments de configuration du fichier de config.

	   Les m�thodes abstraites l�vent une exception pour l'instant, et
	   cette classe ne devrait pas �tre utilis�e comme telle.

	   Terminologie:

	      - D'un lecteur l'on pourra appeler une lecture de donn�es 
	        (ex: disque, socket, etc...)
	      - D'un �crivain on pourra lui fournir des donn�es qu'il
	        pourra "�crire" (ex: disque, socket, etc...)

	   Instanciation:

		Le gateway s'instancie avec un fichier de configuration 
	        qu'il charge et dont l'impl�mentation varie selon le type
	        de gateway. 

	        path		String

				- Chemin d'acc�s vers le fichier de config
	"""
	def __init__(self,path):
		self.config = gateway.loadConfig(path)

	def loadConfig(self,path):
		"""loadConfig(path)

		   Charge la configuration, situ�e au path en particulier.
		   La configuration doit �tre syntaxiquement correcte pour
		   que python puisse l'interpr�ter.
		"""
        	try:
                        fic_cfg = open(pathCfg,'r')
                        config = imp.load_source('config','/dev/null',fic_cfg)
                        fic_cfg.close()

			return config
                except IOError:
                        #print "*** Erreur: Fichier de configuration inexistant, erreur fatale!" #FIXME
                        #sys.exit(-1)
			raise

	loadConfig = staticmethod(loadConfig)

	def establishConnection(self):
	"""establishConnectino()

	   �tablit une connection avec le lecteur et l'�crivain (v�rifie
	   que les ressources sont disponibles aussi)"""
                raise gatewayException('M�thode non implant�e (m�thode abstraite establishConnection)')

	def read(self):
	"""read() -> data

	   data	: Liste d'objets

	   Cette m�thode retourne une liste d'objets, qui peut �tre
	   ing�r�e par l'�crivain. Elle l�ve une exception si
	   une erreur est d�tect�e.
	   """
		raise gatewayException('M�thode non implant�e (m�thode abstraite read)')
	
	def write(self,data):
        """write(data) 

           data : Liste d'objets

	   Cette m�thode prends le data lu par read, et fait le tra�tement
	   appropri�.
           """
                raise gatewayException('M�thode non implant�e (m�thode abstraite write)')

	def run(self):
		"""run()

		   Boucle infinie pour le transfert de data. Une exception
		   non contenue peut �tre lev�e si le lecteur et l'�crivain
		   ne sont pas disponibles."""
		while True:
			# V�rifier que le lecteur et l'�crivain sont disponibles
			pass

			data = self.read()

			if len(data) == 0:
			# S'il n'y a pas de nouveau data
				pass
			else:
				self.write(data)

	def checkLooping(self):
		pass

