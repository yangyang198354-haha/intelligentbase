---
name: ib-prod-deploy
description: intelligentbase 生产环境部署手册。当需要部署 intelligentbase 到生产目标机 192.168.31.133、SSH 连接生产、重启或排查 ib-web / ib-worker / ib-embed / qdrant / nginx、构建并发布前端、核验线上实际跑的是哪版代码、或排查生产部署问题时使用。含访问方式、服务拓扑、部署流程、重启口径、验收判据与已知坑。本文件不含任何口令或密钥。
---

# intelligentbase 生产环境部署手册

> **信息快照：2026-10-07。** 带 ⚠️ 的项为易变 / 用前需实测复核。
> **本文件不含任何口令、密钥、token。** SSH 走密钥认证（§2）；服务凭据一律经
> `/etc/intelligentbase/*.env` 的 `EnvironmentFile` 注入，**任何情况下不得读取回显**（§9）。
> 本手册给"怎么做"，但每次部署仍须先实测"当前是什么样"（生产工作树状态、服务状态、本次拉取涉及的文件）。

## 何时用本 skill

部署 intelligentbase 到生产目标机、SSH 连生产、重启 systemd 服务、构建前端、
核验线上代码版本、排查生产部署问题时。

---

## 1. 生产环境基本信息

| 项 | 值 |
|---|---|
| 目标机 | `192.168.31.133`，Ubuntu 26.04 LTS，x86_64 |
| SSH 用户名 | `yangyang198354`（⚠️ **不是** `yangyang`，用 `yangyang` 会 `Access denied`）|
| SSH 认证 | 密钥 `~/.ssh/ib_prod_ed25519`（公钥已装入目标机 `authorized_keys`，`BatchMode=yes` 免密已验证）|
| sudo | **三个 ib-\* 服务已免密重启**（2026-10-07 起，见 §4）；sudo 的其他动作（含 `daemon-reload`、读写 env）**仍需口令** |
| 部署目录 | `/opt/intelligentbase`（属主 `yangyang198354`，`git pull` 免 sudo）|
| venv | `/opt/intelligentbase/venv`（服务解释器）|
| 配置 | `/etc/intelligentbase/{ib-web,ib-worker,ib-embed}.env`，0600，属主对齐各服务用户 |
| 状态目录 | `/var/lib/intelligentbase`（`drwxrws--- ib-web:ib`，setgid，**动它必须 sudo**）|
| Web root | `/var/www/intelligentbase/`（属主 `yangyang198354`，**部署静态产物不需要 sudo**）|
| 硬件 | Intel i7-3770S 4C/8T @3.1GHz；内存 11GiB；GPU GTX 960（Maxwell 太老，现代 PyTorch/onnxruntime 不支持 → **按 CPU-only 部署**）；磁盘 78G 可用 |
| 主机指纹 | `ssh-ed25519 SHA256:BwIe6k9QhLUWCPPyrOykjSDtrWn+EgtesTllQjUd2eY` |

**部署纪律**（沿用 FreeArk，硬约束）：禁 Docker / 任何容器化；物理机直部署；
代码交付**仅** `git pull origin main`，**禁 scp / pscp / rsync**。

---

## 2. SSH 接入配方

### 2.1 中文用户名坑（本机特有）

本机 Windows 用户名是中文"胖子熊"，Git Bash 的 OpenSSH 解析不了 `~`，会报
`Could not create directory '/c/Users/\305\326...'`。同理**无法写入 known_hosts**。

两个规避手段叠加使用：

1. `-o UserKnownHostsFile=/tmp/ib_kh` —— 把 known_hosts 指到 ASCII 路径
   （否则每次报 known_hosts 写失败，不致命但很吵）。
2. 若要走 `~/.ssh/xxx` 形式的 key 路径且 Bash 解析失败，用 ASCII junction
   `C:\fa-home` → `C:\Users\胖子熊`（`New-Item -ItemType Junction`），然后写 `/c/fa-home/.ssh/...`。

### 2.2 标准连接命令（Bash 工具下）

```bash
ssh -i ~/.ssh/ib_prod_ed25519 \
    -o UserKnownHostsFile=/tmp/ib_kh \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    yangyang198354@192.168.31.133 '<远程命令>'
```

- `BatchMode=yes` 确保**绝不回落到口令交互**——失败就明确失败，不挂住。
- ⚠️ 历史遗留：早期记忆里出现过密钥名 `ib_deploy_key`（2026-09-26）。当前权威是
  `ib_prod_ed25519`（2026-10-05 验证）。若前者不存在，不要以为是环境坏了。

