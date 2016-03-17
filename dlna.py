
import upnp, urllib2
import xml.etree.ElementTree as ET

class Service:

	def __init__(self):
		self.parameters = { }

class Device:

	def __init__(self):
		self.parameters = { }
		self.service = [ ]

class DLNAMediaServer:

	def __init__(self, upnp):

		self.upnp = upnp

	def register(self):

		self.upnp.addObserver(dlna, {'ST': 'urn:schemas-upnp-org:device:MediaServer:1'})

	def downloadRootFile(self, url):
		return urllib2.urlopen(url)

	def formatTagTitle(self, title):
		return title.split('}', 1)[1]

	def parseIconList(self, xml):
		pass

	def parseDevice(self, xml):

		device = Device()

		for field in xml:
			if self.formatTagTitle(field.tag) == 'serviceList':
				device.service.append(self.parseServiceList(field.getchildren()))
			elif self.formatTagTitle(field.tag) == 'iconList':
				self.parseIconList(field.getchildren())
			else:
				device.parameters[self.formatTagTitle(field.tag)] = field.text

		return device

	def parseService(self, xml):

		# find SCPDURL: REQUIRED. URL for service description

		service = Service()

		for field in xml:
			service.parameters[self.formatTagTitle(field.tag)] = field.text

		print service.parameters

		return service

	def parseServiceList(self, xml):

		services = [ ]

		for field in xml:
			if 'service' == self.formatTagTitle(field.tag):
				services.append(self.parseService(field.getchildren()))

		return services

	def processXML(self, xmlContents):

		xml = ET.parse(xmlContents).getroot()

		print 'Processing'

		device = None

		for field in xml.getchildren():
			if 'Device' in field.tag.title():
				device = self.parseDevice(field.getchildren())

		print device.parameters, device.service

	def observe(self, upnp, fields):

		if not ('LOCATION' in fields):
			print 'LOCATION field not field'
			return

		try:

			xmlContents = self.downloadRootFile(fields['LOCATION'])

		except Exception as e:
			print 'Failed to download root file', e

		else:
			self.processXML(xmlContents)

	

if __name__ == '__main__':


	client = upnp.UPNP()
	dlna = DLNAMediaServer(client)
	dlna.register()
	client.createSocket()
	client.searchDevices(1)
	client.eventsLoop()
