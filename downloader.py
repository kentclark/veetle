import time, re, subprocess, os, signal, pycurl, cStringIO, itertools, random, threading
#~ from datetime import datetime
import datetime
from urlparse import urlparse
ua='"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.13) Gecko/2009080316 Ubuntu/8.04 (hardy) Firefox/3.0.13"'
args=' --connect-timeout 20 --socks5 localhost:'
def getChannelHostPort(chn_id):
	Curl = curl('http://www.veetle.com/channel.php?op=getChannelHostPort&cid=' + chn_id, 8)
	Curl.start()
	Curl.finished.wait()
	Curl.file.seek(0)
	ChannelHostPort = Curl.file.getvalue()
	if ChannelHostPort[:3] == 'ok|':
		(ip, ports) = ChannelHostPort[3:].split(':')
		ports = ports.split(',')
		return ip, int(ports[0]), int(ports[1]), int(ports[2])
	else:
		return 0
class curl(threading.Thread):
	def __init__(self, url, ctimeout):
		threading.Thread.__init__(self)
		self.c = pycurl.Curl()
		self.c.setopt(pycurl.FOLLOWLOCATION, 1)
		self.c.setopt(pycurl.MAXREDIRS, 5)
		self.c.setopt(pycurl.NOSIGNAL, 1)
		self.c.setopt(pycurl.WRITEFUNCTION, self.fwrite)
		self.c.setopt(pycurl.CONNECTTIMEOUT, ctimeout)
		self.c.setopt(pycurl.USERAGENT, ua)
		self.c.setopt(pycurl.URL, url)
		self.c.setopt(pycurl.HEADERFUNCTION, self.header)
		self.c.setopt(pycurl.NOPROGRESS, 0)
		self.c.setopt(pycurl.PROGRESSFUNCTION, self.progress)
		self.url = url
		self.filename = self.getfilename()
		self.size = 0
		self.contentlen = False
		self.downloaded = 0
		self.percent = 0
		self.proxy = '-'
		self.resume_from = 0
		self.lastchk = datetime.datetime.now()
		self.lastdl = 0		
		self.speed = 0
		self.time_left = '--:--:--'
		self.cancel = False
		self.file = cStringIO.StringIO()
		self.finished = threading.Event()
		pass
	def header(self, buf):
		try:
			self.statuscode = int( re.findall(r'^HTTP\/1\.[0-2]\s*([1-5][0-9][0-9]).*\s*$', buf, re.M + re.I)[0] )
		except: pass
		try:
			contentlen = re.findall(r'^Content-Length:\s*(.*)\s*$', buf, re.M + re.I)[0]
			if self.statuscode >= 200 and self.statuscode < 300:
				self.size = int(contentlen)
				self.contentlen = True
				if self.size < self.resume_from:
					return pycurl.E_WRITE_ERROR
		except: pass
	def progress(self, download_t, download_d, upload_t, upload_d):
		now = datetime.datetime.now()
		elapsed = now - self.lastchk
		if elapsed.seconds > 1:
			speed = (download_d - self.lastdl) / ( elapsed.seconds + (elapsed.microseconds / 1000000.0) )
			self.speed = int(speed / 1024)
			if speed:
				secs_left =  int( (download_t - download_d) / speed )
				self.time_left = '%8s' % str(datetime.timedelta(seconds = secs_left))
			else:
				self.time_left = '--:--:--'
			#~ print speed, self.speed, self.time_left
			self.lastchk = now
			self.lastdl = download_d
			if self.cancel:
				return pycurl.E_WRITE_ERROR
	def setproxy(self, port):
		self.c.setopt(pycurl.PROXY,'localhost:' + port)
		self.c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
	def run(self):
		if self.resume_from:
			self.c.setopt(pycurl.RESUME_FROM, self.resume_from)
		try:
			self.c.perform()
			self.time_left = '00:00:00'
			self.speed = 0
			self.finished.set()
			self.url = self.c.getinfo(pycurl.EFFECTIVE_URL)
			self.filename = self.getfilename()
			self.size = int( self.c.getinfo(pycurl.SIZE_DOWNLOAD) )
		except pycurl.error: 
			self.c.close()
			self.finished.set()
		#~ except pycurl.error: pass
	def fwrite(self, buf):
		self.downloaded += len(buf)
		self.file.write(buf)
		self.file.flush()
		if self.contentlen:
			self.percent = int(100.0 * self.downloaded / self.size)
		else:
			self.size = self.downloaded
			self.percent = 100
	def getfilename(self):
		o = urlparse(self.url)
		path = o.path.split('/')
		filename = path[len(path) - 1]
		if filename == '':
			return 'index.html'
		else:
			return filename