# Network Simulator Integration Decision

**Date:** 2026-10-15  
**Decision:** Add Cisco Packet Tracer for network topology demonstration and traffic simulation  
**Rationale:** Course requirement mandates network simulator integration

## Integration Strategy

### Why Cisco Packet Tracer (Not NS2)?

1. **Visual Topology:** Easy to show network structure in viva
2. **Traffic Generation:** Can simulate HTTP, VoIP, Streaming, File Transfer
3. **PCAP Export:** Packet Tracer can export PCAP files for analysis
4. **Lower Learning Curve:** GUI-based, easier to demonstrate
5. **Industry Standard:** Widely recognized in networking courses

### Integration Points

**Minimal Scope Addition (Recommended):**

#### Phase 0.5: Network Simulation Task (NEW)
- **CN-023: Network Topology Design & Traffic Generation**
- Create Packet Tracer topology showing:
  - Client machines generating traffic
  - Server providing Web, VoIP, Streaming, File Transfer services
  - Traffic capture point (simulating our ML classification point)
  
- Generate sample traffic for each class:
  - Web Browsing (HTTP/HTTPS)
  - VoIP (simulated voice packets)
  - Streaming (video/audio streams)
  - File Transfer (FTP/large downloads)

- Export PCAPs from Packet Tracer simulation
- Use exported PCAPs as additional test data for FlowSentry

#### How This Fits Current Project:

```text
Phase 0.5 (NEW): Network Simulation
    CN-023: Packet Tracer topology + traffic generation
    ↓
Phase 1-5: (Existing - No changes)
    ML Training on ISCX-VPN2016 dataset
    ↓
Phase 6: PCAP Classification
    CN-013-015: Works with BOTH:
    - ISCX-VPN2016 PCAPs (existing)
    - Packet Tracer generated PCAPs (NEW)
    ↓
Phase 10: Demo
    CN-021: Demo shows:
    - Packet Tracer topology visualization
    - Real-time traffic in Packet Tracer
    - FlowSentry classifying that traffic
```

### Implementation Plan

#### CN-023 Task Specification

**Task ID:** CN-023  
**Task Name:** Network Topology Design & Packet Tracer Integration  
**Phase:** 0.5 (between Phase 0 and Phase 1)  
**Dependencies:** None (can start immediately)

**Goal:** Create a Packet Tracer network topology that demonstrates the four traffic classes FlowSentry classifies, and generate sample PCAP files for testing.

**Why It Is Needed:** Course requirement; demonstrates networking concepts in viva; provides supplementary test data.

**Files/Directories:**
- `simulation/packet_tracer/` - Packet Tracer project files (.pkt)
- `simulation/pcaps/` - Exported PCAPs from Packet Tracer
- `docs/simulation/topology.md` - Topology documentation
- `docs/simulation/traffic_scenarios.md` - Traffic generation scenarios

**Implementation Requirements:**
1. Design network topology with:
   - 1 router (gateway)
   - 1 switch
   - 4 client machines (representing different traffic sources)
   - 4 servers (Web, VoIP, Streaming, FTP)
   - Traffic monitoring point (where capture happens)

2. Configure services:
   - Web Server: HTTP server on port 80
   - VoIP Server: Configure voice services
   - Streaming Server: Video/audio streaming setup
   - FTP Server: File transfer service

3. Generate traffic scenarios:
   - Web Browsing: HTTP GET requests
   - VoIP: Voice call between two clients
   - Streaming: Video stream from server to client
   - File Transfer: Large file download via FTP

4. Export PCAP files:
   - Capture traffic at monitoring point
   - Export one PCAP per traffic type
   - Label PCAPs with traffic class

5. Documentation:
   - Screenshot of topology
   - IP addressing scheme
   - Traffic flow diagrams
   - How to reproduce traffic generation

**Do Not:**
- Replace ISCX-VPN2016 dataset (this is supplementary)
- Build complex routing (simple topology is sufficient)
- Spend more than 1-2 hours on topology design

**Verification:**
- Packet Tracer file opens and shows topology
- PCAP files successfully exported
- PCAPs contain recognizable traffic
- Documentation complete

