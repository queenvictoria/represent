"""
	@TODO
	-	sponsors
	v	matching talkers with voters


"""

# from xml.etree import ElementTree
import datetime
import lxml.etree as ElementTree
import re
import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy import func, select

import os
import glob

# global engine
global session
from local_settings import settings

engine = create_engine(
                "mysql+mysqldb://%s:%s@localhost/%s" % (settings['dbuser'], settings['dbpass'], settings['dbname']), 
                pool_recycle=3600
            )
# engine = create_engine('sqlite:///:memory:', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


def string_to_date(string):
	date = string.split("-")
	return datetime.date(int(date[0]), int(date[1]), int(date[2]))

def string_to_time(string):
	time = string.split(":")
	try:
		return datetime.time(int(time[0]), int(time[1]), 0)
	except:
		return datetime.time(0,0,0)


class Hansard(object):
	def __init__(self, filename):
		self.filename = filename
		date = filename[:-4]
#		self.date = string_to_date(date)
#		datetime.combine(date, time)

		print filename
#		print self.date

	def parse_xml(self):
		try:
			tree = ElementTree.parse(self.filename)
		except:
			print "Unexpected error:", sys.exc_info()[0]
			return

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
				bill.put()

#	default date to be updated below
				current_date = datetime.datetime(self.date.year, self.date.month, self.date.day, 0, 0, 0)

#	get the subdebate.2 siblings of this subdebate
				for subdebate2 in subdebate.iterfind("subdebate.2"):
					reading = subdebate2.find("subdebateinfo/title").text
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
						
						current_date = the_speech.datetime

						the_speech.set_bill(bill)
						the_speech.set_house(self.chamber)

						speaker_name = talker.find("name").text.strip()
						speaker_id = talker.find("name.id").text.strip()
						speaker_hash = generate_hash(speaker_id, speaker_name)
						
						global session
						speaker = session.query(Speaker).get(speaker_hash)
						if not speaker:
							speaker = Speaker(speaker_id=speaker_id, speaker_name=speaker_name)
							speaker.put()

						the_speech.set_speaker(speaker)
						the_speech.put()
						
			#	divisions
					"""
						<division.data>
		              <ayes>
		                <num.votes>68</num.votes>
		                <title>AYES</title>
		                <names>
		                  <name>Ale
              		"""
					for division in subdebate2.iterfind("division/division.data"):
						direction = {'ayes','noes','PAIRS'}
						the_division = Division(bill=bill, date=current_date)
						the_division.bill_hash = bill.bill_hash
						# hacky but works - does relation solve this properly ?
						the_division.put()

						for d in direction:
							query = "%s/names/name" % d
							voters = division.findall(query)
							# how many voters voted `d` way?
							if voters != None:
								the_division.add_votes(d, len(voters))
								for voter in voters:
									vote = Vote(voter_name=voter.text, division=the_division, 
										vote=d)
									vote.put()

						the_division.put()
		# push everything into the database
		global session
		session.commit()



class Bill(Base):
	__tablename__ = 'bill'
	# id = Column(Integer, primary_key=True)
	bill_hash = Column(String(128), primary_key=True)
	name = Column(String(255))
	status = Column(String(32))
	divisions = relationship("Division")

#	sponsors are surely speakers
#	sponsor_id = Column(Integer, ForeignKey('speaker.speaker_id'))
#	sponsor = relationship("Speaker", backref=backref('bill', order_by=id))

	def __init__(self, name):
		self.name = ascii_only(name.strip())
		
		self.status = None
		self.sponsor = None
		print "Created new Bill %s." % self.name
		self.generate_hash()

# @TODO this should be the table primary key -- remove and replace
	def generate_hash(self):
		import hashlib
		m = hashlib.sha1()
		# this needs to be ascii
		m.update(ascii_only(self.name))
		self.bill_hash = m.hexdigest()

	def put(self):
		global session
		self = session.merge(self)


class Division(Base):
	__tablename__ = 'division'
	division_hash = Column(String(128), primary_key=True)
	bill_hash = Column(String(128), ForeignKey('bill.bill_hash'))
