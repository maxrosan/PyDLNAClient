
import upnp, urllib2, threading, urlparse
import xml.etree.ElementTree as ET

from dlnaservice import Device, Service		
import util

class DLNAMediaServer:

	def __init__(self, upnp):

		self.upnp = upnp
		self.observer = [ ] # ( observer object )

	def registerObserver(self):

		self.upnp.addObserver(dlna, {'ST': 'urn:schemas-upnp-org:device:MediaServer:1'})

	def downloadRootFile(self, url):
		return urllib2.urlopen(url)

	def parseIconList(self, xml):
		pass

	def parseDevice(self, xml):

		device = Device()

		for field in xml:
			if util.formatTagTitle(field.tag) == 'serviceList':
				device.service = self.parseServiceList(field.getchildren())
			elif util.formatTagTitle(field.tag) == 'iconList':
				self.parseIconList(field.getchildren())
			else:
				device.parameters[util.formatTagTitle(field.tag)] = field.text

		return device

	def parseService(self, xml):

		# find SCPDURL: REQUIRED. URL for service description

		service = Service()

		for field in xml:
			service.parameters[util.formatTagTitle(field.tag)] = field.text

		print service.parameters

		return service

	def parseServiceList(self, xml):

		services = [ ]

		for field in xml:
			if 'service' == util.formatTagTitle(field.tag):
				services.append(self.parseService(field.getchildren()))

		return services

	def processXML(self, xmlContents, fields):

		xml = ET.parse(xmlContents).getroot()

		print 'Processing'

		device = None

		for field in xml.getchildren():
			if 'Device' in field.tag.title():
				device = self.parseDevice(field.getchildren())

		#print device.parameters, device.service

		if device != None:

			device.fields = fields
			self.downloadActionsDescription(device)

			#self.notifyObservers(device)

	def downloadActionsDescription(self, device):

		threadObserver = threading.Thread(target = DLNAMediaServer.downloadActionsDescriptionThread, args = (device,))
		threadObserver.start()


	def notifyObservers(self, device):
		
		for observer in self.observer:
			threadObserver = threading.Thread(target = DLNAMediaServer.downloadActionsDescriptionThread, args = (observer, device))
			threadObserver.start()


	def addDLNAServiceObserver(self, observer):

		self.observer.append(observer)


	def observe(self, upnp, fields):

		if not ('LOCATION' in fields):
			print 'LOCATION field not field'
			return

		try:

			xmlContents = self.downloadRootFile(fields['LOCATION'])

		except Exception as e:
			print 'Failed to download root file', e

		else:
			self.processXML(xmlContents, fields)


	@staticmethod
	def downloadActionsDescriptionThread(device):
		device.downloadServiceActions()
		

	@staticmethod
	def threadObserverObject(observerObject, device):
		pass

	

if __name__ == '__main__':


	client = upnp.UPNP()
	dlna = DLNAMediaServer(client)
	dlna.registerObserver()
	client.createSocket()
	client.searchDevices(1)
	client.eventsLoop()
