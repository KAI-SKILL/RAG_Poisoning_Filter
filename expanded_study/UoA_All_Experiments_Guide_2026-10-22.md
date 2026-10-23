# UoA 全部实验运行与取回指南

更新：2026-10-22。配套包：`Group9_UoA_All_Experiments_2026-10-22.zip`。

本包覆盖三个模型的 Q、E1、E2、E3 全部网格，替代此前只运行 E3 的 GPU 入口。**目前尚未在 UoA GPU 集群执行本包，未取得新的完整 GPU 攻击成功率。** 已完成的是冻结输入、运行代码与隔离测试；真实结果以集群生成、评分和收集器核验后的文件为准。本聊天云端无法进入校园 VPN、解析并连接校园集群，密码与 2FA 由你在自己的终端输入，不需要发到聊天。

## 1. 本次需要运行什么

| 模型键 | 固定模型配置 | 每模型范围 |
| --- | --- | --- |
| `qwen25_3b_gguf` | 原 Qwen2.5-3B-Instruct，固定 GGUF Q4_K_M 权重 | Q、E1、E2、E3 |
| `qwen3_8b` | Qwen3-8B，固定 revision，BF16，关闭 thinking | Q、E1、E2、E3 |
| `llama31_8b` | Llama-3.1-8B-Instruct，固定 revision，BF16 | Q、E1、E2、E3 |

| 范围 | 每模型分析行数 | 说明 |
| --- | ---: | --- |
| Q | 90 | 30 篇文章 × 3 种上下文条件 |
| E1 | 1,800 | 原实验的完整条件与防御设置 |
| E2 | 700 | 原实验的完整条件，包括 matched benign |
| E3 | 176,400 | 扩展攻击网格及对应清洁基线 |
| 合计 | 178,990 | 三模型合计 536,970 行，12 个模型/范围槽位 |

这些是分析映射行数，不是实际大模型调用次数。E2 每模型有 200 行对应 E1 的基线来源，独立来源条件三模型合计 536,370；实际生成按各自范围内的完全相同提示去重，运行文件会记录真实响应数。旧实验的 557 个提示不作为本轮新增生成次数。

默认提交三个独立模型任务，每任务只申请 **1 GPU、4 CPU、32G 内存**。每个任务内部依次跑 `Q → E1 → E2 → E3`，三个模型任务默认用 `afterany` 依赖串行运行，不需要用 8 张卡跑 3B。一个任务失败或暂停后，后续独立模型仍可运行，但失败的范围不会被标为完成。`--parallel` / Windows `-Parallel` 才显式取消该串行依赖。

默认时间 `00:30:00` 来自站点示例，只是申请值；**不代表能跑完，也不代表站点上限或已获配额**。根据管理员说明和排队政策用 `--time HH:MM:SS` 调整。完整网格可能跨多个 allocation 续跑，不能承诺显存、速度或完成时间。

## 2. 先确认校园连接和目录

1. 在自己的电脑连接校园网或大学 VPN。
2. 使用你自己的 UPI 连接可用服务器：

   ```powershell
   ssh 你的UPI@gpu-server-3.example.invalid
   ```

   也可按站点安排选择 站点提供的其他 GPU 主机。第一次连接按正常 SSH 流程核对主机指纹；依学校说明在该终端的认证提示中输入“密码:当前2FA”，不要把真实值放进命令参数或聊天。
3. 项目、环境、模型、缓存、检查点和临时文件都放在 `/data/你的UPI/`。本包的固定解压目标是：

   ```text
   /data/你的UPI/Group9_All_Experiments/
   ```

   不把大量文件放 HOME，也不修改 HOME。该目录和 ZIP 已存在时，Windows 入口会拒绝覆盖或合并；已有实验请按续跑步骤处理。

所有模型运行、安装依赖、编译 CUDA、下载模型及文件哈希收集工作都在 Slurm allocation 内执行。SSH 登录终端只做登录、认证、文件部署、轻量检查和提交。

## 3. Windows：先上传，或一次上传并提交

把新 ZIP 和 `Run_From_Windows.ps1` 下载到电脑。脚本位于包内 `generation/all_experiments/`，也可使用单独提供的副本。需要正常可用的 Windows OpenSSH Client（`ssh`、`scp`）和 PowerShell 5.1 或更新版本。

在 PowerShell 中，先将 UPI、脚本与 ZIP 路径换成自己的实际值。路径含空格时保留引号：

```powershell
.\Run_From_Windows.ps1 -UPI abc123 -Server 3 -ZipPath 'C:\Downloads\Group9_UoA_All_Experiments_2026-10-22.zip'
```

默认只打印计划，不联网、不上传、不提交。首次运行建议先部署：

```powershell
.\Run_From_Windows.ps1 -UPI abc123 -Server 3 -ZipPath 'C:\Downloads\Group9_UoA_All_Experiments_2026-10-22.zip' -UploadOnly
```

它使用正常 `ssh`/`scp` 提示你认证，将新包上传到 `/data/abc123/`，解压出 `Group9_All_Experiments/`，不提交任务。它不会下载或上传你的凭据。

