import logging
import threading
import random
import time
import os,sys
from multiprocessing import Process

from scorebot.common.communication.BotCommClient import BotCommClient
from scorebot.common.communication.BotMessage import BotMessage

from scorebot.standard.staticflagbot.SharedObjects import *
from scorebot.standard.staticflagbot.StaticFlagSocket import StaticFlagSocket

from scorebot.common.models.Flag import Flag,FlagManager

"""
rweiss - this bot handles the static flag submissions from the teams 
"""

class WebserverThread(threading.Thread):

	def __init__(self,conf):
		threading.Thread.__init__(self)
		self.conf = conf
		staticflag_conf = self.conf.getSection("STATICFLAG_BOT")
		self.webserver = StaticFlagSocket(staticflag_conf.port,self.conf)

	def run(self):
		self.webserver.reactor.run(installSignalHandlers=False)
		pass

class StaticFlagBot(Process):

	def __init__(self,conf,init=False):
		Process.__init__(self)
		self.conf = conf
		self.comm = None
		self.logger = conf.buildLogger("StaticFlagBot")
		self.init = init
		self.logger.info("In Static Flag Init about to start Webserver")
		self.webserver = WebserverThread(self.conf)
		self.logger.info("In Static Flag Init started Webserver")
		
		self.staticFlagConf = self.conf.getSection("STATICFLAG_BOT")

		if self.staticFlagConf.genflags:
			self.logger.info("Generating Static Flags")
			self._genFlags()
			
	def _genFlags(self):
		path = os.path.relpath(os.path.dirname(__file__),sys.path[0])
		f = open(path+"/flags.txt",'w')
		self.flag_manager = self.conf.buildFlagManager()
		for i in range(0,9999):
			flag = Flag(99,99,9999,i)
			flagText = self.flag_manager.toTxt(flag)
			egg = "EGG"+flag[3:]
			f.write(flagText+"\n")
		f.close()
			
	def run(self):
		self.webserver.start()

		server_info = self.conf.getGameStateServerInfo()
		self.comm = BotCommClient(
			server_info.host,
			server_info.port,
			server_info.key,
			server_info.iv,
			"STATICFLAG_BOT")

		self.running = True

		collector = getSharedCollector()

		try:
			self.comm.start()
			while(self.running):
				#comms hub msg 
				msg = self.comm.receive()
				#got msg to collect the flags and send them to the caller.
				assert(msg.type == "COLLECT_STATIC_FLAGS")
				#collector is the "shared memory" between the webserver and this bot.
				flags = collector.collect()
				#sending the collected flags
				self.comm.send(BotMessage("COLLECT_STATIC_FLAGS_RESULT",flags))
				
			self.comm.kill()
		except Exception as e:
			self.logger("An exception occured in staticflagbot")
	
