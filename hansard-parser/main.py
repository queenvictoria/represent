# from xml.etree import ElementTree
import datetime
import lxml.etree as ElementTree
import re

def string_to_date(string):
	date = string.split("-")
	return datetime.date(int(date[0]), int(date[1]), int(date[2]))

def string_to_time(string):
	time = string.split(":")
	return datetime.time(int(time[0]), int(time[1]), 0)


class Hansard(object):
	def __init__(self, filename):
		self.filename = filename
		date = filename[:-4]
		self.date = string_to_date(date)
#		datetime.combine(date, time)

		print filename
#		print self.date

	def parse_xml(self):
		tree = ElementTree.parse(self.filename)
#		tree.hansard.session.header.date
		node = tree.find("session.header/date")
		self.date = string_to_date(node.text)

		self.chamber = tree.find("session.header/chamber").text
		self.parliament = tree.find("session.header/parliament.no").text
		self.session = tree.find("session.header/session.no").text
		self.period = tree.find("session.header/period.no").text

#		parliament, session, period
#	debate/subdebate/speech
#	etree style
#		for debate in tree.iterfind("debate/debateinfo/type[text()='BILL']"):
#	switch to xpath
#		find debates at any level whose debateinfo/type is BILLS
		debates = tree.xpath("//debate[debateinfo/type='BILLS']")
		for debate in debates:
			subdebates = debate.xpath("subdebate.1")
			for subdebate in subdebates:
				name = subdebate.find("subdebateinfo/title").text
				bill = Bill(name=name)

#	get the subdebate.2 siblings of this subdebate
				for subdebate2 in subdebate.iterfind("subdebate.2"):
					reading = subdebate2.find("subdebateinfo/title").text
					print reading
					for speech in subdebate2.iterfind("speech"):
						talktext = speech.find("talk.text")
						speech_words = ElementTree.tostring(talktext, pretty_print=True)
						the_speech = Speech(speech_words=speech_words, reading=reading)
#	talk.start, talk.text, continue
#	talk.start > talker > time.stamp, name, name.id, electorate, party, in.gov, first.speech
						talker = speech.find("talk.start/talker")

						the_speech.electorate = talker.find("electorate").text.strip()
						the_speech.party = talker.find("party").text.strip()

						# almost always empty
						if talker.find("time.stamp").text:
							the_speech.set_datetime(talker.find("time.stamp").text, self.date)
						else:
						#	inside the body text we get timestamps too
							time = talktext.xpath(".//span[@class='HPS-Time']")
							if len(time):
								the_speech.set_datetime(time[0].text, self.date)

						the_speech.set_bill(bill)
						the_speech.set_house(self.chamber)

						speaker = Speaker()
						speaker.speaker_name = talker.find("name").text.strip()
						speaker.speaker_id = talker.find("name.id").text.strip()
						speaker.generate_hash()
						speaker.put()

						the_speech.set_speaker(speaker)
						the_speech.put()
						
				
			
			#bill = Bill()


class Bill(object):
	def __init__(self, name):
		self.name = name.strip()
		self.id = self.generate_hash()
		self.status = None
		print "Created new Bill %s." % self.name

# @TODO this should be the table primary key -- remove and replace
	def generate_hash(self):
		import hashlib
		m = hashlib.sha1()
		m.update(self.name)
		self.id = m.hexdigest()


class Speaker(object):
	def __init__(self, speaker_id="", speaker_name=""):
		self.speaker_name = speaker_name.strip()
		self.speaker_id = speaker_id.strip()
		self.generate_hash()

	def __str__(self):
		return self.speaker_name
	
	def generate_hash(self):
		import hashlib
		m = hashlib.sha1()
		m.update(self.speaker_id+self.speaker_name)
		self.speaker_hash = m.hexdigest()

	"""
		Save to db and return speaker id
	"""
	def put(self):
		print self
		return None

	"""
		Retrieve a speaker from the db
	"""
	def get(self):
		return None


class Speech(object):
	def __init__(self, speech_words=None, speaker_hash=None, reading=None):
		self.speaker_hash = speaker_hash
		self.speech_words = speech_words
		self.reading = reading

		self.party = None
		self.electorate = None
		self.house = None
		self.bill_id = None
		self.datetime = None
		self.word_count = 0

	def set_house(self, house):
		self.house = house
		print self.house

	def set_datetime(self, time, date):
		time = string_to_time(time)
		self.datetime = datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
		print self.datetime

	def set_bill(self, bill):
		self.bill_id = bill.id

	def set_speaker(self, speaker):
		self.speaker_hash = speaker.speaker_hash

	def put(self):
	#	count the words
		words = re.sub(r'<[^>]*?>', '', self.speech_words)
		self.wordcount = len(words.split(' '))
		print self.wordcount

	#	count interuptions
#		interuptions = re.compile(r'*HPS-MemberInterjecting*')
#		print interuptions.match()
#		print interuptions
		interjection = "HPS-MemberInterjecting"
		interuptions = self.speech_words.split(interjection)
		if len(interuptions) > 1:
			self.interuptions = len(interuptions) - 1
			print "%d interruptions." % len(interuptions)

	#	print(self)
		pass

	def __str__(self):
		return str(self.speaker_hash+str(self.datetime)+str(self.bill_id))


def test():
	# source = "2006-02-07.xml"
	source = "2011-06-01.xml"
	h = Hansard(source)
	h.parse_xml()
	# _parse_xml_file(source)


def main():
	pass


test()

