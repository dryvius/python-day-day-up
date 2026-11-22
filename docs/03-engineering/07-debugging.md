# 调试与故障定位

> 所属模块：`03-engineering` · Python 工程化  
> 状态：`已完成正文`  
> 建议学时：3～5 小时  
> 对应练习：[`exercises/03-engineering/07-debugging.md`](../../exercises/03-engineering/07-debugging.md)

## 本章定位

- **模块目标**：从“看到报错就改”升级为“保留现场、缩小范围、验证假设”。
- **本章角色**：建立统一排障流程，覆盖 traceback、`breakpoint()`/pdb、IDE，以及异步和 FastAPI 常见问题。
- **前置**：异常系统、pytest、logging、CLI。
- **原则**：调试器用于观察现场，测试用于固化修复，日志用于跨请求和跨环境追踪；三者不能互相替代。

## 学习目标

1. 能从 traceback 最后一段异常出发，沿调用栈定位首个属于自己代码的帧。
2. 能用 `breakpoint()` / pdb 检查变量、单步执行和调用栈。
3. 能在 IDE 中配置正确解释器、断点和 pytest 调试入口。
4. 能定位“忘记 await、任务异常丢失、阻塞事件循环”等异步问题。
5. 能区分 FastAPI 的启动、路由、校验、依赖和业务异常。
6. 修复后能增加回归测试并移除临时调试产物。

## 重点分级

| 级别 | 内容 | 学习要求 |
|------|------|----------|
| **必掌握** | traceback、最小复现、断点、调用栈、回归测试 | 能独立定位普通 Python 故障 |
| **建议掌握** | IDE 条件断点、pytest 调试、async/FastAPI 定位 | 能处理后续主线常见问题 |
| **了解即可** | 远程调试、采样分析器、分布式 trace | 生产场景再深入 |

---

## 1. 一套稳定的排障闭环

遇到故障时，先把“猜”变成可验证假设：

```text
复现 → 保存完整现场 → 分类故障 → 缩小范围
     → 提出一个假设 → 用断点/日志/测试验证 → 修复 → 回归
```

### 1.1 先固定复现条件

至少记录：

- 运行命令、当前目录、Python 版本和虚拟环境；
- 输入样例与必要配置（密钥必须脱敏）；
- 完整 traceback，不只截最后一行；
- 是否稳定复现，首次出现在哪次变更后；
- 同一输入在测试、CLI、服务中是否都失败。

```bash
python --version
python -c "import sys; print(sys.executable)"
python -m pytest tests/test_parser.py -x -vv
```

### 1.2 先分类，再选工具

| 现象 | 第一检查点 |
|------|------------|
| 立即抛异常 | traceback 与输入边界 |
| 结果错误但不抛异常 | 最小失败用例、关键中间值、断点 |
| 卡住/超时 | 阻塞调用、锁、网络超时、任务栈 |
| 仅 CI 失败 | 依赖声明、路径、环境变量、时区/平台差异 |
| 仅 FastAPI 失败 | 状态码、响应体、服务端 traceback、依赖链 |
| 偶发失败 | 共享状态、并发、随机数、时钟、外部服务 |

### 跑一下

对一个失败测试执行：

```bash
python -m pytest tests/test_parser.py::test_rejects_empty -x -vv
```

先把失败缩到一个用例，再决定是否进入 pdb。不要一开始就在整个服务上到处加断点。

### 易错点

1. 同时改多处“试试看”，即使好了也不知道哪个假设成立。
2. 只复制异常最后一句，丢掉调用路径和源代码行。
3. 为了继续运行而捕获 `Exception` 后静默返回默认值，现场反而消失。
4. 在没有稳定复现前做大规模重构。

---

## 2. 读 traceback：从异常类型回到业务入口

### 2.1 阅读顺序

典型 traceback：

```text
Traceback (most recent call last):
  File "app/main.py", line 12, in main
    load_config(path)
  File "app/config.py", line 21, in load_config
    timeout = int(raw["timeout"])
ValueError: invalid literal for int() with base 10: 'fast'
```

实用阅读顺序：

1. **最后一行**：异常类型与消息，说明直接失败原因。
2. **向上找第一个属于项目的栈帧**：通常是最接近故障的自有代码。
3. **继续向上**：确认坏数据从哪个入口进入。
4. 若有 `During handling...` 或 `direct cause...`，分别检查原异常与转换后的业务异常。

