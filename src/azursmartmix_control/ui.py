from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional
import html
import re
import urllib.parse

import httpx
from nicegui import ui

from azursmartmix_control.config import Settings


# ---------- THEME / CSS (inchangé, gardé compact ici) ----------
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
.q-tab-panels, .q-tab-panel, .q-panel, .q-panel-parent, .q-tabs, .q-tabs__content { background: transparent !important; }
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
  background: var(--az-blue) !important;
  color: white !important;
  padding: 12px 14px;
  font-weight: 900;
  display:flex; align-items:center; justify-content:space-between;
}
.az-card-b{ padding: 14px; background: linear-gradient(180deg, var(--az-card2), var(--az-card)); }

.az-badge{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border-radius:999px;
  font-weight:900; font-size:12px;
  border:1px solid var(--az-border);
  background: rgba(255,255,255,.05);
}
.az-dot{ width:10px; height:10px; border-radius:999px; display:inline-block; }
.az-dot.ok{ background: var(--az-green); }
.az-dot.err{ background: var(--az-red); }
.az-dot.warn{ background: var(--az-orange); }

.az-opbtn .q-btn{
  border-radius: 10px !important;
  font-weight: 950 !important;
  text-transform:none !important;
  padding: 6px 10px !important;
}
.az-opbtn .q-btn--outline{ border:1px solid rgba(255,255,255,.55) !important; color:white !important; }

.az-list{ display:flex; flex-direction:column; gap:8px; }
.az-item{ padding: 10px 12px; border-radius: 10px; border: 1px solid var(--az-border); background: rgba(255,255,255,.04); }
.az-item .idx{ display:inline-block; min-width:24px; font-weight:950; color: rgba(255,255,255,.75); }
.az-item .txt{ font-weight:650; }

.console-frame{
  height: 420px;
  overflow: auto;
  border: 1px solid var(--az-border);
  border-radius: 10px;
  background: rgba(0,0,0,.55) !important;
  padding: 10px 12px;
}
.console-frame, .console-frame * { background: transparent !important; }
.console-frame { background: rgba(0,0,0,.55) !important; }
.console-content{
  font-family: var(--az-mono) !important;
  font-size: 12px !important;
  line-height: 1.35 !important;
  color: rgba(255,255,255,.86) !important;
  white-space: pre-wrap !important;
  word-break: break-word !important;
  margin: 0 !important;
  padding: 0 !important;
}

.t-dim{ color: rgba(255,255,255,.45) !important; }
.t-info{ color: rgba(56, 189, 248, .95) !important; }
.t-warn{ color: rgba(245, 158, 11, .95) !important; }
.t-err{  color: rgba(239, 68, 68, .95) !important; }
.t-ok{   color: rgba(34, 197, 94, .95) !important; }
.t-vio{  color: rgba(167, 139, 250, .95) !important; }
.t-cyan{ color: rgba(34, 211, 238, .95) !important; }
.t-bold{ font-weight: 900 !important; }

.az-tabsbar{
  margin: 10px 0 18px 0;
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 12px;
  overflow: hidden;
}
.az-tabsbar .q-tabs{ background: rgba(0,0,0,.15) !important; }

