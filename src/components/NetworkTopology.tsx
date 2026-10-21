import React, { useState, useEffect, useRef } from 'react';
import { 
  Laptop, 
  Server, 
  Router, 
  Network, 
  Play, 
  Pause,
  RefreshCw, 
  Radio, 
  Send, 
  FileText, 
  ArrowRight, 
  ShieldAlert, 
  Info, 
  Download, 
  Terminal, 
  FileCode,
  Sliders,
  Layers,
  CircleDot,
  Cpu,
  AlertTriangle,
  Flame,
  CheckCircle2
} from 'lucide-react';
import { TrafficClass, NetworkFlow } from '../types';
import { generateSyntheticFlow } from '../utils/mlEngine';
import { exportFlowsToPcapBlob } from '../utils/pcapParser';

export interface Ns2TraceEvent {
  event: '+' | '-' | 'r' | 'd';
  time: number;
  fromNode: number;
  toNode: number;
  pktType: 'cbr' | 'tcp' | 'ack';
  pktSize: number;
  flowId: number;
  srcAddr: string;
  dstAddr: string;
  seqNum: number;
  pktId: number;
}

const SAMPLE_NS2_TRACES: Ns2TraceEvent[] = [
  { event: '+', time: 0.500, fromNode: 1, toNode: 4, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 0, pktId: 1 },
  { event: '-', time: 0.500, fromNode: 1, toNode: 4, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 0, pktId: 1 },
  { event: 'r', time: 0.502, fromNode: 1, toNode: 4, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 0, pktId: 1 },
  { event: '+', time: 0.502, fromNode: 4, toNode: 5, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 0, pktId: 1 },
  { event: '-', time: 0.502, fromNode: 4, toNode: 5, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 0, pktId: 1 },
  { event: 'r', time: 0.512, fromNode: 4, toNode: 5, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 0, pktId: 1 },
  { event: '+', time: 0.520, fromNode: 1, toNode: 4, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 1, pktId: 2 },
  { event: 'r', time: 0.522, fromNode: 1, toNode: 4, pktType: 'cbr', pktSize: 160, flowId: 2, srcAddr: '1.0', dstAddr: '7.0', seqNum: 1, pktId: 2 },
  { event: '+', time: 1.000, fromNode: 0, toNode: 4, pktType: 'tcp', pktSize: 1000, flowId: 1, srcAddr: '0.0', dstAddr: '6.0', seqNum: 0, pktId: 3 },
  { event: '-', time: 1.000, fromNode: 0, toNode: 4, pktType: 'tcp', pktSize: 1000, flowId: 1, srcAddr: '0.0', dstAddr: '6.0', seqNum: 0, pktId: 3 },
  { event: 'r', time: 1.002, fromNode: 0, toNode: 4, pktType: 'tcp', pktSize: 1000, flowId: 1, srcAddr: '0.0', dstAddr: '6.0', seqNum: 0, pktId: 3 },
  { event: '+', time: 1.002, fromNode: 4, toNode: 5, pktType: 'tcp', pktSize: 1000, flowId: 1, srcAddr: '0.0', dstAddr: '6.0', seqNum: 0, pktId: 3 },
  { event: '+', time: 1.500, fromNode: 2, toNode: 4, pktType: 'cbr', pktSize: 1400, flowId: 3, srcAddr: '2.0', dstAddr: '8.0', seqNum: 0, pktId: 4 },
  { event: '-', time: 1.500, fromNode: 2, toNode: 4, pktType: 'cbr', pktSize: 1400, flowId: 3, srcAddr: '2.0', dstAddr: '8.0', seqNum: 0, pktId: 4 },
  { event: 'r', time: 1.502, fromNode: 2, toNode: 4, pktType: 'cbr', pktSize: 1400, flowId: 3, srcAddr: '2.0', dstAddr: '8.0', seqNum: 0, pktId: 4 },
  { event: '+', time: 2.000, fromNode: 3, toNode: 4, pktType: 'tcp', pktSize: 1500, flowId: 4, srcAddr: '3.0', dstAddr: '9.0', seqNum: 0, pktId: 5 },
  { event: '-', time: 2.000, fromNode: 3, toNode: 4, pktType: 'tcp', pktSize: 1500, flowId: 4, srcAddr: '3.0', dstAddr: '9.0', seqNum: 0, pktId: 5 },
  { event: 'r', time: 2.002, fromNode: 3, toNode: 4, pktType: 'tcp', pktSize: 1500, flowId: 4, srcAddr: '3.0', dstAddr: '9.0', seqNum: 0, pktId: 5 },
  { event: '+', time: 2.002, fromNode: 4, toNode: 5, pktType: 'tcp', pktSize: 1500, flowId: 4, srcAddr: '3.0', dstAddr: '9.0', seqNum: 0, pktId: 5 },
  { event: 'd', time: 2.045, fromNode: 4, toNode: 5, pktType: 'tcp', pktSize: 1500, flowId: 4, srcAddr: '3.0', dstAddr: '9.0', seqNum: 14, pktId: 19 }
];

