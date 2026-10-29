#!/usr/bin/env python3
"""Build GitHub Pages with Python 3.9+ and the standard library only.

Edit content/ and static/assets/. Actions rebuilds and publishes public/.
Generated pages are not the canonical source.
"""
from pathlib import Path
from html.parser import HTMLParser
import html, json, os, posixpath, re, shutil, tempfile, xml.etree.ElementTree as ET
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / 'content'
DIST = ROOT / 'public'
STATIC = ROOT / 'static'
SITE = json.loads((CONTENT / 'site.json').read_text(encoding='utf-8'))
SETTINGS = json.loads((CONTENT / 'settings.json').read_text(encoding='utf-8'))
SITE_BASE = (os.environ.get('SITE_URL') or SETTINGS['site_url']).rstrip('/')
PROFILE = SITE['profile']
RECORDS = SITE['records']
BY_PATH = {r['path']: r for r in RECORDS}
PAGES = SITE['pages']
ASSET_PATHS = {'/' + p.relative_to(STATIC / 'assets/original').as_posix()
               for p in (STATIC / 'assets/original').rglob('*') if p.is_file()}
URLS = {p['path'] for p in PAGES} | {'/', '/site-index/', '/admin/', '/slides/', '/awards/', '/appointment/'}
NAV = [('Home', '/#about'), ('Projects', '/#projects'), ('Publications', '/#featured'),
       ('Conference', '/#talks'), ('Activities', '/#news'), ('Awards', '/#awards'),
       ('Appointment', '/#appointment'), ('Experience', '/#experience'),
       ('Contact', '/#contact'), ('Gallery', '/#gallery')]

def esc(value):
    return html.escape(str(value or ''), quote=True)

def page_file(path):
    return (path.lstrip('/') + 'index.html') if path.endswith('/') else path.lstrip('/')

def link(path, current='/'):
    if not path.startswith('/'):
        return path
    resource, sep, fragment = path.partition('#')
    resource, querysep, query = resource.partition('?')
    if resource in ASSET_PATHS:
        target = 'assets/original/' + resource.lstrip('/')
    elif resource in URLS or resource.endswith('/'):
        target = page_file(resource)
    else:
        target = resource.lstrip('/')
    result = posixpath.relpath(target, posixpath.dirname(page_file(current)) or '.')
    return result + ('?' + query if querysep else '') + ('#' + fragment if sep else '')

def resolve_fragment(fragment, path):
    def replace(m):
        return m[1] + m[2] + esc(link(html.unescape(m[3]), path)) + m[2]
    fragment = re.sub(r'((?:href|src|poster)=)([\'"])(/[^\'"]*)\2', replace, fragment)
    def srcset(m):
        parts=[]
        for part in html.unescape(m[2]).split(','):
            bits=part.strip().split()
            if bits:parts.append(link(bits[0],path)+(' '+' '.join(bits[1:]) if len(bits)>1 else ''))
        return 'srcset='+m[1]+esc(', '.join(parts))+m[1]
    return re.sub(r'srcset=([\'"])([^\'"]*)\1', srcset, fragment)

def arrow():return '<span aria-hidden="true">↗</span>'

def header(path):
    nav='\n'.join(f'<a href="{esc(link(target,path))}">{label}</a>' for label,target in NAV)
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="header-inner">
  <a class="brand" href="{esc(link('/',path))}">Wentao Chen<span>Research &amp; academic profile</span></a>
  <button class="menu-toggle icon-button" aria-label="Open navigation" aria-expanded="false" aria-controls="main-nav">☰</button>
  <nav id="main-nav" aria-label="Main navigation">{nav}</nav>
  <div class="header-actions"><button class="icon-button" data-open-search aria-label="Search website"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.7" cy="10.7" r="6.7"/><path d="m16 16 4.5 4.5"/></svg></button><button class="icon-button" data-theme-toggle aria-label="Switch color theme" title="Switch color theme">◐</button></div>
