# -*- coding: utf-8 -*-

import json
import optparse
import os

from twisted.internet import defer, reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.python.failure import Failure

from constants import SERVER_STATE, MAP_SCALE, RESPONSE
from helpers import ProgressOutputter
from render import render


def parse_args():
    usage = """usage: %prog --loader=LOADER --height=HEIGHT --width=WIDTH [hostname]:port ..."""
    parser = optparse.OptionParser(usage)

    help = "Map loader, e.g. \"Hawaii/load.ini\"."
    parser.add_option('-l', '--loader', help=help)

    help = "Map height in meters."
    parser.add_option('--height', type='int', help=help)

    help = "Map width in meters."
    parser.add_option('--width', type='int', help=help)

    help = "Output file. Default map's name."
    parser.add_option('-o', '--out', help=help)

    options, addresses = parser.parse_args()
    if not options.loader:
        parser.error("Map loader is not specified.")

    if not options.height:
        parser.error("Map height is not specified.")
    if options.height % MAP_SCALE != 0:
        parser.error("Map height is not proportional to %s." % MAP_SCALE)

    if not options.width:
        parser.error("Map width is not specified.")
    if options.width % MAP_SCALE != 0:
        parser.error("Map width is not proportional to %s." % MAP_SCALE)

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


class HeightmapCreatorClient(LineOnlyReceiver):

    flag = False

    def connectionMade(self):
        self.lineReceived = self.initialLineReceived

    def connectionLost(self, reason):
        if not self.flag:
            return
        end_point = self.transport.getPeer()
        print("Connection with {:}:{:} was closed.".format(
            end_point.host, end_point.port))

    def initialLineReceived(self, line):
        state = SERVER_STATE.lookupByValue(line)
        if state == SERVER_STATE.READY:
            self.flag = True
            self.lineReceived = self.regularLineReceived
            self.factory.clientConnectionSucceeded(self)
        else:
            self.factory.clientConnectionFailed(
                self.transport.getPeer(),
                Failure(Exception("Server is busy.")))

    def regularLineReceived(self, line):
        subdata = json.loads(line)
        if 'response' in subdata:
            response = RESPONSE.lookupByValue(subdata.get('response'))
            self.on_progress = None
            d, self.on_ready = self.on_ready, None
            data, self.data = self.data, None
            if response == RESPONSE.DONE:
                d.callback(data)
            else:
                d.errback((data, subdata['msg']))
        else:
            samples = subdata['samples']
            self.data += samples
            self.receiver.on_progress(len(samples))

    def get_chunks(self, loader, height, width, prange, d, progress_receiver):
        self.receiver = progress_receiver
        self.on_ready = d
        self.data = []
        request = {
            'loader': loader,
            'height': height,
            'width': width,
            'range': prange,
        }
        self.sendLine(json.dumps(request))


class HeightmapCreatorFactory(ClientFactory):

    protocol = HeightmapCreatorClient

    def __init__(self, d):
        self.connecting = d

    def clientConnectionSucceeded(self, connector):
        host = connector.transport.getPeer()
        print("Successfully connected to {:}:{:}.".format(
            host.host, host.port))
        if self.connecting is not None:
            d, self.connecting = self.connecting, None
            d.callback(connector)

    def clientConnectionFailed(self, connector, reason):
        print("Connecting to {:}:{:} failed: {:}".format(
            connector.host, connector.port, reason.value))
        if self.connecting is not None:
            d, self.connecting = self.connecting, None
            d.errback(connector)


def get_chunk_indexes(height, width, num):
    total = (height/MAP_SCALE) * (width/MAP_SCALE)
    last_id = total - 1
    step = total / float(num)
    last = 0.0
    result = []
    while last < last_id:
        left = int(last)
        right = min(int(last+step), last_id)
        result.append((left, right))
        last = right + 1
    return total, result


def get_chunks(loader, height, width, clients):

    total, indexes = get_chunk_indexes(height, width, len(clients))
    progress = ProgressOutputter(total)

    def on_all_data(results):
        progress.on_done()
        result = []
        for status, r in iter(results):
            result += r
        return result

    dl = []
    for idx, client in zip(indexes, clients):
        d = defer.Deferred()
        dl.append(d)
        client.get_chunks(loader, height, width, idx, d, progress)

    return defer.DeferredList(dl, consumeErrors=True).addCallback(on_all_data)


def connect(host, port):
    d = defer.Deferred()
    f = HeightmapCreatorFactory(d)
    reactor.connectTCP(host, port, f)
    return d


def main():
    options, addresses = parse_args()
    map_name = options.loader.split('/', 1)[0]
    out_path = os.path.join(options.out, map_name)
    print("Querying map {:}.".format(map_name))
    print("Putting results to '{:}'.".format(options.out))
    print("Using servers: {:}.".format(
        ', '.join(["%s:%d" % x for x in addresses])))
    print

    def got_result(result):
        from array import array
        height_array = array('H', result)
        with open(out_path, 'wb') as f:
            height_array.tofile(f)
        render(height_array, out_path, (options.height, options.width))

    def connections_done(results):
        clients = [client for status, client in results if status==True]
        print
        if clients:
            d = get_chunks(
                options.loader, options.height, options.width, clients)
            return d.addCallback(got_result).addBoth(lambda _: reactor.stop())
        else:
            print("Failed to connect to any server you specified.")
            reactor.stop()

    dl = [connect(host, port) for (host, port) in addresses]
    dlist = defer.DeferredList(dl, consumeErrors=True)
    dlist.addCallbacks(connections_done)
    reactor.run()

if __name__ == '__main__':
    main()
