from mininet.topo import Topo
from connection import ConnectionDist
from typing import List
from utils import rand_dist_arr, uniform_dist_arr
from mininet.log import info
import os


class FatTreeTopo(Topo):
    """
    ===================================================================
                            FAT TREE TOPOLOGY
    ===================================================================

    ** Written by Humman **
    Key feature of fat tree is that the bandwidth between each level of the tree
    is same, regardless of the number of devices involved. This opens multiple
    opportunities for load balancing and fault tolerance.

    -------------------------------------------------------------------
    TOPOLOGY STRUCTURE
    -------------------------------------------------------------------

    For a k-ary Fat Tree:

    Component          | Count                | Description
    -------------------|----------------------|---------------------------
    Pods               | k                    | Basic unit of organization
    Core Switches      | (k/2)²               | Top level switches
    Aggregation Sw.    | k * (k/2)            | k/2 per pod
    Edge Switches      | k * (k/2)            | k/2 per pod
    Hosts              | k³/4                 | k/2 hosts per edge switch

    -------------------------------------------------------------------
    CONNECTIVITY PATTERN
    -------------------------------------------------------------------

    • Edge switch:     connects to (k/2) hosts and (k/2) aggregation switches
                       within its pod

    • Aggregation sw.: connects to (k/2) edge switches within its pod and
                       (k/2) core switches

    • Core switch:     connects to k aggregation switches (one in each pod)

    -------------------------------------------------------------------
    REFERENCES
    -------------------------------------------------------------------

    • Al-Fares, M., Loukissas, A., & Vahdat, A. (2008). A scalable, commodity
      data center network architecture. In Proceedings of the ACM SIGCOMM 2008
      Conference on Data Communication (pp. 63-74).

    • Leiserson, C. E. (1985). Fat-trees: Universal networks for hardware-efficient
      supercomputing. IEEE Transactions on Computers, 100(10), 892-901.

    • Singh, A., et al. (2015). Jupiter Rising: A Decade of Clos Topologies and
      Centralized Control in Google's Datacenter Network. In Proceedings of the
      ACM SIGCOMM 2015.
    """

    def __init__(self, k: int = 4) -> None:
        self.k = k
        self.core_switches = []
        super().__init__(k=4)

    def _init_core_switches(self) -> List[str]:
        core_switch_cnt = (self.k // 2) ** 2
        core_switches: List[str] = []
        for i in range(core_switch_cnt):
            sw = self.addSwitch(
                f"core_{i}", protocols="OpenFlow13", failMode="standalone"
            )
            cmd = f"sudo ovs-vsctl set bridge {sw} protocols=OpenFlow13"
            os.system(cmd)
            core_switches.append(sw)

        return core_switches

    def _init_aggr_switches(
        self, pod_index: int, aggr_switch_per_pod: int
    ) -> List[str]:
        aggr_switch_index = pod_index * aggr_switch_per_pod
        aggr_switches: List[str] = []
        for i in range(aggr_switch_per_pod):
            sw = self.addSwitch(
                f"aggr_{aggr_switch_index + i}",
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
            sw = self.addSwitch(
                f"edge_{edge_switch_start_index + i}",
                protocols="OpenFlow13",
                failMode="standalone",
            )
            edge_switches.append(sw)

        return edge_switches

    def _init_hosts(self, pod_index: int, hosts_per_pod: int) -> List[str]:
        host_start_index = pod_index * hosts_per_pod
        hosts: List[str] = []
        for i in range(hosts_per_pod):
            host = self.addHost(f"host_{host_start_index + i}")
            hosts.append(host)

        return hosts

    def _connect_hosts_to_edge_switches(
        self, hosts_per_edge_switch: int, edge_switches: List[str], hosts: List[str]
    ) -> None:
        for i, edge_switch in enumerate(edge_switches):
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
            for j in range(self.k // 2):
                # Calculate index of core switch to connect to
                core_index = i * (self.k // 2) + j
                self.addLink(agg_sw, core_switches[core_index])

    def _init_pods_and_hosts(self) -> None:
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

            self._connect_hosts_to_edge_switches(
                hosts_per_edge_switch, edge_switches, hosts
            )

            self._connect_aggr_to_edge(edge_switches, aggr_switches)

            self._connect_aggr_to_core(self.core_switches, aggr_switches)

    def build(self, k: int) -> None:
        if k % 2 != 0:
            raise Exception("pod count must be an even number")

        self.core_switches = self._init_core_switches()

        self._init_pods_and_hosts()

    @property
    def radix(self):
        return self.k

    @property
    def n_core(self) -> int:
        return (self.k // 2) ** 2

    @property
    def n_aggr(self) -> int:
        return self.k * (self.k // 2)

    @property
    def n_edge(self) -> int:
        return self.k * (self.k // 2)

    def add_clients(self, n_clients: int, dist: ConnectionDist) -> None:
        assert n_clients > 0
        assert isinstance(dist, ConnectionDist)

        clients = []
        for i in range(n_clients):
            clients.append(self.addHost(f"client_{i}"))

        total = n_clients
        bins = self.n_core
        dist_arr = (
            rand_dist_arr(total, bins)
            if dist == ConnectionDist.RANDOM
            else uniform_dist_arr(total, bins)
        )

        assert len(dist_arr) == self.n_core

        client_index = 0
        for core_index in range(self.n_core):
            for _ in range(dist_arr[core_index]):
                info(f"Connecting client: {client_index} to Core {core_index}\n")
                self.addLink(clients[client_index], self.core_switches[core_index])
                client_index += 1
