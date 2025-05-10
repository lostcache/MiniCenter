"""
fat_tree.py: Implementation of a fat-tree topology for Mininet

A Fat-Tree topology uses a specialized multi-rooted tree hierarchy designed
for data centers, with multiple paths between hosts for improved fault tolerance
and load balancing capabilities.

Usage:
  sudo python fat_tree.py [k]

where k is the number of pods (default 4)
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink


class FatTreeTopo(Topo):
    """
    Fat Tree topology with k pods

    A Fat Tree with k pods has:
    - (k/2)^2 core switches
    - k*k/2 aggregation switches
    - k*k/2 edge switches
    - k^3/4 hosts (k/2 hosts per edge switch)
    """

    def __init__(self, pod_count=4):
        self.pod_count = pod_count
        super().__init__()

    def _init_core_switches(self):
        # Core switches (pod_count/2)^2
        core_switch_cnt = (self.pod_count // 2) ** 2
        core_switches = []
        for i in range(core_switch_cnt):
            sw = self.addSwitch(f"c{i}")
            core_switches.append(sw)

        return core_switches

    def _init_aggr_switches(self, pod_index, aggr_switch_per_pod):
        aggr_switch_index = pod_index * aggr_switch_per_pod
        aggr_switches = []
        for i in range(aggr_switch_per_pod):
            sw = self.addSwitch(f"a{aggr_switch_index + i}")
            aggr_switches.append(sw)

        return aggr_switches

    def _init_edge_switches(self, pod_index, edge_switch_per_pod):
        edge_switch_start_index = pod_index * edge_switch_per_pod
        edge_switches = []
        for i in range(self.pod_count // 2):
            sw = self.addSwitch(f"e{edge_switch_start_index + i}")
            edge_switches.append(sw)

        return edge_switches

    def _init_hosts(self, pod_index, hosts_per_pod):
        host_start_index = pod_index * hosts_per_pod
        hosts = []
        for i in range(hosts_per_pod):
            host = self.addHost(f"h{host_start_index + i}")
            hosts.append(host)

        return hosts

    def _connect_hosts_to_edge_switches(
        self, hosts_per_edge_switch, edge_switches, hosts
    ):
        for i, edge_switch in enumerate(edge_switches):
            # Each edge switch connects to k/2 hosts
            for j in range(hosts_per_edge_switch):
                host_index = i * hosts_per_edge_switch + j
                self.addLink(hosts[host_index], edge_switch)

    def _connect_aggr_to_edge(self, edge_switches, aggr_switches):
        for edge_sw in edge_switches:
            for agg_sw in aggr_switches:
                self.addLink(edge_sw, agg_sw)

    def _connect_aggr_to_core(self, core_switches, aggr_switches):
        for i, agg_sw in enumerate(aggr_switches):
            # Each aggregation switch connects to k/2 core switches
            for j in range(self.pod_count // 2):
                # Calculate index of core switch to connect to
                core_index = i * (self.pod_count // 2) + j
                print("Linking aggr_switch: ", i, " to core: ", core_index)
                self.addLink(agg_sw, core_switches[core_index])

    def _init_pods(self, core_switches):
        for pod_index in range(self.pod_count):
            # init aggregation switches for the current pod
            aggr_switches_per_pod = self.pod_count // 2
            aggr_switches = self._init_aggr_switches(pod_index, aggr_switches_per_pod)

            # init edge switches for the current pod
            edge_switches_per_pod = self.pod_count // 2
            edge_switches = self._init_edge_switches(pod_index, edge_switches_per_pod)

            # init hosts for the current pod
            hosts_per_edge_switch = self.pod_count // 2
            hosts_per_pod = edge_switches_per_pod * hosts_per_edge_switch
            hosts = self._init_hosts(pod_index, hosts_per_pod)

            # connect hosts to the edge switches
            self._connect_hosts_to_edge_switches(
                hosts_per_edge_switch, edge_switches, hosts
            )

            # Connect edge switches to aggregation switches within the same pod
            self._connect_aggr_to_edge(edge_switches, aggr_switches)

            # Connect aggregation switches in current pod to core switches
            self._connect_aggr_to_core(core_switches, aggr_switches)

    def build(self, pod=4):
        if pod % 2 != 0:
            raise Exception("pod count must be an even number")

        core_switches = self._init_core_switches()

        self._init_pods(core_switches)


def run_fat_tree(k=4):
    """Create and run a fat tree network with k pods"""
    topo = FatTreeTopo(pod_count=k)
    net = Mininet(topo=topo, switch=OVSKernelSwitch, controller=None, link=TCLink)

    # Add controller
    net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6653)

    net.start()
    info("*** Network started\n")
    info('*** Type "exit" or press Ctrl+D to exit\n')
    CLI(net)
    net.stop()


if __name__ == "__main__":
    import sys

    setLogLevel("info")

    k = 4
    if len(sys.argv) > 1:
        try:
            k = int(sys.argv[1])
            if k % 2 != 0:
                print("Error: k must be an even number")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid value for k: {sys.argv[1]}")
            sys.exit(1)

    run_fat_tree(k)
