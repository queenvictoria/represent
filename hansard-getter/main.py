# from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup
import urllib2
import re
import sys


DOMAIN="parlinfo.aph.gov.au"
URL="http://www.aph.gov.au/Parliamentary_Business/Hansard/Search"
#	?page=2

search_path = "http://www.aph.gov.au/Parliamentary_Business/Hansard/Search"
query_string = "?page=1&hto=1&q=&ps=100&drt=2&drv=7&drvH=7&f=28%2f09%2f2010&to=03%2f06%2f2012&pnu=43&pnuH=43&pi=0&chi=2&coi=0&st=1"

xmlfiles = {}
searches = {}
searches_read = []

out_path = "../data/parlinfo.aph.gov.au/hansard/"


def main():
	parseFile(query_string)

	# get the xml files
	i = 0
	for url in xmlfiles.iterkeys():
		i = i + 1
		filename = "%s/%s" % (out_path, xmlfiles[url])
		
		req = urllib2.Request(url)
		f = urllib2.urlopen(req)
		print "%s %s" % (len(xmlfiles) - i, filename)

		# Open our local file for writing
		outfile = open(filename, "wb")
		#Write to our local file
		outfile.write(f.read())
		outfile.close()


def parseFile(s):
	url = "%s%s" % (search_path, s)
	print url

	file = urllib2.urlopen(url)
	# file = open("../data/www.aph.gov.au/search.html")
	doc = file.read()

#	add it to the list of pages we've parsed
	searches_read.append(s)
	print "Read %d files." % len(searches_read)

	soup = BeautifulSoup(doc)
	for page in soup.select('div.page-controls li a'):
		if not page.get("href") in searches_read:
			parseFile(page.get("href"))
		
#	print soup.select('a[href^=http://parl][title=^XML]')
#	print soup.select("a[title^=XML]")
	xml = soup.select("a[title^=XML]")

#	many of these are the same -- dont worry we'll only download them once
	for x in xml:
		m = re.search('toc_unixml/(.+);fileType', x.get('href'))
		xmlfiles[x.get('href')] = urllib2.unquote(m.group(1))

	print "%d XML files queued." % len(xmlfiles)

main()