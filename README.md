# HG-APP

针对红果免费短剧 **7.4.5.32 / 74532** 的 LSPosed 视频流广告过滤模块。

通过广告数据模型识别，在卡片插入或替换前进行拦截，而非隐藏广告控件。只作用于 `com.phoenix.read` 主进程，不修改原应用 APK。

## 下载与使用

从 [Releases](https://github.com/yerxio/HG-APP/releases) 下载拦截版 APK。

1. 安装 APK，在 LSPosed 中启用 **Hongguo Feed Filter (Research)**。
2. 作用域只勾选红果 `com.phoenix.read`。
3. 彻底停止红果后重新打开。
4. 在 LSPosed 日志或 `adb logcat -s HGFeedFilter:I` 中检查 `READY ... mode=BLOCK`。

这是 LSPosed 模块 APK，不是 KernelSU 安装 ZIP。没有独立启动界面；可以通过 LSPosed 管理。停用模块并重启红果即可恢复原行为。

V1.0 的模块版本为 `1.0`、版本号为 `2`，包名 `local.hongguore.feedfilter`。发布 APK 沿用原型签名，支持覆盖安装先前观察版或拦截版。

## 功能与限制

- 识别 `OneStopAdModel`、`LandscapeOneStopAdModel` 和 `AdRemainNaturalMaterials` 三个广告模型家族。
- 拦截通用列表的 `I2 / Y0 / P4 / Q0` 及横屏覆写入口；其他模型保留原处理逻辑。
- 目标版本不匹配时停止加载业务 Hook。
- 记录 `READY / PASS / BLOCK / BIND`，每个进程最多 400 条；不输出完整素材、URL、账号或令牌。
- 不保证覆盖开屏、激励广告、独立小游戏卡片、批量初始列表或其他未分析路径。
- 不阻断所有广告网络请求，不处理会员、奖励、付费内容与解锁状态。

**验证状态：**关键 DEX 签名、构建、APK 签名与 JVM 夹具测试已通过。原型观察版已在实机确认小游戏推广 `type=7` 经过 `I2`、`Y0`，原型拦截版已确认加载。最近保存的拦截日志没有真实 `BLOCK` 命中；V1.0 发布 APK 尚需实机回归，不宣称全场景去广告已验证。

详见 [设计与验证边界](docs/ANALYSIS.md)、[V1.0 发布说明](docs/RELEASE_V1.0.md) 和 [更新记录](CHANGELOG.md)。

## 构建

需要 Python 3.10+、JDK 17，以及 Android SDK。默认使用 Build Tools `36.0.0` 和平台 `android-36.1`，可通过环境变量调整。下面是 Windows PowerShell 示例：

```powershell
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
python tools\build_module.py
```

脚本从官方 Xposed API 仓库获取 API 82 编译依赖并校验固定 SHA256，执行 JVM 测试、编译、打包、签名和校验。不需要原始红果 APK 即可构建模块。构建输出在：

```text
modules/hongguo-feed-filter/dist/hongguo-feed-filter-observe.apk
modules/hongguo-feed-filter/dist/hongguo-feed-filter-block.apk
modules/hongguo-feed-filter/dist/SHA256SUMS.txt
```

默认生成本地开发签名。自行构建的 APK 与官方 Release 签名不同，通常需要先卸载已安装的模块，或使用你自己原先的签名。维护者可以通过环境变量传入既有密钥：

- `HG_KEYSTORE`：既有 keystore 的绝对路径。
- `HG_KEYSTORE_PASSWORD`：keystore 和私钥的口令，只通过环境变量读取。
- `HG_KEY_ALIAS`：密钥别名。
- `ANDROID_BUILD_TOOLS`、`ANDROID_PLATFORM`：可选 SDK 版本覆盖。

私钥不进入仓库。构建命令及验证输出保存在本地 `analysis/reports/build_verification.json`，默认忽略，不提交。

## 仓库结构

```text
modules/hongguo-feed-filter/   Manifest、Xposed 入口、过滤逻辑、夹具测试
tools/                       构建及可选的 APK 索引、签名核对工具
docs/                         原理与发布说明
```

`tools/index_apk.py` 和 `tools/verify_hook_targets.py` 是可选静态核对工具，需要自行把对应版本样本放入 `resource/APK/`。目标 APK、反编译输出、截图、原始设备日志、签名密钥和本地工具二进制均不随仓库发布。
