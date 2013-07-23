
from twisted.internet.protocol import DatagramProtocol, Protocol, ServerFactory
from twisted.internet import reactor
from autobahn.websocket import WebSocketServerFactory, \
                            WebSocketServerProtocol, \
                               listenWS
from twisted.python import log
import sys

class StaticFlagServerProtocol(WebSocketServerProtocol):
     
    def onConnect(self,connectionRequest):  
        print( dir(connectionRequest))
        return None
    
    def connectionMade(self):
        WebSocketServerProtocol.connectionMade(self)#always before your code
        print( "connection Made")
        print self.debug
        self.factory.connections.append(self)
        
    def connectionLost(self,reason):
        print( "Connection Lost")
        self.factory.connections.remove(self)
        WebSocketServerProtocol.connectionLost(self, reason)#always after your code
        
    def onMessage(self, msg, binary):
        for f in self.factory.observers:
            f(self,msg)
            
class StaticFlagSocket(object):
    def __init__(self,port=50506,conf=None,reactor=reactor):
        
        self.port = port
        self.conf = conf
        self.reactor = reactor     

        self.frontEndListeners={}
        #load flags into memory here.
               
        self._setUpListener("staticflag", self.port, StaticFlagServerProtocol,self._handle)
        #self.reactor.run()
        
    def _handle(self,conn,msg):   
        #deal with the flag submission here.
        # validate IP address of submitter
        # validate the flag; mark the flag as validated and submitted
        j = json.loads(msg)

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


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    s = StaticFlagSocket()
    s.reactor.run()
    
    