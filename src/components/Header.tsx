import React from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  Network, 
  Activity, 
  BarChart3, 
  Binary, 
  Database,
  CheckCircle2,
  Zap
} from 'lucide-react';
import { ACTIVE_MODEL_INFO } from '../data/registryData';

export type TabKey = 'simulation' | 'pcap' | 'live' | 'benchmarks' | 'registry' | 'dataset';

interface HeaderProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    { key: 'simulation' as TabKey, label: 'Network Topology', icon: Network, desc: 'Cisco Packet Tracer simulation' },
    { key: 'pcap' as TabKey, label: 'PCAP Classifier', icon: Binary, desc: 'Flow extraction & inference' },
    { key: 'live' as TabKey, label: 'Live Monitor', icon: Activity, desc: 'Near-live chunk stream' },
    { key: 'benchmarks' as TabKey, label: 'Model Benchmarks', icon: BarChart3, desc: '4-model evaluation & matrix' },
    { key: 'registry' as TabKey, label: 'Model Registry', icon: Cpu, desc: 'Active model & 9 features' },
    { key: 'dataset' as TabKey, label: 'Schema & Labels', icon: Database, desc: 'ISCX-VPN2016 mappings' },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between py-4 gap-4">
          {/* Logo & Project Identity */}
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20 text-white">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                  FlowSentry
                  <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/80 font-mono">
                    Review-1 Specification
                  </span>
                </h1>
              </div>
              <p className="text-xs text-slate-400 font-medium">
                ML-Based Network Traffic Classification Using Flow-Level Statistics · No Payload Inspection
              </p>
            </div>
          </div>

          {/* Active Model Status Pill */}
          <div className="flex items-center gap-3 bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs">
            <div className="flex items-center gap-2 border-r border-slate-800 pr-3">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-400">Active Model:</span>
              <span className="text-slate-200 font-semibold font-mono">Decision Tree</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
              <span className="flex items-center gap-1 font-mono text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                96.70% Acc
              </span>
              <span className="font-mono text-cyan-400 border-l border-slate-800 pl-3">
                0.9577 F1
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 font-mono text-amber-400 border-l border-slate-800 pl-3">
                <Zap className="w-3 h-3" />
                0.007ms/flow
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto pb-2 scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onTabChange(tab.key)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
