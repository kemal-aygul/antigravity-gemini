# antigravity-gemini

Use Google Antigravity's Gemini models and agents as subagents inside [Claude Code](https://claude.com/claude-code).

Claude stays the orchestrator. When you want a Gemini model to do part of the work (a second opinion, a review, research, a calculation), Claude hands that task to the Antigravity CLI (`agy`) on your own machine and gets the result back. Every user signs in with their own Google account; nothing is shared between users.

*Türkçe özet aşağıda.*

## What's inside

| Part | What it does |
|---|---|
| MCP server `antigravity` | Wraps the local `agy` CLI with four tools: `list_antigravity_models`, `list_antigravity_agents`, `run_antigravity_agent`, `get_antigravity_usage` (remaining quota) |
| Subagent `antigravity` | A light wrapper that delegates a task to Antigravity and returns a compact handoff |
| Subagents `gemini-neon`, `gemini-carbon`, `gemini-hydrogen`, `gemini-argon` | One subagent per Gemini 4 family. Their descriptions carry capability and cost figures, so Claude can pick the right one by task difficulty |
| Skill `gemini-delegate` | Tells Claude when and how to delegate, and which Gemini model/effort to choose |
| Command `/antigravity-gemini:setup` | Checks the requirements and installs the missing ones after you confirm |
| Command `/antigravity-gemini:agy-check` | Checks the whole setup end to end with a real Gemini call |
| Start-up check | At each Claude Code start, tells Claude if a requirement is missing (silent when all is well) |

## Requirements

Full list with official install commands: [REQUIREMENTS.md](plugins/antigravity-gemini/REQUIREMENTS.md). In short:

1. **Claude Code** and **Git**
2. **uv**: starts the MCP server and installs Python and its dependency by itself
3. **Antigravity CLI (`agy`)**
4. **Sign-in to Antigravity**, which only you can do: run `agy` once in a terminal

`/antigravity-gemini:setup` installs 2 and 3 for you (it asks first) and walks you through 4.

## Install

**Easiest:** paste the prompt from [INSTALL-PROMPT.md](INSTALL-PROMPT.md) into a new Claude Code session; Claude installs and checks everything, asking you before each install.

Or by hand, in Claude Code:

```
/plugin marketplace add kemal-aygul/antigravity-gemini
/plugin install antigravity-gemini@antigravity-gemini
/antigravity-gemini:setup
```

Restart Claude Code when setup asks you to, then run:

```
/antigravity-gemini:agy-check
```

## Use

Just ask Claude, for example:

- "Ask Gemini (hydrogen, medium) to review this function."
- "Get a second opinion from Gemini on this plan."
- "Run these three checks in parallel on Gemini 4 Neon."
- "List the Antigravity models I can use."
- "How much Gemini quota do I have left?"

## Model notes

Gemini 4 model IDs look like `gemini-4-<family>-<effort>` (families: Hydrogen, Neon, Argon, Carbon). The exact list depends on your account; Claude checks it with `list_antigravity_models`. See [the skill](plugins/antigravity-gemini/skills/gemini-delegate/SKILL.md) for each family's capability, cost and best use, with Claude models on the same benchmark for comparison.

Gemini 4 Argon and Gemini 3.8 Flash are removed from Antigravity on 2026-11-30; the `gemini-argon` subagent stops working then.

Plans: Hydrogen works on every Google AI plan, including Free; Neon and Carbon need a paid Google AI Pro or Ultra plan (Neon is also on Gemini Enterprise). Google Workspace accounts do not include Antigravity; sign in with a personal Google account or a Google Cloud project.

## Safety

By default Gemini runs with Antigravity's sandbox on and without permission to edit files. Claude turns on file editing only when you ask for it.

## Update / remove

Update, then restart Claude Code so the new version loads:

```
/plugin marketplace update antigravity-gemini
/plugin update antigravity-gemini@antigravity-gemini
```

Remove:

```
/plugin uninstall antigravity-gemini@antigravity-gemini
```

---

## Türkçe özet

Bu plugin, Claude Code içinden Google Antigravity'deki Gemini modellerini ve ajanlarını alt ajan olarak kullanmanızı sağlar. Her kullanıcı kendi Google hesabıyla giriş yapar.

**Gerekenler:** Git, uv, Antigravity CLI (`agy`) ve Antigravity'ye giriş (kişisel Google hesabı ya da Google Cloud projesi; Google Workspace hesapları Antigravity'yi kapsamaz). Tam liste ve resmî kurulum komutları [REQUIREMENTS.md](plugins/antigravity-gemini/REQUIREMENTS.md) dosyasında.

**En kolay yol:** [INSTALL-PROMPT.md](INSTALL-PROMPT.md) dosyasındaki promptu yeni bir Claude Code oturumuna yapıştırın; Claude her kurulumdan önce onay alarak her şeyi kurar ve kontrol eder.

**Elle kurulum (Claude Code içinde):**

```
/plugin marketplace add kemal-aygul/antigravity-gemini
/plugin install antigravity-gemini@antigravity-gemini
/antigravity-gemini:setup
```

`setup` komutu eksikleri bulur, onayınızı alıp Git, uv ve `agy`'yi kurar. Girişi siz yaparsınız: terminalde bir kez `agy` çalıştırın. Ardından Claude Code'u yeniden başlatıp `/antigravity-gemini:agy-check` ile test edin. Sonra Claude'a "Bu fonksiyonu Gemini'ye inceletir misin?" gibi isteklerde bulunabilirsiniz. Kalan Gemini kotanızı görmek için "Gemini kotam ne durumda?" diye sorabilirsiniz. Güncellemek için `/plugin marketplace update antigravity-gemini` ve `/plugin update antigravity-gemini@antigravity-gemini` komutlarını çalıştırıp Claude Code'u yeniden başlatın.

**Alt ajanlar:** Her Gemini 4 ailesi için bir alt ajan gelir: `gemini-neon` (zor işler), `gemini-carbon` (Neon'a alternatif), `gemini-hydrogen` (hızlı ve rutin işler) ve `gemini-argon` (30 Kasım 2026'da kaldırılıyor). Hydrogen tüm planlarda (ücretsiz dahil) çalışır; Neon ve Carbon için ücretli Google AI Pro veya Ultra gerekir (Neon, Gemini Enterprise'da da var). Açıklamalarında yetenek ve maliyet bilgisi olduğu için Claude, işin zorluğuna göre uygun olanı seçebilir.

## Changes

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