### 2.3 从 PowerShell 连接（用户终端）

**用户日常终端是 Windows PowerShell**，语法与上面不同，且**不需要** `/tmp/ib_kh` 那套规避
——中文路径问题只发生在 Git Bash 的 MSYS 路径解析；Windows 原生 `ssh.exe` 能正常处理
`$env:USERPROFILE`。

```powershell
ssh -i "$env:USERPROFILE\.ssh\ib_prod_ed25519" -o StrictHostKeyChecking=accept-new `
    yangyang198354@192.168.31.133 "whoami; hostname; command -v systemctl"
```

要点：
- PowerShell 里多行续行是反引号 `` ` ``，**不是** `\`。
- 整条单引号字符串 `'...'` 内的内容原样传给远程，**但 `$` 在双引号里会被 PowerShell 先展开**；
  写远程命令时若含 shell 变量，用单引号包住，或用 `` `$ `` 转义。
- 需要 sudo 输口令时**必须加 `-t`**（分配 TTY），否则 sudo 会去读 stdin。
- Bash 工具（代理自己）仍走 §2.2 的 Git Bash 配方。

---

## 3. 服务拓扑

```
浏览器 --HTTP--> nginx (server_name 192.168.31.133, root /var/www/intelligentbase/)
                   │
                   ├── 静态：/var/www/intelligentbase（前端构建产物，nginx 直读磁盘）
                   └── /api/ --> ib-web (127.0.0.1:18080, Waitress, threads=8)
                                   │
                                   ├── ib-embed  (127.0.0.1:8100, bge-m3 常驻 embedding)
                                   └── qdrant    (127.0.0.1:6333, 向量库)
                                 ib-worker（入库队列 + 重建推进，无端口）
```

| 服务 | 用户 | 端口 | 内存上限 | 重启方式 |
|---|---|---|---|---|
| `ib-web` | `ib-web` | 127.0.0.1:18080（Waitress，threads=8）| 1024M | 需 sudo |
| `ib-worker` | `ib-worker` | 无 | 2048M，`CPUQuota=200%` | 需 sudo |
| `ib-embed` | `ib-embed` | 127.0.0.1:8100 | 2560M | 需 sudo |
| `qdrant` | `qdrant` | 127.0.0.1:6333 | — | 需 sudo |
| `nginx` | root | 80 | — | 需 sudo |

**全部只监听回环**（除 nginx）。ib-embed 与 qdrant 的端口**无鉴权**，不得对外暴露。

单元文件真源：`src/deploy/systemd/*.service`（**交付物，不由代理安装到目标机**）。
磁盘上的 `/etc/systemd/system/ib-{web,worker}.service` 停在 2026-09-26 10:12，与仓库
曾不一致——见 §7.2 的 pending `daemon-reload` 说明。

---

## 4. 免密重启配置（**2026-10-07 已安装并验证通过**）

> **现状：已生效。** 代理现在可以直接 `sudo -n systemctl restart ib-web/ib-worker/ib-embed`。
> 下面 §4.1–4.3 保留为**记录与重建指南**（换机器、误删、需要加放行项时照做）。
> ⚠️ **不要重复安装**：先 `ls -l /etc/sudoers.d/ib-restart` 确认是否已存在。

**背景**：基础镜像下 `sudo` 需要交互式口令，而 `printf '<口令>' | sudo -S` 这类写法
会把明文口令带进命令行、被凭据泄漏防护拦下。**所以不给通配符、不给 shell、不给全身 sudo，
只精确放行三个 `restart`。**

### 4.1 放行内容（真源）

写入 `/etc/sudoers.d/ib-restart`（0440，root:root）：

```
# intelligentbase: 免密重启 ib-* 服务（由 .claude/skills/ib-prod-deploy 记录）
yangyang198354 ALL=(root) NOPASSWD: /usr/bin/systemctl restart ib-web, \
                                    /usr/bin/systemctl restart ib-worker, \
                                    /usr/bin/systemctl restart ib-embed
```

要点：
- `systemctl` 路径以目标机实际为准，安装前用 `command -v systemctl` 确认。
- **不要**写成 `/usr/bin/systemctl restart *` —— sudoers 的通配符 `*` 会匹配 `/`，
  等于放行任意单元、任意动作。
- **不包含** `daemon-reload`。要清 §7.2 那条 pending 警告需要它，但那会影响全系统所有单元，
  刻意留在放行之外，需要时由用户手动跑。

### 4.2 安装步骤（**用户在 PowerShell 终端执行**，需输一次口令）

