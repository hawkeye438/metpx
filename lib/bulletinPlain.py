# -*- coding: UTF-8 -*-
"""D�finition d'une classe concr�te pour les bulletins"""

import bulletin

__version__ = '2.0'

class bulletinPlain(bulletin.bulletin):
	__doc__ = bulletin.bulletin.__doc__ + \
	"""
	### Ajout de bulletinPlain ###

	Implantation minimale d'un bulletin abstrait.

	Concr�tement, doSpecificProcessing ne fait rien.

	Auteur:	Louis-Philippe Th�riault
	Date:	Novembre 2004
  	"""

	def doSpecificProcessing(self):
		"""doSpecificProcessing()

		   Fait rien

                   Auteur:      Louis-Philippe Th�riault
                   Date:        Octobre 2004
		"""
		return
