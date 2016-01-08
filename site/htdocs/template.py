# Helper script to generate web pages for the site

from xml.dom import minidom
from xml.parsers.expat import ExpatError
import sys

def usage():
	print(sys.argv[0] + " <filename.html>")
	sys.exit(2)

def main():
	nav = None
	ul = None
	doc_div = None
	masthead = None
	containers = list()

	if len(sys.argv) != 2:
		usage()

	filename = sys.argv[-1]	

	try:
		doc = minidom.parse(filename)
	except (IOError, ExpatError), e:
		print(e)
		sys.exit(1)

	# Add bootstrap class to all <h1>
	h1_list = doc.getElementsByTagName("h1")
	for h1 in h1_list:
		h1.setAttribute("class", "page-header")

	# Find <nav class="col-md-3"> so we can add TOC nav to it
	nav_list = doc.getElementsByTagName("nav")
	for n in nav_list:
		if n.hasAttributes() and n.getAttribute("class") == "col-md-3":
			nav = n

	div_list = doc.getElementsByTagName("div")
	for div in div_list:
		# Find <div class="document">, for removal
		if div.hasAttributes() and div.getAttribute("class") == "document":
			doc_div = div
		# Find <div class="col-md-3" so we can add TOC nav to it
		# if div.hasAttributes() and div.getAttribute("class") == "col-md-3":
		# 	nav = div
		# Find TOC generated by rst2html
		if div.hasAttribute("id") and div.getAttribute("id") == "contents":
			contents_div = div
			for node in div.childNodes:				
				if node.nodeType != node.TEXT_NODE: 
					if node.tagName == "ul":
						ul = node
		# Remove id from divs added by rst2html
		# if div.hasAttribute("class") and div.getAttribute("class") == "section":
		# 	if div.hasAttribute("id"):
		# 		div.removeAttribute("id")

	# Insert TOC as a sidebar nav
	if ul is not None and nav is not None:
		ul.setAttribute("class", "nav nav-pills nav-stacked hidden-xs hidden-sm")
		ul.setAttribute("data-spy", "affix")
		ul.setAttribute("data-offset-top", "51")
		nav.appendChild(ul)
		contents_div.parentNode.removeChild(contents_div)

		# Now fix all the sub-nav links
		for node in ul.childNodes:
			if node.nodeType not in (node.TEXT_NODE, node.COMMENT_NODE) and node.tagName == "ul":
				node.setAttribute("class", "nav nav-pills nav-stacked sub-nav")

	for node in doc_div.childNodes:
		if node.nodeType not in (node.TEXT_NODE, node.COMMENT_NODE) and (node.tagName == "div" or node.tagName == "nav"):
			containers.append(node.cloneNode(deep=True))	

			# if node.hasAttributes and node.getAttribute("class") == "container":	
			# 	containers.append(node.cloneNode(deep=True))

	# # Remove up all section header <a> tags
	# a_tags = doc.getElementsByTagName("a")
	# for a in a_tags:
	# 	if a.hasAttribute("class") and a.getAttribute("class") == "toc-backref":			
	# 		text = a.firstChild
	# 		p = a.parentNode

	# 		# p.removeChild(a)
	# 		# a.unlink()
	# 		# print(a)
	# 		p.replaceChild(text, a)			
	# 		# p.appendChild(text)
			
	scripts = doc.getElementsByTagName("script")
				
	body = doc_div.parentNode

	# some scrollspy and affix attributes
	body.setAttribute("data-spy", "scroll")
	body.setAttribute("data-target", "#sidenav")
	body.setAttribute("data-offset", "15")
	# Remove extra <div class="document">
	# containers is found earlier in the code
	if containers:		
		for c in containers:
			body.appendChild(c)
		for s in scripts:
			body.appendChild(s)
		body.removeChild(doc_div)


	# Now add some footer stuff

	# Add js libraries
	# t = doc.createTextNode(" ")
	
	# anchor_js = doc.createElement("script")
	# anchor_js.setAttribute("src","./dist/js/anchor.js")
	# anchor_js.appendChild(t)

	# text_value = doc.createTextNode("anchors.add('h1');")
	# anchor_add = doc.createElement("script")
	# anchor_add.appendChild(text_value)

	# body.appendChild(anchor_js)
	# body.appendChild(anchor_add)

	# Write file to disk
	f = open(filename, "wb")
	f.write(doc.toxml().encode('UTF-8'))
	# print doc.toxml()

if __name__ == "__main__":
	main()