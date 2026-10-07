# 黑夜君临（Nightreign）弹反帧 / 弹反动画 对应关系与改帧指南

> 🌐 English version: **[README.en.md](README.en.md)**

> 面向 Mod 作者的实测+数据整理。**不含任何游戏原始文件**（不提供 `.tae`/`.hkx`/`regulation.bin`，只给结论、方法与脚本）。
> 数据来源：本机游戏文件 + Smithbox 官方参数枚举 + 行为图实解 + 社区帧数表（见文末致谢）。
> 所有结论都标注了**证据等级**：`实测`（游戏内验证）/ `机读`（直接从文件读出）/ `推导`（由机读数据推出）。

---

## TL;DR（English abstract）

For **Elden Ring: Nightreign** the player's parry animations live in ten `c0000.anibnd` TAE banks.
Two mechanical rules decide which one a weapon uses:

1. **Skill → bank: `bank = 600 + SwordArtsParam.swordArtsType`** (verified on 191/194 rows of `SwordArtsParam`).
2. **Weapon class → which entry inside that bank: the animId encodes it — `animId = base + 100 × wepmotionCategory`**
   (`base` = 40000 / 40030 / 40040 for one-shot / both-hand / left-hand variants; `+5` for the "no FP" variant).
   The behavior graph confirms this: `SwordArtsOneShot_48_CMSG` (48 = Small Shield) points at exactly `a692_044800`.

So "which animation does my shield use" is now a lookup, not a guess. Editing the **TAE event-table float** (or better, the
`end_off` *pointer*) of `AttackBehavior` + `Flag 119` changes the parry-judgement window; editing `Flag 3 Set Guard Type`
changes the guard/deflect (hyper-armour) window. Those are two different windows.

---

## 1. 结论表：盾 / 战技 → bank → 具体动画

### 1.1 机制一：技能决定 bank

`SwordArtsParam.swordArtsType` 直接决定 tae bank：**`bank = 600 + swordArtsType`**。
对 `SwordArtsParam` 全表 194 行验证：**命中 191**，3 个未命中全部可解释（`[Standard] No Skill` 的
`swordArtsType = 255` 是"无战技"哨兵值；skill 104 是空名占位行）。

| skill id | `SwordArtsParam` 名称 | swordArtsType | bank |
|---|---|---|---|
| 300 | `[Standard] Shield Bash` | 90 | a690 |
| 301 | `[Standard] Barricade Shield` | 91 | a691 |
| **302** | **`[Standard] Parry`**（标准格挡） | 92 | **a692** |
| **303** | **`[Standard] Buckler Parry`**（小圆盾） | 93 | **a693** |
| （304：不存在） | — | — | （a694 存在但无战技） |
| **305** | **`[Magic] Carian Retaliation`**（卡利亚式奉还） | 95 | **a695** |
| **306** | **`[Standard] Storm Wall`**（风暴障壁） | 96 | **a696** |
| **307** | **`[Holy] Golden Parry`**（黄金格挡） | 97 | **a697** |
| 308 | `[Standard] Shield Crash` | 98 | a698 |
| **309** | **`[Magic] Thops's Barrier`**（托普斯的力场） | 99 | **a699** |
| 1196 | `[Specific] Golden Retaliation` | 196 | a796 |

### 1.2 机制二：武器类别决定 bank 里的哪一条（animId）

CMSG 名字里的两位数字 = 该武器的 **`EquipParamWeapon.wepmotionCategory`**，而这个数字**直接编码在 animId 里**：

**`animId = base + 100 × wepmotionCategory`**（NoMP 变体再 `+5`）

| base | 含义 |
|---|---|
| 40000 | 单手 / 单发（`SwordArtsOneShot`） |
| 40030 | 双手（`SwordArtsOneShotShieldBoth`） |
| 40040 | 左手（`SwordArtsOneShotShieldLeft`） |
| 40005 / 40035 / 40045 | 上面三个的"没蓝（NoMP）"版本 |

对应的 `wepmotionCategory`（NR 官方枚举）：

