import asyncore, socket, binascii, struct, random, threading
stunservers = ['stun01.sipphone.com', 'stun.xten.com']
class udpclient(asyncore.dispatcher):
	def __init__(self, dst, bindport):
		self.dst = dst
		self.bindport = bindport
		self.recvbuf = ''
		self.sendbuf = ''
		self.finished = threading.Event()
		asyncore.dispatcher.__init__(self)
	def cn(self):
		try:
			self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.set_reuse_addr()
			self.bind( ('', self.bindport) )
		except socket.error, errmsg:
			#~ print 'Error creating socket!', errmsg
			self.handle_close()
			return False
		try:
			self.connect(self.dst)
		except socket.error, errmsg:
			if errmsg[0] == 99:
				pass # EADDRNOTAVAIL
			else:
				#~ print 'sock error connecting', errmsg, dst
				pass
			self.handle_close()
	def handle_write(self):
		try:
			sent = self.send(self.sendbuf)
			self.sendbuf = self.sendbuf[sent:]
			#~ print 'Sent'
		except socket.error, errmsg:
			#~ print 'Error trying send!', errmsg, self.dst
			self.handle_close()
	def handle_read(self):
		try:
			data = self.recv(8192)
		except socket.error, errmsg:
			if errmsg[0] == 110:
				pass # Connection timeout
			elif errmsg[0] == 111:
				pass # Connection refused
			else:
				#~ print 'Error trying recv!', errmsg, self.dst
				pass
			self.handle_close()
			return False
		self.recvbuf += data
		self.proc_recv()
	def proc_recv(self): pass
	def readable(self): return True
	def writable(self):
		try: return (len(self.sendbuf) > 0)
		except AttributeError: return False
	def handle_close(self):
		self.close()
		self.finished.set()
	def handle_connect(self): pass #~ print 'Handle connect', self.connected, self.closing
	def handle_expt(self):
		#~ open('/dev/dsp','w').write(''.join(chr(128 * (1 + math.sin(math.pi * 440 * i / 100.0))) for i in xrange(1000)))
		if not self.connected:
			#~ print '\nExpt: not connected'
			pass
		else:
			#~ print 'Handle expt', self.dst
			self.handle_close()
class stunclient(udpclient, threading.Thread):
	def __init__(self, dst, bindport, stun_timeout=8):
		threading.Thread.__init__(self)
		self.stun_timeout = stun_timeout
		self.IPv4 = None
		self.port = None
		self.trans_id = '%.32x' % random.randint(1, 0xffffffffffffffffffffffffffffffff) # random 128-bit number
		udpclient.__init__(self, dst, bindport)
	def run(self):
		self.cn()
		self.sendbuf = binascii.unhexlify('00010000' + self.trans_id)
		for x in range(self.stun_timeout):
			try:
				asyncore.poll2(timeout=1.0)
			except: pass
		self.handle_close()
	def proc_recv(self):
		msgtype = struct.unpack_from('!H', self.recvbuf, 0)[0]
		if msgtype != 0x0101:
			print 'Invalid response type!'
			return
		msglen = struct.unpack_from('!H', self.recvbuf, 2)[0]
		
		offset = 20
		while offset < msglen:
			(type, fielddata, offset, bytesize) = self.parse_field(self.recvbuf, offset)
			if type == 0x0001:
				family = struct.unpack_from('!H', fielddata, 0)[0]
				self.port = struct.unpack_from('!H', fielddata, 2)[0]
				if family == 0x0001:
					self.IPv4 = self.IntToDottedIP( struct.unpack_from('!L', fielddata, 4)[0] )
				#~ elif family == 0x0002:
					#~ self.IPv6 = struct.unpack_from('!Q', fielddata, 4)[0]
		self.handle_close()
	def parse_field(self, data, offset):
		(type, length) = struct.unpack_from('!HH', data, offset)
		fielddata = data[(offset + 4):(offset + 4 + length)]
		return type, fielddata, (offset + 4 + length), length
	def IntToDottedIP(self, intip):
		octet = ''
		for exp in [3,2,1,0]:
			octet = octet + str(intip / ( 256 ** exp )) + "."
			intip = intip % ( 256 ** exp )
		return(octet.rstrip('.'))
def getIP():
	for stund in stunservers:
		stunc = stunclient( (stund, 3478), 33388)
		stunc.start()
		stunc.finished.wait()
		ip = stunc.IPv4
		if ip:
			return ip
	return ip