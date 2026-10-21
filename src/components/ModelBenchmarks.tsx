import React, { useState } from 'react';
import { 
  BarChart3, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  Clock, 
  HardDrive, 
  Zap, 
  HelpCircle,
  Award,
  Layers,
  ArrowRightCircle,
  Cpu
} from 'lucide-react';
import { EVALUATED_MODELS } from '../data/registryData';
import { TrafficClass, ModelEvaluation } from '../types';

export const ModelBenchmarks: React.FC = () => {
  const [models, setModels] = useState<ModelEvaluation[]>(EVALUATED_MODELS);
  const [selectedModelId, setSelectedModelId] = useState<string>(EVALUATED_MODELS[0].modelId);

  const activeModel = models.find(m => m.modelId === selectedModelId) || models[0];

  const handleSetActiveModel = (modelId: string) => {
    setModels(prev => prev.map(m => ({
      ...m,
      status: m.modelId === modelId ? 'Selected' : 'Evaluated'
    })));
  };

  const getTrafficColor = (type: TrafficClass) => {
    switch (type) {
      case 'Web Browsing': return 'text-cyan-400';
      case 'VoIP': return 'text-emerald-400';
      case 'Streaming': return 'text-purple-400';
      case 'File Transfer': return 'text-amber-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Review-1 Abstract Check */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold mb-1">
              <Award className="w-4 h-4" />
              <span>Model Comparison & Review-1 Verification (CN-011 / EV-007)</span>
            </div>
            <h2 className="text-xl font-bold text-white">4-Classifier Evaluation & Performance Benchmarks</h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              All 4 classifiers (Decision Tree, Random Forest, XGBoost, and SVM) evaluated on the identical frozen test split (N=11,925 flows). Selection criterion: <strong className="text-slate-200">CV Macro F1 (RID-20)</strong>.
            </p>
          </div>

          {/* Review-1 Verification Pill */}
          <div className="bg-slate-950 border border-emerald-500/40 rounded-xl p-3.5 max-w-sm">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold mb-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Review-1 Abstract Claim Validated:</span>
            </div>
            <div className="text-xs text-slate-300">
              Review-1 claimed <span className="font-mono text-cyan-300">95–98%</span> accuracy for flow features.
              Our test accuracy across tree models is <span className="font-mono font-bold text-emerald-400">96.70% – 97.45%</span>.
            </div>
          </div>
        </div>
      </div>

      {/* Model Selection Cards with Production Switcher */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {models.map((model) => {
          const isSelected = model.modelId === selectedModelId;
          const isProduction = model.status === 'Selected';
          return (
            <div
              key={model.modelId}
              onClick={() => setSelectedModelId(model.modelId)}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                isSelected
                  ? 'border-cyan-500 bg-cyan-950/25 ring-1 ring-cyan-500 shadow-md'
                  : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-slate-400">
                    {isProduction ? (
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-semibold flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Active Model
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        Evaluated
                      </span>
                    )}
                  </span>
                  <span className="text-xs font-mono font-bold text-cyan-400">
                    F1: {(model.testMacroF1 * 100).toFixed(2)}%
                  </span>
                </div>

                <div className="text-sm font-bold text-slate-100">{model.modelName}</div>

                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800/80 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500">Test Accuracy</span>
                    <div className="text-slate-200 font-semibold">{(model.testAccuracy * 100).toFixed(2)}%</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500">Latency / Flow</span>
                    <div className="text-amber-400 font-semibold">{model.inferenceTimeMs.toFixed(4)} ms</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60">
                {!isProduction ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSetActiveModel(model.modelId);
                    }}
                    className="w-full py-1.5 px-2 bg-slate-800 hover:bg-cyan-600 hover:text-white text-slate-300 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1.5"
                  >
                    <Cpu className="w-3.5 h-3.5" />
                    <span>Set as Active</span>
                  </button>
                ) : (
                  <div className="text-center text-[11px] font-mono text-emerald-400 font-semibold py-1">
                    ✓ Currently Serving Registry
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 4-Model Comparative Visualization Bars */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-cyan-400" />
          <span>Cross-Model Benchmark Metric Breakdown</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Accuracy & Macro F1 Bar Chart */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-300 font-semibold">Classification Performance Comparison</span>
              <span className="text-slate-500">Scale: 90% - 100%</span>
            </div>

            <div className="space-y-3 pt-2">
              {models.map(m => {
                const accPct = Math.max(0, (m.testAccuracy - 0.90) / 0.10 * 100);
                const f1Pct = Math.max(0, (m.testMacroF1 - 0.90) / 0.10 * 100);
                return (
                  <div key={m.modelId} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-slate-300 font-semibold">{m.modelName.split(' ')[0]}</span>
                      <span className="text-cyan-400">Acc: {(m.testAccuracy * 100).toFixed(2)}% · F1: {(m.testMacroF1 * 100).toFixed(2)}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden flex gap-0.5">
                      <div className="bg-emerald-500 h-full rounded-l-full" style={{ width: `${accPct}%` }} title={`Accuracy: ${(m.testAccuracy*100).toFixed(2)}%`} />
                      <div className="bg-cyan-500 h-full rounded-r-full" style={{ width: `${f1Pct}%` }} title={`Macro F1: ${(m.testMacroF1*100).toFixed(2)}%`} />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center gap-4 text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-900">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-emerald-500" /> Test Accuracy</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-cyan-500" /> Test Macro F1</span>
            </div>
          </div>

          {/* Latency & Resource Efficiency Chart */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-slate-300 font-semibold">Inference Latency & Model Footprint</span>
              <span className="text-amber-400 font-semibold">Fastest: Decision Tree (0.007ms)</span>
            </div>

            <div className="space-y-3 pt-2">
              {models.map(m => {
                const maxLatency = 0.20;
                const latPct = Math.min(100, (m.inferenceTimeMs / maxLatency) * 100);
                return (
                  <div key={m.modelId} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-slate-300">{m.modelName.split(' ')[0]}</span>
                      <span className="text-amber-300">{m.inferenceTimeMs.toFixed(4)} ms/flow · {m.modelSizeMb.toFixed(1)} MB</span>
                    </div>
                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${m.inferenceTimeMs < 0.01 ? 'bg-emerald-400' : m.inferenceTimeMs < 0.05 ? 'bg-amber-400' : 'bg-rose-400'}`} 
                        style={{ width: `${Math.max(4, latPct)}%` }} 
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="p-2 bg-slate-900/60 rounded border border-slate-850 text-[11px] text-slate-400 font-mono">
              <strong>Why Decision Tree was selected (RID-20):</strong> Decision Tree achieves 96.70% accuracy at <strong className="text-cyan-300">0.0071 ms/flow</strong> with an 8.4 MB footprint and full rule interpretability, making it ideal for wire-speed classification without ensemble overhead.
            </div>
          </div>
        </div>
      </div>

      {/* 4-Model Comparison Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          <span>Comparative Metrics Matrix (PRD OBJ-2 & OBJ-3)</span>
        </h3>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Classifier Model</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">CV Macro F1</th>
                <th className="py-2.5 px-3">Test Accuracy</th>
                <th className="py-2.5 px-3">Test Macro F1</th>
                <th className="py-2.5 px-3">Weighted F1</th>
                <th className="py-2.5 px-3">Inference (ms)</th>
                <th className="py-2.5 px-3">Train Time (s)</th>
                <th className="py-2.5 px-3 text-right">Model Size</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {models.map((m) => (
                <tr 
                  key={m.modelId} 
                  className={`hover:bg-slate-800/40 transition-colors ${
                    m.modelId === selectedModelId ? 'bg-cyan-500/10' : ''
                  }`}
                >
                  <td className="py-2.5 px-3 font-semibold text-slate-100 flex items-center gap-2">
                    {m.modelName}
                    {m.status === 'Selected' && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                        ACTIVE
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      m.status === 'Selected' ? 'bg-emerald-950 text-emerald-300 font-bold' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {m.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-cyan-300">
                    {m.cvMacroF1.toFixed(4)}
                  </td>
                  <td className="py-2.5 px-3 font-semibold text-emerald-400">
                    {(m.testAccuracy * 100).toFixed(2)}%
                  </td>
                  <td className="py-2.5 px-3 text-slate-200">
                    {m.testMacroF1.toFixed(4)}
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">
                    {m.testWeightedF1.toFixed(4)}
                  </td>
                  <td className="py-2.5 px-3 text-amber-300 font-bold">
                    {m.inferenceTimeMs.toFixed(4)} ms
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">
                    {m.trainTimeSeconds.toFixed(1)} s
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300">
                    {m.modelSizeMb.toFixed(2)} MB
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Per-Class Breakdown & Confusion Matrix for Selected Model */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left: Per-Class Table (6 Cols) */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              <span>Per-Class Breakdown ({activeModel.modelName})</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">
              Held-Out Test Set (N={activeModel.testSamples.toLocaleString()})
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Traffic Category</th>
                  <th className="py-2.5 px-3">Precision</th>
                  <th className="py-2.5 px-3">Recall</th>
                  <th className="py-2.5 px-3">F1-Score</th>
                  <th className="py-2.5 px-3 text-right">Support</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {(Object.keys(activeModel.perClass) as TrafficClass[]).map(cls => {
                  const m = activeModel.perClass[cls];
                  return (
                    <tr key={cls} className="hover:bg-slate-800/40">
                      <td className={`py-2.5 px-3 font-semibold ${getTrafficColor(cls)}`}>
                        {cls}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-200">
                        {(m.precision * 100).toFixed(2)}%
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-slate-200">
                        {(m.recall * 100).toFixed(2)}%
                      </td>
                      <td className="py-2.5 px-3 font-bold text-emerald-400">
                        {(m.f1 * 100).toFixed(2)}%
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400">
                        {m.support.toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Observations */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-1.5 text-slate-400 font-sans">
            <div className="font-semibold text-slate-200 mb-1">Key Observations (from CN-010 / best_model.md):</div>
            <div>• <strong className="text-emerald-400">VoIP</strong> achieves highest F1 (98.80%) due to strictly periodic ~20ms RTP packet spacing.</div>
            <div>• <strong className="text-cyan-400">Web Browsing</strong> achieves 96.82% F1 on bursty DOM page resource requests.</div>
            <div>• <strong className="text-amber-400">File Transfer</strong> achieves 94.96% F1 driven by high link throughput (&gt;500 KB/s).</div>
            <div>• <strong className="text-purple-400">Streaming</strong> has lowest F1 (92.50%) due to small sample support (548 samples / 4.6% of test set).</div>
          </div>
        </div>

        {/* Right: Confusion Matrix (6 Cols) */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              <span>Confusion Matrix ({activeModel.modelName})</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">Horizontal: Predicted · Vertical: True</span>
          </div>

          <div className="overflow-x-auto p-2 bg-slate-950 rounded-xl border border-slate-800">
            <table className="w-full text-center text-xs font-mono">
              <thead>
                <tr>
                  <th className="p-2 text-slate-500 font-normal">True \ Pred</th>
                  {activeModel.confusionMatrix.labels.map(l => (
                    <th key={l} className="p-2 text-slate-300 font-semibold">{l.replace(' ', '\n')}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activeModel.confusionMatrix.labels.map((rowLabel, rIdx) => (
                  <tr key={rowLabel} className="border-t border-slate-900">
                    <td className="p-2 text-slate-300 font-semibold text-left whitespace-nowrap">{rowLabel}</td>
                    {activeModel.confusionMatrix.matrix[rIdx].map((val, cIdx) => {
                      const isDiagonal = rIdx === cIdx;
                      return (
                        <td 
                          key={cIdx} 
                          className={`p-3 rounded font-bold transition-all ${
                            isDiagonal
                              ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 font-mono text-sm'
                              : val > 20
                              ? 'bg-red-950/40 text-red-300 border border-red-900/40 font-mono'
                              : 'bg-slate-900/40 text-slate-500 font-mono'
                          }`}
                        >
                          {val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 font-mono">
            Diagonal cells represent correct classifications. Total test accuracy for {activeModel.modelName}: <strong className="text-emerald-400">{(activeModel.testAccuracy * 100).toFixed(2)}%</strong> across 11,925 test flows.
          </div>
        </div>

      </div>
    </div>
  );
};
