# Claude Code ile kurulum promptu

Bu dosya, **antigravity-gemini** plugin'ini Claude Code'a kendi kendine kurdurmak için hazırlandı. Plugin, Claude Code içinden Google Antigravity'deki Gemini modellerini alt ajan olarak kullanmanızı sağlar.

## Nasıl kullanılır

1. Claude Code'da yeni bir oturum açın (masaüstü uygulaması ya da terminal fark etmez).
2. Aşağıdaki **kutunun içindeki metnin tamamını** kopyalayıp ilk mesaj olarak gönderin.
3. Claude sizden onay istediğinde okuyup onaylayın. Antigravity'ye girişi **siz** yapacaksınız: Claude terminalde `agy` çalıştırmanızı isteyecek, açılan tarayıcıda Google hesabınızla giriş yapacaksınız.
4. Claude söylediğinde Claude Code'u tamamen kapatıp açın ve son kontrolü yaptırın.

Gerekenler: Google hesabı (Antigravity'nin Free, Pro veya Ultra planı; Google Workspace planları Antigravity'yi kapsamaz) ve internet bağlantısı. Git, uv ve Antigravity CLI eksikse Claude onayınızla kurar.

Kaynak: https://github.com/kemal-aygul/antigravity-gemini

---

## Prompt

````text
Install and set up the Claude Code plugin "antigravity-gemini" on this machine for me.
Source: https://github.com/kemal-aygul/antigravity-gemini (public). It lets Claude Code
delegate tasks to Gemini models through the local Google Antigravity CLI (agy).
Talk to me in the language I write in. Work step by step and tell me what each step did.

Rules
- Ask me before installing any software, and before changing any Claude Code setting.
- Use only these official installers; never other mirrors or community packages:
  - uv: Windows PowerShell `irm https://astral.sh/uv/install.ps1 | iex`,
        macOS/Linux `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - agy: Windows PowerShell `irm https://antigravity.google/cli/install.ps1 | iex`,
         macOS/Linux `curl -fsSL https://antigravity.google/cli/install.sh | bash`
  - git: Windows `winget install --id Git.Git -e --source winget`, macOS `xcode-select --install`,
         Linux the distribution's package manager.
  On Windows run PowerShell commands as
  `powershell -NoProfile -ExecutionPolicy Bypass -Command "..."`.
- Never sign in for me, and never ask for, type or store a password or API key.
  The Antigravity sign-in is mine to do.
- If a step fails, show me the error and stop; don't try workarounds I haven't approved.

Steps
1. Find the Claude Code CLI: `claude` on PATH, else `~/.local/bin/claude` (`claude.exe` on Windows).
   Print its version.
2. Install the plugin with the CLI:
     claude plugin marketplace add kemal-aygul/antigravity-gemini
     claude plugin install antigravity-gemini@antigravity-gemini --scope user
   If the CLI can't be found or these fail, ask me to type these in Claude Code instead
   and wait for me:
     /plugin marketplace add kemal-aygul/antigravity-gemini
     /plugin install antigravity-gemini@antigravity-gemini
3. Locate the installed plugin folder:
   `~/.claude/plugins/cache/antigravity-gemini/antigravity-gemini/<newest version>/`.
   Read its REQUIREMENTS.md. It is the full list of what the plugin needs.
4. Run the requirement check: `bash "<plugin folder>/scripts/check-prereqs.sh"`.
   Each line reads `<STATUS> <id> <detail>`. Show me the result as a table.
5. For each MISSING item among git, uv, agy (in that order): show me the official command
   above for my OS, wait for my OK, run it, and show the result.
6. If `signin` is MISSING: ask me to open a terminal, run `agy`, finish the browser sign-in,
   and tell you when I'm done. Then run the check again until all four lines are OK.
   A WARN saying uv or agy is "not on PATH" right after installing is expected.
7. Prepare the MCP server so its first start doesn't time out. Run this once with uv (full path
   if uv isn't on PATH yet); it downloads Python and the `mcp` package, then exits:
     uv run --quiet --script "<plugin folder>/server/server.py" < /dev/null
8. If `claude mcp list` works, run it and confirm the line for
   `plugin:antigravity-gemini:antigravity` says Connected.
   If an older, hand-made Antigravity MCP server or a `~/.claude/agents/antigravity.md`
   exists, tell me: it duplicates the plugin's tools and agent. Don't remove it without my OK.
9. Finish with a table: what was already there, what you installed, what I still need to do.
   Then tell me to quit Claude Code completely, reopen it, and in a new session run
     /antigravity-gemini:agy-check
   That command makes one real Gemini call to prove everything works.
````

---

## Kurulumdan sonra

Yeni bir oturumda Claude'a doğal dille iş verebilirsiniz, örneğin:

- "Bu fonksiyonu Gemini'ye (hydrogen, medium) inceletir misin?"
- "Bu plan için Gemini'den ikinci görüş al."
- "Kullanabildiğim Antigravity modellerini listele."

Sorun çıkarsa `/antigravity-gemini:setup` komutu gereksinimleri yeniden kontrol eder ve eksikleri onayınızla kurar.