#	bill = relationship("Bill", backref=backref('division'))
	date = Column(DateTime)
	sponsor = Column(String(32))
	total_votes = Column(Integer)
	split = Column(Float)
	votes = relationship("Vote")

	def __init__(self, bill=None, date=datetime.datetime.now(), sponsor=None):
		self.bill_hash = bill.bill_hash
		self.date = date
		self.sponsor = sponsor
	
		self.total_votes = 0
		self.split = 0
		self.ayes = 0
		self.noes = 0
		self.pairs = 0

		self.generate_hash()

	def add_votes(self, direction='ayes', count=0):
		self.total_votes = self.total_votes + int(count)
		if direction == 'ayes':
			self.ayes = int(count)
		elif direction == 'noes':
			self.noes = int(count)
		elif direction == 'PAIRS':
			self.pairs = int(count)

		if (self.ayes + self.noes) > 0 and self.ayes > 0:
			self.split = round(float(self.ayes) / float( self.ayes + self.noes ),3)

	def generate_hash(self):
		import hashlib
		m = hashlib.sha1()
		m.update(str(self.date)+str(self.bill_hash))
		self.division_hash = m.hexdigest()

	def put(self):
		global session
		self = session.merge(self)
		

class Vote(Base):
	__tablename__ = 'vote'
	id = Column(Integer, primary_key=True)
#	what did we vote about?
	division_hash = Column(String(128), ForeignKey('division.division_hash'))
	division = relationship("Division", backref=backref('vote'))
#	who voted?
	voter_name = Column(String(32))
	vote = Column(String(8))
#	if they voted they must be a member surely
	speaker_hash = Column(String(128), ForeignKey('speaker.speaker_hash'))
#	speaker = relationship("Speaker", backref=backref('vote'))

	def __init__(self, voter_name, division=None, vote='ayes'):
		self.division_hash = division.division_hash
		self.voter_name = voter_name
		self.vote = vote

		speaker = get_by_voter_name(self.voter_name)
		if hasattr(speaker, 'speaker_name'):
			if speaker.speaker_name != "":
				self.speaker = speaker
				self.speaker_hash = self.speaker.speaker_hash

	def put(self):
		global session
		self = session.merge(self)


class Speaker(Base):
	__tablename__ = 'speaker'

	speaker_hash = Column(String(128), primary_key=True)
	speaker_id = Column(String(8))
	speaker_name = Column(String(128))
	speaker_name_short = Column(String(32))

	def __init__(self, speaker_id="", speaker_name=""):
		self.speaker_name = speaker_name.strip()
		self.speaker_id = speaker_id.strip()
		self.speaker_hash = generate_hash(self.speaker_id, self.speaker_name)

	def __str__(self):
		return self.speaker_name
	

	"""
		Save to db and return speaker id
	"""
	def put(self):
		global session
		try:
			self = session.merge(self)
			print "Saved %s" % self.speaker_name
		except:
			print "Couldn't merge speaker."

#		print self.speaker_name

	"""
		Retrieve a speaker from the db
	"""
	def get(self):
		return None

def generate_hash(speaker_id, speaker_name):
	import hashlib
	m = hashlib.sha1()
	m.update(speaker_id+speaker_name)
	return m.hexdigest()

def get_by_voter_name(voter_name):
	# 	talker/name
	# 	<name role="metadata">Symon, Mike, MP</name>
	#	voter_name is speaker_name_short
	#	voter_name
	#	<name>Alexander, JG</name>

	#	search speakers on their last name and first initial
		(lastname, initials) = voter_name.split(", ")
		firstinitial = initials[0:1]
		namelike = "%s, %s%%" % (lastname, firstinitial)
		global session
		# query = session.query(Speaker).filter(Speaker.speaker_name==namelike)
		query = session.query(Speaker).filter(Speaker.speaker_name.like(namelike)) 

		# if we found a result then update the speaker and return the object
		speaker = None
		if query.first():
			speaker = query.first()
			speaker.speaker_name_short = voter_name
			speaker = session.merge(speaker)
		return speaker



