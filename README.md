# Wentao Chen — GitHub Pages 学术网站

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

GitHub Pages 不运行数据库后台。`counter/` 提供独立 Cloudflare Worker + D1 适配器，保留跨设备累计 PV、原子递增和只保存总数/开始时间的设计。它尚需部署到你自己控制的账号，再把真实 HTTPS 地址填入 `content/settings.json` 的 `counter.endpoint`。

当前 `endpoint` 留空，网页明确显示 **Not connected**，不会请求旧 Sites 接口，不会虚构浏览量。详见 [统计后台部署](counter/README_中文.md)。旧站真实计数快照在 `migration/counter-snapshot.json`；正式切换前必须刷新快照，不能把它当作实时总量。

## 本地重建与检查

Python 3.9 及以上即可生成网页，零第三方 Python 依赖。Node.js 22.13+ 用于统计适配器测试，Actions 中使用 Node 24。

```sh
python3 build.py
python3 scripts/validate.py --report test-report.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/counter.test.mjs tests/visits.test.mjs
```

`SITE_URL` 环境变量可覆盖正式域名，用于 GitHub 默认地址或仓库子路径的测试。Actions 根据 Pages 实际地址自动设置它；正式自定义域名生效后会随 Pages 地址更新。生成的站点地图、robots 和 canonical 使用同一基址。

## 验证范围

本地检查报告不代表已部署到 GitHub，也不能代表中国大陆各网络下均可访问。线上发布、Actions 权限、DNS、证书、统计接口和实际国内访问需要在目标账号连接后分别验证。外部论文和基金网站保留原链接；站内校验不声称验证了所有外部服务。
