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

from scorebot.standard.staticflagbot.EggValidator import EggValidator
from scorebot.standard.staticflagbot.EggCollector import EggCollector
from scorebot.standard.submitbot.FlagValidator import FlagValidator
from scorebot.standard.submitbot.FlagCollector import FlagCollector

from scorebot.standard.staticflagbot.SharedObjects import *

class StaticFlagServerProtocol(WebSocketServerProtocol):
     
    def onConnect(self,connectionRequest):  
        #print dir(connectionRequest)
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
        setSharedEggValidator(EggValidator(len(conf.teams),flag_conf.duration))
        setSharedEggCollector(EggCollector())

        #Get the correct *relative* path from wherever it is being executed
        FILE_PATH = os.path.relpath(os.path.dirname(__file__),sys.path[0])
        self.logger.info("FilePath: %s"%FILE_PATH)
        f = open(FILE_PATH+'/eggs.txt','r')
        self.staticFlags = [line[:-1] for line in f]
        
        for team in conf.teams:
            assert(team.id == len(TEAM_DATA))
            #cidr_ip,cidr_mask_txt = team.cidr.split("/")
            self.logger.info("Team Host: %s"%team.host)
            #team_ip = extractNetworkValue(team.host,int(cidr_mask_txt))
            TEAM_DATA.append((team.id,team.host))

        FLAG_MANAGER = conf.buildFlagManager()
    
        self.frontEndListeners={}               
        self._setUpListener("staticflag", self.port, StaticFlagServerProtocol,self._handle)
        
    def _handle(self,conn,msg):   
        #deal with the flag submission here.
        # validate IP address of submitter
        # validate the flag; mark the flag as validated and submitted
        j = json.loads(msg)
        flag_txt = str(j['flag'])
        hacker_ip = conn.peer.host
        self.logger.info("Hacker IP: %s"%hacker_ip)
        hacker_id = -1
        for id, team_ip in TEAM_DATA:
            self.logger.info("team IP: %s"%team_ip)
            if(hacker_ip == team_ip ):
                hacker_id = id
                break              
            #if(extractNetworkValue(hacker_ip,cidr_size) == net):
            #    hacker_id = id
            #    break
            
        self.logger.info("Static Flag from %s"%hacker_id)
        
        if(hacker_id == -1):
            self.logger.info( "Flag was submitted from an IP not associated with any team!")
            j = {'result':"Invalid Flag"}
            conn.sendMessage(json.dumps(j))
            return
        
        if flag_txt.startswith("EGG"):
            self._validateEgg(flag_txt,hacker_id,conn)
        else:
            self._validateFlag(flag_txt,hacker_id,conn)


    
    def _validateEgg(self,flag_txt,hacker_id,conn):
        try:
            
            if flag_txt in self.staticFlags:
                self.logger.info("Valid Flag Lookup: %s"%flag_txt)
                orig_flag = flag_txt
                #HACK: so we can use the same flag logic for parsing.
                #TODO: make an egg parser!
                flag_txt = "FLG"+flag_txt[3:]
                
                flag_validator = getSharedEggValidator()
                flag_collector = getSharedEggCollector()
                flag = FLAG_MANAGER.toFlag(flag_txt)
    
                result = flag_validator.validate(hacker_id,flag)
        
                if(result == FlagValidator.VALID):
                    self.staticFlags.remove(orig_flag)
                    self.logger.info("Removed Submitted Flag: %s"%orig_flag)
                    self.logger.info("Static Flag Count: %d"%len(self.staticFlags))
                    flag_collector.enque((hacker_id,flag))
                    j = {'result':"Flag Accepted"}
                    conn.sendMessage(json.dumps(j))
                else:
                    j = {'result':result}
                    conn.sendMessage(json.dumps(j))
            else:
                self.logger.info( "Invalid Flag")
                j = {'result':"Invalid Flag"}
                conn.sendMessage(json.dumps(j))

        except FlagParseException as e:
            j = {'result':"Invalid Flag"}
            conn.sendMessage(json.dumps(j))
            self.logger.info( "Invalid Flag! %s"%e)
            
    def _validateFlag(self,flag_txt,hacker_id,conn):
        try:
            flag_validator = getSharedValidator()
            flag_collector = getSharedCollector()

            flag = FLAG_MANAGER.toFlag(flag_txt)
            result = flag_validator.validate(hacker_id,flag)
    
            if(result == FlagValidator.VALID):
                flag_collector.enque((hacker_id,flag))
                j = {'result':"Flag Accepted"}
                conn.sendMessage(json.dumps(j))

            elif(result == FlagValidator.SAME_TEAM):
                j = {'result':"Invalid Flag: Same team!"}
                conn.sendMessage(json.dumps(j))

            elif(result == FlagValidator.EXPIRED):
                j = {'result':"Invalid Flag: Too old!"}
                conn.sendMessage(json.dumps(j))

            elif(result == FlagValidator.REPEAT):
                return "Invalid Flag: Repeated submission!"
                j = {'result':"Invalid Flag: Repeated submission!"}
                conn.sendMessage(json.dumps(j))

        except FlagParseException as e:
                j = {'result':"Invalid Flag!"}
                conn.sendMessage(json.dumps(j))
    
    def _setUpListener(self, serviceName, port, protocol, handler=None):
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
        