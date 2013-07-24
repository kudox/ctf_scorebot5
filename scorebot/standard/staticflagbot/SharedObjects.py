from scorebot.standard.staticflagbot.EggValidator import EggValidator
from scorebot.standard.staticflagbot.EggCollector import EggCollector
from scorebot.standard.submitbot.FlagValidator import FlagValidator
from scorebot.standard.submitbot.FlagCollector import FlagCollector

_shared_validator = None
_shared_collector = None

_shared_egg_validator = None
_shared_egg_collector = None

def setSharedEggValidator(validator):
	global _shared_egg_validator
	_shared_egg_validator = validator

def getSharedEggValidator():
	global _shared_egg_validator
	return _shared_egg_validator

def setSharedEggCollector(collector):
	global _shared_egg_collector
	_shared_egg_collector = collector

def getSharedEggCollector():
	global _shared_egg_collector
	return _shared_egg_collector

def setSharedValidator(validator):
	global _shared_validator
	_shared_validator = validator

def getSharedValidator():
	global _shared_validator
	return _shared_validator

def setSharedCollector(collector):
	global _shared_collector
	_shared_collector = collector

def getSharedCollector():
	global _shared_collector
	return _shared_collector