“最后一个栈帧”不一定就是根因。例如库内 `KeyError` 可能由你的输入转换错误导致。定位目标是数据首次违背契约的位置，而非只修补最终崩溃行。

### 2.2 保留异常链

转换异常时使用 `raise ... from exc`：

```python
def parse_timeout(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError("timeout must be an integer") from exc
```

这样对外有领域语义，对内仍保留原始原因。

### 跑一下

```python
def inner() -> int:
    return int("fast")


def outer() -> int:
    return inner()


outer()
```

运行后回答：

- 异常类型是什么？
- 哪个栈帧是真正转换失败的位置？
- 哪个栈帧是业务入口？

### 易错点

1. 用 `raise exc` 代替裸 `raise` 重新抛出，导致 traceback 起点发生变化；在 `except` 中保留原栈通常用 `raise`。
2. 只打印 `str(exc)`，没有 traceback；异常路径日志使用 `logger.exception(...)`。
3. 把第三方库最后一帧当根因，不检查传入参数。
4. 对用户返回完整 traceback，泄露路径、查询和内部结构；用户响应与内部诊断信息应分离。

---

## 3. `breakpoint()` 与 pdb

### 3.1 最小用法

在需要观察的代码前放置：

```python
def normalize_user(raw: dict[str, object]) -> str:
    breakpoint()
    name = raw["name"]
    if not isinstance(name, str):
        raise TypeError("name must be str")
    return name.strip()
```

运行到这里后进入 pdb。常用命令：

| 命令 | 作用 |
|------|------|
| `l` / `ll` | 查看附近/当前函数源码 |
| `p expr` / `pp expr` | 查看表达式 |
| `n` | 执行当前行，停在同一函数下一行 |
| `s` | 进入当前行调用的函数 |
| `r` | 运行到当前函数返回 |
| `w` / `bt` | 查看调用栈 |
| `u` / `d` | 在调用栈上移/下移 |
| `c` | 继续运行到下个断点 |
| `q` | 退出 |

不要用调试器命令修改状态来“修好”程序；可临时验证假设，但最终修复必须进入代码并由测试证明。

### 3.2 失败时自动进入 pdb

pytest 支持：

```bash
python -m pytest tests/test_parser.py -x --pdb
```

它会在失败现场进入调试器，通常比提前猜断点位置更高效。若要显示捕获的输出，可结合 `-s`，但注意输出可能变多。

### 跑一下

```python
def total(prices: list[str]) -> float:
    values = [float(price) for price in prices]
    breakpoint()
    return sum(values)


print(total(["10.5", "2.0"]))
```

在 pdb 中依次执行：

```text
p prices
p values
w
n
p sum(values)
c
```

### 易错点

1. 把 `breakpoint()` 提交进主分支，CI 或服务运行时会停住。
2. 在多进程/重载服务里使用终端 pdb，输入可能连到错误进程；开发时先关闭 reload 或用 IDE attach。
3. pdb 中直接调用有副作用的函数，导致数据库、网络或迭代器状态变化。
4. 变量名恰好与 pdb 命令冲突时，可用 `p variable` 明确求值。

---

## 4. IDE 调试：配置正确比点红点更重要

IDE 断点本质仍是暂停进程并检查栈帧。开始前确认：

1. 解释器指向项目虚拟环境。
2. 工作目录与平时运行命令一致。
3. 环境变量来自安全的本地配置，不提交真实密钥。
4. 调试目标与真实入口一致：模块、pytest 或 ASGI 服务。

### 常见入口

#### 调试模块

以 `python -m app` 的方式启动，而不是直接运行包内某个文件，避免导入路径行为不同。

#### 调试 pytest

从测试旁的“Debug Test”启动，或创建 pytest 类型配置。断点应先落在失败用例和第一个自有代码栈帧。

#### 条件断点

循环或批量请求中，不要让断点命中数千次。可设置：

```text
item.id == "broken-42"
```

也可使用 hit count 或日志断点观察特定条件。

### 跑一下

对一个参数化测试：

1. 在被测函数入口设普通断点；
2. 确认 IDE 选中的解释器；
3. 只调试失败参数；
4. 查看 Variables、Call Stack；
5. 用 Step Into/Over 验证数据在哪一步变坏。