**Expected Output:**
- `simulation/packet_tracer/flowsentry_topology.pkt` - Packet Tracer project
- `simulation/pcaps/web_browsing.pcap` - Web traffic sample
- `simulation/pcaps/voip.pcap` - VoIP traffic sample
- `simulation/pcaps/streaming.pcap` - Streaming traffic sample
- `simulation/pcaps/file_transfer.pcap` - FTP traffic sample
- `docs/simulation/topology.md` - Topology documentation

**Definition of Done:**
- Topology created in Packet Tracer
- All four traffic types generated
- PCAPs exported and readable
- Documentation shows topology and usage

### Integration with Existing Tasks

**No Changes to:**
- CN-001 through CN-022 (existing tasks remain same)
- ML training (still uses ISCX-VPN2016 as primary dataset)
- Model evaluation (unchanged)

**New Integration Point:**
- CN-015 (PCAP Inference): Can now classify BOTH:
  - ISCX-VPN2016 PCAPs (existing)
  - Packet Tracer PCAPs (new - demonstrates real-time capability)

**Demo Enhancement (CN-021):**
- Show Packet Tracer topology on screen
- Generate live traffic in Packet Tracer
- Capture and classify with FlowSentry
- Demonstrates: "We built the network, generated the traffic, and classified it"

### Files to Create

1. **simulation/packet_tracer/flowsentry_topology.pkt**
   - Packet Tracer project file

2. **simulation/pcaps/** directory
   - Exported PCAP files

3. **docs/simulation/topology.md**
   ```markdown
   # FlowSentry Network Topology - Cisco Packet Tracer
   
   ## Topology Overview
   [Screenshot]
   
   ## Network Components
   - Router: Gateway between networks
   - Switch: Connects all devices
   - Clients: 4 machines generating traffic
   - Servers: Web, VoIP, Streaming, FTP
   
   ## IP Addressing Scheme
   | Device | IP Address | Role |
   |--------|------------|------|
   | Router | 192.168.1.1 | Gateway |
   | Client1 | 192.168.1.10 | Web Browsing |
   | Client2 | 192.168.1.11 | VoIP |
   | Client3 | 192.168.1.12 | Streaming |
   | Client4 | 192.168.1.13 | File Transfer |
   | Web Server | 192.168.1.100 | HTTP Server |
   | VoIP Server | 192.168.1.101 | Voice Services |
   | Streaming Server | 192.168.1.102 | Media Server |
   | FTP Server | 192.168.1.103 | File Server |
   
   ## Traffic Generation Steps
   1. Web Browsing: From Client1, open browser and access http://192.168.1.100
   2. VoIP: Place call from Client2 to VoIP Server
   3. Streaming: From Client3, start video stream from 192.168.1.102
   4. File Transfer: From Client4, download large file from FTP server
   
   ## PCAP Capture
   - Capture point: Router interface
   - Start capture before traffic generation
   - Stop capture after traffic completes
   - Export as .pcap file
   ```

4. **docs/simulation/traffic_scenarios.md**
   - Detailed steps to generate each traffic type

### Course Requirement Satisfaction

This integration satisfies the course requirement by:
- ✅ Using Cisco Packet Tracer (industry-standard simulator)
- ✅ Demonstrating networking knowledge (topology, IP addressing, routing)
- ✅ Showing practical application (traffic classification)
- ✅ Providing visual demonstration for viva
- ✅ Not disrupting existing project scope significantly

### Alternative: NS2 Integration (Not Recommended)

If NS2 is specifically required:

**Pros:**
- More realistic packet-level simulation
- Can generate custom traffic patterns

**Cons:**
- Steeper learning curve
- Requires OTcl scripting
- Less visual for viva demonstration
- More time to implement

**Would require:**
- NS2 installation (Linux/WSL)
- Tcl scripts for traffic generation
- Trace file parsing (different from PCAP)
- More complex integration

**Decision:** Start with Packet Tracer; switch to NS2 only if specifically mandated.

---

## Next Steps

1. **Create CN-023 task** in TASKS.md
2. **Update BUILD_PLAN.md** with Phase 0.5
3. **Implement CN-023** (requires Packet Tracer installation)
4. **Continue with CN-013** (CICFlowMeter decision still needed)

## Approval Required

**Decision:** Add CN-023 (Network Simulation with Packet Tracer) as new phase?

**Impact:**
- Adds 1 new task
- Estimated time: 2-4 hours for topology + documentation
- Does not block existing tasks
- Enhances demo significantly

**Status:** Pending team approval
