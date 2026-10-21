# =====================================================================
# FlowSentry — NS-2 (Network Simulator 2) Topology Script
# Task: CN-023 · Network Simulator Integration
# Simulates: Web Browsing, VoIP (G.711), Streaming, and FTP
# =====================================================================

# 1. Initialize Simulator
set ns [new Simulator]

# 2. Define Colors for NAM Packet Visualization
$ns color 1 Blue        ;# Flow 1: Web Browsing
$ns color 2 Green       ;# Flow 2: VoIP (G.711 RTP)
$ns color 3 Purple      ;# Flow 3: Streaming Media
$ns color 4 Amber       ;# Flow 4: File Transfer (FTP)

# 3. Open Trace and NAM Animation Files
set tracefile [open "flowsentry.tr" w]
$ns trace-all $tracefile
set namfile [open "flowsentry.nam" w]
$ns namtrace-all $namfile

# 4. Create Nodes
# Clients: n0 (Web), n1 (VoIP), n2 (Stream), n3 (FTP)
set n0 [$ns node]
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]

# Intermediate Infrastructure: n4 (Gateway Switch), n5 (Core Router)
set n4 [$ns node]
set n5 [$ns node]

# Servers: n6 (Web Srv), n7 (VoIP Srv), n8 (Stream Srv), n9 (FTP Srv)
set n6 [$ns node]
set n7 [$ns node]
set n8 [$ns node]
set n9 [$ns node]

# Label Nodes for NAM
$n0 label "Client-Web"
$n1 label "Client-VoIP"
$n2 label "Client-Stream"
$n3 label "Client-FTP"
$n4 label "Switch-SW1"
$n5 label "Router-R1"
$n6 label "Web-Server:80"
$n7 label "VoIP-Server:5060"
$n8 label "Stream-Server:554"
$n9 label "FTP-Server:21"

# 5. Establish Duplex Links (Bandwidth, Delay, Queue Type)
# Client access links (100Mbps, 2ms)
$ns duplex-link $n0 $n4 100Mb 2ms DropTail
$ns duplex-link $n1 $n4 100Mb 2ms DropTail
$ns duplex-link $n2 $n4 100Mb 2ms DropTail
$ns duplex-link $n3 $n4 100Mb 2ms DropTail

# Core Bottleneck Link between Switch SW1 and Router R1 (Flow Capture Point)
# 10 Mbps bottleneck link, 10ms delay, Queue buffer limit 30 packets
$ns duplex-link $n4 $n5 10Mb 10ms DropTail
$ns queue-limit $n4 $n5 30

# Server farm links (100Mbps, 2ms)
$ns duplex-link $n5 $n6 100Mb 2ms DropTail
$ns duplex-link $n5 $n7 100Mb 2ms DropTail
$ns duplex-link $n5 $n8 100Mb 2ms DropTail
$ns duplex-link $n5 $n9 100Mb 2ms DropTail

# Monitor the Queue at the bottleneck link for NAM
$ns duplex-link-op $n4 $n5 queuePos 0.5

# 6. Setup Traffic Class 1: Web Browsing (Bursty Exponential ON/OFF)
set tcp_web [new Agent/TCP]
$tcp_web set fid_ 1
$tcp_web set window_ 32
$ns attach-agent $n0 $tcp_web
set sink_web [new Agent/TCPSink]
$ns attach-agent $n6 $sink_web
$ns connect $tcp_web $sink_web

set web_app [new Application/Traffic/Exponential]
$web_app attach-agent $tcp_web
$web_app set packetSize_ 1000
$web_app set burst_time_ 500ms
$web_app set idle_time_ 1000ms
$web_app set rate_ 1Mb

# 7. Setup Traffic Class 2: VoIP (Isochronous G.711 Audio Codec, CBR/UDP)
set udp_voip [new Agent/UDP]
$udp_voip set fid_ 2
$ns attach-agent $n1 $udp_voip
set null_voip [new Agent/Null]
$ns attach-agent $n7 $null_voip
$ns connect $udp_voip $null_voip

set voip_app [new Application/Traffic/CBR]
$voip_app attach-agent $udp_voip
$voip_app set packetSize_ 160     ;# 20ms G.711 voice payload
$voip_app set rate_ 64Kb          ;# 64 kbps standard toll voice
$voip_app set interval_ 0.020     ;# 20 ms strict periodic cadence
$voip_app set random_ false

# 8. Setup Traffic Class 3: Streaming Media (Continuous Video Chunk Delivery)
set tcp_stream [new Agent/TCP]
$tcp_stream set fid_ 3
$tcp_stream set window_ 64
$ns attach-agent $n2 $tcp_stream
set sink_stream [new Agent/TCPSink]
$ns attach-agent $n8 $sink_stream
$ns connect $tcp_stream $sink_stream

set stream_app [new Application/Traffic/CBR]
$stream_app attach-agent $tcp_stream
$stream_app set packetSize_ 1400
$stream_app set rate_ 2.5Mb
$stream_app set interval_ 0.004

# 9. Setup Traffic Class 4: File Transfer (Bulk FTP Over Newreno TCP)
set tcp_ftp [new Agent/TCP/Newreno]
$tcp_ftp set fid_ 4
$tcp_ftp set window_ 128
$ns attach-agent $n3 $tcp_ftp
set sink_ftp [new Agent/TCPSink]
$ns attach-agent $n9 $sink_ftp
$ns connect $tcp_ftp $sink_ftp

set ftp_app [new Application/FTP]
$ftp_app attach-agent $tcp_ftp

# 10. Simulation Event Schedule
$ns at 0.5 "$voip_app start"
$ns at 1.0 "$web_app start"
$ns at 1.5 "$stream_app start"
$ns at 2.0 "$ftp_app start"

$ns at 8.0 "$ftp_app stop"
$ns at 8.5 "$stream_app stop"
$ns at 9.0 "$web_app stop"
$ns at 9.5 "$voip_app stop"

# Finish Procedure
proc finish {} {
    global ns tracefile namfile
    $ns flush-trace
    close $tracefile
    close $namfile
    puts "NS-2 Simulation Complete. Trace saved to flowsentry.tr, NAM saved to flowsentry.nam"
    exit 0
}

$ns at 10.0 "finish"

# Execute
$ns run
