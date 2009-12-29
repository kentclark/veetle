from HTMLParser import HTMLParser
import downloader
class getchannels(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.result = []
		self.div = []
		self.h2 = []
		self.a = []
		Curl = downloader.curl('http://www.veetle.com/frameworked/index.php/listing', 8)
		Curl.start()
		Curl.finished.wait()
		Curl.file.seek(0)
		listing = Curl.file.getvalue()
		self.feed(listing)
	def handle_starttag(self, tag, attrs):
		if tag == 'div':
			self.div.append(attrs)
		if tag == 'h2':
			self.h2.append(attrs)
		if tag == 'a' and self.h2 and not self.a and [('class','grid')] in self.div:
			try:
				cid = dict(attrs)['href'].split('cid=')[1]
				self.result.append( ['', cid] )
			except (KeyError, IndexError): pass
			self.a.append(attrs)
	def handle_endtag(self, tag):
		if tag == 'div':
			self.div.pop()
		if tag == 'h2':
			self.h2.pop()
			if self.a: self.a.pop()
	def handle_data(self, data):
		if self.a and self.h2 and [('class','grid')] in self.div:
			title = data.strip()
			if len(title):
				pos = len(self.result) - 1
				try:
					self.result[pos][0] += title
				except IndexError: pass					
#~ if __name__ == "__main__":
	#~ c = getchannels()
	#~ for x in c.result:
		#~ print 'ID: %s Name: %s' %  (x[1] , x[0])