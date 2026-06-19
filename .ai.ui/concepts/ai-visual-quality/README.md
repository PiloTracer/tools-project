# UIS-06 — AI visual quality

**Id:** UIS-06  
**Use when:** UI produced or heavily edited by an agent (Cursor, Copilot, etc.).

**Parallel:** Agent OS MOD-06 (`ai-amplification`) covers **architecture and module boundaries**; UIS-06 covers **anti-slop on AI UI**. Pair with **UIS-07** when craft tier ≥ refined.

**Prompt:** [`prompt.md`](prompt.md)

**Default:** Agent UI sessions are **AI-assisted: yes** unless human declares **`human-only`** in the same message.
