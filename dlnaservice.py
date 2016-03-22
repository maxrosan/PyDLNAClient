
import upnp, urllib2, threading, urlparse
import xml.etree.ElementTree as ET

import util

class Service:

	def __init__(self):
		self.parameters = { }
		self.location = None

	def downloadFileAction(self, path):
		return urllib2.urlopen(self.location + path)

	def downloadAndParseAction(self):

		xmlContents = None

		try:
			xmlContents = self.downloadFileAction(self.parameters['SCPDURL'])
		except Exception as e:
			print 'Failed to download file ', self.location + self.parameters['SCPDURL']
			print e
		else:
			self.parseActionXML(xmlContents)

	def parseAction(self, actionTag):
		pass

	def parseActionXML(self, xmlContents):

		xml = ET.parse(xmlContents).getroot()

		for field in xml.getchildren():
	
			tag = util.formatTagTitle(field.tag)
		
			if tag == 'actionList':
				self.parseAction(field)	


class Device:

	def __init__(self):
		self.parameters = { }
		self.service = [ ]
		self.fields = None

	def downloadServiceActions(self):

		print self.service

		for service in self.service:
			print 'Downloading description of service: ', service.parameters['serviceId']

			service.location = 'http://' + urlparse.urlparse(self.fields['LOCATION']).netloc
			service.downloadAndParseAction()