| 值 | 名称 | 实测代表武器 |
|---|---|---|
| 20 | Dagger | `[Common] Dagger` |
| 22 | Claw | `[Common] Hookclaws` |
| 27 | Thrusting Sword | `[Common] Estoc` |
| 28 | Curved Sword | Bandit's Curved Sword |
| **47** | **Greatshield** | Dragon Towershield |
| **48** | **Small Shield** | Buckler / Perfumer's Shield / Wylder's Small Shield |
| **49** | **Medium Shield** | Round Shield / Heater Shield |
| 42 | Fist | `[Unarmed] Unarmed` |

### 1.3 最终对照表（盾相关）

| Excel 行 | 技能 | bank | 具体动画（机读） | 弹反窗（我们口径 Start→End，帧） |
|---|---|---|---|---|
| 拳头 / 钩爪 / 中盾 / 刺剑格挡 | 302 | a692 | `a692_040000` | 4→6 |
| 曲剑格挡 | 302 | a692 | `a692_042800` | 4→6 |
| 短剑格挡 | 302 | a692 | `a692_042000` | 4→8 |
| **小盾格挡** | 302 | a692 | **`a692_044800`** | 5→10 |
| 小圆盾格挡 | 303 | a693 | `a693_040000` | 4→9 |
| 卡利亚式奉还（正常 / 没蓝） | 305 | a695 | `a695_040000` / `a695_040005` | 4→10 / 6→8 |
| 风暴障壁（正常 / 没蓝） | 306 | a696 | `a696_040000` / `a696_040005` | 4→9 / 5→10 |
| 黄金格挡（正常 / 没蓝） | 307 | a697 | `a697_040000` / `a697_040005` | 4→7 / 5→10 |
| 托普斯力场（正常 / 没蓝） | 309 | a699 | `a699_040000` / `a699_040005` | 4→8 / 6→10 |

> **口径务必注意**：Excel 帧数表的「起」= 我们记录的 `Start` **+1**、「止」= 我们记录的 `End`；
> Excel 的「帧数」= 止 − 起 + 1（含端点），我们记录的跨度 = `End − Start`。例：Excel `6→10` = 我们 `5→10` = 5 帧。

---

## 2. 行为图（behbnd）里的选择机制

- clip generator 的动画名字段形如 `a[TaeId]_[AnimationId]`（TaeId = bank）。
- 选择由 FromSoftware 自定义类 **`CustomManualSelectorGenerator`（CMSG）** 完成：
  **一个 CMSG = 一个 animId**，内含该 animId 下的**全部** clip generator（多个 bank 的同一条目）。
  引用链：`CMSG.m_generators[] → hkbClipGenerator.m_animationName`。
- 类别选择由 `hkbManualSelectorGenerator`（名字如 `SwordArtsOneShotShieldLeft CategorySelector`）
  的 **generators 数组下标**完成；`selectedgeneratorindex` 默认 0（= 通用条目），
  `indexselector = null` ⇒ **索引由运行时（引擎/hks）设置**，行为图里没有"映射表"。
- 因此：**同一 animId 的 CMSG 会同时包含多个 bank**；"哪个 bank 生效"由角色当前生效的 tae id 决定
  （本文件第 1.1 节的技能→bank 规则就是它的来源）。

---

## 3. 怎么改（两种方法，务必选对）

### 3.1 老办法：直接改写 `end_off` 指向的那个 f32 —— **有坑**

TAE 里时间是"**同一瞬间只存一份 float**"，多个事件用偏移共用它，而且时间轴首尾相连。
直接改 float 会**连带移动别的事件的时间**。逐条审计（33 个盾相关条目）结果：

- **只有 6 条是干净的**（`a692` 的 40000/40030/40040、`a693` 的 40000/40030/40040）；
- **24 条**会把同动画里一个 `type 129 = "Play Sound - By State Info [Wwise]"`（音效事件）的**起点**
  一起推后，而它自己的 end 更小 → 变成 `start > end`（音效时序错乱，游戏不会崩，但不清真）；
- 3 条只是无害共享。

### 3.2 推荐办法：**改指针，而不是改 float**

