# Hongguo Feed Filter

LSPosed 模块包名：`local.hongguore.feedfilter`。

- [项目说明、安装与构建](../../README.md)
- [识别与拦截设计](../../docs/ANALYSIS.md)
- [V1.0 发布说明](../../docs/RELEASE_V1.0.md)

源码位于 `src/`，测试夹具位于 `tests/`。`assets/xposed_init` 声明加载入口，Manifest 的 scope 只包含 `com.phoenix.read`。

两种构建使用同一个包名，相互覆盖安装：

- **observe**：记录数据模型及插入、替换、绑定，不阻止原方法。
- **block**：使用相同分类逻辑，并拒绝已识别广告模型的插入和替换。

发布附件为 block 版本。安装新版本后请重启目标应用，使用当前进程的 `READY` 日志确认模式；仅看到广告减少不等于已验证拦截。
