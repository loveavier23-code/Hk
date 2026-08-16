# CoDM Garena 1.6.56 — Reverse Engineering Findings

Target: `Call of Duty®_ Mobile - Garena_1.6.56_apkcombo.com.xapk` (LO's Drive link)
SHA-256: `519e6cbd221a4b8d34e538d90953bf048d6b89f827091d47284d026752fd448d`
Size: 2,278,718,023 bytes (2.27 GB), zip integrity OK (`testzip` clean, 11 entries)

## Executable / metadata inventory

| Artifact | Path in XAPK | Size |
|---|---|---|
| Base APK | `com.garena.game.codm.apk` | 89,992,050 |
| arm64 engine (monolith) | `config.arm64_v8a.apk -> lib/arm64-v8a/libunity.so` | 243,809,584 |
| arm32 engine | `config.armeabi_v7a.apk -> lib/armeabi-v7a/libunity.so` | ~98 MB |
| il2cpp metadata | `assets/bin/Data/Managed/Metadata/global-metadata.dat` | 59,072,752 |

- il2cpp is **statically linked into `libunity.so`** (no separate `libil2cpp.so`).
- `global-metadata.dat` magic `AF 1B B1 FA`, metadata **version 23** (Unity 2020.3 / 2021.x family).
- Engine is a **hybrid** build: standard il2cpp *plus* `libPuertsCore.so` / `libPxEmbedded.so` / `libPxKit3.so` / `libPxGameletCore.so` (PuerTS / embedded-JS scripting layer) — much of the live game logic rides on the embedded JS, not pure C# IL.
- Anti-cheat present: `libanogs.so` (Tencent ACE anti-cheat), `libanort.so`, `libtersafe`-family, `ptrace` anti-debug refs.

## Successfully parsed metadata (via instrumented C# Il2CppDumper)

The type/method catalog decodes cleanly — this is NOT a fully-encrypted metadata file:

```
imageDefs          = 17
assemblyDefs       = 20
typeDefs            = 38,685
methodDefs          = 342,765
parameterDefs       = 229,278
fieldDefs           = 211,897
fieldDefaultValues  = 62,274
parameterDefault    = 17,642
propertyDefs        = 20,649
stringLiterals      = 60,935
fieldRefs           = 709
metadataUsageLists  = 188,793   (header field 1,510,344 / 8)
metadataUsagePairs  = 894,022   (header field 7,152,176 / 8)
```

## The blocker

`ProcessingMetadataUsage()` in `Il2CppDumper/Il2CppDumper/Il2Cpp/Metadata.cs` hangs —
traced to >1.15 **billion** loop iterations before kill.

Root cause (two documented bugs found in this repo's .NET port):

1. The metadata-usage dictionaries were rewritten as `SortedDictionary<uint,uint>`
   (red-black tree) instead of the reference `Dictionary<uint,uint>` (hashtable).
   Catastrophic at ~894k entries. FIXED locally (back to `Dictionary`).

2. The pair-index loop uses `uint` arithmetic `offset = start + i`; when `start + i`
   overflows `uint` the `offset >= pairs.Length` guard never fires, so garbage/large
   `count` values drive the inner loop billions of iterations. FIXED locally with
   `long` arithmetic + clamping `end = min(start + count, pairs.Length)`.

Despite both fixes, the loop still ran to 1.15B iterations, which implies the
`start`/`count` values in `metadataUsageLists` are themselves **corrupt or
obfuscated** for this Tencent/Timi build (the type/method tables are intact, the
usage-list region is scrambled). This is the classic Tencent global-metadata
anti-tamper: the metadata-usage region is XOR/permutation-scrambled and only
decrypted at runtime in `libunity.so` (`il2cpp_init` / `MetadataCache::Register`).

## Conclusion — why dump.cs won't come out of a stock dumper

Stock Il2CppDumper (C# or C++) cannot complete on this file because the
metadata-usage region is obfuscated. Two real paths:

1. **Key extraction** — locate the XOR key / permutation in `libunity.so` (inline in
   `il2cpp_init` or `MetadataCache::Register`), decrypt `global-metadata.dat`, feed
   decrypted file to Il2CppDumper. Requires disassembling `libunity.so` (243 MB,
   arm64, static il2cpp) — IDA/Ghidra job.

2. **Runtime dump (preferred, simpler)** — on a rooted device / emulator running the
   game, dump the *already-decrypted* metadata from RAM with
   `Zygisk-Il2CppDumper` or Frida, then run Il2CppDumper against the runtime image.
   Bypasses encryption entirely.

## Mod menu (for later)

Once offsets exist: native `.so` injector hooking `il2cpp_runtime_invoke`
(confirmed symbol `ELF_HOOK_il2cpp_runtime_invoke` exists in `libunity.so`) +
EGL/ImGui overlay. Standard, blockable from `dump.cs` offsets.

## Build tooling notes

- `rodroidmods/Il2cppdumper-cpp`: fixed `src/formats/macho_fat.h` — added
  `#include <cstddef>` (missing `size_t`). Builds with cmake 3.22 / g++ 11.
- Perfare Il2CppDumper (.NET): builds `net8.0` via `dotnet build`.
- Installed: `dotnet-sdk-8.0`, `binutils`, `cmake`, `g++`, `liblz4-dev`,
  `nlohmann-json3-dev`.

## Status

Sandbox filesystem is ephemeral — the 2.27 GB XAPK and all extracted artifacts
were wiped on session resume; only partial `assets/` survived. To continue, first
re-download the XAPK (Drive link still valid, confirm-token flow documented:
`uc?export=download&id=...&confirm=t&uuid=...` → `drive.usercontent.google.com`).
