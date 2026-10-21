import React, { useState, useEffect } from 'react';
import { 
  Laptop, 
  Server, 
  Router, 
  Network, 
  Play, 
  RefreshCw, 
  Radio, 
  Send, 
  FileText, 
  ArrowRight,
  ShieldAlert,
  Info,
  Download,
  Terminal,
  FileCode
} from 'lucide-react';
import { TrafficClass, NetworkFlow } from '../types';
import { generateSyntheticFlow } from '../utils/mlEngine';
import { exportFlowsToPcapBlob } from '../utils/pcapParser';

export const NetworkTopology: React.FC = () => {
  const [activeTraffic, setActiveTraffic] = useState<TrafficClass | null>('Web Browsing');
  const [capturedFlows, setCapturedFlows] = useState<NetworkFlow[]>([]);
  const [showIosConfig, setShowIosConfig] = useState<boolean>(false);
  const [packetAnimation, setPacketAnimation] = useState<{
    source: string;
    target: string;
    step: 'client-switch' | 'switch-router' | 'router-server' | 'complete';
    trafficType: TrafficClass;
  } | null>(null);

  // Initialize with a few captured flows
  useEffect(() => {
    const f1 = generateSyntheticFlow('Web Browsing');
    const f2 = generateSyntheticFlow('VoIP');
    const f3 = generateSyntheticFlow('Streaming');
    const f4 = generateSyntheticFlow('File Transfer');
    setCapturedFlows([f1, f2, f3, f4]);
  }, []);

  const triggerSimulation = (trafficType: TrafficClass) => {
    setActiveTraffic(trafficType);
    
    // Animate packet traversal
    setPacketAnimation({
      source: trafficType,
      target: 'router',
      step: 'client-switch',
      trafficType
    });

    setTimeout(() => {
      setPacketAnimation(prev => prev ? { ...prev, step: 'switch-router' } : null);
    }, 500);

    setTimeout(() => {
      setPacketAnimation(prev => prev ? { ...prev, step: 'router-server' } : null);
    }, 1000);

    setTimeout(() => {
      setPacketAnimation(null);
      const newFlow = generateSyntheticFlow(trafficType);
      setCapturedFlows(prev => [newFlow, ...prev.slice(0, 14)]);
    }, 1500);
  };

  const handleExportCapturePcap = (trafficType?: TrafficClass) => {
    const targetFlows = trafficType
      ? capturedFlows.filter(f => f.predictedClass === trafficType)
      : capturedFlows;
    
    const flowsToExport = targetFlows.length > 0 ? targetFlows : capturedFlows;
    const blob = exportFlowsToPcapBlob(flowsToExport);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = trafficType ? `${trafficType.toLowerCase().replace(' ', '_')}.pcap` : 'router_r1_capture.pcap';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPacketTracerScript = () => {
    const script = `! =======================================================
! Cisco Packet Tracer Topology Setup Script (CN-023)
! Project: FlowSentry - Network Traffic Classification
! Gateway Router: Cisco 2911 (R1)
! =======================================================
enable
configure terminal
hostname R1

! Configure Client-facing Interface (Subnet: 10.0.0.0/24)
interface GigabitEthernet0/0
 description Client Subnet Gateway
 ip address 10.0.0.1 255.255.255.0
 no shutdown
exit

! Configure Server Farm Interface (Subnet: 10.0.1.0/24)
interface GigabitEthernet0/1
 description Server Farm & Traffic Capture Point
 ip address 10.0.1.1 255.255.255.0
 no shutdown
exit

! Enable IP Routing
ip routing

! Verification
show ip interface brief
show ip route

end
write memory
`;
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
      {/* Top Banner & Context */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold mb-1">
              <Network className="w-4 h-4" />
              <span>Cisco Packet Tracer Architecture (CN-023 / Review-1)</span>
            </div>
            <h2 className="text-xl font-bold text-white">Enterprise Network Simulation & Router Capture Point</h2>
            <p className="text-sm text-slate-400 max-w-3xl mt-1">
              Simulates client workstations generating application traffic through Switch SW1 and Router R1.
              Traffic is tapped at Router interface <span className="font-mono text-cyan-300 font-semibold">Gi0/1</span>, grouped by five-tuple into bidirectional flows, and classified by FlowSentry without inspecting payload bytes.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 self-start md:self-center">
            <button
              onClick={() => setShowIosConfig(!showIosConfig)}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono flex items-center gap-1.5 transition-all"
            >
              <Terminal className="w-3.5 h-3.5 text-cyan-400" />
              <span>{showIosConfig ? 'Hide Cisco IOS Config' : 'View Cisco IOS Config'}</span>
            </button>

            <button
              onClick={handleDownloadPacketTracerScript}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono flex items-center gap-1.5 transition-all"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Download .ios Script</span>
            </button>
          </div>
        </div>

        {/* Traffic Buttons Bar */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-mono">Trigger Packet Stream:</span>
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

          <button
            onClick={() => handleExportCapturePcap()}
            className="text-xs px-3 py-1.5 rounded-lg border border-cyan-600 bg-cyan-950/40 hover:bg-cyan-900/50 text-cyan-300 font-mono flex items-center gap-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export Capture PCAP</span>
          </button>
        </div>
      </div>

      {/* Cisco IOS Config Drawer */}
      {showIosConfig && (
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2">
            <span className="flex items-center gap-2 text-cyan-400 font-bold">
              <Terminal className="w-4 h-4" />
              <span>Cisco 2911 Router R1 Running Configuration (docs/simulation/topology.md)</span>
            </span>
            <button
              onClick={handleDownloadPacketTracerScript}
              className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
            >
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
R1(config-if)# exit

! Server Farm Interface (Traffic Capture Tapping Point)
R1(config)# interface GigabitEthernet0/1
R1(config-if)# ip address 10.0.1.1 255.255.255.0
R1(config-if)# no shutdown
R1(config-if)# exit

! Enable IP Routing
R1(config)# ip routing
R1(config)# end
R1# write memory`}
          </pre>
        </div>
      )}

      {/* Visual Network Topology Canvas */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
        {/* Subnet Labels */}
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

        {/* Topology Diagram Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-11 gap-4 items-center">
          
          {/* CLIENTS (Columns 1-3) */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 font-semibold">
              Client Devices (Traffic Generators)
            </h4>
            
            {/* Client 1 */}
            <div 
              onClick={() => triggerSimulation('Web Browsing')}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                activeTraffic === 'Web Browsing'
                  ? 'border-cyan-500/60 bg-cyan-950/30 ring-1 ring-cyan-500/50'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg">
                    <Laptop className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">Client1 (Web)</div>
                    <div className="text-xs font-mono text-slate-400">10.0.0.10 → Port 80/443</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                  HTTP GET
                </span>
              </div>
            </div>

            {/* Client 2 */}
            <div 
              onClick={() => triggerSimulation('VoIP')}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                activeTraffic === 'VoIP'
                  ? 'border-emerald-500/60 bg-emerald-950/30 ring-1 ring-emerald-500/50'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                    <Radio className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">Client2 (VoIP)</div>
                    <div className="text-xs font-mono text-slate-400">10.0.0.11 → Port 5060/RTP</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                  SIP/RTP
                </span>
              </div>
            </div>

            {/* Client 3 */}
            <div 
              onClick={() => triggerSimulation('Streaming')}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                activeTraffic === 'Streaming'
                  ? 'border-purple-500/60 bg-purple-950/30 ring-1 ring-purple-500/50'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
                    <Laptop className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">Client3 (Stream)</div>
                    <div className="text-xs font-mono text-slate-400">10.0.0.12 → Port 554/8080</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-purple-950 text-purple-300 border border-purple-800">
                  RTSP/HLS
                </span>
              </div>
            </div>

            {/* Client 4 */}
            <div 
              onClick={() => triggerSimulation('File Transfer')}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                activeTraffic === 'File Transfer'
                  ? 'border-amber-500/60 bg-amber-950/30 ring-1 ring-amber-500/50'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">Client4 (FTP)</div>
                    <div className="text-xs font-mono text-slate-400">10.0.0.13 → Port 21/20</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-amber-950 text-amber-300 border border-amber-800">
                  FTP RETR
                </span>
              </div>
            </div>
          </div>

          {/* SWITCH & ROUTER (Columns 4-8) */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center p-4 bg-slate-900/40 rounded-xl border border-slate-800/80 my-2 lg:my-0 space-y-6">
            
            {/* Switch SW1 */}
            <div className="w-full max-w-xs p-3.5 bg-slate-900 border border-slate-700 rounded-xl text-center shadow-lg relative">
              <div className="flex items-center justify-center gap-2 text-cyan-400 mb-1">
                <Network className="w-5 h-5" />
                <span className="text-sm font-bold text-slate-200">Switch SW1</span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Cisco 2960-24TT · VLAN 1</p>
              <div className="mt-2 flex justify-center gap-1.5 text-[10px] font-mono text-slate-400">
                <span className="bg-slate-800 px-1.5 py-0.5 rounded">Fa0/1</span>
                <span className="bg-slate-800 px-1.5 py-0.5 rounded">Fa0/2</span>
                <span className="bg-slate-800 px-1.5 py-0.5 rounded">Fa0/3</span>
                <span className="bg-slate-800 px-1.5 py-0.5 rounded">Fa0/4</span>
              </div>
            </div>

            {/* Link connecting Switch & Router */}
            <div className="w-0.5 h-6 bg-cyan-500/40 relative">
              {packetAnimation?.step === 'switch-router' && (
                <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping absolute -left-1 top-1/2 -translate-y-1/2" />
              )}
            </div>

            {/* ROUTER R1 (The Core Capture Point) */}
            <div className="w-full max-w-sm p-4 bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-cyan-500/50 rounded-2xl text-center shadow-xl shadow-cyan-500/10 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-cyan-500 text-slate-950 text-[10px] font-bold font-mono tracking-wider uppercase">
                Packet Capture Point
              </div>

              <div className="flex items-center justify-center gap-2 text-cyan-400 mt-1 mb-1">
                <Router className="w-6 h-6 text-cyan-400" />
                <span className="text-base font-bold text-white">Router R1 (Cisco 2911)</span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800 text-xs text-left font-mono">
                <div className="bg-slate-950/80 p-2 rounded border border-slate-800">
                  <span className="text-slate-400 text-[10px]">Interface Gi0/0</span>
                  <div className="text-slate-200 font-bold">10.0.0.1/24</div>
                  <span className="text-[10px] text-cyan-400">Client Gateway</span>
                </div>
                <div className="bg-cyan-950/40 p-2 rounded border border-cyan-800/80">
                  <span className="text-cyan-300 text-[10px]">Interface Gi0/1 (TAP)</span>
                  <div className="text-cyan-200 font-bold">10.0.1.1/24</div>
                  <span className="text-[10px] text-emerald-400">Flow Extraction</span>
                </div>
              </div>

              <div className="mt-3 text-[11px] text-slate-400 bg-slate-950/60 p-2 rounded border border-slate-800/60">
                <span className="text-cyan-300 font-semibold">Tshark / Adapter:</span> 5-Tuple Aggregation → Statistical Features (Time, Volume, IAT)
              </div>
            </div>

          </div>

          {/* SERVERS (Columns 9-11) */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 font-semibold">
              Server Farm (Target Services)
            </h4>

            {/* Web Server */}
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
                    <Server className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">Web Server</div>
                    <div className="text-xs font-mono text-slate-400">10.0.1.100 : 80</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-blue-950 text-blue-300 border border-blue-800">
                  Apache/HTTP
                </span>
              </div>
            </div>

            {/* VoIP Server */}
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                    <Server className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">VoIP PBX Server</div>
                    <div className="text-xs font-mono text-slate-400">10.0.1.101 : 5060</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Asterisk/SIP
                </span>
              </div>
            </div>

            {/* Streaming Server */}
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
                    <Server className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">Streaming Server</div>
                    <div className="text-xs font-mono text-slate-400">10.0.1.102 : 554</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-purple-950 text-purple-300 border border-purple-800">
                  RTSP/Media
                </span>
              </div>
            </div>

            {/* FTP Server */}
            <div className="p-3 rounded-xl border border-slate-800 bg-slate-900/60">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
                    <Server className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">FTP Server</div>
                    <div className="text-xs font-mono text-slate-400">10.0.1.103 : 21/20</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-amber-950 text-amber-300 border border-amber-800">
                  vsftpd
                </span>
              </div>
            </div>

          </div>

        </div>

        {/* Live Packet Animation Status */}
        {packetAnimation && (
          <div className="mt-4 p-2.5 bg-cyan-950/80 border border-cyan-800 rounded-xl flex items-center justify-between text-xs font-mono text-cyan-300 animate-pulse">
            <span className="flex items-center gap-2">
              <Send className="w-3.5 h-3.5 text-cyan-400" />
              Traversing: {packetAnimation.trafficType} packets → Router Gi0/1 Flow Aggregator
            </span>
            <span className="text-slate-400 font-sans">Extracting 5-Tuple...</span>
          </div>
        )}
      </div>

      {/* Captured Flows at Router R1 Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Flows Extracted at Router R1 Interface (Gi0/1)</h3>
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

        {/* Explainability Callout */}
        <div className="mt-4 p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-start gap-3">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-slate-200">Viva Examination Defense Point (PRD §1 & Review-1):</strong> Notice that the IP addresses and port numbers are shown above strictly as session metadata for networking inspection, but are <span className="text-amber-300 underline font-semibold">excluded from model features</span> (per RID-07). Classification relies entirely on the statistical behavior of the bidirectional flow (IAT distributions, packet cadences, and byte throughput).
          </div>
        </div>
      </div>
    </div>
  );
};
