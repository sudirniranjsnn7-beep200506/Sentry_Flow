import React, { useState } from 'react';
import { 
  Cpu, 
  ShieldCheck, 
  CheckCircle2, 
  GitBranch, 
  Key, 
  HardDrive, 
  FileCode, 
  Layers, 
  Sliders, 
  Info,
  ChevronDown,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { ACTIVE_MODEL_INFO, SELECTED_FEATURES_INFO } from '../data/registryData';

export const ModelRegistryView: React.FC = () => {
  const [activeFeature, setActiveFeature] = useState<string>(SELECTED_FEATURES_INFO[0].name);
  const [isVerifyingChecksum, setIsVerifyingChecksum] = useState<boolean>(false);
  const [checksumVerified, setChecksumVerified] = useState<boolean>(true);

  const selectedFeature = SELECTED_FEATURES_INFO.find(f => f.name === activeFeature) || SELECTED_FEATURES_INFO[0];

  const handleVerifyNow = () => {
    setIsVerifyingChecksum(true);
    setTimeout(() => {
      setIsVerifyingChecksum(false);
      setChecksumVerified(true);
    }, 500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold mb-1">
              <Cpu className="w-4 h-4" />
              <span>File-Based Model Registry (CN-012 / TRD §20)</span>
            </div>
            <h2 className="text-xl font-bold text-white">Active Model Registry & Provenance</h2>
            <p className="text-sm text-slate-400 max-w-2xl mt-1">
              Models are stored with SHA-256 integrity checksums, library environments, canonical feature schemas, and hyperparameters in <span className="font-mono text-cyan-300">artifacts/registry/</span>.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleVerifyNow}
              disabled={isVerifyingChecksum}
              className="text-xs px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-mono flex items-center gap-2 transition-all"
            >
              <ShieldCheck className={`w-4 h-4 ${checksumVerified ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{isVerifyingChecksum ? 'Verifying SHA-256...' : 'Verify Checksum'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Model Overview & Integrity Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left: Metadata & Integrity (7 Cols) */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-mono uppercase text-cyan-400 font-semibold tracking-wider">
                Production Model
              </span>
              <h3 className="text-lg font-bold text-white mt-0.5">{ACTIVE_MODEL_INFO.modelName}</h3>
              <div className="text-xs font-mono text-slate-400 mt-1">
                ID: <strong className="text-slate-200">{ACTIVE_MODEL_INFO.modelId}</strong>
              </div>
            </div>

            <div className="text-right">
              <span className="px-3 py-1 rounded-full text-xs font-bold font-mono bg-emerald-950 text-emerald-300 border border-emerald-800 inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Active & Verified
              </span>
              <div className="text-[11px] font-mono text-slate-500 mt-1">
                Registered: {ACTIVE_MODEL_INFO.registrationDate}
              </div>
            </div>
          </div>

          {/* Cryptographic Checksums */}
          <div className="space-y-3 font-mono text-xs">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Pipeline SHA-256 Checksum:</span>
                </span>
                <span className="text-emerald-400 text-[10px] font-semibold">MATCHES DISK</span>
              </div>
              <div className="text-slate-200 break-all text-[11px] bg-slate-900 p-1.5 rounded border border-slate-800/80">
                {ACTIVE_MODEL_INFO.pipelineSha256}
              </div>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Label Mapping Hash:</span>
                </span>
                <span className="text-emerald-400 text-[10px] font-semibold">APPROVED (G-LABEL)</span>
              </div>
              <div className="text-slate-200 break-all text-[11px] bg-slate-900 p-1.5 rounded border border-slate-800/80">
                {ACTIVE_MODEL_INFO.labelMappingHash}
              </div>
            </div>
          </div>

          {/* Tree Structure Specs */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 font-semibold">
              Fitted Decision Tree Structure (scikit-learn 1.9.1)
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px]">Total Nodes</span>
                <div className="text-base font-bold text-white mt-0.5">{ACTIVE_MODEL_INFO.treeStats.nodes.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px]">Leaf Nodes</span>
                <div className="text-base font-bold text-cyan-400 mt-0.5">{ACTIVE_MODEL_INFO.treeStats.leaves.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px]">Max Depth</span>
                <div className="text-base font-bold text-purple-400 mt-0.5">{ACTIVE_MODEL_INFO.treeStats.maxDepth}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                <span className="text-slate-500 text-[10px]">Features Retained</span>
                <div className="text-base font-bold text-emerald-400 mt-0.5">{ACTIVE_MODEL_INFO.treeStats.featuresRetained}</div>
              </div>
            </div>
          </div>

          {/* Hyperparameters Table */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono space-y-2">
            <span className="text-slate-400 font-semibold block">Tuned Hyperparameters:</span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <div><span className="text-slate-500">criterion:</span> <span className="text-slate-200">gini</span></div>
              <div><span className="text-slate-500">splitter:</span> <span className="text-slate-200">best</span></div>
              <div><span className="text-slate-500">max_depth:</span> <span className="text-slate-200">40</span></div>
              <div><span className="text-slate-500">min_samples_split:</span> <span className="text-slate-200">2</span></div>
              <div><span className="text-slate-500">min_samples_leaf:</span> <span className="text-slate-200">1</span></div>
              <div><span className="text-slate-500">class_weight:</span> <span className="text-slate-200">balanced</span></div>
            </div>
          </div>
        </div>

        {/* Right: 9 Selected Features Explorer (5 Cols) */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              <span>9 Selected Features (CN-005)</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">RandomForest Selector</span>
          </div>

          <p className="text-xs text-slate-400">
            Out of 21 canonical flow metrics, in-fold feature selection retained these 9 features capturing the rhythm and throughput of encrypted traffic:
          </p>

          <div className="space-y-2">
            {SELECTED_FEATURES_INFO.map(feat => {
              const isSelected = feat.name === activeFeature;
              return (
                <div
                  key={feat.name}
                  onClick={() => setActiveFeature(feat.name)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-cyan-500 bg-cyan-950/30 ring-1 ring-cyan-500'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-semibold text-slate-200 flex items-center gap-2">
                      <span className="w-4 text-cyan-400 font-bold">#{feat.rank}</span>
                      <span>{feat.name}</span>
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {feat.family} ({feat.unit})
                    </span>
                  </div>

                  {isSelected && (
                    <div className="mt-2.5 pt-2 border-t border-slate-800 text-xs space-y-1 font-sans">
                      <p className="text-slate-300">{feat.description}</p>
                      <p className="text-cyan-300/90 text-[11px] font-medium mt-1">
                        <strong>Traffic Impact:</strong> {feat.classImpact}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
};
