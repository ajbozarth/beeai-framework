<!--
Thank you for your pull request. Please review and complete the sections below.
-->

### Which issue(s) does this pull-request address?

<!--
Please include a link to an issue in the tracker.  The issue describes the problem to be solved.  If there is no issue raised for this PR then either raise one with a summary and description of the problem or add a summary and description of the problem here
-->

Closes: #

### Description

<!-- Provide a description of the change, pay special attention to describing any breaking changes.  The description describes the resolution to the problem described in the linked issue (or to the problem outlined in this PR). -->

### Checklist

#### General
- [ ] I have read the appropriate contributor guide: [Python](https://github.com/i-am-bee/beeai-framework/blob/main/CONTRIBUTING.md)
/ [TypeScript](https://github.com/i-am-bee/beeai-framework/blob/main/CONTRIBUTING.md)
- [ ] I have signed off on my commit: [Python instructions](https://github.com/i-am-bee/beeai-framework/blob/main/python/CONTRIBUTING.md#developer-certificate-of-origin-dco) / [TypeScript instructions](https://github.com/i-am-bee/beeai-framework/blob/main/typescript/CONTRIBUTING.md#developer-certificate-of-origin-dco)
- [ ] Commit messages and PR title follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)
- [ ] Appropriate label(s) added to PR: `Python` for Python changes, `TypeScript` for TypeScript changes

#### Code quality checks
- [ ] Code quality checks pass: `mise check` (`mise fix` to auto-fix)

#### Testing
- [ ] Unit tests pass: `mise test:unit`
- [ ] E2E tests pass: `mise test:e2e`
- [ ] Tests are included (for bug fixes or new features)

#### Documentation
- [ ] Documentation is updated
- [ ] Embedme embeds code examples in docs. To update after edits, run: Python `mise docs:fix`
