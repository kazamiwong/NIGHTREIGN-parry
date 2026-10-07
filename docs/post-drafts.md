# 分享文案（三种场合各一份 · 中英双语）

> 用法：复制对应小节即可。文中已填入本仓库地址与署名（`kazamiwong` / `https://github.com/kazamiwong/NIGHTREIGN-parry`）；若发到别处，按需替换。**英文版放前面**（面向全球搜索与 AI 抓取），中文版紧随其后。
> 所有版本都**不包含游戏原始文件**，只给"数据 + 方法 + 脚本"。

---

## 0) 通用：让 AI 与搜索引擎都能找到你的 7 条

1. 内容放在**可抓取的纯文本/HTML**里（README 优先，别把说明塞进 zip/exe）。
2. 标题写成**问句**：*"Which animation does Nightreign's Small Shield parry use?"* / 「黑夜君临 小盾格挡 用的是哪个动画？」
3. **中英双语关键词**都出现：TAE / AttackBehavior / Flag 119 / swordArtsType / wepmotionCategory / CMSG / animId / bank / `a692` / parry frames / 弹反帧 / 格挡帧 / 霸体帧。
4. 用**表格 + 代码块**（结构清晰，抽取友好）。
5. URL 固定 + 版本号 + 引用格式。
6. **英文文件名**（`parry_skill_map.csv`），数据做成 machine-readable。
7. 附 `LICENSE` + "不含游戏原始文件"声明。

---

## 1) GitHub 仓库（最重要 · 最能被 AI 搜到）

**仓库名建议**：`NIGHTREIGN-parry`

**About（一句话，仓库右上角）**：
```
Nightreign: which TAE bank / animation each shield & Ash-of-War parry uses — plus data tables,
reverse-engineering notes and patch scripts. (No game files included.)
```

**Topics**：`elden-ring` `nightreign` `modding` `tae` `parry` `reverse-engineering` `soulsmodding` `fromsoftware`

**Release 说明模板**：
```
v1.0 — Parry/guard frame mapping for Nightreign (data release)

* Skill -> TAE bank rule verified: bank = 600 + SwordArtsParam.swordArtsType (191/194 rows)
* Weapon class -> animation: animId = base + 100 * wepmotionCategory (base 40000/40030/40040, +5 for No-FP)
* Behavior-graph (behbnd -> XML via HKLib) confirms: SwordArtsOneShot_48_CMSG -> a692_044800 only
* Scripts: TAE parser, pointer-repoint frame patcher (zero side effects), behavior-graph mapper
* No game files are included; generate the patch yourself with tools/patch_frames_repoint.py
```

---

## 2) Reddit 帖（r/EldenringMods / r/Nightreign / r/soulsmods）

**English**

> **Title:** Nightreign parry frames: which animation does each shield / Ash of War actually use? (data + how to patch)
>
> I reverse-engineered the mapping between shields and their parry animations in **Elden Ring: Nightreign**, and it
> turns out two simple rules decide everything:
>
> 1. **Skill → TAE bank: `bank = 600 + SwordArtsParam.swordArtsType`** (verified on 191/194 rows).
>    So Standard Parry (302) → `a692`, Buckler Parry (303) → `a693`, Carian Retaliation (305) → `a695`,
>    Storm Wall (306) → `a696`, Golden Parry (307) → `a697`, Thops's Barrier (309) → `a699`.
> 2. **Weapon class → which entry inside that bank: `animId = base + 100 × wepmotionCategory`**
>    (`base` = 40000 one-shot / 40030 both-hand / 40040 left-hand; `+5` for the out-of-FP variant).
>
> Cross-checked against the behavior graph (converted `c0000.hkx` with HKLib to XML):
> `SwordArtsOneShot_48_CMSG` (48 = Small Shield) points at exactly **`a692_044800`**, and the dagger/curved-sword
> entries (`_20_` → `a692_042000`, `_28_` → `a692_042800`) match too.
>
> The parry window lives in the TAE **event table**: `AttackBehavior` (type 1, param 64 = Parry) shares its time
> slot with `Flag 119 TryToInvokeForceParryMode`. **Heads-up:** the naive way (overwrite that float) also drags a
> `type 129 Play Sound` event's start past its end — in 24 of 33 entries. I wrote a **pointer-repoint** patcher that
> edits the event header's `end_off` field instead, so nothing else moves (verified byte-for-byte).
>
> Data tables + scripts (no game files): `https://github.com/kazamiwong/NIGHTREIGN-parry`
>
> Questions/corrections welcome — especially in-game confirmation of the four skill banks.

**中文**

