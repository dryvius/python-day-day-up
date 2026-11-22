# 模块 02-advanced-python：Python 高级特性与类型系统

> 状态：`七章正文与练习已全部完成` · 建议周期：5～7 周

## 模块目标

建立 Python 内功，能读现代框架源码里的抽象。

## 为什么现在学

Agent Framework 大量使用 Class / Protocol / Generic / DI。

## 章节目录

1. [面向对象编程](./01-oop.md) · [练习](../../exercises/02-advanced-python/01-oop.md)
2. [Python 数据模型](./02-data-model.md) · [练习](../../exercises/02-advanced-python/02-data-model.md)
3. [异常系统](./06-exception-system.md) · [练习](../../exercises/02-advanced-python/06-exception-system.md)
4. [Iterator / Generator](./03-iterator-generator.md) · [练习](../../exercises/02-advanced-python/03-iterator-generator.md)
5. [装饰器](./04-decorator.md) · [练习](../../exercises/02-advanced-python/04-decorator.md)
6. [上下文管理器](./05-context-manager.md) · [练习](../../exercises/02-advanced-python/05-context-manager.md)
7. [类型系统](./07-typing-system.md) · [练习](../../exercises/02-advanced-python/07-typing-system.md)

## 建议学习方式

1. 按上面的**学习顺序**阅读；文件编号保持原样是为了避免既有链接失效。异常系统提前后，装饰器重试与上下文清理会更容易理解
2. 只把「必掌握」吃透，其余按兴趣加餐
3. 立即做对应 `exercises/` 练习，先按自己的理解写出来再对照
4. 用模块末尾的自检确认是否可进入下一模块

## 模块通关门禁

- [ ] 所有章节基础练习达到各自“通过线”
- [ ] 能实现一个带类型注解的 `Tool`/`ToolRegistry`，并用自定义异常表达注册与调用失败
- [ ] 能写出生成器、装饰器和上下文管理器各一个实际用例，并覆盖成功/失败测试
- [ ] 能用 `Protocol` 或等价抽象描述 LLM/工具契约，不使用无边界的 `Any`
- [ ] 能阅读一段使用 `__call__`、装饰器、上下文管理和类型泛型的框架代码，并画出调用关系

## 导航

- 返回总览：[../../README.md](../../README.md)
