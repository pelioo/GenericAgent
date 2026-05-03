# ReAct Cognitive Loop SOP

> 核心认知循环框架 v1.0  
> 来源：用户定制（彭利） | 适用：复杂任务推理与执行 | 优先级：HIGH

---

## 🎯 框架概述

```
Emotional + Meta-Analysis 
  → Dynamic Divergent Planning 
  → Adaptive Action & Observation 
  → Graph Synthesis + Ethical Guardrails 
  → Reflective Loop & Proactive Suggestion
```

### 核心原则
1. **认知闭环**：每轮循环必须包含输入→推理→行动→反思
2. **伦理优先**：行动前必须通过伦理护栏检查
3. **元认知监控**：持续自我审视推理过程
4. **知识沉淀**：每轮循环后更新知识图谱

---

## 🔄 五阶段详解

### Stage 1️⃣: Emotional + Meta-Analysis（情感 + 元认知分析）

**目的**：理解用户意图 + 评估自身状态

**操作步骤**：
1. 情感识别：判断用户语气/情绪（友好/急切/困惑/愤怒）
2. 意图解析：提取核心需求和隐含约束
3. 元认知检查：
   - 我理解正确吗？
   - 我有足够信息吗？
   - 是否需要澄清？

**输出**：
```json
{
  "emotion": "友好/急切/困惑",
  "intent": "核心任务",
  "constraints": ["约束1", "约束2"],
  "confidence": 0.85,
  "need_clarify": false
}
```

---

### Stage 2️⃣: Dynamic Divergent Planning（动态发散规划）

**目的**：生成多个可能的解决路径

**操作步骤**：
1. 头脑风暴：不限制方案数量
2. 评估可行性：对每个方案预估成功率
3. 优先级排序：按"成功率×价值"排序
4. 备选方案：准备2-3个备选计划

**输出**：
```json
{
  "primary_plan": {
    "steps": ["步骤1", "步骤2", "步骤3"],
    "estimated_success": 0.9
  },
  "alternatives": [
    {"plan_id": "A", "description": "...", "success": 0.7}
  ]
}
```

---

### Stage 3️⃣: Adaptive Action & Observation（自适应行动与观察）

**目的**：执行计划 + 实时监控结果

**操作步骤**：
1. 执行首选方案
2. 关键节点检查点（每步后评估）
3. 异常处理：失败时自动切换备选方案
4. 结果记录：保存所有中间结果

**输出**：
```json
{
  "action_taken": "执行的具体操作",
  "observation": "观察到的结果",
  "success": true,
  "next_action": "下一步操作"
}
```

---

### Stage 4️⃣: Graph Synthesis + Ethical Guardrails（图谱合成 + 伦理护栏）

**目的**：知识整合 + 安全检查

**操作步骤**：
1. **伦理检查**（必须先执行）：
   - 是否违反用户安全准则？
   - 是否涉及敏感操作？
   - 是否需要用户确认？
2. **知识图谱更新**：
   - 新增节点：任务类型、解决路径
   - 更新边：关联关系
3. 经验沉淀：失败教训也需记录

**伦理检查清单**：
- [ ] 不读取/移动密钥文件
- [ ] 不执行不可逆危险操作
- [ ] 需用户批准的操作先询问
- [ ] 敏感操作记录日志

---

### Stage 5️⃣: Reflective Loop & Proactive Suggestion（反思循环 + 主动建议）

**目的**：自我改进 + 主动服务

**操作步骤**：
1. 反思本轮表现：
   - 哪里做得好？
   - 哪里可以改进？
   - 下次遇到类似任务如何优化？
2. **[Self-Improving增强]** 检查corrections.md是否有本轮相关纠正 → 记录
3. **[Self-Improving增强]** 复杂任务(≥3轮)生成反思条目 → 写入self_improving_reflections.md
4. 检查用户是否还有其他潜在需求
5. 主动建议：如果发现用户可能需要相关信息，主动提醒

**输出**：
```json
{
  "reflection": "反思内容",
  "improvement": "下次改进点",
  "proactive_suggestions": ["建议1", "建议2"],
  "correction_tracked": true/false,
  "reflection_logged": true/false
}
```

---

## 📋 完整循环示例

```
用户请求：查询宁波天气

[Stage 1] Emotion=友好, Intent=查天气, Confidence=0.95
    ↓
[Stage 2] Plan1=用web_scan, Plan2=用subprocess
    ↓
[Stage 3] 执行web_scan → 获取数据成功
    ↓
[Stage 4] 伦理检查✓ → 更新天气知识图谱
    ↓
[Stage 5] 反思：可用js增强搜索 → 建议：五一出行注意...
    ↓
[输出完整天气报告+建议给用户]
```

---

## ⚡ 执行规则

1. **强制闭环**：每个任务必须经历完整5阶段（或明确跳过原因）
2. **失败升级**：某阶段失败 → 记录 → 尝试备选 → 3次失败请求用户干预
3. **效率权衡**：
   - 简单任务可简化流程，但保留核心检查点
   - 复杂任务严格执行全部阶段
4. **记录要求**：关键决策点必须记录原因

---

## 🔗 与其他SOP的关系

- **基础冲突时**：本SOP优先级 > 通用规则
- **结合使用**：
  - web任务 → 结合 tmwebdriver_sop
  - 键鼠任务 → 结合 ljqCtrl_sop
  - 视觉任务 → 结合 vision_sop

---

*最后更新：2026-05-03 | 创建者：GA | 定制者：彭利*
