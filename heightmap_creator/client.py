# -*- coding: utf-8 -*-

import optparse

from twisted.internet import defer, reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.python.failure import Failure

from constants import SERVER_STATE


class HeightmapCreatorClient(LineOnlyReceiver):

    def connectionMade(self):
        self.lineReceived = self.initialLineReceived

    def connectionLost(self, reason):
        # TODO:
        pass

    def initialLineReceived(self, line):
        state = SERVER_STATE.lookupByValue(line)
        if state == SERVER_STATE.READY:
            self.factory.clientConnectionSucceeded(self)
            self.lineReceived = self.usualLineReceived
        else:
            self.factory.clientConnectionFailed(
                self.transport.getPeer(),
                Failure(Exception("Server is busy.")))

    def usualLineReceived(self, line):
        # TODO:
        pass


class HeightmapCreatorFactory(ClientFactory):

    protocol = HeightmapCreatorClient

    def __init__(self, d):
        self.connecting = d

    def clientConnectionSucceeded(self, connector):
        host = connector.transport.getPeer()
        print "Successfully connected to {:}:{:}.".format(
            host.host, host.port)
        if self.connecting is not None:
            d, self.connecting = self.connecting, None
            d.callback(connector)

    def clientConnectionFailed(self, connector, reason):
        print "Connecting to {:}:{:} failed: {:}".format(
            connector.host, connector.port, reason.value)
        if self.connecting is not None:
            d, self.connecting = self.connecting, None
            d.errback(connector)


def parse_args():
    usage = """usage: %prog --map=MAP --height=HEIGHT --width=WIDTH [hostname]:port ..."""
    parser = optparse.OptionParser(usage)

    help = "Map loader, e.g. \"Hawaii/load.ini\"."
    parser.add_option('-l', '--loader', help=help)

    help = "Map height in meters."
    parser.add_option('--height', help=help)

    help = "Map width in meters."
    parser.add_option('--width', help=help)

    help = "Output file. Default map's name."
    parser.add_option('-o', '--out', help=help)

    options, addresses = parser.parse_args()
    if not options.loader:
        parser.error("Map loader is not specified.")
    if not options.height:
        parser.error("Map height is not specified.")
    if not options.width:
        parser.error("Map width is not specified.")
    if not addresses:
        parser.error("At least one server address must be specified.")

    def parse_address(addr):
        if ':' not in addr:
            host = '127.0.0.1'
            port = addr
        else:
            host, port = addr.split(':', 1)
        if not port.isdigit():
            parser.error('Ports must be integers.')
        return host, int(port)

    return options, map(parse_address, addresses)


def get_chunks(loader, height, width, clients):
    d = defer.Deferred()
    #TODO:
    return d

def connect(host, port):
    d = defer.Deferred()
    f = HeightmapCreatorFactory(d)
    reactor.connectTCP(host, port, f)
    return d


def main():
    options, addresses = parse_args()
    map_name = options.loader.split('/', 1)[0]
    options.out = options.out or map_name
    print "Querying map {:}.".format(map_name)
    print "Putting result to '{:}'.".format(options.out)
    print "Using servers: {:}.".format(
        ', '.join(["%s:%d" % x for x in addresses]))
    print

    def got_result(result):
        # TODO:
        print result

    def connections_done(results):
        clients = [client for status, client in results if status==True]
        print
        if clients:
            d = get_chunks(
                options.loader, options.height, options.width, clients)
            return d.addCallback(got_result).addBoth(lambda _: reactor.stop())
        else:
            print "Failed to connect to any server you specified."
            reactor.stop()

    ds = [connect(host, port) for (host, port) in addresses]
    dlist = defer.DeferredList(ds, consumeErrors=True)
    dlist.addCallbacks(connections_done)
    reactor.run()

if __name__ == '__main__':
    main()