</div></header>'''

def footer(path):
    return f'''<footer class="site-footer"><div><strong>Wentao Chen</strong><p>Beijing Institute of Technology · Jiaxing, China</p></div>
<div class="footer-right"><a href="{esc(link('/site-index/',path))}">All pages</a><a href="{esc(link('/maintenance.html#edit-content',path))}">编辑内容</a><a href="{esc(link('/maintenance.html',path))}">更新说明</a><p class="footer-copyright" hidden>© 2026 Wentao Chen · <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" rel="license">CC BY-NC-ND 4.0</a></p><p class="original-credit" hidden>Original site published with <a href="https://wowchemy.com/">Wowchemy</a>, an <a href="https://github.com/wowchemy/wowchemy-hugo-themes">open source</a> website builder.</p><p class="site-views" title="Total page views since this counter was enabled. Reloads count as new views.">Total views: <span data-site-views role="status" aria-live="polite">…</span></p></div></footer>'''

def shell(path, title, body, mainclass='', description=None):
    root=posixpath.relpath('.',posixpath.dirname(page_file(path)) or '.')+'/'
    desc=description or 'Wentao Chen, Associate Professor at Beijing Institute of Technology. Micro/nanoscale thermal transport, interfacial heat transfer, and molecular dynamics.'
    css=link('/assets/site.css',path)
    return f'''<!doctype html>
<html lang="en" data-root="{root}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(desc)}">
  <meta name="author" content="{esc(PROFILE['name'])}">
  <meta name="theme-color" content="#165b9e">
  <meta name="site-views-endpoint" content="{esc(SETTINGS['counter'].get('endpoint',''))}">
  {'<base href="'+esc(SITE_BASE+'/')+'">' if path=='/404.html' else ''}
  <link rel="canonical" href="{esc(SITE_BASE + path)}">
  <title>{esc(title)}{' | Wentao Chen' if title != 'Wentao Chen' else ''}</title>
  <link rel="icon" href="{esc(link('/assets/favicon.svg',path))}" type="image/svg+xml">
  <link rel="stylesheet" href="{esc(css)}">
  <script src="{esc(link('/assets/theme.js',path))}"></script>
  <script defer src="{esc(link('/assets/search-data.js',path))}"></script>
  <script defer src="{esc(link('/assets/site.js',path))}"></script>
  <script defer src="{esc(link('/assets/visits.js',path))}"></script>
</head>
<body>
{header(path)}
<main id="main" class="{mainclass}">
{body}
</main>
{footer(path)}
<dialog id="site-search" aria-labelledby="search-title"><div class="search-top"><h2 id="search-title">Search this website</h2><button class="icon-button" data-close-search aria-label="Close search">×</button></div><label class="sr-only" for="search-query">Search titles, abstracts, projects, and activities</label><input id="search-query" type="search" placeholder="Search papers, projects, activities…" autocomplete="off"><p class="search-hint">Search the complete website. Press Esc to close.</p><div id="search-results" aria-live="polite"></div></dialog>
</body>
</html>
'''

def write_page(path,title,body,mainclass='',description=None):
    dest=DIST/page_file(path);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(shell(path,title,resolve_fragment(body,path),mainclass,description),encoding='utf-8')

def item_links(item):
    links=''.join(f'<a class="text-link" href="{esc(x["url"])}" target="_blank" rel="noopener noreferrer">{esc(x["label"])} {arrow()}</a>' for x in item.get('links',[]))
    return links