### 易错点

1. IDE 运行的是全局 Python，本地终端运行的是 `.venv`，依赖版本不同。
2. 调试配置工作目录错误，导致相对路径或配置文件找不到。
3. 开启 FastAPI reload 后出现父子两个进程，断点不命中或命中两次。
4. 在 Watch 中执行昂贵属性或有副作用表达式。

---

## 5. 异步代码常见定位

异步故障不只表现为异常，还可能是警告、挂起、任务被取消或“从未执行”。

### 5.1 忘记 `await`

```python
result = client.fetch()  # 得到 coroutine，不是结果
```

常见信号：

```text
RuntimeWarning: coroutine '...' was never awaited
```

修复前先确认当前函数能否变成 `async def`，再：

```python
result = await client.fetch()
```

不要用随手加 `asyncio.run()` 修补框架内部异步代码；运行中的事件循环不能被这样嵌套管理。

### 5.2 后台任务异常丢失

```python
task = asyncio.create_task(worker())
```

如果既不保存任务、也不 await/检查结果，可能出现：

```text
Task exception was never retrieved
```

结构化并发优先用 `TaskGroup`：

```python
async with asyncio.TaskGroup() as group:
    group.create_task(fetch_one())
    group.create_task(fetch_two())
```

确实需要长生命周期后台任务时，要保存引用、定义关闭策略并记录异常。

### 5.3 阻塞事件循环

在 `async def` 中调用 `time.sleep()`、同步 HTTP 或大型 CPU 计算，会让所有请求一起卡住。

```python
# 错误
time.sleep(2)

# 定时等待
await asyncio.sleep(2)

# 必须调用的同步阻塞函数
result = await asyncio.to_thread(blocking_call)
```

### 5.4 开启 asyncio 调试信息

本地可使用：

```bash
PYTHONASYNCIODEBUG=1 python -X dev -m pytest tests/test_async_service.py -x -vv
```

它能暴露未等待协程、慢回调和资源警告，但会增加噪音和开销，不应无条件用于生产。

### 跑一下

```python
import asyncio
import time


async def bad_worker() -> None:
    time.sleep(1)


async def heartbeat() -> None:
    for _ in range(3):
        print("tick")
        await asyncio.sleep(0.2)


async def main() -> None:
    await asyncio.gather(bad_worker(), heartbeat())


asyncio.run(main())
```

观察 `tick` 为什么延迟，再把 `time.sleep` 改成 `await asyncio.sleep` 比较。

### 易错点

1. 把所有异步超时都归因于网络；先检查同步阻塞。
2. 捕获 `CancelledError` 后不重新抛出或不完成清理，破坏取消语义。
3. 为了看到异常把任务全部串行 await，掩盖真实并发结构。
4. 用断点长时间暂停事件循环，触发客户端超时；调试时缩短链路或提高本地超时，而非改变生产默认值。

---

## 6. FastAPI 常见定位

### 6.1 先按生命周期分层

| 阶段 | 常见现象 | 检查点 |
|------|----------|--------|
| import/启动 | 服务起不来 | 完整启动 traceback、导入路径、配置、lifespan |
| 路由匹配 | 404/405 | URL、前缀、HTTP method、路由注册 |
| 请求校验 | 422 | 响应 `detail`、参数位置、Pydantic schema |
| 依赖注入 | 401/403/500 | 依赖执行顺序、header/cookie、异常映射 |
| 业务处理 | 500/结果错 | 服务端 traceback、业务边界、数据库/外部服务 |
| 响应序列化 | 500 | `response_model`、返回类型、不可序列化对象 |

422 通常不是“FastAPI 坏了”，而是请求没有满足公开契约。先读响应 JSON 中的 `loc`、`msg`、`type`。

### 6.2 最小测试优先

用测试客户端复现比手工点接口更稳定：

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_item_rejects_missing_name() -> None:
    response = client.post("/items", json={})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "name"
