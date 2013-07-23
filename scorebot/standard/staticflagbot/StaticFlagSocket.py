"""
This is the websocket handler process for the submission of the static flags from the teams.
The client implementation is left to the vuln server. This will define the API for submitting static flags.


"""
import re
import sys
import os
import cgi
import struct 
import json
import socket
import logging

from twisted.internet.protocol import DatagramProtocol, Protocol, ServerFactory
from twisted.internet import reactor
from autobahn.websocket import WebSocketServerFactory, \
                            WebSocketServerProtocol, \
                               listenWS
                               
from scorebot.common.models.Flag import FlagParseException, Flag
from scorebot.standard.staticflagbot.FlagValidator import FlagValidator
from scorebot.standard.staticflagbot.FlagCollector import FlagCollector
from scorebot.standard.staticflagbot.SharedObjects import *

class StaticFlagServerProtocol(WebSocketServerProtocol):
     
    def onConnect(self,connectionRequest):  
        print dir(connectionRequest)
        return None
    def connectionMade(self):
        WebSocketServerProtocol.connectionMade(self)#always before your code
        self.factory.connections.append(self)
        
    def connectionLost(self,reason):
        self.factory.connections.remove(self)
        WebSocketServerProtocol.connectionLost(self, reason)#always after your code
        
    def onMessage(self, msg, binary):
        for f in self.factory.observers:
            f(self,msg)
            
FILE_PATH = "/"
TEAM_DATA = []
FLAG_MANAGER = None

def extractNetworkValue(ip_txt,masksize):
    mask = (2L<<masksize-1)-1
    ip = struct.unpack('I',socket.inet_aton(ip_txt))[0] 
    return ip & mask
           
class StaticFlagSocket(object):
    def __init__(self,port,conf,reactor=reactor):
        global FILE_PATH
        global TEAM_DATA
        global FLAG_MANAGER
        
        self.port = port
        self.conf = conf
        self.reactor = reactor
        self.logger = conf.buildLogger("StaticFlagSocket")
        
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
        

        self.frontEndListeners={}
        #load flags into memory here.
               
        self._setUpListener("staticflag", self.port, StaticFlagServerProtocol,self._handle)
        #self.reactor.run()
        
    def _handle(self,conn,msg):   
        #deal with the flag submission here.
        # validate IP address of submitter
        # validate the flag; mark the flag as validated and submitted
        j = json.loads(msg)
        
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
        pass
    
    def _setUpListener(self, serviceName, port, protocol, handler=None):
        #print("[" + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + "]" + " Setting Up Listener")
        url = "ws://localhost:%d"%(port)       
        factory = WebSocketServerFactory(url, debug=True, debugCodePaths=True)    
        factory.protocol = protocol
        factory.setProtocolOptions(allowHixie76=True)
        
        #HACK: add an array for observing messages
        factory.observers = [] #called for every message; for the ui to listen
        
        if handler !=None:
            factory.observers.append(handler)
        
        factory.connections = [] #all connections that are active; for the protocol to send data
        self.frontEndListeners[serviceName] = factory
        listenWS(self.frontEndListeners[serviceName]) 
        