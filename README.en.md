# Nightreign Parry Frames — which animation does each shield / Ash of War actually use?

Community reverse-engineering notes, data tables and patch scripts for **Elden Ring: Nightreign** (2025).
Everything here was derived from the game files on a retail install; **no game files are included** in this repository.

* Code: **MIT** — see [`LICENSE`](LICENSE)
* Data & docs: **CC BY 4.0** — see [`data/LICENSE`](data/LICENSE)

---

## TL;DR — two rules decide everything

1. **Skill → TAE bank:** &nbsp;`bank = 600 + SwordArtsParam.swordArtsType`
   (verified on **191 / 194** rows of `SwordArtsParam`; the 3 misses are the `No Skill` sentinel `swordArtsType = 255` and one nameless placeholder row)
2. **Weapon class → which entry inside that bank:** &nbsp;`animId = base + 100 × wepmotionCategory`
   * `base` = `40000` one-shot / `40030` both-hand / `40040` left-hand
   * `+5` for the **out-of-FP ("no MP")** variant → `40005 / 40035 / 40045`

| Purpose | Skill id | Bank | Animation (normal / out-of-FP) | Window (frames, 30 fps) |
|---|---|---|---|---|
| Fist / Claw / Medium Shield / Thrusting Sword parry | 302 `[Standard] Parry` | a692 | `a692_040000` / — | 4→6 |
| Curved Sword parry | 302 | a692 | `a692_042800` | 4→6 |
| Dagger parry | 302 | a692 | `a692_042000` | 4→8 |
| **Small Shield parry** | 302 | a692 | **`a692_044800`** | 5→10 |
| Buckler parry | 303 `[Standard] Buckler Parry` | a693 | `a693_040000` | 4→9 |
| Carian Retaliation | 305 `[Magic] Carian Retaliation` | a695 | `a695_040000` / `a695_040005` | 4→10 / 6→8 |
| Storm Wall | 306 `[Standard] Storm Wall` | a696 | `a696_040000` / `a696_040005` | 4→9 / 5→10 |
| Golden Parry | 307 `[Holy] Golden Parry` | a697 | `a697_040000` / `a697_040005` | 4→7 / 5→10 |
| Thops's Barrier | 309 `[Magic] Thops's Barrier` | a699 | `a699_040000` / `a699_040005` | 4→8 / 6→10 |

Skill → bank, for the whole shield family (all banks verified to exist as `aNNN.tae`):

| skill | name | `swordArtsType` | bank |
|---|---|---|---|
| 300 | `[Standard] Shield Bash` | 90 | a690 |
| 301 | `[Standard] Barricade Shield` | 91 | a691 |
| **302** | `[Standard] Parry` | 92 | **a692** |
| **303** | `[Standard] Buckler Parry` | 93 | **a693** |
| — | *(skill 304 does not exist)* | — | *(a694.tae exists but has no skill)* |
| **305** | `[Magic] Carian Retaliation` | 95 | **a695** |
| **306** | `[Standard] Storm Wall` | 96 | **a696** |
| **307** | `[Holy] Golden Parry` | 97 | **a697** |
| 308 | `[Standard] Shield Crash` | 98 | a698 |
| **309** | `[Magic] Thops's Barrier` | 99 | **a699** |
| 1196 | `[Specific] Golden Retaliation` | 196 | a796 |

`wepmotionCategory` values used above (from the NR param enum + `EquipParamWeapon`):

| value | meaning | example weapon |
|---|---|---|
| 20 | Dagger | `[Common] Dagger` |
| 22 | Claw | `[Common] Hookclaws` |
| 27 | Thrusting Sword | `[Common] Estoc` |
| 28 | Curved Sword | Bandit's Curved Sword |
| 42 | Fist | `[Unarmed] Unarmed` |
| 47 | Greatshield | Dragon Towershield |
| **48** | **Small Shield** | Buckler / Perfumer's Shield / Wylder's Small Shield |
| **49** | **Medium Shield** | Round Shield / Heater Shield |

> **Frame convention.** This repo records the window as stored in the TAE file (`Start` → `End`, in frames at 30 fps).
> Community spreadsheets usually list `Start + 1` and `End`, and their "frame count" is `End − Start + 1` (inclusive).
> Example: spreadsheet `6→10` = this repo's `5→10` = 5 frames.

---

## 1. Where the parry window actually lives

A TAE animation carries an **event table**. The parry judgement is:

