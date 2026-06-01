#!/usr/bin/env python3

from mininet.node import RemoteController, OVSSwitch
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mnoptical.dataplane import OpticalNet as Mininet, km, m, dB, dBm
from mnoptical.dataplane import UnidirectionalOpticalLink as ULink, Terminal
from mnoptical.ofcdemo.lroadm import LROADM, NetconfPortBase
from mnoptical.rest import RestServer
from mnoptical.ofcdemo.netconfserver import NetconfServer
from mnoptical.ofcdemo.demolib import OpticalCLI as CLI, cleanup
import sys

class OpticalRingTopo(Topo):
    ethbase = 0
    hostport = 200
    txbase = 100
    rxbase = 200
    listenPortBase = 6653
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.txcount = 1
        self.build_topology()
        
    def wdmLink(self, src, dst, port1, port2, spans=(1*m,), **params):
        params.setdefault('cls', ULink)
        self.addLink(src, dst, port1, port2, spans=spans, **params)
        
    def addNetworkNodes(self, i, name, power=0*dBm):
        transceivers = tuple((f'tx{i}', power) for i in range(self.txcount))
        topts = {'transceivers': transceivers, 'monitor_mode': 'in'}
        host, switch, term, roadm = f'h{i}', f's{i}', f't{i}', name
        self.addHost(host)
        self.addSwitch(switch, listenPort=self.listenPortBase+i, protocols='OpenFlow14')
        self.addSwitch(term, cls=Terminal, **topts)
        ncport = NetconfPortBase + i
        self.addSwitch(roadm, cls=LROADM, netconfPort=ncport)
        
        # Internal links
        self.addLink(host, switch, port2=self.hostport)
        for j in range(1, self.txcount+1):
            self.addLink(switch, term, self.ethbase+j, self.ethbase+j)
            self.wdmLink(term, roadm, self.txbase+j, LROADM.addbase+j)
            self.wdmLink(roadm, term, LROADM.dropbase+j, self.rxbase+j)

    def build_topology(self):
        # 4 Nodes
        self.addNetworkNodes(1, 'ROADM-1')
        self.addNetworkNodes(2, 'ROADM-2')
        self.addNetworkNodes(3, 'ROADM-3')
        self.addNetworkNodes(4, 'ROADM-4')
            
        # Connect ROADMs based on topology.json distances
        # ROADM-1 -> ROADM-2 (215km)
        spans_1_2 = [215*km, ('amp1_2', 0.22*215*dB)]
        self.wdmLink('ROADM-1', 'ROADM-2', LROADM.lineout, LROADM.linein, spans_1_2)
        
        # ROADM-2 -> ROADM-3 (150km)
        spans_2_3 = [150*km, ('amp2_3', 0.22*150*dB)]
        self.wdmLink('ROADM-2', 'ROADM-3', LROADM.lineout, LROADM.linein, spans_2_3)
        
        # ROADM-3 -> ROADM-4 (140km)
        spans_3_4 = [140*km, ('amp3_4', 0.22*140*dB)]
        self.wdmLink('ROADM-3', 'ROADM-4', LROADM.lineout, LROADM.linein, spans_3_4)

        # ROADM-4 -> ROADM-1 (160km)
        spans_4_1 = [160*km, ('amp4_1', 0.22*160*dB)]
        self.wdmLink('ROADM-4', 'ROADM-1', LROADM.lineout, LROADM.linein, spans_4_1)

def run():
    cleanup()
    setLogLevel('info')
    
    topo = OpticalRingTopo()
    
    # Use ONOS as remote controller (port 30653 is exposed by k3s)
    c0 = RemoteController('c0', ip='127.0.0.1', port=30653)
    net = Mininet(topo=topo, controller=None)
    net.addController(c0)
    
    # Start servers (username 'onos' corresponds to ONOS controller defaults)
    restServer = RestServer(net, port=8085)
    netconfServer = NetconfServer(net, username='onos', password='rocks')
    
    info('*** Starting Network ***\n')
    net.start()
    restServer.start()
    netconfServer.start()
    
    info('*** Network Running. Open ONOS UI at http://localhost:30181/onos/ui/ ***\n')
    info('*** To exit, type "exit" or press Ctrl+D ***\n')
    CLI(net)
    
    # Cleanup
    netconfServer.stop()
    restServer.stop()
    net.stop()

if __name__ == '__main__':
    run()
