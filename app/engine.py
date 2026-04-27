"""
ClipboardAI — Core Engine (fixed + Ollama support)
"""

import sys, json, os, threading, time, logging
from datetime import datetime
from pathlib import Path
from typing import Callable, List

import pyperclip, requests
from dotenv import load_dotenv, set_key
from pynput import keyboard

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).parent.parent.resolve()

CONFIG_PATH = BASE_DIR / "config.json"
ENV_PATH    = BASE_DIR / ".env"
LOG_PATH    = BASE_DIR / "log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("ClipboardAI")

# Suppress noisy third-party debug logs
for _noisy in ("httpx", "httpcore", "groq", "google", "PIL", "urllib3"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

DEFAULT_CONFIG = {
    "backend": "groq",
    "model": "llama-3.3-70b-versatile",
    "timeout_seconds": 30,
    "log_file": "log.txt",
    "hotkey_undo": "ctrl+alt+z",
    "start_minimized": False,
    "ollama_url": "http://localhost:11434",
    "modes": {
        "explain": {
            "hotkey": "ctrl+alt+space",
            "label": "Explain",
            "description": "Plain-language explanation",
            "prompt": "You are a brilliant teacher. Explain the following clearly and concisely, using simple language. Answer in the same language as the question.",
            "web_search": False,
        },
        "code": {
            "hotkey": "ctrl+alt+c",
            "label": "Code",
            "description": "Write production-ready code",
            "prompt": "You are an expert software engineer. Write clean, efficient code for the task below. Output ONLY the code and short inline comments.",
            "web_search": False,
        },
        "fix": {
            "hotkey": "ctrl+alt+f",
            "label": "Fix",
            "description": "Debug and fix code",
            "prompt": "You are an expert debugger. Find the bug(s) in the code or error below and return the FIXED code with a short comment above each change.",
            "web_search": False,
        },
        "translate": {
            "hotkey": "ctrl+alt+t",
            "label": "Translate",
            "description": "Translate to English",
            "prompt": "Translate the following to English. If a target language is specified, use that instead. Output ONLY the translated text.",
            "web_search": False,
        },
    },
}


class Engine:
    def __init__(self):
        self._callbacks: List[Callable] = []
        self._listener = None
        self._running = False
        self._lock = threading.Lock()
        self._prev_clipboard = ""
        self._ensure_config()
        self._reload_env()

    # ── Config ─────────────────────────────────────────────────────────────

    def _ensure_config(self):
        if not CONFIG_PATH.exists():
            self.save_config(DEFAULT_CONFIG)

    def load_config(self) -> dict:
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error("Failed to load config: %s", e)
            return dict(DEFAULT_CONFIG)

    def save_config(self, cfg: dict):
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        log.info("Config saved.")

    # ── Env / API Keys ─────────────────────────────────────────────────────

    def _reload_env(self):
        """Load .env from clipboard-app/ first; fall back to sibling copy-paste/ dir."""
        candidates = [
            BASE_DIR / ".env",
            BASE_DIR.parent / "copy-paste" / ".env",
        ]
        for path in candidates:
            if path.exists():
                load_dotenv(path, override=True)
                log.info("Loaded .env from %s", path)
                return
        log.warning(
            "No .env found. Searched: %s",
            ", ".join(str(p) for p in candidates)
        )

    def get_api_keys(self) -> dict:
        self._reload_env()
        return {
            "GEMINI_API_KEY":  os.getenv("GEMINI_API_KEY", ""),
            "GROQ_API_KEY":    os.getenv("GROQ_API_KEY", ""),
            "OPENAI_API_KEY":  os.getenv("OPENAI_API_KEY", ""),
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", ""),
        }

    def save_api_keys(self, keys: dict):
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        for k, v in keys.items():
            if v is not None:
                set_key(str(ENV_PATH), k, v)
        self._reload_env()
        log.info("API keys saved to .env")

    # ── Listener ───────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        try:
            cfg = self.load_config()
            hotkey_map = self._build_hotkey_map(cfg)
            self._listener = keyboard.GlobalHotKeys(hotkey_map)
            self._listener.start()
            self._running = True
            self._emit("started")
            log.info("Hotkey listener started.")
        except Exception as e:
            log.error("Failed to start listener: %s", e)
            self._emit("error", msg=f"Listener failed: {e}")

    def stop(self):
        if not self._running:
            return
        try:
            if self._listener:
                self._listener.stop()
                self._listener = None
        except Exception:
            pass
        self._running = False
        self._emit("stopped")
        log.info("Hotkey listener stopped.")

    def restart(self):
        self.stop()
        time.sleep(0.3)
        self.start()

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Hotkey map ─────────────────────────────────────────────────────────

    def _parse_hotkey(self, combo: str) -> str:
        parts = []
        for p in combo.lower().split("+"):
            p = p.strip()
            parts.append(p if len(p) == 1 else f"<{p}>")
        return "+".join(parts)

    def _build_hotkey_map(self, cfg: dict) -> dict:
        hmap = {}
        for mode_name, mcfg in cfg.get("modes", {}).items():
            raw = mcfg.get("hotkey", "")
            if not raw:
                continue
            key = self._parse_hotkey(raw)

            def make_cb(label=mcfg.get("label", mode_name), mc=dict(mcfg)):
                def _cb():
                    threading.Thread(
                        target=self._process_clipboard, args=(label, mc), daemon=True
                    ).start()
                return _cb

            hmap[key] = make_cb()
            log.debug("Registered hotkey %s -> %s", key, mode_name)

        undo_raw = cfg.get("hotkey_undo", "ctrl+alt+z")
        hmap[self._parse_hotkey(undo_raw)] = lambda: threading.Thread(
            target=self._restore_clipboard, daemon=True
        ).start()
        return hmap

    # ── Clipboard pipeline ─────────────────────────────────────────────────

    def _process_clipboard(self, mode_label: str, mode_cfg: dict):
        if not self._lock.acquire(blocking=False):
            log.warning("Already processing — ignoring duplicate.")
            return
        try:
            user_text = pyperclip.paste() or ""
            if not user_text.strip():
                self._emit("log", msg=f"[{mode_label}] Clipboard empty.")
                return

            self._prev_clipboard = user_text
            self._emit("processing", mode=mode_label, chars=len(user_text))
            log.info("[%s] Processing %d chars.", mode_label, len(user_text))

            system_prompt = mode_cfg.get("prompt", "Answer concisely.")

            # Optional web search
            search_ctx = ""
            if mode_cfg.get("web_search", False):
                self._emit("log", msg=f"[{mode_label}] Searching web...")
                search_ctx = self._web_search(
                    user_text,
                    mode_cfg.get("search_suffix", "solution"),
                    mode_cfg.get("search_sites"),
                    mode_cfg.get("search_results", 5),
                )

            full_text = user_text
            if search_ctx:
                full_text = (
                    f"{user_text}\n\n{search_ctx}\n\n"
                    "Using the above search results as context, give the best answer."
                )

            start = time.time()
            answer = self._ask_ai(full_text, system_prompt)
            elapsed = time.time() - start

            pyperclip.copy(answer)
            self._emit("done", mode=mode_label, elapsed=elapsed, chars=len(answer))
            self._write_log(mode_label, user_text, search_ctx, answer, elapsed)

        except Exception as exc:
            log.error("Pipeline error: %s", exc, exc_info=True)
            self._emit("error", mode=mode_label, msg=str(exc))
        finally:
            self._lock.release()

    def _restore_clipboard(self):
        if not self._prev_clipboard:
            self._emit("log", msg="Nothing to undo.")
            return
        pyperclip.copy(self._prev_clipboard)
        self._emit("log", msg="Clipboard restored (undo).")
        self._prev_clipboard = ""

    # ── AI dispatch ────────────────────────────────────────────────────────

    def _ask_ai(self, user_text: str, system_prompt: str) -> str:
        self._reload_env()
        cfg = self.load_config()
        primary = cfg.get("backend", "groq").lower()

        backends = {
            "gemini": self._call_gemini,
            "groq":   self._call_groq,
            "openai": self._call_openai,
            "ollama": self._call_ollama,
        }

        order = [primary] + [b for b in backends if b != primary]
        last_err = None
        for name in order:
            fn = backends.get(name)
            if not fn:
                continue
            try:
                log.info("Trying backend: %s", name)
                result = fn(user_text, system_prompt, cfg)
                log.info("Backend '%s' succeeded.", name)
                return result
            except Exception as exc:
                log.warning("Backend '%s' failed: %s", name, exc)
                last_err = exc
                # Only try primary; don't auto-fallback to avoid confusion
                break

        raise RuntimeError(f"Backend '{primary}' failed: {last_err}")

    def _call_gemini(self, user_text, system_prompt, cfg):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError("google-genai not installed. Run: pip install google-genai")
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing from .env")
        client = genai.Client(api_key=api_key)
        model = cfg.get("model", "gemini-2.0-flash")
        resp = client.models.generate_content(
            model=model,
            contents=user_text,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return resp.text.strip()

    def _call_groq(self, user_text, system_prompt, cfg):
        try:
            from groq import Groq
        except ImportError:
            raise RuntimeError("groq not installed. Run: pip install groq")
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY missing from .env — add it in the API Keys tab")
        client = Groq(api_key=api_key)
        model = cfg.get("model", "llama-3.3-70b-versatile")
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_text},
            ],
            timeout=cfg.get("timeout_seconds", 30),
        )
        return r.choices[0].message.content.strip()

    def _call_openai(self, user_text, system_prompt, cfg):
        api_key  = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model    = cfg.get("model", "gpt-4o-mini")
        if not api_key:
            raise ValueError("OPENAI_API_KEY missing from .env")
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_text},
            ]},
            timeout=cfg.get("timeout_seconds", 30),
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _call_ollama(self, user_text, system_prompt, cfg):
        """Call local Ollama via its native API."""
        base_url = cfg.get("ollama_url", "http://localhost:11434").rstrip("/")
        model    = cfg.get("model", "llama3.2")
        log.info("Calling Ollama at %s model=%s", base_url, model)
        resp = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_text},
                ],
                "stream": False,
            },
            timeout=cfg.get("timeout_seconds", 120),
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"].strip()

    def get_ollama_models(self, base_url: str = "") -> list:
        """Fetch installed Ollama models. Returns list of model name strings."""
        cfg = self.load_config()
        url = (base_url or cfg.get("ollama_url", "http://localhost:11434")).rstrip("/")
        try:
            resp = requests.get(f"{url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as exc:
            log.warning("Ollama model discovery failed: %s", exc)
            return []

    # ── Web search ─────────────────────────────────────────────────────────

    def _web_search(self, user_text, suffix, sites, max_results) -> str:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            query = user_text.strip().split("\n")[0][:120] + " " + suffix
            if sites:
                query += " " + " ".join(sites[:3])
            lines = ["\n=== WEB SEARCH RESULTS ==="]
            with DDGS() as ddgs:
                for i, r in enumerate(ddgs.text(query, max_results=max_results), 1):
                    lines.append(f"[{i}] {r.get('title','')}\n    {r.get('body','')[:400]}")
            lines.append("=== END ===\n")
            return "\n".join(lines)
        except Exception as exc:
            log.warning("Web search failed (non-fatal): %s", exc)
            return ""

    # ── Log file ───────────────────────────────────────────────────────────

    def _write_log(self, mode, query, search_ctx, response, elapsed):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        searched = "(+web)" if search_ctx else ""
        entry = (
            f"\n{'─'*60}\n"
            f"[{ts}] MODE: {mode} {searched} ({elapsed:.2f}s)\n"
            f"QUERY:\n{query}\n\nRESPONSE:\n{response}\n"
        )
        try:
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            log.error("Failed to write log: %s", e)

    def get_log_text(self) -> str:
        try:
            return LOG_PATH.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def clear_log(self):
        try:
            LOG_PATH.write_text("", encoding="utf-8")
        except Exception:
            pass

    # ── Events ─────────────────────────────────────────────────────────────

    def add_callback(self, cb: Callable):
        self._callbacks.append(cb)

    def _emit(self, event: str, **kwargs):
        for cb in self._callbacks:
            try:
                cb(event, **kwargs)
            except Exception:
                pass
