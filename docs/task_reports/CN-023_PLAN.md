# Task Report: CN-023 — Network Topology Design & Packet Tracer Integration

**Task ID:** CN-023  
**Task Name:** Network Topology Design & Packet Tracer Integration  
**Phase:** 0.5 (NEW - Network Simulation)  
**Date:** 2026-10-15  
**Status:** 📋 PLANNED - Ready to implement

## What This Task Adds

Creates a Cisco Packet Tracer network topology that demonstrates the four traffic classes FlowSentry classifies (Web Browsing, VoIP, Streaming, File Transfer) and generates sample PCAP files for testing.

## Rationale

**Course Requirement:** Network simulator (Cisco Packet Tracer or NS2) must be included in project.

**Integration Strategy:**
- Minimal scope addition
- Demonstrates networking concepts in viva
- Provides supplementary test data
- Shows practical application of classification

## Files to Create

### Packet Tracer Project:
- `simulation/packet_tracer/flowsentry_topology.pkt` - Main topology file

### Exported PCAPs:
- `simulation/pcaps/web_browsing.pcap`
- `simulation/pcaps/voip.pcap`
- `simulation/pcaps/streaming.pcap`
- `simulation/pcaps/file_transfer.pcap`

### Documentation:
- `docs/simulation/topology.md` - Topology design and IP addressing
- `docs/simulation/traffic_scenarios.md` - Traffic generation procedures
- `docs/simulation/screenshots/` - Topology screenshots for report

## Implementation Requirements

1. **Topology Components:**
   - 1 Router (gateway)
   - 1 Switch
   - 4 Clients (traffic generators)
   - 4 Servers (Web, VoIP, Streaming, FTP)
   - Traffic monitoring point

2. **Services Configuration:**
   - HTTP server (port 80)
   - VoIP services
   - Media streaming
   - FTP server

3. **Traffic Generation:**
   - Web Browsing: HTTP GET requests
   - VoIP: Voice call simulation
   - Streaming: Video/audio stream
   - File Transfer: Large file download

4. **PCAP Export:**
   - Capture at router interface
   - Export separate PCAP per traffic type
   - Label and document each capture

## Dependencies

- **Prerequisites:** Cisco Packet Tracer installed
- **Depends on:** Nothing (can start immediately)
- **Blocks:** Nothing (parallel to existing phases)
- **Integration point:** CN-015 (PCAP Inference can use these PCAPs)

## Estimated Time

- Topology design: 1 hour
- Service configuration: 30 minutes
- Traffic generation: 30 minutes
- PCAP export: 30 minutes
- Documentation: 30 minutes
- **Total: ~3 hours**

## Verification Checklist

- [ ] Packet Tracer installed and working
- [ ] Topology file created and opens correctly
- [ ] All 4 servers configured and running
- [ ] All 4 traffic types generated successfully
- [ ] PCAP files exported and readable
- [ ] Documentation complete with screenshots
- [ ] IP addressing scheme documented
- [ ] Traffic generation steps documented

## Integration with Existing Project

**Does NOT Change:**
- Existing CN-001 through CN-022 tasks
- ISCX-VPN2016 dataset usage
- ML training pipeline
- Model evaluation

**Enhances:**
- CN-015 (PCAP Inference): Can test on Packet Tracer PCAPs
- CN-021 (Demo): Shows topology + real-time classification
- Viva presentation: Visual demonstration of networking concepts

## Expected Output

```
simulation/
├── packet_tracer/
│   └── flowsentry_topology.pkt
├── pcaps/
│   ├── web_browsing.pcap
│   ├── voip.pcap
│   ├── streaming.pcap
│   └── file_transfer.pcap
└── README.md

docs/simulation/
├── topology.md
├── traffic_scenarios.md
└── screenshots/
    ├── topology_overview.png
    ├── web_server_config.png
    ├── voip_config.png
    └── traffic_capture.png
```

## Demo Flow (CN-021 Integration)

1. Open Packet Tracer topology
2. Show network structure (router, switch, clients, servers)
3. Start traffic generation:
   - Client1 → Web Server: HTTP requests
   - Client2 ↔ VoIP Server: Voice call
   - Client3 → Streaming Server: Video stream
   - Client4 → FTP Server: File download
4. Capture traffic at router
5. Export PCAP
6. Run FlowSentry: `python -m inference.pcap_classifier --pcap simulation/pcaps/web_browsing.pcap`
7. Show classification results
8. Repeat for other traffic types

**Demonstrates:**
- Network topology design (networking knowledge)
- Traffic generation (practical application)
- Classification pipeline (ML integration)
- End-to-end system (complete solution)

## Status

- **Prerequisites:** Need Cisco Packet Tracer installed
- **Dependencies:** None
- **Ready to start:** Yes (once Packet Tracer installed)
- **Integration decision:** Documented in `docs/decisions/network_simulator_integration.md`

## Next Actions

1. Install Cisco Packet Tracer (if not already installed)
2. Create simulation/ directory structure
3. Design topology
4. Configure services
5. Generate and export traffic
6. Document everything

---

**Note:** This task satisfies the course requirement for network simulator integration without disrupting the existing ML pipeline. It provides visual demonstration capabilities and supplementary test data.
