---
name: agent-skills-cross-platform-sync
description: This skill should be used when the user wants to migrate, version-control, back up, or synchronize Agent Skills across WorkBuddy, Claude Code, Codex, Cursor, OpenCode, or other SKILL.md-compatible agents. It captures the safe workflow for using a private Git repository as the single source of truth, copying or linking skill directories into platform-native locations, using Windows Junction or symlink carefully, backing up before replacing directories, avoiding secrets and runtime files, and verifying Git and skill discovery status.
description_zh: 跨平台技能同步
description_en: Agent Skills Cross-Platform Sync
disable: false
agent_created: true
---

# agent-skills-cross-platform-sync

## When to use
Use this skill when the user asks to:
- Migrate WorkBuddy skills into a Git repository.
- Sync the same `SKILL.md` skills across WorkBuddy, Claude Code, Codex, Cursor, OpenCode, Gemini CLI, or similar agents.
- Convert copied skill directories into Windows Junctions or symlinks.
- Back up, restore, audit, or version-control personal Agent Skills.
- Decide whether to use copy, symlink, Junction, or platform-specific installation.

## Steps
1. Treat the Git repository as the single source of truth. Prefer a clean repository such as `D:\Repos\agent-skills` with this structure:

   ```text
   agent-skills/
   ├── README.md
   ├── .gitignore
   ├── agent-created-skills.json
   └── skills/
       └── <skill-name>/
           └── SKILL.md
   ```

2. Only migrate user-created or explicitly selected skills. Do not blindly migrate marketplace skills, connector skills, runtime state, logs, caches, databases, login state, MCP config, or secrets.
3. Before replacing any live agent skill directory with a symlink or Junction, create a timestamped backup outside the live skills directory and verify that every selected skill has a `SKILL.md` in the backup.
4. On Windows, prefer per-skill Junctions rather than replacing the entire platform skills directory. Keep platform-owned skills and connector skills untouched.
5. Use these common target locations as deployment targets, not as the source of truth:

   ```text
   WorkBuddy:   C:\Users\<user>\.workbuddy\skills\
   Claude Code: C:\Users\<user>\.claude\skills\
   Codex new:   C:\Users\<user>\.agents\skills\
   Codex legacy:C:\Users\<user>\.codex\skills\
   ```

6. After creating links, verify that each platform directory entry is a reparse point or symlink and that `SKILL.md` is readable through the platform-native path.
7. Keep `.gitignore` conservative. Ignore secrets, `.env` files, logs, caches, databases, temporary backups, archives, node modules, Python caches, and editor files.
8. Commit meaningful changes in the skills source repository. Use commit messages that explain what changed, for example `feat: add podcast briefing skill` or `fix: clarify Codex skill path guidance`.
9. When adding a new WorkBuddy-created skill after the repository exists, add it to the source repo and then deploy it back into WorkBuddy through copy or Junction. Avoid leaving WorkBuddy and the Git source diverged.

## Pitfalls
- Do not sync the whole `.workbuddy`, `.claude`, `.codex`, or `.agents` directory. These directories may contain runtime state, logs, local databases, or credentials.
- Do not put API keys, tokens, cookies, passwords, or local-only absolute paths inside portable `SKILL.md` files.
- Do not commit Windows Junctions or symlinks as the canonical artifact. Commit real skill directories and recreate links per machine.
- Do not replace the entire WorkBuddy skills folder with a Junction unless explicitly intended; it can interfere with marketplace or connector skills.
- Do not assume Codex has only one path. Newer Codex documentation prefers `$HOME/.agents/skills`; older tutorials and versions may use `$HOME/.codex/skills`.
- Do not delete original skill folders until backup and link verification both pass.

## Verification
Before reporting completion, verify:
- The source repository has the selected skills under `skills/<skill-name>/SKILL.md`.
- The live platform path resolves to the intended repository path when using Junction or symlink.
- The live platform path can read `SKILL.md`.
- `git status --short` is clean or expected changes are committed.
- A rollback backup path is available and excluded from Git.
