# design · 控糖场景界面线框

一期四个核心界面的线框图源文件。视觉词汇从零建立——仓库里没有前端代码或设计系统可对齐。

**已发布画布**：https://claude.ai/code/artifact/2bc38b7f-7986-49b0-9210-c9e0bbee1af4

## 文件

| 文件 | 画板 | 尺寸 |
|---|---|---|
| `Main.dc.html` | 健管师工作台 | 1440×900 |
| `DoctorSignoff.dc.html` | 医师签发工作台 | 1440×900 |
| `PatientCard.dc.html` | 患者端企微日报（数据完整 / 数据不足 两态对照） | 860×900 |
| `FamilyWeekly.dc.html` | 子女端周报 | 390×844 |
| `canvas.json` | 画板在画布上的布局、便签、打开视图 | — |

每个 `.dc.html` 是一块独立画板。`canvas.json` 只是排版清单，不含内容。

**构建产物不入库**：`glycowise-phase1-wireframes.html`（2.4M，内含编辑器 payload）由上面五个文件生成，已在 `.gitignore` 中排除。

## 这套线框要验证什么

不是视觉，是信息架构。三条硬规则：

1. **「没有数据」和「没有异常」在健管师队列、患者端、子女端三处都不能长得一样。** 数据缺口用虚线加斜纹底，读起来是一个洞；无异常是安静的实线灰。两者永远不共用一种视觉语言。
2. **夜间覆盖率排在结论之前。** 覆盖不足时明说"下面的低血糖次数是下限不是实际值"，并阻断加强降糖方向的草稿。这是挡住医源性加药那条路径的界面手段。
3. **一期没有实时告警，界面不能有任何暗示夜间监护的元素。** 子女端进一步把"不做什么"写在明面上。

其余约束的出处见 `studio/changes/glycowise/decisions/confirmed-facts.md`，尤其 C-06（企微做不到大按钮大字号，大字走图片、交互走回复数字）与 B-12（上面第 1 条）。

## 改动流程

改本地源文件，然后重新生成并发布：

```bash
cd design
BASE=<design skill 的 base directory>
node "$BASE/seed-canvas.mjs" \
  --template "$BASE/payload.template.html" \
  --out glycowise-phase1-wireframes.html \
  --title "控糖一期界面线框" \
  --artboard Main.dc.html --artboard DoctorSignoff.dc.html \
  --artboard PatientCard.dc.html --artboard FamilyWeekly.dc.html \
  --canvas canvas.json
node "$BASE/seed-canvas.mjs" --check glycowise-phase1-wireframes.html
```

然后用 Artifact 工具发布同一路径，URL 不变。

## ⚠ 双向同步的坑

画布在浏览器里是可编辑的，别人改完点保存，**线上版本就和这里的源文件不一致了**。

此时**不要**直接用本地源重新生成覆盖——那会丢掉别人的编辑。正确做法是先把已发布的画布反向提取成working 文件（`seed-canvas.mjs --extract`），在提取出来的文件上改，再重新生成发布。

判断依据很简单：**只要有人可能在浏览器里动过，就先提取再改。**

## 已知留空

- AGP 曲线区是占位框。图表本身不是这轮要验证的东西，等信息架构定了再画。
- 店长看板与结营解读包未做。前者是权限受限的精简视图，后者本质是打印物，价值低于这四个。
- 二期界面（载体相关）未做，二期主要是硬件与运维，可设计的屏很少。
