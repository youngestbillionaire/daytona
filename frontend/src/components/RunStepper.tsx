import React from 'react';
import { 
  CheckCircle2, 
  Circle, 
  Loader2, 
  XCircle, 
  Search, 
  Network, 
  Sparkles, 
  FileCode, 
  Hammer, 
  ShieldAlert, 
  Globe, 
  Camera, 
  Presentation, 
  Mic, 
  CheckCheck
} from 'lucide-react';
import { StageEvent } from '../types';

const STAGES_META = [
  { id: 'IDEA_RECEIVED', name: 'Idea Ingestion', icon: Sparkles },
  { id: 'MARKET_RECON', name: 'Market Recon (Oxylabs)', icon: Search },
  { id: 'COMPETITOR_ENRICHMENT', name: 'Competitor Scraping', icon: Search },
  { id: 'OPPORTUNITY_GRAPH', name: 'Opportunity Graph (Neo4j)', icon: Network },
  { id: 'WHITESPACE_ANALYSIS', name: 'Whitespace Analysis', icon: Sparkles },
  { id: 'IDEATION', name: 'Product Ideation (Nosana)', icon: Sparkles },
  { id: 'NAMING_AND_BRANDING', name: 'Naming & Branding', icon: Sparkles },
  { id: 'SPEC_GENERATION', name: 'Technical Spec Gen', icon: FileCode },
  { id: 'MVP_SCAFFOLD', name: 'Sandbox Scaffold (Daytona)', icon: Hammer },
  { id: 'MVP_CODE_GENERATION', name: 'Modular Code Gen', icon: FileCode },
  { id: 'MVP_BUILD_AND_TEST', name: 'Build & Test Validation', icon: Hammer },
  { id: 'MVP_SELF_HEAL_LOOP', name: 'Self-Healing Repair', icon: ShieldAlert },
  { id: 'MVP_DEPLOY_PREVIEW', name: 'Deploy Live Preview', icon: Globe },
  { id: 'SCREENSHOT_CAPTURE', name: 'Screenshot Capture', icon: Camera },
  { id: 'DECK_GENERATION', name: 'Pitch Deck Generation', icon: Presentation },
  { id: 'NARRATION_GENERATION', name: 'Pitch Narration (TTS)', icon: Mic },
];

interface RunStepperProps {
  stages: StageEvent[];
  selectedStage: string;
  setSelectedStage: (stage: string) => void;
  currentStage: string;
}

export default function RunStepper({ stages, selectedStage, setSelectedStage, currentStage }: RunStepperProps) {
  const getStageStatus = (stageId: string) => {
    const found = stages.find(s => s.stage === stageId);
    if (found) return found.status;
    if (currentStage === stageId) return 'running';
    return 'pending';
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-5 shadow-2xl flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div>
          <h3 className="font-extrabold text-sm text-white">Pipeline Execution Stepper</h3>
          <p className="text-xs text-slate-400 font-mono">15 Specialized Agent Stages</p>
        </div>
        <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 px-2.5 py-1 rounded-full border border-cyan-800">
          State Machine Active
        </span>
      </div>

      <div className="space-y-1.5 overflow-y-auto pr-1 flex-1">
        {STAGES_META.map((meta, index) => {
          const status = getStageStatus(meta.id);
          const isSelected = selectedStage === meta.id;
          const Icon = meta.icon;

          return (
            <button
              key={meta.id}
              onClick={() => setSelectedStage(meta.id)}
              className={`w-full text-left flex items-center justify-between p-3 rounded-2xl transition-all duration-200 ${
                isSelected
                  ? 'bg-cyan-500/10 border border-cyan-500/40 text-cyan-200'
                  : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className="text-[10px] font-mono text-slate-500 w-4">
                  {(index + 1).toString().padStart(2, '0')}
                </div>
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4 text-slate-400" />
                  <span className="text-xs font-semibold text-white tracking-tight">{meta.name}</span>
                </div>
              </div>

              <div>
                {status === 'succeeded' && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 animate-in zoom-in-50" />
                )}
                {status === 'running' && (
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                )}
                {status === 'failed' && (
                  <XCircle className="w-4 h-4 text-rose-500" />
                )}
                {status === 'pending' && (
                  <Circle className="w-3.5 h-3.5 text-slate-700" />
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
