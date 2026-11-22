# Git 协作与 CI 门禁

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/03-engineering/06-git-ci.md`](../../exercises/03-engineering/06-git-ci.md)

## 本章定位

- **模块目标**：把“本机能跑”升级为“变更可追踪、可审查、可自动验证”。
- **本章角色**：掌握日常 Git 闭环，并用 GitHub Actions 把 FakeLLM + pytest 变成合并门禁。
- **前置**：项目结构、依赖管理、pytest、CLI。
- **边界**：本章讲提交与验证流水线；复杂发布、部署和 GitHub 权限治理留到后续工程实践。

## 学习目标

1. 能创建分支、组织小提交，并读懂 `status`、`diff`、`log`。
2. 能根据“未提交、已提交、已共享”选择安全的撤销方式。
3. 能维护 Python 项目的 `.gitignore`，并理解“忽略不等于保密”。
4. 能配置 GitHub Actions，在无真实模型密钥时运行 FakeLLM 与 pytest。
5. 能把 CI 检查设为 PR 合并前的 required check。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | 分支、提交、diff、restore/revert、`.gitignore`、pytest CI | 能独立完成一次可审查变更 |
| **建议掌握** | rebase 更新分支、缓存、required check | 能维护稳定 PR 流程 |
| **了解即可** | tag、release、矩阵测试、部署流水线 | 有交付需求再深入 |

---

## 1. 日常闭环：分支 → 修改 → 验证 → 提交

### 为什么不直接在 `main` 上改

分支给一次变更提供独立边界。它让代码审查、自动检查和回退都围绕一个明确目标进行，而不是把多个任务混成一团。

推荐闭环：

```text
同步 main → 创建主题分支 → 小步修改 → 本地验证
          → 检查 diff → 提交 → 推送 → Pull Request → CI 通过 → 合并
```

### 怎么做

```bash
git switch main
git pull --ff-only
git switch -c feat/textstat-json

git status
git diff
pytest -q

git add app tests
git diff --cached
git commit -m "feat(cli): add json output"
git push -u origin feat/textstat-json
```

关键命令的职责：

| 命令 | 回答的问题 |
|------|------------|
| `git status` | 哪些文件被改、暂存或未跟踪 |
| `git diff` | 工作区相对暂存区改了什么 |
| `git diff --cached` | 下一次提交会包含什么 |
| `git log --oneline --decorate -n 10` | 最近提交和当前分支指向哪里 |

提交应保持单一意图。测试应与实现放在同一提交或紧邻提交，不要把格式化全仓、功能开发和无关重构混在一起。

### 跑一下

```bash
git switch -c chore/git-practice
printf "practice\n" > git-practice.txt
git status
git diff -- git-practice.txt
git add git-practice.txt
git diff --cached
git commit -m "chore: add git practice marker"
git log --oneline -n 3
```

练习结束后，若该提交只在本地临时分支，可切回原分支并删除练习分支；不要在有未保存工作时机械删除。

### 易错点

1. `git add .` 后不看 `git diff --cached`，把密钥、日志或无关文件一起提交。
2. 一个提交同时包含多个目的，导致审查和回退都困难。
3. 直接 `git pull` 接受隐式 merge；团队若要求线性更新，明确使用 `--ff-only` 或约定的 rebase 流程。
4. 把“提交成功”当作“代码正确”；提交前仍要运行项目约定的测试与静态检查。

---

## 2. 撤销与回退：先判断变更是否已共享

Git 没有一个适用于所有场景的“撤销”按钮。先判断状态：

```text
未暂存修改？ → restore
已暂存但未提交？ → restore --staged，再决定是否丢弃工作区修改
本地提交且未共享？ → 可谨慎改写历史
已推送/已共享提交？ → revert 生成反向提交
```

### 2.1 未提交修改

查看后再丢弃某个文件的工作区修改：

```bash
git diff -- app/cli.py
git restore app/cli.py
```

取消暂存但保留文件内容：

```bash
git restore --staged app/cli.py
```

这两条含义不同：`--staged` 只把文件移出暂存区，不会删除刚写的代码。

### 2.2 已提交但尚未共享

若只是提交说明写错：

```bash
git commit --amend
```

改写本地历史会改变提交 ID。只有确认提交未被他人基于其继续工作时才使用。课程主线不要求依赖 `reset --hard`；它会同时移动分支并丢弃工作区，误用恢复成本高。

### 2.3 已共享提交

对已推送或已合并的错误提交，优先新增反向提交：

```bash
git log --oneline
git revert <commit-id>
```

`revert` 保留完整审计轨迹，适合共享分支。若冲突，解决后执行：

```bash
git add <resolved-files>
git revert --continue
```

### 跑一下

在临时分支创建两个提交，然后回退第二个：

```bash
git switch -c practice/revert
printf "v1\n" > revert-demo.txt
git add revert-demo.txt
git commit -m "chore: add revert demo"
printf "v2\n" >> revert-demo.txt
git add revert-demo.txt
git commit -m "chore: update revert demo"
git revert HEAD
git log --oneline -n 4
```

确认文件回到第一版内容，同时历史中出现一个新的 `Revert ...` 提交。

### 易错点

| 错误 | 风险 | 更安全的做法 |
|------|------|--------------|
| 对共享分支 force push | 覆盖他人历史 | 使用 `git revert` |
| 未看 diff 就 `restore` | 未提交工作直接丢失 | 先 `git diff`，必要时复制或 stash |
| 把 `restore --staged` 当删除修改 | 误解状态 | 它只取消暂存 |
| 用 revert 回退 merge 却不理解主线父提交 | 可能留下意外结果 | 先在临时分支演练并请维护者复核 |

---

## 3. `.gitignore`：控制进入版本库的文件

### 为什么需要

Python 项目会产生虚拟环境、缓存、测试报告、本地配置和 IDE 状态。这些文件不可移植、变化频繁，甚至可能含密钥，不应进入仓库。

### 推荐基线

```gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Virtual environments
.venv/
venv/

