# 上传到 GitHub

解压后打开 `RAG_Poisoning_Filter` 文件夹，在文件资源管理器地址栏输入 `powershell` 并回车。当前目录应直接看得到 `README.md` 和 `run_project.py`。

先在 GitHub 创建空仓库，不添加初始化文件。在这个文件夹内执行：

```powershell
git init -b main
git config user.name "Research Contributor"
git config user.email "research@example.invalid"
git add .
git diff --cached --name-only
```

确认上传清单后执行：

```powershell
git commit -m "Add research implementation and experiment results"
$repositoryUrl = Read-Host "Paste your new repository HTTPS URL"
git remote add origin $repositoryUrl
git push -u origin main
```

以上提交署名仅设置在当前仓库，不使用真实姓名或联系邮箱。仓库地址在终端输入，不保存在文件里。GitHub 登录按提示完成。压缩包本身留在仓库目录外。

上传无需安装 Python 依赖、下载模型或还原大型数据。查看主实验数值验证与扩展实验运行方法，请阅读 `README.md` 和 `expanded_study/README.md`。
