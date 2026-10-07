# 脚本说明（3-脚本）

这些都是本次会话自己写的脚本，Python 3.12 可直接跑（只用到标准库；`xlsx_crosscheck.py` 与 `dump_xlsx.py` 需要 openpyxl）。
**所有脚本里的路径默认写的是本机路径**（`E:\黑夜君临mod\...`、`C:\Users\kazamiwong\...`），换机器请自行改顶部常量。

| 脚本 | 用途 | 典型用法 |
|---|---|---|
| `tae.py` | **TaE 解析器**（按 SoulsFormatsNEXT 移植）。已扩展 `event.start_off` / `end_off` / **`end_off_pos`**（事件头里字段的文件偏移，改指针要用） | `from tae import Tae; t = Tae(open('a692.tae','rb').read())` |
| `patch_frames_repoint.py` | **推荐改帧器（改指针）**：把 `AttackBehavior`/`Flag119` 的 `end_off` 指向一个**已存在的时刻槽**，零副作用；自带逐字节 diff 断言 | `python patch_frames_repoint.py --bank a692 --anim 40000 44800 --to 20 --out mods\xxx --apply` |
| `patch_frames.py` | 老改帧器（**直接改 f32**）。⚠️ 会连带移动共用同一时刻槽的其它事件（33 条里 24 条命中），仅适合先审计 | 同上，参数一致（`--end` 秒） |
| `audit_patch_safety.py` | **安全性审计**：逐条判断"改 float 会不会连带移动别的事件" | `python audit_patch_safety.py` |
| `dump_anim_events.py` | dump 某动画的所有事件（type / flag id / 偏移 / 起止），并标出**共用同一 `end_off`** 的事件 | `python dump_anim_events.py a692 44800` |
| `make_patch_list.py` | 生成「所有盾统一」的精确改动清单（+ `parry_patch_list.csv`） | `python make_patch_list.py` |
| `beh_xml_map.py` | **行为图 XML 解析器**（tagfile 格式）：CMSG → 动画名映射 | `python beh_xml_map.py c0000.xml probe` / `parry` / `map --out x.csv` |
| `beh_reach.py` | 行为图**可达性** BFS：判断哪些对象是"活数据" | `python beh_reach.py c0000.xml` |
| `beh_selector.py` | 打印 CategorySelector 的 generators 数组顺序 + 索引变量 | `python beh_selector.py c0000.xml` |
| `beh_xml_probe2.py` | 侦察 tagfile XML 的真实语法（标签/属性样例） | `python beh_xml_probe2.py c0000.xml` |
| `skill_bank_rule.py` | 验证 `bank = 600 + swordArtsType`（对全表统计命中率） | `python skill_bank_rule.py` |
| `animid_encoding.py` | 验证 `animId = base + 100×类别 (+5 NoMP)` | `python animid_encoding.py` |
| `cmsg_suffix_entries.py` | 统计每个类别后缀引用了哪些 bank 的条目 | `python cmsg_suffix_entries.py` |
| `frame_table_check.py` | **直接读 xlsx**（不经转述）+ 打印各 bank 窗口集合 | `python frame_table_check.py` |
| `xlsx_crosscheck.py` | 把 xlsx 的「霸体/特效」列拿去 tae 里找对应事件 | `python xlsx_crosscheck.py` |
| `wep_cols.py` | 定位武器栏位（wepmotionCategory / swordArtsParamId 等） | `python wep_cols.py` |

## 两个必须知道的坑

1. **改 float vs 改指针**：TAE 里时间是"同一瞬间只存一份"，多个事件用偏移共用。
   直接改那个 f32 会**连带移动别的事件的时间**（实测 33 条里 24 条会把一个
   `type 129 = Play Sound` 事件的起点推过头）→ **优先用 `patch_frames_repoint.py`**。
2. **Excel/社区帧数表的口径**：表的「起」= 我们的 `Start` + 1、「止」= 我们的 `End`；
   表的「帧数」= 止 − 起 + 1。换算错了就会得出"某行找不到对应动画"的假结论。

## 复现整条链（从零）

```powershell
# 1) 解包（人工）：WitchyBND 解 c0000.anibnd.dcx → Target\INTERROOT_win64\chr\c0000\tae\*.tae
# 2) 行为图转 XML（可选，人工/命令行）：HKLib.CLI v0.1.3-NR 拖入 Behaviors\c0000.hkx
#    注意：目标框架 net7.0；若本机无 .NET 7 → 设 $env:DOTNET_ROLL_FORWARD='Major' 即可
# 3) 解析/复核
python beh_xml_map.py c0000.xml parry
# 4) 改帧（推荐改指针）
python patch_frames_repoint.py --bank a692 --anim 40000 40005 40030 40035 40040 40045 44800 44830 44840 --to 20 --out mods\all_shields_uniform20f --apply
# 5) 封包（人工）：右键 mods\all_shields_uniform20f → WitchyBND
# 6) 加载：ME3，层级必须是 mods\chr\c0000.anibnd.dcx；离线 + 关 EAC
```

---

**目录说明**：本文件夹下 `核心\` 是上表这 16 个常用脚本；`历史与工具\` 是探索期写过的其它脚本（DCX/Oodle 解码、TaE 批量扫描、表格读数等，`进度总览.md` 第十章会引用它们），日常用不到但保留以便复现。
