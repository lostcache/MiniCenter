# Fat Tree Topology for Mininet

This project implements a configurable Fat Tree topology using Mininet. Fat Tree topologies are commonly used in data center networks to provide high bandwidth, fault tolerance, and improved load balancing through multiple paths between hosts.

## What is a Fat Tree Topology?

A Fat Tree is a specialized multi-rooted tree network topology. Unlike regular tree topologies where bandwidth is reduced as you move up the hierarchy, Fat Trees maintain consistent bandwidth throughout the network. The key characteristics are:

- Non-blocking: Full bandwidth available between any pair of hosts
- Multiple paths: Provides redundancy and load balancing capabilities
- Scalable: Can be easily expanded to accommodate more hosts

In a k-ary Fat Tree:
- There are k pods
- Each pod contains k/2 edge switches and k/2 aggregation switches
- There are (k/2)² core switches
- Each edge switch connects to k/2 hosts
- Total hosts: k³/4

## Requirements

- Python 2.7+ or Python 3
- Mininet (http://mininet.org/download/)
- Open vSwitch
- (Optional) An SDN controller like Ryu, ONOS, or OpenDaylight

## Installation

```
git clone https://github.com/yourusername/trans_balancer.git
cd trans_balancer
```

## Usage

Run the fat tree topology with the default configuration (4 pods):

```
sudo python fat_tree.py
```

To specify a different number of pods (k must be an even number):

```
sudo python fat_tree.py 6
```

## Network Details

For a Fat Tree with k=4:
- 4 core switches 
- 8 aggregation switches (2 per pod)
- 8 edge switches (2 per pod)
- 16 hosts (2 hosts per edge switch)

## Using with Controllers

By default, the implementation uses a RemoteController listening on 127.0.0.1:6653. To use a different controller:

1. Start your controller (e.g., `ryu-manager simple_switch.py`)
2. Modify the controller IP/port in `fat_tree.py` if necessary
3. Run the Fat Tree topology

## Customization

You can modify the `FatTreeTopo` class to change various aspects of the topology:
- Switch naming scheme
- Link properties (bandwidth, delay)
- Host configuration

## Troubleshooting

- Ensure you're running the script with sudo privileges
- Verify that Mininet is properly installed
- If using a controller, make sure it's running before starting the topology

## License

MIT