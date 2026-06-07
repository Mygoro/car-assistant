# OTTO — 2-Minute Spoken Pitch (skeleton, scenario blanks)

**Context**: Setup day = final presentation. No slides, no timer. ~2 min spoken beside the booth. Tone matches the professor's value — *"don't buy an off-the-shelf solution; build the personal tool you actually need."* **English only.**
**How to fill**: Fill each `[[ ]]` with 1–2 spoken sentences once the scenario writer's output (persona + 3 core scenarios) is final. Conversational; read aloud to land in ~2 min.

---

### ① Hook — identity (~15s)
> "Hi. I wanted to build something the off-the-shelf car assistants — Bixby, Siri — simply can't do. So I made **OTTO: my own hands-free voice AI assistant for the car.**"

### ② What it is (~20s)
> "OTTO **listens through Discord, runs on my home server, and answers out loud.** No need to touch your phone — fully hands-free, while driving."
> (optional one-liner: stack — openwakeword · faster-whisper · Claude · ElevenLabs · MCP)

### ③ Differentiator — the Bixby one-two (~25s)
> "The difference is **composite queries, not single commands.** It weaves together your calendar, maps, lecture notes, and web search. For example —"
> `[[Scenario example 1 — one utterance chaining two sources. e.g. "When should I leave for tomorrow's meeting?" → calendar + predicted traffic]]`
> "Bixby would say 'here's your schedule' and make you look up directions separately. **OTTO reasons it into one answer.**"

### ④ Since the last update → to the finish (~40s)
> "Since my last update, the final stretch was three things.
> First, I **wired in real tools** — Google Calendar, Kakao Maps, Notion, and web search — through MCP and native tools.
> Second, I **injected my own context and tone** so it answers like *my* assistant, not a generic one.
> Third, I **cut the voice latency to about 3.4 seconds** from end-of-speech to first sound.
> And for this exhibition, I stripped out my personal data and replaced it with `[[persona one-liner]]` mock data so **anyone can try it themselves.**"

### ⑤ Demo invite (~15s)
> "Scan this QR with your phone to join on Discord and **talk to OTTO yourself.** The schedule and notes you'll see aren't real — they belong to a fictional student. Put on the earphones, **say 'Crank Otto,' then ask.** If it doesn't answer, just repeat the wake word clearly two or three times."
> `[[recommended opening utterance — same as the #start card]]`
> *(Wake word retained: "Crank Otto." English recognition for arbitrary speakers gets a final tuning pass; the "repeat 2–3×" line is the live fallback.)*

### ⑥ Closing — value (~15s)
> "In the end, this isn't built to be graded — **it's built because I actually want to use it.** Carrying my own way of working, my own context, inside my own tool — that's why I made OTTO. Thank you."

---
**Blanks to fill**
- [ ] `[[Scenario example 1]]` (③) — the single strongest two-source chaining moment
- [ ] `[[persona one-liner]]` (④)
- [ ] `[[recommended opening utterance]]` (⑤)
- [x] Wake word retained ("Crank Otto") — ⑤ line finalized with "repeat 2–3×" fallback; English recognition tuned in final pass
- [ ] Read aloud once and time it under 2 min
