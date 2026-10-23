# UoA Group9 全范围生成实验运行包

本包替代旧 E3-only GPU 运行包。执行三个固定模型的 Q、E1、E2、E3，共12个独立槽位。当前没有在校园集群执行模型；本包内不含新完整生成结果或新ASR。

先读 `UoA_All_Experiments_Guide_2026-10-22.md`。Windows入口为 `generation/all_experiments/Run_From_Windows.ps1`；用户本人连接VPN并在自己的终端完成SSH认证。所有计算通过Slurm，所有数据、环境、缓存均留在自己的 `/data/<UPI>/`。不要把密码、2FA或HF token发给聊天。

默认1GPU串行三个模型任务，30分钟只是可调整的示例请求。实际文件系统、模块、模型许可、GPU和代理需在集群验证。NFS/Lustre上的SQLite WAL会被拒绝，不可删除guard绕过。

模型运行入口：`generation/all_experiments/submit_all_slurm.sh`（默认计划，`--submit`真实提交，已有记录续跑加`--resume`）。完整结果收集器：`generation/all_experiments/collect_all_results.py --project-root ROOT --package`，请在Slurm CPU allocation运行。只有全部12槽位真实响应、设备、评分和辅助对比均通过才ALL_COMPLETE。

冻结输入每模型178,990分析映射，57,099为源提示逐范围去重的预算，均不是实际调用次数。24个E3模板每个1,200攻击条件，同一1,200问题跨模板复用。E1/E2选择与神经过滤特征沿用冻结历史记录；本生成包不声称重新训练检测器或重新计算神经过滤特征。Q/E1/E2输入构造器的原字节来源另保存在prior_study指定子集，旧回答缓存不作为新生成结果。

新一轮真实CPU检测/检索结果单独交付于 `Group9_Fresh_Sparse_2026-10-22.zip`；报告中已区分历史数据、真实新算与未执行范围。