def listing_card(item, number=None, image=False):
    year=item.get('date','')[:4]
    journal=item.get('fields',{}).get('Publication','')
    kind=item.get('fields',{}).get('Type','')
    meta=(item['activity_details']['date'] if item['kind']=='activities'
          else item.get('fields',{}).get('Date') or item.get('metadata') or year)
    authors=', '.join(item.get('authors') or [])
    cover=f'<a class="item-image" tabindex="-1" aria-hidden="true" href="{esc(item["path"])}"><img src="{esc(item["image"])}" alt="" loading="lazy"></a>' if image and item.get('image') else ''
    num=f'<span class="item-number">{number:02d}</span>' if number else ''
    summary=item.get('summary','')
    if item['kind']=='publication' and not item.get('featured'):summary=journal
    # All full abstracts stay in the corresponding detail page.
    if len(summary)>420:summary=summary[:417]+'…'
    return f'''<article class="listing-item {item['kind']}" data-filter-item data-year="{esc(year)}" data-type="{esc(kind)}">
{num}<div class="item-text"><p class="item-eyebrow">{esc(year)}{' · '+esc(journal) if journal else ''}</p><h3><a href="{esc(item['path'])}">{esc(item['title'])}</a></h3>
{'<p class="item-summary">'+esc(summary)+'</p>' if summary else ''}
{'<p class="item-authors">'+esc(authors)+'</p>' if authors else ''}
{'<p class="item-meta">'+esc(meta)+'</p>' if item['kind'] in ['talk','activities'] else ''}
<div class="item-links">{item_links(item)}<a class="detail-link" href="{esc(item['path'])}">Details <span aria-hidden="true">→</span></a></div></div>{cover}
</article>'''

def section(section_id, number, title, subtitle, body, extra='', classes='', source='content/site.json'):
    return f'''<!-- EDIT: {title}; source {source} -->
<section id="{section_id}" class="content-section {classes}"><div class="section-label"><span class="section-index">{number}</span><h2>{title}</h2><p>{subtitle}</p>{extra}</div><div class="section-content">{body}</div></section>'''