在放行生效前，此步**必须由用户执行**——代理拿不到交互式口令。

**前置核对**（确认 `systemctl` 路径与现有 sudoers.d 内容）：

```powershell
ssh -i "$env:USERPROFILE\.ssh\ib_prod_ed25519" -o StrictHostKeyChecking=accept-new `
    yangyang198354@192.168.31.133 "command -v systemctl; echo ---; ls -l /etc/sudoers.d/"
```

**安装**：

> ⚠️ **2026-10-07 实测：不要试图把整条远程命令作为 `ssh` 参数从 PowerShell 传入。**
> PowerShell 5.1 会把含内嵌 `"` 的原生参数重新解析后再交给 `ssh.exe`，命令被改写 ——
> 表现为 `sudo` 根本没执行、无口令提示、规则未落盘（输出里还会多出 `printf "%s\n"`
> 被拆坏残留的 `n`）。**改用「先开交互式会话、再在远端粘贴」的方式，彻底绕开引号问题。**

**① 开交互式会话**（**不带**远程命令）：

```powershell
ssh -i "$env:USERPROFILE\.ssh\ib_prod_ed25519" -o StrictHostKeyChecking=accept-new yangyang198354@192.168.31.133
```

**② 在远端 bash 提示符下粘贴**（这里已是目标机的 bash，heredoc 不受 PowerShell 影响）：

```bash
cat > /tmp/ib-restart.sudoers <<'EOF'
# intelligentbase: 免密重启 ib-* 服务
yangyang198354 ALL=(root) NOPASSWD: /usr/bin/systemctl restart ib-web, /usr/bin/systemctl restart ib-worker, /usr/bin/systemctl restart ib-embed
EOF
sudo visudo -cf /tmp/ib-restart.sudoers
```

**③ 看到 `parsed OK` 之后再落盘**（校验不通过就不要执行这步）：

```bash
sudo install -m 0440 -o root -g root /tmp/ib-restart.sudoers /etc/sudoers.d/ib-restart \
  && rm -f /tmp/ib-restart.sudoers && ls -l /etc/sudoers.d/ib-restart
```

**④ 断开**：`exit`

- **先写 `/tmp` 临时文件、`visudo -cf` 校验通过才 `install` 落盘**：sudoers.d 里一份
  语法错的文件会让**整个 sudo 失效**，必须校验在前。
- 若 §4.2 ① 的 `command -v systemctl` 输出的不是 `/usr/bin/systemctl`，
  把 ② 和 ③ 里的路径一起改掉。
- `/etc/sudoers.d/` 下的文件名**不得含 `.`、不得以 `~` 结尾**（`ib-restart` 合规）。

### 4.3 验证

**关键**：`sudo -n true` **不是**有效判据——放行范围只有 `systemctl restart ib-*`，
不含 `true`，所以即使装对了它也会失败。同理 `sudo -n -l` 在本机需要二次认证，也不可靠。

唯一确凿的验证是**真跑一条放行内的命令**（就是代理部署时会跑的那条）：

```powershell
ssh -i "$env:USERPROFILE\.ssh\ib_prod_ed25519" -o StrictHostKeyChecking=accept-new `
    yangyang198354@192.168.31.133 "sudo -n systemctl restart ib-web && sleep 8 && systemctl is-active ib-web ib-worker ib-embed"
```

- 放行**未生效**：立刻返回 `sudo: a password is required`，**什么都不会发生**，无副作用。
- 放行**已生效**：`ib-web` 重启一次，约 5–8 秒，输出三个 `active`。
  ⚠️ 代价：前端聊天会话是**内存态**，本次重启会丢掉进行中的会话；没有并发用户时无影响。

### 4.4 生效后

代理即可自行重启（**不含** `daemon-reload`）：

```bash
ssh ... 'sudo -n systemctl restart ib-web && sleep 6 && systemctl is-active ib-web ib-worker ib-embed'
```

若 §4.1 未安装，**纯前端改动根本不需要重启**（nginx 直读磁盘），只有后端 Python 改了才要找用户。

---

## 5. 标准部署流程

> 前置：本地改动已 commit 且 **push 到 `origin/main`**，否则目标机 `git pull` 拉不到。

### 5.1 后端（Python）改动

```bash
# 1) 拉取（目标机，免 sudo）
ssh ... 'cd /opt/intelligentbase && git log --oneline -1 && git pull origin main && git log --oneline -1'

