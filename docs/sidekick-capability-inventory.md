# Binary Ninja Sidekick capability inventory

This document inventories the publicly documented capabilities of Binary Ninja
Sidekick so Axio Analyst product and architecture decisions can be made against
a concrete reference. It describes Sidekick, not implemented Axio Analyst
behavior. Axio Analyst's current behavior remains defined by
[architecture.md](architecture.md), [configuration.md](configuration.md), and
[roadmap.md](roadmap.md).

## Research scope

- Research date: 2026-08-10.
- Product generation: Sidekick 26.1.
- Documentation build shown by the documentation root during research:
  `26.1.516`.
- Sources: current official Vector 35 Sidekick documentation, product pages,
  pricing page, FAQ, terms, and privacy policy.
- Method: documentation inventory only. This was not a paid-account usability
  test, protocol inspection, or independent validation of model quality.

Sidekick changes quickly. Treat plan prices, usage limits, data policy, model
routing, minimum versions, defaults, and exact UI placement as time-sensitive.
Recheck the linked official source before relying on them operationally.

## Executive summary

Current Sidekick is a stateful reverse-engineering workspace and agent platform,
not just a chat panel. Its documented system combines:

1. A persistent lead-agent conversation and optional multi-thread chat tree.
2. Specialist research, transformation, repair, modeling, debugger, and
   automation modes.
3. Direct Binary Ninja database transformations for analysis recovery, names,
   types, comments, structures, imports, and other database objects.
4. Evidence-backed findings, artifacts, blockers, validation, provenance, and a
   rolling session briefing.
5. Structural BNQL queries, local semantic search, persistent indexes, and code
   maps.
6. Multi-binary project analysis and explicit workspace export/import.
7. Python and headless APIs, reusable scripts/agents/skills, configurable model
   pools, and MCP tools.
8. Fail-closed tool permissions and a persistent transaction audit trail.

The important product distinction is that Sidekick intentionally crosses the
read-only boundary. It can alter the Binary Ninja database, run Python, control
the debugger, call external MCP tools, and operate file repositories when the
corresponding tools are approved. Axio Analyst `0.9.0` does none of those
things.

## Product and execution model

Sidekick is split between a local Binary Ninja plugin and optional service
capabilities:

- The plugin owns UI integration, workspace state, local indexes, local
  semantic vectors, file repositories, permissions, and database application.
- The Sidekick service supplies the built-in lead agent, suggestion operations,
  automatic synthesis, and validation.
- Library agents, prompts, and API automation can instead use configured
  Sidekick, Anthropic, OpenAI, or OpenAI-compatible endpoints.
- Local OpenAI-compatible endpoints include deployments such as Ollama, vLLM,
  and LM Studio.
- A custom/local endpoint does not inherently reproduce the Sidekick service's
  proprietary persona, prompting, skills, or specialist coordination.

The built-in agent separates actions into:

- **Attention**: read, query, search, model, and reason without changing the
  Binary Ninja database.
- **Transformation**: write names, types, comments, structures, analysis state,
  and other Binary Ninja objects.

Sidekick documents an attend-before-transform rule: it first resolves and reads
the referenced object, and it stops on an unresolved reference rather than
guessing a substitute.