def achievement_cards(section_id):
    """Read complete cards verbatim, including dates and institution links."""
    source=(CONTENT/'home'/f'{section_id}.html').read_text(encoding='utf-8')

    class Cards(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.depth=0
            self.start=0
            self.cards=[]
            self.lines=[0]+[m.end() for m in re.finditer('\n',source)]

        def source_offset(self):
            line,column=self.getpos()
            return self.lines[line-1]+column

        def handle_starttag(self,tag,attrs):
            if tag!='div':
                return
            if self.depth:
                self.depth+=1
            elif 'card' in dict(attrs).get('class','').split():
                self.start=self.source_offset()
                self.depth=1

        def handle_endtag(self,tag):
            if tag=='div' and self.depth:
                self.depth-=1
                if not self.depth:
                    end=source.index('>',self.source_offset())+1
                    self.cards.append(source[self.start:end])

    parser=Cards()
    parser.feed(source)
    return parser.cards

def numbered_achievements(cards):
    rows=[]
    for number,card in enumerate(cards,1):
        card=card.replace('class="card ','class="card numbered-achievement ',1)
        opening_end=card.index('>')+1
        card=card[:opening_end]+f'<span class="item-number">{number:02d}</span>'+card[opening_end:]
        rows.append(card)
    return ''.join(rows)

def achievement_archive(section_id,title):
    cards=achievement_cards(section_id)
    description='Honors, awards & scholarships' if section_id=='awards' else 'Academic service & professional memberships'
    body=f'<div class="page-heading"><p class="eyebrow">Academic profile</p><h1>{esc(title)}</h1><p class="page-intro">{description} · {len(cards)} entries</p></div>'
    body+='<div class="legacy-home achievement-archive">'+numbered_achievements(cards)+'</div>'
    write_page('/'+section_id+'/',title,body,'archive-main')

def gallery_content():
    return (CONTENT/'home/gallery.html').read_text(encoding='utf-8')

def gallery_body(body):
    marker='<!-- GALLERY_CONTENT -->'
    if body.count(marker)!=1:
        raise ValueError('Expected one gallery content marker')
    return body.replace(marker,gallery_content())

def homepage():
    p=PROFILE
    aff=''.join(f'<a href="{esc(a["url"])}" target="_blank" rel="noopener noreferrer">{esc(a["name"])}</a>' for a in p['affiliations'])
    socials=''.join(f'<a href="{esc(a["url"])}"'+(' target="_blank" rel="noopener noreferrer"' if a['url'].startswith('http') else '')+f'>{esc(a["label"])} {arrow()}</a>' for a in p['links'] if a['label']!='Email')
    interests=''.join(f'<li>{esc(x)}</li>' for x in p['interests'])
    edu=''.join(f'<li><strong>{esc(x["course"])}</strong><span>{"<br>".join(esc(line) for line in x["institution"].splitlines())}</span></li>' for x in p['education'])
    body=f'''<!-- EDIT: Biography, affiliations, education and links in content/site.json -->
<section id="about" class="hero"><div class="profile-panel"><div class="portrait-frame"><img class="portrait" src="{esc(p['portrait'])}" alt="{esc(p['name'])}" width="270" height="270"></div><h1>{esc(p['name'])}</h1><p class="profile-role">{esc(p['role'])}</p><p class="profile-team">{esc(p['team'])}</p><div class="affiliations">{aff}</div><a class="email-link" href="mailto:{esc(p['email'])}">{esc(p['email'])} {arrow()}</a><div class="social-links" aria-label="Academic profiles">{socials}</div></div>
<div class="intro-panel"><h2>{p['hero_title']}</h2><div class="biography"><h3 class="sr-only">Biography</h3>{p['biography_html']}</div>
<div class="interests-education"><div><h3>Research interests</h3><ul class="interest-list">{interests}</ul></div><div><h3>Education</h3><ul class="education-list">{edu}</ul></div></div></div></section>
<div class="overview-strip"><a href="/publication/"><strong>{sum(x['kind']=='publication' for x in RECORDS):02d}</strong><span>Publications</span><b>↗</b></a><a href="/project/"><strong>{sum(x['kind']=='project' for x in RECORDS):02d}</strong><span>Research projects</span><b>↗</b></a><a href="/event/"><strong>{sum(x['kind']=='talk' for x in RECORDS):02d}</strong><span>Conference contributions</span><b>↗</b></a><a href="/activities/"><strong>{sum(x['kind']=='activities' for x in RECORDS):02d}</strong><span>Academic activities</span><b>↗</b></a></div>'''
    definitions=[('projects','01','Projects','Research programs & collaborations','project','/project/',False),
       ('featured','02','Publications','Selected research publications','publication','/publication/',True),
       ('talks','03','Conference','Presentations & invited talks','talk','/event/',True),
       ('news','04','Activities','Academic exchanges & international collaboration','activities','/activities/',True)]
    for sec,n,title,subtitle,kind,url,image in definitions:
        items=[BY_PATH[x['path']] for x in SITE['home_lists'][sec]]
        if kind in ('talk','activities'):
            items=[dict(item,image=preview.get('image') or item.get('image'))
                   for item,preview in zip(items,SITE['home_lists'][sec])]
        limit=SITE.get('home_limits',{}).get(sec)
        if isinstance(limit,int) and limit>=0:
            items=items[:limit]
        cards=''.join(listing_card(x,i+1,image) for i,x in enumerate(items))
        extra=f'<a class="section-more" href="{url}">View all {sum(x["kind"]==kind for x in RECORDS)} <span aria-hidden="true">→</span></a>'
        body+=section(sec,n,title,subtitle,cards,extra, 'has-images' if image else '')
    for sec,n,title,sub in [('awards','05','Awards','Honors, awards & scholarships'),('appointment','06','Appointment','Academic service & professional memberships'),('experience','07','Experience','Research, academic & industry experience'),('contact','08','Contact','Get in touch')]:
        if sec in ('awards','appointment'):
            cards=achievement_cards(sec)
            limit=SITE.get('home_limits',{}).get(sec,len(cards))
            extra=f'<a class="section-more" href="/{sec}/">View all {len(cards)} <span aria-hidden="true">→</span></a>'
            body+=section(sec,n,title,sub,numbered_achievements(cards[:limit]),extra,classes='legacy-home '+sec+'-section')
            continue
        frag=(CONTENT/'home'/f'{sec}.html').read_text(encoding='utf-8')
        # Keep verbatim source content. The fragment's wrapper owns the original anchor.
        frag=frag.replace('id="'+sec+'"','data-original-section="'+sec+'"',1)
        frag=re.sub(r'<div class="section-heading[^>]*>.*?</div>','',frag,flags=re.S)
        body+=section(sec,n,title,sub,frag,classes='legacy-home '+sec+'-section')
    body+=section('gallery','09','Gallery','Photo collection',gallery_content(),
                  classes='gallery-section',source='content/home/gallery.html')
    write_page('/','Wentao Chen',body,'home-main')

def archive_page(path,title,kind,typ=None):
    items=[x for x in RECORDS if x['kind']==kind and (not typ or x.get('fields',{}).get('Type')==typ)]
    items.sort(key=lambda x:x.get('date',''),reverse=True)
    years=sorted({i.get('date','')[:4] for i in items},reverse=True)
    options=''.join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in years)
    types=sorted({i.get('fields',{}).get('Type','') for i in items}-{''})
    type_select=('<label>Type<select data-filter-type><option value="">All types</option>'+''.join(f'<option>{esc(t)}</option>' for t in types)+'</select></label>') if types else ''
    body=f'''<div class="page-heading"><p class="eyebrow">Research archive</p><h1>{esc(title)}</h1><p class="page-intro">Explore the complete collection.</p></div><div class="filter-bar"><label class="filter-query">Search<input type="search" data-filter-search placeholder="Search titles, authors, and topics…"></label><label>Year<select data-filter-year><option value="">All years</option>{options}</select></label>{type_select}<p data-filter-count aria-live="polite">{len(items)} entries</p></div><div class="archive-list">'''+''.join(listing_card(x,i+1,kind in ['publication','activities','talk']) for i,x in enumerate(items))+'''</div><p class="empty-filter" hidden>No matching entries. Try a different term or year.</p>'''
    write_page(path,title,body,'archive-main')

