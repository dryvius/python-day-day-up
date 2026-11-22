# 练习：Git 协作与 CI 门禁

> 对应文档：[`docs/03-engineering/06-git-ci.md`](../../docs/03-engineering/06-git-ci.md)  
> 状态：`已完成出题`  
> 建议用时：90～150 分钟

## 练习说明

在一个临时练习仓库或独立练习分支完成本章任务。不要在承载未提交工作的分支上演练丢弃修改或回退。

目标是为一个已使用 pytest 的 Python 项目建立：

```text
可审查的小提交 + 正确忽略规则 + FakeLLM 测试 + GitHub Actions 门禁
```

---

## 热身题

### W1. 状态判断

分别写出以下场景优先使用的命令，并说明是否保留文件内容：

1. 文件已修改、未暂存，想丢弃该文件修改。
2. 文件已暂存，想取消暂存但保留修改。
3. 错误提交已经推送到共享分支，需要安全回退。

**验收**：答案分别涉及 `restore`、`restore --staged`、`revert`，且没有把它们混成同一种撤销。

### W2. Ignore 判断

解释为什么 `.env.example` 通常应提交，而 `.env` 不应提交；再说明 `.env` 曾经提交后，仅补 `.gitignore` 为什么不够。

---

## 基础题（必做）

### B1. 分支与小提交

创建主题分支，在其中：

1. 增加一个纯函数及对应 pytest。
2. 用 `git status`、`git diff` 检查修改。
3. 只暂存相关实现和测试。
4. 用 Conventional Commits 风格提交。

**验收**：

- 分支名能表达任务；
- `git diff --cached` 中没有日志、密钥或无关格式化；
- 提交信息如 `feat(core): add text normalizer`；
- `python -m pytest -q` 通过。

### B2. `.gitignore` 基线

编写或补充 `.gitignore`，至少覆盖：

```text
__pycache__/
.pytest_cache/
.venv/
.env
.coverage
htmlcov/
*.log
```

保留 `.env.example`。

运行：

```bash
git check-ignore -v .venv/ .env app.log
git status --ignored --short
```

**验收**：能指出每个文件命中了哪条规则；不会用 `*.json` 等过宽规则误伤项目文件。

### B3. FakeLLM 单测

为依赖 LLM 客户端的一个函数注入 Fake：

```python
class FakeLLM:
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: object,
    ) -> dict:
        return {"role": "assistant", "content": "ok"}
```

要求：

- 测试不读取真实 API Key；
- 测试不访问网络；
- 至少断言返回结构和一次关键业务行为；
- 真实服务测试若存在，标记为 `live` 并能从默认门禁排除。

### B4. GitHub Actions 工作流

**学习者单项目**：新增 `.github/workflows/ci.yml`：

- `pull_request` 和 `push` 到 `main` 时触发；
- 使用 Python 3.12（或与本课一致的 3.11）；
- 从项目声明安装依赖；
- 执行 `python -m pytest -q`（Fake 为默认路径即可）；
- 仅当你自己加了需外网/密钥的集成测试时，才注册 `live` 标记并改用 `-m "not live"`——**不要假设本课参考实现已有该标记**；
- job 名固定为 `pytest-fake`；
- `permissions` 至少保持 `contents: read`；
- 设置合理超时。

**对照本课仓库**：阅读 [`.github/workflows/projects-ci.yml`](../../.github/workflows/projects-ci.yml)，用文字说明它如何用 `matrix.project` + `working-directory` 覆盖六个 `playground/projects/*`，以及 P4～P6 的条件评测步骤。不必把 matrix 抄进你的练习仓。

**验收**：

1. 你的单项目 YAML 可解析。
2. 工作流不包含真实模型密钥。
3. 故意改坏断言时 CI 失败，修复后恢复。
4. 在仓库 Ruleset/分支保护中将 `pytest-fake` 设为 required check；若没有管理员权限，提交配置步骤与截图/文字记录。
5. 能口述本课 `projects-ci.yml` 与单项目 `ci.yml` 的差异。

### B5. 安全回退

在临时分支创建两个提交，用 `git revert HEAD` 回退第二个。

**验收**：

- 原提交仍在历史中；
- 新增一个反向提交；
- 文件内容回到第一个提交后的状态；
- 能说明为何共享分支优先采用这种方式。

---

## 进阶题（建议）

### A1. 并发与缓存

为工作流增加：

- 同一分支新运行触发时取消旧运行；
- pip 或 uv 依赖缓存；
- 不让缓存成为依赖声明之外的隐式来源。

### A2. PR 验证清单

在项目贡献说明中加入提交前命令：

```bash
git diff --check
python -m pytest -q
```

并要求提交者检查 `git diff --cached`。若项目自行引入了 `live` 标记，再写明 `-m "not live"`。

---

## 挑战题（可选）

### C1. 双层测试策略

设计两个 job：

1. `pytest-fake`：每个 PR 必跑、required、无 secrets。
2. `live-smoke`：只允许手动触发或受信任环境运行、非 required。

写清权限、secret、超时和失败策略。不要让来自 fork 的不可信代码获得生产凭据。

---

## 本章通过线

- [ ] B1～B5 完成。
- [ ] 能根据变更状态选择安全回退方式。
- [ ] `.gitignore` 不包含过宽规则，且理解已跟踪文件的处理。
- [ ] FakeLLM + pytest 可在无密钥、无网络环境运行。
- [ ] PR 上存在真正的 required check，而不只是一个 Action 文件。
- [ ] 运行 `git diff --check` 无错误。

## 自检问题

1. `git diff` 与 `git diff --cached` 分别看什么？
2. 为什么已推送提交优先 `revert`，而不是强推改写历史？
3. 为什么 `.gitignore` 不是密钥保护机制？
4. 为什么真实 LLM 不适合作为基础合并门禁？
5. 为什么稳定的 job 名对 required check 很重要？

## 导航

- 对应正文：[Git 协作与 CI 门禁](../../docs/03-engineering/06-git-ci.md)
- 上一练习：[CLI 入口与参数解析](./05-cli-entrypoints.md)
- 下一练习：[调试与故障定位](./07-debugging.md)
