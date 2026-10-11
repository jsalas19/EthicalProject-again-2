# Import required Ryu core components and OpenFlow v1.3
from collections import defaultdict, deque
import os
import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from ryu.lib.packet import packet, ethernet, ipv4
from ryu.ofproto import ofproto_v1_3


# Define a custom Ryu app for detecting DoS attacks and responding with host migration
class DoSDetector(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]  # Use OpenFlow 1.3

    def __init__(self, *args, **kwargs):
        super(DoSDetector, self).__init__(*args, **kwargs)
        self.mac_to_port = {}  # Keeps MAC-to-port mapping per switch
        self.ip_packet_times = defaultdict(deque)  # Tracks packet timestamps per destination IP
        self.attack_state = {}  # Tracks per-IP attack state and cooldowns
        self.window_size = 1.0  # Look back one second for packet bursts
        self.threshold = 5  # Threshold packets/sec to trigger DoS detection
        self.cooldown = 10.0  # Do not retrigger the same destination too quickly

    # Install default flow to send unknown packets to controller
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        # Install flow entry
        mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
        datapath.send_msg(mod)

    def _evaluate_attack(self, dst_ip, now):
        """Check if the destination is currently under attack and trigger migration if needed."""
        packet_times = self.ip_packet_times[dst_ip]
        while packet_times and now - packet_times[0] > self.window_size:
            packet_times.popleft()

        count = len(packet_times)
        state = self.attack_state.setdefault(dst_ip, {"active": False, "last_trigger": 0.0})

        if count >= self.threshold:
            if not state["active"] and (now - state["last_trigger"]) >= self.cooldown:
                self.logger.warning(f"⚠️ POSSIBLE DoS attack on {dst_ip} — {count} packets in {self.window_size:.1f}s")
                state["active"] = True
                state["last_trigger"] = now
                self.migrate_host(dst_ip)
            elif state["active"]:
                self.logger.info(f"DoS detection remains active for {dst_ip} ({count} packets in window)")
        elif state["active"] and count < self.threshold:
            state["active"] = False
            self.logger.info(f"Attack state cleared for {dst_ip}; traffic returned below threshold.")

    # Handle incoming packets (PacketIn events)
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # Parse the incoming packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Count packets by destination IP if it's an IPv4 packet
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            dst_ip = ipv4_pkt.dst
            now = time.time()
            self.ip_packet_times[dst_ip].append(now)
            self._evaluate_attack(dst_ip, now)

        src = eth.src
        dst = eth.dst
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # Learn the source MAC address on the current port
        self.mac_to_port[dpid][src] = in_port

        # Forward the packet out to the correct port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD  # Flood if destination unknown

        actions = [parser.OFPActionOutput(out_port)]
        data = None if msg.buffer_id != ofproto.OFP_NO_BUFFER else msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    # Function to migrate host h3 from s2 to s1
    def migrate_host(self, target_ip):
        host_name = 'h3'
        self.logger.info(f"🚀 Initiating automatic migration of {host_name} due to traffic spike on {target_ip}...")

        cmds = [
            'py net.configLinkStatus("h3", "s2", "down")',
            'py net.addLink(h3, s1)',
            'py h3.cmd("ifconfig h3-eth1 10.0.0.3/8 up")',
            'py h3.cmd("route add default dev h3-eth1")',
            'py h3.cmd("ip link delete h3-eth0")',
            'py s2.detach("s2-eth1")',
            'py net.delLink(next(link for link in net.links if "s2-eth1" in str(link)))',
            'py os.system("/usr/bin/ovs-ofctl del-flows s1 -O OpenFlow13")',
            'py os.system("/usr/bin/ovs-ofctl del-flows s2 -O OpenFlow13")'
        ]

        cmd_file = '/tmp/mncmd'
        if os.path.exists(cmd_file):
            os.remove(cmd_file)

        with open(cmd_file, 'w', encoding='utf-8') as cmd_handle:
            for cmd in cmds:
                cmd_handle.write(f"{cmd}\n")

        time.sleep(2)

        verify = os.popen("ovs-vsctl list-ports s1").read()
        if "s1-eth3" in verify:
            self.logger.info("✅ Host h3 migration verified: h3-eth1 is attached to s1.")
        else:
            self.logger.error("❌ Host h3 migration failed or incomplete.")
            self.logger.error(verify)
