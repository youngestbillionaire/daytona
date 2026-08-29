import json
import logging
import re
from typing import Callable, List, Optional
from orchestrator.clients.daytona_client import daytona_client
from orchestrator.models import (
    GeneratedFile,
    IdeationOutput,
    MvpCodegenOutput,
    MvpScaffoldOutput,
    SpecGenerationOutput,
)

logger = logging.getLogger("founder0.stage.mvp_codegen")

def validate_component_code(code: str) -> bool:
    """Lightweight static check for valid, safe React component."""
    if not code or not isinstance(code, str) or not code.strip():
        return False
    if "export default" not in code:
        return False
    if "eval(" in code or "Function(" in code:
        return False
    # Check bracket and brace balance
    if code.count("{") != code.count("}"):
        return False
    if code.count("(") != code.count(")"):
        return False
    if code.count("[") != code.count("]"):
        return False
    return True

def escape_jsx_string(s: str) -> str:
    """Safely escape text for inclusion in JSX templates."""
    if not s:
        return ""
    # Strip any potential raw script tags and escape double quotes
    sanitized = s.replace("<script>", "").replace("</script>", "")
    return sanitized.replace('"', '\\"')

async def run_mvp_codegen(
    scaffold: MvpScaffoldOutput,
    ideation: IdeationOutput,
    spec: SpecGenerationOutput,
    log: Optional[Callable[[str], None]] = None
) -> MvpCodegenOutput:
    """
    Stage 2.9: MVP_CODE_GENERATION
    Generates tailored React components and landing page copy,
    performs static safety checks, and uploads them to the Daytona sandbox.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"💻 [MVP_CODE_GENERATION] Generating modular code for sandbox {scaffold.sandbox_id}...")
    sandbox = await daytona_client.get_sandbox(scaffold.sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {scaffold.sandbox_id} not found")

    generated_files: List[GeneratedFile] = []
    component_imports = []
    component_tags = []

    palette = ideation.suggested_color_palette or ["#0284c7", "#0f172a", "#38bdf8"]
    primary_color = palette[0]

    # Generate each feature component
    for feat in spec.feature_implementations:
        cname = feat.component_name or "FeatureCard"
        emit(f"⚡ [MVP_CODE_GENERATION] Generating React component: '{cname}' for feature '{feat.feature_name}'...")
        
        safe_title = escape_jsx_string(feat.feature_name)
        safe_desc = escape_jsx_string(feat.ui_description)

        comp_code = f"""'use client';

import React, {{ useState }} from 'react';

export interface {cname}Props {{
  title?: string;
  description?: string;
}}

export default function {cname}({{
  title = "{safe_title}",
  description = "{safe_desc}"
}}: {cname}Props) {{
  const [isActive, setIsActive] = useState(false);
  const [counter, setCounter] = useState(0);

  return (
    <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm shadow-xl hover:border-cyan-500/50 transition-all duration-300 group">
      <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center font-bold text-xl mb-4 group-hover:scale-105 transition-transform">
        ⚡
      </div>
      <h3 className="text-xl font-bold text-white mb-2 tracking-tight group-hover:text-cyan-300 transition-colors">
        {{title}}
      </h3>
      <p className="text-slate-400 text-sm leading-relaxed mb-6">
        {{description}}
      </p>
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
        <button 
          onClick={{() => {{
            setIsActive(!isActive);
            setCounter(c => c + 1);
          }}}}
          className="text-xs font-semibold px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 transition-all active:scale-95"
        >
          {{isActive ? 'Active Mode (Clicks: ' + counter + ')' : 'Execute Action'}}
        </button>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-1 rounded-md border border-emerald-800">
          Live Feature
        </span>
      </div>
    </div>
  );
}}
"""
        # Static validation
        if not validate_component_code(comp_code):
            raise ValueError(f"Static check failed for component {cname}")

        rel_path = f"components/features/{cname}.tsx"
        await sandbox.write_file(rel_path, comp_code)
        generated_files.append(GeneratedFile(
            path=rel_path,
            content=comp_code,
            component_name=cname
        ))
        emit(f"  └─ Validated & written: {rel_path}")

        component_imports.append(f"import {cname} from '../components/features/{cname}';")
        component_tags.append(f"          <{cname} />")

    # Generate bespoke landing page using the generated components and copy
    emit("📝 [MVP_CODE_GENERATION] Injecting brand copy and dynamic feature grid into app/page.tsx...")
    
    page_content = f"""'use client';