def activity_body(body,item):
    """Render editable activity facts with the Conference detail-page layout."""
    details=item['activity_details']
    rows=[]
    for label,key in [('Date','date'),('Event','event'),('Location','location')]:
        value='<br>'.join(esc(line) for line in details[key].splitlines())
        if key=='event':
            value=f'<a href="{esc(details["url"])}" target="_blank" rel="noopener noreferrer">{value}</a>'
        rows.append(f'''<div class="row">
<div class="col-md-1"></div>
<div class="col-md-10"><div class="row">
<div class="col-12 col-md-3 pub-row-heading">{label}</div>
<div class="col-12 col-md-9">{value}</div>
</div></div>
<div class="col-md-1"></div>
</div>''')
    marker='<!-- ACTIVITY_DETAILS -->'
    if body.count(marker)!=1:
        raise ValueError(f'Expected one activity details marker in {item["path"]}')
    return body.replace(marker,'<section class="activity-details" aria-label="Activity details">\n'+'\n'.join(rows)+'\n</section>')

def project_body(body,item):
    """Render a project's editable fund name as a link beside the Fund label."""
    details=item['fund_details']
    marker='<!-- PROJECT_FUND -->'
    if body.count(marker)!=1:
        raise ValueError(f'Expected one project fund marker in {item["path"]}')
    row=f'''<section class="project-fund" aria-label="Project funding">
<div class="row">
<div class="col-md-1"></div>
<div class="col-md-10"><div class="row">
<div class="col-12 col-md-3 pub-row-heading">Fund</div>
<div class="col-12 col-md-9"><a href="{esc(details['url'])}" target="_blank" rel="noopener noreferrer">{esc(details['name'])}</a></div>
</div></div>
<div class="col-md-1"></div>
</div>
</section>'''
    return body.replace(marker,row)

def article_title(body, title):
    return re.sub(r'<h1\b[^>]*>.*?</h1>', '<h1>'+esc(title)+'</h1>', body, count=1, flags=re.S)

