from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os
import time
import threading


class MyTopo(Topo):
    """
    Custom topology:
    - Two switches (s1, s2)
    - Three hosts (h1, h2, h3)
    - Links:
        - h1 <-> s1
        - h2 <-> s1
        - h3 <-> s2
        - s1 <-> s2
    """
    def build(self):
        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')

        host1 = self.addHost('h1')
        host2 = self.addHost('h2')
        host3 = self.addHost('h3')

        self.addLink(host1, switch1)
        self.addLink(host2, switch1)
        self.addLink(host3, switch2)
        self.addLink(switch1, switch2)


def process_mncmd(net):
    """Background loop to execute commands from /tmp/mncmd every second."""
    h3 = net.get('h3')
    s2 = net.get('s2')
    s1 = net.get('s1')
    h1 = net.get('h1')
    h2 = net.get('h2')

    while True:
        command_file = '/tmp/mncmd'
        if os.path.exists(command_file):
            with open(command_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                cmd = line.strip()
                if cmd:
                    print(f"*** Executing CLI command: {cmd}")
                    try:
                        if cmd.startswith('py '):
                            exec(cmd[3:], {'net': net, 'h3': h3, 's2': s2, 's1': s1, 'h1': h1, 'h2': h2, 'os': os})
                        else:
                            os.system(cmd)
                    except Exception as e:
                        print(f"❌ Error executing '{cmd}': {e}")
            os.remove(command_file)
        time.sleep(1)


def run():
    """Start the Mininet network with the custom topology and background cmd handler."""
    topo = MyTopo()
    net = Mininet(topo=topo, controller=RemoteController, switch=OVSSwitch, link=TCLink)
    net.start()
    info("\n[Topology] Network started. Use 'pingall' or 'iperf' to test.\n")

    # Start background command processor
    threading.Thread(target=process_mncmd, args=(net,), daemon=True).start()

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()

