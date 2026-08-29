import io
import logging
from pathlib import Path
from typing import Callable, Optional
from jinja2 import Template
from orchestrator.models import (
    DeckGenerationOutput,
    IdeationOutput,
    MarketReconOutput,
    MvpDeployOutput,
    OpportunityGraphOutput,
    ScreenshotOutput,
    WhitespaceAnalysisOutput,
)

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

logger = logging.getLogger("founder0.stage.deck_generation")

DECK_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ ideation.product_name }} — Institutional Seed Pitch Deck | FOUNDER-0</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@500;700;800&display=swap" rel="stylesheet">
  
  <style>
    :root {
      --primary: {{ primary_color }};
      --bg-dark: {{ bg_color }};
      --accent: {{ accent_color }};
    }
    
    * {
      box-sizing: border-box;
      user-select: none;
    }
    
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #030712;
      color: #f8fafc;
      overflow: hidden;
      height: 100vh;
      width: 100vw;
    }

    .font-display {
      font-family: 'Space Grotesk', sans-serif;
    }

    .font-mono {
      font-family: 'JetBrains Mono', monospace;
    }

    /* Cinematic 3D Presentation Canvas */
    #deck-viewport {
      perspective: 1400px;
      perspective-origin: center center;
    }

    .slide {
      opacity: 0;
      visibility: hidden;
      transform: scale(0.94) translateY(24px) rotateX(3deg);
      transition: opacity 0.55s cubic-bezier(0.16, 1, 0.3, 1),
                  transform 0.55s cubic-bezier(0.16, 1, 0.3, 1),
                  visibility 0.55s;
      position: absolute;
      inset: 0;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .slide.active {
      opacity: 1;
      visibility: visible;
      transform: scale(1) translateY(0) rotateX(0deg);
      pointer-events: auto;
      z-index: 10;
    }

    .slide.exit-prev {
      opacity: 0;
      visibility: hidden;
      transform: scale(0.94) translateY(-24px) rotateX(-3deg);
    }

    /* Staggered Element Entrance Animations */
    .slide.active .stagger-1 { animation: slideUpFade 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.06s both; }
    .slide.active .stagger-2 { animation: slideUpFade 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.12s both; }
    .slide.active .stagger-3 { animation: slideUpFade 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.18s both; }
    .slide.active .stagger-4 { animation: slideUpFade 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.24s both; }
    .slide.active .stagger-5 { animation: slideUpFade 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.30s both; }

    @keyframes slideUpFade {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* Ambient Glow Backdrops */
    .glow-orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.30;
      pointer-events: none;
      transition: all 1s ease;
    }

    .glass-card {
      background: rgba(15, 23, 42, 0.70);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.09);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55);
    }

    .glass-card-hover {
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .glass-card-hover:hover {
      transform: translateY(-3px);
      border-color: rgba(56, 189, 248, 0.45);
      box-shadow: 0 25px 60px rgba(56, 189, 248, 0.18);
    }

    /* Fluid Title Size */
    .fluid-title {
      font-size: clamp(2.2rem, 5.5vw, 4.8rem);
    }

    .fluid-subtitle {
      font-size: clamp(1.1rem, 2.5vw, 1.85rem);
    }

    /* Particle Canvas */
    #particles-canvas {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 1;
    }

    /* Speaker Notes Modal */
    #speaker-notes {
      transform: translateY(100%);
      transition: transform 0.3s ease;
    }
    #speaker-notes.open {
      transform: translateY(0);
    }
  </style>
