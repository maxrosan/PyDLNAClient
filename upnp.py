

import socket, struct, select, time
import Queue

class UPNP:

	def __init__(self):
		self.MCAST_GROUP = '239.255.255.250'
		self.MCAST_PORT  = 1900
		self.sock = None
		self.queueOutput = Queue.PriorityQueue() # time, period, host, port, message
		self.observers = [ ]

	def addObserver(self, objectReference, matchFields):

		self.observers.append((matchFields, objectReference))

	def createSocket(self):
	
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

		sock.bind(('', self.MCAST_PORT))

		mreq = struct.pack('=4sl', socket.inet_aton(self.MCAST_GROUP), socket.INADDR_ANY)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

		self.sock = sock

	def buildMessage(self, headerString, messageParameters):

		message = headerString + '\r\n'

		for key in messageParameters:
			message += key + ': ' + messageParameters[key] + '\r\n'

		message += '\r\n'

		return message

	def parseLine(self, line):

		key = ''
		value = ''
		state = 0 # 0 - key, 1 - value

		for i in range(0, len(line)):
			if state == 0:
				if line[i] != ':':
					key += line[i]
				else:
					state = 1
			elif state == 1:
				value += line[i]

		key = key.strip()
		value = value.strip()

		return (key, value)

	def parseReceivedResponse(self, response):
	
		lines = response.split('\r\n')
		
		headerResponseCode = lines[0]

		if headerResponseCode == 'HTTP/1.1 200 OK':

			print 'Processing response'

			hashFields = { }

			for lineIndex in range(1, len(lines)):
				key, value = self.parseLine(lines[lineIndex])
				hashFields[key] = value
				#print key, value

			for observers in self.observers:
				
				observerFields = observers[0]
				observerObjectReference = observers[1]

				matched = True

				for fieldName in observerFields:
					matched = matched and \
					( fieldName in hashFields ) and ( hashFields[fieldName] == observerFields[fieldName] )
	
				if matched:
					observerObjectReference.observe(self, hashFields)
					

		else:
			print 'Response not processed: ', headerResponseCode


	def eventsLoop(self):

		if self.sock == None:
			print 'It is necessary to create a socket first'
			return

		READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
		READ_WRITE = READ_ONLY | select.POLLOUT

		pollSocket = select.poll()
		pollSocket.register(self.sock, READ_WRITE)
		
		while True:

			events = pollSocket.poll(1000)

			for fdEvent, flag in events:
				if fdEvent == self.sock.fileno():

					if flag & (select.POLLIN | select.POLLPRI):

						self.parseReceivedResponse(self.sock.recv(1024))

					elif flag & select.POLLOUT:
						try:
 							timeValue, period, host, port, message = self.queueOutput.get_nowait()
 						except Queue.Empty:
							pass
						else:
							if timeValue <= time.time():
								self.sock.sendto(message, (host, port))
								if period > 0:
									self.queueOutput.put((time.time() + period, period, host, port, message))	
								print "Sending message"
							else:
								self.queueOutput.put((timeValue, period, host, port, message))
						

	def scheduleMessage(self, timeDelay, period, host, port, message):
		self.queueOutput.put((time.time() + timeDelay, period, host, port, message))

	def searchDevices(self, timeDelay):

		params = { 'HOST': '239.255.255.250',
		 'MAN': '"ssdp:discover"',
		 'MX': '3',
		 'ST': 'urn:schemas-upnp-org:device:MediaServer:1',
		}

		message = self.buildMessage('M-SEARCH * HTTP/1.1', params)
		self.scheduleMessage(timeDelay, 0, self.MCAST_GROUP, self.MCAST_PORT, message)

		print "Sending search"

	def dumpListen(self):

		if self.sock == None:
			print 'It is necessary to create a socket first'
			return

		while True:
			print self.sock.recv(1024)


if __name__ == '__main__':

	client = UPNP()
	client.createSocket()
	client.searchDevices(1)
	client.eventsLoop()
