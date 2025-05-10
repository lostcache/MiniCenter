#!/usr/bin/python

"""
load_balancing_demo.py: Demonstrate load balancing capabilities in Fat Tree topology

This script creates a Fat Tree topology and demonstrates its load balancing
capabilities by generating traffic between hosts and monitoring link utilization.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
import time
import os
import sys

# Import the FatTreeTopo class
from fat_tree import FatTreeTopo


def run_load_balancing_demo(k=4):
    """
    Create and run a Fat Tree topology with load balancing demonstration

    Args:
        k (int): Number of pods (must be even)
    """
    # Create Fat Tree topology with k pods
    topo = FatTreeTopo(k=k)

    # Set up the network with TCLinks to enable bandwidth control
    net = Mininet(topo=topo, switch=OVSKernelSwitch, controller=None, link=TCLink)

    # Add controller - can be replaced with custom controller for advanced load balancing
    net.addController("c0", controller=RemoteController, ip="127.0.0.1", port=6653)

    net.start()

    # Show network topology
    info("\n*** Network topology:\n")
    dumpNodeConnections(net.hosts)

    # Wait for the network to initialize
    info("\n*** Waiting for network to stabilize...\n")
    time.sleep(2)

    # Calculate the number of hosts in the network (k^3/4)
    num_hosts = (k**3) // 4

    # Get the first and last hosts for our test
    h1 = net.get(f"h1")
    hLast = net.get(f"h{num_hosts}")

    # Start iperf server on the last host
    info(f"\n*** Starting iperf server on {hLast.name}\n")
    hLast.cmd("iperf -s -u &")
    time.sleep(1)  # Give it time to start

    # First test: Single flow
    info(f"\n*** Running single flow test from {h1.name} to {hLast.name}\n")
    h1.cmd(f"iperf -c {hLast.IP()} -u -b 10M -t 10 &")

    # Wait for the first test to complete
    info("*** Waiting for single flow test to complete...\n")
    time.sleep(12)

    # Second test: Multiple parallel flows to demonstrate load balancing
    info("\n*** Running multiple parallel flows to demonstrate load balancing\n")
    num_flows = min(8, num_hosts // 2)  # Use at most 8 flows

    # Start multiple parallel iperf flows from different hosts
    for i in range(1, num_flows + 1):
        src = net.get(f"h{i}")
        info(f"*** Starting flow from {src.name} to {hLast.name}\n")
        src.cmd(f"iperf -c {hLast.IP()} -u -b 10M -t 20 -p {5000+i} &")

    # Start monitoring script
    info("\n*** Monitoring link utilization...\n")

    # Function to check link utilization on a switch
    def check_utilization(switch_name):
        switch = net.get(switch_name)
        info(f"*** Link statistics for {switch_name}:\n")
        result = switch.cmd("ovs-ofctl dump-ports", switch_name)
        info(result + "\n")

    # Monitor some core switches
    for i in range(1, min((k // 2) ** 2 + 1, 5)):  # Monitor up to 4 core switches
        check_utilization(f"c{i}")
        time.sleep(1)

    info('\n*** Type "exit" or press Ctrl+D to exit\n')
    CLI(net)

    # Clean up
    info("\n*** Stopping network\n")
    net.stop()


if __name__ == "__main__":
    # Set log level
    setLogLevel("info")

    # Default number of pods
    k = 4

    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            k = int(sys.argv[1])
            if k % 2 != 0:
                print("Error: k must be an even number")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid value for k: {sys.argv[1]}")
            sys.exit(1)

    # Run the demo
    run_load_balancing_demo(k)
