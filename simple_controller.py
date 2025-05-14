from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types


class SimpleController(app_manager.RyuApp):
    """
    A simple controller for Fat Tree topologies.

    This controller implements a basic learning switch that will enable
    connectivity between hosts in the Fat Tree topology.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleController, self).__init__(*args, **kwargs)
        # MAC address table maps MAC addresses to switch ports
        self.mac_to_port = {}
        self.logger.info("Simple Controller Started")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Handle switch connection and install table-miss flow entry.

        A table-miss flow entry sends all unmatched packets to the controller.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Clear flow table on switch connection
        self.clear_flows(datapath)

        # Install table-miss flow entry
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)
        self.logger.info(f"Switch {datapath.id} connected")

    def clear_flows(self, datapath):
        """
        Clear all flows from the switch's flow table.
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Create a flow mod message to delete all flows
        match = parser.OFPMatch()
        instructions = []
        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=match,
            instructions=instructions,
        )
        datapath.send_msg(flow_mod)

    def add_flow(
        self, datapath, priority, match, actions, buffer_id=None, hard_timeout=0
    ):
        """
        Install a flow entry to the switch's flow table.
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                buffer_id=buffer_id,
                priority=priority,
                match=match,
                instructions=inst,
                hard_timeout=hard_timeout,
            )
        else:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=inst,
                hard_timeout=hard_timeout,
            )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handle packet-in events from switches.

        This is the main logic for the learning switch:
        1. Learn the source MAC address and port
        2. If the destination is known, forward to the right port
        3. If unknown, flood the packet
        """
        # If you hit this, you might want to increase the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug(
                "Packet truncated: only %s of %s bytes",
                ev.msg.msg_len,
                ev.msg.total_len,
            )

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        # Get datapath ID to identify the switch
        dpid = datapath.id

        # Initialize mac_to_port table for this switch if not present
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        # Parse the packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP packets
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        # Ignore IPv6 neighbor discovery packets
        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return

        # Get MAC addresses
        dst = eth.dst
        src = eth.src

        # Learn MAC address to avoid FLOOD next time
        self.mac_to_port[dpid][src] = in_port

        # Log packet information
        self.logger.info(
            f"Packet in switch:{dpid} src:{src} dst:{dst} in_port:{in_port}"
        )

        # Determine output port
        if dst in self.mac_to_port[dpid]:
            # Known destination, forward to the right port
            out_port = self.mac_to_port[dpid][dst]
        else:
            # Unknown destination, flood the packet
            out_port = ofproto.OFPP_FLOOD

        # Construct action list
        actions = [parser.OFPActionOutput(out_port)]

        # Install a flow to avoid packet-in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # Install with higher priority and a hard timeout
            self.add_flow(datapath, 1, match, actions, hard_timeout=300)

        # Send packet out to handle the current packet
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)


if __name__ == "__main__":
    print("Run this controller with ryu-manager:")
    print("ryu-manager simple_controller.py")