若模型授权、站点环境已经准备好，可从全新目标一次上传并提交：

```powershell
.\Run_From_Windows.ps1 -UPI abc123 -Server 3 -ZipPath 'C:\Downloads\Group9_UoA_All_Experiments_2026-10-22.zip' -Time '04:00:00' -Submit
```

这里的 4 小时也只是示例，请按实际站点政策填写。`-Submit` 会真正提交三个任务；返回 job ID 只表示进入队列。若已经执行过 `-UploadOnly`，不要再次用 `-Submit` 上传到同一目标，直接采用第 5 节 SSH 提交命令。

只有管理员要求时才指定 `-Partition`、`-Account`、`-Qos`；站点说明未给出这些值，脚本保留 Slurm 默认值。不会凭空猜测分区或账户，也不调用付费 API。

## 4. 首次模型授权与站点环境

先 SSH 到所选服务器：

```bash
UPI="$(id -un)"
PROJECT="/data/$UPI/Group9_All_Experiments"
cd "$PROJECT"
```

环境要求为 Python **3.11 或 3.12**、可用的 NVIDIA 驱动/CUDA 编译工具及 C++ 编译工具。原 3B 分支会从固定源码构建 CUDA llama.cpp；8B 分支创建私有环境，使用固定 PyTorch/Transformers 版本。安装与构建由 allocation 内的任务完成，不安装系统包、不使用 sudo。

若站点需要 `module load`，使用管理员给出的真实模块名。可在 `/data/$UPI/` 建立你自己的站点初始化文件，其中只放实际模块和环境选择，例如设置 `GROUP9_PYTHON` 为 Python 3.11/3.12 的可执行文件路径；不要把密码或 token 写入该文件。SSH 手动提交前先 `source` 它。Windows 一次提交可加：

```powershell
-RemoteSetupFile '/data/abc123/group9_site_modules.sh'
```

该文件必须已在服务器上存在；脚本不会猜测或安装站点模块。模块环境随提交传给 allocation，CUDA、GPU 和文件系统的实际检查仍由任务完成。

Llama-3.1 需要你的 Hugging Face 账号已接受模型许可并获准访问。先在自己的浏览器完成 [模型访问申请](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)。认证是轻量登录操作，可在自己的校园终端用已有官方 `hf` CLI 完成：

```bash
export HF_HOME="$PROJECT/runtime_all/hf_home"
export http_proxy='http://squid.auckland.ac.nz:3128'
export https_proxy="$http_proxy"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
export NO_PROXY='localhost,127.0.0.1,::1'
export no_proxy="$NO_PROXY" HF_HUB_DISABLE_XET=1
hf auth login
```

不要把 token 写在 `hf auth login --token ...` 参数中。按交互提示登录，token 保存在你自己的 `/data/` 私有认证目录。若没有 `hf` 命令，任何 CLI 安装也应在 Slurm 内进行；另一种无需安装 CLI 的本地交互方式是：

```bash
mkdir -p "$PROJECT/runtime_all/hf_home"
chmod 700 "$PROJECT/runtime_all/hf_home"
read -r -s -p 'Your authorized HF read token (hidden): ' GROUP9_LOCAL_TOKEN
printf '\n'
if [[ -n "$GROUP9_LOCAL_TOKEN" ]]; then
  (umask 077; printf '%s' "$GROUP9_LOCAL_TOKEN" > "$PROJECT/runtime_all/hf_home/token")
else
  printf 'Empty input: existing token was not changed.\n' >&2
fi
unset GROUP9_LOCAL_TOKEN
```

