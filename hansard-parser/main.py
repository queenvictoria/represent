# from xml.etree import ElementTree
import datetime
import lxml.etree as ElementTree

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

						speaker = Speaker()
						speaker.speaker_name = talker.find("name").text.strip()
						speaker.speaker_id = talker.find("name.id").text.strip()
						speaker.generate_hash()

						the_speech.speaker_hash = speaker.speaker_hash
						
				
			
			#bill = Bill()


class Bill(object):
	def __init__(self, name):
		self.name = name.strip()
		status = None
		print "Created new Bill %s." % self.name


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

	def set_datetime(self, time, date):
		time = string_to_time(time)
		self.datetime = datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
		print self.datetime



def test():
	# source = "2006-02-07.xml"
	source = "2011-06-01.xml"
	h = Hansard(source)
	h.parse_xml()
	# _parse_xml_file(source)


def main():
	pass


test()