# Local secrets and overrides
.env
.env.*
!.env.example

# Build artifacts
build/
dist/
*.egg-info/

# IDE / OS
.idea/
.vscode/
.DS_Store

# Local runtime output
*.log
```

团队共享的 IDE 配置是否提交应由团队决定，不要盲目复制模板。锁文件通常用于复现依赖，应按所用工具的官方建议提交，而不是一概忽略。

### 跑一下

```bash
git check-ignore -v .venv/ .env app.log
git status --ignored --short
```

若某文件已经被 Git 跟踪，新增 ignore 规则不会自动取消跟踪：

```bash
git rm --cached .env
```

随后必须轮换其中已泄露的密钥。`.gitignore` 不是安全边界：密钥一旦进入提交历史，就按泄露事件处理。

### 易错点

1. 忽略 `.env.example`，导致别人不知道需要哪些变量。
2. 把依赖锁文件、迁移文件或业务数据样例一股脑忽略，破坏可复现性。
3. 认为删掉最新提交中的密钥就安全；远端历史、缓存和日志里仍可能存在。
4. 使用过宽规则，如 `*.json`，误伤配置、测试夹具和评测集。

---

## 4. GitHub Actions：FakeLLM + pytest 合并门禁

### 为什么 CI 不应调用真实 LLM

合并门禁必须快速、确定、可重复。真实 LLM 具有网络抖动、额度、密钥和非确定性问题。按本课程约定，单测与 CI 必须在 FakeLLM 下通过；真模型验证属于可选集成测试或评测，不阻塞基础合并。

可靠边界：

```text
PR 必跑：纯逻辑 + FakeLLM + pytest
可选任务：真实 API 集成测试（手动触发、独立 secrets、非必需）
```

### 两种工作流：学习者单仓 vs 本课仓库矩阵

教学上先掌握**单项目**门禁；本课仓库本身用 **matrix** 覆盖六个参考实现。不要把两者混成同一份 YAML。

#### A. 学习者自己的项目：`.github/workflows/ci.yml`

在你独立维护的小项目里，新增单 job 即可：

```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: pytest-fake
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Install project
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      - name: Run deterministic tests
        env:
          LLM_BACKEND: fake
        run: python -m pytest -q