class Speech(Base):
	__tablename__ = 'speech'
	id = Column(Integer, primary_key=True)

	speaker_hash = Column(String(128), ForeignKey('speaker.speaker_hash'))
	speaker = relationship("Speaker", backref=backref('speech'))

	reading = Column(String(32))
	party = Column(String(32))
	house = Column(String(32))
	bill_hash = Column(String(128), ForeignKey('bill.bill_hash'))
	bill = relationship("Bill", backref=backref('bill'))

	datetime = Column(DateTime)
	word_count = Column(Integer)

	speech_words = Column(Text)

	def __init__(self, speech_words=None, speaker_hash=None, reading=None):
		
		self.speaker_hash = speaker_hash
		self.speech_words = speech_words
		self.reading = reading

		self.party = None
		self.electorate = None
		self.house = None
		self.bill_hash = None
		self.datetime = None
		self.word_count = 0

	def set_house(self, house):
		self.house = house
		# print self.house

	def set_datetime(self, time, date):
		time = string_to_time(time)
		self.datetime = datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
		# print self.datetime

	def set_bill(self, bill):
		self.bill_hash = bill.bill_hash

	def set_speaker(self, speaker):
		self.speaker_hash = speaker.speaker_hash

	def put(self):
	#	count the words
		words = re.sub(r'<[^>]*?>', '', self.speech_words)
		self.word_count = len(words.split(' '))
		# print self.wordcount

	#	count interuptions
#		interuptions = re.compile(r'*HPS-MemberInterjecting*')
#		print interuptions.match()
#		print interuptions
		interjection = "HPS-MemberInterjecting"
		interuptions = self.speech_words.split(interjection)
		if len(interuptions) > 1:
			self.interuptions = len(interuptions) - 1
			# print "%d interruptions." % len(interuptions)

		global session
		self = session.merge(self)
		# commit here as we need to make sure we're not duplicating speakers
		# session.commit()

	def __str__(self):
		return str(self.speaker_hash+str(self.datetime)+str(self.bill_hash))

Base.metadata.create_all(engine) 


def test():
	# source = "2006-02-07.xml"
	source = "2011-06-01.xml"
	h = Hansard(source)
	h.parse_xml()

	global session
#	session.query(func.count(Speaker.speaker_id))
	# _parse_xml_file(source)
	speakers = session.query(func.count(Speaker.speaker_id)).all() # about .01 sec
	votes = session.query(func.count(Vote.id)).all() # about .01 sec
	divisions = session.query(func.count(Division.id)).all() # about .01 sec
	speechs = session.query(func.count(Speech.id)).all() # about .01 sec
	votes = session.query(func.count(Vote.id)).all() # about .01 sec
	print speakers, votes, divisions, speechs

"""
	Select all votes whose speaker is None and run the get_by_voter_name again.
"""
def update_speaker_names():
	global session
	unknown = session.query(Vote).filter(Vote.speaker == None).all()
	print len(unknown)
	for voter in unknown:
		speaker = get_by_voter_name(voter.voter_name)
		if hasattr(speaker, 'speaker_name'):
			if speaker.speaker_name != "":
				voter.speaker = speaker
				voter.speaker_hash = voter.speaker.speaker_hash
				session.merge(voter)
				print voter.speaker.speaker_name_short

def ascii_only(s):
	return "".join(i for i in s if ord(i)<128)

def main():
	path = "../data/hansard-xml.d/"
	for source in glob.glob(os.path.join(path, '*.xml')):
		print "current file is: " + source
		h = Hansard(source)
		h.parse_xml()

	global session
#	session.query(func.count(Speaker.speaker_id))
	# _parse_xml_file(source)
	speakers = session.query(func.count(Speaker.speaker_id)).all() # about .01 sec
	votes = session.query(func.count(Vote.id)).all() # about .01 sec
	divisions = session.query(func.count(Division.division_hash)).all() # about .01 sec
	speechs = session.query(func.count(Speech.id)).all() # about .01 sec
	votes = session.query(func.count(Vote.id)).all() # about .01 sec
	print speakers, votes, divisions, speechs



main()
# test()
# update_speaker_names()

