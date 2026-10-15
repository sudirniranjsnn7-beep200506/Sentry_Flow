# Network Simulation - FlowSentry

This directory contains Cisco Packet Tracer simulation files for demonstrating network traffic classification.

## Purpose

- Satisfies course requirement for network simulator integration
- Demonstrates networking concepts (topology, IP addressing, routing)
- Generates sample traffic for FlowSentry classification
- Provides visual demonstration for viva presentation

## Directory Structure

```
simulation/
├── packet_tracer/
│   └── flowsentry_topology.pkt    # Packet Tracer project file
├── pcaps/
│   ├── web_browsing.pcap          # HTTP traffic sample
│   ├── voip.pcap                  # VoIP traffic sample
│   ├── streaming.pcap             # Streaming traffic sample
│   └── file_transfer.pcap         # FTP traffic sample
└── README.md                      # This file
```

## Prerequisites

**Cisco Packet Tracer** must be installed:
- Download from: https://www.netacad.com/courses/packet-tracer (requires free account)
- Version: 8.0 or later recommended
- Platform: Windows/macOS/Linux

## Quick Start

1. Open `packet_tracer/flowsentry_topology.pkt` in Packet Tracer
2. Navigate to Simulation Mode
3. Follow traffic generation steps in `docs/simulation/traffic_scenarios.md`
4. Export PCAPs to `pcaps/` directory
5. Use PCAPs with FlowSentry:
   ```powershell
   python -m inference.pcap_classifier --pcap simulation/pcaps/web_browsing.pcap
   ```

## Network Topology Overview

```
[Client1: Web]     [Client2: VoIP]     [Client3: Stream]     [Client4: FTP]
      |                   |                    |                    |
      |                   |                    |                    |
      -------------------------------------------------------------------
                                    |
                              [Switch]
                                    |
                                [Router]
                                    |
      -------------------------------------------------------------------
      |                   |                    |                    |
[Web Server]        [VoIP Server]      [Streaming Server]    [FTP Server]
 192.168.1.100       192.168.1.101       192.168.1.102       192.168.1.103
```

## Traffic Classes

| Traffic Type | Source | Destination | Service | Port |
|--------------|--------|-------------|---------|------|
| Web Browsing | Client1 (192.168.1.10) | Web Server (192.168.1.100) | HTTP | 80 |
| VoIP | Client2 (192.168.1.11) | VoIP Server (192.168.1.101) | Voice | 5060 |
| Streaming | Client3 (192.168.1.12) | Streaming Server (192.168.1.102) | RTSP | 554 |
| File Transfer | Client4 (192.168.1.13) | FTP Server (192.168.1.103) | FTP | 21 |

## Integration with FlowSentry

1. **Generate Traffic:**
   - Use Packet Tracer to simulate traffic
   - Capture at Router interface

2. **Export PCAP:**
   - Save capture as .pcap file
   - Place in `simulation/pcaps/`

3. **Classify with FlowSentry:**
   - Load trained model from registry
   - Run classification on Packet Tracer PCAPs
   - Verify correct classification

4. **Demo Flow:**
   - Show Packet Tracer topology
   - Generate live traffic
   - Capture and classify in real-time
   - Display results on dashboard

## Notes

- PCAPs from Packet Tracer are simulated traffic
- Primary training data still from ISCX-VPN2016 dataset
- Packet Tracer PCAPs for demonstration and supplementary testing
- Does not replace real-world traffic capture

## Documentation

See `docs/simulation/` for:
- `topology.md` - Detailed topology design
- `traffic_scenarios.md` - Traffic generation procedures
- `screenshots/` - Visual documentation

## Troubleshooting

**Packet Tracer won't open .pkt file:**
- Ensure you're using Packet Tracer 8.0+
- Try opening Packet Tracer first, then File → Open

**PCAP export fails:**
- Ensure traffic has been generated in Simulation Mode
- Check that capture was started before traffic generation
- Verify Router interface is selected for capture

**FlowSentry can't read PCAP:**
- Check PCAP format (should be standard libpcap)
- Try opening in Wireshark first to verify
- Ensure CICFlowMeter adapter is working (CN-013)

## Related Tasks

- **CN-023:** Network Topology Design & Packet Tracer Integration
- **CN-013:** CICFlowMeter Integration (needed to process PCAPs)
- **CN-015:** PCAP Inference (classification pipeline)
- **CN-021:** Demo Packaging (final presentation)

---

**Status:** Directory structure created, ready for Packet Tracer topology implementation.
