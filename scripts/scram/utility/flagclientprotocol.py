from autobahn.websocket import WebSocketClientProtocol
import json
from twisted.internet import reactor
class FlagClientProtocol(WebSocketClientProtocol):
    
    def onConnect(self, conn):
        #this is where cookies should be available.
        return None
    
    def onOpen(self):
        j = {'flag':self.factory.flag}
        self.sendMessage(json.dumps(j))
          
    def connectionMade(self):
        WebSocketClientProtocol.connectionMade(self)#always before your code
        self.factory.connections.append(self)
        
    def connectionLost(self,reason):
        self.factory.connections.remove(self)
        WebSocketClientProtocol.connectionLost(self, reason)#always after your code
        reactor.stop()
        
    def onMessage(self, msg, binary):
        self.factory.observer(msg)