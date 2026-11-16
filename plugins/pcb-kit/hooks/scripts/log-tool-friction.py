#!/usr/bin/env python3
"""PostToolUse / PostToolUseFailure hook: record tool friction for later improvement of the tools.

Appends one JSON line per finding to <feedback dir>/auto/<date>_<session>.jsonl:
- tool_error: a Konnect tool failed or returned a structured error
- large_response: a Konnect tool answered with more than LARGE_RESPONSE_BYTES
- workaround_script: a Bash call ran pcbnew or kipy Python instead of a Konnect tool

The feedback dir is $PCB_FEEDBACK_DIR, default ~/Work/pcb-feedback (rules/05-tool-feedback.md).
Never blocks and never prints: any problem here is swallowed so the tool call is unaffected.
"""
import datetime
import json
import os
import re
import sys

LARGE_RESPONSE_BYTES = 10 * 1024
TRUNCATE = 600
KONNECT_PREFIX = "mcp__konnect__"
WORKAROUND_RE = re.compile(r"\b(import\s+pcbnew|from\s+pcbnew|import\s+kipy|from\s+kipy|pcbnew\.)")
PY_FILE_RE = re.compile(r"(?:^|\s)([^\s;|&<>'\"]+\.py)\b")


def response_text(resp):
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, list):
        return "\n".join(response_text(r) for r in resp)
    if isinstance(resp, dict):
        if "text" in resp and isinstance(resp["text"], str):
            return resp["text"]
        if "content" in resp:
            return response_text(resp["content"])
    return json.dumps(resp, ensure_ascii=False)


def structured_error(text):
    """Konnect errors ride in the text as {"message": ..., "error": {"kind": ...}}."""
    try:
        body = json.loads(text)
    except (ValueError, TypeError):
        return None
    if isinstance(body, dict) and isinstance(body.get("error"), dict) and "kind" in body["error"]:
        return body["error"]["kind"], str(body.get("message", ""))
    return None


def script_uses_pcbnew(cmd, cwd):
    if WORKAROUND_RE.search(cmd) or re.search(r"\bpcbnew\b", cmd):
        return True
    for path in PY_FILE_RE.findall(cmd):
        full = os.path.join(cwd or "", os.path.expanduser(path))
        try:
            with open(full, encoding="utf-8", errors="replace") as f:
                if WORKAROUND_RE.search(f.read(200_000)):
                    return True
        except OSError:
            continue
    return False


def main():
    d = json.load(sys.stdin)
    event = d.get("hook_event_name", "")
    tool = d.get("tool_name", "")
    tool_input = d.get("tool_input") or {}
    findings = []

    if tool.startswith(KONNECT_PREFIX):
        if event == "PostToolUseFailure":
            findings.append(("tool_error", None, str(d.get("error", ""))[:TRUNCATE]))
        else:
            text = response_text(d.get("tool_response"))
            err = structured_error(text)
            if err:
                findings.append(("tool_error", err[0], err[1][:TRUNCATE]))
            size = len(text.encode("utf-8"))
            if size > LARGE_RESPONSE_BYTES:
                findings.append(("large_response", None, f"{size} bytes"))
    elif tool == "Bash":
        cmd = tool_input.get("command", "")
        if script_uses_pcbnew(cmd, d.get("cwd")):
            detail = cmd[:TRUNCATE]
            if event == "PostToolUseFailure":
                detail = "FAILED: " + detail
            findings.append(("workaround_script", None, detail))

    if not findings:
        return

    root = os.path.expanduser(os.environ.get("PCB_FEEDBACK_DIR", "~/Work/pcb-feedback"))
    auto = os.path.join(root, "auto")
    os.makedirs(auto, exist_ok=True)
    now = datetime.datetime.now().astimezone()
    session = (d.get("session_id") or "nosession")[:8]
    path = os.path.join(auto, f"{now:%Y-%m-%d}_{session}.jsonl")
    input_json = json.dumps(tool_input, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        for kind, error_kind, detail in findings:
            f.write(json.dumps({
                "ts": now.isoformat(timespec="seconds"),
                "session": d.get("session_id"),
                "cwd": d.get("cwd"),
                "transcript": d.get("transcript_path"),
                "event": event,
                "kind": kind,
                "tool": tool[len(KONNECT_PREFIX):] if tool.startswith(KONNECT_PREFIX) else tool,
                "error_kind": error_kind,
                "detail": detail,
                "input": input_json[:TRUNCATE],
            }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
