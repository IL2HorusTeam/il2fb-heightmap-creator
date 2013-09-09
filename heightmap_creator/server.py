# -*- coding: utf-8 -*-

import optparse

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineOnlyReceiver

from il2ds_middleware.parser import ConsoleParser, DeviceLinkParser
from il2ds_middleware.protocol import ConsoleClientFactory, DeviceLinkClient
from il2ds_middleware import service

from constants import SERVER_STATE


class HeightmapCreatorClient(LineOnlyReceiver):

    def connectionMade(self):
        state = self.factory.connect(self)
        self.sendLine(state.value)
        if state == SERVER_STATE.BUSY:
            self.transport.loseConnection()
            return
        self.factory.client = self
        #TODO:

    def connectionLost(self, reason):
        self.factory.disconnect(self)

    def lineReceived(self, line):
        print line


class HeightmapCreatorClient(ServerFactory):

    protocol = HeightmapCreatorClient

    def __init__(self, dlink, console):
        self.dlink = dlink
        self.console = console
        self.state = SERVER_STATE.READY

    def connect(self, client):
        result = self.state
        if self.state == SERVER_STATE.READY:
            self.state = SERVER_STATE.BUSY
            client.console, client.dlink = self.console, self.dlink
        return result

    def disconnect(self, client):
        self.state = SERVER_STATE.READY
        client.console, client.dlink = None, None


def parse_args():
    usage = """usage: %prog [--host=HOST] [--port=PORT] [--dshost=DSHOST] [--dsport=DSPORT] --log=LOG"""
    parser = optparse.OptionParser(usage)

    help = "The host to listen on. Default is localhost."
    parser.add_option('--host', help=help, default='localhost')

    help = "The port to listen on. Specified by OS By default."
    parser.add_option('--port', type='int', default=0, help=help)

    help = "The host to connect to. Default is localhost."
    parser.add_option('--dshost', help=help, default='localhost')

    help = "The cs_client port to connect to. Default is 20000."
    parser.add_option('--csport', type='int', default=20000, help=help)

    help = "The DeviceLink port to connect to. Default is 20000."
    parser.add_option('--dlport', type='int', default=10000, help=help)

    options, args = parser.parse_args()
    return options


def main():
    options = parse_args()
    dl_address = (options.dshost, options.dlport)
    print "Trying to work with:"
    print "Server cs_client on %s:%d." % (options.dshost, options.csport)
    print "Device Link on %s:%d." % dl_address

    def on_start(_):
        print "Successfully connected to game server."
        f = HeightmapCreatorClient(dl_client, cs_client)
        connector = reactor.listenTCP(options.port, f, interface=options.host)
        host = connector.getHost()
        print "Listening clients on %s:%d." % (host.host, host.port)

    def on_connected(client):
        cs_client = client
        d = dl_client.on_start.addCallback(on_start)
        reactor.listenUDP(0, dl_client)
        return d

    def on_fail(err):
        print "Failed to connect to game server: %s" % err.value
        reactor.stop()

    def on_connection_lost(err):
        print "Connection was lost."

    p = DeviceLinkParser()
    dl_client, cs_client = DeviceLinkClient(dl_address, parser=p), None
    p = ConsoleParser(
        (service.PilotBaseService(), service.MissionBaseService()))
    f = ConsoleClientFactory(parser=p)
    f.on_connecting.addCallbacks(on_connected, on_fail)
    f.on_connection_lost.addErrback(on_connection_lost)
    reactor.connectTCP(options.dshost, options.csport, f)
    reactor.run()


if __name__ == '__main__':
    main()
