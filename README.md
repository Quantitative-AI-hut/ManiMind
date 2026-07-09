# ManiMind

ManiMind 是一个面向数学科普动画生产的多 Agent 编排项目。输入论文和笔记，输出可审核的讲解脚本、分镜、Manim 数学动画、HTML 科普片段，以及后续配音、字幕、剪辑拼接所需的结构化产物。

仓库定位是“编排层”，不重写外部渲染引擎内部实现。
`ClaudeCode/` 仅作为可选参考源码包，其可复用编排能力已抽取到 `src/manimind/`。

## 当前架构要点

1. 预启动阶段加载文档与配置，检测工具链，注册能力路径。
2. 主 Agent 解析论文与笔记，产出研究总结、公式目录与项目状态。
3. 协调 Agent 切分分镜并并发派发 HTML / Manim / SVG 子任务。
4. 子 Agent 分别回写长期上下文和短期协作上下文。
5. 审核 Agent 通过后，进入配音、字幕、剪辑拼接。

## 目录结构

```text
ManiMind/
├─ AGENTS.md
├─ README.md
├─ docs/
├─ configs/
├─ scripts/
├─ src/manimind/
├─ tests/
├─ resources/
│  ├─ skills/html-animation/
│  ├─ skills/manim/
│  └─ references/hyperframes/
├─ runtime/
├─ outputs/
└─ logs/
```

## 初始化步骤

1. 初始化目录与占位文件：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\init-workspace.ps1
```

2. 同步第三方精选资产（白名单）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-thirdparty-assets.ps1
```

源仓库不在项目根目录时，可显式传路径：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-thirdparty-assets.ps1 `
  -HtmlSkillSource "<AI-Animation-Skill-main 路径>" `
  -HyperframesSource "<hyperframes-main 路径>"
```

3. 检查依赖：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-prerequisites.ps1
```

## 关键约束

- 第三方资产统一放在 `resources/`，不再使用独立 `vendor/`。
- 长期上下文只写 `runtime/projects/<project_id>/`。
- 短期协作上下文只写 `runtime/sessions/<session_id>/`。
- 审核未通过不得进入后处理。

## 编排 CLI（新增）

- `plan <manifest.json>`：生成标准项目计划。
- `context-pack <manifest.json> <role_id> <stage>`：生成角色上下文包。
- `context-pack ... --render-prompt-sections`：额外输出提示词分段渲染结果。
- `task-update <manifest.json> <task_id> <status> <actor_role>`：按状态机推进任务。
- `context-pack` 默认会阻断角色非法阶段请求；需要显式放行时使用 `--allow-disallowed-stage`。
- 三个命令支持 `--session-id`，并会把状态与事件日志落盘到 `runtime/projects/<project_id>/` 与 `runtime/sessions/<session_id>/`。
- `pipeline-run <manifest.json> --render-manim`：在 Manim Worker 生成代码后立即渲染视频并抽取关键帧，作为审核 Agent 的视频级证据来源；渲染、抽帧、黑屏、低对比、低细节、跨帧几乎无运动、缺少解释性动画信号、公式缺少视觉 companion 或跨镜头变量颜色冲突会强制阻塞审核。
- `quality-audit <manifest.json>`：不调用 LLM，读取已有 Manim 代码与渲染证据，复用确定性审核规则生成 `outputs/<project_id>/quality-audit.json` 与人工审片用的 `outputs/<project_id>/quality-summary.md`。
- `assemble-video <manifest.json>`：读取长期上下文中的 Manim 渲染证据，按清单镜头顺序拼接分段视频，生成 `outputs/<project_id>/<project_id>-final.mp4`；可用 `--output-name` 指定文件名。
- `build-subtitles <manifest.json>`：读取旁白脚本和分段视频真实时长，生成 `outputs/<project_id>/<project_id>.srt`。
- `mux-subtitles <manifest.json>`：把 SRT 作为软字幕轨封装进成片，生成 `outputs/<project_id>/<project_id>-final-subtitled.mp4`。
- `burn-subtitles <manifest.json>`：把 SRT 烧录进画面，生成平台通用的 `outputs/<project_id>/<project_id>-final-burned.mp4`。
- `build-voiceover <manifest.json>`：使用 Windows SAPI 根据旁白脚本生成离线 WAV 旁白。
- `mux-voiceover <manifest.json>`：把旁白合成进烧录字幕版视频；如果旁白和视频时长不一致，会按旁白长度缩放视频节奏。

## Web API 骨架（新增）

- 新增 `backend/` FastAPI 骨架，直接复用编排内核：
  - `POST /api/projects/plan`
  - `GET /api/projects/{project_id}/runtime`
  - `POST /api/projects/tasks`
  - `POST /api/projects/tasks/update`
  - `POST /api/projects/context-pack`
- 启动示例（安装 `api` 依赖后）：

```powershell
& 'C:\Users\84025\AppData\Local\Programs\Python\Python312\python.exe' -m pip install -e ".[api]"
& 'C:\Users\84025\AppData\Local\Programs\Python\Python312\python.exe' -m uvicorn backend.main:app --reload
```

## 文档入口

- [docs/README.md](/C:/Users/84025/Desktop/ManiMind/docs/README.md)
- [docs/通用项目架构模板.md](/C:/Users/84025/Desktop/ManiMind/docs/通用项目架构模板.md)
- [docs/上下文与状态设计.md](/C:/Users/84025/Desktop/ManiMind/docs/上下文与状态设计.md)
- [docs/第三方整合.md](/C:/Users/84025/Desktop/ManiMind/docs/第三方整合.md)
- [docs/ClaudeCode抽取清单.md](/C:/Users/84025/Desktop/ManiMind/docs/ClaudeCode抽取清单.md)
