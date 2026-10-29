#!/usr/bin/env python3
"""Validate the actual Pages artifact: local links, images, fragments and records."""
import argparse,html,json,re,sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.ids=set();self.refs=[];self.images=[];self.tags=[]
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);self.tags.append((tag,attrs))
        if attrs.get('id'):self.ids.add(attrs['id'])
        if tag=='a' and attrs.get('name'):self.ids.add(attrs['name'])
        for key in ['href','src','poster']:
            if attrs.get(key):self.refs.append((tag,key,attrs[key]))
        for item in attrs.get('srcset','').split(','):
            if item.strip():self.refs.append((tag,'srcset',item.strip().split()[0]))
        if tag=='img':self.images.append(attrs)

def validate(directory):
    root=Path(directory).resolve()
    files=sorted(p for p in root.rglob('*') if p.is_file())
    pages={p:Document(p.read_text(encoding='utf-8')) for p in files if p.suffix=='.html'}
    errors=[];checked=0;external=set();images=0
    for file,document in pages.items():
        for tag,key,reference in document.refs:
            parsed=urlsplit(html.unescape(reference))
            if parsed.scheme or parsed.netloc:
                if parsed.scheme in ['https','http']:external.add(reference)
                continue
            if not parsed.path:target=file
            else:
                target=(root/parsed.path.lstrip('/') if parsed.path.startswith('/') else file.parent/parsed.path).resolve()
                if target.is_dir() or parsed.path.endswith('/'):target=target/'index.html'
            checked+=1
            label=f'{file.relative_to(root)}: {key}={reference}'
            if not target.is_relative_to(root):errors.append('Path escapes artifact: '+label);continue
            if not target.is_file():errors.append('Missing target: '+label);continue
            fragment=unquote(parsed.fragment)
            # The original publication list uses #1/#2 as JavaScript filter values.
            if fragment and target in pages and fragment not in pages[target].ids:
                if fragment in ['1','2'] and target==root/'publication/index.html':continue
                errors.append('Missing fragment: '+label)
        images+=len(document.images)
        for attrs in document.images:
            if 'alt' not in attrs:errors.append(f'Missing image alt: {file.relative_to(root)}')
    for file in (root/'assets').glob('*.css'):
        for reference in re.findall(r'url\(\s*[\'"]?([^\s)\'"]+)',file.read_text(encoding='utf-8')):
            if urlsplit(reference).scheme or reference.startswith('#'):continue
            target=(file.parent/unquote(reference.split('?')[0])).resolve()
            checked+=1
            if not target.is_file():errors.append(f'Missing CSS asset: {file.relative_to(root)}: {reference}')
    site=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))
    home=(root/'index.html').read_text(encoding='utf-8')
    kinds=Counter(item['kind'] for item in site['records'])
    for item in site['records']:
        path=root/(item['path'].lstrip('/')+'index.html')
        if not path.is_file():errors.append('Missing record page: '+item['path']);continue
        body=path.read_text(encoding='utf-8')
        if html.escape(item['title'],quote=True) not in body:errors.append('Detail title out of sync: '+item['path'])
        if item['kind']=='project':
            if not re.search(r'>Fund<',body):errors.append('Missing project Fund: '+item['path'])
            if 'PROJECT_FUND' in body:errors.append('Unexpanded project marker: '+item['path'])
        if item['kind']=='activities' and 'ACTIVITY_DETAILS' in body:errors.append('Unexpanded activity marker: '+item['path'])
    for marker in ['<!-- PROJECT_FUND -->','<!-- ACTIVITY_DETAILS -->','<!-- GALLERY_CONTENT -->']:
        if any(marker in p.read_text(encoding='utf-8') for p in pages):errors.append('Unexpanded content marker: '+marker)
    for section,limit in site['home_limits'].items():
        match=re.search(r'<section id="'+re.escape(section)+r'".*?</section>',home,re.S)
        if not match:errors.append('Missing home section: '+section);continue
        count=len(re.findall(r'class="item-number"',match[0]))
        if count>limit:errors.append(f'Home limit exceeded: {section}: {count}>{limit}')
    if not (root/'.nojekyll').exists():errors.append('Missing .nojekyll')
    for path in files:
        if path.is_symlink():errors.append('Symlink in artifact: '+str(path.relative_to(root)))
    settings=json.loads((ROOT/'content/settings.json').read_text(encoding='utf-8'))
    return {
        'status':'passed' if not errors else 'failed',
        'scope':'local static artifact; external links, public GitHub deployment, DNS/HTTPS and mainland access require live checks',
        'html_pages':len(pages),'files':len(files),'local_references_checked':checked,
        'image_references':images,'external_links_not_fetched':len(external),
        'content_records':dict(kinds),'gallery_photos':len(list((root/'assets/gallery').glob('photo-*.jpg'))),
        'counter_status':'endpoint configured; live verification required' if settings['counter'].get('endpoint') else 'independent backend prepared; endpoint not connected',
        'errors':errors,
    }

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=ROOT/'public');parser.add_argument('--report',type=Path)
    args=parser.parse_args();report=validate(args.directory)
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:args.report.write_text(text+'\n',encoding='utf-8')
    print(text);sys.exit(0 if report['status']=='passed' else 1)
