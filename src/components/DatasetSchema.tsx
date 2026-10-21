import React, { useState } from 'react';
import { 
  Database, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  Filter, 
  Sparkles, 
  Key,
  ShieldCheck,
  FileCode,
  Search,
  Calculator,
  Zap,
  ArrowRight
} from 'lucide-react';
import { LABEL_MAPPINGS, CANONICAL_21_FEATURES } from '../data/registryData';
import { TrafficClass, FlowFeatures } from '../types';
import { classifyFlow } from '../utils/mlEngine';

export const DatasetSchema: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'labels' | 'schema' | 'pipeline' | 'calculator'>('labels');
  const [testLabelQuery, setTestLabelQuery] = useState<string>('P2P');

  // Interactive Calculator State
  const [calcDuration, setCalcDuration] = useState<number>(18.5);
  const [calcThroughput, setCalcThroughput] = useState<number>(45000);
  const [calcMeanFiat, setCalcMeanFiat] = useState<number>(0.022);
  const [calcStdFlowiat, setCalcStdFlowiat] = useState<number>(0.003);

  const getTargetClassBadge = (target: TrafficClass | 'DROP') => {
    switch (target) {
      case 'Web Browsing': return 'bg-cyan-950 text-cyan-300 border-cyan-800';
      case 'VoIP': return 'bg-emerald-950 text-emerald-300 border-emerald-800';
      case 'Streaming': return 'bg-purple-950 text-purple-300 border-purple-800';
      case 'File Transfer': return 'bg-amber-950 text-amber-300 border-amber-800';
      case 'DROP': return 'bg-rose-950 text-rose-300 border-rose-800';
    }
  };

  // Evaluate test label
  const testLabelResult = (() => {
    const q = testLabelQuery.trim().toUpperCase();
    if (!q) return null;
    const matched = LABEL_MAPPINGS.find(m => m.originalLabel.toUpperCase() === q);
    if (matched) return matched;
    
    // Fuzzy matching
    if (q.includes('VOIP') || q.includes('VOICE') || q.includes('SIP')) {
      return { originalLabel: q, targetClass: 'VoIP' as TrafficClass, category: 'Inferred Audio', notes: 'Matches voice RTP patterns' };
    }
    if (q.includes('STREAM') || q.includes('VIDEO') || q.includes('YOUTUBE')) {
      return { originalLabel: q, targetClass: 'Streaming' as TrafficClass, category: 'Inferred Media', notes: 'Matches media streaming' };
    }
    if (q.includes('FT') || q.includes('FTP') || q.includes('P2P') || q.includes('TORRENT')) {
      return { originalLabel: q, targetClass: 'File Transfer' as TrafficClass, category: 'Inferred Bulk', notes: 'Matches file transfer' };
    }
    if (q.includes('BROWSE') || q.includes('HTTP') || q.includes('WEB')) {
      return { originalLabel: q, targetClass: 'Web Browsing' as TrafficClass, category: 'Inferred Web', notes: 'Matches HTTP web browsing' };
    }
    return { originalLabel: q, targetClass: 'DROP' as const, category: 'Unmapped Protocol', notes: 'Outside PRD §14 target classes' };
  })();

  // Evaluate interactive calculator
  const calcFeatures: FlowFeatures = {
    duration: calcDuration,
    max_biat: calcMeanFiat * 2.2,
    mean_fiat: calcMeanFiat,
    mean_biat: calcMeanFiat * 1.1,
    flowBytesPerSecond: calcThroughput,
    min_flowiat: 0.0001,
    max_flowiat: calcMeanFiat * 3,
    mean_flowiat: calcMeanFiat,
    std_flowiat: calcStdFlowiat,
    flowPktsPerSecond: 80
  };

  const calcResult = classifyFlow(calcFeatures, {
    srcIp: '10.0.0.10',
    dstIp: '10.0.1.100',
    srcPort: 54100,
    dstPort: 80,
    protocol: 'TCP'
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold mb-1">
              <Database className="w-4 h-4" />
              <span>Dataset Governance & Feature Contract (CN-004 / CN-005)</span>
            </div>
            <h2 className="text-xl font-bold text-white">Dataset Label Mapping & Feature Schema</h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Governs ISCX-VPN2016 Scenario B mappings, zero-leakage preprocessing pipelines, and canonical 21-feature schemas enforced across training and inference.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setActiveTab('labels')}
              className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                activeTab === 'labels'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              Label Mappings (G-LABEL)
            </button>
            <button
              onClick={() => setActiveTab('schema')}
              className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                activeTab === 'schema'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              Canonical 21 Schema
            </button>
            <button
              onClick={() => setActiveTab('pipeline')}
              className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                activeTab === 'pipeline'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              Zero-Leakage Pipeline
            </button>
            <button
              onClick={() => setActiveTab('calculator')}
              className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                activeTab === 'calculator'
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 font-semibold'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              Feature Calculator
            </button>
          </div>
        </div>
      </div>

      {/* Tab 1: Label Mapping */}
      {activeTab === 'labels' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold mb-1 font-mono">
                <CheckCircle2 className="w-4 h-4" />
                <span>Status: APPROVED (config/label_mapping.yaml)</span>
              </div>
              <h3 className="text-base font-bold text-white">ISCX-VPN2016 Scenario B → 4 Target Classes</h3>
            </div>
            <div className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
              SHA-256: <span className="text-cyan-300">ecdf7e9f550eb0e5...</span>
            </div>
          </div>

          {/* Label Mapping Tester */}
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5" />
                <span>Interactive Label Mapping Rule Evaluator (TRD §6.4)</span>
              </span>
              <span className="text-[11px] font-mono text-slate-500">Try: VPN-P2P, CHAT, VOIP, MAIL</span>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={testLabelQuery}
                onChange={(e) => setTestLabelQuery(e.target.value)}
                placeholder="Enter dataset label..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            {testLabelResult && (
              <div className="flex items-center justify-between p-3 bg-slate-900/80 rounded-lg border border-slate-800 text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Input: <strong className="text-white">{testLabelResult.originalLabel}</strong></span>
                  <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-slate-400">Policy:</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-sans font-medium border ${getTargetClassBadge(testLabelResult.targetClass)}`}>
                    {testLabelResult.targetClass}
                  </span>
                </div>
                <div className="text-slate-400">{testLabelResult.category}</div>
              </div>
            )}
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Original ARFF/CSV Label</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Sample Count</th>
                  <th className="py-2.5 px-3">Target Application Class</th>
                  <th className="py-2.5 px-3 text-right">Mapping Policy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {LABEL_MAPPINGS.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-bold text-slate-200">{item.originalLabel}</td>
                    <td className="py-2.5 px-3 text-slate-400">{item.category}</td>
                    <td className="py-2.5 px-3 text-slate-300">{item.sampleCount?.toLocaleString() || 'N/A'}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-sans font-medium border ${getTargetClassBadge(item.targetClass)}`}>
                        {item.targetClass}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-400">
                      {item.targetClass === 'DROP' ? 'Explicit Exclusion (Reported)' : 'Preserved for Model'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-400">
            <strong className="text-slate-200">Non-Silent Exclusion Rule (DS-007):</strong> Notice that non-target categories like CHAT (4,120 flows) and MAIL (3,200 flows) were explicitly counted and dropped before training, preventing heterogeneous label blending while strictly maintaining data lineage.
          </div>
        </div>
      )}

      {/* Tab 2: Canonical 21 Feature Schema */}
      {activeTab === 'schema' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">
                Feature Families (Review-1 §TRD 9)
              </span>
              <h3 className="text-base font-bold text-white mt-0.5">21 Canonical Flow Metrics Schema</h3>
            </div>
            <div className="text-xs font-mono text-slate-400">
              Coverage: <strong className="text-cyan-400">19 Time</strong> · <strong className="text-amber-400">2 Volume</strong>
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Feature Name</th>
                  <th className="py-2.5 px-3">Family</th>
                  <th className="py-2.5 px-3">Unit</th>
                  <th className="py-2.5 px-3">Role in Active Pipeline</th>
                  <th className="py-2.5 px-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {CANONICAL_21_FEATURES.map((feat) => {
                  const isSelected = feat.role === 'Selected Feature';
                  return (
                    <tr 
                      key={feat.name}
                      className={`hover:bg-slate-800/40 ${isSelected ? 'bg-cyan-500/5' : ''}`}
                    >
                      <td className={`py-2.5 px-3 font-semibold ${isSelected ? 'text-cyan-300 font-bold' : 'text-slate-200'}`}>
                        {feat.name}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                          {feat.family}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{feat.unit}</td>
                      <td className="py-2.5 px-3">
                        {isSelected ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 font-sans font-medium">
                            ★ Selected Model Feature
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Filtered (Pruned by Selector)</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 text-xs">{feat.desc}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Zero-Leakage Pipeline Architecture */}
      {activeTab === 'pipeline' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Learned Preprocessing & In-Fold Feature Selector</h3>
            <p className="text-sm text-slate-400 mt-1">
              Guarantees strict absence of data leakage (ML-008 & AC-003). All scalers, variance thresholds, and importance filters are fit exclusively on training folds during 5-fold cross-validation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <div className="text-xs font-mono text-cyan-400 font-bold">STAGE 1: CLEANING</div>
              <div className="text-sm font-semibold text-slate-200">Identifier Removal</div>
              <p className="text-xs text-slate-400">
                Removes IPs, MACs, timestamps, and port numbers from feature matrix (retained strictly as display metadata).
              </p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <div className="text-xs font-mono text-cyan-400 font-bold">STAGE 2: SCALING</div>
              <div className="text-sm font-semibold text-slate-200">MinMaxScaler</div>
              <p className="text-xs text-slate-400">
                Learns min/max solely from train fold to normalize high-scale duration and throughput values without leaking test distribution.
              </p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <div className="text-xs font-mono text-cyan-400 font-bold">STAGE 3: SELECTION</div>
              <div className="text-sm font-semibold text-slate-200">Variance & Correlation</div>
              <p className="text-xs text-slate-400">
                Prunes constant/near-constant features (VarianceThreshold) and drops redundant collinear pairs with correlation &gt; 0.95.
              </p>
            </div>

            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <div className="text-xs font-mono text-cyan-400 font-bold">STAGE 4: ESTIMATOR</div>
              <div className="text-sm font-semibold text-slate-200">SelectFromModel</div>
              <p className="text-xs text-slate-400">
                Uses RandomForestClassifier feature importances to retain top 9 discriminative features for the final Decision Tree model.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Interactive Feature Calculator */}
      {activeTab === 'calculator' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold mb-1 font-mono">
              <Calculator className="w-4 h-4" />
              <span>Direct Flow Feature Calculator</span>
            </div>
            <h3 className="text-base font-bold text-white">Simulate & Classify Arbitrary Statistical Parameters</h3>
            <p className="text-sm text-slate-400 mt-1">
              Adjust flow metrics directly and observe how the fitted Decision Tree branches classify the flow in real-time.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-7 bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-4">
              <h4 className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider">
                Input Feature Values
              </h4>

              <div className="space-y-4 text-xs font-mono">
                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>duration:</span>
                    <span className="text-cyan-400 font-bold">{calcDuration.toFixed(1)} seconds</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="60"
                    step="0.5"
                    value={calcDuration}
                    onChange={(e) => setCalcDuration(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>flowBytesPerSecond (Throughput):</span>
                    <span className="text-cyan-400 font-bold">{(calcThroughput / 1000).toFixed(1)} KB/s ({calcThroughput.toLocaleString()} B/s)</span>
                  </div>
                  <input
                    type="range"
                    min="5000"
                    max="1500000"
                    step="5000"
                    value={calcThroughput}
                    onChange={(e) => setCalcThroughput(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>mean_fiat (Forward IAT):</span>
                    <span className="text-cyan-400 font-bold">{(calcMeanFiat * 1000).toFixed(1)} ms</span>
                  </div>
                  <input
                    type="range"
                    min="0.002"
                    max="0.200"
                    step="0.002"
                    value={calcMeanFiat}
                    onChange={(e) => setCalcMeanFiat(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-slate-300 mb-1">
                    <span>std_flowiat (Flow IAT Jitter):</span>
                    <span className="text-cyan-400 font-bold">{(calcStdFlowiat * 1000).toFixed(1)} ms</span>
                  </div>
                  <input
                    type="range"
                    min="0.001"
                    max="0.200"
                    step="0.001"
                    value={calcStdFlowiat}
                    onChange={(e) => setCalcStdFlowiat(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
                  />
                </div>
              </div>
            </div>

            {/* Classification Output */}
            <div className="lg:col-span-5 bg-slate-950 p-5 rounded-xl border border-slate-800 space-y-4">
              <h4 className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider">
                Inference Result
              </h4>

              <div className="p-4 bg-slate-900 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-xs text-slate-400 font-mono">Predicted Traffic Class</div>
                  <div className="text-lg font-bold text-white mt-1">{calcResult.predictedClass}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400 font-mono">Confidence</div>
                  <div className="text-lg font-bold text-emerald-400 font-mono">
                    {(calcResult.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Decision Rules */}
              <div className="space-y-1.5 text-xs font-mono bg-slate-900 p-3 rounded-xl border border-slate-800/80">
                <span className="text-slate-400 font-bold block mb-1">Evaluated Decision Path:</span>
                {calcResult.decisionPath.map((rule, idx) => (
                  <div key={idx} className="text-slate-300 flex items-start gap-1.5">
                    <span className="text-cyan-400">›</span>
                    <span>{rule}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
