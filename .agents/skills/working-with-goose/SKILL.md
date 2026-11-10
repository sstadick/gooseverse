---
name: working-with-goose
description: Develops Gooseverse packages using shared naming, imports, tests, and goose-doc conventions. Use when creating or changing Goose packages, examples, documentation, or cross-package releases.
---

# Working with Goose

Use the package's current source, CI, and API documentation as the contract;
this skill describes shared Gooseverse practices, not a frozen language version.

## Know the packages

| Repository (under github.com/sstadick) | Entry / namespace | Role |
| --- | --- | --- |
| goose-doc | `doc.goose` / `doc` | API generation, source parser, executable docs |
| goose-simd | `simd_bytes.goose` / `simd_bytes` | Byte vectors, masks, searches |
| goose-bstr | `bstr.goose` / `bstr` | Native byte-string operations |
| goose-opts | `opts.goose` / `opts` | Struct-derived CLI parsing and help |
| goose-io | `io.goose` / `io` | Files, buffered readers/writers, borrowed lines |
| goose-bio | `bio.goose` / `bio` | Interval tree, FASTA/FASTQ reader, radix sort |

Runtime dependencies run `goose-io → goose-bstr → goose-simd`. goose-bio's
entry is empty: programs import `bio.iitree`, `bio.fastx`, or `bio.radix_sort`,
which keep their own namespaces, and only `bio.fastx` requires goose-io and
goose-bstr. All six use goose-doc for documentation. The current catalog and
complete runnable examples are at https://github.com/sstadick/gooseverse. Read
the relevant package's README, API.md, tests, and `.github/workflows/ci.yml`
before changing it.
Use https://github.com/aardappel/goose for language and standard-library facts;
sstadick/goose is a contribution fork. Check the actual compiler revision when
relying on a new language feature.

## Names and public APIs

- Repositories use `goose-topic`; entry files and short namespaces use
  `snake_case`. Avoid reserved words: use `simd_bytes`, not `simd`.
- Use `snake_case` for functions, variables, fields, and modules; use
  `PascalCase` for structs and enums. Follow the surrounding API's established
  spelling for constants and enum variants. These are Gooseverse conventions,
  not a claim that the language enforces a universal style guide.
- Do not repeat the package name inside every function: prefer
  `bstr::find(bytes, pattern)`, not `bstr::bstr_find(...)`.
- Preserve existing public names and semantics unless an API change is part
  of the task. Keep namespace migrations separate from behavioral refactors.
- Use native types where appropriate: `const u8[:]` for borrowed bytes and
  `u8[>..]` for a growable owned builder. State ownership, lifetime, offsets,
  sentinel values, and encoding assumptions in API comments.
- Namespace changes can change generated C identifiers. Inspect `.build`
  sidecars and native adapters as well as Goose code; match an entry-file
  rename with its sidecar. Verify compiled native code, not just TinyCC.

## Imports and UFCS

An import selects an entry file; it does not rename the namespace declared
inside it. Do not invent import aliases, namespace opening, nested namespaces,
or re-export shims. A program's root file must declare transitive packages too:

```goose
import bstr from "github.com/sstadick/goose-bstr@main";
import simd_bytes from "github.com/sstadick/goose-simd@main";
```

`@main` is a moving branch, cached until `goose fetch --update program.goose`.
Gooseverse examples intentionally track branches, with no package version pins.
That does not remove reproducibility requirements from package CI, releases,
or applications: select compatible immutable revisions there. A different ref
of the same dependency source produces a warning; a different source is an
error. Read warnings and test the combination rather than assuming compatibility.

Use explicit qualified functions for primitives and borrowed byte slices:
`bstr::find(bytes, pattern)`. Importing bstr does not attach its functions to
all byte slices. Use receiver-directed UFCS for package-owned structs/enums,
such as `mask.first()` or `reader.read_line()`; qualified calls remain valid.
Do not add wrapper types merely to give a byte slice methods.

## Documentation with goose-doc

1. Put `//` comments immediately above declarations. Describe observable
   behavior, then include a fenced `goose` example with assertions.
