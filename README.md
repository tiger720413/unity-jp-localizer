# unity-jp-localizer

Unity 游戏日文 → 中文汉化工具包(等长字节替换法)。

在 Steam Frame(ARM64 + Proton)上实战验证:成功汉化 IL2CPP v39 游戏「セクシチュ」(217 条 UI 文本),游戏正常启动无损坏。

## 为什么是"等长字节替换"

老 Unity 资源包和 IL2CPP 元数据都没有可靠的类型信息,直接改文本会破坏结构。本工具包的策略:**翻译文本编码后字节长度必须 ≤ 原文,不足用空格补齐**,文件字节布局完全不变,游戏必然能正常加载。

中文通常比日文短(3 字节/字 对 3 字节/字,但中文更精炼),大部分文本能完美卡位。

## 工具

### 1. scan_jp.py — 日文字符串扫描器

字节级扫描任意文件中的 UTF-8 日文串(平假名/片假名/CJK 汉字):

```bash
python3 scan_jp.py <文件或目录> <输出.txt>
```

输出:每行 `文件路径 | 偏移 | 文本`,按长度降序,便于先看大文本。

### 2. meta_dump/ — v35+ IL2CPP 元数据字符串精确导出器

**关键发现(2026-11)**:IL2CPP 元数据 **v35 起字符串字面量不再有长度字段**——每个字符串从自己的 `dataIndex` 延伸到下一个字符串的 `dataIndex`(或字面量区末尾)。老工具按旧布局解析会全部错位。

本导出器用 [LibCpp2IL](https://github.com/SamboyCoding/Cpp2IL) 解析元数据,输出每个字符串字面量的 **精确文件偏移 + 字节长度**:

```bash
cd meta_dump
dotnet build -c Release
dotnet bin/Release/net10.0/meta_dump.dll <global-metadata.dat> <data.unity3d或任意Data文件> > literals.txt
# 输出格式: 索引\t文件偏移\t字节长度\t字符串
```

依赖:dotnet SDK(10.0)+ LibCpp2IL 与 AssetRipper.Primitives(Cpp2IL 的 bin 目录里有)。

### 3. patch_strings.py — 等长替换补丁器

表驱动的批量替换:

```bash
python3 patch_strings.py <目标文件> <翻译表.tsv> [--dry-run]
```

翻译表格式(TSV,`\t` 分隔,`\n` 用 `\\n`):

```
<文件偏移>\t<原文>\t<译文>
715438	お気に入り	收藏
717555	一番奥の個室…\nノックは4回\n…	最里面的单间…\n敲门4下\n…
```

规则:
- 译文 UTF-8 字节数必须 ≤ 原文,超出报错并列出
- 替换前校验偏移处内容 == 原文(防错位)
- 自动备份 `<文件>.bak`

### 4. cecil_patch/ — Mono 程序集 IL 检查绕过补丁器

对 Mono(非 IL2CPP)Unity 游戏的检查类方法做最小 IL 补丁(如跳过"必须连接头显"检查)。基于 Mono.Cecil,支持按方法名 + API 调用模式定位并 NOP 掉分支:

```bash
cd cecil_patch
dotnet build -c Release
dotnet bin/Release/net10.0/cecil_patch.dll <Assembly-CSharp.dll>
```

需要修改 `Program.cs` 中的目标类型/方法/模式(每游戏不同,示例 = VR Kanojo 2017 的 `InitScene2::CheckHMD` 的 `Input.GetKey(Home)` 分支)。

## 实战案例

`examples/sekushichu_table.tsv` — 「セクシチュ」的 217 条 UI 文本翻译表(菜单/操作说明/场景名/确认框),可直接参考格式。

## 工作流

1. `scan_jp.py` 粗扫游戏文件找日文
2. IL2CPP 游戏:用 `meta_dump` 拿精确偏移;Mono 游戏:直接字节定位
3. 翻译,填翻译表(注意 `{}` 等占位符保留、译文字节数不超原文)
4. `patch_strings.py` 打补丁(自动备份+校验)
5. 启动游戏验证,收工

## License

MIT
