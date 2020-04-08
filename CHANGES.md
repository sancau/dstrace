### 0.1.0

- Initial minimal working version.

### 0.1.1

- Allow to set custom dstrace command in .dstrace

### 0.1.2

#### Features:

- Respect branch configuration during Confluence pages update
- Allow to hide code cells input while exporting to Confluence
- Allow local configuration file for credentials
- Add a CLI command for forced Confluence pages update

#### Fixes:

- Proper "since last push" changed notebooks list resolver

#### Other:

- Fix dependencies versions
- Minor refactoring

### 0.1.3

#### Fixes:

- fixed incorrect last commit url resolver

### 0.1.4

#### Fixes:

- fixed a bug where .dstracelocal would not be correctly added to .gitignore on dstrace init

### 0.1.5

#### Fixes:

- fixed markup issues (margins between code blocks when rendering Confluence pages)

#### Features:

- allow to disable *Source Commit: ...* line for Confluence pages by adding *no_commit_url: true* to Confluence's page config
- allow forcing specific code cell inputs to Confluence by markig them with *dstrace_confluence_force_include_input* metadata tag
- allow to skip "nbconvert to python" step for specific Confluence pages by adding *no_conversion_to_python: true* to a Confluence page config

#### Other:

- add some helpers for testing and debugging during development
- use vendoring strategy for nbconflux https://github.com/Valassis-Digital-Media/nbconflux.git
