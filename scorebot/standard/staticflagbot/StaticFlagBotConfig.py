
import ConfigParser
import os

from scorebot.common.models.ServiceInfo import ServiceInfo
from scorebot.config.ConfigHandler import ConfigHandler

class StaticFlagBotConfigHandler(ConfigHandler):

	def canHandle(self,section):
		return section == "StaticFlagBot"

	def parse(self,cip,section,config):
		assert(config.hasSection("STATICFLAG_BOT") == False),"StaticFlagBot data already defined!"
		staticflagbot_conf = StaticFlagBotConfig()
		staticflagbot_conf.port = cip.getint(section,"port")
		staticflagbot_conf.genflags = cip.getint(section,"genflags")
		config.addSection("STATICFLAG_BOT",staticflagbot_conf)

class StaticFlagBotConfig:

	def __init__(self):
		self.port = None
		self.genflags = False

	def port(self):
		return self.port
	def genflags(self):
		return self.genflags
