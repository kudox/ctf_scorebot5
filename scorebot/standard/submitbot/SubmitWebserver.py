import socket
import SocketServer
import re
import sys
import os
import cgi
import struct 

from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from scorebot.common.models.Flag import FlagParseException, Flag
from scorebot.standard.submitbot.FlagValidator import FlagValidator
from scorebot.standard.submitbot.FlagCollector import FlagCollector
from scorebot.standard.submitbot.SharedObjects import *

VALID_FILE_REGEX = re.compile("^(/)?\w+\.(html|css|jpg)$")
FILE_PATH = "/"
TEAM_DATA = []
FLAG_MANAGER = None

def extractNetworkValue(ip_txt,masksize):
	mask = (2L<<masksize-1)-1
	ip = struct.unpack('I',socket.inet_aton(ip_txt))[0] 
	return ip & mask

class SubmitHttpHandler(SimpleHTTPRequestHandler):
	def send_head(self):
		"""Common code for GET and HEAD commands.

		This sends the response code and MIME headers.

		Return value is either a file object (which has to be copied
		to the outputfile by the caller unless the command was HEAD,
		and must be closed by the caller under all circumstances), or
		None, in which case the caller has nothing further to do.

		"""
		path = self.translate_path(self.path)
		f = None
		if os.path.isdir(path):
			if not self.path.endswith('/'):
				# redirect browser - doing basically what apache does
				self.send_response(301)
				self.send_header("Location", self.path + "/")
				self.end_headers()
				return None
			for index in "index.html", "index.htm":
				index = os.path.join(path, index)
				if os.path.exists(index):
					path = index
					break
			else:
				return self.list_directory(path)
		ctype = self.guess_type(path)
		try:
			# Always read in binary mode. Opening files in text mode may cause
			# newline translations, making the actual size of the content
			# transmitted *less* than the content-length!
			f = open(path, 'rb')
		except IOError:
			self.send_error(404, "File not found")
			return None
		self.send_response(200)
		self.send_header("Content-type", ctype)
		fs = os.fstat(f.fileno())
		self.send_header("Content-Length", str(fs[6]))
		self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
		self.send_header('Access-Control-Allow-Origin', '*')
		self.end_headers()
		return f
	
	def do_GET(self):
		if(VALID_FILE_REGEX.search(self.path) != None or self.path == "/"):
			self.path = FILE_PATH+self.path
			SimpleHTTPRequestHandler.do_GET(self)
		else:
			self.send_response(404)
			self.end_headers()
			
	def do_OPTIONS(self):
		self.send_response(200, "OK")
		self.send_header('Access-Control-Allow-Origin', '*')
		self.send_header('Access-Control-Allow-Methods', 'POST, GET, HEAD, OPTIONS')
		self.send_header('Access-Control-Max-Age', '30')
		self.send_header("Access-Control-Allow-Headers", "origin, x-requested-with, content-type")  
		self.send_header('Content-Type', 'text/html')
		self.end_headers()
		
	def do_POST(self):

		try:
			contentType, ct_dict = cgi.parse_header(self.headers.getheader('content-type'))
			length_str,cl_dict = cgi.parse_header(self.headers.getheader('content-length'))
			
			data = cgi.parse_qs(self.rfile.read(int(length_str)))
			result = self.__update(self.client_address[0],data['flag'][0])
			#result = self.__update(self.client_address[0],"test")
	
			self.send_response(200)
			self.end_headers()
			header = open(FILE_PATH+os.sep+"result_header.html")
			footer = open(FILE_PATH+os.sep+"result_footer.html")
	
			self.wfile.write(header.read())
			self.wfile.write(result)
			self.wfile.write(footer.read())
		except Exception as e:
			self.send_response(500)
			self.wfile.write(e)
			print"Flag Submission Error",e

	def __update(self,hacker_ip,flag_txt):
		hacker_id = -1
		for id, net, cidr_size in TEAM_DATA:
			if(extractNetworkValue(hacker_ip,cidr_size) == net):
				hacker_id = id
				break

		if(hacker_id == -1):
			return "Flag was submitted from an IP not associated with any team!"
	
		#TODO: Flag submission frequency check

		try:
			flag_validator = getSharedValidator()
			flag_collector = getSharedCollector()

			flag = FLAG_MANAGER.toFlag(flag_txt)
			result = flag_validator.validate(hacker_id,flag)
	
			if(result == FlagValidator.VALID):
				flag_collector.enque((hacker_id,flag))
				return "Flag accepted!"

			elif(result == FlagValidator.SAME_TEAM):
				return "Invalid Flag: Same team!"

			elif(result == FlagValidator.EXPIRED):
				return "Invalid Flag: Too old!"

			elif(result == FlagValidator.REPEAT):
				return "Invalid Flag: Repeated submission!"

		except FlagParseException as e:
			return "Invalid Flag!"
			
	def log_message(self, format, *args):
		pass

class SubmitWebserver(SocketServer.ThreadingMixIn,HTTPServer):

	def __init__(self,port,conf):
		global FILE_PATH
		global TEAM_DATA
		global FLAG_MANAGER

		HTTPServer.__init__(self,('',port),SubmitHttpHandler)
		
		#will likely move where these shared objects are created
		flag_conf = conf.getSection("FLAG")
		setSharedValidator(FlagValidator(len(conf.teams),flag_conf.duration))
		setSharedCollector(FlagCollector())

		#Get the correct *relative* path from wherever it is being executed
		FILE_PATH = os.path.relpath(os.path.dirname(__file__),sys.path[0])

		for team in conf.teams:
			assert(team.id == len(TEAM_DATA))
			cidr_ip,cidr_mask_txt = team.cidr.split("/")
			team_ip = extractNetworkValue(team.host,int(cidr_mask_txt))
			TEAM_DATA.append((team.id,team_ip,int(cidr_mask_txt)))

		FLAG_MANAGER = conf.buildFlagManager()

	def serve(self):
		SocketServer.TCPServer.allow_reuse_addr = True
		self.serve_forever()
