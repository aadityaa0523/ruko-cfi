# Work done in AgentFoundry

Ruko's first version was built outside AgentFoundry (see the README's History section). The tasks below are run in AgentFoundry's agent on this repository, each as its own commit. A row is only marked done after it has really been run there.

| # | Task | Check | Done |
|---|---|---|---|
| 1 | Add a startup test for `/api/health` so a bad deploy is caught | `python -m pytest -q` | no |
| 2 | Add a test that every language file has the same keys as English, and fix any broken placeholders or unnatural words in the five regional-language files | `python -m pytest -q` | no |
| 3 | Make the family screen use the same language picker as the other pages | open `/family/`, switch language | no |

Commits made from AgentFoundry start with `AF:`.
