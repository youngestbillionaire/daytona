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
  <title>{{ ideation.product_name }} — Pitch Deck | FOUNDER-0</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: {{ primary_color }};
      --bg-dark: {{ bg_color }};
      --accent: {{ accent_color }};
    }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #030712;
      color: #f8fafc;
      overflow-x: hidden;
    }
    .slide {
      display: none;
      min-height: 85vh;
      animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .slide.active {
      display: flex;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(12px) scale(0.99); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    .font-mono {
      font-family: 'JetBrains Mono', monospace;
    }
  </style>
</head>
<body class="p-6 md:p-12 flex flex-col justify-between min-h-screen">

  <!-- TOP BAR -->
  <header class="flex justify-between items-center pb-6 border-b border-slate-800">
    <div class="flex items-center space-x-3">
      <div class="w-8 h-8 rounded-lg flex items-center justify-center font-black text-white text-sm font-mono" style="background: var(--primary)">
        F0
      </div>
      <span class="font-extrabold text-lg text-white">{{ ideation.product_name }}</span>
      <span class="text-xs text-slate-500 font-mono hidden sm:inline">| FOUNDER-0 Synthesized Deck</span>
    </div>
    <div class="flex items-center space-x-2 font-mono text-xs text-slate-400">
      <span>Slide <span id="currentSlideNum" class="text-cyan-400 font-bold">1</span> / 7</span>
    </div>
  </header>

  <!-- SLIDES CONTAINER -->
  <div class="my-auto py-8">

    <!-- SLIDE 1: TITLE -->
    <div class="slide active flex-col items-center justify-center text-center max-w-4xl mx-auto" data-slide="1">
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-8">
        🚀 Autonomous Venture Synthesis
      </div>
      <h1 class="text-5xl md:text-7xl font-black text-white tracking-tight mb-6 leading-tight">
        {{ ideation.product_name }}
      </h1>
      <p class="text-2xl md:text-3xl text-cyan-400 font-bold mb-8 max-w-2xl">
        {{ ideation.tagline }}
      </p>
      <p class="text-lg text-slate-400 max-w-xl leading-relaxed">
        {{ ideation.one_line_pitch }}
      </p>
    </div>

    <!-- SLIDE 2: PROBLEM -->
    <div class="slide flex-col max-w-5xl mx-auto" data-slide="2">
      <div class="text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest">01 / The Real Problem</div>
      <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-8">Verified User Complaints in Market Recon</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {% for complaint in recon.raw_complaint_pool[:3] %}
        <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
          <div class="text-2xl text-rose-400 font-bold mb-4 font-mono">"{{ loop.index }}"</div>
          <p class="text-slate-300 text-sm leading-relaxed mb-4 italic">"{{ complaint }}"</p>
          <div class="text-xs font-mono text-slate-500">Source: Verified Community Review</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- SLIDE 3: MARKET GAP -->
    <div class="slide flex-col max-w-5xl mx-auto" data-slide="3">
      <div class="text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest">02 / Opportunity Graph</div>
      <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-6">Market Whitespace & Feature Void</h2>
      <div class="p-8 rounded-3xl bg-slate-900/90 border border-cyan-500/30 mb-6">
        <h3 class="text-xl font-bold text-cyan-300 mb-3">Primary Market Gap</h3>
        <p class="text-lg text-white leading-relaxed">{{ whitespace.primary_gap }}</p>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center">
          <div class="text-2xl font-bold text-white font-mono">{{ graph.node_count }}</div>
          <div class="text-xs text-slate-400">Knowledge Graph Nodes</div>
        </div>
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center">
          <div class="text-2xl font-bold text-white font-mono">{{ recon.competitors|length }}</div>
          <div class="text-xs text-slate-400">Analyzed Competitors</div>
        </div>
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center">
          <div class="text-2xl font-bold text-emerald-400 font-mono">100%</div>
          <div class="text-xs text-slate-400">Whitespace Unaddressed</div>
        </div>
      </div>
    </div>

    <!-- SLIDE 4: SOLUTION -->
    <div class="slide flex-col max-w-5xl mx-auto" data-slide="4">
      <div class="text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest">03 / The Solution</div>
      <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-6">{{ ideation.product_name }} Product Architecture</h2>
      <p class="text-slate-300 text-base mb-8 max-w-3xl leading-relaxed">{{ ideation.elevator_pitch }}</p>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        {% for feat in ideation.core_features %}
        <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center text-cyan-400 font-bold bg-cyan-500/10 mb-4">⚡</div>
          <h4 class="text-lg font-bold text-white mb-2">{{ feat.name }}</h4>
          <p class="text-slate-400 text-xs leading-relaxed mb-3">{{ feat.description }}</p>
          <div class="text-[11px] font-mono text-emerald-400">Value: {{ feat.user_value }}</div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- SLIDE 5: LIVE PRODUCT & QR CODE -->
    <div class="slide flex-col max-w-5xl mx-auto" data-slide="5">
      <div class="text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest">04 / Verifiable MVP</div>
      <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-6">Live Running Prototype</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
        <div class="md:col-span-2 p-4 rounded-2xl bg-slate-900 border border-slate-800">
          <img src="{{ screenshot.screenshot_url }}" alt="Live MVP" class="rounded-xl w-full object-cover shadow-2xl border border-slate-800">
        </div>
        <div class="flex flex-col items-center text-center p-6 rounded-2xl bg-slate-900/90 border border-slate-800">
          <div class="p-3 bg-white rounded-2xl shadow-xl mb-4">
            <img src="{{ qr_url }}" alt="Scan to open MVP" class="w-36 h-36">
          </div>
          <span class="text-sm font-bold text-white mb-1">Scan Live App</span>
          <span class="text-xs text-slate-400 font-mono mb-4 break-all">{{ deploy.preview_url }}</span>
          <a href="{{ deploy.preview_url }}" target="_blank" class="px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs font-mono">
            Launch Preview
          </a>
        </div>
      </div>
    </div>

    <!-- SLIDE 6: BUSINESS MODEL -->
    <div class="slide flex-col max-w-5xl mx-auto" data-slide="6">
      <div class="text-xs font-mono text-cyan-400 mb-2 uppercase tracking-widest">05 / Business Model</div>
      <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-6">Monetization & Go-To-Market</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <h4 class="text-sm font-mono text-cyan-400 uppercase mb-2">Revenue Engine</h4>
          <p class="text-xl font-bold text-white mb-3">{{ ideation.monetization_model }}</p>
          <p class="text-slate-400 text-sm">{{ ideation.pricing_suggestion }}</p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <h4 class="text-sm font-mono text-cyan-400 uppercase mb-2">Target ICP</h4>
          <p class="text-xl font-bold text-white mb-3">{{ ideation.target_user_persona.name }}</p>
          <p class="text-slate-400 text-sm leading-relaxed">{{ ideation.target_user_persona.description }}</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
        <h4 class="text-xs font-mono text-slate-500 uppercase mb-2">Differentiation Moat</h4>
        <p class="text-slate-300 text-sm">{{ ideation.differentiation_from_competitors }}</p>
      </div>
    </div>

    <!-- SLIDE 7: THE ASK -->
    <div class="slide flex-col items-center justify-center text-center max-w-3xl mx-auto" data-slide="7">
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-mono mb-8">
        💰 The Ask (100% Joke Disclaimer)
      </div>
      <h2 class="text-4xl md:text-5xl font-black text-white mb-6">
        Raising $5,000,000 at a $50M Valuation
      </h2>
      <p class="text-lg text-slate-400 leading-relaxed mb-8">
        To train autonomous agents that replace entire founding teams before demo day even starts.
      </p>
      <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 max-w-md w-full">
        <div class="text-xs font-mono text-slate-500 mb-2">NEXT MILESTONES</div>
        <div class="text-sm font-bold text-emerald-400">✓ Day 0: Autonomous MVP Shipped</div>
        <div class="text-sm font-bold text-cyan-400 mt-1">✓ Day 1: Market Recon Validated</div>
        <div class="text-sm font-bold text-purple-400 mt-1">🚀 Day 30: $100K ARR Scale</div>
      </div>
    </div>

  </div>

  <!-- NAVIGATION CONTROLS -->
  <footer class="flex justify-between items-center pt-6 border-t border-slate-800">
    <button id="prevBtn" onclick="changeSlide(-1)" class="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-sm font-mono transition-all">
      ← Previous
    </button>
    <div class="flex space-x-1.5" id="dots">
      {% for i in range(1, 8) %}
      <span class="w-2.5 h-2.5 rounded-full bg-slate-800 dot cursor-pointer" onclick="goToSlide({{ i }})"></span>
      {% endfor %}
    </div>
    <button id="nextBtn" onclick="changeSlide(1)" class="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-sm font-bold font-mono transition-all">
      Next →
    </button>
  </footer>

  <script>
    let currentSlide = 1;
    const totalSlides = 7;

    function showSlide(n) {
      document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.dot').forEach((d, idx) => {
        d.style.backgroundColor = (idx + 1 === n) ? 'var(--primary)' : '#1e293b';
      });
      const active = document.querySelector(`.slide[data-slide="${n}"]`);
      if (active) active.classList.add('active');
      document.getElementById('currentSlideNum').innerText = n;
      document.getElementById('prevBtn').disabled = (n === 1);
      document.getElementById('nextBtn').innerText = (n === totalSlides) ? 'Finish ✓' : 'Next →';
    }

    function changeSlide(step) {
      currentSlide = Math.max(1, Math.min(totalSlides, currentSlide + step));
      showSlide(currentSlide);
    }

    function goToSlide(n) {
      currentSlide = n;
      showSlide(n);
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') changeSlide(1);
      if (e.key === 'ArrowLeft') changeSlide(-1);
    });

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
    Renders a bespoke, dynamic 7-slide venture pitch deck in HTML/CSS with custom
    brand theming, live QR code pointing to the MVP preview URL, and presentation controls.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"📊 [DECK_GENERATION] Synthesizing 7-slide investor pitch deck for '{ideation.product_name}'...")

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
    emit(f"✅ [DECK_GENERATION] 7-slide deck rendered and saved to {deck_path}")

    return DeckGenerationOutput(
        deck_html_path=str(deck_path),
        deck_pdf_path=None,
        deck_url=deck_url,
        slides_count=7,
        qr_code_url=qr_url
    )