.az-editor{
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 12px;
  background: rgba(0,0,0,.12);
  padding: 12px;
}
.az-editor-h{
  display:flex; align-items:center; justify-content:space-between;
  gap: 10px; margin-bottom: 10px;
}
.az-editor-grid{
  display:grid;
  grid-template-columns: 360px 1fr 52px;
  gap: 10px;
}
@media (max-width: 1200px){ .az-editor-grid{ grid-template-columns: 1fr; } }
.az-editor-grid input{ font-family: var(--az-mono) !important; }
.az-editor-row{
  padding: 8px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.04);
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
        self.timeout = httpx.Timeout(30.0, connect=3.0)

        self._timer = None

        # header elements
        self._restart_needed = False
        self._restart_badge = None
        self._tag_select = None
        self._tag_value = self._default_tag_from_image()
        self._ops_busy = False

        # ops dialog
        self._ops_dialog = None
        self._ops_html = None

        # dashboard bits (placeholders - tu peux reconnecter tes cartes existantes)
        self._log_html_engine = None
        self._log_html_sched = None

        # compose env editor
        self._compose_env_rows_container = None
        self._compose_env_rows: List[Dict[str, Any]] = []
        self._compose_env_busy = False
        self._compose_env_format = "dict"

    # ---------- helpers ----------
    def _default_tag_from_image(self) -> str:
        s = (self.settings.azursmartmix_image or "").strip()
        if ":" in s:
            return s.rsplit(":", 1)[1].strip() or "latest"
        return "latest"

    def _set_restart_needed(self, needed: bool) -> None:
        self._restart_needed = bool(needed)
        if not self._restart_badge:
            return
        if not self._restart_needed:
            self._restart_badge.set_content("")
            return
        self._restart_badge.set_content(
            '<span class="az-badge" style="border-color: rgba(245,158,11,.55); background: rgba(245,158,11,.15);">'
            '<span class="az-dot warn"></span>'
            '<span>Need restart to take effect</span>'
            "</span>"
        )

    def _on_tag_change(self, e) -> None:
        try:
            self._tag_value = str(e.value).strip()
        except Exception:
            self._tag_value = self._default_tag_from_image()

    # ---------- http helpers ----------
    async def _get_json(self, path: str) -> Dict[str, Any]:
        url = f"http://127.0.0.1:{self.settings.ui_port}{self.api_base}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, dict) else {"data": data}

    async def _get_text(self, path: str) -> str:
        url = f"http://127.0.0.1:{self.settings.ui_port}{self.api_base}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text

    async def _post_text(self, path: str) -> str:
        url = f"http://127.0.0.1:{self.settings.ui_port}{self.api_base}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url)
            r.raise_for_status()
            return r.text

    async def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"http://127.0.0.1:{self.settings.ui_port}{self.api_base}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, dict) else {"data": data}

    # ---------- ops dialog ----------
    def _build_ops_dialog(self) -> None:
        with ui.dialog() as d:
            self._ops_dialog = d
            with ui.card().classes("az-card").style("min-width: 920px; max-width: 1200px;"):
                with ui.element("div").classes("az-card-h"):
                    ui.label("Operations Console")
                    ui.button("Close", on_click=d.close).props("outline")
                with ui.element("div").classes("az-card-b"):
                    ui.label(f"cwd: {self.settings.azuramix_dir}").style("font-family: var(--az-mono); font-size: 12px; opacity:.85;")
                    ui.label(f"compose: {self.settings.azuramix_compose_file}").style("font-family: var(--az-mono); font-size: 12px; opacity:.65; margin-top: 2px;")
                    ui.separator().style("opacity:.25; margin: 10px 0;")
                    with ui.element("div").classes("console-frame").style("height: 520px;"):
                        self._ops_html = ui.html('<div class="console-content">—</div>')

    def _highlight_ops_html(self, text: str) -> str:
        esc = html.escape(text)
        esc = re.sub(r"\b(True|False)\b", lambda m: f'<span class="t-bold {"t-ok" if m.group(1)=="True" else "t-err"}">{m.group(1)}</span>', esc)
        esc = re.sub(r"\berror\b", lambda m: f'<span class="t-err t-bold">{m.group(0)}</span>', esc, flags=re.IGNORECASE)
        esc = re.sub(r"\bdocker\b", lambda m: f'<span class="t-cyan t-bold">{m.group(0)}</span>', esc, flags=re.IGNORECASE)
        esc = re.sub(r"\bcompose\b", lambda m: f'<span class="t-cyan">{m.group(0)}</span>', esc, flags=re.IGNORECASE)
        return f'<div class="console-content">{esc}</div>'

    def _set_ops_busy(self, busy: bool) -> None:
        self._ops_busy = busy
        if self._tag_select:
            self._tag_select.disable() if busy else self._tag_select.enable()

    async def _run_op(self, label: str, path: str, clears_restart_hint: bool = False) -> None:
        if self._ops_busy:
            ui.notify("Operation already running", type="warning")
            return
        self._set_ops_busy(True)
        try:
            if self._ops_dialog:
                self._ops_dialog.open()
            if self._ops_html:
                self._ops_html.set_content(self._highlight_ops_html(f"== {label} ==\nPOST {path}\n\nrunning...\n"))

            txt = await self._post_text(path)

            if self._ops_html:
                self._ops_html.set_content(self._highlight_ops_html(txt))
            ui.notify(f"{label}: done", type="positive")

            if clears_restart_hint:
                self._set_restart_needed(False)
        except Exception as e:
            if self._ops_html:
                self._ops_html.set_content(self._highlight_ops_html(f"== {label} ==\nerror: {e}\n"))
            ui.notify(f"{label}: error", type="negative")
        finally:
            self._set_ops_busy(False)

    async def op_compose_down(self) -> None:
        await self._run_op("Stop (docker compose down)", "/ops/compose/down", clears_restart_hint=False)

    async def op_compose_up(self) -> None:
        await self._run_op("Start (docker compose up -d)", "/ops/compose/up", clears_restart_hint=True)

    async def op_compose_recreate(self) -> None:
        await self._run_op("Recreate (up -d --force-recreate)", "/ops/compose/recreate", clears_restart_hint=True)

    async def op_compose_update(self) -> None:
        tag = str(self._tag_value or "").strip()
        qs = ("?tag=" + urllib.parse.quote(tag, safe="")) if tag else ""
        await self._run_op(f"Update (down + rm image:{tag or 'default'})", "/ops/compose/update" + qs, clears_restart_hint=True)

    # ---------- compose env editor ----------
    def _compose_env_add_row(self) -> None:
        self._compose_env_rows.append({"k": "", "v": "", "k_in": None, "v_in": None})
        self._render_compose_env_rows()

    def _render_compose_env_rows(self) -> None:
        if not self._compose_env_rows_container:
            return
        self._compose_env_rows_container.clear()

        with self._compose_env_rows_container:
            if not self._compose_env_rows:
                ui.html('<div style="opacity:.75; font-size:12px;">— no env vars —</div>')
                return

            for idx, row in enumerate(self._compose_env_rows):
                with ui.element("div").classes("az-editor-row"):
                    with ui.element("div").classes("az-editor-grid"):
                        k_in = ui.input(value=str(row.get("k", "")), placeholder="KEY").props("dense outlined")
                        v_in = ui.input(value=str(row.get("v", "")), placeholder="VALUE").props("dense outlined")

                        def make_rm(i: int):
                            def _rm():
                                if 0 <= i < len(self._compose_env_rows):
                                    self._compose_env_rows.pop(i)
                                    self._render_compose_env_rows()
                            return _rm

                        ui.button("✕", on_click=make_rm(idx)).props("unelevated color=negative")

                        row["k_in"] = k_in
                        row["v_in"] = v_in

    async def refresh_compose_env_editor(self) -> None:
        if self._compose_env_busy:
            return
        self._compose_env_busy = True
        try:
            data = await self._get_json("/compose/engine_env")
            env = data.get("environment") if isinstance(data, dict) else None
            if not isinstance(env, dict):
                env = {}
            items = [(str(k), "" if env.get(k) is None else str(env.get(k))) for k in sorted(env.keys())]
            self._compose_env_rows = [{"k": k, "v": v, "k_in": None, "v_in": None} for k, v in items]
            self._render_compose_env_rows()
        except Exception as e:
            self._compose_env_rows = [{"k": "error", "v": str(e), "k_in": None, "v_in": None}]
            self._render_compose_env_rows()
        finally:
            self._compose_env_busy = False

    async def save_compose_env_editor(self) -> None:
        if self._compose_env_busy:
            ui.notify("Compose editor busy", type="warning")
            return
        self._compose_env_busy = True
        try:
            env_out: Dict[str, str] = {}
            for row in self._compose_env_rows:
                k_in = row.get("k_in")
                v_in = row.get("v_in")
                k = (str(getattr(k_in, "value", row.get("k", ""))) or "").strip()
                v = str(getattr(v_in, "value", row.get("v", ""))) if v_in is not None else str(row.get("v", ""))
                if not k:
                    continue
                env_out[k] = v

            payload = {"environment": env_out, "env_format_prefer": self._compose_env_format}
            r = await self._post_json("/compose/engine_env", payload)

            if r.get("ok"):
                self._set_restart_needed(True)
                ui.notify("Saved. Restart required.", type="warning")
            else:
                ui.notify("Save failed", type="negative")
        except Exception as e:
            ui.notify(f"Save error: {e}", type="negative")
        finally:
            self._compose_env_busy = False

    # ---------- build ----------
    def build(self) -> None:
        ui.add_head_html(f"<style>{AZURA_CSS}</style>")
        ui.add_head_html(f"<script>{AZURA_JS}</script>")
        ui.page_title("AzurSmartMix Control")

        self._build_ops_dialog()

        # Header
        with ui.header().classes("az-topbar items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.label("azuracast").classes("az-brand text-xl")
                ui.label("AzurSmartMix Control").classes("az-sub text-sm")
                self._restart_badge = ui.html("").classes("ml-2")

            with ui.row().classes("items-center gap-2 az-opbtn"):
                self._tag_select = ui.select(
                    options=["latest", "beta1", "beta2", "rc", "dev"],
                    value=self._tag_value,
                    label="Tag",
                    on_change=self._on_tag_change,
                ).props("dense outlined").style("min-width: 140px;")

                ui.button("Start", on_click=self.op_compose_up).props("unelevated color=positive")
                ui.button("Stop", on_click=self.op_compose_down).props("unelevated color=negative")
                ui.button("Recreate", on_click=self.op_compose_recreate).props("unelevated color=warning")
                ui.button("Update", on_click=self.op_compose_update).props("outline")

        # Main
        with ui.element("div").classes("az-wrap"):
            with ui.element("div").classes("az-tabsbar"):
                # ✅ FIX: tabs as context manager -> QTab children are guaranteed under QTabs
                with ui.tabs() as tabs:
                    tab_dash = ui.tab("Dashboard")
                    tab_compose = ui.tab("Compose Env")

            # ✅ FIX: tab_panels bound to the same `tabs` object
            with ui.tab_panels(tabs, value=tab_dash).classes("w-full"):
                with ui.tab_panel(tab_dash):
                    # Ici je laisse volontairement minimal: tu peux recoller tes cartes existantes
                    ui.label("Dashboard (existing cards stay here)").style("opacity:.8;")

                    with ui.element("div").classes("az-card"):
                        with ui.element("div").classes("az-card-h"):
                            ui.label("Logs (quick check)")
                            ui.label("tail=40").classes("text-xs").style("opacity:.85;")
                        with ui.element("div").classes("az-card-b"):
                            tabs2 = ui.tabs().classes("w-full")
                            t_eng = ui.tab("engine")
                            t_sch = ui.tab("scheduler")
                            with ui.tab_panels(tabs2, value=t_eng).classes("w-full"):
                                with ui.tab_panel(t_eng):
                                    with ui.element("div").classes("console-frame").style("height:260px;"):
                                        self._log_html_engine = ui.html('<div class="console-content">—</div>')
                                with ui.tab_panel(t_sch):
                                    with ui.element("div").classes("console-frame").style("height:260px;"):
                                        self._log_html_sched = ui.html('<div class="console-content">—</div>')

                with ui.tab_panel(tab_compose):
                    with ui.element("div").classes("az-card").style("grid-column: 1 / -1;"):
                        with ui.element("div").classes("az-card-h"):
                            ui.label("Compose Env Editor")
                            ui.label(f"{self.settings.compose_service_engine} @ {self.settings.azuramix_compose_file}").classes("text-xs").style("opacity:.85;")
                        with ui.element("div").classes("az-card-b"):
                            with ui.element("div").classes("az-editor"):
                                with ui.element("div").classes("az-editor-h"):
                                    ui.label("Edit environment variables (engine)").style("font-weight: 950;")
                                    with ui.row().classes("items-center gap-2"):
                                        ui.button("Reload", on_click=self.refresh_compose_env_editor).props("outline")
                                        ui.button("Add", on_click=self._compose_env_add_row).props("outline")
                                        ui.button("Save", on_click=self.save_compose_env_editor).props("unelevated color=positive")

                                ui.label("Changes are written to docker-compose.yml. Restart/Recreate required to apply.").style(
                                    "font-size: 12px; opacity:.75; margin-bottom: 10px;"
                                )

                                self._compose_env_rows_container = ui.element("div").classes("az-list")

        # initial refresh
        ui.timer(0.1, self.refresh_compose_env_editor, once=True)
        ui.timer(0.2, self.refresh_logs_quick, once=True)

    async def refresh_logs_quick(self) -> None:
        try:
            eng = await self._get_text("/logs?service=engine&tail=40")
            if self._log_html_engine:
                self._log_html_engine.set_content(f'<div class="console-content">{html.escape(eng)}</div>')
        except Exception:
            if self._log_html_engine:
                self._log_html_engine.set_content('<div class="console-content">—</div>')

        try:
            sch = await self._get_text("/logs?service=scheduler&tail=40")
            if self._log_html_sched:
                self._log_html_sched.set_content(f'<div class="console-content">{html.escape(sch)}</div>')
        except Exception:
            if self._log_html_sched:
                self._log_html_sched.set_content('<div class="console-content">—</div>')