```

若你**自己**后续加了需要外网/真实密钥的集成测试，再在 `pyproject.toml` 注册 `live` 标记，并把 CI 改成 `python -m pytest -q -m "not live"`。**本课六个参考实现默认不使用 `live` 标记**——Fake 是默认路径，CI 直接跑全量 pytest，不要凭空假设仓库里已有 `-m "not live"`。

#### B. 本课仓库实况：`.github/workflows/projects-ci.yml`

本仓库用 matrix 在六个 `playground/projects/*` 目录分别安装与测试（摘录）：

```yaml
name: Projects CI

on:
  push:
    paths:
      - "playground/projects/**"
      - ".github/workflows/projects-ci.yml"
  pull_request:
    paths:
      - "playground/projects/**"
      - ".github/workflows/projects-ci.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test:
    name: Test ${{ matrix.project }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        project:
          - playground/projects/01-cli-tool
          - playground/projects/02-fastapi-todo
          - playground/projects/03-ai-chat
          - playground/projects/04-rag-kb
          - playground/projects/05-tool-agent
          - playground/projects/06-research-agent
    defaults:
      run:
        working-directory: ${{ matrix.project }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: ${{ matrix.project }}/pyproject.toml
      - name: Install project
        run: python -m pip install --upgrade pip && python -m pip install -e '.[dev]'
      - name: Run tests
        env:
          APP_API_KEY: ci-development-key
        run: pytest
      # P4～P6 另有条件步骤跑 scripts/eval/run_eval.py
```

要点：

- 每个项目是独立 working-directory，互不共享安装环境；
- Fake 路径默认绿；真模型密钥不进入该门禁；
- P4/P5/P6 在 pytest 之后额外跑评测脚本（见工作流条件步骤）；
- 完整文件以仓库 [`.github/workflows/projects-ci.yml`](../../.github/workflows/projects-ci.yml) 为准。

Fake 应通过依赖注入进入被测对象，不要在测试里根据“CI 环境”偷偷改变业务语义：

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

### 把检查设为门禁

工作流存在不等于门禁。仓库管理员还需在 GitHub 的分支保护或 Ruleset 中：

1. 目标分支选择 `main`。
2. 要求通过 Pull Request 合并。
3. 开启“Require status checks to pass”。
4. 选择稳定的检查名（单项目示例为 `pytest-fake`；本课仓库为 `Test playground/projects/...` 这类 matrix job 名）。
5. 视团队需要要求分支在合并前保持最新。

工作流 job 的 `name` 不应频繁改，否则 required check 可能失去匹配。

### 跑一下

本地先在单个项目目录执行与 CI 等价的核心命令：

```bash
cd playground/projects/01-cli-tool   # 或其他项目
python -m pip install -e '.[dev]'
python -m pytest -q
```

再推送测试分支，确认 PR 中：

- 对应 job 被触发；
- 不要求真实模型 API Key；
- 故意破坏一个断言会红；
- 修复并推送后重新变绿。

### 易错点

1. 只在 `push: main` 触发：错误代码合并后才发现，应同时监听 `pull_request`。
2. 把 secrets 直接写进 YAML、测试或日志；secret 只通过仓库配置注入，Fake 门禁不需要模型 secret。
3. 用 `pytest` 裸命令时解释器来源不明确；`python -m pytest` 更容易保证使用当前环境。
4. 本地装了额外依赖而 CI 未声明，形成“我的机器能跑”。
5. Action 只显示绿灯但未配置 required check，红灯仍可合并。
6. 给第三方 PR 暴露高权限 token；默认使用最小 `permissions`，不要在不可信代码上运行敏感 secrets。
7. 把本课仓库的 matrix 工作流原样抄进单项目，或反过来假设本课项目已启用 `live` / `-m "not live"`。

---

## 5. 分支同步与冲突处理（建议掌握）

开始处理冲突前确保工作区干净，并获取远端状态：

```bash
git fetch origin
git rebase origin/main
```

若团队采用 merge，则遵循团队约定，不要在同一 PR 中反复混用 merge/rebase。rebase 冲突时：

```bash
# 编辑冲突文件，删除冲突标记并验证
git add <resolved-files>
git rebase --continue
```

无法确认该如何合并时：

```bash
git rebase --abort
```

rebase 会重写主题分支提交 ID；不要对多人共享、他人已基于其开发的分支擅自 rebase。

---

## 6. 一套可执行的提交前检查

项目可把统一命令写进 README、Makefile 或任务工具，但本质应清楚：

```bash
git status --short
git diff --check
python -m pytest -q
git diff --cached
```

（若你的项目额外注册了 `live` 标记，再改用 `python -m pytest -q -m "not live"`。）

其中：

- `git diff --check` 检查尾随空格和冲突标记等补丁问题；
- pytest 验证行为；
- cached diff 验证提交边界。

不要让本地 hook 成为唯一门禁：hook 可以被跳过，CI 才是共享的最终验证环境。

---

## 7. 综合小例子：给 CLI 增加 JSON 输出

1. 创建 `feat/textstat-json`。
2. 修改业务输出并补 pytest。
3. 本地运行 Fake/pytest 门禁。
4. 检查工作区 diff，排除 `.env`、日志和临时输出。
5. 以 `feat(cli): add json output` 提交并推送。
6. PR 说明写清行为变化和验证命令。
7. 对应 CI job（单项目 `pytest-fake`，或本课仓库的 matrix job）通过后合并。
8. 若合并后发现行为错误，使用 `git revert <commit>` 创建修复 PR，而不是改写 `main` 历史。

这条链路把“开发动作”与“可审查证据”绑定起来：提交说明目标，测试说明契约，CI 说明在干净环境可复现。

---

## 8. 自检

- [ ] 能解释工作区、暂存区、提交三种状态。
- [ ] 提交前会检查 `git diff` 与 `git diff --cached`。
- [ ] 能区分 `restore`、`restore --staged`、`commit --amend`、`revert`。
- [ ] 不会对已共享的 `main` 随意改写历史。
- [ ] 能用 `git check-ignore -v` 解释某文件为何被忽略。
- [ ] 知道 `.gitignore` 不能挽救已经泄露的密钥。
- [ ] 能写一个只依赖声明文件、FakeLLM 和 pytest 的单项目 GitHub Actions job。
- [ ] 能说明本课 `projects-ci.yml` matrix 与单项目 `ci.yml` 的差异。
- [ ] 能说明“Action 绿灯”和“required check 门禁”的区别。

### 一句话带走

> Git 让每次变更可追踪、可审查、可回退；CI 用确定性的 FakeLLM + pytest 证明它可以安全合并。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[CLI 入口与参数解析](./05-cli-entrypoints.md)
- 下一章：[调试与故障定位](./07-debugging.md)
