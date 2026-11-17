# 视频流广告识别与拦截设计

本模块针对红果 `7.4.5.32 / 74532` 的混合视频列表。普通剧集与推广素材可能共用同一 Activity，单看页面名或是否正在播放视频不足以分类。

## 识别

| 数据模型 | 模块分类 |
|---|---|
| `com.bytedance.tomato.onestop.base.model.OneStopAdModel` | `ONE_STOP_AD` |
| `com.dragon.read.ad.onestop.serieslandscape.model.LandscapeOneStopAdModel` | `LANDSCAPE_AD` |
| `OneStopAdModel$AdRemainNaturalMaterials` | `NATURAL_PROMOTION` |
| 其他模型，包括普通视频包装对象 | `KEEP` |

匹配包括上述类型的子类。观察模式曾在实机捕获小游戏推广素材 `AdRemainNaturalMaterials`，字段 `type=7`，经过 `I2`、`Y0` 后绑定到视频列表。正常视频模型包括 `VideoDetailModelWrapper` 和 `SaasVideoDataWrapper`。模块按完整类型名识别，不只依据 type 数字、UI 文案或视频数据是否为空。

## 拦截入口

基类：`com.dragon.read.component.shortvideo.impl.v2.view.adapter.a`。

| 方法 | 广告对象的处理 |
|---|---|
| `I2(int,int,Object):boolean` | 原方法执行前返回 false |
| `Y0(int,int,String,Object):boolean` | 原方法执行前返回 false |
| `P4(int,Object):boolean` | 原方法执行前返回 false |
| `Q0(int,Object):void` | 原方法执行前结束，保留已有项 |

额外 Hook `com.dragon.read.component.shortvideo.impl.fullscreen.d.P4(int,Object)`。通用入口没有方向限制，但横竖屏各路径仍需分别回归。

`Y0` 原逻辑可能先删除旧项再调用插入方法，因此在 `Y0` 前拦截比仅在最终插入处返回失败更完整。模块不将广告伪装成普通视频，也不直接篡改列表数量和索引。

## 加载和日志

- 仅匹配 `com.phoenix.read` 主进程。
- 在 `Application.attach` 之后检查目标版本并解析 ClassLoader。
- 必需方法签名不匹配时记录初始化错误。
- `READY` 表示 Hook 初始化，`PASS` 表示放行，`BLOCK` 表示拒绝插入或替换，`BIND` 表示列表绑定。
- 单个进程最多记录 400 条诊断消息，不输出完整广告 payload、URL、账号或令牌。
- 观察与拦截两种构建只在 `BuildMode.BLOCK` 常量上不同。

## 验证边界

已完成原始 DEX 关键签名核对、源码编译、APK 签名校验与 JVM 夹具测试。观察版实机已确认自然流推广的类型和 I2、Y0 调用，先前拦截原型也已成功加载。

截至发布准备时，最近保存的拦截模式日志没有实际 `BLOCK` 命中。因此不将“模块加载成功”或“刷动时未见广告”当作广告拦截的端到端证明。V1.0 仅更新发布版本与构建流程，业务 Hook 未变化；V1.0 APK 本身未在设备上重新安装回归。

本模块不是全局广告拦截器。批量初始列表、其他 SDK 路径、开屏广告、激励广告、独立小游戏卡片可能不被覆盖。广告网络请求与预取仍可能发生。模块不处理会员、奖励结算、付费内容或解锁状态。

验收需要真实 `BLOCK` 命中，并同时检查正常视频播放、回滑、选集、横竖屏切换和关闭模块后的行为恢复。