该段只在你自己的终端接收隐藏输入，不会把 token 加入命令历史或参数。官方 Hub 的默认 token 文件为 `$HF_HOME/token`；若你另设了 `HF_TOKEN_PATH` 或 `HF_TOKEN`，需按自己的认证配置处理。凭据不会包含在结果收集包中。参考：[官方 CLI 登录](https://huggingface.co/docs/huggingface_hub/en/guides/cli)、[官方环境变量](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables)。

任务自动配置代理 `squid.auckland.ac.nz:3128`、localhost 的 `NO_PROXY` 和 `HF_HUB_DISABLE_XET=1`。模型下载仍需要站点代理可用及相应许可，失败会保留日志，不会伪装成已完成。

## 5. SSH 内正式提交

在项目根运行计划，确认三个模型和四个范围都列出：

```bash
cd "$PROJECT"
export GROUP9_UPI="$UPI" GROUP9_PROJECT_ROOT="$PROJECT"
# 若需要，先 source 自己的站点模块初始化文件。
bash generation/all_experiments/submit_all_slurm.sh --time 04:00:00
```

确认资源申请符合站点政策后，通过命令本身明确提交：

```bash
bash generation/all_experiments/submit_all_slurm.sh --time 04:00:00 --submit
```

脚本只做轻量提交检查；pip、编译、模型下载、大文件哈希和生成都在 allocation 内进行。提交记录位于打印出的 `generation/all_experiments/submissions/<时间>/job_ids.tsv`，包含三个 job ID 与依赖关系。若出现拒绝、无权限或未知返回格式，脚本非零退出，保留 `FAILED_OR_UNCERTAIN`，停止后续提交，不会自动重试或取消已排队任务。

查看队列与调度记录：

```bash
squeue -u "$UPI"
sacct -u "$UPI" --format=JobID,JobName,State,ExitCode,Elapsed
```

Slurm 标准输出在项目根的 `group9-suite-<jobid>.out/.err`。每个范围的实际运行、提示、响应和评分位于：

```text
generation/all_runs/<模型键>/<Q|E1|E2|E3>/
generation/all_results/<模型键>/<Q|E1|E2|E3>/
```

`all_runs` 是运行目录；`all_results` 是闭合导出。不要把正在写入的 SQLite 文件单独当成完整结果交付。

## 6. 文件系统与失败后的续跑

`/data` 在这些服务器上的实际文件系统类型尚未验证，不能假定是本地 ext4/xfs。日志会输出 `findmnt` 的观察结果；**现有 live SQLite guard 会拒绝 NFS/Lustre 等不受支持的非本地运行位置**，不会为绕过报错而移除。若被拒绝，请先向管理员确认 `/data/你的UPI/` 内实际可用的节点本地 ext4/xfs 等支持位置，再据诊断调整项目/运行路径；不能把未经确认的 `/data` 路径当成本地盘。不要改放 HOME 或随意 `/tmp`。将具体文件系统诊断带回后才能确定修改方式。

任务在限时前收到 Slurm 信号会请求暂停并尽量形成闭合导出；遇到强制终止或文件系统故障时仍需核验。超时、模型权限缺失、依赖安装失败、CUDA 不匹配和不完整响应都会保留失败/暂停状态，不生成新的“完整 ASR”声明。

排除问题并确认上一批任务均已结束后，可在同一冻结项目下提交续跑：

```bash
bash generation/all_experiments/submit_all_slurm.sh --time 04:00:00 --resume --submit
```

这会创建新的提交记录；同范围使用经过指纹校验的已有响应继续，已完成范围应复用其记录。不要同时启动两批任务写同一模型/范围目录，也不要修改运行输入、模型 revision、评分代码或配置来强行续跑。配置改变应使用独立实验分支。

## 7. 收集真实数据并下载

三个模型任务结束后，通过 **Slurm CPU 任务**运行收集器；不需要额外申请 GPU。先确保项目路径变量仍正确：

```bash
cd "$PROJECT"
export GROUP9_PROJECT_ROOT="$PROJECT"
sbatch --job-name=group9-collect --cpus-per-task=1 --mem=4G --time=00:30:00 \
  --chdir="$PROJECT" --export=ALL \
  --wrap='python3 generation/all_experiments/collect_all_results.py --project-root "$GROUP9_PROJECT_ROOT" --package'
```

若默认 `python3` 不是可用的 Python 3，请先按站点模块选择实际解释器。收集器只有标准库，不加载模型、不联网；它验证每个闭合导出的文件清单、输入/配置和响应完整性。校验过程仍在 allocation 内进行。

输出位于 `generation/all_collected/`：

- `collection_inventory.json` 和 `.csv`：逐一列出 12 个槽位的验证状态。
- 全部通过时，状态才是 **`ALL_COMPLETE`**，结果包为 `Group9_All_Experiments_COMPLETE_Results.zip`。
- 任意缺失、损坏或未完成时，状态保持 **`INCOMPLETE`**，默认退出码 3；可生成 `Group9_All_Experiments_INCOMPLETE_Checkpoints.zip`，其中只收录通过闭合封包校验的现有导出。它不是完整实验结果。

在 Windows PowerShell 中下载收集输出：

```powershell
scp -r abc123@gpu-server-3.example.invalid:/data/abc123/Group9_All_Experiments/generation/all_collected 'C:\Downloads\Group9_All_Collected'
```

把下载的 inventory 和对应结果/检查点 ZIP 发回，即可据实际生成响应更新分析与 report。不要下载或发送 `runtime_all/`、模型缓存、私有环境、`hf_home/token` 等认证内容。已保存的历史 CPU 结果与旧 E3 快照保持独立，不补成新 GPU 数据。

## 8. 本包已验证与未验证的边界

Linux shell 入口已通过 12 项隔离 mock 检查，覆盖默认不提交、三个任务依赖、空格路径、Slurm spool 路径、无 allocation 拒绝、失败和未知 job ID，以及 `/data`/代理环境。输入与模型 revision 采用冻结注册表，生成和评分分别记录来源。

本机没有可用 Windows PowerShell、UoA GPU 或校园网络连接；Windows 上传脚本仅完成静态检查，未执行 Windows SSH/SCP、Slurm 真实提交、集群 CUDA 编译或 GPU 推理。因此它是一份可审阅的运行入口，不是已跑完的 GPU 实验报告。站点模块、代理访问、Llama 授权、实际文件系统与资源申请是否成功，以你的集群日志为准。
