# Select an audit unit

Initialize one exact release:

```bash
policy-audit init --version 2.106.1
```

The command creates an isolated Git worktree for the release tag, confirms that
the checked-out package declares the requested version, and inventories that
source. Do not audit the current branch as a substitute for the release
worktree.

Claim the next statutory parameter or program formula:

```bash
policy-audit next --version 2.106.1 --scope policy
```

Unchecked units are ordered by their source's last modification date. After
every unit has a review, the least recently checked unit is selected. The
`last_checked_at` field records past work; it is not evidence that the policy is
still current.

Parameter YAML documents are one audit unit by default. Brackets and breakdown
members in the document must be researched together.

When one logical rule spans multiple YAML documents, pass a reviewed grouping
file during initialization:

```yaml
groups:
  - unit_id: parameter:gov.example.program.combined_rule
    units:
      - parameter:gov.example.program.part_one
      - parameter:gov.example.program.part_two
```

```bash
policy-audit init --version 2.106.1 --parameter-groups groups.yaml
```