def validate_content():
    parsed=urlsplit(SITE_BASE)
    if parsed.scheme!='https' or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError('site_url/SITE_URL must be an absolute HTTPS URL without query or fragment')
    endpoint=SETTINGS['counter'].get('endpoint','')
    if endpoint:
        parsed=urlsplit(endpoint)
        if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
            raise ValueError('counter.endpoint must be an HTTPS URL without credentials or fragment')
    paths=set()
    for page in PAGES:
        path=page['path']
        if not path.startswith('/') or '..' in path.split('/') or path in paths:
            raise ValueError('Invalid or duplicate page path: '+path)
        paths.add(path)
        source=(CONTENT/page['body_file']).resolve()
        if not source.is_relative_to(CONTENT.resolve()) or not source.is_file():
            raise ValueError('Missing or unsafe page body: '+page['body_file'])
    record_paths=set()
    for item in RECORDS:
        if item['path'] in record_paths or item['path'] not in paths:
            raise ValueError('Duplicate record or missing detail page: '+item['path'])
        record_paths.add(item['path'])
        if item['kind']=='activities' and not all(item.get('activity_details',{}).get(k) for k in ['date','event','location','url']):
            raise ValueError('Missing activity details: '+item['path'])
        if item['kind']=='project' and not all(item.get('fund_details',{}).get(k) for k in ['name','url']):
            raise ValueError('Missing project fund: '+item['path'])
    for name,items in SITE['home_lists'].items():
        for item in items:
            if item['path'] not in record_paths:
                raise ValueError('Unknown home-list item: '+item['path'])

