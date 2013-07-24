from scorebot.standard.staticflagbot.EggValidator import EggValidator
from scorebot.standard.staticflagbot.EggCollector import EggCollector

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