export const NetworkTopology: React.FC = () => {
  const [simulatorMode, setSimulatorMode] = useState<'packet_tracer' | 'ns2'>('packet_tracer');
  
  // Cisco Packet Tracer state
  const [activeTraffic, setActiveTraffic] = useState<TrafficClass | null>('Web Browsing');
  const [capturedFlows, setCapturedFlows] = useState<NetworkFlow[]>([]);
  const [showIosConfig, setShowIosConfig] = useState<boolean>(false);
  const [packetAnimation, setPacketAnimation] = useState<{
    source: string;
    target: string;
    step: 'client-switch' | 'switch-router' | 'router-server' | 'complete';
    trafficType: TrafficClass;
  } | null>(null);

  // NS-2 Simulation State
  const [ns2Time, setNs2Time] = useState<number>(2.05);
  const [isNs2Playing, setIsNs2Playing] = useState<boolean>(false);
  const [queueOccupancy, setQueueOccupancy] = useState<number>(14);
  const [dropCount, setDropCount] = useState<number>(1);
  const [ns2Events, setNs2Events] = useState<Ns2TraceEvent[]>(SAMPLE_NS2_TRACES);
  const ns2TimerRef = useRef<number | null>(null);

  // Initialize flows
  useEffect(() => {
    const f1 = generateSyntheticFlow('Web Browsing');
    const f2 = generateSyntheticFlow('VoIP');
    const f3 = generateSyntheticFlow('Streaming');
    const f4 = generateSyntheticFlow('File Transfer');
    setCapturedFlows([f1, f2, f3, f4]);
  }, []);

  // NS-2 playback loop
  useEffect(() => {
    if (isNs2Playing) {
      ns2TimerRef.current = window.setInterval(() => {
        setNs2Time(prev => {
          const next = prev + 0.05;
          if (next >= 10.0) {
            setIsNs2Playing(false);
            return 10.0;
          }
          // Fluctuate queue occupancy based on FTP & video traffic
          setQueueOccupancy(Math.floor(10 + Math.random() * 18));
          if (Math.random() < 0.1) {
            setDropCount(d => d + 1);
          }
          return parseFloat(next.toFixed(2));
        });
      }, 200);
    } else {
      if (ns2TimerRef.current) clearInterval(ns2TimerRef.current);
    }
    return () => {
      if (ns2TimerRef.current) clearInterval(ns2TimerRef.current);
    };
  }, [isNs2Playing]);

  const triggerSimulation = (trafficType: TrafficClass) => {
    setActiveTraffic(trafficType);
    setPacketAnimation({
      source: trafficType,
      target: 'router',
      step: 'client-switch',
      trafficType
    });

    setTimeout(() => {
      setPacketAnimation(prev => prev ? { ...prev, step: 'switch-router' } : null);
    }, 450);

    setTimeout(() => {
      setPacketAnimation(prev => prev ? { ...prev, step: 'router-server' } : null);
    }, 900);

    setTimeout(() => {
      setPacketAnimation(null);
      const newFlow = generateSyntheticFlow(trafficType);
      setCapturedFlows(prev => [newFlow, ...prev.slice(0, 14)]);
    }, 1350);
  };

  const handleExportCapturePcap = (trafficType?: TrafficClass) => {
    const targetFlows = trafficType
      ? capturedFlows.filter(f => f.predictedClass === trafficType)
      : capturedFlows;
    const blob = exportFlowsToPcapBlob(targetFlows.length > 0 ? targetFlows : capturedFlows);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = trafficType ? `${trafficType.toLowerCase().replace(' ', '_')}.pcap` : 'packet_tracer_capture.pcap';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPacketTracerScript = () => {
    const script = `! Cisco Packet Tracer 8.0+ IOS Configuration (Router R1)
enable
configure terminal
hostname R1
interface GigabitEthernet0/0
 description Client Subnet Gateway
 ip address 10.0.0.1 255.255.255.0
 no shutdown
exit
interface GigabitEthernet0/1
 description Server Farm & Traffic Capture Point
 ip address 10.0.1.1 255.255.255.0
 no shutdown
exit
ip routing
end
write memory`;
    const blob = new Blob([script], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'flowsentry_router_r1_config.ios';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadNs2Tcl = () => {
    const tclScript = `# NS-2 Topology Script (OTcl) for FlowSentry
set ns [new Simulator]
$ns color 1 Blue
$ns color 2 Green
$ns color 3 Purple
$ns color 4 Amber
set tf [open "flowsentry.tr" w]
$ns trace-all $tf
set nf [open "flowsentry.nam" w]
$ns namtrace-all $nf
# Nodes
set n0 [$ns node]; set n1 [$ns node]; set n2 [$ns node]; set n3 [$ns node]
set n4 [$ns node]; set n5 [$ns node]
set n6 [$ns node]; set n7 [$ns node]; set n8 [$ns node]; set n9 [$ns node]
# Links
$ns duplex-link $n0 $n4 100Mb 2ms DropTail
$ns duplex-link $n1 $n4 100Mb 2ms DropTail
$ns duplex-link $n2 $n4 100Mb 2ms DropTail
$ns duplex-link $n3 $n4 100Mb 2ms DropTail
$ns duplex-link $n4 $n5 10Mb 10ms DropTail
$ns queue-limit $n4 $n5 30
$ns duplex-link $n5 $n6 100Mb 2ms DropTail
$ns duplex-link $n5 $n7 100Mb 2ms DropTail
$ns duplex-link $n5 $n8 100Mb 2ms DropTail
$ns duplex-link $n5 $n9 100Mb 2ms DropTail
# VoIP G.711 CBR
set udp2 [new Agent/UDP]; $udp2 set fid_ 2; $ns attach-agent $n1 $udp2
set cbr2 [new Application/Traffic/CBR]; $cbr2 attach-agent $udp2
$cbr2 set packetSize_ 160; $cbr2 set rate_ 64Kb; $cbr2 set interval_ 0.020
$ns at 0.5 "$cbr2 start"
# Execute
$ns run`;
    const blob = new Blob([tclScript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'flowsentry_topology.tcl';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadNs2Trace = () => {
    let traceContent = `# NS-2 Trace File Format
# Event Time From To PktType PktSize Flags FlowId SrcAddr DstAddr SeqNum PktId\n`;
    SAMPLE_NS2_TRACES.forEach(t => {
      traceContent += `${t.event} ${t.time.toFixed(6)} ${t.fromNode} ${t.toNode} ${t.pktType} ${t.pktSize} ------- ${t.flowId} ${t.srcAddr} ${t.dstAddr} ${t.seqNum} ${t.pktId}\n`;
    });
    const blob = new Blob([traceContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'flowsentry.tr';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getTrafficBadge = (type: TrafficClass) => {
    switch (type) {
      case 'Web Browsing': return 'bg-cyan-950 text-cyan-300 border-cyan-800';
      case 'VoIP': return 'bg-emerald-950 text-emerald-300 border-emerald-800';
      case 'Streaming': return 'bg-purple-950 text-purple-300 border-purple-800';
      case 'File Transfer': return 'bg-amber-950 text-amber-300 border-amber-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner with Dual-Simulator Toggle */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold mb-1">
              <Network className="w-4 h-4" />
              <span>Dual Network Simulators: Cisco Packet Tracer & NS-2 (CN-023)</span>
            </div>
            <h2 className="text-xl font-bold text-white">Network Topology & Discrete-Event Traffic Simulation</h2>
            <p className="text-sm text-slate-400 max-w-3xl mt-1">
              {simulatorMode === 'packet_tracer' 
                ? 'Cisco Packet Tracer enterprise topology with 4 clients, Catalyst 2960 switch, 2911 router gateway (Gi0/1 capture TAP), and server farm.'
                : 'NS-2 (Network Simulator 2) OTcl simulation with 10 nodes, bottleneck link (10Mbps DropTail queue limit 30), and packet event tracing (.tr / .nam).'
              }
            </p>
          </div>

          {/* Simulator Toggle Pills */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 self-start md:self-center">
            <button
              onClick={() => setSimulatorMode('packet_tracer')}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                simulatorMode === 'packet_tracer'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              <span>Cisco Packet Tracer</span>
            </button>
            <button
              onClick={() => setSimulatorMode('ns2')}
              className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
                simulatorMode === 'ns2'
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>NS-2 (Network Simulator 2)</span>
            </button>
          </div>
        </div>

        {/* Mode-specific Top Bar Controls */}
        {simulatorMode === 'packet_tracer' ? (
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono">Simulate Packet Stream:</span>
              <div className="flex flex-wrap gap-1.5">
                {(['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'] as TrafficClass[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => triggerSimulation(t)}
                    className={`text-xs px-2.5 py-1.5 rounded-lg border font-medium flex items-center gap-1.5 transition-all shadow-sm ${
                      activeTraffic === t
                        ? 'bg-cyan-500 text-slate-950 border-cyan-400 font-semibold shadow-cyan-500/20'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <Play className="w-3 h-3 fill-current" />
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowIosConfig(!showIosConfig)}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 font-mono flex items-center gap-1"
              >
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span>IOS Config</span>
              </button>
              <button
                onClick={handleDownloadPacketTracerScript}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 font-mono flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>.ios</span>
              </button>
              <button
                onClick={() => handleExportCapturePcap()}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-cyan-600 bg-cyan-950/40 text-cyan-300 hover:bg-cyan-900/50 font-mono flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>Export PCAP</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsNs2Playing(!isNs2Playing)}
                className={`text-xs px-3 py-1.5 rounded-lg font-mono font-bold flex items-center gap-1.5 transition-all ${
                  isNs2Playing 
                    ? 'bg-amber-500 text-slate-950 hover:bg-amber-400' 
                    : 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
                }`}
              >
                {isNs2Playing ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                <span>{isNs2Playing ? 'Pause Simulation' : 'Run NS-2 Clock'}</span>
              </button>

              <div className="flex items-center gap-2 font-mono text-xs text-slate-300 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                <span>Clock:</span>
                <span className="text-cyan-400 font-bold">{ns2Time.toFixed(2)}s / 10.0s</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadNs2Tcl}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 font-mono flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>.tcl script</span>
              </button>
              <button
                onClick={handleDownloadNs2Trace}
                className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 font-mono flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>.tr trace</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* VIEW 1: CISCO PACKET TRACER TOPOLOGY */}
      {simulatorMode === 'packet_tracer' && (
        <>
          {showIosConfig && (
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2">
                <span className="flex items-center gap-2 text-cyan-400 font-bold">
                  <Terminal className="w-4 h-4" />
                  <span>Cisco 2911 Router R1 Running Configuration</span>
                </span>
                <button onClick={handleDownloadPacketTracerScript} className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1">
                  <Download className="w-3 h-3" />
                  <span>Save file</span>
                </button>
              </div>
              <pre className="text-slate-300 overflow-x-auto p-3 bg-slate-900/80 rounded-xl border border-slate-800/80 leading-relaxed">
{`Router> enable
Router# configure terminal
Router(config)# hostname R1
! Client Subnet Gateway
R1(config)# interface GigabitEthernet0/0
R1(config-if)# ip address 10.0.0.1 255.255.255.0
R1(config-if)# no shutdown
! Server Farm Interface (Traffic Capture Tapping Point)
R1(config)# interface GigabitEthernet0/1
R1(config-if)# ip address 10.0.1.1 255.255.255.0
R1(config-if)# no shutdown
! Enable IP Routing
R1(config)# ip routing
R1(config)# end`}
              </pre>
            </div>
          )}

          {/* Visual Topology Canvas */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
            <div className="flex justify-between items-center text-xs font-mono text-slate-500 mb-6 border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500/80" />
                <span>Client Network: <strong className="text-slate-300">10.0.0.0/24</strong> (Gateway: 10.0.0.1 Gi0/0)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                <span>Server Network: <strong className="text-slate-300">10.0.1.0/24</strong> (Gateway: 10.0.1.1 Gi0/1)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-11 gap-4 items-center">
              {/* Clients */}
              <div className="lg:col-span-3 space-y-3">
                <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 font-semibold">
                  Client Devices (Traffic Generators)
                </h4>
                
                <div 
                  onClick={() => triggerSimulation('Web Browsing')}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    activeTraffic === 'Web Browsing' ? 'border-cyan-500/60 bg-cyan-950/30 ring-1 ring-cyan-500/50' : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg"><Laptop className="w-4 h-4" /></div>
                      <div>
                        <div className="text-sm font-semibold text-slate-200">Client1 (Web)</div>
                        <div className="text-xs font-mono text-slate-400">10.0.0.10 → Port 80</div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">HTTP</span>
                  </div>
                </div>

                <div 
                  onClick={() => triggerSimulation('VoIP')}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    activeTraffic === 'VoIP' ? 'border-emerald-500/60 bg-emerald-950/30 ring-1 ring-emerald-500/50' : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg"><Radio className="w-4 h-4" /></div>
                      <div>
                        <div className="text-sm font-semibold text-slate-200">Client2 (VoIP)</div>
                        <div className="text-xs font-mono text-slate-400">10.0.0.11 → Port 5060</div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">SIP/RTP</span>
                  </div>
                </div>

                <div 
                  onClick={() => triggerSimulation('Streaming')}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    activeTraffic === 'Streaming' ? 'border-purple-500/60 bg-purple-950/30 ring-1 ring-purple-500/50' : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg"><Laptop className="w-4 h-4" /></div>
                      <div>
                        <div className="text-sm font-semibold text-slate-200">Client3 (Stream)</div>
                        <div className="text-xs font-mono text-slate-400">10.0.0.12 → Port 554</div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-purple-950 text-purple-300 border border-purple-800">RTSP</span>
                  </div>
                </div>

                <div 
                  onClick={() => triggerSimulation('File Transfer')}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    activeTraffic === 'File Transfer' ? 'border-amber-500/60 bg-amber-950/30 ring-1 ring-amber-500/50' : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg"><FileText className="w-4 h-4" /></div>
                      <div>
                        <div className="text-sm font-semibold text-slate-200">Client4 (FTP)</div>
                        <div className="text-xs font-mono text-slate-400">10.0.0.13 → Port 21/20</div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-amber-950 text-amber-300 border border-amber-800">FTP</span>
                  </div>
                </div>
              </div>

              {/* Core switch & Router */}
              <div className="lg:col-span-5 flex flex-col items-center justify-center p-4 bg-slate-900/40 rounded-xl border border-slate-800/80 my-2 lg:my-0 space-y-6">
                <div className="w-full max-w-xs p-3.5 bg-slate-900 border border-slate-700 rounded-xl text-center shadow-lg relative">
                  <div className="flex items-center justify-center gap-2 text-cyan-400 mb-1">
                    <Network className="w-5 h-5" />
                    <span className="text-sm font-bold text-slate-200">Switch SW1</span>
                  </div>
                  <p className="text-xs text-slate-400 font-mono">Cisco 2960-24TT · VLAN 1</p>
                </div>

                <div className="w-full max-w-sm p-4 bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-cyan-500/50 rounded-2xl text-center shadow-xl relative">
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-cyan-500 text-slate-950 text-[10px] font-bold font-mono tracking-wider uppercase">
                    Packet Capture Point
                  </div>
                  <div className="flex items-center justify-center gap-2 text-cyan-400 mt-1 mb-1">
                    <Router className="w-6 h-6 text-cyan-400" />
                    <span className="text-base font-bold text-white">Router R1 (Cisco 2911)</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800 text-xs text-left font-mono">
                    <div className="bg-slate-950/80 p-2 rounded border border-slate-800">
                      <span className="text-slate-400 text-[10px]">Gi0/0</span>
                      <div className="text-slate-200 font-bold">10.0.0.1/24</div>
                    </div>
                    <div className="bg-cyan-950/40 p-2 rounded border border-cyan-800/80">
                      <span className="text-cyan-300 text-[10px]">Gi0/1 (TAP)</span>
                      <div className="text-cyan-200 font-bold">10.0.1.1/24</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Servers */}
              <div className="lg:col-span-3 space-y-3">
                <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 font-semibold">
                  Server Farm
                </h4>
                <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg"><Server className="w-4 h-4" /></div>
                    <div><div className="text-sm font-semibold text-slate-200">Web Server</div><div className="text-xs font-mono text-slate-400">10.0.1.100 : 80</div></div>
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg"><Server className="w-4 h-4" /></div>
                    <div><div className="text-sm font-semibold text-slate-200">VoIP PBX</div><div className="text-xs font-mono text-slate-400">10.0.1.101 : 5060</div></div>
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg"><Server className="w-4 h-4" /></div>
                    <div><div className="text-sm font-semibold text-slate-200">Streaming Srv</div><div className="text-xs font-mono text-slate-400">10.0.1.102 : 554</div></div>
                  </div>
                </div>
                <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg"><Server className="w-4 h-4" /></div>
                    <div><div className="text-sm font-semibold text-slate-200">FTP Server</div><div className="text-xs font-mono text-slate-400">10.0.1.103 : 21</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* VIEW 2: NS-2 (NETWORK SIMULATOR 2) */}
      {simulatorMode === 'ns2' && (
        <div className="space-y-6">
          {/* NS2 NAM Simulation & Bottleneck Queue View */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 relative overflow-hidden space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-slate-200 font-bold">NS-2 NAM Topology: 10 Nodes · Bottleneck Link: n4 ↔ n5 (10 Mbps, 10ms delay, DropTail)</span>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="text-slate-400">Queue: <strong className="text-cyan-400">{queueOccupancy} / 30 pkts</strong></span>
                <span className="text-rose-400 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Drops: {dropCount}</span>
                </span>
              </div>
            </div>

            {/* NS2 Visual Node Network */}
            <div className="grid grid-cols-1 md:grid-cols-10 gap-3 items-center text-center font-mono text-xs">
              {/* Clients: n0, n1, n2, n3 (Cols 1-2) */}
              <div className="md:col-span-2 space-y-2">
                <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-800 text-blue-300">
                  <div className="font-bold">n0: Web</div>
                  <div className="text-[10px] text-slate-400">TCP / Pareto</div>
                </div>
                <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300">
                  <div className="font-bold">n1: VoIP</div>
                  <div className="text-[10px] text-slate-400">UDP / CBR 160B</div>
                </div>
                <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800 text-purple-300">
                  <div className="font-bold">n2: Stream</div>
                  <div className="text-[10px] text-slate-400">TCP / CBR 2.5Mb</div>
                </div>
                <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-800 text-amber-300">
                  <div className="font-bold">n3: FTP</div>
                  <div className="text-[10px] text-slate-400">TCP Newreno</div>
                </div>
              </div>

              {/* Gateway n4 (Col 3-4) */}
              <div className="md:col-span-2 flex flex-col items-center">
                <div className="p-3 bg-slate-900 border border-slate-700 rounded-xl w-full">
                  <CircleDot className="w-5 h-5 text-cyan-400 mx-auto mb-1" />
                  <div className="font-bold text-slate-200">Node n4</div>
                  <div className="text-[10px] text-slate-400">Gateway Switch</div>
                </div>
              </div>

              {/* Core Bottleneck Link with Buffer Queue (Col 5-6) */}
              <div className="md:col-span-2 p-3 bg-slate-900/80 border-2 border-cyan-500/50 rounded-xl space-y-2">
                <div className="text-[11px] font-bold text-cyan-300 uppercase">Bottleneck Link (n4 ↔ n5)</div>
                <div className="text-[10px] text-slate-400">10 Mbps · 10ms · DropTail</div>
                {/* Visual buffer slots */}
                <div className="h-3 w-full bg-slate-950 rounded border border-slate-800 overflow-hidden flex">
                  <div className="bg-cyan-500 h-full transition-all duration-300" style={{ width: `${(queueOccupancy / 30) * 100}%` }} />
                </div>
                <div className="text-[10px] text-slate-500">Flow Tapping Point</div>
              </div>

              {/* Router n5 (Col 7-8) */}
              <div className="md:col-span-2 flex flex-col items-center">
                <div className="p-3 bg-slate-900 border border-slate-700 rounded-xl w-full">
                  <Router className="w-5 h-5 text-cyan-400 mx-auto mb-1" />
                  <div className="font-bold text-slate-200">Node n5</div>
                  <div className="text-[10px] text-slate-400">Core Router</div>
                </div>
              </div>

              {/* Servers: n6, n7, n8, n9 (Cols 9-10) */}
              <div className="md:col-span-2 space-y-2">
                <div className="p-2 rounded-lg bg-blue-950/40 border border-blue-900 text-blue-300">
                  <div className="font-bold">n6: Web Srv</div>
                  <div className="text-[10px] text-slate-400">Port 80 Sink</div>
                </div>
                <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-900 text-emerald-300">
                  <div className="font-bold">n7: VoIP Srv</div>
                  <div className="text-[10px] text-slate-400">Null Agent</div>
                </div>
                <div className="p-2 rounded-lg bg-purple-950/40 border border-purple-900 text-purple-300">
                  <div className="font-bold">n8: Stream Srv</div>
                  <div className="text-[10px] text-slate-400">Sink Agent</div>
                </div>
                <div className="p-2 rounded-lg bg-amber-950/40 border border-amber-900 text-amber-300">
                  <div className="font-bold">n9: FTP Srv</div>
                  <div className="text-[10px] text-slate-400">Sink Agent</div>
                </div>
              </div>
            </div>
          </div>

          {/* NS-2 Trace File Event Stream (.tr Viewer) */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileCode className="w-5 h-5 text-cyan-400" />
                <span>NS-2 Discrete-Event Trace Log (flowsentry.tr)</span>
              </h3>
              <span className="text-xs font-mono text-slate-400">
                Format: <strong className="text-slate-200">Event Time From To PktType PktSize Flags FlowId Src Dst Seq PktId</strong>
              </span>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-2">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-slate-500 border-b border-slate-800/80">
                  <tr>
                    <th className="py-2 px-2.5">Event</th>
                    <th className="py-2 px-2.5">Time (s)</th>
                    <th className="py-2 px-2.5">Hop</th>
                    <th className="py-2 px-2.5">Protocol</th>
                    <th className="py-2 px-2.5">Size</th>
                    <th className="py-2 px-2.5">Flow ID</th>
                    <th className="py-2 px-2.5">Src → Dst</th>
                    <th className="py-2 px-2.5">Seq #</th>
                    <th className="py-2 px-2.5 text-right">FlowSentry Class</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40 text-slate-300">
                  {ns2Events.map((evt, idx) => {
                    const evtColor = evt.event === '+' ? 'text-blue-400' :
                                     evt.event === '-' ? 'text-emerald-400' :
                                     evt.event === 'r' ? 'text-cyan-400' : 'text-rose-400 font-bold';
                    const flowName = evt.flowId === 1 ? 'Web Browsing' :
                                     evt.flowId === 2 ? 'VoIP' :
                                     evt.flowId === 3 ? 'Streaming' : 'File Transfer';
                    return (
                      <tr key={idx} className={`hover:bg-slate-900/50 ${evt.event === 'd' ? 'bg-rose-950/20' : ''}`}>
                        <td className={`py-1.5 px-2.5 font-bold ${evtColor}`}>
                          {evt.event === '+' ? '+ (Enqueue)' :
                           evt.event === '-' ? '- (Dequeue)' :
                           evt.event === 'r' ? 'r (Receive)' : 'd (Drop)'}
                        </td>
                        <td className="py-1.5 px-2.5 text-slate-400">{evt.time.toFixed(6)}</td>
                        <td className="py-1.5 px-2.5 text-slate-200">n{evt.fromNode} → n{evt.toNode}</td>
                        <td className="py-1.5 px-2.5 uppercase">{evt.pktType}</td>
                        <td className="py-1.5 px-2.5 text-slate-300">{evt.pktSize} B</td>
                        <td className="py-1.5 px-2.5">
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-cyan-300">
                            Flow {evt.flowId}
                          </span>
                        </td>
                        <td className="py-1.5 px-2.5 text-slate-400">{evt.srcAddr} → {evt.dstAddr}</td>
                        <td className="py-1.5 px-2.5 text-slate-400">{evt.seqNum}</td>
                        <td className="py-1.5 px-2.5 text-right">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-sans font-medium border ${getTrafficBadge(flowName as TrafficClass)}`}>
                            {flowName}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-start gap-2.5">
              <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-200">Trace-to-Flow Feature Extraction:</strong> FlowSentry aggregates the packet timestamp deltas from the NS-2 `.tr` trace events into inter-arrival times (<code className="text-cyan-300">mean_fiat</code>, <code className="text-cyan-300">mean_biat</code>), measuring packet size throughput to predict application classes with 96.70% accuracy.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Captured Flows Table (Available in both modes) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Flows Extracted from Simulation Interface</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">
              {capturedFlows.length} Captured Bidirectional Flows
            </span>
            <button
              onClick={() => handleExportCapturePcap()}
              className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono flex items-center gap-1 border border-slate-700"
            >
              <Download className="w-3 h-3 text-cyan-400" />
              <span>Save PCAP</span>
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Flow ID</th>
                <th className="py-2.5 px-3">Five-Tuple (Src → Dst)</th>
                <th className="py-2.5 px-3">Proto</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Throughput</th>
                <th className="py-2.5 px-3">Mean FIAT</th>
                <th className="py-2.5 px-3">Packets / Bytes</th>
                <th className="py-2.5 px-3">ML Prediction</th>
                <th className="py-2.5 px-3 text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {capturedFlows.map((flow) => (
                <tr key={flow.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-3 text-slate-400">{flow.id}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">
                    {flow.fiveTuple.srcIp}:{flow.fiveTuple.srcPort} <span className="text-cyan-400">→</span> {flow.fiveTuple.dstIp}:{flow.fiveTuple.dstPort}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                      {flow.fiveTuple.protocol}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">
                    {flow.features.duration.toFixed(2)}s
                  </td>
                  <td className="py-2.5 px-3 text-cyan-300 font-semibold">
                    {(flow.features.flowBytesPerSecond / 1000).toFixed(1)} KB/s
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">
                    {(flow.features.mean_fiat * 1000).toFixed(1)} ms
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">
                    {flow.packetCount.toLocaleString()} pkts / {(flow.byteCount / 1024).toFixed(1)} KB
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded-full text-[11px] font-sans font-medium border ${getTrafficBadge(flow.predictedClass)}`}>
                      {flow.predictedClass}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right font-bold text-emerald-400">
                    {(flow.confidence * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