def generate():
    DIST.mkdir(exist_ok=True)
    homepage()
    archives={'/publication/':('Publications','publication',None),'/project/':('Projects','project',None),'/event/':('Conference & presentations','talk',None),'/activities/':('Activities','activities',None),'/publication-type/1/':('Conference papers','publication','Conference paper'),'/publication-type/2/':('Journal articles','publication','Journal article')}
    for p in PAGES:
        path=p['path']
        if path in archives:continue
        content=(CONTENT/p['body_file']).read_text(encoding='utf-8')
        item=BY_PATH.get(path)
        title=item['title'] if item else p['title']
        if item:content=article_title(content,title)
        if item and item['kind']=='activities':content=activity_body(content,item)
        if item and item['kind']=='project':content=project_body(content,item)
        if path=='/others/gallery/':content=gallery_body(content)
        bread=f'<div class="breadcrumbs"><a href="/">Home</a><span>/</span><a href="/site-index/">All pages</a></div>'
        write_page(path,title,bread+content,'detail-main')
    for path,(title,kind,typ) in archives.items():archive_page(path,title,kind,typ)
    achievement_archive('awards','Awards')
    achievement_archive('appointment','Appointment')
    groups=[('Publications','publication'),('Projects','project'),('Conference & presentations','talk'),('Activities','activities')]
    allbody='<div class="page-heading"><p class="eyebrow">Academic directory</p><h1>All pages</h1><p>Browse publications, projects, presentations, activities, and academic profile.</p></div>'
    for title,kind in groups:
        allbody+='<section class="site-map-group"><h2>'+title+'</h2><ul>'+''.join('<li><a href="'+esc(x['path'])+'">'+esc(x['title'])+'</a></li>' for x in RECORDS if x['kind']==kind)+'</ul></section>'
    covered={x['path'] for x in RECORDS}|set(archives)
    # Keep the directory focused; legacy indexes, pagination and template pages retain their original URLs.
    allbody+='<section class="site-map-group"><h2>Academic profile</h2><ul><li><a href="/awards/">All awards & scholarships</a></li><li><a href="/appointment/">All appointments & professional memberships</a></li><li><a href="/others/gallery/">Gallery</a></li></ul></section>'
    write_page('/site-index/','All pages',allbody,'archive-main')
    write_page('/slides/','Slides','<div class="page-heading"><h1>Slides</h1></div><p>The original slides index was unavailable. The existing example presentation is preserved below.</p><p><a href="/slides/example/">View the original example slides →</a></p>','archive-main')
    write_page('/admin/','Website editor','<div class="page-heading"><h1>网站内容更新</h1></div><p>请修改 GitHub 仓库中的 content 文件。提交后自动检查、生成并发布网页。</p><p><a class="button" href="/maintenance.html#edit-content">查看内容编辑说明 →</a></p><p>本地可视化编辑助手保留用于临时预览。直接修改生成的 HTML 不会同步到源内容，下一次发布会覆盖。</p><p><a href="/editor.html">打开本地编辑助手</a></p>','archive-main')
    search=[]
    for x in RECORDS:
        page=next((p for p in PAGES if p['path']==x['path']),None)
        full=(CONTENT/page['body_file']).read_text(encoding='utf-8') if page else ''
        if page and x['kind']=='activities':full=activity_body(full,x)
        if page and x['kind']=='project':full=project_body(full,x)
        text=html.unescape(re.sub('<[^>]+>',' ',full))
        search.append({'title':x['title'],'kind':x['kind'],'href':page_file(x['path']),'text':' '.join((x.get('summary','')+' '+text).split())})
    home_text=' '.join(PROFILE['interests'])+' '+html.unescape(re.sub('<[^>]+>',' ',PROFILE['biography_html']))
    search.append({'title':'Biography, research interests & education','kind':'profile','href':'index.html#about','text':home_text+' '+json.dumps(PROFILE['education'],ensure_ascii=False)})
    for sec in ['awards','appointment','experience','contact']:
        full=(CONTENT/'home'/f'{sec}.html').read_text(encoding='utf-8')
        href=sec+'/index.html' if sec in ('awards','appointment') else 'index.html#'+sec
        search.append({'title':sec.title(),'kind':'profile','href':href,'text':' '.join(html.unescape(re.sub('<[^>]+>',' ',full)).split())})
    # Index auxiliary pages as well, including the gallery and slide example.
    for p in PAGES:
        if p['path'] in covered:continue
        full=(CONTENT/p['body_file']).read_text(encoding='utf-8')
        if p['path']=='/others/gallery/':full=gallery_body(full)
        search.append({'title':p['title'],'kind':'page','href':page_file(p['path']),'text':' '.join(html.unescape(re.sub('<[^>]+>',' ',full)).split())})
    (DIST/'assets/search-data.js').write_text('window.SITE_SEARCH = '+json.dumps(search,ensure_ascii=False).replace('</','<\\/')+';\n',encoding='utf-8')
    edit_pages=[{'path':'index.html','title':'首页 / Biography'}]+[{'path':page_file(p['path']),'title':p['title']} for p in PAGES]
    edit_pages += [{'path':'site-index/index.html','title':'All pages'},{'path':'slides/index.html','title':'Slides'},
                   {'path':'awards/index.html','title':'All awards'},{'path':'appointment/index.html','title':'All appointments'}]
    (DIST/'assets/editor-pages.js').write_text('window.EDIT_PAGES = '+json.dumps(edit_pages,ensure_ascii=False)+';\n',encoding='utf-8')
    # Use the custom domain or the actual Pages URL supplied by Actions.
    root=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for p in sorted(URLS):ET.SubElement(ET.SubElement(root,'url'),'loc').text=SITE_BASE+p
    ET.ElementTree(root).write(DIST/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+SITE_BASE+'/sitemap.xml\n')
    (DIST/'.nojekyll').touch()
    write_page('/404.html','Page not found','<div class="page-heading"><h1>Page not found</h1></div><p>The page may have moved.</p><p><a href="/">Return to the homepage →</a></p>','archive-main')
    print(f'Built {len(list(DIST.rglob("*.html")))} HTML pages. Open public/index.html.')

def build():
    global DIST
    validate_content()
    destination=ROOT/'public'
    try:
        with tempfile.TemporaryDirectory(prefix='.build-',dir=ROOT) as temporary:
            DIST=Path(temporary)/'public'
            shutil.copytree(STATIC,DIST)
            generate()
            if destination.exists():shutil.rmtree(destination)
            DIST.replace(destination)
    finally:
        DIST=destination

if __name__=='__main__':build()