| Event | Meaning |
|---|---|
| `AttackBehavior` (**type 1**, parameter `+0x00 = 64`) | the parry attack/behaviour |
| `JumpTable flag 119` = `TryToInvokeForceParryMode` | "parry ready" window — **in vanilla it shares the same Start/End slot as the AttackBehavior above** |
| `JumpTable flag 3` = `Set Guard Type` | guard / deflect / hyper-armour window (this is what "Deflect Frames" mods edit) |
| `JumpTable flag 18` = `Anim Cancel After Successful Parry` | separate window |
| `JumpTable flag 5` = `Parry Window` | lives on the **victim** side, not in these animations |

Extending the parry window therefore means changing the shared `Start`/`End` slot of `AttackBehavior` + `Flag 119`
(**Start is best left alone** — moving the opening frame is a different, harder-to-attribute change).

The four FP-costing skills also have their own **VFX windows**, which do **not** equal the parry window
(Golden `5→7`, Storm Wall `1→10`, Thops `4→16`, Carian `5→10`, spreadsheet convention) — so a longer parry window
does not automatically make the visual effect last longer.

---

## 2. Two ways to patch the window — and the trap

The event table stores **offsets**, not inline values: each event header holds three offsets
(`start_off`, `end_off`, `data_off`) into a shared pool of time floats. **One instant exists only once in the file**,
and several events can point at it — the timeline is contiguous, so `AttackBehavior.end` may be the very same float
as the next phase event's `start`.

**(a) Overwriting the float — the tempting way, with a side effect.**
Writing a new `f32` at `end_off` also moves everything else that points at that instant.
Audited on 33 shield-related entries: **only 6 are clean**; **24** would drag the `start` of a
`type 129 = "Play Sound - By State Info [Wwise]"` event past its own end (audio timing corruption; the game does not
crash, but it is wrong). A smart patcher should *refuse* to write when it detects this.

**(b) Repointing `end_off` — the recommended way.**
Instead of changing a float, rewrite the event header's `end_off` **offset field** so it points at an **already
existing** instant whose value is the length you want. Because NR/ER TAEs use 64-bit varints (fixed 8-byte fields),
this is still an in-place, length-preserving edit — and **nothing else in the file changes**.

```powershell
python tools\patch_frames_repoint.py --bank a692 `
  --anim 40000 40005 40030 40035 40040 40045 44800 44830 44840 `
  --to 20 --out mods\all_shields_uniform20f --apply
# repeat for a693 / a695 / a696 / a697 / a699 (missing animations are skipped automatically)
```
`--to` is the target end frame. The script picks the closest **existing** instant in that animation, prints the frame
it actually landed on, and asserts that only the intended pointer fields differ (byte-level diff).

---

## 3. Behaviour-graph confirmation (optional, but it is the strongest evidence)

