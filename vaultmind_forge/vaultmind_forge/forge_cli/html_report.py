from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, select_autoescape

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>VaultMind Forge Report - {{ job_id }}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
    .ok { color: #0a7a3e; }
    .bad { color: #b00020; }
    .muted { color: #777; }
    .h { font-weight: 600; margin-bottom: .5rem; }
    .metric { display: flex; justify-content: space-between; margin: .25rem 0; }
    .pill { padding: .2rem .5rem; border-radius: 999px; background: #f0f0f0; }
  </style>
</head>
<body>
  <h1>VaultMind Forge - {{ job_id }}</h1>
  <p class="muted">Generated {{ now }}</p>

  <h2>Passes</h2>
  <div class="grid">
  {% for rep in reports %}
    <div class="card">
      <div class="h">Pass: {{ rep.pass }}</div>
      <div class="metric"><span>Decision</span><span class="pill">{{ rep.decision }}</span></div>
      {% for k, v in rep.metrics.items() %}
        <div class="metric"><span>{{ k }}</span><span>{{ '%.3f'|format(v) }}</span></div>
      {% endfor %}
      <div class="h" style="margin-top:.5rem">Remedies</div>
      {% if rep.remedies %}
        <ul>
        {% for r in rep.remedies %}
          <li>{{ r.issue }} — <span class="muted">{{ r.prescription }}</span></li>
        {% endfor %}
        </ul>
      {% else %}
        <div class="muted">None</div>
      {% endif %}
    </div>
  {% endfor %}
  </div>

  <h2>Diagnostics</h2>
  <div class="grid">
  {% for name, d in diagnostics.items() %}
    <div class="card">
      <div class="h">{{ name }}</div>
      <div>backend: <span class="pill">{{ d.backend }}</span></div>
      <div>ok: <span class="pill">{{ d.ok }}</span></div>
      <div>time: {{ '%.1f'|format(d.ms) }} ms</div>
      {% if d.error %}<div class="bad">{{ d.error }}</div>{% endif %}
    </div>
  {% endfor %}
  </div>
</body>
</html>
"""


def write_html_report(job_id: str, reports: List[Dict], diagnostics: Dict[str, Dict], out_dir: Path) -> Path:
    env = Environment(autoescape=select_autoescape())
    tmpl = env.from_string(TEMPLATE)
    html = tmpl.render(job_id=job_id, reports=reports, diagnostics=diagnostics, now=datetime.utcnow().isoformat())
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{job_id}__report.html"
    path.write_text(html, encoding="utf-8")
    return path