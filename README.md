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
| [goose-io](https://github.com/sstadick/goose-io) | Synchronous files, absolute seeking, buffered streams, and borrowed lines | `io` |
| [goose-bio](https://github.com/sstadick/goose-bio) | Interval indexes, FASTA/FASTQ streaming, plain/BGZF indexed FASTA, and radix sort | `bio`, then `bio.iitree`, `bio.lapper`, `bio.fastx`, `bio.faidx`, `bio.radix_sort` |
| [goose-deflate](https://github.com/sstadick/goose-deflate) | Whole-buffer DEFLATE, zlib, gzip, and checksums through libdeflate | `deflate` |
| [goose-bgzf](https://github.com/sstadick/goose-bgzf) | Streaming BGZF reader/writer and virtual-offset seeking | `bgzf` |
| [goose-seqair](https://github.com/sstadick/goose-seqair) | Experimental BAM/SAM/CRAM readers/writers, BAI/CSI/CRAI indexed regions, and raw pileups | `seqair`, then `seqair.bam`, `seqair.sam`, `seqair.cram`, `seqair.cram_index`, `seqair.pileup` |
| [goose-bitvec](https://github.com/sstadick/goose-bitvec) | Packed bit vectors, range operations, popcount, and sparse set-bit iteration | `bitvec` |
| [goose-perbase](https://github.com/sstadick/goose-perbase) | Parallel base counts, run-length depth, and adjacent-interval merging for indexed BAM/CRAM | CLI: `goose-perbase` |
| [goose-raylib](https://github.com/sstadick/goose-raylib) | Graphics, input, audio, images, and vector/matrix math through raylib and raymath | `raylib` |

Runtime dependencies: **goose-io → goose-bstr → goose-simd**. In goose-bio,
the FASTA/FASTQ and indexed FASTA readers use goose-io and goose-bstr; indexed
FASTA also uses goose-bgzf/goose-deflate for BGZF reference access. All
packages use goose-doc for documentation; goose-doc also documents itself.
goose-deflate has no Goose runtime dependencies; it builds vendored libdeflate
with CMake and a native C compiler, including when using `goose run`.
goose-bgzf uses goose-io and goose-deflate, reusing buffers and codec handles
for block-based reading/writing and BAM-style virtual offsets.
goose-seqair builds on these packages for alignment I/O and uses goose-simd for
CRAM codecs. Its README documents format support and writer limitations.
goose-bitvec has no runtime package dependencies; mutations are worker-local,
not atomic. Its benchmarks distinguish dense scans from sparse enumeration.
goose-raylib also has no Goose package dependencies; it builds vendored raylib
with CMake 3.25+ and a native compiler. Its desktop build needs platform graphics
development libraries even when running the display-free image example below.

Use a current Goose compiler with package `c_headers` support. Save any example
below as `main.goose`, then run `goose run main.goose`. These are complete programs,
including explicit transitive package imports. Branch imports are cached: use
`goose fetch --update main.goose` to refresh them.

These examples deliberately follow `main`, not particular releases. A package
may request a different dependency ref; Goose warns when the root selects a
different ref of the same repository. This catalog tests its examples together,
but does not promise compatibility across arbitrary revisions. Applications
that need reproducibility should choose compatible immutable revisions themselves.

### goose-perbase

An experimental command-line port of [Perbase](https://github.com/sstadick/perbase),
built on goose-seqair, goose-bio, goose-bgzf and goose-bitvec. `base-depth` emits
per-position base counts, `only-depth` emits depth runs, and `merge-adjacent`
coalesces TSV intervals. Depth commands use worker-owned indexed BAM/CRAM readers
and deterministic output ordering. Plain and BGZF FASTA references and TSV
output are supported; compressed references require FAI/GZI indexes.

```sh
git clone https://github.com/sstadick/goose-perbase
cd goose-perbase
python3 scripts/build.py
build/goose-perbase base-depth reads.bam -t 8 -o bases.tsv
build/goose-perbase only-depth reads.cram -r reference.fa.gz -t 8 -o depth.tsv
build/goose-perbase merge-adjacent depth.tsv -o merged.tsv
```

The application pins its own dependencies; no sibling library checkout is needed.
See its [build requirements and compatibility limits](https://github.com/sstadick/goose-perbase#build-and-run)
and [differential tests and benchmarks](https://github.com/sstadick/goose-perbase/blob/main/bench/README.md).

### goose-bitvec

Set half-open ranges and enumerate only the set bits. Tail padding remains zero
when resizing; newly exposed bits default to clear.

```goose
import std;
import bitvec from "github.com/sstadick/goose-bitvec@main";

fn main() {
    let bits = bitvec::BitVec { .. };
    bits.reset(130); bits.set_range(63, 129);
    assert(bits.count_ones() == 66 && !bits.test(129));
    bits.resize(64); bits.resize(130);
    var positions: i64[>..] = [];
    bits.ones() { i => positions.push(i); };
    assert(positions.len == 1 && positions[0] == 63);
}
```

### goose-seqair

Read a SAM alignment into the same borrowed record interface used by BAM.
This example creates and removes a small file. Record views expire on the next
reader operation; use region stores when records must outlive a read.

```goose
import std;
import os;
import seqair from "github.com/sstadick/goose-seqair@main";
import seqair.bam;
import seqair.sam;
import bgzf from "github.com/sstadick/goose-bgzf@main";
import deflate from "github.com/sstadick/goose-deflate@main";
import io from "github.com/sstadick/goose-io@main";
import bstr from "github.com/sstadick/goose-bstr@main";
import simd_bytes from "github.com/sstadick/goose-simd@main";

fn main() {
    let path = "example.sam";
    assert(write_file(path, "@SQ\tSN:chrA\tLN:100\nr\t0\tchrA\t6\t40\t4M\t*\t0\t0\tACGT\tIIII\n"));
    defer delete_file(path);
    let reader = sam::Reader { .. }; defer reader.close();
    assert(reader.open(path) == bam::Status.Record);
    assert(reader.read() == bam::Status.Record);
    {
        let record = reader.record();
        assert(record.name() == "r" && record.fields.pos == 5);
        assert(record.base(2) == 'G' && record.quality(2) == 40);
    }
    assert(reader.read() == bam::Status.End);
}
```

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
each of which has its own namespace. `bio.iitree` is an interval tree over
named contigs; `bio.lapper` indexes one sequence's sorted intervals in blocks
for faster queries. They and `bio.radix_sort` need no other package;
`bio.fastx` needs goose-io, goose-bstr, and goose-simd.

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

### goose-deflate

Compress and decompress independent buffers with reusable handles and
caller-owned storage. Native builds inline the C adapters, leaving direct
libdeflate calls. This is whole-buffer compression, not streaming gzip or a
BGZF reader. Decompression validates the gzip checksum and stops after one
member; use `consumed` to advance through concatenated members.

```goose
import deflate from "github.com/sstadick/goose-deflate@main";

fn main() {
    let c, ok = deflate::compressor(1);
    let d, ready = deflate::decompressor();
    assert(ok && ready);
    defer c.close();
    defer d.close();

    let input = "ACGTACGTACGT\n";
    var compressed: u8[128] = [0; 128];
    let n = c.compress(deflate::Format.Gzip, input, compressed);
    assert(n > 0);
    var output: u8[64] = [0; 64];
    let result = d.decompress(deflate::Format.Gzip, compressed[..n], output);
    assert(result.status == deflate::Status.Success);
    assert(result.consumed == n && result.written == input.len);
    assert(output[..result.written] == input);
    assert(deflate::crc32("123456789") == 0xcbf43926);
}
```

See the [API](https://github.com/sstadick/goose-deflate/blob/main/API.md) and
[direct-C performance comparison](https://github.com/sstadick/goose-deflate/blob/main/bench/README.md).

### goose-bgzf

Read and write BGZF incrementally, with checked block framing and checksums.
Virtual offsets address compressed blocks plus positions inside them; they are
not ordinary byte distances. `read_some` reports the initialized prefix length.
Check writer close for final errors. This example creates/truncates and removes
`example.bgz`.

```goose
import std;
import os;
import bgzf from "github.com/sstadick/goose-bgzf@main";
import io from "github.com/sstadick/goose-io@main";
import bstr from "github.com/sstadick/goose-bstr@main";
import simd_bytes from "github.com/sstadick/goose-simd@main";
import deflate from "github.com/sstadick/goose-deflate@main";

fn main() {
    let path = "example.bgz"; defer delete_file(path);
    let writer = bgzf::Writer { .. }; defer writer.close();
    assert(writer.open(path, 1) == bgzf::Status.Ready);
    assert(writer.write("first\n") == bgzf::Status.Ready);
    let offset = writer.tell();
    assert(writer.write("second\n") == bgzf::Status.Ready);
    assert(writer.close() == bgzf::Status.Ready);

    let reader = bgzf::Reader { .. }; defer reader.close();
    assert(reader.open(path) == bgzf::Status.Ready);
    assert(reader.seek(offset) == bgzf::Status.Ready);
    var bytes: u8[32] = [0; 32];
    let n, status = reader.read_some(bytes);
    assert(status == bgzf::Status.Ready && bytes[..n] == "second\n");
    let count, end = reader.read_some(bytes);
    assert(count == 0 && end == bgzf::Status.End);
}
```

See the [API](https://github.com/sstadick/goose-bgzf/blob/main/API.md) and
[performance baseline](https://github.com/sstadick/goose-bgzf/blob/main/bench/README.md).

### goose-raylib

Use raylib's graphics, input and audio APIs and raymath's vector/matrix functions.
Native builds inline the packed-to-C value adapters through `c_headers`;
TinyCC calls exports generated from the same adapters. Resources are manually
owned: unload each once, normally with `defer`. Pointer-based `_raw` calls retain
the native C ownership and memory-layout requirements; Goose callbacks are not
supported.

This example creates and edits CPU image pixels without opening a window:

```goose
import raylib from "github.com/sstadick/goose-raylib@main";

fn main() {
    var image = raylib::gen_image_color(7, 5, raylib::BLUE);
    defer raylib::unload_image(image);
    assert(raylib::is_image_valid(image));
    raylib::image_draw_pixel(image, 6, 4, raylib::RED);
    assert(raylib::get_image_color(image, 6, 4) == raylib::RED);
    assert(raylib::get_image_color(image, 5, 4) == raylib::BLUE);
    raylib::image_crop(image, raylib::Rectangle { 4.0, 3.0, 3.0, 2.0 });
    assert(image.width == 3 && image.height == 2);
    assert(raylib::get_image_color(image, 2, 1) == raylib::RED);
}
```

See the [API](https://github.com/sstadick/goose-raylib/blob/main/API.md),
[coverage and omissions](https://github.com/sstadick/goose-raylib/blob/main/COVERAGE.md),
and [window example](https://github.com/sstadick/goose-raylib/blob/main/examples/window.goose).
The [build instructions](https://github.com/sstadick/goose-raylib#run) list platform dependencies.

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

With Python 3, Git, Goose, CMake 3.25+, GCC, Clang, and raylib's platform
development libraries installed:

```sh
python3 tests/examples.py
```

The runner extracts the programs directly from this README and executes their
assertions using TinyCC, GCC, and Clang in temporary directories. It uses an
isolated package cache, so each invocation fetches the current branch heads.
Set `GOOSE=/path/to/goose` to select your compiler. CI builds upstream Goose
from its default branch and runs the same check; failures are visible instead of silently freezing
the catalog to an old package release.
Use `python3 tests/examples.py --cc clang` to run TinyCC and Clang only.

MIT; see [LICENSE](LICENSE).
