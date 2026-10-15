# FlowSentry Network Topology - Cisco Packet Tracer

**Task:** CN-023 - Network Topology Design & Packet Tracer Integration  
**Purpose:** Demonstrate networking concepts and generate sample traffic for classification

## Topology Overview

FlowSentry's Packet Tracer topology simulates a typical enterprise network with multiple traffic sources and destinations, demonstrating the four traffic classes our ML model classifies.

### Visual Representation

```
                    FLOWSENTRY NETWORK TOPOLOGY
                    
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Client1  │  │ Client2  │  │ Client3  │  │ Client4  │      │
│  │ Web      │  │ VoIP     │  │ Stream   │  │ FTP      │      │
│  │10.0.0.10 │  │10.0.0.11 │  │10.0.0.12 │  │10.0.0.13 │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│       │             │             │             │              │
│       └─────────────┴─────────────┴─────────────┘              │
│                           │                                     │
│                      [Switch]                                   │
│                      SW1                                       │
│                           │                                     │
│                      [Router]                                   │
│                       R1                                       │
│                      (Gateway)                                  │
│                           │                                     │
│       ┌─────────────┬─────────────┬─────────────┐              │
│       │             │             │             │              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Web Server│  │VoIP Srv  │  │Stream Srv│  │FTP Server│      │
│  │ HTTP     │  │ SIP/RTP  │  │ RTSP     │  │ FTP      │      │
│  │10.0.1.100│  │10.0.1.101│  │10.0.1.102│  │10.0.1.103│      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                          SERVERS                                │
└─────────────────────────────────────────────────────────────────┘

Traffic Capture Point: Router R1 Interface (to servers)
```

## Network Components

### Router
- **Device:** 2911 Integrated Services Router
- **Name:** R1
- **Role:** Gateway between client and server networks
- **Interfaces:**
  - GigabitEthernet0/0: 10.0.0.1/24 (Client network)
  - GigabitEthernet0/1: 10.0.1.1/24 (Server network)
- **Configuration:** Basic routing, no ACLs

### Switch
- **Device:** 2960-24TT Switch
- **Name:** SW1
- **Role:** Connect all clients
- **Configuration:** Default (all ports in VLAN 1)

### Clients

| Device | IP Address | Subnet Mask | Default Gateway | Traffic Type |
|--------|------------|-------------|-----------------|--------------|
| Client1 | 10.0.0.10 | 255.255.255.0 | 10.0.0.1 | Web Browsing |
| Client2 | 10.0.0.11 | 255.255.255.0 | 10.0.0.1 | VoIP |
| Client3 | 10.0.0.12 | 255.255.255.0 | 10.0.0.1 | Streaming |
| Client4 | 10.0.0.13 | 255.255.255.0 | 10.0.0.1 | File Transfer |

**Device Type:** Generic PC or Laptop

### Servers

| Server | IP Address | Service | Port | Description |
|--------|------------|---------|------|-------------|
| Web Server | 10.0.1.100 | HTTP | 80 | Web pages, HTTP requests |
| VoIP Server | 10.0.1.101 | SIP/RTP | 5060, 10000-20000 | Voice over IP calls |
| Streaming Server | 10.0.1.102 | RTSP | 554 | Video/audio streaming |
| FTP Server | 10.0.1.103 | FTP | 21, 20 | File transfers |

**Device Type:** Generic Server

## IP Addressing Scheme

### Client Network (10.0.0.0/24)
```
Network:    10.0.0.0
Subnet:     255.255.255.0
Gateway:    10.0.0.1 (Router R1 - Gi0/0)
DHCP Range: 10.0.0.10 - 10.0.0.254 (optional)
```

### Server Network (10.0.1.0/24)
```
Network:    10.0.1.0
Subnet:     255.255.255.0
Gateway:    10.0.1.1 (Router R1 - Gi0/1)
Servers:    10.0.1.100 - 10.0.1.103
```

## Configuration Steps

### 1. Router Configuration

```cisco
Router> enable
Router# configure terminal
Router(config)# hostname R1

! Configure client-facing interface
R1(config)# interface GigabitEthernet0/0
R1(config-if)# ip address 10.0.0.1 255.255.255.0
R1(config-if)# no shutdown
R1(config-if)# exit

! Configure server-facing interface
R1(config)# interface GigabitEthernet0/1
R1(config-if)# ip address 10.0.1.1 255.255.255.0
R1(config-if)# no shutdown
R1(config-if)# exit

! Enable IP routing
R1(config)# ip routing
R1(config)# end
R1# write memory
```

### 2. Client Configuration

For each client (PC/Laptop):
1. Click on the device
2. Go to Desktop → IP Configuration
3. Set:
   - IP Address: 10.0.0.10 (Client1), 10.0.0.11 (Client2), etc.
   - Subnet Mask: 255.255.255.0
   - Default Gateway: 10.0.0.1

### 3. Server Configuration

