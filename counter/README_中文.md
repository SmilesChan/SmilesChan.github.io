# 独立浏览次数后台

此目录是可测试、可部署的 Worker + D1 适配器，不依赖 ChatGPT Sites。GitHub Pages 仅负责网页。需要你自己控制的 Cloudflare 账号与 D1 数据库；本迁移尚未代替你创建这些资源。

Cloudflare Workers 和 D1 有免费额度，是否适用及用量上限以你账号当前官方计划为准。使用自有后台不代表任意地区都保证可达，正式启用前仍需实际网络测试。

## 一次性配置

1. 在你自己的 Cloudflare 账号创建名为 `wentaochen-views` 的 D1 数据库。
2. 复制 `wrangler.example.jsonc` 为 `wrangler.local.jsonc`，填入真实 `database_id`。在 `ALLOWED_ORIGINS` 中按需加入实际 `https://<用户名>.github.io`；只填 Origin，不包含仓库路径或结尾 `/`。保留正式域名的 Origin。
3. 使用当前官方 Wrangler CLI 在你自己的终端登录 Cloudflare，不要把 API Token、密码或登录验证码发到聊天或提交到仓库。
4. 在此目录执行数据库迁移：

```sh
wrangler d1 migrations apply wentaochen-views --remote --config wrangler.local.jsonc
```

5. 切换前从旧站读取最新真实总量并更新 `migration/counter-snapshot.json`。在项目根目录生成一次性导入 SQL：

```sh
python3 scripts/counter-seed.py migration/counter-snapshot.json > counter/seed.local.sql
```

6. 在本目录首次导入并部署：

```sh
wrangler d1 execute wentaochen-views --remote --config wrangler.local.jsonc --file seed.local.sql
wrangler deploy --config wrangler.local.jsonc
```

导入仅在计数不存在时写入，重复执行不会重置已累计的值。新后台开始接收正式访问后，不应反复导入旧站快照；如果迁移期间旧站仍有访问，应在交接时明确计数截至时间，避免声称包含了未经同步的增量。

7. 将真实接口 `https://<你的Worker地址>/api/site-views` 写入 `content/settings.json` → `counter.endpoint` 并提交。不得填写示例域名。自动发布后页脚开始读取真实共享总量。

## 验证

- GET `/api/site-views`：读取总量，不增加。
- 使用允许的网站 Origin 发起一次 POST：仅增加一次，页面刷新再次增加。
- 换设备访问应读取共享总数；重新部署不重置。
- 未配置 Origin、未允许的 Origin 和不支持的方法不能写入。
- 没有数据库或存储失败返回 503，前端显示 Unavailable，不显示模拟数字。

程序只存储一个累计数和开始时间，不自行保存访客 IP 或逐次访问记录。托管服务本身的基础网络处理与平台政策独立于此。Origin 白名单用于限制浏览器来源，不是防机器人计数系统。

本地测试：`node --test tests/counter.test.mjs tests/visits.test.mjs`，在项目根目录运行，需要 Node.js 22.13+。

## 官方文档

- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/workers/wrangler/configuration/
- https://developers.cloudflare.com/d1/worker-api/d1-database/
