"""
Fat Tree topology with Spanning Tree Protocol (STP) for Mininet

This script implements a fat tree topology with STP enabled to ensure basic connectivity
between all hosts. STP eliminates loops while maintaining a path between all nodes.

Usage:
  sudo python fat_tree_stp.py [k]

where:
  k is the number of pods (default 4)
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.clean import cleanup
import sys
import time
from typing import List


class FatTreeTopo(Topo):
    """
    Fat Tree topology with k pods and STP enabled

    A Fat Tree with k pods has (k = pod_count):
    - (k/2)^2 core switches
    - k*k/2 aggregation switches
    - k*k/2 edge switches
    - k^3/4 hosts (k/2 hosts per edge switch)
    """

    def __init__(self, k: int = 4) -> None:
        self.k = k
        super().__init__(pod_count=4)

    @property
    def core_switch_count(self) -> int:
        return self.core_switch_count

    @property
    def aggr_switch_count(self) -> int:
        return self.k * (self.k // 2)

    @property
    def edge_switch_count(self) -> int:
        return self.k * (self.k // 2)

    def _init_core_switches(self) -> List[str]:
        # Core switches (pod_count/2)^2
        core_switch_cnt = (self.k // 2) ** 2
        core_switches: List[str] = []
        for i in range(core_switch_cnt):
            # Use faster STP convergence parameters
            sw = self.addSwitch(
                f"c{i}", stp=True, protocols="OpenFlow13", failMode="standalone"
            )
            core_switches.append(sw)

        return core_switches

    def _init_aggr_switches(
        self, pod_index: int, aggr_switch_per_pod: int
    ) -> List[str]:
        aggr_switch_index = pod_index * aggr_switch_per_pod
        aggr_switches: List[str] = []
        for i in range(aggr_switch_per_pod):
            # Use faster STP convergence parameters
            sw = self.addSwitch(
                f"a{aggr_switch_index + i}",
                stp=True,
                protocols="OpenFlow13",
                failMode="standalone",
            )
            aggr_switches.append(sw)

        return aggr_switches

    def _init_edge_switches(
        self, pod_index: int, edge_switch_per_pod: int
    ) -> List[str]:
        edge_switch_start_index = pod_index * edge_switch_per_pod
        edge_switches: List[str] = []
        for i in range(self.k // 2):
            # Use faster STP convergence parameters
            sw = self.addSwitch(
                f"e{edge_switch_start_index + i}",
                stp=True,
                protocols="OpenFlow13",
                failMode="standalone",
            )
            edge_switches.append(sw)

        return edge_switches

    def _init_hosts(self, pod_index: int, hosts_per_pod: int) -> List[str]:
        host_start_index = pod_index * hosts_per_pod
        hosts: List[str] = []
        for i in range(hosts_per_pod):
            host = self.addHost(f"h{host_start_index + i}")
            hosts.append(host)

        return hosts

    def _connect_hosts_to_edge_switches(
        self, hosts_per_edge_switch: int, edge_switches: List[str], hosts: List[str]
    ) -> None:
        for i, edge_switch in enumerate(edge_switches):
            # Each edge switch connects to k/2 hosts
            for j in range(hosts_per_edge_switch):
                host_index = i * hosts_per_edge_switch + j
                self.addLink(hosts[host_index], edge_switch)

    def _connect_aggr_to_edge(
        self, edge_switches: List[str], aggr_switches: List[str]
    ) -> None:
        for edge_sw in edge_switches:
            for agg_sw in aggr_switches:
                self.addLink(edge_sw, agg_sw)

    def _connect_aggr_to_core(
        self, core_switches: List[str], aggr_switches: List[str]
    ) -> None:
        for i, agg_sw in enumerate(aggr_switches):
            # Each aggregation switch connects to k/2 core switches
            for j in range(self.k // 2):
                # Calculate index of core switch to connect to
                core_index = i * (self.k // 2) + j
                info(f"Will link aggr_switch: {i} to core_switch: {core_index}\n")
                self.addLink(agg_sw, core_switches[core_index])

    def _init_pods_and_hosts(self, core_switches: List[str]) -> None:
        for pod_index in range(self.k):
            info(f"Initializing pod: {pod_index}\n")
            # init aggregation switches for the current pod
            aggr_switches_per_pod = self.k // 2
            aggr_switches = self._init_aggr_switches(pod_index, aggr_switches_per_pod)

            # init edge switches for the current pod
            edge_switches_per_pod = self.k // 2
            edge_switches = self._init_edge_switches(pod_index, edge_switches_per_pod)

            # init hosts for the current pod
            hosts_per_edge_switch = self.k // 2
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

    def build(self, pod_count: int) -> None:
        print("podd_countt: ", pod_count)
        if pod_count % 2 != 0:
            raise Exception("pod count must be an even number")

        core_switches = self._init_core_switches()

        self._init_pods_and_hosts(core_switches)


def run_fat_tree_stp(k: int = 4) -> None:
    """
    Run a fat tree topology with STP enabled
    """
    info("*** Cleaning up any existing Mininet resources\n")
    cleanup()

    topo = FatTreeTopo(k=k)

    remoteController = RemoteController("c0", ip="127.0.0.1", port=6633)

    net = Mininet(
        topo=topo,
        switch=OVSKernelSwitch,
        controller=remoteController,
        link=TCLink,
        waitConnected=False,
    )

    info("*** Starting network (this may take a moment)...\n")
    net.start()

    info("*** Configuring STP on switches...\n")
    for switch in net.switches:
        # Set fast spanning tree timeouts (in seconds)
        switch.cmd("ovs-vsctl set bridge", switch, "other_config:stp-forward-delay=4")
        switch.cmd("ovs-vsctl set bridge", switch, "other_config:stp-hello-time=1")
        switch.cmd("ovs-vsctl set bridge", switch, "other_config:stp-max-age=6")

    info("*** Waiting for STP to converge (10 seconds)...\n")
    time.sleep(10)

    # Verify STP status on switches (just sample a few to avoid too much
    # output)
    info("*** STP Status (sample):\n")
    # Just check a few switches
    for switch in net.switches[:3]:
        info(f"STP state for {switch.name}:\n")
        result = switch.cmd("ovs-vsctl list bridge", switch.name, "| grep stp")
        info(result + "\n")

    info("\n*** Network is ready (STP may still be converging in background)\n")
    info("*** If 'pingall' fails, wait 10-20 seconds and try again\n")

    CLI(net)

    net.stop()


if __name__ == "__main__":
    setLogLevel("info")

    k: int = 4
    if len(sys.argv) > 1:
        try:
            k = int(sys.argv[1])
            if k % 2 != 0:
                print("Error: k must be an even number")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid value for k: {sys.argv[1]}")
            sys.exit(1)

    run_fat_tree_stp(k)