```

异步依赖或异步数据库测试可使用项目已选定的 async 测试方案；不要在同步测试中随意嵌套事件循环。

### 6.3 调试服务

开发时可暂时关闭 reload，确保断点连接到唯一进程：

```bash
uvicorn app.main:app --log-level debug
```

重点观察：

- 请求 ID/路径/状态码；
- 服务端完整 traceback；
- 依赖和业务层的第一个自有代码帧；
- 外部调用是否设置连接、读取和总超时；
- 日志是否脱敏。

### 6.4 不要吞掉 HTTP 语义

过宽异常处理会把 404/401 等业务响应改成 500：

```python
try:
    return service.get_item(item_id)
except ItemNotFoundError as exc:
    raise HTTPException(status_code=404, detail="item not found") from exc
```

只在明确边界转换已知异常。未知异常应保留 traceback，由统一错误处理中间件返回安全文案。

### 跑一下

构造三个请求并分别记录证据：

1. 错 URL，观察 404；
2. 对正确 URL 使用错误 method，观察 405；
3. 缺少必填字段，观察 422 的 `detail.loc`。

不要只记状态码，要能说出它在哪个阶段失败。

### 易错点

1. 浏览器能访问 GET，就误以为 POST 路由也正确。
2. 看到 422 就在业务函数打断点；请求尚未通过校验，业务函数不会执行。
3. `--reload` 下断点行为异常仍反复点击；先关闭 reload。
4. 把数据库 session、协程或自定义对象直接作为响应返回。
5. 将完整请求体、Authorization header 或模型 prompt 写入 debug 日志。

---

## 7. 日志、调试器、测试如何分工

| 工具 | 最适合 | 不适合 |
|------|--------|--------|
| traceback | 一次异常的调用路径与原因链 | 解释无异常的错误结果 |
| 调试器 | 单次可复现故障、检查内存状态 | 长时间生产观测 |
| logging | 跨请求、跨进程、线上历史证据 | 精细单步执行 |
| pytest | 固化输入输出契约、防止复发 | 临时探索未知现场 |

推荐组合：

```text
日志找到失败 run_id
→ 用同一输入写最小失败测试
→ 用 traceback/断点验证根因
→ 修复并保留回归测试
→ 删除 breakpoint 与敏感临时日志
```

日志的配置、字段和脱敏规范归 [`04-logging.md`](./04-logging.md)；本章只讨论如何把日志作为定位证据。

---

## 8. 综合小例子：FastAPI 异步接口变慢

现象：`POST /summaries` 偶发需要 6 秒，同时健康检查也变慢。

定位过程：

1. 用请求 ID 关联日志，确认多个请求同时停顿。
2. 测试中并发请求，得到稳定复现。
3. IDE 断点和调用栈显示 `async def summarize()` 内调用同步 SDK。
4. 开启 asyncio debug，看到慢回调提示。
5. 将可替换 SDK 改为异步客户端；过渡期用 `asyncio.to_thread` 隔离阻塞。
6. 增加并发回归测试，断言健康检查不会被单请求长时间阻塞。
7. 移除临时断点，保留脱敏耗时日志。

关键不是“猜到 SDK 慢”，而是证据链证明：同步阻塞发生在事件循环线程，并影响无关请求。

---

## 9. 自检

- [ ] 能按“最后一行 → 第一个自有代码帧 → 上游入口”阅读 traceback。
- [ ] 转换异常时会保留异常链，重新抛出时知道何时用裸 `raise`。
- [ ] 会使用 `p`、`n`、`s`、`w`、`u`、`d`、`c`。
- [ ] 能用 `pytest -x --pdb` 进入失败现场。
- [ ] 能检查 IDE 的解释器、工作目录、环境变量和真实入口。
- [ ] 能识别未 await 协程、后台任务异常和事件循环阻塞。
- [ ] 能区分 FastAPI 的 404、405、422 与业务 500。
- [ ] 修复后会增加回归测试，并移除 `breakpoint()` 与敏感临时日志。

### 一句话带走

> 高效调试不是多打几个 print，而是保留证据、缩小失败范围，并让每次观察只验证一个假设。

完成本章后，进入 [Project 1：Python CLI 工具](../projects/01-cli-tool.md)，用真实 CLI 练习排障与回归测试。

## 导航

- 返回模块：[README](./README.md)
- 上一章：[Git 协作与 CI 门禁](./06-git-ci.md)
- 下一站：[Project 1：Python CLI 工具](../projects/01-cli-tool.md)
- 下一模块：[计算机与服务端基础](../04-systems-basics/README.md)