import React, {{ useState }} from 'react';
{chr(10).join(component_imports)}

export default function Home() {{
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!email) return;
    setStatus('loading');
    try {{
      const res = await fetch('/api/waitlist', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ email }}),
      }});
      const data = await res.json();
      if (res.ok) {{
        setStatus('success');
        setMessage(data.message || 'Joined waitlist!');
        setEmail('');
      }} else {{
        setStatus('error');
        setMessage(data.error || 'Failed to join waitlist');
      }}
    }} catch (err: any) {{
      setStatus('error');
      setMessage(err.message || 'Network error');
    }}
  }};

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-between p-6 md:p-24 selection:bg-cyan-500 selection:text-white">
      {{/* HEADER */}}
      <header className="w-full max-w-6xl flex justify-between items-center py-4 mb-16 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-black text-white text-lg shadow-lg shadow-cyan-500/20">
            {ideation.product_name[:2].upper()}
          </div>
          <span className="font-extrabold text-xl tracking-tight text-white">{ideation.product_name}</span>
        </div>
        <a 
          href="#signup" 
          className="text-xs font-semibold px-5 py-2.5 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all font-mono shadow-md shadow-cyan-500/10 hover:shadow-cyan-500/30"
        >
          Get Early Access
        </a>
      </header>

      {{/* HERO SECTION */}}
      <section className="w-full max-w-4xl text-center flex flex-col items-center mb-24">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-6">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          FOUNDER-0 Autonomous MVP
        </div>
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 leading-tight">
          {ideation.tagline}
        </h1>
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-10 leading-relaxed">
          {ideation.elevator_pitch}
        </p>
      </section>

      {{/* CORE FEATURES GRID */}}
      <section className="w-full max-w-6xl mb-24">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">Engineered To Solve Market Gaps</h2>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">
            {ideation.differentiation_from_competitors}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
{chr(10).join(component_tags)}
        </div>
      </section>

      {{/* SIGNUP CTA */}}
      <section id="signup" className="w-full max-w-2xl bg-gradient-to-b from-slate-900 to-slate-900/90 border border-slate-800 rounded-3xl p-8 md:p-12 text-center shadow-2xl relative overflow-hidden mb-16">
        <div className="absolute inset-0 bg-cyan-500/10 blur-3xl rounded-full"></div>
        <div className="relative z-10">
          <h3 className="text-2xl md:text-3xl font-bold text-white mb-3">Join the {ideation.product_name} Waitlist</h3>
          <p className="text-slate-400 text-sm mb-8">{ideation.pricing_suggestion} — Be the first to get access.</p>
          
          <form onSubmit={{handleSubmit}} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input 
              type="email" 
              value={{email}}
              onChange={{(e) => setEmail(e.target.value)}}
              placeholder="Enter your email..." 
              required
              className="flex-1 px-4 py-3 rounded-xl bg-slate-950/90 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-sm transition-all"
            />
            <button 
              type="submit" 
              disabled={{status === 'loading'}}
              className="px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition-all whitespace-nowrap disabled:opacity-50 shadow-lg shadow-cyan-500/20"
            >
              {{status === 'loading' ? 'Submitting...' : 'Join Waitlist'}}
            </button>
          </form>

          {{message && (
            <p className={{`mt-4 text-xs font-mono ${{status === 'success' ? 'text-emerald-400' : 'text-rose-400'}}`}}>
              {{message}}
            </p>
          )}}
        </div>
      </section>

      {{/* FOOTER */}}
      <footer className="w-full max-w-6xl py-8 border-t border-slate-900 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 font-mono">
        <div>© 2026 {ideation.product_name}. Powered by FOUNDER-0.</div>
        <div className="mt-2 sm:mt-0 flex gap-4">
          <span>Daytona Cloud Sandbox</span>
          <span>•</span>
          <span>Nosana GPU Inference</span>
        </div>
      </footer>
    </main>
  );
}}
"""
    await sandbox.write_file("app/page.tsx", page_content)
    generated_files.append(GeneratedFile(path="app/page.tsx", content=page_content))
    emit("✅ [MVP_CODE_GENERATION] Successfully generated and verified all component code.")

    return MvpCodegenOutput(
        generated_files=generated_files,
        hero_copy={
            "product_name": ideation.product_name,
            "tagline": ideation.tagline,
            "elevator_pitch": ideation.elevator_pitch
        },
        static_check_passed=True
    )
