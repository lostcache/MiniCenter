# MiniCenter

MiniCenter is an abstraction layer over Mininet and Ryu that enables users to emulate a reasonably realistic datacenter environment for network experimentation, testing, and research.

## Overview

MiniCenter provides a simplified interface for creating and managing datacenter network topologies with the following features:

- **Realistic Datacenter Topologies**: Supports standard datacenter network architectures including Fat Tree, Leaf-Spine, and custom topologies
- **SDN Integration**: Seamless integration with Ryu SDN controller for programmable network control
- **Simplified API**: Abstract away the complexities of Mininet and Ryu configuration
- **Traffic Simulation**: Tools to generate realistic datacenter traffic patterns
- **Performance Monitoring**: Built-in monitoring capabilities for network performance metrics
- **Extensible Framework**: Easily add custom network components and behaviors

## Requirements

- Python 3.9.18
- Mininet (http://mininet.org/download/)
- Open vSwitch
- Ryu (for the controller)

## Installation

```
git clone https://github.com/yourusername/MiniCenter.git
cd MiniCenter
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

### Run Datacenter Topologies

Run with default Fat Tree configuration (4 pods):

```
sudo python fat_tree.py
```

Specify a different number of pods (must be an even number):

```
sudo python fat_tree.py 6
```

<!-- ### Run Leaf-Spine Topology

```
sudo python leaf_spine.py
```

-->

### Run in one command

```
ryu-manager simple_controller.py & python fat_tree.py
```

### Test Connectivity

```
mininet> pingall
```

- Note: it might take multiple tries for pingall to reach 100% connectivity since STP might still be converging in the background.

### Clean Exit

```
mininet> exit
```

## Advanced Features

### Custom Traffic Patterns

MiniCenter allows you to generate realistic datacenter traffic patterns:

```
sudo python traffic_generator.py --pattern hadoop
```

Available patterns: hadoop, webserver, database, mixed

### Network Monitoring

Monitor network performance in real-time:

```
sudo python monitor.py
```

## Architecture

MiniCenter consists of three main components:

1. **Topology Generator**: Creates virtual network topologies that mirror real datacenter architectures
2. **Controller Interface**: Provides SDN control capabilities through Ryu
3. **Simulation Tools**: Generates realistic network traffic and workloads

## Troubleshooting

- Run all commands with sudo privileges
- Ensure Mininet and Open vSwitch are properly installed
- Start the controller before running the topology
- If connectivity issues occur, wait 10-20 seconds for STP to converge
- Default controller connection is 127.0.0.1:6633

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