事件头里存的是 3 个 **varint 偏移**（NR 是 64 位 varint，每项 8 字节定长）：
`start_off` / `end_off` / `data_off`。把 `AttackBehavior` 与 `Flag 119` 的 **`end_off` 字段改成指向另一个
"已经存在的时刻槽"**，就能延长窗口，而且**其它事件一个字节都不动**、文件长度不变。

实测：33 个盾相关条目**全部**都能找到"正好第 20 帧"的已有槽（与目标差 0.0 帧），
每个文件只变 6–12 字节，且全部落在指定的指针字段内（脚本自带逐字节 diff 断言）。

```powershell
# 示例：把 a692 的相关条目统一改成"第 20 帧结束"
python tools\patch_frames_repoint.py --bank a692 `
  --anim 40000 40005 40030 40035 40040 40045 44800 44830 44840 `
  --to 20 --out mods\all_shields_uniform20f --apply
# a693 / a695 / a696 / a697 / a699 同理（不存在的动画会被自动跳过）
```

> 手动用 DSAnimStudio 改也没问题（编辑器会正确维护时间槽），只是它保存的是整个 `anibnd`。

### 3.3 改哪个窗？（"弹反帧"有两层含义）

| 目的 | TAE 事件 | 说明 |
|---|---|---|
| **弹反判定窗** | `AttackBehavior`（type 1，参数 `+0x00 = 64` Parry） | 与下面这条**原版共用同一对时间槽** |
| **弹反就绪窗** | `JumpTable flag 119 = TryToInvokeForceParryMode` | 改上面那个槽时它一起变 |
| **格挡 / 刀反 / 霸体窗** | `JumpTable flag 3 = Set Guard Type` | X2 / X1.5 那类 "Deflect Frames" 改的是它；社区帧数表的「霸体帧」列也等于它（16/16 吻合） |
| 弹反成功后的取消 | `JumpTable flag 18 = Anim Cancel After Successful Parry` | 独立窗，一般不动 |
| 特殊战灰特效 | 与战技相关（黄金/风暴障壁/托普斯/卡利亚各有不同，见 §5） | **与弹反窗不是一回事**，只改弹反窗视觉不会跟着变长 |

改完还必须满足：**(a)** 改的是该武器实际会用到的那条 animId（§1.2 的价值所在）；
**(b)** 窗不能越界或破坏后面的阶段事件；**(c)** MOD 真的被加载（封包 + ME3 + 离线关 EAC）。

---

## 4. 复现流程（从零到能改）

