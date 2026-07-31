# 健康模块

## Health User

健康数据由 `Health User` 角色管理。两个健康 DocType 都启用了 owner 权限，
用户只能操作自己创建或由可信服务以其身份创建的记录。

管理员分配角色后，用户可以在 Frappe Desk 中使用健康模块。

## Health Body Metrics

身体指标记录使用以下命名格式：

```text
HBM-YYYY-MM-DD-#####
```

主要字段：

| 分类 | 字段 |
| --- | --- |
| 基础测量 | 测量时间、体重 kg、身高 cm、BMI |
| 脂肪与代谢 | 体脂率、脂肪重量、基础代谢 kcal/day |
| 肌肉 | 肌肉重量、肌肉率、骨骼肌重量 |
| 蛋白质 | 蛋白质重量、蛋白质率 |
| 水分 | 身体水分重量、身体水分率 |
| 骨骼 | 骨矿物质重量、骨矿物质率 |
| 来源 | Manual、MCP、Image Import |

BMI 为只读派生字段。控制器会拒绝非正数体重/身高、负数重量指标以及超过
`0–100` 范围的百分比。

### 测量时间

如果 MCP 来源只提供日期，没有精确时间，服务会设置
`measurement_time_is_estimated`，并在结果中返回提示。不要把估算时间当成
精确设备采集时间。

### MCP 写入幂等

MCP 客户端可以提供不超过 140 字符的 `client_request_id`。服务将
“用户 + request ID”哈希成唯一 key：

- 同一用户重复请求不会创建第二条记录；
- 不同用户可以使用相同 request ID；
- 重复调用会返回原记录，并将 `created` 标记为 false。

客户端应为每一次逻辑写入生成稳定且唯一的 request ID。

## Health Food Item

食物条目名称唯一，并按基础份量记录：

- 蛋白质；
- 脂肪；
- 碳水化合物；
- 自动计算的热量。

热量计算：

```text
calories = protein × 4 + carbohydrate × 4 + fat × 9
```

所有营养值必须为非负数，`base_unit` 必填。默认基础份量为 `100 g`。

## MCP 业务接口

Personal 为独立 Gateway 提供两个内部 method：

```text
personal.health.sidecar_api.create_health_body_metrics
personal.health.sidecar_api.get_health_body_metrics
```

它们虽然使用 `allow_guest=True` 接收网关请求，但并非公开匿名 API：进入业务
逻辑前必须通过内部断言签名、issuer、audience、scope、过期时间、用户状态和
防重放校验。缺少有效断言的请求会被拒绝。

## 测试重点

健康模块测试覆盖：

- BMI 和热量计算；
- 非法负值、百分比和基础份量；
- owner 权限隔离；
- MCP 创建与查询；
- request ID 幂等；
- 内部断言签名、防重放和用户切换。
