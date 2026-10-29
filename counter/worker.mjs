const baseHeaders = {
  'Content-Type': 'application/json; charset=utf-8',
  'Cache-Control': 'private, no-store',
  'X-Content-Type-Options': 'nosniff',
  Vary: 'Origin',
};

function reply(body, status, cors = {}, extra = {}) {
  return new Response(JSON.stringify(body), {status, headers: {...baseHeaders, ...cors, ...extra}});
}

export async function handleSiteViews(request, env) {
  if (new URL(request.url).pathname !== '/api/site-views') return reply({error: 'not_found'}, 404);
  const origins = new Set((env.ALLOWED_ORIGINS || '').split(',').map(x => x.trim()).filter(Boolean));
  const origin = request.headers.get('Origin');
  const allowed = origin && origins.has(origin);
  const cors = allowed ? {'Access-Control-Allow-Origin': origin} : {};
  if (origin && !allowed) return reply({error: 'origin_not_allowed'}, 403);
  if (request.method === 'OPTIONS') {
    if (!allowed || !['GET', 'POST'].includes(request.headers.get('Access-Control-Request-Method'))) {
      return reply({error: 'origin_or_method_not_allowed'}, 403);
    }
    return new Response(null, {status: 204, headers: {
      ...baseHeaders, ...cors, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600',
    }});
  }
  if (!['GET', 'POST'].includes(request.method)) {
    return reply({error: 'method_not_allowed'}, 405, cors, {Allow: 'GET, POST, OPTIONS'});
  }
  if (request.method === 'POST' && !allowed) return reply({error: 'origin_required'}, 403);
  if (!env.DB) return reply({error: 'counter_unavailable'}, 503, cors);
  try {
    const row = request.method === 'POST'
      ? await env.DB.prepare(`
          INSERT INTO site_views (id, total, started_at) VALUES ('global', 1, ?)
          ON CONFLICT(id) DO UPDATE SET total = site_views.total + 1
          RETURNING total, started_at
        `).bind(new Date().toISOString()).first()
      : await env.DB.prepare("SELECT total, started_at FROM site_views WHERE id = 'global'").first();
    return reply({total: row?.total ?? 0, startedAt: row?.started_at ?? null}, 200, cors);
  } catch {
    return reply({error: 'counter_unavailable'}, 503, cors);
  }
}

export default {fetch: handleSiteViews};