#### Web Server (10.0.1.100)
1. Click on server → Services → HTTP
2. Enable HTTP service
3. Edit index.html:
   ```html
   <html>
   <body>
   <h1>FlowSentry Web Server</h1>
   <p>Traffic Classification Test</p>
   </body>
   </html>
   ```
4. Set IP: 10.0.1.100, Subnet: 255.255.255.0, Gateway: 10.0.1.1

#### VoIP Server (10.0.1.101)
1. Click on server → Config
2. Enable Call Manager Express (if available)
3. Configure SIP settings (or use simplified telephony)
4. Set IP: 10.0.1.101

#### Streaming Server (10.0.1.102)
1. Use HTTP server for video files
2. Place sample video files in HTTP directory
3. Set IP: 10.0.1.102

#### FTP Server (10.0.1.103)
1. Click on server → Services → FTP
2. Enable FTP service
3. Create user: username "user", password "pass"
4. Add sample files for download
5. Set IP: 10.0.1.103

## Traffic Flow

### Web Browsing Traffic
```
Client1 (10.0.0.10) → Router (10.0.0.1) → Router (10.0.1.1) → Web Server (10.0.1.100)
                  TCP Port 80 (HTTP)
                  
Request:  GET /index.html HTTP/1.1
Response: HTML content
```

### VoIP Traffic
```
Client2 (10.0.0.11) ↔ Router ↔ VoIP Server (10.0.1.101)
                    UDP Ports 5060 (SIP), 10000-20000 (RTP)
                    
SIP: Signaling (call setup)
RTP: Voice packets (small, frequent, regular intervals)
```

### Streaming Traffic
```
Client3 (10.0.0.12) → Router → Streaming Server (10.0.1.102)
                    TCP Port 80 or RTSP Port 554
                    
Request:  Video stream request
Response: Large, continuous data flow (asymmetric)
```

### File Transfer Traffic
```
Client4 (10.0.0.13) ↔ Router ↔ FTP Server (10.0.1.103)
                    TCP Ports 21 (control), 20 (data)
                    
Commands: USER, PASS, RETR, STOR
Data:     Large file chunks, sustained transfer
```

## Verification

### Connectivity Test
From any client, open Command Prompt:
```cmd
ping 10.0.1.100    # Ping Web Server
ping 10.0.1.101    # Ping VoIP Server
ping 10.0.1.102    # Ping Streaming Server
ping 10.0.1.103    # Ping FTP Server
```

### Web Server Test
From Client1:
1. Open Web Browser
2. Navigate to: `http://10.0.1.100`
3. Verify page loads

### FTP Server Test
From Client4:
1. Open Command Prompt
2. Type: `ftp 10.0.1.103`
3. Login with configured credentials
4. Test file download

## Packet Capture Setup

### Capture Point
- **Interface:** Router R1, GigabitEthernet0/1 (server-side)
- **Why this location:** All traffic between clients and servers passes through

### Capture Steps
1. Click on Router R1
2. Go to **Simulation Mode** (bottom right, play button)
3. Click **Edit Filters** → Select all traffic types
4. Start traffic generation (see traffic_scenarios.md)
5. Watch packets flow in Simulation Window
6. Export capture:
   - Click **Export** button
   - Select **Pcap** format
   - Save to `simulation/pcaps/`

### Alternative Capture Method
1. Add a generic PC as "sniffer" to the network
2. Connect sniffer to Router via Switch
3. Configure port mirroring (if switch supports it)
4. Use Wireshark on sniffer to capture

## Screenshots to Capture

For documentation and viva:

1. **Topology Overview:**
   - Full topology in Packet Tracer
   - Save as: `docs/simulation/screenshots/topology_overview.png`

2. **Router Configuration:**
   - Show running config
   - Save as: `docs/simulation/screenshots/router_config.png`

3. **Web Server Test:**
   - Browser showing HTTP page
   - Save as: `docs/simulation/screenshots/web_test.png`

4. **Packet Capture:**
   - Simulation window showing packets
   - Save as: `docs/simulation/screenshots/packet_capture.png`

## Troubleshooting

### Clients Can't Reach Servers
- Check IP configuration on all devices
- Verify router interfaces are "up"
- Check routing table: `show ip route` on router
- Ping gateway first, then server

### Services Not Working
- HTTP: Ensure HTTP service enabled on server
- FTP: Check user credentials and permissions
- VoIP: Verify SIP configuration
- Streaming: Ensure video files exist on server

### Can't Export PCAP
- Must be in Simulation Mode
- Must have captured packets
- Try different export formats
- Use Wireshark on separate capture device

## Related Documentation

- `traffic_scenarios.md` - How to generate each traffic type
- `../simulation/README.md` - Simulation directory overview
- `../task_reports/CN-023_PLAN.md` - Task implementation plan

---

**Status:** Topology design complete. Ready for implementation in Cisco Packet Tracer.
