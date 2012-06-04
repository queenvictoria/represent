# from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup
import pickle

import urllib2
import urllib
from urlparse import urlparse, parse_qs, parse_qsl
import re
import sys
import os


DOMAIN="parlinfo.aph.gov.au"
URL="http://www.aph.gov.au/Parliamentary_Business/Hansard/Search"
#	?page=2

search_path = "http://www.aph.gov.au/Parliamentary_Business/Hansard/Search"
num_results = 100
parliament_no = 42;

# senate chi=1
# reps chi=2
# main committee=3
# joint committee=4
# estimates=5
# all other committees=6

chamber = 2

default_query = {
	"page": 1,
	"hto": 1,
	"q": '',
	"ps": num_results,
	"drt": 2,
	"drv": 7,
	"drvH": 7,
	"f": "01/01/1995",
	"to": "01/01/2032",
	"pnu": parliament_no,
	"pnuH": parliament_no,
	"pi": 0,
	"chi": chamber,
	"coi": 0,
	"st": 1,
}

global defaults
global options
defaults = {}
defaults['xmlfiles'] = {}
defaults['searches'] = {}
defaults['searches_read'] = []
options_file = "settings.pickle"
out_path = "../data/parlinfo.aph.gov.au/hansard"


def init():
	global defaults
	global options
	# copy the defults to opts
	options = defaults
	# copy the default args into the query
	options["query_string"] = default_query

	# merge the opts with the saved opts
	_load_opts(options)

	# pop off the last page we loaded and run that one again 
	# (helps with cancellations where the initial load page is stored)
	# catch empty list error
	try:
		options['searches_read'].pop()
	except:
		pass

def main():
	global options
	init()
	
	try:
		options["query_string"].append(('q',''))
	except:
		# first time around its not a list
		pass

	query_string = "?%s" % urllib.urlencode(options["query_string"])
	parseFile(query_string)

	print "Retrieving %d XML files." % len(options['xmlfiles'])

	# get the xml files
	i = 0
	try:
		os.mkdir("%s/%s" % (out_path, parliament_no))
	except OSError, e:
		if e.errno == 17:
			print "Directory exists."
		else:
			print e.errno, e.args
			
			print "Coulding make directory %s/%s." % (out_path, parliament_no)
			return
	except:
		print "Coulding make directory %s/%s." % (out_path, parliament_no)
		return

	for url in options['xmlfiles'].iterkeys():
		i = i + 1
		filename = "%s/%s/%s" % (out_path, parliament_no, options['xmlfiles'][url])
		
		# don't download files we already have
		if os.path.isfile(filename):
			print "Already downloaded %s/%s" % (parliament_no, options['xmlfiles'][url])
			continue

		req = urllib2.Request(url)
		f = urllib2.urlopen(req)
		print "%s %s" % (len(options['xmlfiles']) - i, filename)

		# Open our local file for writing
		outfile = open(filename, "wb")
		#Write to our local file
		outfile.write(f.read())
		outfile.close()


def parseFile(s):
	url = "%s%s" % (search_path, s)
	print "Loading %s ..." % url
	file = urllib2.urlopen(url)
	# file = open("../data/www.aph.gov.au/search.html")
	doc = file.read()

#	add it to the list of pages we've parsed
	options['searches_read'].append(s)
	print "read %d files." % len(options['searches_read'])

	soup = BeautifulSoup(doc)
		
#	find all the xml files and queue them
#	print soup.select('a[href^=http://parl][title=^XML]')
#	print soup.select("a[title^=XML]")
	xml = soup.select("a[title^=XML]")
#	many of these are the same -- dont worry we'll only download them once
	for x in xml:
		m = re.search('toc_unixml/(.+);fileType', x.get('href'))
		options['xmlfiles'][x.get('href')] = urllib2.unquote(m.group(1))

	print "%d XML files queued." % len(options['xmlfiles'])
#	save out the query string so we can resume in the right place
	o = urlparse(url)
	options["query_string"] = parse_qsl(o.query)

	_save_opts()
	
	for page in soup.select('div.page-controls li a'):
		if not page.get("href") in options['searches_read']:
			parseFile(page.get("href"))
		else:
#			print "Already read that one."
			pass


"""
	Save out options so we can cancel and resume.
"""
def _save_opts():
	global options
	f = open(options_file, "wb")
	pickle.dump(options, f)
	f.close()


"""
	Merge defaults with saved options.
"""
def _load_opts(defaults):
	global options
	try:
		f = open(options_file, "rb")
		options = pickle.load(f)
		f.close()
		options = dict(defaults.items() + options.items())
		print "Loaded options."
	except:
		print "Couldn't load previous options."
		pass


main()