# 2) 重启（§4 生效后；否则交给用户）
ssh ... 'sudo -n systemctl restart ib-web'      # 仅 web 改动
ssh ... 'sudo -n systemctl restart ib-worker'   # worker 改动
# 依赖变化时还需装依赖：/opt/intelligentbase/venv/bin/pip install -r <req>（需 sudo 或属主身份）
```

### 5.2 前端（纯静态）改动 —— **不需要 sudo、不需要重启**

web root `/var/www/intelligentbase/` 属主就是 `yangyang198354`。

```bash
ssh ... 'cd /opt/intelligentbase && git pull origin main && \
         cd src/frontend && npm run build && \
         rm -rf /var/www/intelligentbase/assets && \
         cp -r dist/assets /var/www/intelligentbase/ && \
         cp dist/index.html /var/www/intelligentbase/'
```

生产机有 node v22 / npm 9，`node_modules` 已就位（依赖没变就不必 `npm install`）。
前端是纯静态文件，nginx 直读磁盘，**硬刷新即生效**：
`index.html` 为 `no-store`，`assets/*` 为 immutable 30d 且带新 hash 自动加载。

### 5.3 配置类改动（`/etc/intelligentbase/*.env`）

- 属主是各服务用户、0600 —— `yangyang198354` **读不了也写不了**，必须 sudo。
- 改完必须重启对应服务才生效（ADR-32：**生效 = 保存 + 服务重启重装配**）。
- **不要把密钥值回显到终端或写进任何入库文件**（§9）。

---

## 6. 什么改动重启什么

| 改动 | 重启 |
|---|---|
| 前端 `src/frontend/**` | **不重启**，重新 build + 拷 `/var/www/` 即可 |
| `ibweb/**`（Web 路径）| `ib-web` |
| `ibweb/worker.py` / 入库链路 | `ib-worker` |
| `ib-embed` 服务代码 / 模型配置 | `ib-embed` |
| `/etc/intelligentbase/ib-web.env` | `ib-web` |
| `/etc/intelligentbase/ib-worker.env` | `ib-worker` |
| `src/deploy/systemd/*.service` | 需 `install` 到 `/etc/systemd/system/` + `daemon-reload` + restart（**由用户执行**）|
| `src/deploy/nginx/*` | `nginx -t && systemctl reload nginx`（reload 不是 restart）|
| 数据库迁移 `src/deploy/migrations/*.sql` | 台账 schema 由 `ib-web.service` 的 `ExecStartPre` 幂等建（`IF NOT EXISTS`），随 `ib-web` 重启自动完成 |

**⚠️ 只加在对应服务**：`ib-worker` 是纯入库/重建 worker，不读定义文档也不读提示词
（`ibweb/worker.py` 无相关引用），`ib-embed.env` 更无关。往错的文件里加键不会报错，只是静默无效。

---

## 7. 部署后验收判据

### 7.1 ⚠️ `.pyc` 是陷阱，不能用来判断线上跑的是哪版代码

`/opt/intelligentbase` 属主是 `yangyang198354`，服务 `User=ib-web` **不在该属主的组**里 →
ib-web **写不进 `__pycache__`** → Python 只能内存编译 → `.pyc` 长期停留在旧版本。
实测过：`.pyc` 里搜不到新符号，**但线上跑的确实是新代码**。

**正确判据**（两条同时成立即可断言"进程执行的是当前源码"）：

1. `git -C /opt/intelligentbase log --oneline -1` = 目标 commit；
2. 该 commit 涉及的每个源文件 `stat -c %y`（随 pull 落到磁盘的时间）**早于**
   `systemctl show -p ActiveEnterTimestamp ib-web`。

理由：`.pyc` 头里记了源码 mtime，源码更新即失效 → 服务要么重编译（写不进去就内存编译），
**不存在"用了陈旧 .pyc"这一支**。

### 7.2 ⚠️ `daemon-reload` pending 警告是长期存在的，不是本次部署引入的

`systemctl restart` 会打印
`Warning: The unit file ... of ib-web.service changed on disk. Run 'systemctl daemon-reload'`

这是**长期挂起的 pending 变更**（`/etc/systemd/system/ib-{web,worker}.service` mtime 停在
2026-09-26 10:12，无 `.service.d/` drop-in，本仓 deploy 也不写系统单元）。**它不影响重启生效**：
重启仍按 systemd 缓存里的单元定义执行，而 `EnvironmentFile=/etc/intelligentbase/ib-web.env`
照常读取。要用磁盘上的单元定义，需用户跑一次 `sudo systemctl daemon-reload` 再重启。

### 7.3 服务存活与日志

```bash
ssh ... 'systemctl is-active ib-web ib-worker ib-embed'
ssh ... 'journalctl -u ib-web --since "2026-10-07 12:00:00" -p warning --no-pager'
```

用户在 `adm` 组，**`journalctl` 免 sudo 可读**。
⚠️ 查日志**务必用 `--since` 锚定真实启动时刻**（目标机时区 CST，先 `date` 校准；
用未来时间点会让 `grep -c` 假报 0）。

### 7.4 定义文档 / 提示词是否真的从文件态加载

`/etc/intelligentbase/ib-web.env`（0600 `ib-web:ib-web`）中应设：

- `IB_DEFINITION_DOC_PATH=/var/lib/intelligentbase/definition.json`
- `IB_EXPERT_PROMPT_DIR=/var/lib/intelligentbase/prompts`

**唯一可靠判据是这一行日志的存否**：

```
{"outcome": "path_not_configured_using_in_memory_default", "stage": "definition_doc"}
```

它由 `ibweb/composition.py::build_definition_store` **只在 `IB_DEFINITION_DOC_PATH` 为空时**打出。
**没有这一行** = 文件态生效。启动日志出现 `{"outcome": "succeeded", "stage": "startup"}`
即证明定义文档已被 `FileDefinitionDocumentStore.load()` 读取并通过 `admit_two_domains` 校验
（`_assemble` 在 composition.py:586/589 启动期同步执行，非惰性）。

⚠️ 状态目录 `/var/lib/intelligentbase` 是 `drwxrws--- ib-web:ib`，`yangyang198354` **不在 `ib` 组**，
既读不了也写不进 —— **不能靠 `ls` / `grep` 直接核对** `ib-web.env` 或 `definition.json`，
只能走上面的日志判据。若要重置回种子，需删除并重建 `definition.json`（须 sudo）。

---

## 8. 已知坑

1. **SSH 用户名**是 `yangyang198354`，不是 `yangyang`。
2. **中文用户名**致 Git Bash 解析不了 `~` 与 known_hosts —— 见 §2.1。
3. **不加 sudo 的 `systemctl restart`** 报 `Access denied ... requires interactive authentication`，
   不要反复重试，这是权限问题不是环境问题。
4. **`ssh root@192.168.31.133`** 会 `Permission denied (publickey,password)` —— 无 root 密钥登录。
5. **`.pyc` 陷阱** —— 见 §7.1，这是最容易误判"部署没生效"的一条。
6. **前端 HTTP/2 会破坏 SSE**：nginx 配置里刻意**不开 http2**（响应体已发送并计入 access_log，
   但 END_STREAM 不送达浏览器 → 前端"生成中…"卡死）。改 nginx 时不要"顺手"打开。
7. **SSE 反代硬条件**：`proxy_buffering off` / `gzip off` / `proxy_read_timeout 300s`，
   任一被改回默认都会让长问答表现为"问了很久才一次性出结果"。
8. **`ib-web` 的 `--channel-timeout=120`** 必须 > SSE 最长静默期；调小会让长问答中途断开，
   而且**日志里看不到错误**（是正常超时关闭）。
9. **`ib-worker` 单实例**：多实例会双双 OOM，检查只有一份在跑。
10. **`qdrant` 的 `LimitNOFILE=65536`** 不要调回默认，否则 collection 多了会随机 500
    且报错指向 storage 层，很难联想到 limit。

---

## 9. 凭据纪律（硬约束）

- sudo 口令、DeepSeek key、服务 token **一律不落盘、不进 history、不回显**。
- 服务密钥写 `0600` 的 `/etc/intelligentbase/*.env`，属主与各服务用户对齐。
- **不得**用 `printf '<口令>' | sudo -S` —— 明文口令进命令行会被拦下，且本身就不该这么做（§4）。
- 查配置只核对**键是否存在**，不打印值。
- 本仓库是 **PUBLIC**，任何 commit 都是对外发布。部署产物（本文件、`src/deploy/**`）
  **不得**含任何真实凭据；`deploy_templates_have_no_secrets` 自检会扫描 `src/deploy/`。

---

## 10. 维护说明

本手册与以下记忆互为补充，改动生产接入方式时**两者都要更新**：

- `prod-ssh-access` —— SSH 配方、服务拓扑、重启口径
- `prod-state-paths-configured` —— 状态目录权限与生效判据
- `prod-live-code-judgement` —— 线上代码版本判据、`daemon-reload` 警告由来

**每次部署仍须实测当前状态**（生产工作树 HEAD、服务 `is-active`、本次涉及文件），
不要假定手册里的快照仍然成立。
