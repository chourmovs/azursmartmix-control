# src/azursmartmix_control/ui.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import html
import re

import httpx
from nicegui import ui

from azursmartmix_control.config import Settings


AZURA_CSS = r"""
:root{
  --az-blue: #1e88e5;
  --az-blue-dark: #1565c0;
  --az-bg: #1f242d;
  --az-card: #262c37;
  --az-card2: #2b3340;
  --az-border: rgba(255,255,255,.08);
  --az-text: rgba(255,255,255,.92);
  --az-muted: rgba(255,255,255,.65);
  --az-green: #22c55e;
  --az-red: #ef4444;
  --az-orange: #f59e0b;
  --az-cyan: #22d3ee;
  --az-violet: #a78bfa;
  --az-shadow: 0 10px 30px rgba(0,0,0,.25);
  --az-radius: 10px;
  --az-font: Inter, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;
  --az-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  --wrap-max: 1860px;
  --grid-gap: 18px;
}

html, body { background: var(--az-bg) !important; color: var(--az-text) !important; font-family: var(--az-font) !important; }
.q-page-container, .q-layout, .q-page { background: var(--az-bg) !important; }
.q-card, .q-table__container, .q-menu, .q-dialog__inner, .q-drawer { background: transparent !important; }

.q-tab-panels,
.q-tab-panel,
.q-panel,
.q-panel-parent,
.q-tabs,
.q-tabs__content,
.q-tab-panels .q-panel,
.q-tab-panels .q-panel-parent { background: transparent !important; }

.q-html, .q-html * { background: transparent !important; }

.az-topbar{
  background: linear-gradient(0deg, var(--az-blue) 0%, var(--az-blue-dark) 100%) !important;
  color: white !important;
  border-bottom: 1px solid rgba(255,255,255,.15);
  box-shadow: var(--az-shadow);
}
.az-topbar .az-brand { font-weight: 900; }
.az-topbar .az-sub { opacity: .85; font-weight: 600; }

.az-wrap{ width:100%; max-width: var(--wrap-max); margin: 0 auto; padding: 18px 18px 28px 18px; }
.az-grid{ display:grid; grid-template-columns: 1fr 1fr; gap: var(--grid-gap); }
@media (max-width: 1200px){ .az-grid{ grid-template-columns: 1fr; } }

.az-card{
  background: var(--az-card) !important;
  border: 1px solid var(--az-border);
  border-radius: var(--az-radius);
  box-shadow: var(--az-shadow);
  overflow: hidden;
  min-width: 520px;
}
@media (max-width: 1200px){ .az-card{ min-width: unset; } }

.az-card-h{
  padding: 12px 14px;
  border-bottom: 1px solid var(--az-border);
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 10px;
}
.az-card-h .q-label{ font-weight: 800; letter-spacing: .2px; }
.az-card-b{ padding: 12px 14px; }

.az-actions .q-btn{ border: 1px solid rgba(255,255,255,.18) !important; }
.az-actions .q-btn--outline{ color: white !important; }
.az-actions .q-btn--standard{ background: rgba(255,255,255,.10) !important; color: white !important; }
.az-actions .q-btn .q-focus-helper{ display:none; }

.az-badge{
  display:inline-flex;
  align-items:center;
  gap: 8px;
  font-size: 12px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--az-border);
  background: rgba(255,255,255,.05);
}
.az-dot{ width:10px; height:10px; border-radius:999px; display:inline-block; }
.az-dot.ok{ background: var(--az-green); box-shadow: 0 0 0 3px rgba(34,197,94,.15); }
.az-dot.warn{ background: var(--az-orange); box-shadow: 0 0 0 3px rgba(245,158,11,.15); }
.az-dot.bad{ background: var(--az-red); box-shadow: 0 0 0 3px rgba(239,68,68,.15); }

.az-list{ display:flex; flex-direction:column; gap: 8px; }
.az-item{
  border: 1px solid var(--az-border);
  border-radius: 10px;
  padding: 10px;
  background: rgba(0,0,0,.12);
}
.az-item .i-h{ display:flex; justify-content:space-between; gap:10px; }
.az-item .i-n{ font-weight: 900; opacity: .9; }
.az-item .i-ts{ font-family: var(--az-mono); color: var(--az-muted); font-size: 12px; }
.az-item .i-t{ margin-top: 6px; font-weight: 850; }
.az-item .i-p{ margin-top: 3px; font-family: var(--az-mono); color: var(--az-muted); font-size: 12px; }

.console-frame{
  border: 1px solid var(--az-border);
  border-radius: 10px;
  overflow:hidden;
  background: rgba(0,0,0,.10);
}
.console-content{
  font-family: var(--az-mono);
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 10px 12px;
  max-height: 520px;
  overflow:auto;
}

.t-dim{ color: rgba(255,255,255,.72); }
.hl-info{ color: rgba(34,211,238,.95); font-weight: 900; }
.hl-warn{ color: rgba(245,158,11,.95); font-weight: 900; }
.hl-err{ color: rgba(239,68,68,.95); font-weight: 900; }
.hl-engine{ color: rgba(167,139,250,.95); font-weight: 900; }
.hl-sched{ color: rgba(34,197,94,.95); font-weight: 900; }
.hl-key{ color: rgba(255,255,255,.88); font-weight: 900; }
.hl-uri{ color: rgba(255,255,255,.80); }

.az-player{
  margin-top: 10px;
  border: 1px solid var(--az-border);
  border-radius: 10px;
  padding: 10px;
  background: rgba(0,0,0,.12);
}
.az-player audio{ width: 100%; }
.az-player .hint{
  margin-top: 6px;
  font-family: var(--az-mono);
  font-size: 12px;
  opacity: .75;
}

.env-toolbar{ display:flex; align-items:center; gap:10px; margin-bottom: 10px; }
.env-search{ width: 100%; }
.env-frame{
  border: 1px solid var(--az-border);
  border-radius: 10px;
  overflow:hidden;
  max-height: 360px;
  background: rgba(0,0,0,.10);
}
.env-row{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap: 10px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.env-row:last-child{ border-bottom:0; }
.env-k{
  font-family: var(--az-mono);
  font-size: 12px;
  color: rgba(255,255,255,.88);
  font-weight: 900;
  cursor: pointer;
}
.env-v{
  font-family: var(--az-mono);
  font-size: 12px;
  color: rgba(255,255,255,.80);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

/* meta rows */
.np-meta{
  margin-top: 8px;
  display:flex;
  flex-direction:column;
  gap: 6px;
}
.np-line{
  font-family: var(--az-mono);
  font-size: 12px;
  color: rgba(255,255,255,.80);
}
.np-k{ color: rgba(255,255,255,.55); }
.np-v{ color: rgba(255,255,255,.92); font-weight: 900; }
.np-pill{
  display:inline-flex; align-items:center; gap:8px;
  padding: 5px 10px;
  border-radius: 999px;
  border:1px solid var(--az-border);
  background: rgba(255,255,255,.05);
}
"""

