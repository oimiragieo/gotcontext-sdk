# Submitting `gotcontext` to the official Anthropic plugin directory

**One-time manual step.** Anthropic's directory is reviewed — we can't
automate the submission itself, only keep the plugin ready to pass review.

## Pre-flight

1. Verify structure:

   ```bash
   claude plugin validate ./plugins/gotcontext
   ```

   The validator is strict about `.claude-plugin/plugin.json`, `SKILL.md`
   frontmatter, and referenced file paths. Fix anything it reports.

2. Confirm no external file references. The plugin is self-contained under
   `plugins/gotcontext/`. Hooks or scripts that walk up into the monorepo are
   a common rejection reason.

3. Test locally — install from the working tree:

   ```
   /plugin marketplace add ./
   /plugin install gotcontext@gotcontext-plugins
   ```

   Run each of the 5 skills on a small sample and confirm the MCP server
   connects with `GOTCONTEXT_API_KEY` in the env.

4. Verify the README answers:
   - What does this plugin do?
   - How do I install it?
   - How do I get the required API key?
   - What does each skill do?

## Submit

Use one of:

- <https://claude.ai/settings/plugins/submit>
- <https://platform.claude.com/plugins/submit>

Both forms accept a GitHub URL or a zip of `plugins/gotcontext/`. Repo must
be public. Reviews typically take a few days.

## After approval

External plugins are listed in `external_plugins/` of the official repo.
Users can then:

```
/plugin install gotcontext
```

without any marketplace-add step.

## Meanwhile

Users can install directly from our GitHub today:

```
/plugin marketplace add oimiragieo/gotcontext-main
/plugin install gotcontext
```

Marketplace listing adds discoverability, not functionality.

## Common rejection reasons (per Anthropic)

1. **Outside-directory references** — all skill/hook/script paths must be
   under the plugin directory.
2. **Insufficient README** — "install and use" is not enough.
3. **Plugin does too much** — if we ever bundle >7 skills, split.
