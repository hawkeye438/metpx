"""Superclasse pour un gateway de transfert de bulletins"""
import imp

__version__ = '2.0'

class gateway:
	"""Regroupe les traits communs d'un gateway.

	   De cette classe sera sp�cialis� les receivers, senders, etc.
	   Un module self.config sera accessible qui contiendra les
	   �l�ments de configuration du fichier de config.

	   Les m�thodes abstraites l�vent une exception pour l'instant, et
	   cette classe ne devrait pas �tre utilis�e comme telle."""
	def __init__(self,path):
		self.loadConfig(path)

	def loadConfig(self,path):
		"""loadConfig(path)

		   Charge la configuration, situ�e au path en particulier.
		   La configuration doit �tre syntaxiquement correcte pour
		   que python puisse l'interpr�ter.

		   self.config est un module valide apr�s l'ex�cution si 
		   aucune erreur."""
        	try:
                        fic_cfg = open(pathCfg,'r')
                        self.config = imp.load_source('config','/dev/null',fic_cfg)
                        fic_cfg.close()
                except IOError:
                        #print "*** Erreur: Fichier de configuration inexistant, erreur fatale!" #FIXME
                        #sys.exit(-1)
			pass

	def establishConnection(self):
		pass

	def checkLooping(self):
		pass