AZURA_JS = r"""
document.addEventListener('click', (ev) => {
  const el = ev.target.closest('[data-copy]');
  if (!el) return;
  const txt = el.getAttribute('data-copy') || el.textContent || '';
  if (!txt) return;
  navigator.clipboard.writeText(txt).catch(()=>{});
});
"""


class ControlUI:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_base = settings.api_prefix.rstrip("/")
        self.timeout = httpx.Timeout(2.5, connect=1.5)
        self._timer = None

        self._docker_badge = None
        self._rt_engine_tbl = None
        self._rt_sched_tbl = None

        self._now_title = None
        self._now_meta = None
        self._now_player = None

        self._up_list_container = None

        self._env_search = None
        self._env_frame = None
        self._env_rows: List[Tuple[str, str]] = []

        self._env_editor_grid = None
        self._env_inputs: Dict[str, ui.input] = {}
        self._env_editor_note = None

        self._tag_input = None
        self._tag_last_applied = None

        self._need_restart_badge = None

        self._log_html_engine = None
        self._log_html_sched = None

    def _stream_public_url(self) -> str:
        public = getattr(self.settings, "icecast_public_url", "") or ""
        public = str(public).strip()
        if public:
            return public.rstrip("/")
        scheme = getattr(self.settings, "icecast_scheme", "http")
        host = getattr(self.settings, "icecast_host", "localhost")
        port = getattr(self.settings, "icecast_port", 8000)
        mount = getattr(self.settings, "icecast_mount", "/")
        if not str(mount).startswith("/"):
            mount = "/" + str(mount)
        return f"{scheme}://{host}:{port}{mount}"

    def build(self) -> None:
        ui.add_head_html(f"<style>{AZURA_CSS}</style>")
        ui.add_head_html(f"<script>{AZURA_JS}</script>")
        ui.page_title("AzurSmartMix Control")

        with ui.header().classes("az-topbar items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.label("azuracast").classes("az-brand text-xl")
                ui.label("AzurSmartMix Control").classes("az-sub text-sm")

                self._need_restart_badge = ui.html("")
            with ui.row().classes("items-center gap-2 az-actions"):
                ui.button("Down", on_click=self.stack_down).props("outline")
                ui.button("Up", on_click=self.stack_up).props("outline")
                ui.button("Restart", on_click=self.stack_restart).props("outline")

                self._tag_input = ui.input(placeholder="tag (latest, beta1, …)").props("dense outlined").style("width: 180px;")
                ui.button("Apply tag", on_click=self.apply_tag).props("outline")

                ui.button("Purge image", on_click=self.purge_image).props("outline")
                ui.button("Refresh", on_click=self.refresh_all).props("unelevated color=white text-color=primary")
                ui.button("Auto 5s", on_click=self.enable_autorefresh).props("outline")
                ui.button("Stop", on_click=self.disable_autorefresh).props("outline")

        with ui.element("div").classes("az-wrap"):
            # Main page tabs (keeps old frames; adds one dedicated editor tab)
            with ui.tabs().classes("w-full") as main_tabs:
                t_dash = ui.tab("dashboard")
                t_env = ui.tab("engine env")
                t_logs = ui.tab("logs")

            with ui.tab_panels(main_tabs, value=t_dash).classes("w-full"):
                with ui.tab_panel(t_dash):
                    with ui.element("div").classes("az-grid"):
                        self._card_runtime()
                        self._card_env_readonly()
                        self._card_now()
                        self._card_upcoming()

                with ui.tab_panel(t_env):
                    self._card_env_editor()

                with ui.tab_panel(t_logs):
                    self._card_logs()

        ui.timer(0.1, self.refresh_all, once=True)

    # --------------------------- CARDS ---------------------------

    def _card_runtime(self) -> None:
        with ui.element("div").classes("az-card"):
            with ui.element("div").classes("az-card-h"):
                ui.label("Runtime Status")
                self._docker_badge = ui.html(
                    '<span class="az-badge"><span class="az-dot warn"></span><span>Docker: …</span></span>'
                )
            with ui.element("div").classes("az-card-b"):
                self._rt_engine_tbl = ui.html("—")
                ui.separator().classes("my-2")
                self._rt_sched_tbl = ui.html("—")

    def _card_env_readonly(self) -> None:
        with ui.element("div").classes("az-card"):
            with ui.element("div").classes("az-card-h"):
                ui.label("Engine env (docker-compose)")
                ui.label(self.settings.compose_service_engine).classes("text-xs").style("opacity:.85;")
            with ui.element("div").classes("az-card-b"):
                with ui.element("div").classes("env-toolbar"):
                    self._env_search = ui.input(placeholder="Filter (key/value)…").classes("env-search").props("dense outlined")
                    ui.button("Clear", on_click=self._env_clear_filter).props("outline")
                self._env_frame = ui.element("div").classes("env-frame")

    def _card_env_editor(self) -> None:
        with ui.element("div").classes("az-card").style("min-width: unset;"):
            with ui.element("div").classes("az-card-h"):
                ui.label("Edit Engine env (docker-compose)")
                ui.label("Save => need restart").classes("text-xs").style("opacity:.85;")
            with ui.element("div").classes("az-card-b"):
                self._env_editor_note = ui.html('<div class="t-dim" style="font-size:12px;">Loading…</div>')
                self._env_editor_grid = ui.element("div").classes("env-frame").style("max-height: 520px;")

                with ui.row().classes("items-center gap-2").style("margin-top: 10px;"):
                    ui.button("Reload from compose", on_click=self.refresh_engine_env_editor).props("outline")
                    ui.button("Save", on_click=self.save_engine_env_editor).props("unelevated color=primary")
                    ui.button("Clear restart banner", on_click=self.clear_need_restart).props("outline")

    def _now_meta_html(self, now: Dict[str, Any]) -> str:
        title_eff = html.escape(str(now.get("title_effective") or "—"))
        title_obs = html.escape(str(now.get("title_observed") or "—"))
        listeners = html.escape(str(now.get("listeners") or "—"))
        bitrate = html.escape(str(now.get("bitrate") or "—"))

        hint = '<span class="t-dim">click to copy</span>'

        return (
            '<div class="np-meta">'
            f'  <div class="np-line"><span class="np-k">effective:</span> <span class="np-v" data-copy="{title_eff}">{title_eff}</span> {hint}</div>'
            f'  <div class="np-line"><span class="np-k">observed:</span> <span class="t-dim" data-copy="{title_obs}">{title_obs}</span></div>'
            f'  <div class="np-line"><span class="np-k">listeners:</span> <span class="np-v" data-copy="{listeners}">{listeners}</span> '
            f'      <span class="t-dim">|</span> <span class="np-k">bitrate:</span> <span class="np-v" data-copy="{bitrate}">{bitrate}</span></div>'
            '</div>'
        )

    def _player_html(self, url: str) -> str:
        u = html.escape(url)
        return (
            f'<div class="az-player">'
            f'  <audio controls preload="none" crossorigin="anonymous">'
            f'    <source src="{u}" type="audio/mpeg" />'
            f'  </audio>'
            f'  <div class="hint" data-copy="{u}">{u}</div>'
            f'</div>'
        )

    def _card_now(self) -> None:
        stream_url = self._stream_public_url()
        mount = getattr(self.settings, "icecast_mount", "/gst-test.mp3")
        with ui.element("div").classes("az-card"):
            with ui.element("div").classes("az-card-h"):
                ui.label("Now Playing")
                ui.label(str(mount)).classes("text-xs").style("opacity:.85;")
            with ui.element("div").classes("az-card-b"):
                self._now_title = ui.label("—").classes("text-xl").style("font-weight: 950; margin: 2px 0 0 0;")
                self._now_meta = ui.html(self._now_meta_html({}))
                self._now_player = ui.html(self._player_html(stream_url))

    def _card_upcoming(self) -> None:
        with ui.element("div").classes("az-card"):
            with ui.element("div").classes("az-card-h"):
                ui.label("Upcoming")
                ui.label("scheduler").classes("text-xs").style("opacity:.85;")
            with ui.element("div").classes("az-card-b"):
                self._up_list_container = ui.element("div").classes("az-list")

    def _card_logs(self) -> None:
        # FIX Quasar error: QTab must be a child of QTabs => use context manager.
        with ui.element("div").classes("az-card").style("min-width: unset;"):
            with ui.element("div").classes("az-card-h"):
                ui.label("Logs")
                ui.label("tail=200").classes("text-xs").style("opacity:.85;")
            with ui.element("div").classes("az-card-b"):
                with ui.tabs().classes("w-full") as tabs:
                    t_engine = ui.tab("engine")
                    t_sched = ui.tab("scheduler")

                with ui.tab_panels(tabs, value=t_engine).classes("w-full"):
                    with ui.tab_panel(t_engine):
                        with ui.element("div").classes("console-frame").style("background: rgba(0,0,0,.55) !important;"):
                            self._log_html_engine = ui.html('<div class="console-content">—</div>')
                    with ui.tab_panel(t_sched):
                        with ui.element("div").classes("console-frame").style("background: rgba(0,0,0,.55) !important;"):
                            self._log_html_sched = ui.html('<div class="console-content">—</div>')

    # --------------------------- HTTP helpers ---------------------------

    def _api_url(self, path: str) -> str:
        p = path if path.startswith("/") else f"/{path}"
        return f"http://127.0.0.1:{self.settings.ui_port}{self.api_base}{p}"

    async def _get_json(self, path: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(self._api_url(path))
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, dict) else {"data": data}

    async def _get_text(self, path: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(self._api_url(path))
            r.raise_for_status()
            return r.text

    async def _post_json(self, path: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(self._api_url(path), json=(payload or {}))
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, dict) else {"data": data}

    # --------------------------- UI: runtime/status ---------------------------

    def _set_docker_badge(self, ok: bool, text: str) -> None:
        if not self._docker_badge:
            return
        dot = "ok" if ok else "warn"
        self._docker_badge.set_content(
            f'<span class="az-badge"><span class="az-dot {dot}"></span><span>{html.escape(text)}</span></span>'
        )

    def _runtime_tbl_html(self, data: Dict[str, Any]) -> str:
        def row(k: str, v: Any) -> str:
            vv = "—" if v is None or v == "" else str(v)
            vve = html.escape(vv)
            return f'<div class="np-line"><span class="np-k">{html.escape(k)}:</span> <span class="np-v" data-copy="{vve}">{vve}</span></div>'

        return (
            '<div class="np-meta">'
            + row("name", data.get("name"))
            + row("image", data.get("image"))
            + row("status", data.get("status"))
            + row("health", data.get("health"))
            + row("uptime", data.get("uptime"))
            + "</div>"
        )

    async def refresh_runtime(self) -> None:
        try:
            data = await self._get_json("/panel/runtime")
        except Exception:
            data = {"docker_ping": False, "engine": {"present": False}, "scheduler": {"present": False}}

        docker_ping = bool(data.get("docker_ping"))
        self._set_docker_badge(docker_ping, "Docker: OK" if docker_ping else "Docker: unreachable")

        eng = data.get("engine") if isinstance(data, dict) else None
        sch = data.get("scheduler") if isinstance(data, dict) else None

        if self._rt_engine_tbl:
            self._rt_engine_tbl.set_content(self._runtime_tbl_html(eng if isinstance(eng, dict) else {}))
        if self._rt_sched_tbl:
            self._rt_sched_tbl.set_content(self._runtime_tbl_html(sch if isinstance(sch, dict) else {}))

    # --------------------------- UI: env readonly ---------------------------

    async def refresh_engine_env(self) -> None:
        if self._env_frame is None:
            return
        try:
            data = await self._get_json("/panel/engine_env")
            env = data.get("environment") if isinstance(data, dict) else None
            if isinstance(env, dict):
                self._env_rows = [(k, str(env.get(k, ""))) for k in sorted(env.keys())]
            else:
                self._env_rows = [("error", str(data))]
        except Exception as e:
            self._env_rows = [("error", str(e))]
        self._render_env_readonly()

    def _env_clear_filter(self) -> None:
        if self._env_search:
            self._env_search.set_value("")
        self._render_env_readonly()

    def _render_env_readonly(self) -> None:
        if self._env_frame is None:
            return
        q = (self._env_search.value or "").strip().lower() if self._env_search else ""
        rows = self._env_rows
        if q:
            rows = [(k, v) for (k, v) in rows if q in k.lower() or q in v.lower()]

        self._env_frame.clear()
        with self._env_frame:
            if not rows:
                ui.html('<div style="padding:10px; opacity:.7;">—</div>')
                return
            for k, v in rows:
                k_e = html.escape(k)
                v_e = html.escape(v)
                ui.html(
                    f'<div class="env-row">'
                    f'  <div class="env-k" data-copy="{k_e}">{k_e}</div>'
                    f'  <div class="env-v" data-copy="{v_e}">{v_e}</div>'
                    f'</div>'
                )

    # --------------------------- UI: env editor ---------------------------

    async def refresh_engine_env_editor(self) -> None:
        if self._env_editor_grid is None:
            return
        self._env_inputs = {}
        try:
            data = await self._get_json("/panel/engine_env")
            env = data.get("environment") if isinstance(data, dict) else None
            if not isinstance(env, dict):
                env = {}
            self._env_editor_note.set_content(
                f'<div class="t-dim" style="font-size:12px;">Loaded {len(env)} variables from compose. Click Save to persist.</div>'
            )
        except Exception as e:
            env = {}
            self._env_editor_note.set_content(
                f'<div class="hl-err" style="font-size:12px;">Failed to load: {html.escape(str(e))}</div>'
            )

        self._env_editor_grid.clear()
        with self._env_editor_grid:
            # Render as rows of inputs, preserving keys. Values editable.
            keys = sorted(env.keys())
            if not keys:
                ui.html('<div style="padding:10px; opacity:.7;">No environment variables found.</div>')
                return

            for k in keys:
                v = "" if env.get(k) is None else str(env.get(k))
                with ui.row().classes("items-center").style("padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,.06);"):
                    ui.label(k).style("width: 280px; font-family: var(--az-mono); font-size: 12px; font-weight: 900;")
                    inp = ui.input(value=v).props("dense outlined").style("width: 100%; font-family: var(--az-mono);")
                    self._env_inputs[str(k)] = inp

    async def save_engine_env_editor(self) -> None:
        env_out: Dict[str, str] = {}
        for k, inp in (self._env_inputs or {}).items():
            env_out[k] = "" if inp.value is None else str(inp.value)

        try:
            res = await self._post_json("/panel/engine_env", {"environment": env_out})
            ok = bool(res.get("ok")) if "ok" in res else bool(res.get("present"))  # compat
            if ok:
                self._env_editor_note.set_content(
                    '<div class="hl-info" style="font-size:12px;">Saved. Restart required to take effect.</div>'
                )
            else:
                self._env_editor_note.set_content(
                    f'<div class="hl-err" style="font-size:12px;">Save failed: {html.escape(str(res))}</div>'
                )
        except Exception as e:
            self._env_editor_note.set_content(
                f'<div class="hl-err" style="font-size:12px;">Save failed: {html.escape(str(e))}</div>'
            )

        await self.refresh_need_restart()

    # --------------------------- UI: now & upcoming ---------------------------

    async def refresh_now(self) -> None:
        try:
            now = await self._get_json("/panel/now")
            title = now.get("title_effective") or now.get("title_observed") or "—"
            self._now_title.set_text(title)
            if self._now_meta:
                self._now_meta.set_content(self._now_meta_html(now if isinstance(now, dict) else {}))
        except Exception:
            self._now_title.set_text("—")
            if self._now_meta:
                self._now_meta.set_content(self._now_meta_html({}))

    async def refresh_upcoming(self) -> None:
        if self._up_list_container is None:
            return
        try:
            up = await self._get_json("/panel/upcoming?n=10")
            items = up.get("upcoming") or []
            if not isinstance(items, list):
                items = []
        except Exception:
            items = []

        self._up_list_container.clear()
        with self._up_list_container:
            if not items:
                ui.html('<div style="opacity:.7; font-size: 12px;">—</div>')
                return
            for i, it in enumerate(items, start=1):
                if not isinstance(it, dict):
                    continue
                title = str(it.get("title_display") or it.get("title") or "—")
                playlist = str(it.get("playlist") or it.get("pl") or "—")
                ts = str(it.get("ts") or it.get("at") or "")
                ui.html(
                    '<div class="az-item">'
                    f'  <div class="i-h"><div class="i-n">#{i:02d}</div><div class="i-ts" data-copy="{html.escape(ts)}">{html.escape(ts)}</div></div>'
                    f'  <div class="i-t" data-copy="{html.escape(title)}">{html.escape(title)}</div>'
                    f'  <div class="i-p" data-copy="{html.escape(playlist)}">{html.escape(playlist)}</div>'
                    "</div>"
                )

    # --------------------------- UI: logs ---------------------------

    _re_level = re.compile(r"\b(INFO|WARN|WARNING|ERROR|CRITICAL|DEBUG)\b")
    _re_engine_tag = re.compile(r"\bazurmixd\.engine\b")
    _re_sched_tag = re.compile(r"\bazurmixd\.scheduler\b")
    _re_uri = re.compile(r"\b(file:///[^ ]+)\b")

    def _highlight_logs_html(self, text: str) -> str:
        esc = html.escape(text)

        def repl_level(m: re.Match) -> str:
            lvl = m.group(1)
            if lvl in ("WARN", "WARNING"):
                return f'<span class="hl-warn">{lvl}</span>'
            if lvl in ("ERROR", "CRITICAL"):
                return f'<span class="hl-err">{lvl}</span>'
            return f'<span class="hl-info">{lvl}</span>'

        esc = self._re_level.sub(repl_level, esc)
        esc = self._re_engine_tag.sub('<span class="hl-engine">azurmixd.engine</span>', esc)
        esc = self._re_sched_tag.sub('<span class="hl-sched">azurmixd.scheduler</span>', esc)
        esc = self._re_uri.sub(lambda m: f'<span class="hl-uri">{html.escape(m.group(1))}</span>', esc)

        return f'<div class="console-content">{esc or "—"}</div>'

    async def refresh_logs(self) -> None:
        try:
            eng = await self._get_text("/logs?service=engine&tail=200")
            if self._log_html_engine:
                self._log_html_engine.set_content(self._highlight_logs_html(eng))
        except Exception:
            if self._log_html_engine:
                self._log_html_engine.set_content('<div class="console-content">—</div>')

        try:
            sch = await self._get_text("/logs?service=scheduler&tail=200")
            if self._log_html_sched:
                self._log_html_sched.set_content(self._highlight_logs_html(sch))
        except Exception:
            if self._log_html_sched:
                self._log_html_sched.set_content('<div class="console-content">—</div>')

    # --------------------------- UI: need restart banner ---------------------------

    async def refresh_need_restart(self) -> None:
        if not self._need_restart_badge:
            return
        try:
            data = await self._get_json("/panel/need_restart")
            need = bool(data.get("need_restart"))
            reason = str(data.get("reason") or "")
        except Exception:
            need = False
            reason = ""

        if not need:
            self._need_restart_badge.set_content("")
            return

        r = html.escape(reason) if reason else "Restart required for changes to take effect."
        self._need_restart_badge.set_content(
            f'<span class="az-badge"><span class="az-dot warn"></span><span>need restart</span></span>'
            f'<span style="margin-left:10px; font-size:12px; opacity:.85;" class="t-dim" data-copy="{r}">{r}</span>'
        )

    async def clear_need_restart(self) -> None:
        try:
            await self._post_json("/panel/need_restart/clear", {})
        except Exception:
            pass
        await self.refresh_need_restart()

    # --------------------------- Header actions ---------------------------

    async def stack_down(self) -> None:
        try:
            await self._post_json("/panel/stack/down", {})
        except Exception:
            pass
        await self.refresh_all()

    async def stack_up(self) -> None:
        try:
            await self._post_json("/panel/stack/up", {})
        except Exception:
            pass
        await self.refresh_all()

    async def stack_restart(self) -> None:
        try:
            await self._post_json("/panel/stack/restart", {})
        except Exception:
            pass
        await self.refresh_all()

    async def apply_tag(self) -> None:
        tag = (self._tag_input.value or "").strip() if self._tag_input else ""
        if not tag:
            return
        try:
            res = await self._post_json("/panel/image_tag", {"tag": tag})
            if res.get("ok"):
                self._tag_last_applied = tag
        except Exception:
            pass
        await self.refresh_need_restart()

    async def purge_image(self) -> None:
        tag = (self._tag_input.value or "").strip() if self._tag_input else ""
        if not tag:
            tag = self._tag_last_applied or "latest"
        try:
            # Query-based endpoint; use GET-style POST helper by embedding query in path.
            await self._post_json(f"/panel/stack/update_image_cache?tag={tag}", {})
        except Exception:
            pass
        await self.refresh_need_restart()

    # --------------------------- refresh orchestrator ---------------------------

    async def refresh_all(self) -> None:
        await self.refresh_need_restart()
        await self.refresh_runtime()
        await self.refresh_engine_env()
        await self.refresh_now()
        await self.refresh_upcoming()
        await self.refresh_logs()
        await self.refresh_engine_env_editor()

    def enable_autorefresh(self) -> None:
        if self._timer is not None:
            return
        self._timer = ui.timer(5.0, self.refresh_all)

    def disable_autorefresh(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        self._timer = None
