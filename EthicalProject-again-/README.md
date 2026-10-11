# EthicalProject: SDN DoS Detection and Host Migration

This project is a small proof-of-concept Mininet + Ryu application that detects a potential denial-of-service condition and automatically migrates a host from one switch to another.

The design is intentionally simple and focused on demonstrating the core idea rather than being production-ready or scalable.

## What it does

- Builds a small Mininet topology with two Open vSwitch instances and three hosts
- Uses a Ryu controller to monitor packet-in events
- Tracks traffic bursts for destination IPs within a rolling time window
- Triggers a migration when a destination exceeds the configured threshold
- Writes a set of Mininet commands to `/tmp/mncmd` so the topology can react to the alert

## Project layout

- `backend/dos_detector.py` – Ryu controller logic for packet inspection and attack detection
- `backend/my_topology.py` – Mininet topology and command processing loop
- `install.sh` – environment setup script for Ubuntu-based systems
- `run.sh` – launches the controller and topology in separate terminals
- `requirements.txt` – Python dependency list

## Requirements

This project expects a Linux environment with:

- Python 3.8
- Mininet
- Open vSwitch
- Ryu 4.34
- Eventlet 0.30.2

## Installation

From the project directory:

```bash
chmod +x install.sh run.sh
./install.sh
```

The script installs the required OS packages and creates a Python virtual environment before installing the project dependencies.

## Running the demo

```bash
bash run.sh
```

This starts:

1. the Ryu controller in one terminal window
2. the Mininet topology in another terminal window

Once the topology is running, you can test the setup with commands such as:

```bash
pingall
```

Then generate extra traffic toward a host to trigger the detection threshold and observe the migration behavior.

## Notes on the prototype

This is intentionally a lightweight prototype. Some of the current trade-offs include:

- a single-host migration flow rather than a general purpose policy engine
- command execution through a temporary file for demonstration purposes
- hard-coded host and switch names for simplicity
- a basic threshold and cooldown approach, not a production-grade mitigation system

## Suggested future improvements

- Add time-window tracking that is more precise and easier to tune
- Replace command-file-based migration with cleaner Mininet API calls or a safer command queue
- Add per-host attack state instead of a single global migration flag
- Add recovery logic to restore the original topology after an attack is over
- Expose threshold, cooldown, and window values via configuration
- Add logging and tests for normal and attack conditions