Convert `Behaviors\c0000.hkx` to XML with [HKLib.CLI](https://github.com/The12thAvenger/HKLib/releases) (`v0.1.3-NR`)
and parse it with `tools/beh_xml_map.py`:

* 33,380 objects, **21,470 `hkbClipGenerator`**, **3,969 `CustomManualSelectorGenerator` (CMSG)**.
* A CMSG represents **one animId** and holds *all* clip generators with that animId (i.e. several banks at once);
  the reference chain is `CMSG.m_generators[] → hkbClipGenerator.m_animationName`.
* The bank is picked by the character's active tae ids; the *category* is picked by the index of a
  `hkbManualSelectorGenerator` named e.g. `SwordArtsOneShotShieldLeft CategorySelector`
  (its `indexselector` is `null` — the index is set at runtime).
* Result: **`SwordArtsOneShot_48_CMSG` (48 = Small Shield) references exactly one parry animation: `a692_044800`**;
  `_20_` (Dagger) → `a692_042000`; `_28_` (Curved Sword) → `a692_042800`. The generic `SwordArtsOneShot_CMSG`
  (animId 40000) references six banks; the `_NoMP` list (animId 40005) references only the four FP-costing banks.
* Dead data: `a002_040392`, `a003_040392`, `a020_035200/035201/035202` have **zero references** in the whole graph.
* Categories **2–9** (`_02_`…`_09_` CMSGs) exist and are reachable, but **no NR weapon uses them**
  (the NR enum only has 0 and 20–52) — ER leftovers, never played.

---

## 4. Reproduce the whole pipeline

1. **Unpack** `Game\chr\c0000.anibnd.dcx` with [WitchyBND](https://github.com/ividyon/WitchyBND)
   → `Target\INTERROOT_win64\chr\c0000\tae\*.tae`.
   (WitchyBND refuses to run with redirected output — run it from the context menu / a real terminal.)
2. **Behaviour graph (optional):** drop `c0000.hkx` on `HKLib.CLI.exe`.
   Its target framework is **net7.0**; if only .NET 6/8/9 is installed, set `$env:DOTNET_ROLL_FORWARD='Major'`
   (no need to install .NET 7). Output is **tagfile XML** (`<hktagfile>/<type>/<object>/<field>/<string>/<pointer>`),
   not the packfile `hkobject/hkparam` style.
3. **Parse / inspect:** `python tools\beh_xml_map.py c0000.xml parry` (or `probe`, `anim`, `map`, `find`).
4. **Patch:** `python tools\patch_frames_repoint.py …` (see above).
5. **Repack & load:** WitchyBND the tree back to `c0000.anibnd.dcx`, load it with
   [ME3](https://github.com/garyttierney/me3) at the path **`mods\chr\c0000.anibnd.dcx`**.
   **Play offline with EAC disabled** — editing `c0000` is always detectable.

---

## 5. What is in this repository

| Path | Contents |
|---|---|
| `data/parry_skill_map.csv` | **the main table**: spreadsheet row → skill → bank → animation → window → mechanism → evidence level |
| `data/parry_47_animations.csv` | all 47 player parry animations with bank, action file (`hkt`), judge id, window |
| `data/parry_patch_list.csv` | the 33 entries to patch for "all shields the same", with target frames |
| `data/parry_cmsg_map.csv` | behaviour-graph result: which CMSG references which of the 47 animations |
| `data/parry_cmsg_expected.csv` | the prediction table (22 animIds) written *before* the graph was parsed — used as a test |
| `data/parry_events_catalogue.csv` | raw dump: 12,869 parry/guard-related events across all 523 `c0000` TAEs (14 columns) |
| `data/bank_report.txt` | per-bank statistics for all 523 TAEs |
| `tools/` | TAE parser, pointer-repoint patcher, safety auditor, behaviour-graph mapper, verification scripts |
| `tools/README.md` | what each script does, plus the two gotchas (float vs pointer, frame convention) |
| `docs/post-drafts.md` | ready-to-post text for Reddit / Nexus / wiki (bilingual) |

---

## 6. Known limits / open questions

* **VFX windows** of the four FP-costing skills are not mapped to a specific TAE event yet.
* `a534_049980` is referenced by `AutoParyy_Idle_CMSG` ("auto parry idle") — owner mechanism unknown.
* `a907` (`AddDemonSwordMode_ParryStance_CMSG` …) belongs to a character-specific (Executor) system — out of scope for now.
* **Medium shields use the generic entries** (`a692` `40000/40030/40040`), which are shared with fists / claws /
  thrusting swords — patching them affects those weapons too (their vanilla windows are identical anyway).
* The rule `bank = 600 + swordArtsType` is **not universal**: 1xx and 2xx skill families do not map onto banks that way
  (e.g. no `a59x` TAEs exist at all). It is verified for the shield family used here.
* "Patching the window changes the in-game feel" is supported by community tests and by the semantics of the events —
  but the author did **not** independently verify every patched entry in game. Test before you rely on it.

---

## 7. Evidence levels

* **machine-read** — read directly from the file bytes / CSV parameters (skill→bank rule, animId encoding,
  windows, Flag 3 windows, CMSG references, dead data).
* **derived** — forced by combining machine-read data (e.g. "Storm Wall = a696" is the only bank holding both
  required windows).
* **community-tested** — e.g. "Buckler = a693", "Carian = a695", "Golden = a697" were reported by other players;
  this repo reproduces them from data but does not claim its own in-game verification.

---

## 8. Credits & disclaimer

* [HKLib / ERClipGeneratorTool](https://github.com/The12thAvenger/HKLib) (The12thAvenger) — hkx → XML for Nightreign,
  and the authoritative explanation of the CMSG mechanism.
* [WitchyBND](https://github.com/ividyon/WitchyBND) (ividyon) — BND4/DCX unpack & repack.
* [Smithbox](https://github.com/vawser/Smithbox) — official param enums and the NR TAE template used to name events.
* [soulsmodding wiki](https://www.soulsmodding.com/) — TAE / Havok Behaviour reference.
* Community frame spreadsheets (credited in the Chinese notes) — used for cross-checking the window values.

This project is **unofficial** reverse-engineering material and contains **no FromSoftware game files**.
*Elden Ring* / *Nightreign* and related names are trademarks of FromSoftware / Bandai Namco; this project is not
affiliated with them. Modifying `c0000` is detectable by anti-cheat — **play offline with EAC off**, at your own risk.

---

## Cite as

> kazamiwong (2026). *Nightreign Parry Frames — TAE banks, animIds and windows.*
> https://github.com/kazamiwong/NIGHTREIGN-parry

