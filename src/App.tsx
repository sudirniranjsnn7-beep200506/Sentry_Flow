import React, { useState } from 'react';
import { Header, TabKey } from './components/Header';
import { NetworkTopology } from './components/NetworkTopology';
import { PcapClassifier } from './components/PcapClassifier';
import { LiveMonitor } from './components/LiveMonitor';
import { ModelBenchmarks } from './components/ModelBenchmarks';
import { ModelRegistryView } from './components/ModelRegistryView';
import { DatasetSchema } from './components/DatasetSchema';
import { 
  ShieldCheck, 
  Sparkles, 
  ExternalLink, 
  HelpCircle,
  FileText,
  Play
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('simulation');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Global Navigation Header */}
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'simulation' && <NetworkTopology />}
        {activeTab === 'pcap' && <PcapClassifier />}
        {activeTab === 'live' && <LiveMonitor />}
        {activeTab === 'benchmarks' && <ModelBenchmarks />}
        {activeTab === 'registry' && <ModelRegistryView />}
        {activeTab === 'dataset' && <DatasetSchema />}
      </main>

      {/* Academic & Provenance Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/60 py-6 mt-12 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <div className="font-semibold text-slate-300">
              FlowSentry — Computer Networks Academic Review-1 Project (VIT)
            </div>
            <div className="text-slate-500 mt-0.5">
              Team: Sudir Niranj R (24BDS0267) · Vishal B S (24BCE2475)
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-slate-400 font-mono text-[11px]">
            <span>Dataset: ISCX-VPN2016</span>
            <span>•</span>
            <span>Production Model: Decision Tree (96.70% Acc)</span>
            <span>•</span>
            <span>Port: 3000</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
