# CLAUDE.md Snippet

Add this to your nf-core pipeline's CLAUDE.md for always-on docs awareness:

```markdown
## nf-core Documentation

- Use `/nfcore-docs` to load nf-core specs and docs into context
- Docs cached at `~/.cache/nfcore-docs/` (sparse checkout of nf-core/website, auto-updates if >24h stale)
- The skill generates a dynamic index of all pages with section headers on each invocation
- Context budget: index ~15K tokens (1.5%), specs ~60K (6%), all docs ~275K (28%) of 1M
```
