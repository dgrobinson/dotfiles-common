---
description: review and consolidate documentation across the repo
---

# Update Documentation

Carefully read through the repo root CLAUDE.md in its entirety.

* If you've learned anything in our conversation so far that would be useful for you to remember in the future, add it to a CLAUDE.md in the repo.
* If you've learned something about code in a particular subfolder that already has a CLAUDE.md file, you should deploy a subagent to update that CLAUDE.md and follow the common instructions below.

## Rules for all updates to CLAUDE.md files

The following rules apply to any CLAUDE.md file you change:

* If anything is outdated/incorrect anywhere in the CLAUDE.md file, fix it, even if it is not directly related to the current conversation.
* If anything is too verbose and can be made more concise without losing meaning, do so.
* If a section is growing too large, consider moving it into a new or existing markdown file inside docs/ .
    * Only do this for sections that are significantly large and complex (~hundreds of lines).
    * In the CLAUDE.md files, you should maintain a single section at the top with a list of all such files and a brief description of what they contain (unless no such files exist).
* Do not allow any CLAUDE.md to exceed 1000 lines. If that happens, you MUST break it into other md files and have the CLAUDE.md file reference them.