> **标题**：黑夜君临弹反帧：每面盾 / 每个战灰到底用哪条动画？（数据 + 改帧方法）
>
> 我把《黑夜君临》里"盾 → 弹反动画"的对应关系逆出来了，两条规则就能决定：
> **① 技能决定库：`bank = 600 + swordArtsParamId 的 swordArtsType`**（194 行里 191 行命中）——
> 标准格挡 302→`a692`、小圆盾 303→`a693`、卡利亚 305→`a695`、风暴障壁 306→`a696`、黄金 307→`a697`、托普斯 309→`a699`；
> **② 武器类别决定库里的哪一条：`animId = 基数 + 100 × wepmotionCategory`**（基数 40000/40030/40040 = 单手/双手/左手，"没蓝"再 +5）。
>
> 并用行为图交叉验证（HKLib 把 `c0000.hkx` 转 XML）：`SwordArtsOneShot_48_CMSG`（48 = 小盾）只指向 **`a692_044800`**。
>
> 弹反窗在 TAE 事件表里：`AttackBehavior`（type 1，参数 64 = Parry）与 `Flag 119` 共用时间槽。
> ⚠️ 直接改那个 float 会连带把 `type 129`（音效）事件的起点拖过头（33 条里 24 条中招）；我改成**改指针**（改事件头的 `end_off`），
> 其它数据一字未动，逐字节验证过。
>
> 数据表 + 脚本（不含游戏文件）：`https://github.com/kazamiwong/NIGHTREIGN-parry`

---

## 3) Nexus Mods（玩家手动搜索的主战场）

**Description（EN）**

```
Nightreign Parry Frames — data & patch scripts

WHAT THIS IS
A complete, data-verified mapping of which TAE animation each shield / Ash of War parry uses,
plus scripts that patch the parry window safely.

WHY IT MATTERS
If you extend the wrong animation's window, nothing happens in game. This tells you exactly which
entry (bank + animId) belongs to which weapon class and skill.

KEY RESULTS
* bank = 600 + SwordArtsParam.swordArtsType   (302->a692, 303->a693, 305->a695, 306->a696, 307->a697, 309->a699)
* animId = base + 100 * wepmotionCategory     (40000 one-shot / 40030 both / 40040 left; +5 = out of FP)
* Small Shield parry = a692_044800 ; Dagger = a692_042000 ; Curved Sword = a692_042800
* Golden Parry normal/No-FP = a697_040000 / a697_040005

HOW TO USE
Run tools/patch_frames_repoint.py against your own unpacked c0000 anibnd to generate the patch,
then repack with WitchyBND and load with ME3 (mods\chr\c0000.anibnd.dcx). Offline + EAC off.

NOT INCLUDED
No game files. Data + scripts only.
```

**中文描述**：把上面那段用同样结构翻一遍即可（结论表照抄 README 的表格）。

---

## 4) soulsmodding wiki（技术圈的权威资料站）

**建议新页面**：`ern-refmat:tae:parry`（或 `format:tae:nightreign-parry`），标题 *"Nightreign — Parry / Guard TAE banks and animations"*。

页面骨架：

```
== Skill -> TAE bank ==
bank = 600 + SwordArtsParam.swordArtsType

{| class="wikitable"
! skill !! name !! swordArtsType !! bank
|-
| 302 || [Standard] Parry || 92 || a692
|-
| 303 || [Standard] Buckler Parry || 93 || a693
|-
| 305 || [Magic] Carian Retaliation || 95 || a695
|-
| 306 || [Standard] Storm Wall || 96 || a696
|-
| 307 || [Holy] Golden Parry || 97 || a697
|-
| 309 || [Magic] Thops's Barrier || 99 || a699
|}

== Weapon class -> animId ==
animId = base + 100 * wepmotionCategory  (base 40000 / 40030 / 40040, +5 = No-FP)

== Parry window location ==
AttackBehavior (type 1, param 0x00 = 64 Parry) shares its time slot with Flag 119
TryToInvokeForceParryMode.  Flag 3 Set Guard Type is the guard/hyper-armour window.

== See also ==
TAE, Havok Behaviour, ERClipGeneratorTool (CMSG mechanism)
```

---

## 5) 发布前 checklist

- [ ] README 在最外层，且第一段就是结论（AI 抓取偏好）
- [ ] 中英双语关键词都出现过（正文与标题）
- [ ] `LICENSE` 填上你的名字/GitHub 用户名（现在是占位符）
- [ ] **不含**游戏原始文件（`.tae/.hkx/.dcx/regulation.bin`）与第三方帧数表
- [ ] 致谢写全：HKLib / ERClipGeneratorTool（The12thAvenger）、WitchyBND（ividyon）、Smithbox、soulsmodding wiki、社区帧数表
- [ ] 明确写出"改 c0000 会被反作弊检测 → 离线 + 关 EAC"
- [ ] 给出引用格式：`kazamiwong (2026). Nightreign parry frame mapping. https://github.com/kazamiwong/NIGHTREIGN-parry`



