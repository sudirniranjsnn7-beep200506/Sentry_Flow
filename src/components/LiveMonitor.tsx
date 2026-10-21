import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Play, 
  Square, 
  Radio, 
  Zap, 
  Clock, 
  HardDrive, 
  Layers, 
  ShieldAlert, 
  Cpu, 
  CheckCircle2,
  TrendingUp,
  BarChart2,
  Sliders,
  AlertTriangle,
  Flame
} from 'lucide-react';
import { NetworkFlow, TrafficClass } from '../types';
import { generateSyntheticFlow } from '../utils/mlEngine';

export const LiveMonitor: React.FC = () => {
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [flows, setFlows] = useState<NetworkFlow[]>([]);
  const [streamSpeed, setStreamSpeed] = useState<number>(1); // 1 = 1 flow/sec, 2 = 2 flows/sec, 5 = 5 flows/sec
  const [oodThreshold, setOodThreshold] = useState<number>(0.75); // Out-of-distribution threshold (RID-19)
  const [totalBytesProcessed, setTotalBytesProcessed] = useState<number>(14250000);
  const [meanLatencyMs, setMeanLatencyMs] = useState<number>(0.0071);
  const [oodAlertCount, setOodAlertCount] = useState<number>(0);
  const intervalRef = useRef<number | null>(null);

  // Initialize with initial live buffer
  useEffect(() => {
    const initial = Array.from({ length: 8 }, () => generateSyntheticFlow());
    setFlows(initial);
  }, []);

  // Streaming loop
  useEffect(() => {
    if (isRunning) {
      const intervalMs = Math.round(1000 / streamSpeed);
      intervalRef.current = window.setInterval(() => {
        // Occasionally generate an out-of-distribution / anomalous flow to demonstrate RID-19
        const isAnomalous = Math.random() < 0.15;
        let newFlow = generateSyntheticFlow();
        
        if (isAnomalous) {
          // Artificial anomalous flow (e.g. DNS tunneling / BitTorrent encryption signature)
          newFlow = {
            ...newFlow,
            id: `flow-ood-${Math.floor(100 + Math.random() * 900)}`,
            confidence: 0.58 + Math.random() * 0.14,
            decisionPath: [
              'Mixed inter-arrival times: does not fit strict VoIP or Web signature',
              'Throughput variance outside standard Gaussian bounds',
              '⚠️ Flagged: Out-of-Distribution / Low Confidence Flow (RID-19)'
            ]
          };
          setOodAlertCount(c => c + 1);
        }

        setFlows(prev => [newFlow, ...prev.slice(0, 24)]);
        setTotalBytesProcessed(prev => prev + newFlow.byteCount);
        setMeanLatencyMs(0.0068 + Math.random() * 0.0008);
      }, intervalMs);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning, streamSpeed]);

  const classCounts: Record<TrafficClass, number> = {
    'Web Browsing': flows.filter(f => f.confidence >= oodThreshold && f.predictedClass === 'Web Browsing').length,
    'VoIP': flows.filter(f => f.confidence >= oodThreshold && f.predictedClass === 'VoIP').length,
    'Streaming': flows.filter(f => f.confidence >= oodThreshold && f.predictedClass === 'Streaming').length,
    'File Transfer': flows.filter(f => f.confidence >= oodThreshold && f.predictedClass === 'File Transfer').length,
  };

  const oodCount = flows.filter(f => f.confidence < oodThreshold).length;

  const getTrafficColor = (type: TrafficClass, conf: number) => {
    if (conf < oodThreshold) {
      return 'bg-amber-950/80 text-amber-300 border-amber-800';
    }
    switch (type) {
      case 'Web Browsing': return 'bg-cyan-950 text-cyan-300 border-cyan-800';
      case 'VoIP': return 'bg-emerald-950 text-emerald-300 border-emerald-800';
      case 'Streaming': return 'bg-purple-950 text-purple-300 border-purple-800';
      case 'File Transfer': return 'bg-amber-950 text-amber-300 border-amber-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Live Monitor Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold mb-1">
              <Activity className="w-4 h-4" />
              <span>Near-Live Rolling Chunk Classification (CN-016 / CN-017 / RT-003)</span>
            </div>
            <h2 className="text-xl font-bold text-white">Live Interface Capture & Flow Classifier</h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Processes rolling packet windows, extracts statistical flow features without payload access, and enforces <span className="font-mono text-amber-300">RID-19 OOD Confidence Guards</span> for unmapped or anomalous traffic.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 transition-all shadow-sm ${
                isRunning
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30'
                  : 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
              }`}
            >
              {isRunning ? (
                <>
                  <Square className="w-3.5 h-3.5 fill-current" />
                  <span>Pause Stream</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Resume Capture</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Real-time Controls Bar: Speed & OOD Threshold */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3 bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            <Sliders className="w-4 h-4 text-cyan-400 shrink-0" />
            <div className="flex-1">
              <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
                <span>Ingestion Rate:</span>
                <span className="text-cyan-400 font-bold">{streamSpeed} flow{streamSpeed > 1 ? 's' : ''}/sec</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={streamSpeed}
                onChange={(e) => setStreamSpeed(parseInt(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="flex-1">
              <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
                <span>OOD / Uncertainty Guard (RID-19):</span>
                <span className="text-amber-300 font-bold">{(oodThreshold * 100).toFixed(0)}% Min Conf</span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.95"
                step="0.05"
                value={oodThreshold}
                onChange={(e) => setOodThreshold(parseFloat(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Real-Time Telemetry Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Inference Latency</span>
            <Zap className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono">
            {meanLatencyMs.toFixed(4)} <span className="text-sm font-normal text-slate-400">ms/flow</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Single Decision Tree traversal</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Flow Ingestion Rate</span>
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-cyan-400 font-mono">
            {streamSpeed} <span className="text-sm font-normal text-slate-400">flows/s</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Rolling 1-second chunks</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Traffic Processed</span>
            <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {(totalBytesProcessed / (1024 * 1024)).toFixed(1)} <span className="text-sm font-normal text-slate-400">MB</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Payload bytes discarded</div>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>OOD Flows Flagged</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">
            {oodCount} <span className="text-sm font-normal text-slate-400">flows</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Below {(oodThreshold * 100).toFixed(0)}% confidence</div>
        </div>
      </div>

      {/* Real-time Category Breakdown Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-slate-400 uppercase font-semibold">Live Traffic Distribution (Active Window)</span>
          <span className="text-cyan-400 font-bold">{flows.length} Active Flows</span>
        </div>

        <div className="h-3 w-full bg-slate-950 rounded-full flex overflow-hidden border border-slate-800">
          {(['Web Browsing', 'VoIP', 'Streaming', 'File Transfer'] as TrafficClass[]).map(cls => {
            const count = classCounts[cls];
            const pct = flows.length ? (count / flows.length) * 100 : 0;
            const bg = cls === 'Web Browsing' ? 'bg-cyan-500' :
                       cls === 'VoIP' ? 'bg-emerald-500' :
                       cls === 'Streaming' ? 'bg-purple-500' : 'bg-amber-500';
            return (
              <div 
                key={cls} 
                className={`${bg} h-full transition-all duration-500`} 
                style={{ width: `${pct}%` }}
                title={`${cls}: ${count} (${pct.toFixed(1)}%)`}
              />
            );
          })}
          {oodCount > 0 && (
            <div 
              className="bg-amber-500 h-full transition-all duration-500" 
              style={{ width: `${(oodCount / flows.length) * 100}%` }}
              title={`OOD / Uncertain: ${oodCount}`}
            />
          )}
        </div>

        <div className="flex flex-wrap justify-between gap-2 text-xs font-mono text-slate-300 pt-1">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
            <span>Web: {classCounts['Web Browsing']}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>VoIP: {classCounts['VoIP']}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
            <span>Streaming: {classCounts['Streaming']}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>FTP: {classCounts['File Transfer']}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="text-amber-300">Uncertain (OOD): {oodCount}</span>
          </div>
        </div>
      </div>

      {/* Streaming Flow Feed Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <span>Live Bidirectional Flow Event Stream</span>
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {isRunning ? `Ingesting at ${streamSpeed} flow/sec on Gi0/1...` : 'Stream paused'}
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Flow ID</th>
                <th className="py-2.5 px-3">Five-Tuple (Src → Dst)</th>
                <th className="py-2.5 px-3">Proto</th>
                <th className="py-2.5 px-3">Duration</th>
                <th className="py-2.5 px-3">Throughput</th>
                <th className="py-2.5 px-3">Classification</th>
                <th className="py-2.5 px-3 text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {flows.map((flow, idx) => {
                const isOod = flow.confidence < oodThreshold;
                return (
                  <tr 
                    key={flow.id} 
                    className={`hover:bg-slate-800/40 transition-colors ${
                      idx === 0 && isRunning ? 'bg-cyan-500/10' : ''
                    } ${isOod ? 'bg-amber-950/20' : ''}`}
                  >
                    <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">{flow.timestamp.split(' ')[1]}</td>
                    <td className="py-2.5 px-3 text-slate-300 font-semibold">{flow.id}</td>
                    <td className="py-2.5 px-3 text-slate-200">
                      {flow.fiveTuple.srcIp}:{flow.fiveTuple.srcPort} <span className="text-cyan-400">→</span> {flow.fiveTuple.dstIp}:{flow.fiveTuple.dstPort}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                        {flow.fiveTuple.protocol}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{flow.features.duration.toFixed(2)}s</td>
                    <td className="py-2.5 px-3 text-cyan-300 font-semibold">
                      {(flow.features.flowBytesPerSecond / 1000).toFixed(1)} KB/s
                    </td>
                    <td className="py-2.5 px-3">
                      {isOod ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-sans font-medium border bg-amber-950 text-amber-300 border-amber-800 flex items-center gap-1 w-fit">
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                          <span>Uncertain ({flow.predictedClass})</span>
                        </span>
                      ) : (
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-sans font-medium border ${getTrafficColor(flow.predictedClass, flow.confidence)}`}>
                          {flow.predictedClass}
                        </span>
                      )}
                    </td>
                    <td className={`py-2.5 px-3 text-right font-bold ${isOod ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {(flow.confidence * 100).toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
