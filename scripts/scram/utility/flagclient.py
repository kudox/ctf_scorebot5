import os, random, time, sys, string

from autobahn.websocket import WebSocketClientFactory, connectWS
from twisted.internet import reactor
import json

from utility import pybrowse, browserpersonality, CtfUtil
from utility.flagclientprotocol import FlagClientProtocol

class FlagClient(object):
    
    def __init__(self,port):
        self.port = port
        
    def flagObserver(self,msg):
        j = json.loads(msg)
        try:
            if(j['oldflag']!='none'):
                print "FLAG:",j['oldflag']  
        except KeyError:
            print "Old Flag not present!! You should not see this msg!!",msg
            
    def score(self,ip,flag,cookie):
        try:       
            factory = WebSocketClientFactory("ws://"+ip+":"+str(self.port)+"/stash",debug=True)
            factory.flag = flag
            factory.connections = [] 
            factory.observer = self.flagObserver
            factory.protocol = FlagClientProtocol
            connectWS(factory)
            reactor.run()
            sys.exit(0)
        except Exception as e:
            print "exception",e
            sys.exit(1)