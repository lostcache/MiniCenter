# Trans-Balancer

A configurable Fat Tree topology implementation with SDN controller for Mininet.

## Requirements

- Python 3.9.18
- Mininet (http://mininet.org/download/)
- Open vSwitch
- Ryu (for the controller)

## Installation

```
git clone https://github.com/lostcache/trans_balancer.git
cd trans_balancer
pyenv local 3.9.18
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Start the Controller

Start the Ryu controller:

```
ryu-manager simple_controller.py
```

### Run the Fat Tree Topology

Run with default configuration (4 pods):

```
sudo python fat_tree.py
```

Specify a different number of pods (must be an even number):

```
sudo python fat_tree.py 6
```

### Run in one command

```
ryu-manager simple_controller.py & python fat_tree.py
```

### Check the fat-tree network in miniet cli

```
mininet> pingall
```

- Note: it might take multiple tries for pingall to reach 100% connectivity since STP might still be converging in the background.

### clean exit

```
mininet> exit
```

### Controller Details

The included `simple_controller.py` implements:

- Basic learning switch functionality
- MAC address learning
- Flow installation with timeouts
- Packet handling for standard Ethernet frames

## Troubleshooting

- Run all commands with sudo privileges
- Ensure Mininet and Open vSwitch are properly installed
- Start the controller before running the topology
- If connectivity issues occur, wait 10-20 seconds for STP to converge
- Default controller connection is 127.0.0.1:6633

## License

MIT