Sources: [About Sidekick](https://docs.sidekick.binary.ninja/about/index.html),
[agent architecture](https://docs.sidekick.binary.ninja/tutorials/agent-capabilities.html),
and [Sidekick API](https://docs.sidekick.binary.ninja/guide/sidekick_api.html).

## User-interface inventory

### Sidekick center-pane view

Sidekick 26.1 adds a center-pane view type alongside Binary Ninja's Linear,
Graph, Hex, and IL views. It is the home of one persistent `Workspace Chat` and
contains four tabs:

| Tab | Documented behavior |
| --- | --- |
| Chat | Persistent lead-agent conversation, binary summary, suggested prompts, and a collapsible active-work drawer. |
| Briefing | Read-only rolling case file synthesized from workspace and notebook activity. |
| Artifacts | Feed of non-rejected artifact outcomes such as YARA rules, reports, PoCs, and scripts. |
| Findings | Feed of non-rejected, evidence-anchored findings from all notebook entries. |

The active-work drawer shows notebook entries with open tasks, progress, elapsed
work time, and open blockers. Selecting an item navigates to the responsible
chat or notebook entry.

There is a documentation inconsistency about the `Prefer Sidekick View` default:
the 26.1 release page says it is enabled by default, while the detailed view
guide says it is disabled by default. Do not encode either value as confirmed
without checking the installed build.

Sources: [Sidekick view](https://docs.sidekick.binary.ninja/guide/sidekick_view.html)
and [What's New in 26.1](https://docs.sidekick.binary.ninja/whats-new-26-1.html).

### Chats sidebar

The separate Chats sidebar is the thread-oriented interface. It supports:

- Creating independent conversations.
- Parent/child thread trees for delegated investigations.
- Watching specialist-agent threads.
- Live thinking, tool-running, compaction, approval, and error states.
- Aggregate thread, change, and finding counts.
- Automatic and manual thread names.
- Pinning and pinned-only filtering.
- Full-text chat search.
- Permanent deletion of a thread and its descendants.
- Copying assistant messages.
- Retrying an assistant response.
- Editing a user message and rerunning from that point.
- Cancelling the active turn and its child work.
- Expandable tool groups with arguments and results.
- Visual differentiation between read and write tools.
- Per-call approval, rejection, rejection reasons, and argument editing.
- Bulk approval or rejection of pending descendant calls.
- Viewing and importing raw thread JSON.
- Context attachment through `@` mentions.
- Library slash commands for scripts, agents, and skills.

Source: [chat guide](https://docs.sidekick.binary.ninja/guide/chat.html).

### Resources sidebar

The Resources sidebar is a searchable workspace-wide browser for:

- Notebook entries.
- Indexes.
- Code Maps.
- Workspace repositories.

It provides a browse list and resource-specific detail view. Search combines
immediate title/kind/summary matching with deeper searches across tasks,
outcomes, index rows, map nodes, and repository filenames. Resources can be
pinned to dedicated Binary Ninja panes.

Source: [workspace resources](https://docs.sidekick.binary.ninja/guide/resources.html).

### Other persistent surfaces

- **Transaction Log sidebar**: database-change audit history.
- **Library sidebar**: reusable application-wide scripts, agents, skills, and
  their repositories.
- **Status indicator**: online, offline, disconnected, or missing-key state and
  related connection actions.
- **Configuration dialogs**: tool permissions, MCP servers, automation models,
  semantic indexing, workspace portability, workspace management, and API key.

## Agent and chat capabilities

### Request classification

The lead agent classifies requests into four top-level modes:

| Mode | Purpose |
| --- | --- |
| Transform | Rename, retype, annotate, restructure, or otherwise improve the binary representation. |
| Investigate | Explain, find, trace, or answer a binary question with evidence. |
| Reference | Search Binary Ninja or Sidekick documentation. |
| Script | Create or use automation for novel work when explicitly requested. |

Classification influences delegation, notebook creation, skills, and how much
work becomes a tracked multi-turn investigation. The user can steer it with
instructions such as `just answer` or `investigate systematically`.

### Specialist modes

| Specialist | Documented scope | Database posture |
| --- | --- | --- |
| Research | Multi-hop graph walks, unnamed-code discovery, semantic patterns, and structural/behavioral candidate searches. | Read-only. |
| Transform | Default-name recovery, structure reconstruction, signature correction, and documentation of deobfuscation patterns. | Reads, then writes. |
| Repair Analysis | Corrects local function boundaries, imports, indirect calls, xrefs, and code/data classification when faulty analysis blocks work. | Bounded writes. |
| Modeling | Extends a persistent behavioral model of components, data flow, protocols, dependencies, and uncertainty. | Workspace-model writes. |
| Debugger | Breakpoints, steered execution, registers, memory, and runtime extraction such as decrypted buffers or API tables. | Runtime control; mutation is possible. |
| Automation | Authors reusable Python scripts, local agents, skills, or small supporting-file bundles. | Writes Library resources; does not automatically execute the generated script. |

### What chat can operate

The documented chat tool surface can:

- Query functions, instructions, data variables, strings, symbols, types,
  xrefs, and other Binary Ninja objects.
- Run BNQL structural and semantic queries.
- Read and update indexes.
- Read and update notebook entries and structured analysis context.
- Read and update code maps.
- Rename functions and variables, apply types, and add comments.
- Run Python inside Binary Ninja.
- Search bundled documentation.
- Control and inspect the Binary Ninja debugger.
- Run reusable Library items.
- Discover and use configured MCP tools.
- Create scripted tools for novel analysis tasks.

### Continuity and background work

Sidekick maintains continuity with:

- A workspace-level behavioral model.
- A rolling briefing attached to new analysis work.
- Persistent notebook entries and outcomes.
- Enabled skills selected for the analysis domain.
- Resumable multi-turn investigations.
- Visible background `Notebook Validation` and `Analysis Briefings` threads.

Background validation checks new findings and artifacts against existing
context. Later contradictory evidence can move a previously accepted outcome
to rejected and trigger reconsideration of dependent outcomes.

Source: [agent architecture](https://docs.sidekick.binary.ninja/tutorials/agent-capabilities.html).

## Direct suggestion actions

Five cursor-oriented, single-shot actions are documented:

| Menu action | Scope and behavior |
| --- | --- |
| Suggest Repairs | Repairs inaccurate local analysis around the cursor so boundaries, signatures, xrefs, and control flow become trustworthy. |
| Suggest Types | Recovers structures, unions, enums, fields, arrays, function signatures, local/global variable types, and function-pointer tables. |
| Suggest Imported Types | Applies likely imported signatures using format metadata, curated type data, service knowledge, and call-site evidence. |
| Suggest Names | Renames only default-named functions, locals, arguments, and data variables; existing meaningful names are preserved. |
| Suggest Comments | Adds targeted explanations for non-obvious logic, constants, patterns, and data behavior. |

Suggestion operations:

- Use the current code or data address as their starting scope.
- Run as background tasks.
- Apply changes directly rather than presenting a mandatory pre-application
  diff.
- Group their changes into a Binary Ninja undo action.
- Record attempted, rejected, failed, and committed work in the Transaction Log.
- May repair an untrustworthy analysis substrate before performing a more
  targeted transformation.
- Re-read the modified region to verify the result.

`Suggest Repairs` may create or remove functions; correct signatures, calling
conventions, and stack cleanup; recover indirect branches and jump tables;
repair missing code/data references; correct symbols and variables; and apply
bounded analysis steering.

Source: [editing with suggestions](https://docs.sidekick.binary.ninja/guide/suggestions.html).

## Evidence, Notebook, and briefing

Sidekick describes three persistent forms of understanding:

1. The Binary Ninja database for concrete code and data objects.
2. A sparse behavioral model for roles, flows, external interactions,
   dependencies, and uncertainty.
3. The Notebook for goals, tasks, durable outcomes, and intermediate state.

### Notebook entries

Entry types are:

- `operational`: a concrete analysis task.
- `research`: an open-ended investigation.
- `learning`: recorded understanding about the target.

Entries support renaming, searching, dependencies, linked originating/recent
threads, completion, abandonment, reactivation, and permanent deletion.
Completion resolutions are `achieved`, `partial`, `infeasible`, and `deferred`.

### Tasks

Tasks represent forward-looking work and move through:

- `pending`
- `in_progress`
- `completed`
- `blocked`

### Outcomes

Outcome kinds are:

- `finding`: a reusable fact anchored to binary evidence.
- `artifact`: a concrete deliverable such as a report, YARA rule, PoC, or
  generated script.
- `blocker`: an external obstacle requiring attention.

An outcome can include a title, description, confidence, important flag,
function/type/address references, and thread provenance. Statuses are `draft`,
`verified`, and `rejected`. Rejection requires a reason and may cascade to
dependent outcomes.

Outcomes are agent-produced rather than arbitrary handwritten records so their
confidence and provenance have a defined origin. Users steer creation through
tasks or chat requests.

### Structured analysis context

An entry may store machine-readable `analysis_context`, including scope,
candidate lists, partition rules, or coverage manifests. It survives across
turns and sessions and is available to tools and scripts, but is not rendered in
the current Notebook UI.

### Session Briefing

The rolling briefing contains:

- Goal.
- Status.
- Key findings.
- Current focus.
- Open questions.
- Wayfinding landmarks, functions, flows, sinks, and sources.

It is read-only in the UI; users request corrections through chat. Background
synthesis and validation require the Sidekick service, while manual Notebook
use remains available offline.

Source: [Notebook guide](https://docs.sidekick.binary.ninja/guide/notebook.html).

## BNQL and semantic indexing

### BNQL

Binary Ninja Query Language is a path-oriented query language over one or more
open Binary Ninja views. It supports:

- Object traversal and filtering.
- Functions, blocks, instructions, variables, data variables, strings,
  symbols, and views.
- Call, reference, and other graph relationships.
- Names, addresses, regular expressions, counts, entropy, and predicates.
- Set operations including unions and exclusions.
- Relative and absolute paths.
- Cross-binary queries.
- Semantic `concept()` expressions when semantic indexing is active.

Queries execute locally. The Resources query editor limits a UI execution to
1,000 results by default; the Python API can execute without that UI limit.

Source: [BNQL reference](https://docs.sidekick.binary.ninja/reference/bnql.html).

### Semantic indexing

The semantic index builds a local vector database for natural-language and
similarity search. It can index:

- Decompiled functions.
- Disassembly.
- All IL levels.
- Referenced and admitted strings.
- Symbols.
- Indexed chat content when its adapter is enabled.

It supports:

- Natural-language function, string, and symbol search.
- Similar-object search from an existing Binary Ninja object.
- Object-type filtering, similarity thresholds, reranking, and result limits.
- Combining semantic matches with structural BNQL predicates.
- Cross-binary search across open project members.
- Use from the Python API and headless sessions.

The index and vectors are maintained locally and binary content is not sent to
the Sidekick cloud for this feature. Semantic indexing is disabled by default.
Managed sidecars require `llama-server`; unmanaged mode uses configured
embedding and reranking URLs. Index vectors are regenerable and excluded from
workspace snapshots.

Source: [semantic indexing](https://docs.sidekick.binary.ninja/guide/semantic_indexing.html).

## Persistent indexes

Indexes are named collections of addressable Binary Ninja objects. They can be
used to:

- Track candidates for review.
- Save BNQL or semantic query results.
- Supply a batch of objects to analysis.
- Record automation results with per-entry metadata.
- Organize locations from several binaries.
- Overlay points of interest on Code Maps.

Index types are:

| Type | Population | Refreshable | Manual curation |
| --- | --- | --- | --- |
| BNQL | One stored query | Yes | No |
| Script | Script or agent execution | Yes | No |
| Manual | Queries, automation, and manual additions | No | Yes |

Index tables support filtering, column sorting/resizing/reordering, metadata
columns, copy, deletion, address navigation, cross-binary tab activation, and a
live pinned-pane view. BNQL and Script indexes can be converted permanently to
Manual indexes.

Source: [indexes guide](https://docs.sidekick.binary.ninja/guide/indexes.html).

## Code Maps

Code Maps are named, persistent graph resources.

Automatic maps support:

- One or more root functions.
- Separate caller and callee traversal depths.
- Adjustable node width.
- Index overlays within function nodes.
- Pruning nodes that do not contain or connect relevant index entries.
- Navigation from graph tokens to binary addresses.
- Cross-view function URIs.

Manual maps support arbitrary nodes and directed edges with labels, body lines,
metadata, and optional Binary Ninja anchors. They can represent conceptual
relationships, protocols, message flows, or agent-generated summaries rather
than a literal call graph. Converting an automatic map to manual is permanent.

Maps can be created or updated by chat, searched, renamed, deleted, and pinned
to a standalone Binary Ninja pane.

Source: [Code Maps guide](https://docs.sidekick.binary.ninja/guide/code_maps.html).

## Multi-binary projects

Sidekick maps workspace identity as follows:

| Binary Ninja target | Sidekick workspace |
| --- | --- |
| Standalone raw binary or BNDB | One workspace for that file. |
| Binary Ninja project | One shared workspace for all project files. |

Project-wide state includes chats, the semantic index, Notebook, indexes, code
maps, and repositories. Binary-specific state includes the active cursor,
selected function, debugger session, semantic scope, and Transaction Log.

With multiple project binaries open, Sidekick can:

- Run BNQL across all of them.
- Return semantically related objects from any open member.
- Include a binary-origin column in mixed indexes.
- Reason across binaries in one agent request.
- Navigate directly to the owning binary tab.
- Retain workspace knowledge when one member is closed.

Only open binaries are currently queryable, even though workspace information
about closed members is retained.

Source: [multi-binary projects](https://docs.sidekick.binary.ninja/guide/multiple_binaries.html).

## Database modifications and BNMF

Binary Ninja Modification Format is Sidekick's declarative JSON protocol for
database write-back. The documented URI handlers cover:

- Address comments.
- Named types.
- Structure and union members.
- Data variables.
- Functions.
- Function instructions.
- Integer operand display types.
- Function variables.
- Basic-block highlights.
- User data references.
- Global pointer values.
- Raw memory.
- Symbols.
- Sections and segments.
- Tags and tag types.
- External libraries and external locations.
- Imported function signatures.
- Components and their membership.
- Stack variables.
- Per-call stack adjustments.
- Function return stack adjustments.

BNMF supports:

- Atomic batches, in which every change succeeds or the batch is rolled back.
- Best-effort batches, in which independent successful changes remain.
- Explicit modification dependencies and topological ordering.
- Existence and property preconditions.
- Targeted collection add/remove operations.
- Object deletion through a null desired state where supported.
- Human-readable descriptions for Binary Ninja undo history.
- Structured per-modification results and errors.

This means the lower-level mutation surface is broader than the five visible
suggestion commands. The documented format can express raw-memory and analysis
object changes, although Sidekick is not marketed as a general-purpose binary
patching workflow.

Source: [BNMF reference](https://docs.sidekick.binary.ninja/reference/bnmf.html).

## Permissions and safety controls

Sidekick's chat tools are fail-closed by default: a call requires approval
unless a matching policy explicitly allows it.

### Approval actions

- Allow one call.
- Allow the tool category for the current chat.
- Allow that exact tool for the current chat.
- Reject one call.
- Reject with a reason returned to the agent.
- Edit the JSON arguments before approving.
- Bulk approve or reject pending child-thread calls.

### Permission hierarchy

Rules can be stored at:

1. This Chat.
2. This Workspace.
3. All Workspaces.

Each tool or tag can be `Allow`, `Ask`, or `Inherit`. Exact tool rules outrank
tag rules, and the most specific tag wins. If no rule allows a call, the final
decision is `Ask`.

Documented tag families cover:

- Repository read, write, and Git management.
- Visible UI and current selection.
- Notebook and briefing query/update.
- Binary database query/update.
- Index and Code Map query/update.
- Library execution.
- Python execution and evaluation inside Binary Ninja.
- Documentation access.
- Debugger control, inspection, mutation, backend commands, and breakpoints.
- MCP tools.

Background/system actors have process-owned policies and do not inherit the
user's workspace or application permission rules.

Source: [tool permissions](https://docs.sidekick.binary.ninja/tutorials/tool-permissions.html).

## Transaction Log and undo

The Transaction Log records every Sidekick database change that was committed,
rejected, or failed. It includes chat and suggestion operations.

It supports:

- Filtering by committed, rejected, and failed state.
- Search across type, ID, description, and serialized content.
- Details and errors for each transaction.
- Old/new diff rendering for changed properties.
- Navigation to affected addresses.
- Analysis Update, Index Update, and Task Recommendation records.
- Live updates as operations complete.
- Deletion of individual audit records.

Important boundaries:

- The Transaction Log does not expose its own undo button.
- Binary Ninja's normal undo operation reverses committed changes.
- A suggestion batch is grouped into one Binary Ninja undo action.
- Removing a log entry does not revert the database change.
- Rejected and failed transactions were not applied.

Source: [Transaction Log](https://docs.sidekick.binary.ninja/guide/transaction_log.html).

## Library and reusable automation

The Library stores reusable application-wide assets shared by every workspace:

- Python scripts.
- Custom agents.
- Skills.
- Blank or multi-file repositories.

Library functionality includes:

- Starter templates and text-command creation.
- Multiple entry points per item.
- Draft and published states.
- Working-copy editing.
- Revision history.
- Clone, rename, delete, and file-manager actions.
- Catalog repair for broken, unindexed, or orphaned repositories.
- Runtime arguments and saved per-entry-point values.
- JSON-schema validation for script arguments.
- Template variables for agents and skills.
- One-hour default Python execution timeout, configurable to another value or
  unlimited.

Execution modes are:

| Entry point | Direct action | Chat integration |
| --- | --- | --- |
| Python | Run locally and show raw progress/output. | Run in a new chat so the agent can inspect and continue from the output. |
| Agent | Start a new chat/kernel using its configured completion pool. | Appears as its own specialized conversation. |
| Skill | Inject rendered reusable instructions into a selected chat. | Can be launched with `/slug` and validated variables. |

Workspace repositories are separate from Library items: they are versioned file
stores scoped to one file/project workspace rather than reusable globally.

Source: [Library guide](https://docs.sidekick.binary.ninja/guide/library.html).

## Python and headless API

The supported public package is `sidekick.api`. It works inside an active Binary
Ninja UI session and in headless Binary Ninja scripts.

Documented capabilities include:

- Opening or borrowing a file/project session.
- Opening more project members.
- Running BNQL.
- Semantic `concept()` search.
- Rendering Binary Ninja objects at identifier, summary, contents, or
  contextual detail.
- Loading and executing single-shot YAML prompts.
- Loading local YAML/Library agents.
- Loading the built-in service-backed Sidekick agent.
- Continuing one stateful headless Sidekick conversation across calls.
- Reading and writing indexes.
- Reading and updating automatic Code Map configuration.
- Creating, reading, updating, and deleting Notebook entries, tasks, outcomes,
  and analysis context.
- Accessing the active session and kernel.
- Constraining loaded agents to read-oriented tags with
  `allow_updates=False`.

Notable limits:

- The Sidekick plugin must be installed and active.
- Semantic search needs an active semantic index.
- Manual Code Map graph payloads are not writable through v1 of the public API;
  only automatic-map configuration is supported there.
- Local agents default to autonomous tool execution in API contexts because
  headless scripts have no interactive approval card. Visibility still depends
  on their configured tool tags.
- Headless automation requires a Binary Ninja edition that supports the
  necessary API use.

Source: [Sidekick API](https://docs.sidekick.binary.ninja/guide/sidekick_api.html).

## Completion pools and model endpoints

Agents and prompts refer to logical completion pools. A pool contains one or
more ordered endpoints and falls back when an earlier endpoint fails.

Shipped logical pools are:

- `smart`: primary analysis, code generation, type suggestion, and research.
- `fast`: naming chats, summaries, and notebook operations.

Documented endpoint types are:

- `sidekick`: hosted Sidekick service.
- `anthropic`: direct Anthropic API using an environment-variable key.
- `openai`: direct OpenAI API using an environment-variable key.
- `openai-compatible`: Ollama, vLLM, LM Studio, and similar servers.

Endpoint configuration includes service model, base URL, token limits,
tokenizer, API-key environment variable, and pricing fields. Routing
configuration is stored locally as YAML.

Source: [completion-pool configuration](https://docs.sidekick.binary.ninja/guide/sidekick_api.html#configuring-completion-pools).

## MCP integration

Sidekick can launch external Model Context Protocol servers over stdio and
register selected tools in chat. It supports:

- Multiple configured servers.
- Per-server enable/disable state.
- Explicit tool allowlists.
- Tool aliases.
- Per-server and per-tool tags.
- Additional environment variables.
- Request timeouts.
- Server discovery and validation through the configuration UI.
- Reused healthy subprocess sessions.
- The normal Sidekick tool-approval system.

MCP tools can provide filesystem, web, Git, database, threat-intelligence, or
arbitrary custom capabilities. Default `mcp` tools are visible to the root chat
agent. Automated suggestion specialists do not import MCP capabilities by
default.

Source: [MCP guide](https://docs.sidekick.binary.ninja/guide/mcp_tools.html).

## Workspace storage and portability

### Local storage

Sidekick resolves its application directory in this order:

1. `SIDEKICK_HOME`.
2. `$BN_USER_DIRECTORY/sidekick/` in the plugin.
3. `~/.sidekick/` for standalone use.

Key storage is:

| Location | Contents |
| --- | --- |
| `data/workspaces.db` | Chats, processes, indexes, code maps, notebook entries, tasks, and transaction history, namespaced by workspace. |
| `data/semantics.db` | Local semantic vector records and index metadata. |
| `config/completion_routing/` | Model endpoint and completion-pool YAML. |
| `config/mcp_tools_config.json` | External MCP server configuration. |
| `kernel/` | Application-level kernel state and Library catalog. |
| `cache/models/` | Downloaded local embedding/reranking GGUF files. |
| `filestore/` | Versioned workspace and application-level repositories. |
| Binary Ninja `settings.json` | API key and `sidekick.*` settings. |

Normal chats, indexes, maps, notebook content, and transaction history do not
automatically live in the BNDB. Sidekick does automatically write workspace and
view identity metadata when a file is first saved after Sidekick opens it.

### Export and import

Workspace portability explicitly embeds a snapshot in BNDB or project metadata.
Selectable snapshot content includes:

- User chats and, optionally, background/system chats.
- Indexes, Code Maps, and workspace repositories.
- Notebook entries, tasks, and outcomes.
- Transaction history, which is off by default.

Export modes are:

- **My Team**: authored conversations plus complete non-conversation resources.
- **Just Me (transport)**: all selected content regardless of author.

Import merge strategies are:

- Keep newer.
- Keep existing.
- Overwrite.

The importer reports applied, skipped, and failed records. Multiple analysts can
export independently and combine snapshots with `Keep newer`. Semantic vectors
are not exported. Internal transactions and script-execution records are also
excluded.

Sources: [data storage](https://docs.sidekick.binary.ninja/reference/data_storage.html)
and [sharing analysis data](https://docs.sidekick.binary.ninja/guide/sharing_data.html).

## Service, offline, and write matrix

| Capability | Sidekick service required | Local data/database effect |
| --- | --- | --- |
| Built-in lead-agent Chat | Yes | Stores chats and derived workspace knowledge locally; approved tools may modify BNDB. |
| Automatic thread titles | Yes | Updates local chat metadata. |
| Suggest Repairs/Types/Imported Types/Names/Comments | Yes | Applies Binary Ninja database changes. |
| Background Notebook validation | Yes | Updates local outcome status/provenance. |
| Session briefing synthesis | Yes | Updates local briefing state. |
| Manual Notebook use | No | Updates local workspace database. |
| Manual/BNQL indexes | No | Updates local workspace database. |
| BNQL queries | No | Read-only unless results are saved to an index. |
| Code Maps | No | Updates local workspace resources. |
| Transaction Log browsing | No | Read-only browsing; deleting an entry removes audit history only. |
| Semantic indexing | No Sidekick cloud requirement | Builds local vectors; may contact configured model-download or custom embedding endpoints. |
| `sidekick.api` | Depends on chosen agent/model | Can be read-only or writable depending on API call and runtime policy. |
| Local/custom Library agents | No Sidekick cloud requirement | Effects depend on exposed tools and permissions. |
| MCP tools | No inherent Sidekick cloud requirement | Effects depend entirely on the configured server/tool. |
| Workspace export/import | No | Writes or reads snapshots in BNDB/project metadata and merges local records. |

Source: [getting started and service matrix](https://docs.sidekick.binary.ninja/tutorials/getting-started.html).

## Network and privacy inventory

Vector 35 states that online Sidekick sends only the context needed for a
request rather than the entire binary. Typical context includes the selected
function, disassembly or IL, referenced variables, query strings, and related
analysis material.

Online operation also collects documented metadata including:

- Sidekick plan API key.
- Binary Ninja serial, version, and edition.
- Sidekick plugin version.
- Python version.
- OS and architecture.
- IP address.
- Request size, user agent, and timestamp.
- Data required to execute the user's request.

The current legal terms distinguish data use:

- All tiers use submitted data to provide, secure, and maintain the service.
- Commercial-use data is licensed for providing the service.
- Non-commercial and limited-free use may also be licensed for product
  improvement and AI/ML training.
- Training data is described as sanitized of PII and anonymized first.
- Data not permitted for training is ordinarily deleted within 30 days.
- Permitted training data and request metadata may be retained indefinitely
  unless removal is requested.
- Third-party inference providers may receive data needed to provide the
  service under their own policies.
- The current Pro plan separately advertises `Data not used for training`.

Offline mode prevents Sidekick service requests, but configured local or
third-party endpoints and MCP servers are independent network boundaries. A
user must assess each one separately.

Sources: [official FAQ](https://sidekick.binary.ninja/faq/),
[terms and privacy policy](https://docs.sidekick.binary.ninja/about/legal-terms-and-conditions.html),
and [pricing](https://sidekick.binary.ninja/pricing/).

## Requirements, plans, and availability

The official FAQ and setup documentation currently state:

- Binary Ninja `5.3+` with an active license.
- Windows, macOS, and Linux support.
- All Binary Ninja editions except Free, because Free cannot load plugins.
- Python `>=3.10,<3.13`; the bundled Binary Ninja interpreter is recommended.
- Approximately 500 MB additional disk space for plugin dependencies, before
  optional model/index growth.
- The plugin can be installed through Binary Ninja's Plugin Manager.
- The plugin itself is free, but most built-in AI analysis requires a Sidekick
  service plan.

Pricing observed on 2026-08-10 was:

| Plan | Monthly | Annual effective monthly | Main distinction |
| --- | ---: | ---: | --- |
| Non-Commercial | USD 30 | USD 24 | Standard usage; non-commercial terms. |
| Pro | USD 100 | USD 80 | Four-times usage, commercial use, and no training on submitted data. |
| Max | USD 300 | USD 240 | Ten-times standard usage. |
| Self-Hosted | Custom | Custom | Private/air-gapped deployment and hardware-bounded unlimited usage. |

Prices, taxes, allowances, and conditions are volatile and must be checked on
the live pricing page. Self-hosted Sidekick uses concurrent-user licensing and
currently has a three-license minimum.

Sources: [getting started](https://docs.sidekick.binary.ninja/tutorials/getting-started.html),
[FAQ](https://sidekick.binary.ninja/faq/), and
[pricing](https://sidekick.binary.ninja/pricing/).

## Exact `Plugins > Sidekick` menu inventory

The current canonical menu reference lists:

### Chat and suggestions

- `New Sidekick Chat`
- `Suggest Repairs`
- `Suggest Types`
- `Suggest Imported Types`
- `Suggest Names`
- `Suggest Comments`

### Session

- `Open Sidekick View`
- `Open Session Briefing`
- `Configure Tool Permissions...`

### Workspace management

- `Import/Export Workspace Data...`
- `Reset Semantic Index for Workspace...`
- `Manage Workspaces...`

### Migration

- `Import 5.x Automation Workbench...`

### Configuration

- `Configure MCP Servers...`
- `Configure Automation Models...`
- `Configure Semantic Indexing...`

### Help and onboarding

- `Open Sidekick User Guide...`
- `Open Sidekick FAQ...`
- `Welcome to Sidekick!`

### Account and connection

- `Sign-in to Account...`
- `Configure API Key...`
- `Purchase a Service Plan...`
- `Toggle Online / Offline`

Source: [Sidekick menu reference](https://docs.sidekick.binary.ninja/reference/menu_reference.html).

## Documented limitations and non-capabilities

- Sidekick is not read-only. Suggestions and approved tools modify the BNDB,
  and workspace identity metadata is written when saving a file.
- It does not upload the entire binary as a normal service operation, but it
  does transmit request-derived code/data context and metadata while online.
- It does not automatically carry analysis data inside a BNDB; explicit
  snapshot export/import is required.
- It does not automatically cloud-sync independent analyst workspaces; the
  documented collaboration model is snapshot exchange and merge.
- Semantic indexing is disabled by default and depends on a working embedding
  and reranking configuration.
- Semantic indexes are not included in snapshots.
- The Transaction Log is an audit interface, not an undo controller.
- Manual Code Map payload updates are unavailable through v1 of the public
  Python API, even though they can be edited in the UI.
- Only currently open project binaries are queried.
- Binary Ninja Free cannot load the plugin.
- Hosted service usage is limited by plan.
- Model output and automated verification remain AI-produced analysis, not a
  correctness guarantee.
- Custom model endpoints provide flexible inference but do not necessarily
  reproduce Sidekick's hosted agent scaffolding or quality.
- MCP, Python, debugger, repository, and raw database tools materially expand
  the trust boundary when enabled.

## Implications for Axio Analyst

This inventory should inform prioritization, not become a requirement to clone
Sidekick. Sidekick's natural workflow comes from a connected system rather than
from chat styling alone:

1. Work has durable goals, state, and outcomes.
2. Claims are visibly tied to evidence and provenance.
3. Quick actions coexist with longer investigations.
4. Search, indexes, maps, and findings are navigable workspace objects.
5. Every mutation is permissioned and auditable.
6. Automation is reusable and inspectable.
7. Context survives across sessions and binaries.

For Axio Analyst, the highest-value read-only adaptations are:

- A calmer center-pane or well-composed sidebar with a persistent analysis
  home rather than several equally weighted boxes.
- Structured findings and evidence references beyond address extraction.
- A generated session summary with open questions and current focus.
- Searchable, locally stored conversations and findings with explicit privacy
  controls.
- Inspectable provider work, errors, cancellation, and usage without exposing
  implementation noise in the primary conversation.
- Reusable bounded analysis recipes that retain provider neutrality.

The following Sidekick-inspired features belong behind later, explicit Axio
version boundaries:

- BNDB mutation and reversible change transactions.
- Python or arbitrary tool execution.
- Debugger control.
- MCP access.
- Semantic whole-workspace indexing.
- Multi-agent investigations.
- Cross-binary workspaces and collaboration snapshots.

Axio should preserve its current distinctions unless a future release changes
them deliberately:

- Provider-neutral supervised CLI adapters instead of one required hosted
  service.
- Authentication delegated to each provider without credential persistence.
- Bounded, previewable context instead of implicit whole-workspace disclosure.
- No BNDB mutation in `0.9.x`.
- No arbitrary filesystem, shell, Python, debugger, or network tools.

## Official source index

- [Documentation home](https://docs.sidekick.binary.ninja/index.html)
- [What's New in 26.1](https://docs.sidekick.binary.ninja/whats-new-26-1.html)
- [Getting Started](https://docs.sidekick.binary.ninja/tutorials/getting-started.html)
- [How Sidekick Analyzes Binaries](https://docs.sidekick.binary.ninja/tutorials/agent-capabilities.html)
- [Understanding Tool Permissions](https://docs.sidekick.binary.ninja/tutorials/tool-permissions.html)
- [Working in the Sidekick View](https://docs.sidekick.binary.ninja/guide/sidekick_view.html)
- [Analyzing Binaries with Chat](https://docs.sidekick.binary.ninja/guide/chat.html)
- [Using Semantic Indexing](https://docs.sidekick.binary.ninja/guide/semantic_indexing.html)
- [Browsing Workspace Resources](https://docs.sidekick.binary.ninja/guide/resources.html)
- [Recording Analysis in the Notebook](https://docs.sidekick.binary.ninja/guide/notebook.html)
- [Editing Binaries with Suggestions](https://docs.sidekick.binary.ninja/guide/suggestions.html)
- [Building and Using Indexes](https://docs.sidekick.binary.ninja/guide/indexes.html)
- [Visualizing with Code Maps](https://docs.sidekick.binary.ninja/guide/code_maps.html)
- [Reviewing Changes in the Transaction Log](https://docs.sidekick.binary.ninja/guide/transaction_log.html)
- [Working with Multiple Binaries in a Project](https://docs.sidekick.binary.ninja/guide/multiple_binaries.html)
- [Sharing Analysis Data](https://docs.sidekick.binary.ninja/guide/sharing_data.html)
- [Scripting and Automation with the Sidekick API](https://docs.sidekick.binary.ninja/guide/sidekick_api.html)
- [Adding External Tools with MCP](https://docs.sidekick.binary.ninja/guide/mcp_tools.html)
- [Managing Scripts, Agents, and Skills in the Library](https://docs.sidekick.binary.ninja/guide/library.html)
- [Sidekick Menu Reference](https://docs.sidekick.binary.ninja/reference/menu_reference.html)
- [Data Storage](https://docs.sidekick.binary.ninja/reference/data_storage.html)
- [Settings](https://docs.sidekick.binary.ninja/reference/settings.html)
- [BNQL](https://docs.sidekick.binary.ninja/reference/bnql.html)
- [BNMF](https://docs.sidekick.binary.ninja/reference/bnmf.html)
- [About Sidekick](https://docs.sidekick.binary.ninja/about/index.html)
- [Terms and Privacy Policy](https://docs.sidekick.binary.ninja/about/legal-terms-and-conditions.html)
- [Product capabilities](https://sidekick.binary.ninja/product/capabilities/)
- [FAQ](https://sidekick.binary.ninja/faq/)
- [Pricing](https://sidekick.binary.ninja/pricing/)
