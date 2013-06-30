#!/usr/bin/python -u

import os, random, time, sys, string

from autobahn.websocket import WebSocketClientProtocol
from autobahn.websocket import WebSocketClientFactory, connectWS
from twisted.internet import reactor
import json

from utility import pybrowse, browserpersonality, CtfUtil

class FlagClientProtocol(WebSocketClientProtocol):
    
    def onConnect(self, conn):
        #this is where cookies should be available.
        return None
    
    def onOpen(self):
        self.factory.logFile.write("Poll Socket Open \n")
        j = {'flag':self.factory.flag}
        self.sendMessage(json.dumps(j))
          
    def connectionMade(self):
        WebSocketClientProtocol.connectionMade(self)#always before your code
        self.factory.logFile.write("Poll Connection Made \n")
        self.factory.connections.append(self)
        
    def connectionLost(self,reason):
        self.factory.connections.remove(self)
        WebSocketClientProtocol.connectionLost(self, reason)#always after your code
        self.factory.logFile.close()
        reactor.stop()
        
    def onMessage(self, msg, binary):
        self.factory.observer(msg)
        
def flagObserver(msg):
    #need to print to std out the cookie and old flag.
    j = json.loads(msg)
    if(j['oldflag']!='none'):
        print "FLAG:",j['oldflag']  
        
def score(ip,flag,cookie):
    #create a websocket conn to ip & port
    try:
        fd = os.open("./var/"+ip+".txt",os.O_RDWR | os.O_CREAT)
        f = os.fdopen(fd,"r+")
        
        factory = WebSocketClientFactory("ws://"+ip+":8081/stash",debug=True)
        factory.flag = flag
        factory.logFile = f
        factory.connections = [] 
        factory.observer = flagObserver
        factory.protocol = FlagClientProtocol
        connectWS(factory)
        reactor.run()
        f.close()
        sys.exit(0)
    except Exception as e:
        print e
        f.close()
        sys.exit(1)

if __name__ == "__main__":
    CtfUtil.main(score)