# GitHub Copilot Toolbox — MCP & Skills awareness

_Generated: 2026-11-06T16:43:20.459Z_

## How to use this report

- **Saved copy:** This file is **`.github/copilot-toolbox-mcp-skills-awareness.md`** — refreshed whenever the toolbox runs an MCP & Skills scan (including on workspace open when auto-scan is enabled). It is meant for **Copilot workspace context** together with `.github/copilot-instructions.md` (which gets a shorter replaceable summary when auto-merge is on).
- **MCP:** Lists **configured** servers from `mcp.json`. **Live tool use** still requires **Copilot Chat → Agent** with those servers **trusted/started** in the MCP tools UI.
- **Skills:** **On-disk** folders with `SKILL.md`. Copilot does not auto-load them; attach `SKILL.md` or paths in chat when useful.
- **Task routing:** When the user’s request matches a server’s purpose (e.g. Confluence → Confluence/Atlassian MCP), prefer that **server id** from the tables below.

---

## MCP — workspace

Workspace `mcp.json` _(folder: animeApps)_

- **c:\Users\Ajmal Khan\Desktop\animeApps\.vscode\mcp.json** — _File missing_

_No active workspace servers in mcp.json._

## MCP — user profile

- **C:\Users\Ajmal Khan\AppData\Roaming\Code\User\mcp.json** — _File missing_

_No active user-scoped servers in mcp.json._

## Skills (local `SKILL.md` folders)

### Project-scoped

_None found (or no workspace open)._

### User-scoped

- **audit-hosting** — `C:\Users\Ajmal Khan\.copilot\skills\audit-hosting`
  - Audit a Hostinger web hosting account (Shared, Cloud and Agency plans) and report what needs attention: every plan and website, SSL problems, broken or vulnerable WordPress installs, failed Node.js builds and vulnerable 

- **connect-domain** — `C:\Users\Ajmal Khan\.copilot\skills\connect-domain`
  - Connect a custom domain to a website on Hostinger web hosting (Shared, Cloud or Agency plans) end to end: attach the domain to the site, point DNS at Hostinger without breaking existing email or verification records, ins

- **deploy-to-hosting** — `C:\Users\Ajmal Khan\.copilot\skills\deploy-to-hosting`
  - Deploy an existing project to a website on Hostinger web hosting (Shared, Cloud or Agency plans) and keep it deployed: picks the right deploy for static sites, Node.js apps (Next.js, Nuxt, Express, Vite and similar), PHP

- **hostinger-headless** — `C:\Users\Ajmal Khan\.copilot\skills\hostinger-headless`
  - Orchestrator for the Hostinger Headless build flow — build and deploy a real website on the user's Hostinger account from a single prompt that names a domain. Holds the stage flow and the state contract, and drives each 

- **maintain-wordpress** — `C:\Users\Ajmal Khan\.copilot\skills\maintain-wordpress`
  - Keep WordPress sites on Hostinger web hosting updated and secure: checks core, plugin and theme versions, known vulnerabilities and install health on one site or every site in the account, reports what needs doing, appli

- **migrate-to-hosting** — `C:\Users\Ajmal Khan\.copilot\skills\migrate-to-hosting`
  - Move an existing website from another host to Hostinger web hosting (Shared, Cloud or Agency plans) without downtime: WordPress sites from a files archive and SQL dump, static and PHP sites from an archive, Node.js apps 

- **troubleshoot-website** — `C:\Users\Ajmal Khan\.copilot\skills\troubleshoot-website`
  - Diagnose and fix a website on Hostinger web hosting (Shared, Cloud or Agency plans) that is down, slow, erroring, insecure or failing to build. Checks the site from outside, reads builds, runtime logs, WordPress health, 

---

## Suggested next steps

- **MCP:** Command Palette → `MCP: List Servers` (or this extension’s hub **MCP** tab) → start/trust servers in **Copilot Chat → Agent → tools**.
- **Edit config:** `MCP: Open Workspace Folder MCP Configuration` / `MCP: Open User Configuration`.
- **Refresh this report:** run **Intelligence — scan MCP & Skills awareness** again after changing `mcp.json` or adding skills.

_Report from GitHub Copilot Toolbox extension._
