# 练习：调试与故障定位

> 对应文档：[`docs/03-engineering/07-debugging.md`](../../docs/03-engineering/07-debugging.md)  
> 状态：`已完成出题`  
> 建议用时：90～150 分钟

## 练习说明

本章不以“修好即可”为验收，而要求提交一条证据链：

```text
复现命令 → 现象/traceback → 假设 → 验证方式 → 根因 → 修复 → 回归测试
```

调试样例可放在 `playground/03-engineering/07-debugging/`。完成后不得保留会阻塞运行的 `breakpoint()`。

---

## 热身题

### W1. Traceback 阅读

运行：

```python
def parse_port(raw: str) -> int:
    return int(raw)


def load_config(config: dict[str, str]) -> int:
    return parse_port(config["port"])


load_config({"port": "fast"})
```

写出：

1. 异常类型和直接原因；
2. 最接近故障的自有代码帧；
3. 数据进入的上游业务入口；
4. 你会在哪一层增加输入校验。

### W2. 工具选择

分别选择 traceback、调试器、logging、pytest 中最合适的首选工具：

1. 线上某个 `run_id` 偶发失败；
2. 本地稳定复现的中间变量错误；
3. 修复后防止同一输入再次出错；
4. 程序立即抛异常并显示完整调用栈。

---

## 基础题（必做）

### B1. 异常链

实现 `load_timeout(raw: str) -> int`：

- 非整数输入转换为带业务语义的 `ConfigError`；
- 使用 `raise ... from exc` 保留原始 `ValueError`；
- pytest 同时断言业务异常和 `__cause__`。

**验收**：完整 traceback 同时包含底层转换失败和上层配置语义。

### B2. pdb 定位

给定：

```python
def average(values: list[str]) -> float:
    numbers = [float(value) for value in values]
    return sum(numbers) / len(values)
```

为 `average([])` 写失败测试，使用：

```bash
python -m pytest <test-path> -x --pdb
```

在调试记录中写出至少一次：

- `p values`
- `p numbers`
- `w`
- `u`/`d`

修复契约可以选择拒绝空列表或定义默认值，但必须由测试明确，不得静默猜测。

### B3. 最小复现与回归

从项目中过去遇到的一个错误，或自行构造一个解析错误：

1. 将问题缩成一个失败 pytest；
2. 只提出一个根因假设；
3. 用断点或额外断言验证；
4. 修复；
5. 保留回归测试；
6. 删除临时断点与敏感日志。

**验收**：提交说明中能区分“现象”和“根因”。

### B4. IDE 调试

用 IDE 调试 B3 的失败测试：

- 解释器必须是项目虚拟环境；
- 在第一个自有代码帧设置断点；
- 展示调用栈和关键变量；
- 若循环命中多次，改用条件断点。

**验收**：记录解释器路径、工作目录、调试入口和断点命中条件。

### B5. 异步阻塞定位

运行并解释：

```python
import asyncio
import time


async def blocking_job() -> None:
    time.sleep(1)


async def heartbeat() -> list[float]:
    loop = asyncio.get_running_loop()
    ticks: list[float] = []
    for _ in range(3):
        ticks.append(loop.time())
        await asyncio.sleep(0.1)
    return ticks
```

补出并发执行两者的 `main()` 和测试，然后将阻塞调用替换为正确方案。

**验收**：

- 能证明健康任务被阻塞，而非只说“感觉慢”；
- 定时等待使用 `await asyncio.sleep`；
- 若模拟必须保留的同步函数，使用 `asyncio.to_thread`；
- 可用 `PYTHONASYNCIODEBUG=1` 辅助观察。

### B6. FastAPI 分层定位

为一个最小 FastAPI 路由构造：

1. 404：路径错误；
2. 405：method 错误；
3. 422：请求缺少必填字段；
4. 业务 404：资源不存在并由领域异常映射；
5. 500：未知异常，服务端保留 traceback，响应不泄露内部细节。

**验收**：

- 每种情况有测试；
- 422 会检查 `detail.loc`；
- 不用 `except Exception` 把所有错误都改成同一状态码；
- 日志不包含 Authorization、密钥或完整敏感请求体。

---

## 进阶题（建议）

### A1. 后台任务异常

构造一个 `asyncio.create_task()` 内抛错且未取回结果的例子，观察警告。再使用 `TaskGroup` 或显式任务所有权修复。

回答：

- 谁拥有任务？
- 谁等待结果？
- 谁负责取消与关闭？
- 异常如何传播或记录？

### A2. FastAPI 断点

关闭 reload，以单进程方式调试服务：

```bash
uvicorn app.main:app --log-level debug
```

在依赖函数、路由入口、业务函数分别设置断点，观察 422 请求为何不会进入路由业务函数。

---

## 挑战题（可选）

### C1. 故障报告模板

为项目建立可复用模板，至少包含：

```text
环境 / 版本
最小复现命令
期望与实际
完整 traceback 或关联 run_id
影响范围
根因
修复
回归测试
```

用 B5 或 B6 填一份完整报告。

---

## 本章通过线

- [ ] B1～B6 完成。
- [ ] 能从 traceback 找到异常类型、故障帧和上游入口。
- [ ] 会使用 pdb/IDE 查看变量和调用栈。
- [ ] 能用证据识别异步阻塞或任务异常。
- [ ] 能按 FastAPI 生命周期区分 404、405、422、业务错误和未知 500。
- [ ] 每个修复都有最小回归测试。
- [ ] 仓库中无遗留 `breakpoint()`，无敏感临时日志。

## 自检问题

1. 为什么只看 traceback 最后一行不够？
2. `n` 和 `s` 的区别是什么？
3. 为什么 IDE 调试前必须确认解释器和工作目录？
4. “coroutine was never awaited”通常说明什么？
5. FastAPI 返回 422 时，为何路由业务断点可能不命中？
6. 调试完成后，哪些证据应留下，哪些临时手段应删除？

## 导航

- 对应正文：[调试与故障定位](../../docs/03-engineering/07-debugging.md)
- 上一练习：[Git 协作与 CI 门禁](./06-git-ci.md)
- 返回练习总览：[README](../README.md)
