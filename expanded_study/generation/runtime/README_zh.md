# 生成运行环境：CPU与可选CUDA复建

这里提供固定版本的运行时构建和模型下载代码。`native_build_manifest.json`是**已经构建并检查的CPU运行时凭证**，不代表GPU实验。CUDA分支只完成语法、参数和离线计划检查；本机没有构建CUDA运行时，也没有运行GPU生成。当前CPU实验的执行状态以`generation/run/`为准。

运行时固定到`llama-cpp-python v0.3.36`使用的`llama.cpp`提交`0c1e57098bba43ac29e6e3b677cdceebdd22334f`。源压缩包SHA-256见`source_identity.json`。生成模型固定到Qwen2.5-3B-Instruct-GGUF的原提交；Q4_K_M权重为2,104,932,768字节，下载后必须匹配`model_manifest.json`中的SHA-256。下载器同时获取原README和LICENSE，并且不加载模型。

## Linux CPU

在解压后的项目根目录运行：

```bash
python generation/runtime/build_native_server.py --workdir /tmp/group9_cpu --jobs 4
python generation/runtime/download_model.py --model-dir /tmp/group9_models
```

CPU构建参数保持原配置。CMake和Ninja安装在指定工作目录，不要求改动现有Python环境；系统仍须有C/C++编译器。完整运行时包括`build/bin/llama-server`及同目录共享库，不能只复制很小的启动程序。

## Linux CUDA／Google Colab等笔记本环境

先在环境中选择实际提供的GPU，并检查`nvidia-smi`和`nvcc --version`。GPU、驱动、CUDA工具链及编译器须相容。此说明不保证某个平台提供免费GPU、特定显存或完成时长。

以下命令适用于具有CUDA工具链的Linux环境；Colab代码单元调用命令时在行首加`!`：

```bash
python generation/runtime/build_native_server.py --cuda --cuda-architectures native --workdir /content/group9_cuda --jobs 2
python generation/runtime/download_model.py --model-dir /content/group9_models
```

`--cuda`启用`GGML_CUDA=ON`，其余CPU构建参数保留。`--cuda-architectures native`针对构建时可见的GPU；默认`auto`不覆盖固定源码的架构选择逻辑。需要显式架构列表时使用CMake格式并加引号，例如`--cuda-architectures "75;86"`，应根据实际GPU与工具链选择，不能凭此例假定硬件型号。

**构建CUDA后还需要通过支持GPU层数参数的生成launcher启动新实验。** 仅编译CUDA运行时不会自动证明模型已使用GPU。CPU运行的v1 launcher和已有结果必须保留；GPU运行应使用单独输出目录和新的配置/运行时哈希，不能把CPU缓存与GPU结果直接混入同一实验。层数、槽位、上下文与批大小由后续launcher配置及实测决定，此辅助脚本不修改这些参数。

## 仅检查命令

以下命令不联网、不安装依赖、不构建、不下载模型，也不新建工作目录：

```bash
python generation/runtime/build_native_server.py --cuda --cuda-architectures native --workdir /tmp/group9_check --dry-run
python generation/runtime/download_model.py --model-dir /tmp/group9_check_models --dry-run
```

`--help`列出全部参数。已验证的离线检查见`runtime_helper_validation.json`；它不是GPU吞吐或生成结果。下载器会复用校验通过的完整文件，保留中断的`.partial`以便续传；完整文件哈希错误时拒绝覆盖，部分文件损坏时可用`--restart`重新下载。

源归属：<https://github.com/abetlen/llama-cpp-python/tree/v0.3.36>；<https://github.com/ggml-org/llama.cpp/tree/0c1e57098bba43ac29e6e3b677cdceebdd22334f>。模型原始许可证随下载保留。
