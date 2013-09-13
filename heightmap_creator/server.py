# -*- coding: utf-8 -*-

import json
import optparse
import os

from twisted.internet import defer, reactor
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineOnlyReceiver

from il2ds_middleware.parser import ConsoleParser
from il2ds_middleware.protocol import ConsoleClientFactory, DeviceLinkClient
from il2ds_middleware import service

from constants import (SERVER_STATE, MAP_SCALE, MAX_HEIGHT, RESPONSE,
    MAX_OBJECTS_ON_MAP, MISSION_TEMPLATE, DS_CONSOLE_TIMEOUT, DL_TIMEOUT,
    MAX_TCP_BUFFER_SIZE, )
from helpers import ProgressOutputter


def parse_args():
    usage = """usage: %prog [--host=HOST] [--port=PORT] [--dshost=DSHOST] [--csport=CSPORT] [--dlport=DLPORT] --dir=DIR"""
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

    help = "Path to the server's dogfight missions directory."
    parser.add_option('--dir', help=help)

    options, args = parser.parse_args()
    if options.dir is None:
        parser.error("Path to missions directory is not set.")
    return options


class HeightmapCreatorClient(LineOnlyReceiver):

    peer = None
    MAX_LENGTH = MAX_TCP_BUFFER_SIZE

    def connectionMade(self):
        end_point = self.transport.getPeer()
        peer = "{:}:{:}".format(end_point.host, end_point.port)
        print "Connection from {:}...".format(peer),
        state = self.factory.connect()
        self.sendLine(state.value)
        if state == SERVER_STATE.BUSY:
            self.transport.loseConnection()
            print "rejected."
            return
        self.peer = peer
        print "accepted."

    def connectionLost(self, reason):
        if self.peer is not None:
            peer, self.peer = self.peer, None
            print("Connection with %s was closed." % peer)
        self.factory.disconnect()

    def lineReceived(self, line):
        data = json.loads(line)
        reactor.callLater(0, self._query_range, data, MAX_OBJECTS_ON_MAP)

    @defer.inlineCallbacks
    def _query_range(self, data, step):
        start, stop = tuple(data.pop('range'))
        left = start
        total = stop - start
        progress = ProgressOutputter(total)
        self.chunks = []

        while left < stop:
            if self.peer is None:
                print "Aborted."
                defer.returnValue(False)

            right = min(left+step-1, stop)
            yield self._do_query(xrange(left, right+1), data)
            progress.on_progress(right-left)
            left = right + 1

        if left == stop:
            yield self._do_query([left, ], data)
            progress.on_progress(1)

        progress.on_done()
        for chunk in self.chunks:
            data = { 'chunk': chunk, }
            self.sendLine(json.dumps(data))
        self.chunks = None
        data = { 'response': RESPONSE.DONE.value, }
        self.sendLine(json.dumps(data))
        self.transport.loseConnection()

    def _do_query(self, idxs, data):

        def on_results(results):
            if self.peer is not None:
                samples = [int(s[s.rfind(';')+1:]) for s in iter(results)]
                self.chunks.append(samples)
                self.sendLine(json.dumps({
                    'processed': len(samples),
                }))
            os.remove(fpath)

        mname, fpath = self._generate_mission(idxs, data)
        return self.factory.console.mission_load(mname).addCallback(
            lambda _: self.factory.console.mission_begin()).addCallback(
            lambda _: self.factory.dlink.refresh_radar()).addCallback(
            lambda _: self.factory.dlink.all_static_pos()).addCallback(
                on_results)

    def _generate_mission(self, idxs, data):
        fname = 'heightmap.mis'
        mname = '/'.join(['net', 'dogfight', fname])
        fpath = os.path.join(self.factory.missions_dir, fname)
        with open(fpath, 'w') as f:
            f.write(MISSION_TEMPLATE.format(data['loader']))
            w = int(data['width']/MAP_SCALE)
            for i, idx in enumerate(idxs):
                y, x = divmod(idx, w)
                x *= MAP_SCALE
                x += MAP_SCALE >> 1
                y *= MAP_SCALE
                y += MAP_SCALE >> 1
                y = data['height'] - y
                f.write("  {0}_Static vehicles.stationary.Stationary$Wagon12 2 {1} {2} 360.00 0.0\n".format(
                    i, x, y))
        return mname, fpath


class HeightmapCreatorFactory(ServerFactory):

    protocol = HeightmapCreatorClient

    def __init__(self, dlink, console, missions_dir):
        self.dlink = dlink
        self.console = console
        self.missions_dir = missions_dir
        self.state = SERVER_STATE.READY

    def connect(self):
        result = self.state
        if self.state == SERVER_STATE.READY:
            self.state = SERVER_STATE.BUSY
        return result

    def disconnect(self):
        self.state = SERVER_STATE.READY


def main():
    options = parse_args()
    dl_address = (options.dshost, options.dlport)
    print("Trying to work with:")
    print("Server console client on %s:%d." % (options.dshost, options.csport))
    print("Device Link on %s:%d." % dl_address)

    def on_start(_):
        print("Successfully connected to game server.")
        f = HeightmapCreatorFactory(clients[0], clients[1], options.dir)
        connector = reactor.listenTCP(options.port, f, interface=options.host)
        host = connector.getHost()
        print("Listening clients on %s:%d." % (host.host, host.port))

    def on_connected(client):
        clients.append(client)
        d = dl_client.on_start.addCallback(on_start)
        reactor.listenUDP(0, dl_client)
        return d

    def on_fail(err):
        print("Failed to connect to game server: %s" % err.value)
        reactor.stop()

    def on_connection_lost(err):
        print("Connection was lost.")

    dl_client = DeviceLinkClient(dl_address, timeout_value=DL_TIMEOUT)
    clients = [dl_client, ]
    p = ConsoleParser(
        (service.PilotBaseService(), service.MissionBaseService()))
    f = ConsoleClientFactory(parser=p, timeout_value=DS_CONSOLE_TIMEOUT)
    f.on_connecting.addCallbacks(on_connected, on_fail)
    f.on_connection_lost.addErrback(on_connection_lost)
    reactor.connectTCP(options.dshost, options.csport, f)
    reactor.run()


if __name__ == '__main__':
    main()
