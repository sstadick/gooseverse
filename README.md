# Gooseverse

@sstadick's public [Goose](https://github.com/aardappel/goose) packages,
examples, and shared development practices.

This is a catalog, not a distribution or a version lockfile. Links and examples
follow each project's `main` branch; there are no pinned package versions,
submodules, or coordinated version numbers. Each package owns its releases,
compatibility policy, tests, and API reference.

## Packages

| Project | Purpose | Import / namespace |
| --- | --- | --- |
| [goose-doc](https://github.com/sstadick/goose-doc) | API references and executable documentation | `doc` |
| [goose-simd](https://github.com/sstadick/goose-simd) | Byte vectors, comparison masks, and accelerated searches | `simd_bytes` |
| [goose-bstr](https://github.com/sstadick/goose-bstr) | Byte-string search, splitting, and text handling | `bstr` |
| [goose-opts](https://github.com/sstadick/goose-opts) | Struct-derived command-line options and help | `opts` |
| [goose-io](https://github.com/sstadick/goose-io) | Synchronous files, buffered streams, and borrowed lines | `io` |
| [goose-bio](https://github.com/sstadick/goose-bio) | Implicit interval tree, FASTA/FASTQ reader, and radix sort | `bio`, then `bio.iitree`, `bio.fastx`, `bio.radix_sort` |

Runtime dependencies: **goose-io → goose-bstr → goose-simd**. In goose-bio,
only the FASTA/FASTQ reader has dependencies: goose-io and goose-bstr. All
packages use goose-doc for documentation; goose-doc also documents itself.

Use a current Goose compiler with package `c_headers` support. Save any example
below as `main.goose`, then run `goose run main.goose`. These are complete programs,
including explicit transitive package imports. Branch imports are cached: use
`goose fetch --update main.goose` to refresh them.

These examples deliberately follow `main`, not particular releases. A package
may request a different dependency ref; Goose warns when the root selects a
different ref of the same repository. This catalog tests its examples together,
but does not promise compatibility across arbitrary revisions. Applications
that need reproducibility should choose compatible immutable revisions themselves.

### goose-doc

Extract documented declarations from Goose source, generate Markdown API
references, and run documentation examples. The `goose-doc` command is the usual
entry point; the `doc` package also exposes the parser:

```goose
import doc from "github.com/sstadick/goose-doc@main";

fn main() {
    let entries = doc::parse("// Double a number.\nfn twice(n: i64) -> i64 { n * 2 }");
    assert(entries.len == 1);
    for entry in entries { assert(entry.name == "twice"); }
}
```

See its [API](https://github.com/sstadick/goose-doc/blob/main/API.md) and
[documentation workflow](https://github.com/sstadick/goose-doc#generate-your-first-reference).

### goose-simd

Compare byte lanes and combine masks. TinyCC uses scalar fallback; native
acceleration depends on the compiler and target. This package is experimental,
and its implementation and API may change.

```goose
import simd_bytes from "github.com/sstadick/goose-simd@main";

fn main() {
    let v = simd_bytes::load<simd_bytes::U8x16>("red,green;blue___");
    let separators = v.eq(',').bit_or(v.eq(';'));
    assert(separators.first() == 3);
    assert(separators.last() == 9);
    assert(separators.to_bits() == 520);
}
```

See the [API](https://github.com/sstadick/goose-simd/blob/main/API.md).

### goose-bstr

Search, split, and transform native byte slices without adding a string wrapper.
Operations accept arbitrary bytes, including NUL and invalid UTF-8. Search
positions are byte offsets; missing matches return `-1`.

```goose
import bstr from "github.com/sstadick/goose-bstr@main";
import simd_bytes from "github.com/sstadick/goose-simd@main";

fn main() {
    assert(bstr::find("café menu", "menu") == 6);
    let key, value, found = bstr::split_once_str("name=goose", "=");
    assert(found && key == "name" && value == "goose");
    assert(bstr::find("goose", "duck") == -1);
}
```

See the [API](https://github.com/sstadick/goose-bstr/blob/main/API.md).

### goose-opts

Describe command-line options with a struct. Parsing returns values, a help
request flag, and an error message; your application controls output and exits.

```goose
import opts from "github.com/sstadick/goose-opts@main";

struct Options {
    count: opts::Field<i64> = opts::Field<i64> {
        value: 1, short: "c", help: "Number of copies",
    },
}

fn main() {
    let argv = ["--count", "3"];
    let options, help_requested, error = opts::parse<Options>(argv);
    assert(error.len == 0 && !help_requested);
    assert(options.count.value == 3);
}
```

See the [API](https://github.com/sstadick/goose-opts/blob/main/API.md).

### goose-io

Read and write files incrementally. Buffered wrappers take ownership of their
file handles, and returned lines borrow the reader's buffer. Check close/flush
results as well as writes. **This example creates or overwrites `hello.txt`.**

```goose
import io from "github.com/sstadick/goose-io@main";
import bstr from "github.com/sstadick/goose-bstr@main";
import simd_bytes from "github.com/sstadick/goose-simd@main";

fn main() {
    let output, created = io::open_write("hello.txt");
    assert(created);
    let writer = io::buffered_writer(output);
    assert(writer.write("hello\n") == 6);
    assert(writer.close());

    let input, opened = io::open_read("hello.txt");
    assert(opened);
    let reader = io::buffered_reader(input);
    let line, status = reader.read_line();
    assert(status == io::LineStatus.Line && line == "hello");
    assert(reader.close());
}
```

See the [API](https://github.com/sstadick/goose-io/blob/main/API.md).

### goose-bio

Find the intervals that overlap a query, read FASTA and FASTQ records, and
sort integer keys. `bio` only names the package: import the modules you use,
each of which has its own namespace. `bio.iitree` and `bio.radix_sort` need no
other package; `bio.fastx` needs goose-io, goose-bstr, and goose-simd.

```goose
import bio from "github.com/sstadick/goose-bio@main";
import bio.iitree;

fn main() {
    let tree = iitree::IITree<i64> { .. };
    tree.add("chr1", 10, 20, 1);
    tree.add("chr1", 15, 30, 2);
    tree.add("chr2", 10, 20, 4);
    tree.index();

    var found = 0;
    tree.overlap("chr1", 18, 25) { interval => found += interval.value; };
    assert(found == 3);
    tree.overlap("chr1", 20, 25) { interval => found += interval.value; };
    assert(found == 5);
}
```

See the [API](https://github.com/sstadick/goose-bio/blob/main/API.md).

## Shared best practices

The [working-with-goose skill](.agents/skills/working-with-goose/SKILL.md)
covers naming, imports and UFCS, the package map, tests, documentation with
goose-doc, and dependency-ordered changes and releases.

Install it into an Amp project:

```sh
amp skill add sstadick/gooseverse/.agents/skills/working-with-goose
```

Add `--global` to install it for all your local projects. Other Agent Skills
clients can use the same skill directory and `SKILL.md`.

The compiler lives upstream at [aardappel/goose](https://github.com/aardappel/goose).
[sstadick/goose](https://github.com/sstadick/goose) is a contribution fork,
not a separately versioned Gooseverse package.

## Check the examples

With Python 3, Git, Goose, GCC, and Clang installed:

```sh
python3 tests/examples.py
```

The runner extracts the programs directly from this README and executes their
assertions using TinyCC, GCC, and Clang in temporary directories. It uses an
isolated package cache, so each invocation fetches the current branch heads.
Set `GOOSE=/path/to/goose` to select your compiler. CI builds upstream Goose
from its default branch and runs the same check; failures are visible instead of silently freezing
the catalog to an old package release.

MIT; see [LICENSE](LICENSE).