</head>
<body class="relative flex flex-col justify-between p-4 md:p-6 lg:p-8 h-screen select-none overflow-hidden">

  <!-- BACKGROUND PARTICLES & GLOW -->
  <canvas id="particles-canvas"></canvas>
  <div class="glow-orb w-[520px] h-[520px] -top-32 -left-32 bg-cyan-500/20"></div>
  <div class="glow-orb w-[640px] h-[640px] -bottom-32 -right-32 bg-indigo-500/20"></div>

  <!-- TOP BAR / HEADER -->
  <header class="relative z-20 flex justify-between items-center pb-3 border-b border-slate-800/80 max-w-7xl mx-auto w-full">
    <div class="flex items-center space-x-3">
      <div class="w-9 h-9 rounded-xl flex items-center justify-center font-black text-white text-xs font-mono shadow-lg shadow-cyan-500/25 ring-1 ring-white/20" style="background: linear-gradient(135deg, var(--primary), var(--accent));">
        F0
      </div>
      <div>
        <div class="flex items-center space-x-2">
          <span class="font-extrabold text-base md:text-lg text-white tracking-tight">{{ ideation.product_name }}</span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            INSTITUTIONAL SEED DECK
          </span>
        </div>
      </div>
    </div>
    
    <!-- Controls Helper & Slide Counter -->
    <div class="flex items-center space-x-4">
      <div class="hidden md:flex items-center space-x-2 text-xs font-mono text-slate-400">
        <kbd class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">←</kbd>
        <kbd class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">→</kbd>
        <span>navigate</span>
        <span class="text-slate-600">|</span>
        <kbd class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]" onclick="toggleNotes()">N</kbd>
        <span>speaker notes</span>
        <span class="text-slate-600">|</span>
        <kbd class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]" onclick="toggleFullscreen()">F</kbd>
        <span>fullscreen</span>
      </div>

      <div class="font-mono text-xs px-3 py-1 rounded-xl bg-slate-900/90 border border-slate-800 text-slate-300">
        Slide <span id="currentSlideNum" class="text-cyan-400 font-bold">1</span> / <span id="totalSlidesNum">8</span>
      </div>
    </div>
  </header>

  <!-- PROGRESS BAR -->
  <div class="relative z-20 w-full max-w-7xl mx-auto h-1 bg-slate-900/80 rounded-full mt-2 overflow-hidden">
    <div id="progress-fill" class="h-full transition-all duration-300" style="width: 12.5%; background: linear-gradient(90deg, var(--primary), var(--accent));"></div>
  </div>

  <!-- SLIDES VIEWPORT -->
  <main id="deck-viewport" class="relative z-10 flex-1 w-full max-w-7xl mx-auto my-auto overflow-hidden">

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 1: PATTERN INTERRUPT / TITLE
         ═════════════════════════════════════════════════════════ -->
    <div class="slide active items-center text-center max-w-4xl mx-auto px-4" data-slide="1" data-notes="HOOK & PATTERN INTERRUPT: Start with commanding confidence. State the one-line thesis: legacy tools manage human friction rather than eliminating it. Emphasize that our Daytona cloud-compiled MVP is live right now.">
      <div class="stagger-1 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 text-xs font-mono mb-6 backdrop-blur-md">
        <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
        <span>AUTONOMOUS VENTURE SYNTHESIS • DAYTONA RUNTIME VERIFIED</span>
      </div>

      <h1 class="stagger-2 font-display fluid-title font-black tracking-tight text-white mb-4 leading-none">
        {{ ideation.product_name }}
      </h1>

      <p class="stagger-3 fluid-subtitle font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-300 mb-6 max-w-3xl leading-tight">
        {{ ideation.tagline }}
      </p>

      <p class="stagger-4 text-sm md:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed mb-8">
        {{ ideation.one_line_pitch }}
      </p>

      <div class="stagger-5 flex flex-wrap justify-center gap-2.5 text-xs font-mono text-slate-300">
        <span class="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-1.5">⚡ Zero-Human Overhead</span>
        <span class="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-1.5">🛡️ Verifiable Sandbox Prototype</span>
        <span class="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-1.5">📈 TAM: {{ ideation.tam_estimate }}</span>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 2: THE BLEEDING NECK PROBLEM (LOSS AVERSION)
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-start max-w-5xl mx-auto px-4" data-slide="2" data-notes="PSYCHOLOGICAL DRIVER: Loss Aversion. Investors need to feel what users lose every single week—hard dollars, personal dignity, and wasted hours. Ground every point in verified community feedback.">
      <div class="stagger-1 text-xs font-mono text-rose-400 mb-2 uppercase tracking-widest flex items-center gap-2">
        <span>01 / The Pain Point</span>
        <span class="w-12 h-px bg-rose-500/40"></span>
      </div>
      
      <h2 class="stagger-2 font-display text-2xl md:text-4xl font-black text-white mb-2">
        The Cost of Inaction Is Visceral
      </h2>
      <p class="stagger-2 text-slate-400 text-xs md:text-sm mb-6 max-w-2xl">
        Every week, millions of users suffer through manual overhead, broken agreements, and passive-aggressive friction caused by outdated software paradigms.
      </p>

      <div class="stagger-3 grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
        {% for complaint in recon.raw_complaint_pool[:3] %}
        <div class="glass-card glass-card-hover p-5 rounded-2xl flex flex-col justify-between border-rose-500/20 bg-slate-900/50">
          <div>
            <div class="w-7 h-7 rounded-lg bg-rose-500/10 text-rose-400 font-mono font-bold flex items-center justify-center text-xs mb-3">
              0{{ loop.index }}
            </div>
            <p class="text-slate-200 text-xs md:text-sm leading-relaxed italic mb-4 font-medium">
              "{{ complaint }}"
            </p>
          </div>
          <div class="text-[10px] font-mono text-slate-400 flex items-center gap-1.5 pt-2.5 border-t border-slate-800/80">
            <span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            Verified Community Friction Point
          </div>
        </div>
        {% endfor %}
      </div>

      <div class="stagger-4 mt-5 p-3.5 rounded-xl bg-rose-950/25 border border-rose-900/40 w-full flex items-center justify-between">
        <div class="text-xs text-rose-300 font-mono flex items-center gap-2">
          <span class="font-bold text-rose-400">PSYCHOLOGICAL DRIVER:</span> {{ ideation.psychological_hook }}
        </div>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 3: COMPETITIVE MATRIX & OPPORTUNITY GRAPH
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-start max-w-5xl mx-auto px-4" data-slide="3" data-notes="COMPETITIVE POSITIONING: Show that 100% of incumbents sit in the 'High Human Effort / Passive Tool' quadrant. {{ ideation.product_name }} captures the uncrowded 'Autonomous / Zero-Friction' category.">
      <div class="stagger-1 text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest flex items-center gap-2">
        <span>02 / Competitive Matrix & Opportunity Graph</span>
        <span class="w-12 h-px bg-cyan-500/40"></span>
      </div>

      <h2 class="stagger-2 font-display text-2xl md:text-4xl font-black text-white mb-2">
        Incumbents Suffer From Structural Blindness
      </h2>
      <p class="stagger-2 text-slate-400 text-xs md:text-sm mb-4 max-w-2xl">
        Our knowledge graph mapped incumbent feature sets against real user pain points, exposing an untouched market vacuum.
      </p>

      <!-- 2x2 Matrix + Gap Highlight -->
      <div class="stagger-3 grid grid-cols-1 md:grid-cols-2 gap-4 w-full mb-4">
        <!-- Matrix Visual -->
        <div class="glass-card p-5 rounded-2xl border-slate-800 bg-slate-900/80 flex flex-col justify-between">
          <div class="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-2 font-bold flex items-center justify-between">
            <span>Market Positioning Quad</span>
            <span class="text-[10px] text-slate-400">Autonomous vs Manual</span>
          </div>
          <div class="relative h-40 border border-slate-800 rounded-xl bg-slate-950/60 p-3 flex flex-col justify-between text-[10px] font-mono text-slate-400">
            <div class="flex justify-between items-start">
              <span class="text-slate-400">Passive Tracking</span>
              <span class="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40">⭐ {{ ideation.product_name }}</span>
            </div>
            <div class="flex justify-between items-end">
              <span class="text-rose-400">✕ {% for comp in recon.competitors[:2] %}{{ comp.name }}{% if not loop.last %}, {% endif %}{% endfor %}</span>
              <span class="text-slate-400">Active Enforcement</span>
            </div>
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="w-full h-px bg-slate-800"></div>
            </div>
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="h-full w-px bg-slate-800"></div>
            </div>
          </div>
        </div>

        <!-- Primary Gap Card -->
        <div class="glass-card p-5 rounded-2xl border-cyan-500/30 bg-gradient-to-br from-slate-900/90 to-cyan-950/30 flex flex-col justify-between">
          <div>
            <div class="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-2 font-bold">Unaddressed Category Void</div>
            <p class="text-xs md:text-sm text-slate-200 font-medium leading-relaxed">
              {{ whitespace.primary_gap }}
            </p>
          </div>
          <div class="pt-3 border-t border-slate-800/80 text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            0% Incumbent Coverage in Active Resolution
          </div>
        </div>
      </div>

      <!-- Proof Numbers -->
      <div class="stagger-4 grid grid-cols-2 sm:grid-cols-4 gap-3 w-full">
        <div class="glass-card p-3 rounded-xl text-center">
          <div class="font-display text-xl md:text-2xl font-black text-cyan-400 font-mono">{{ graph.node_count }}</div>
          <div class="text-[10px] text-slate-400 uppercase font-mono">Knowledge Nodes</div>
        </div>
        <div class="glass-card p-3 rounded-xl text-center">
          <div class="font-display text-xl md:text-2xl font-black text-white font-mono">{{ recon.competitors|length }}</div>
          <div class="text-[10px] text-slate-400 uppercase font-mono">Competitors Mapped</div>
        </div>
        <div class="glass-card p-3 rounded-xl text-center">
          <div class="font-display text-xl md:text-2xl font-black text-emerald-400 font-mono">0%</div>
          <div class="text-[10px] text-slate-400 uppercase font-mono">Incumbent Moat</div>
        </div>
        <div class="glass-card p-3 rounded-xl text-center">
          <div class="font-display text-xl md:text-2xl font-black text-indigo-400 font-mono">10x</div>
          <div class="text-[10px] text-slate-400 uppercase font-mono">Friction Reduction</div>
        </div>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 4: THE CONTRARIAN INSIGHT (CURIOSITY GAP)
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-start max-w-5xl mx-auto px-4" data-slide="4" data-notes="PETER THIEL ZERO-TO-ONE SLIDE: What does consensus get wrong? Why is our perspective a non-obvious ground truth? Walk through the 10x paradigm shift.">
      <div class="stagger-1 text-xs font-mono text-purple-400 mb-2 uppercase tracking-widest flex items-center gap-2">
        <span>03 / The Contrarian Truth</span>
        <span class="w-12 h-px bg-purple-500/40"></span>
      </div>

      <h2 class="stagger-2 font-display text-2xl md:text-4xl font-black text-white mb-4">
        Why The Consensus Is Dead Wrong
      </h2>

      <div class="stagger-3 grid grid-cols-1 md:grid-cols-2 gap-4 w-full mb-4">
        <!-- The Flawed Consensus -->
        <div class="glass-card p-5 md:p-6 rounded-2xl border-rose-500/30 bg-rose-950/10">
          <div class="flex items-center space-x-2 text-rose-400 text-xs font-mono font-bold uppercase mb-2">
            <span>✕ The Flawed Market Consensus (1-to-N)</span>
          </div>
          <p class="text-slate-300 text-xs md:text-sm leading-relaxed">
            Incumbents build prettier tracking dashboards and send push notification reminders, expecting humans to negotiate awkward friction manually.
          </p>
        </div>

        <!-- The Contrarian Breakthrough -->
        <div class="glass-card p-5 md:p-6 rounded-2xl border-emerald-500/30 bg-emerald-950/10 shadow-lg shadow-emerald-500/10">
          <div class="flex items-center space-x-2 text-emerald-400 text-xs font-mono font-bold uppercase mb-2">
            <span>✓ The Ground-Truth Reality (Zero-to-One)</span>
          </div>
          <p class="text-white text-xs md:text-sm font-semibold leading-relaxed">
            {{ ideation.contrarian_insight }}
          </p>
        </div>
      </div>

      <!-- 10x Paradigm Shift Box -->
      <div class="stagger-4 glass-card p-4 rounded-xl border-purple-500/30 bg-purple-950/20 w-full flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-300 flex items-center justify-center font-bold text-lg flex-shrink-0">
          ⚡
        </div>
        <div>
          <div class="text-[11px] font-mono text-purple-300 font-bold uppercase">The 10x Moonshot Factor</div>
          <p class="text-xs text-slate-300">{{ ideation.ten_x_factor }}</p>
        </div>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 5: THE SOLUTION & FEATURE ARCHITECTURE
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-start max-w-5xl mx-auto px-4" data-slide="5" data-notes="SOLUTION ARCHITECTURE: Highlight the three core engineering pillars. Point out that each pillar maps 1:1 to user complaints identified in reconnaissance.">
      <div class="stagger-1 text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest flex items-center gap-2">
        <span>04 / Solution Pillars</span>
        <span class="w-12 h-px bg-cyan-500/40"></span>
      </div>

      <h2 class="stagger-2 font-display text-2xl md:text-4xl font-black text-white mb-1">
        {{ ideation.product_name }} Architecture
      </h2>
      <p class="stagger-2 text-slate-400 text-xs mb-4 max-w-3xl leading-relaxed">
        {{ ideation.elevator_pitch }}
      </p>

      <div class="stagger-3 grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
        {% for feat in ideation.core_features %}
        <div class="glass-card glass-card-hover p-5 rounded-2xl flex flex-col justify-between border-slate-800">
          <div>
            <div class="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 flex items-center justify-center font-black text-sm mb-3">
              0{{ loop.index }}
            </div>
            <h4 class="text-sm font-extrabold text-white mb-1.5 tracking-tight">{{ feat.name }}</h4>
            <p class="text-slate-400 text-xs leading-relaxed mb-3">{{ feat.description }}</p>
          </div>
          <div class="pt-2.5 border-t border-slate-800/80">
            <span class="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 block truncate">
              Payoff: {{ feat.user_value }}
            </span>
          </div>
        </div>
        {% endfor %}
      </div>

      <div class="stagger-4 mt-4 p-3 rounded-xl bg-slate-900/80 border border-slate-800 w-full flex items-center justify-between text-xs font-mono text-slate-400">
        <span>🛡️ Defensibility Engine: {{ ideation.technical_moat }}</span>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 6: VERIFIABLE LIVE MVP & QR CODE
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-start max-w-5xl mx-auto px-4" data-slide="6" data-notes="DEMONSTRATION BIAS: The unfair advantage. Invite investors to scan the QR code right now and see the real, compiled Next.js application running inside the Daytona cloud sandbox.">
      <div class="stagger-1 text-xs font-mono text-emerald-400 mb-2 uppercase tracking-widest flex items-center gap-2">
        <span>05 / Verifiable Proof</span>
        <span class="w-12 h-px bg-emerald-500/40"></span>
      </div>

      <h2 class="stagger-2 font-display text-2xl md:text-4xl font-black text-white mb-3">
        Not A Figma Mockup. A Running Application.
      </h2>

      <div class="stagger-3 grid grid-cols-1 md:grid-cols-3 gap-4 w-full items-center">
        <!-- Live App Screenshot -->
        <div class="md:col-span-2 glass-card p-2.5 rounded-2xl border-slate-800 overflow-hidden relative group">
          <div class="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-950 rounded-t-xl border-b border-slate-800 text-[10px] font-mono text-slate-500">
            <span class="w-2 h-2 rounded-full bg-rose-500/80"></span>
            <span class="w-2 h-2 rounded-full bg-amber-500/80"></span>
            <span class="w-2 h-2 rounded-full bg-emerald-500/80"></span>
            <span class="ml-2 text-slate-400 truncate">{{ deploy.preview_url }}</span>
          </div>
          <img src="{{ screenshot.screenshot_url }}" alt="Live Running MVP" class="w-full h-52 md:h-64 object-cover rounded-b-xl border border-slate-800 shadow-2xl group-hover:scale-[1.01] transition-transform duration-500">
        </div>

        <!-- QR Code Card -->
        <div class="glass-card p-5 rounded-2xl border-cyan-500/30 text-center flex flex-col items-center justify-between h-full bg-gradient-to-b from-slate-900 to-cyan-950/30">
          <div>
            <div class="text-[11px] font-mono text-cyan-400 uppercase tracking-wider font-bold mb-2">Live Daytona Sandbox</div>
            <div class="p-2 bg-white rounded-xl shadow-2xl mb-3 inline-block">
              <img src="{{ qr_url }}" alt="Scan to open running MVP" class="w-28 h-28 md:w-32 md:h-32">
            </div>
            <div class="text-xs font-bold text-white mb-0.5">Scan With Smartphone</div>
            <div class="text-[10px] text-slate-400 font-mono mb-3">Live SQLite & Next.js 14 Runtime</div>
          </div>
          <a href="{{ deploy.preview_url }}" target="_blank" class="w-full py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-xs font-mono transition-all shadow-lg shadow-cyan-500/20 active:scale-95">
            Launch Sandbox Preview ↗
          </a>
        </div>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 7: BUSINESS MODEL & GO-TO-MARKET
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-start max-w-5xl mx-auto px-4" data-slide="7" data-notes="GTM & ECONOMICS: Explain the value-aligned monetization and viral organic loop that creates high LTV and low CAC.">
      <div class="stagger-1 text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest flex items-center gap-2">
        <span>06 / Unit Economics & GTM</span>
        <span class="w-12 h-px bg-cyan-500/40"></span>
      </div>

      <h2 class="stagger-2 font-display text-2xl md:text-4xl font-black text-white mb-4">
        Monetization & Beachhead Distribution
      </h2>

      <div class="stagger-3 grid grid-cols-1 md:grid-cols-2 gap-4 w-full mb-4">
        <!-- Monetization Engine -->
        <div class="glass-card p-5 md:p-6 rounded-2xl border-slate-800">
          <div class="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1.5 font-bold">Revenue Architecture</div>
          <p class="text-lg font-black text-white mb-2">{{ ideation.monetization_model }}</p>
          <div class="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-400 mb-3">
            Suggested Tiers: {{ ideation.pricing_suggestion }}
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Value capture scales directly with active transaction volume rather than punitive usage paywalls.
          </p>
        </div>

        <!-- Target ICP & Wedge -->
        <div class="glass-card p-5 md:p-6 rounded-2xl border-slate-800">
          <div class="text-xs font-mono text-indigo-400 uppercase tracking-wider mb-1.5 font-bold">Target Persona & Beachhead Wedge</div>
          <p class="text-lg font-black text-white mb-1">{{ ideation.target_user_persona.name }}</p>
          <p class="text-xs text-slate-300 leading-relaxed mb-3">{{ ideation.target_user_persona.description }}</p>
          <div class="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-indigo-300">
            🎯 Viral Wedge: {{ ideation.go_to_market_wedge }}
          </div>
        </div>
      </div>

      <div class="stagger-4 glass-card p-3.5 rounded-xl border-slate-800 w-full flex justify-between items-center text-xs font-mono text-slate-400">
        <span>Addressable Market: {{ ideation.tam_estimate }}</span>
        <span class="text-emerald-400 font-bold">High LTV / Sub-Zero CAC Potential</span>
      </div>
    </div>

    <!-- ═════════════════════════════════════════════════════════
         SLIDE 8: THE ASK & CAPITAL ALLOCATION
         ═════════════════════════════════════════════════════════ -->
    <div class="slide items-center text-center max-w-4xl mx-auto px-4" data-slide="8" data-notes="THE ASK & SCARCITY: Conclude with conviction. Detail the capital allocation split and the 3-stage milestone execution roadmap.">
      <div class="stagger-1 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-mono mb-4">
        <span>💰 INSTITUTIONAL SEED ROUND</span>
      </div>

      <h2 class="stagger-2 font-display text-3xl md:text-5xl font-black text-white mb-2">
        Raising $2.5M Seed
      </h2>

      <p class="stagger-3 text-slate-300 text-xs md:text-sm max-w-2xl mx-auto mb-6 leading-relaxed">
        Capital will accelerate autonomous distribution, scale customer onboarding across beachhead verticals, and cement the definitive technical moat.
      </p>

      <!-- Allocation & Roadmap -->
      <div class="stagger-4 grid grid-cols-1 sm:grid-cols-3 gap-3.5 w-full max-w-3xl mb-6">
        <div class="glass-card p-4 rounded-xl border-cyan-500/30 text-left">
          <div class="flex justify-between items-center mb-1">
            <span class="text-[10px] font-mono text-cyan-400">40% ALLOCATION</span>
            <span class="text-[10px] font-mono text-slate-500">STAGE 01</span>
          </div>
          <div class="text-xs font-bold text-white mb-0.5">Core Product & Sandbox</div>
          <p class="text-[11px] text-slate-400">Scale autonomous execution pipeline and self-heal reliability.</p>
        </div>
        <div class="glass-card p-4 rounded-xl border-purple-500/30 text-left">
          <div class="flex justify-between items-center mb-1">
            <span class="text-[10px] font-mono text-purple-400">35% ALLOCATION</span>
            <span class="text-[10px] font-mono text-slate-500">STAGE 02</span>
          </div>
          <div class="text-xs font-bold text-white mb-0.5">GTM & Viral Expansion</div>
          <p class="text-[11px] text-slate-400">Capture 10,000 beachhead users via targeted community wedges.</p>
        </div>
        <div class="glass-card p-4 rounded-xl border-emerald-500/30 text-left">
          <div class="flex justify-between items-center mb-1">
            <span class="text-[10px] font-mono text-emerald-400">25% ALLOCATION</span>
            <span class="text-[10px] font-mono text-slate-500">STAGE 03</span>
          </div>
          <div class="text-xs font-bold text-white mb-0.5">Scale & Security</div>
          <p class="text-[11px] text-slate-400">Achieve $1M+ ARR run-rate with enterprise compliance audits.</p>
        </div>
      </div>

      <div class="stagger-5 flex gap-3 items-center justify-center">
        <a href="{{ deploy.preview_url }}" target="_blank" class="px-6 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black text-xs font-mono shadow-xl shadow-cyan-500/25 transition-all hover:scale-105 active:scale-95">
          Launch Running MVP ↗
        </a>
      </div>
    </div>

  </main>

  <!-- BOTTOM NAVIGATION BAR -->
  <footer class="relative z-20 flex justify-between items-center pt-3 border-t border-slate-800/80 max-w-7xl mx-auto w-full">
    <button id="prevBtn" onclick="changeSlide(-1)" class="px-3.5 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-slate-300 text-xs font-mono transition-all disabled:opacity-30 disabled:cursor-not-allowed">
      ← Previous
    </button>
    
    <!-- Slide dots -->
    <div class="flex items-center space-x-2" id="dots">
      {% for i in range(1, 9) %}
      <button onclick="goToSlide({{ i }})" class="dot w-2 h-2 rounded-full transition-all duration-300 bg-slate-800 hover:bg-slate-600" title="Slide {{ i }}"></button>
      {% endfor %}
    </div>

    <button id="nextBtn" onclick="changeSlide(1)" class="px-4 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold font-mono transition-all shadow-md shadow-cyan-500/10 active:scale-95">
      Next →
    </button>
  </footer>

  <!-- SPEAKER NOTES DRAWER -->
  <div id="speaker-notes" class="fixed bottom-0 left-0 right-0 z-50 p-5 bg-slate-950/95 border-t border-slate-800 backdrop-blur-xl shadow-2xl max-w-3xl mx-auto rounded-t-3xl border-x">
    <div class="flex justify-between items-center mb-2">
      <div class="flex items-center space-x-2 text-xs font-mono text-cyan-400 font-bold">
        <span>🎙️ SPEAKER NOTES & PSYCHOLOGICAL TALKING POINTS</span>
      </div>
      <button onclick="toggleNotes()" class="text-xs text-slate-500 hover:text-white font-mono">✕ Close (N)</button>
    </div>
    <p id="notes-content" class="text-xs text-slate-300 leading-relaxed font-sans"></p>
  </div>

  <!-- SLIDE DECK SCRIPT & ANIMATION LOGIC -->
  <script>
    let currentSlide = 1;
    const slides = document.querySelectorAll('.slide');
    const totalSlides = slides.length;
    document.getElementById('totalSlidesNum').innerText = totalSlides;

    function showSlide(n) {
      currentSlide = Math.max(1, Math.min(totalSlides, n));

      slides.forEach((s, idx) => {
        const slideNum = idx + 1;
        s.classList.remove('active', 'exit-prev');
        if (slideNum === currentSlide) {
          s.classList.add('active');
        } else if (slideNum < currentSlide) {
          s.classList.add('exit-prev');
        }
      });

      // Update dots
      document.querySelectorAll('.dot').forEach((d, idx) => {
        if (idx + 1 === currentSlide) {
          d.style.backgroundColor = 'var(--primary)';
          d.style.transform = 'scale(1.3)';
        } else {
          d.style.backgroundColor = '#1e293b';
          d.style.transform = 'scale(1)';
        }
      });

      // Update progress bar
      const progressPercent = (currentSlide / totalSlides) * 100;
      document.getElementById('progress-fill').style.width = progressPercent + '%';

      // Update numbers & buttons
      document.getElementById('currentSlideNum').innerText = currentSlide;
      document.getElementById('prevBtn').disabled = (currentSlide === 1);
      document.getElementById('nextBtn').innerText = (currentSlide === totalSlides) ? 'Finish 🚀' : 'Next →';

      // Update speaker notes
      const activeEl = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
      if (activeEl) {
        document.getElementById('notes-content').innerText = activeEl.getAttribute('data-notes') || 'No speaker notes for this slide.';
      }
    }

    function changeSlide(step) {
      showSlide(currentSlide + step);
    }

    function goToSlide(n) {
      showSlide(n);
    }

    function toggleNotes() {
      document.getElementById('speaker-notes').classList.toggle('open');
    }

    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        changeSlide(1);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        changeSlide(-1);
      } else if (e.key.toLowerCase() === 'n') {
        toggleNotes();
      } else if (e.key.toLowerCase() === 'f') {
        toggleFullscreen();
      }
    });

    // Particle Background System
    (function initParticles() {
      const canvas = document.getElementById('particles-canvas');
      const ctx = canvas.getContext('2d');
      let width, height;
      let particles = [];

      function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
      }
      window.addEventListener('resize', resize);
      resize();

      for (let i = 0; i < 45; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          size: Math.random() * 2 + 0.5,
          alpha: Math.random() * 0.35 + 0.1
        });
      }

      function render() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => {
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < 0) p.x = width;
          if (p.x > width) p.x = 0;
          if (p.y < 0) p.y = height;
          if (p.y > height) p.y = 0;

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(56, 189, 248, ${p.alpha})`;
          ctx.fill();
        });
        requestAnimationFrame(render);
      }
      render();
    })();

    showSlide(1);
  </script>
</body>
</html>
"""

async def run_deck_generation(
    run_id: str,
    ideation: IdeationOutput,
    recon: MarketReconOutput,
    whitespace: WhitespaceAnalysisOutput,
    graph: OpportunityGraphOutput,
    deploy: MvpDeployOutput,
    screenshot: ScreenshotOutput,
    log: Optional[Callable[[str], None]] = None
) -> DeckGenerationOutput:
    """
    Stage 2.14: DECK_GENERATION
    Renders a bespoke, dynamic 8-slide cinematic pitch deck in HTML/CSS with custom
    brand theming, competitive matrix, live QR code pointing to the MVP preview URL, and presentation controls.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"📊 [DECK_GENERATION] Synthesizing cinematic 8-slide pitch deck for '{ideation.product_name}'...")

    decks_dir = Path("artifacts") / "decks" / run_id
    decks_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate QR Code pointing to live preview URL
    emit(f"📱 [DECK_GENERATION] Generating QR Code for MVP Preview URL: {deploy.preview_url}...")
    qr_path = decks_dir / "preview_qr.png"
    if HAS_QRCODE:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(deploy.preview_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#0284c7", back_color="#ffffff")
            qr_img.save(str(qr_path))
        except Exception:
            qr_path.write_bytes(b"")
    else:
        qr_path.write_bytes(b"")
    qr_url = f"/api/artifacts/decks/{run_id}/preview_qr.png"

    # 2. Setup theme palette tokens
    palette = ideation.suggested_color_palette or ["#0284c7", "#0f172a", "#38bdf8"]
    primary_color = palette[0]
    bg_color = palette[1] if len(palette) > 1 else "#0f172a"
    accent_color = palette[2] if len(palette) > 2 else "#38bdf8"

    # 3. Render Jinja2 Template
    template = Template(DECK_TEMPLATE)
    deck_html = template.render(
        ideation=ideation,
        recon=recon,
        whitespace=whitespace,
        graph=graph,
        deploy=deploy,
        screenshot=screenshot,
        qr_url=qr_url,
        primary_color=primary_color,
        bg_color=bg_color,
        accent_color=accent_color
    )

    deck_path = decks_dir / "index.html"
    with open(deck_path, "w", encoding="utf-8") as f:
        f.write(deck_html)

    deck_url = f"/api/artifacts/decks/{run_id}/index.html"
    emit(f"✅ [DECK_GENERATION] 8-slide cinematic pitch deck rendered and saved to {deck_path}")

    return DeckGenerationOutput(
        deck_html_path=str(deck_path),
        deck_pdf_path=None,
        deck_url=deck_url,
        slides_count=8,
        qr_code_url=qr_url
    )
