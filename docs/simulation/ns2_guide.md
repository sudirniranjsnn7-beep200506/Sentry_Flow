# FlowSentry Network Simulation Guide: NS-2 & Cisco Packet Tracer

**Task:** CN-023 - Dual Simulator Integration (Packet Tracer & Network Simulator 2)  
**Academic Requirement:** Fulfills both GUI-based enterprise topology (Cisco Packet Tracer) and discrete-event packet tracing (NS-2).

---

## 1. Cisco Packet Tracer Setup

### Topology Overview
- **Clients:** 10.0.0.10 (Web), 10.0.0.11 (VoIP), 10.0.0.12 (Streaming), 10.0.0.13 (FTP)
- **Switch:** Cisco Catalyst 2960-24TT (SW1, VLAN 1)
- **Router:** Cisco 2911 (R1 Gateway: Gi0/0 = 10.0.0.1, Gi0/1 = 10.0.1.1 - Capture Point)
- **Servers:** 10.0.1.100 (Web HTTP), 10.0.1.101 (VoIP SIP/RTP), 10.0.1.102 (Streaming Media), 10.0.1.103 (vsftpd)

### Exporting PCAPs from Packet Tracer
1. Switch to **Simulation Mode** (Shift + S).
2. Filter for TCP, UDP, HTTP, SIP, RTSP, FTP.
3. Generate traffic from clients.
4. Export the capture file from Router R1 interface Gi0/1 as `.pcap`.
5. Upload or load directly into FlowSentry's PCAP Classifier tab.

---

## 2. NS-2 (Network Simulator 2) Setup

### Running the OTcl Script
Run NS-2 on Linux / WSL / macOS:
```bash
# Execute simulation script
ns simulation/ns2/flowsentry_topology.tcl

# Launch Network Animator (NAM)
nam flowsentry.nam
```

### Trace File Analysis (`flowsentry.tr`)
NS-2 generates 12-column event traces:
```text
Event(+/-/r/d) Time From To PktType PktSize Flags FlowId SrcAddr DstAddr SeqNum PktId
+ 0.500000 1 4 cbr 160 ------- 2 1.0 7.0 0 1
```

- `FlowId 1` (Blue): Web Browsing (`Agent/TCP` + `Application/Traffic/Exponential`)
- `FlowId 2` (Green): VoIP Audio (`Agent/UDP` + `Application/Traffic/CBR`, 160 bytes @ 20ms interval)
- `FlowId 3` (Purple): Streaming Media (`Agent/TCP` + `Application/Traffic/CBR`, 1400 bytes @ 2.5 Mbps)
- `FlowId 4` (Amber): File Transfer (`Agent/TCP/Newreno` + `Application/FTP`, bulk transfer with DropTail drops `d`)

FlowSentry parses these trace events, calculates statistical flow features, and verifies classification accuracy against the ground truth flow IDs.
