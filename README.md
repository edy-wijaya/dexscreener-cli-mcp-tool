# Dexscreener Unofficial CLI + MCP + Skills

![Dexscreener CLI Screenshot](assets/screenshot.png)

**100% free to use.** All APIs included are public and free - no API keys required to get started. Optional Moralis key unlocks holder data.

A visual terminal scanner, MCP server, and AI skill for Dexscreener token signals. **Unofficial** - not affiliated with or endorsed by Dexscreener.

Scans hot tokens across Solana, Base, Ethereum, BSC, and Arbitrum. Scores them by volume, liquidity, momentum, and flow pressure. Use it from the terminal, connect it to AI agents via MCP, or load it as a skill in Claude/Codex/OpenClaw.

**Free APIs used:**
- [Dexscreener API](https://docs.dexscreener.com/) - token data, pairs, profiles, boosts
- [GeckoTerminal API](https://www.geckoterminal.com/) - trending pools, new tokens
- [Blockscout API](https://docs.blockscout.com/) - holder counts (Base chain)
- [Honeypot.is API](https://honeypot.is/) - holder counts (Solana, ETH, BSC)
- [Moralis API](https://moralis.io/) - holder counts (optional, requires free key)

---

## Quick Install

You need **Python 3.11+** and **Git** installed. Then follow these 3 steps:

### Step 1: Clone the repo

Open a terminal (Command Prompt, PowerShell, or Terminal) and paste this:

```bash
git clone https://github.com/vibeforge1111/dexscreener-cli-mcp-tool.git
cd dexscreener-cli-mcp-tool
```

### Step 2: Run the installer

**Windows** - paste this in the same terminal:
```
install.bat
```

**Mac / Linux** - paste this instead:
```bash
chmod +x install.sh && ./install.sh
```

This creates a virtual environment and installs everything. Takes about 30 seconds.

<details>
<summary>Manual install (if the script doesn't work)</summary>

```bash
python -m venv .venv
```

Activate the environment:
```bash
# Mac / Linux:
source .venv/bin/activate

# Windows Command Prompt:
.venv\Scripts\activate.bat

# Windows PowerShell:
.venv\Scripts\Activate.ps1
```

Then install:
```bash
pip install -e .
```
</details>

### Step 3: Run your first scan

```bash
ds setup       # 5-question wizard - picks your chains, style, and filters
ds hot         # Scan hot tokens with your settings
```

That's it. The setup wizard saves your choices and auto-loads them on every scan.

---

## Commands

### One-Shot Scans

| Command | What it does |
|---------|-------------|
| `ds hot` | Scan hot tokens across your configured chains |
| `ds search <query>` | Search tokens by name, symbol, or address |
| `ds top-new` | Top new tokens by 24h volume |
| `ds new-runners` | Fresh token runners with momentum scoring |
| `ds alpha-drops` | Alpha-grade new drops with breakout scoring |
| `ds ai-top` | AI-themed token leaderboard |
| `ds inspect <address>` | Deep-dive on a specific token |

### Real-Time Live Dashboards

These run continuously and auto-refresh every few seconds. Press `Ctrl+C` to stop.

| Command | What it does |
|---------|-------------|
| `ds watch` | Live hot runner board - refreshes every 7s |
| `ds new-runners-watch` | Live new runner tracker with keyboard chain switching |
| `ds alpha-drops-watch` | Live alpha drop scanner with built-in alerts |

All live modes support `--interval` to set refresh speed and `--limit` to control how many tokens show.

### Custom Scan Profiles

Create your own scan profiles with any combination of chains and filters. They persist across sessions.

```bash
# Create a custom profile
ds preset save my-degen --chains solana,base --limit 15 --min-liquidity-usd 8000 --min-txns-h1 5

# Use it in any scan
ds hot --preset my-degen
ds watch --preset my-degen

# List / inspect / delete profiles
ds preset list
ds preset show my-degen
ds preset delete my-degen
```

The 3 built-in profiles (strict / balanced / discovery) are always available. Your custom profiles sit on top.

### Setup & Maintenance

| Command | What it does |
|---------|-------------|
| `ds setup` | Interactive wizard - builds a "default" profile from 5 questions |
| `ds doctor` | Diagnose issues and verify your setup |
| `ds update` | Pull latest code and reinstall |
| `ds profiles` | Show built-in filter thresholds per chain |

### Tasks & Alerts

Set up automated scans that run on a schedule and alert you via Discord, Telegram, or webhooks.

| Command | What it does |
|---------|-------------|
| `ds task create <name>` | Create a scheduled scan task |
| `ds task list` | List all tasks |
| `ds task run <name>` | Run a task once |
| `ds task daemon` | Run scheduler for all due tasks |
| `ds task configure <name>` | Add alerts (Discord, Telegram, webhook) |
| `ds task test-alert <name>` | Send a test alert |

### Output

Add `--json` to any scan command for machine-readable JSON output.

```bash
ds hot --json
ds search pepe --json
```

---

## What Can I Do With This?

### "I just want to see what's hot right now"

```bash
ds hot
```

Shows the top trending tokens across all chains, scored and ranked. Done.

### "I only care about Solana"

```bash
ds hot --chains solana --limit 10
```

### "Show me tokens on Base too"

```bash
ds hot --chains solana,base --limit 15
```

### "I want a live feed that updates automatically"

```bash
ds watch --chains solana,base --interval 5
```

This refreshes every 5 seconds. Press `Ctrl+C` to stop.

### "Show me brand new tokens that just launched"

```bash
ds new-runners --chain solana
ds top-new --chain base
```

### "I want a live feed of new launches only"

```bash
ds new-runners-watch --chain solana --interval 6
```

### "Find me alpha - new drops with breakout potential"

```bash
ds alpha-drops --chains solana,base
```

Or live with auto-refresh:
```bash
ds alpha-drops-watch --chains solana,base
```

### "Search for a specific token"

```bash
ds search pepe
ds search 0x6982508145454ce325ddbe47a25d4ec3d2311933    # by address
```

### "I found a token, give me everything on it"

```bash
ds inspect So11111111111111111111111111111111111111112 --chain solana
```

### "I want to filter differently than the defaults"

Save your own profile and reuse it everywhere:

```bash
ds preset save my-degen --chains solana,base --limit 20 --min-liquidity-usd 5000 --min-txns-h1 3

ds hot --preset my-degen
ds watch --preset my-degen
```

### "Alert me on Discord when something hot appears"

```bash
# 1. Save your filter profile
ds preset save scout --chains solana --limit 10 --min-liquidity-usd 10000

# 2. Create a task that scans every 60 seconds
ds task create my-alerts --preset scout --interval-seconds 60

# 3. Add your Discord webhook
ds task configure my-alerts --discord-webhook-url https://discord.com/api/webhooks/YOUR/WEBHOOK

# 4. Test it
ds task test-alert my-alerts

# 5. Start the scanner
ds task daemon --all
```

Works the same with Telegram:
```bash
ds task configure my-alerts --telegram-bot-token YOUR_BOT_TOKEN --telegram-chat-id YOUR_CHAT_ID
```

### "I want JSON output for my own scripts"

```bash
ds hot --json
ds search pepe --json
ds hot --chains solana --limit 5 --json > tokens.json
```

### "I want an AI agent to use this"

Start the MCP server and connect it to Claude, Codex, or any MCP-compatible agent:
```bash
dexscreener-mcp
```

Then ask in natural language: "What's hot on Solana?" or "Find new tokens on Base with high volume."

---

## MCP Server

The MCP server exposes all scanning functionality to AI agents (Claude, Codex, etc.).

### Start the server

```bash
dexscreener-mcp
```

### Claude Desktop config

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dexscreener": {
      "command": "path/to/dexscreener-cli-mcp-tool/.venv/Scripts/dexscreener-mcp",
      "args": []
    }
  }
}
```

On Mac/Linux use `.venv/bin/dexscreener-mcp` instead.

### MCP Tools

| Tool | Description |
|------|-------------|
| `scan_hot_tokens` | Scan and rank hot tokens by chain with scoring |
| `search_pairs` | Search Dexscreener pairs by name/symbol/address |
| `inspect_token` | Deep-dive on a token with concentration proxies |
| `save_preset` | Save a named scan preset |
| `list_presets` | List all saved presets |
| `create_task` | Create a scheduled scan task with alerts |
| `list_tasks` | List all scan tasks |
| `run_task_scan` | Run a task scan and return ranked results |
| `run_due_tasks` | Run one scheduler cycle for all due tasks |
| `test_task_alert` | Send a test alert through task channels |
| `list_task_runs` | List task run history |
| `export_state_bundle` | Export all presets/tasks/runs as JSON |
| `import_state_bundle` | Import a state bundle |
| `get_rate_budget_stats` | Get API rate limit and budget stats |

### MCP Resources

| URI | Content |
|-----|---------|
| `dexscreener://profiles` | Available scan profiles with thresholds |
| `dexscreener://presets` | Saved scan presets |
| `dexscreener://tasks` | Saved scan tasks |

### MCP Prompts

| Prompt | Purpose |
|--------|---------|
| `alpha_scan_plan` | Generate an execution-ready scan plan |
| `runner_triage` | Triage a token candidate for momentum trading |

---

## AI Skill Usage

This tool works as a skill for AI coding agents. Load the `SKILL.md` file to teach any agent how to use the CLI and MCP tools with natural language.

**Example natural language queries an agent can handle:**
- "What are the hottest tokens on Solana right now?"
- "Find me new tokens on Base with high volume"
- "Set up a scan task with Discord alerts for Solana alpha"
- "Search for pepe tokens and show me the top results"
- "What's the liquidity and volume for this token address?"

See `SKILL.md` for the full skill specification.

---

## APIs & Data Sources

Everything works out of the box with zero API keys. You can optionally add keys to unlock more data.

### What's included for free (no keys needed)

| API | What it provides | Rate Limit |
|-----|-----------------|------------|
| [Dexscreener](https://docs.dexscreener.com/) | All token/pair data, prices, volume, liquidity, boosts, profiles | 60-300 rpm |
| [GeckoTerminal](https://www.geckoterminal.com/) | Holder counts, trending pools, new token discovery | Free tier |
| [Blockscout](https://docs.blockscout.com/) | Holder counts for Ethereum and Base | Unlimited |
| [Honeypot.is](https://honeypot.is/) | Holder counts for all EVM chains | Free tier |

### Optional APIs you can add

| API | What it unlocks | How to get a key | Cost |
|-----|----------------|-----------------|------|
| [Moralis](https://moralis.io/) | Better holder data for all chains (EVM + Solana) | Sign up at moralis.io | Free tier available (40K requests/month) |

To add an optional key, create a `.env` file in the project root:
```
MORALIS_API_KEY=your_key_here
```

### Holder data coverage per chain

The scanner tries multiple providers in order until it gets a result:

| Chain | GeckoTerminal | Moralis (optional) | Blockscout | Honeypot.is |
|-------|:---:|:---:|:---:|:---:|
| **Solana** | yes | yes (with key) | - | - |
| **Ethereum** | yes | yes (with key) | yes | yes |
| **Base** | yes | yes (with key) | yes | yes |
| **BSC** | yes | yes (with key) | - | yes |
| **Arbitrum** | yes | yes (with key) | - | yes |
| **Polygon** | yes | yes (with key) | - | yes |
| **Optimism** | yes | yes (with key) | - | yes |
| **Avalanche** | yes | yes (with key) | - | yes |

Without any API keys, you still get holder counts on every chain through GeckoTerminal, Blockscout, and Honeypot.is. Adding a Moralis key gives you a more reliable fallback.

### How rate limiting works

Dexscreener enforces:
- **60 rpm** for token profiles, boosts, orders
- **300 rpm** for search, pairs, token-pairs

The scanner handles this automatically with separate rate-limit buckets, 20-second caching, and retry/backoff. Holder data is cached for 15 minutes. You don't need to worry about hitting limits.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MORALIS_API_KEY` | No | Enables Moralis holder data (free tier: 40K req/month) |
| `DS_TABLE_MODE` | No | Set to `compact` for narrow terminals |
| `DS_TABLE_WIDTH` | No | Override auto-detected terminal width |

---

## Scan Profiles

Three built-in filter profiles, applied with chain-specific multipliers:

| Profile | Min Liquidity | Min 24h Volume | Min Txns/h | Good for |
|---------|--------------|----------------|------------|----------|
| **discovery** | $8,000 | $10,000 | 5 | Finding early gems, degen plays, micro-caps |
| **balanced** | $20,000 | $40,000 | 25 | General scanning, mix of safety and opportunity |
| **strict** | $35,000 | $90,000 | 50 | Established tokens only, blue-chip filtering |

Use `ds profiles --chains solana,base` to see chain-adjusted values.

You can also create your own profiles with `ds preset save` (see [Custom Scan Profiles](#custom-scan-profiles) above).

---

## How Scoring Works

Each token gets a 0-100 score based on 8 weighted components:

| Component | What it measures |
|-----------|-----------------|
| **Volume velocity** | How fast trading volume is growing |
| **Transaction velocity** | Rate of transaction count increase |
| **Relative strength** | Performance compared to the chain average |
| **Breakout readiness** | Price compression patterns (coiling before a move) |
| **Boost velocity** | Rate of Dexscreener boost activity |
| **Momentum decay** | Whether momentum is sustaining or fading |
| **Liquidity depth** | Health and depth of the liquidity pool |
| **Flow pressure** | Buy vs sell transaction imbalance |

**What the scores mean:** 80+ = very hot, 60-80 = interesting, 40-60 = moderate, below 40 = weak

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No tokens found | Lower filters: `--min-liquidity-usd 10000 --min-txns-h1 5` |
| Only Solana results | Expected when Solana dominates Dexscreener boosts. Try `--chains base` |
| Unicode garbled | Run `chcp 65001` (Windows) or use a modern terminal |
| Import errors | Run `ds doctor` then `ds update` |
| API timeouts | Check internet, run `ds doctor` to verify API connectivity |

Run `ds doctor` anytime to check your setup.

---

## Updating

```bash
ds update
```

Or manually:
```bash
git pull
pip install -e .
```

---

## Project Structure

```
dexscreener_cli/
  cli.py          - All CLI commands (Typer)
  ui.py           - Terminal rendering (Rich)
  scanner.py      - Token discovery and scanning
  scoring.py      - 8-component scoring engine
  models.py       - Data models (PairSnapshot, HotTokenCandidate)
  holders.py      - Multi-provider holder count fetching
  client.py       - Dexscreener API client with rate limiting
  config.py       - Constants and filter defaults
  state.py        - Preset/task persistence (JSON files)
  mcp_server.py   - MCP server exposing all tools
  alerts.py       - Discord/Telegram/webhook alerts
  task_runner.py   - Task execution and scheduling
  watch_controls.py - Keyboard controls for live mode
```

---

## License

MIT
