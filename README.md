# Wentao Chen — GitHub Pages 学术网站

**已发布：** https://wentaochen.cn/  
**自动发布：** 修改 `content/` 并提交到 `main` 后，检查、构建和发布会自动运行。  
**待确认：** Pages 的 Enforce HTTPS 设置，以及 www 入口的证书与跳转。

2026-10-29 首次部署已通过 GitHub Actions 全部检查。252 个公开网页和资源（含 84 个 HTML 页面）的 HTTP 下载与生成文件完全一致；线上搜索、论文筛选、项目链接、Gallery 和 390px 手机布局均已验证。随后已确认阿里云根域名 A 和 www CNAME 指向 GitHub Pages，且 `https://wentaochen.cn/` 返回正确首页。此结果不代表已验证中国大陆各网络访问。详见 `migration/TEST_RESULTS.json`。

这是从 Sites 已发布 v27 整理的独立 GitHub Pages 源码。个人简介、论文、项目、报告、活动、奖项、任职、单位 logo、Gallery 及原有图片保留。原站继续运行，迁移目录不含原平台凭据或运行环境。

## 日常更新

只修改下表中的源文件，提交到 `main`。GitHub Actions 自动生成网页、检查站内链接和内容，再发布到 Pages；不用在电脑上安装 Python，也不用手动上传生成后的 HTML。

| 修改内容 | 源文件 |
|---|---|
| 简介、邮箱、教育、论文/项目/报告/活动列表 | `content/site.json` |
| 某条记录的完整正文 | `content/pages/对应路径/body.html` |
| 奖项、任职、经历、联系方式 | `content/home/对应栏目.html` |
| Gallery 照片顺序及说明 | `content/home/gallery.html` |
| 图片文件 | `static/assets/` |
| 正式域名、统计接口地址 | `content/settings.json` |

记录的 `title` 自动同步到首页、归档列表、详情页标题和搜索。项目基金链接编辑 `fund_details`；活动 Date/Event/Location 编辑 `activity_details`。完整正文仍在对应 `body.html`，新增条目应同时增加记录和正文。首页显示数量与顺序由 `home_limits`、`home_lists` 控制。

`public/` 是自动生成的网页，不作为源文件提交。页脚“编辑内容”和“更新说明”会说明正确维护方式。本地可视化编辑助手仍保留，但它导出的 HTML 不会反向修改源内容，不用于自动发布。

## 首次部署与域名切换

具体步骤见 [部署与域名切换](docs/DEPLOYMENT_中文.md)。需要 GitHub 账号及一个专用于此网站的公开仓库；建议仓库名为 `<你的GitHub用户名>.github.io`，使用 `main` 分支。

仓库 Settings → Pages → Source 选择 **GitHub Actions**。首次推送会运行 `.github/workflows/pages.yml`，后续每次修改内容都会自动检查和发布。拉取请求只做检查，不发布。

先用 GitHub 分配的地址测试首页、内页、搜索、图库和手机布局。确认后再在 Pages 绑定 `wentaochen.cn`，并修改阿里云 DNS。域名仍在阿里云，无需转移注册商。

## 浏览次数统计

已接入公开的自建不蒜子计数服务（soxft/busuanzi）：`https://busuanzi.9420.ltd/api`。无需另购服务器；首页和内页右下角显示同一域名的累计页面访问量 PV，刷新或打开新页面增加一次。这个数字不是独立访客人数。

设置位于 `content/settings.json` 的 `counter`：`provider` 为 `busuanzi`，`endpoint` 为上述 HTTPS 接口。新计数于 **2026-10-29** 接入，包含验证访问；旧 Sites 的历史数字没有自动合并。数据由该第三方服务存储，重新发布本站不会主动清零。接口失败显示 Unavailable；离线显示 Online only。页面只向接口发送公开规范网址，不发送查询参数、Cookie 或持久访客标识；服务端会收到正常网络请求信息。服务项目与 API 文档：https://github.com/soxft/busuanzi/wiki/api 。

若日后需要自有后台，`counter/` 仍保留 Worker + D1 适配器；部署后把 `provider` 改为 `custom` 并填入真实接口。旧站真实计数快照保留在 `migration/counter-snapshot.json`，未加到新服务的数字中。详见 [统计后台部署](counter/README_中文.md)。

## 本地重建与检查

Python 3.9 及以上即可生成网页，零第三方 Python 依赖。Node.js 22.13+ 用于统计适配器测试，Actions 中使用 Node 24。

```sh
python3 build.py
python3 scripts/validate.py --report test-report.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/counter.test.mjs tests/visits.test.mjs
```

正式域名在 `content/settings.json` 的 `site_url` 中维护，当前为 `https://wentaochen.cn`。Actions 默认使用这个内容设置生成站点地图、robots 和 canonical；不会因 Pages 暂未强制 HTTPS 而生成 HTTP 规范地址。特殊部署或 GitHub 默认地址/仓库子路径测试可用 `SITE_URL` 环境变量覆盖，Actions 中对应仓库变量 `SITE_URL`；日常更新无需设置它。

## 验证范围

本地检查报告不代表已部署到 GitHub，也不能代表中国大陆各网络下均可访问。线上发布、Actions 权限、DNS、证书、统计接口和实际国内访问需要在目标账号连接后分别验证。外部论文和基金网站保留原链接；站内校验不声称验证了所有外部服务。
