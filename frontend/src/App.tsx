import React, { useState, useEffect } from 'react';
import { Sparkles, ArrowRight, Play, RefreshCw, Cpu, Layers } from 'lucide-react';
import Navbar from './components/Navbar';
import RunStepper from './components/RunStepper';
import TerminalLogs from './components/TerminalLogs';
import KnowledgeGraph from './components/KnowledgeGraph';
import LiveMVPPreview from './components/LiveMVPPreview';
import PitchDeckViewer from './components/PitchDeckViewer';
import RunHistory from './components/RunHistory';
import { Run, StageEvent, GraphData } from './types';

const SAMPLE_IDEAS = [
  "an app for splitting bills with roommates who hate each other",
  "ai automated bookkeeping and schedule C deductions for solo freelancers",
  "a local board game meetup app that locks an attendance bond to prevent ghosting",
  "a circadian rhythm and caffeine cutoff coach that adapts to shift workers",
  "an automated safe postgres schema migration linter with table lock simulation"
];

export default function App() {
  const [currentTab, setCurrentTab] = useState<'launch' | 'live' | 'history'>('launch');
  const [ideaInput, setIdeaInput] = useState('');
  const [isLaunching, setIsLaunching] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const [stages, setStages] = useState<StageEvent[]>([]);
  const [selectedStage, setSelectedStage] = useState<string>('IDEA_RECEIVED');
  const [liveLogs, setLiveLogs] = useState<string[]>([]);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [], node_count: 0, edge_count: 0 });
  const [runsList, setRunsList] = useState<Run[]>([]);

  // Fetch runs list periodically or on mount
  const fetchRuns = async () => {
    try {
      const res = await fetch('/api/runs');
      if (res.ok) {
        const data = await res.json();
        setRunsList(data);
      }
    } catch (e) {
      console.error("Error fetching runs:", e);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 8000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket connection for active run
  useEffect(() => {
    if (!activeRunId) return;

    // Fetch initial timeline
    fetch(`/api/runs/${activeRunId}/timeline`)
      .then(res => res.json())
      .then(data => {
        if (data.stages) setStages(data.stages);
      })
      .catch(console.error);

    // Fetch run details
    fetch(`/api/runs/${activeRunId}`)
      .then(res => res.json())
      .then(data => setActiveRun(data))
      .catch(console.error);

    // Fetch graph
    fetch(`/api/runs/${activeRunId}/graph`)
      .then(res => res.json())
      .then(data => {
        if (data.nodes) setGraphData(data);
      })
      .catch(console.error);

    // Connect WS
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/runs/${activeRunId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { event: eventType, data } = msg;

        if (eventType === 'log') {
          setLiveLogs(prev => [...prev, data.log]);
        } else if (eventType === 'stage_transition') {
          setSelectedStage(data.stage);
          // Refetch timeline
          fetch(`/api/runs/${activeRunId}/timeline`)
            .then(res => res.json())
            .then(tData => {
              if (tData.stages) setStages(tData.stages);
            });
          // Refetch run details too, so fields like product_name (set as soon as
          // the IDEATION stage finishes) show up immediately instead of being
          // stuck on "Synthesizing Concept..." until the whole run completes.
          fetch(`/api/runs/${activeRunId}`)
            .then(res => res.json())
            .then(rData => setActiveRun(rData))
            .catch(console.error);
        } else if (eventType === 'graph_update') {
          setGraphData(data);
        } else if (eventType === 'run_completed' || eventType === 'run_failed') {
          fetch(`/api/runs/${activeRunId}`)
            .then(res => res.json())
            .then(rData => setActiveRun(rData));
          fetchRuns();
        }
      } catch (err) {
        console.error("WS Parse error:", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [activeRunId]);

  const handleLaunch = async (ideaToLaunch?: string) => {
    const idea = ideaToLaunch || ideaInput;
    if (!idea.trim()) return;

    setIsLaunching(true);
    try {
      const res = await fetch('/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea: idea.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveRunId(data.id);
        setActiveRun(data);
        setLiveLogs([]);
        setStages([]);
        setGraphData({ nodes: [], edges: [], node_count: 0, edge_count: 0 });
        setCurrentTab('live');
        fetchRuns();
      }
    } catch (err) {
      console.error("Failed to launch run:", err);
    } finally {
      setIsLaunching(false);
    }
  };

  const handleReplay = async (runId: string) => {
    try {
      const res = await fetch(`/api/runs/${runId}/replay`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setActiveRunId(data.id);
        setActiveRun(data);
        setLiveLogs([]);
        setStages([]);
        setGraphData({ nodes: [], edges: [], node_count: 0, edge_count: 0 });
        setCurrentTab('live');
        fetchRuns();
      }
    } catch (err) {
      console.error("Failed to replay:", err);
    }
  };

  const handleSelectRun = (runId: string) => {
    setActiveRunId(runId);
    setCurrentTab('live');
  };

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        activeRunId={activeRunId || undefined}
      />

      <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full">
        {/* VIEW 1: LAUNCH NEW VENTURE */}
        {currentTab === 'launch' && (
          <div className="max-w-4xl mx-auto py-12 flex flex-col items-center text-center">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-8 animate-in fade-in zoom-in-95">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              Autonomous Venture Creation Engine
            </div>

            <h1 className="text-5xl md:text-7xl font-black text-white tracking-tight mb-6 leading-tight">
              One Sentence.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">
                A Shipped Startup.
              </span>
            </h1>

            <p className="text-base md:text-lg text-slate-400 max-w-2xl mb-12 leading-relaxed">
              FOUNDER-0 automates competitive recon, knowledge graph synthesis, Daytona sandbox MVP scaffolding, self-healing code generation, and pitch decks without human intervention.
            </p>

            {/* Input Card */}
            <div className="w-full bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 md:p-8 shadow-2xl relative mb-12">
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={ideaInput}
                  onChange={(e) => setIdeaInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleLaunch()}
                  placeholder="Enter your one-sentence startup idea..."
                  className="flex-1 px-5 py-4 rounded-2xl bg-slate-950/90 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 transition-all font-medium"
                />
                <button
                  onClick={() => handleLaunch()}
                  disabled={isLaunching || !ideaInput.trim()}
                  className="flex items-center justify-center space-x-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 active:scale-95"
                >
                  <Sparkles className="w-4 h-4 text-slate-950" />
                  <span>{isLaunching ? 'Synthesizing...' : 'Launch Pipeline'}</span>
                </button>
              </div>

              {/* Sample Prompts */}
              <div className="mt-6 pt-6 border-t border-slate-800/80 text-left">
                <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-3">
                  Or select a verified benchmark prompt:
                </div>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_IDEAS.map((sample, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setIdeaInput(sample);
                        handleLaunch(sample);
                      }}
                      className="text-xs px-3 py-1.5 rounded-xl bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-300 transition-all text-left truncate max-w-md"
                    >
                      ⚡ {sample}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Stats Banner */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full text-center">
              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                <div className="text-xl font-bold text-cyan-400 font-mono">15</div>
                <div className="text-xs text-slate-400 font-mono">Autonomous Stages</div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                <div className="text-xl font-bold text-white font-mono">Daytona</div>
                <div className="text-xs text-slate-400 font-mono">Cloud Sandbox Stack</div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                <div className="text-xl font-bold text-emerald-400 font-mono">Neo4j</div>
                <div className="text-xs text-slate-400 font-mono">Opportunity Graph</div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800">
                <div className="text-xl font-bold text-purple-400 font-mono">Nosana</div>
                <div className="text-xs text-slate-400 font-mono">GPU LLM Inference</div>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 2: LIVE RUN DETAIL */}
        {currentTab === 'live' && activeRun && (
          <div className="space-y-6">
            {/* Header Card */}
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-3xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-3">
                  <span className="text-xs font-mono text-yellow-400 bg-yellow-950/40 px-2.5 py-0.5 rounded-full border border-yellow-800/50">
                    {activeRun.id}
                  </span>
                  <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-full ${
                    activeRun.status === 'completed'
                      ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                      : activeRun.status === 'failed'
                      ? 'bg-rose-950/60 text-rose-400 border border-rose-800'
                      : 'bg-cyan-950/60 text-cyan-400 border border-cyan-800 animate-pulse'
                  }`}>
                    {activeRun.status.toUpperCase()}
                  </span>
                </div>
                <h2 className="text-2xl font-black text-white">
                  {activeRun.product_name || 'Synthesizing Concept...'}
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Prompt: "{activeRun.idea}"
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => handleReplay(activeRun.id)}
                  className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Replay Run</span>
                </button>
              </div>
            </div>

            {/* Grid Layout: Stepper + Graph + Logs */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Stepper (Left col) */}
              <div className="lg:col-span-4 h-[680px]">
                <RunStepper
                  stages={stages}
                  selectedStage={selectedStage}
                  setSelectedStage={setSelectedStage}
                  currentStage={activeRun.current_stage}
                />
              </div>

              {/* Right area: Graph + Logs */}
              <div className="lg:col-span-8 flex flex-col space-y-6">
                <div className="h-[340px]">
                  <KnowledgeGraph graphData={graphData} />
                </div>
                <div className="flex-1">
                  <TerminalLogs
                    stages={stages}
                    selectedStage={selectedStage}
                    liveLogs={liveLogs}
                  />
                </div>
              </div>
            </div>

            {/* Bottom Deliverables Section: Live MVP Preview & Deck Viewer */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-4">
              <LiveMVPPreview
                previewUrl={activeRun.preview_url}
                productName={activeRun.product_name}
              />
              <PitchDeckViewer
                deckUrl={activeRun.deck_path}
                productName={activeRun.product_name}
                narrationScript={activeRun.narration_path}
              />
            </div>
          </div>
        )}

        {/* VIEW 3: RUN HISTORY */}
        {currentTab === 'history' && (
          <RunHistory
            runs={runsList}
            onSelectRun={handleSelectRun}
            onReplayRun={handleReplay}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-600 font-mono">
        FOUNDER-0 Autonomous Venture Engine • Built for Autonomous AI Hackathons
      </footer>
    </div>
  );
}
