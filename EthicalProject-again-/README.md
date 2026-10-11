# SDN Host Migration Under DoS Attack

This project simulates a Software-Defined Networking (SDN) environment using Mininet and Ryu to detect a Denial-of-Service (DoS) attack and automatically relocate the affected host to a different switch to mitigate the attack.

The prototype is designed for research and lab use. It combines:

- a Mininet topology with multiple hosts and switches,
- a Ryu OpenFlow controller that watches traffic patterns,
- a lightweight mitigation routine that moves the victim host when abnormal traffic is detected.

---

## Overview

The topology creates a small SDN network where a host is serving traffic and can be overwhelmed by excessive packet volume. The controller monitors destination IP traffic and triggers a mitigation when a packet threshold is exceeded.

Once the attack is identified, the system attempts to:

1. disable the old link to the compromised host,
2. attach the host to a backup switch,
3. reconfigure the host networking interfaces,
4. clear stale OpenFlow state on the affected switches.

This is a practical example of how an SDN controller can respond dynamically to network-layer attacks.

---

## Project layout

```text
.
├── backend/
│   ├── dos_detector.py    # Ryu controller app for traffic monitoring and mitigation
│   └── my_topology.py     # Mininet network topology
├── install.sh             # environment setup and dependency installation
├── run.sh                 # starts the controller and topology in separate terminals
├── requirements.txt       # Python package dependencies
├── README.md              # project documentation
└── venv38/                # created by install.sh (when using the provided setup)
```

---

## Prerequisites

This project is intended for an Ubuntu-based environment with root or sudo access.

- Ubuntu 20.04 or 22.04
- Python 3.8
- `sudo` access
- `gnome-terminal` for launching separate windows
- Mininet
- Open vSwitch
- `virtualenv` / venv support

---

## Installation

From the project directory, run:

```bash
bash install.sh
```

The installer performs the following:

- updates system packages,
- installs Python 3.8 and required tools,
- installs Mininet and Open vSwitch,
- creates a virtual environment named `venv38`,
- installs the Ryu controller and compatible dependencies.

If you want to install dependencies manually instead, this project expects the packages listed in `requirements.txt` and the controller stack used by the `run.sh` script.

---

## Running the project

Start the simulation by running:

```bash
bash run.sh
```

This script:

- activates the Python virtual environment,
- launches the Ryu controller in one terminal,
- launches the Mininet topology in a separate terminal.

The topology is defined in `backend/my_topology.py`, and the detection logic is in `backend/dos_detector.py`.

---

## Behavior

The DoS detector checks packet flow counts per destination IP and compares them against a threshold value. When the threshold is crossed, it raises an alert and triggers the migration sequence.

Important notes:

- the threshold is intentionally small for a lab environment,
- the script is a prototype, not a hardened production-grade security system,
- network state changes depend on the host environment and switch configuration.

---

## Useful commands

Once the controller and topology are running, you can use Mininet CLI commands like:

```bash
pingall
h1 ping h3
```

You may also inspect switch state with commands such as:

```bash
sudo ovs-vsctl show
sudo ovs-ofctl dump-flows s1
sudo ovs-ofctl dump-flows s2
```

---

## Notes

This project is best suited for educational and research environments where you want to explore:

- SDN control-plane logic,
- OpenFlow traffic monitoring,
- basic attack detection with programmable networking,
- dynamic network response to suspicious traffic patterns.

If you are using this as a coursework or research project, consider documenting the exact topology, thresholds, and any assumptions behind the migration logic in your final write-up.

---


