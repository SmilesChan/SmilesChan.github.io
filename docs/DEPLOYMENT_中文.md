# GitHub Pages 部署与 wentaochen.cn 切换

## 1. 创建网站仓库

在你自己的 GitHub 账号中创建专用公开仓库。建议名称为 `<GitHub用户名>.github.io`。将本项目源码推送到 `main`，保留 `.github/workflows/pages.yml`。不要上传 ZIP 本身，不要上传旧 Sites 的 `.git`、`.openai`、环境变量或依赖文件夹。

本项目的 `static/` 保存图片、样式、脚本和本地辅助页面；`content/` 保存可编辑内容；`build.py` 自动生成 `public/`。Pages 发布的仅为 `public/`。

## 2. 启用自动发布

仓库 Settings → Pages → Build and deployment → Source 选择 **GitHub Actions**。在 Actions 中打开 “Build, check and publish academic website”，必要时点击 Run workflow。

工作流会生成全部网页，检查站内链接/图片/片段锚点，测试仅修改内容的更新流程，以及统计接口适配器。全部通过后才部署。若失败，在 Actions 查看具体错误，修正源内容后重新提交。

默认使用 `content/settings.json` 中的 HTTPS `site_url` 生成 sitemap 和 canonical，当前正式地址为 `https://wentaochen.cn`。测试其他发布地址时，可设置仓库变量 `SITE_URL` 临时覆盖；测试结束后清除覆盖，或改为正式 HTTPS 地址。Pages 的 Enforce HTTPS 开关单独控制请求跳转。

## 3. 在默认地址完成实测

测试首页和各栏目 View all，打开论文/项目/活动详情；检查完整图片、基金/Event 外链、搜索和筛选；使用手机查看导航和 Gallery 横向滚动。让中国大陆不同网络的访客测试真实访问情况。浏览次数接口另按 `counter/README_中文.md` 部署和测试。

连接账号前无法执行 GitHub 线上发布及 DNS/HTTPS 验证；本地报告只覆盖生成文件和本地功能。

## 4. 绑定并验证域名

先在 GitHub 个人设置 Settings → Pages → Add a domain 添加 `wentaochen.cn`。GitHub 将生成账户专属 TXT 验证记录；按实际说明在阿里云添加并完成验证。TXT 值不能预先猜测。

然后在网站仓库 Settings → Pages → Custom domain 中填写 `wentaochen.cn` 并保存。使用自定义 Actions 时，仅放置 `CNAME` 文件不能代替这里的绑定操作。

## 5. 正式切换阿里云 DNS

新站通过测试并已在 Pages 绑定域名后，再将根域名 `@` 的旧 Sites A 记录替换为以下四条。不要把新旧平台的 A 记录混在一起。

| 主机记录 | 类型 | 新记录值 |
|---|---|---|
| `@` | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |

若启用 IPv6，按 GitHub 当前官方文档添加全部四条对应 AAAA，不要填写其他平台地址。如果需要同时支持 www，可增加 `www` 的 CNAME，目标为实际 `<GitHub用户名>.github.io`，不带协议或仓库名。www 是额外入口，`wentaochen.cn` 本身即可作为正式地址。

旧 Sites 的 A 值曾为 `162.159.143.30` 和 `172.66.3.26`。先保留原配置截图，必要时可以恢复旧站；旧站的平台地区限制仍可能存在。旧 TXT 验证记录与网站路由分开，不影响根域名 A 的切换，不必同时删除。

等待解析与证书完成后，在 Pages 开启 Enforce HTTPS，并验证 `https://wentaochen.cn` 的页面、内链、证书和统计。域名及 HTTPS 迁移不是靠本地构建就能完成的。

## 官方依据

- GitHub Docs, *Using custom workflows with GitHub Pages*：https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- GitHub Docs, *Managing a custom domain for your GitHub Pages site*：https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
- GitHub Docs, *Verifying your custom domain for GitHub Pages*：https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages
- GitHub Docs, *Securing your GitHub Pages site with HTTPS*：https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https

配置依据于 2026-10-29 核对的官方说明；执行切换前应复核 GitHub 界面的实际记录。
