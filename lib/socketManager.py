"""D�finition des diverses classes d�coulant de socketManager.

Ces classes servent � l'�tablissement de la connection, la 
r�ception et envoi des bulletins et la v�rification du respect 
des contraintes relatives aux protocoles.
"""

__version__ = '2.0'

class socketManager:
	"""Classe abstraite regroupant toutes les fonctionnalit�es 
requises pour un gestionnaire de sockets. Les m�thodes 
qui ne retournent qu'une exception doivent �tres red�finies 
dans les sous-classes.

Les arguments � passer pour initialiser un socketManager sont les
suivants:

	type		'master','slave' (default='slave')

			- Si master est fourni, le programme se 
			  connecte � un h�te distant, si slave,
			  le programme �coute pour une 
			  connection.

	localPort	int (default=9999)

			- Port local ou se 'bind' le socket.

	remoteHosts	[ (str hostname,int port) ]

			- Liste de (hostname,port) pour la 
			  connection. Lorsque timeout secondes
			  est atteint, le prochain couple dans
			  la liste est essay�.

			- Doit �tre absolument fourni si type='master',
			  et non fourni si type='slave'.

	timeout		int (default=None)
			
			- Lors de l'�tablissement d'une connection 
			  � un h�te distant, d�lai avant de dire 
			  que l'h�te de r�ponds pas.

"""
	def __init__(type='slave',localPort=9999,remoteHosts=None,timeout=None):
		self.type = type
		self.localPort = localPort
		self.remoteHosts = remoteHosts
		self.timeout = timeout