2. Maintain `api.txt` with qualified public names. A name selects all overloads;
   the file is an API documentation allowlist, not language access control.
3. Put imports and other top-level declarations in `tests/doc_preamble.goose`.
   Example fences contain statements for `fn main()`, not complete programs.
   Include transitive imports. A local `import topic from "..";` resolves the
   package because doctest temporary directories live under the package root.
4. Prefer existing `scripts/docs.sh` and `scripts/doctest.sh`. Set `GOOSE` to
   the intended compiler and `GOOSE_DOC` to the checkout's `main.goose`. Inspect
   each script's contract rather than assuming a global installation.
5. Regenerate committed API.md after changing public source or comments, then
   run the stale-document check and execute documentation examples.

For a new library `topic.goose`, with goose-doc checked out next door, generate:

```sh
goose run ../goose-doc/main.goose -- --title "Topic API" --symbols api.txt \
  --require-docs --require-examples --output API.md topic.goose
```

Check the committed output without rewriting it by adding `--check`. Execute
examples with TinyCC, then native compilers supported by the package:

```sh
python3 ../goose-doc/doctest.py --symbols api.txt \
  --preamble tests/doc_preamble.goose --require-examples topic.goose
python3 ../goose-doc/doctest.py --symbols api.txt \
  --preamble tests/doc_preamble.goose --require-examples --cc gcc topic.goose
python3 ../goose-doc/doctest.py --symbols api.txt \
  --preamble tests/doc_preamble.goose --require-examples --cc clang topic.goose
```

The standalone CLI is built with `goose build main.goose -O2 -o goose-doc`
from its checkout. Generation parses source; it does not typecheck the library
or run examples. Execute only trusted documentation: doctests are not sandboxed.
Keep relative source links in committed API.md. Generate release attachments
from the release checkout with `--source-url` pointing to that exact Git commit.

## Tests and compatibility

- Run existing checks before and after a change with the same compiler and
  frozen dependencies. Separate pre-existing failures from regressions.
- Execute examples with assertions enabled. Cover both sides of relevant
  boundaries, using independently derived expected values.
- Keep regression tests through public APIs. Prefer extending existing cases
  over tests of internal helpers or incidental output formatting.
- For byte strings, preserve arbitrary bytes, UTF-8 behavior, byte offsets,
  empty patterns, and borrowed lifetimes. Run bstr's differential tests.
- For SIMD, check scalar/native paths, lane masks, tails, alignment, and
  supported runtime dispatch/AVX2 checks; do not require AVX2 unconditionally.
- For I/O, exercise partial writes, flush/close errors, LF/CRLF/lone CR, EOF,
  buffer boundaries, and ownership transfer. Borrowed lines expire on the next
  reader operation; copying the slice does not copy its data.
- For options, test errors as well as parsing, help, repeated options, and
  shell completions required by its CI.
- Use each repository's actual CI matrix. Run available checks locally and
  report unavailable platforms as pending. When publishing is authorized,
  push locally tested changes so CI can run the remaining checks; missing
  local platforms alone are not a reason to withhold the branch. Do not
  claim full coverage or merge/release with required checks failing.

## Cross-package changes and releases

Change documentation tooling first when needed, then SIMD, bstr, I/O, and
bio; options only needs docs. Use compatible published release tags for runtime
dependencies and match those tags in tests, examples, and transitive root imports.
Keep compiler and documentation-tool CI pins on exact commits. During unreleased
coordinated repairs, published upstream repair commits can be temporary pins;
switch to the upstream release tag before releasing the downstream package.
Publish in dependency order and identify dependent PRs. Never move published tags;
dependency-only changes to released packages need new patch releases.
Keep the Gooseverse catalog unpinned even when individual libraries use pins.

Read tags and release workflows before choosing new version numbers. Breaking
import/namespace changes need explicit migration notes and an appropriate
version bump; never move old tags. Release only tested revisions, with required
CI passing and publication authorized. Repository redirects preserve URLs, not
old entry-file names at new revisions. Nightly maintenance should reuse its
existing rolling PR rather than open one per night.
