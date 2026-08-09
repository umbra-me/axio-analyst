# Axio Analyst demo binary

This is a small, harmless C++ console application for testing Binary Ninja and
Axio Analyst. The Release build contains several non-inlined functions with
useful reversing shapes:

- a case-insensitive custom name hash;
- a derived six-digit access code;
- validation with input checks and a branchless equality test;
- a byte-by-byte banner decoder;
- a score calculation with nested branches;
- a four-way score classifier.

## Build and run

From this directory:

```powershell
.\build.ps1
.\build\Release\axio_analyst_demo.exe --demo
```

Requirements are CMake and a Visual Studio installation with the MSVC C++
toolchain. `build.ps1` configures an x64 Release build and leaves all generated
files under `build/`.

Expected `--demo` output:

```text
Axio Analyst Demo!
user: analyst
access: granted
signal: critical (26)
```

Open `build/Release/axio_analyst_demo.exe` in Binary Ninja. The `build/`
directory is intentionally ignored because the executable is a generated local
test artifact.

For a separate Windows test instance, pass the generated binary as a positional
argument:

```powershell
& "$env:LOCALAPPDATA\Programs\Vector35\BinaryNinja\binaryninja.exe" `
  -n -d .\build\Release\axio_analyst_demo.exe
```

Binary Ninja's built-in command-line help lists `files` as optional positional
arguments and defines `-l, --debug-log <file>` as **Log output to <file>**.
Do not put the fixture immediately after that option: it can overwrite this
disposable executable with log output. If that occurs, close the test instance
and force a clean generated build before rerunning `build.ps1`:

```powershell
cmake --build build --config Release --target clean
.\build.ps1
```

For a release smoke test, open the `AX` sidebar and confirm its header version
matches `plugin.json`, the Settings introduction repeats that version, and the
Binary Ninja log contains the versioned registration message. This validates
host loading and widget construction without sending the fixture to a provider.
Provider requests remain a separate, explicit test action.

The 2026-08-10 live pass verified the registration log, resting sidebar,
function switching, a one-item/3,275-character primary preview, an
eight-item/14,195-character all-pack preview, Settings summaries, and no BNDB
creation. See [`docs/gui-verification.md`](../../docs/gui-verification.md) for
the complete evidence and deferred interaction checks.

Useful Axio Analyst questions include:

- "Explain the function that validates the six-digit code."
- "What input reaches the success path?"
- "Recover the algorithm used to decode the hidden banner."
- "Explain how the signal score is calculated and classified."

Release optimization makes the binary realistic enough to exercise HLIL while
the `NOINLINE` markers keep the important functions available for inspection.

## Function guide

| Source function | Reversing shape |
| --- | --- |
| `rotate_left` | Small bit-manipulation primitive. |
| `hash_name` | Case-normalized iterative hash with multiply, rotate, and xor. |
| `compute_access_code` | Hash-derived bounded six-digit value. |
| `parse_six_digits` | Length and character validation plus decimal accumulation. |
| `validate_access_code` | Early validation branches and branchless equality reduction. |
| `decode_banner` | Stateful byte-by-byte XOR decoder. |
| `calculate_signal_score` | Loop with nested thresholds and delta checks. |
| `classify_signal` | Ordered four-way threshold classifier. |
| `run_demo` | Deterministic caller that exercises every core routine. |
| `main` | Exact `--demo` dispatch and interactive access-check paths. |

The fixture is intentionally transparent in source and contains no real
credential or exploit. Its purpose is to compare an Axio Analyst explanation
with known behavior and to exercise incomplete-context questions by selecting
individual functions.

## Clean rebuild

Generated files stay under `build/`. To rebuild from scratch, remove only that
exact generated directory after closing the demo process, then rerun
`build.ps1`. Never commit the generated executable or CMake build tree.