1. **解包**：用 WitchyBND 解 `Game\chr\c0000.anibnd.dcx` → `Target\INTERROOT_win64\chr\c0000\tae\*.tae`。
2. **行为图转 XML**（可选，用于自己复核 CMSG）：用 [HKLib.CLI v0.1.3-NR](https://github.com/The12thAvenger/HKLib/releases)
   拖入 `c0000.hkx`。注意两点：
   - 它目标框架是 **net7.0**，若本机只有 .NET 6/8/9，设环境变量 **`DOTNET_ROLL_FORWARD=Major`** 即可，不必装 .NET 7；
   - 输出是 **tagfile XML**（`<hktagfile>/<type>/<object>/<field>/<string>/<pointer>`），不是 packfile 的 `hkobject/hkparam`。
3. **解析 tae**：用 `tools\tae.py`（按 SoulsFormatsNEXT 移植，已扩展 `start_off`/`end_off`/`end_off_pos`）。
4. **改帧**：`tools\patch_frames_repoint.py`（推荐）或 `tools\patch_frames.py`（改 float，注意 §3.1 的坑）。
5. **封包 / 加载**：WitchyBND 封包成 `c0000.anibnd.dcx` → 用 ME3 加载，目录层级必须是
   `mods\chr\c0000.anibnd.dcx`。**必须离线 + 关 EAC**（改 c0000 一定会被反作弊检测）。

---

## 5. 已知边界 / 未解（诚实清单）

- **ER 遗留槽位**：类别号 **2–9** 的条目（如 `a693_040240`/`a693_040340`）在 NR 里没有武器使用
  （`WEPMOTION_CATEGORY` 枚举只有 0 与 20–52，`EquipParamWeapon` 实测也没有 1–19），
  它们被 CategorySelector 引用、结构上"活着"，但**永远选不中** → 不用改。
- **死数据**：`a002_040392`、`a003_040392`、`a020_035200/035201/035202` 在整张行为图里**零引用**。
- **`a534_049980`** 由 `AutoParyy_Idle_CMSG` 持有（"自动弹反待机"），归属机制未定。
- **`a907`** 相关（`AddDemonSwordMode_ParryStance_CMSG` 等）= 执行者妖刀体系，**另案处理**。
- **特效窗**：四个耗蓝战技的"特效帧"与弹反窗不同（黄金 `5→7`、风暴障壁 `1→10`、托普斯 `4→16`、卡利亚 `5→10`），
  尚未定位到确切 TAE 事件；只延长弹反窗时**视觉不会同步**。
- **中盾共用通用条目**：`a692` 的 `40000/40030/40040` 与徒手/爪/刺剑等共用，改它会一并影响那批武器
  （好在它们原窗本来一致）。

---

## 6. 证据分级（重要，别把推导当实测）

| 结论 | 等级 |
|---|---|
| 六个技能 → 六个 bank；`bank = 600 + swordArtsType` | **机读**（对 194 行验证 191 命中） |
| 武器类别 → animId 编码；`_48_CMSG` 只指向 `a692_044800` | **机读**（行为图实解 + 参数列） |
| 窗口数值（Start/End/Flag3） | **机读**（tae 逐字节解析；Flag3 与第三方帧数表 16/16 吻合） |
| 中盾/小盾/小圆盾/短剑/曲剑的最终动画 | **机读 + 推导**（帧窗唯一性 + 条目族结构） |
| 小圆盾 = a693、卡利亚 = a695、黄金 = a697 | 社区/作者**实测**（本文件仅转述并交叉印证） |
| "改了 TAE 窗 → 游戏里手感变宽" | 由实测与既有 MOD 支撑；**本文件未独立验证**，建议自行实测 |

---

## 7. 致谢 / 免责

- [HKLib](https://github.com/The12thAvenger/HKLib)（hkx → XML，NR 版 v0.1.3-NR）与
  [ERClipGeneratorTool](https://github.com/The12thAvenger/ERClipGeneratorTool)（CMSG 机制说明，作者即 HKLib 作者）。
- [WitchyBND](https://github.com/ividyon/WitchyBND)（BND4/DCX 解封包）、[Smithbox](https://github.com/vawser/Smithbox)（官方参数枚举与 TAE 模板）。
- [soulsmodding wiki](https://www.soulsmodding.com/) 的 TAE / Havok Behavior 资料。
- 社区帧数表（`黑环小辛弹反帧提取`）——本文的帧窗交叉验证用到它，**不随本文再分发**。
- 本文只包含**自行推导的数据与脚本**，不含任何 FromSoftware 游戏文件。请自行从正版游戏提取所需文件；
  修改 `c0000` 会被反作弊检测，**务必离线并关闭 EAC**，风险自负。

---

## 8. 许可 / License

- **代码**（`tools/` 下的脚本）：**MIT** —— 见根目录 `LICENSE`。可自由使用、修改、再发布（含商用），只需保留版权与许可声明。
- **数据与文档**（`data/`、`docs/`、本 README）：**CC BY 4.0** —— 见 `data/LICENSE`。可自由使用（含商用），**需署名**并附许可链接。
  想更宽松可以把数据改成 CC0；想禁止商用可改 CC BY-NC（但很多整合包/平台会回避非商用许可）。
- **引用格式 / Cite as**：`kazamiwong (2026). Nightreign parry frame mapping — TAE banks, animIds and windows. https://github.com/kazamiwong/NIGHTREIGN-parry`
- **免责 / Disclaimer**：本项目为非官方逆向工程资料，**不含任何 FromSoftware 游戏文件**。
  *Elden Ring / Nightreign* 及相关名称与商标归 FromSoftware / Bandai Namco 所有，本项目与其无隶属关系。
  修改 `c0000` 会被反作弊检测 —— 请**离线并关闭 EAC**，风险自负。


