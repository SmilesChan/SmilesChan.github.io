'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const preview = $('#preview'), pageSelect = $('#page-select'), source = $('#html-source');
  const files = new Map(), modified = new Map();
  let currentPath = 'index.html', original = '', mode = 'visual', selected = null, selectedBlock = null, dirty = false;
  const note = text => { $('#status').textContent = text; };
  const safePath = path => path && !path.startsWith('/') && !path.split('/').includes('..') && !path.includes('\\') && !/^[a-z]+:/i.test(path);
  const encode = text => new TextEncoder().encode(text);
  function populate(extra=[]) {
    const list = new Map((window.EDIT_PAGES || []).map(p => [p.path,p.title]));
    extra.forEach(p => {if (p.endsWith('.html') && !['editor.html','maintenance.html'].includes(p)) list.set(p,list.get(p)||p);});
    pageSelect.replaceChildren();
    for (const [path,title] of list) {const o=document.createElement('option');o.value=path;o.textContent=title+' · '+path;pageSelect.append(o);}
    pageSelect.value=currentPath;
  }
  function serialized() {
    if (!original) return '';
    const doc = new DOMParser().parseFromString(original,'text/html');
    const main = doc.querySelector('main');
    if (main) main.innerHTML = mode === 'source' ? source.value : preview.contentDocument.querySelector('main')?.innerHTML || main.innerHTML;
    doc.title=$('#page-title').value || doc.title;
    return '<!doctype html>\n'+doc.documentElement.outerHTML;
  }
  function remember() {
    if (!original || !dirty) return;
    modified.set(currentPath,serialized());dirty=false;
    $('#modified-list').replaceChildren();
    for (const path of modified.keys()) { const p=document.createElement('div');p.textContent='已修改：'+path;$('#modified-list').append(p); }
  }
  function showDocument(text,path) {
    original=text;currentPath=path;$('#page-path').value=path;pageSelect.value=path;
    const doc=new DOMParser().parseFromString(text,'text/html');
    if(!doc.querySelector('main')){note('该文件没有 main 主体，无法安全地进行可视化编辑。');original='';return;}
    $('#page-title').value=doc.title;
    source.value=doc.querySelector('main').innerHTML;
    // Scripts never run inside the editing preview.
    doc.querySelectorAll('script,base').forEach(e=>e.remove());
    const base=doc.createElement('base');base.href=new URL(path,location.href).href;doc.head.prepend(base);
    const style=doc.createElement('style');style.textContent='main[contenteditable]{outline:2px dashed #88afd0;outline-offset:-2px;min-height:300px}main a{cursor:text}main img{cursor:crosshair}header,footer{pointer-events:none}';doc.head.append(style);
    const editable=doc.querySelector('main');editable.contentEditable='true';editable.spellcheck=false;
    preview.onload=()=>{
      const d=preview.contentDocument;
      d.querySelector('main')?.addEventListener('input',()=>{dirty=true;note('内容已修改；下载前请检查文字与链接。');});
      d.addEventListener('click',e=>{
        const main=d.querySelector('main');if(!main.contains(e.target))return;
        const target=e.target.closest('a,img');if(target){e.preventDefault();selected=target;$('#selected-url').value=target.getAttribute(target.tagName==='IMG'?'src':'href')||'';}
        selectedBlock=e.target.closest('.listing-item,.row.experience,.card');
        $('#selection-status').textContent=selectedBlock?'已选择条目，可复制。':target?'已选择'+(target.tagName==='IMG'?'图片':'链接')+'，可修改地址。':'已选择正文。';
      });
      note('已加载 '+path+'。点击正文开始编辑。');
    };
    preview.srcdoc='<!doctype html>\n'+doc.documentElement.outerHTML;selected=null;selectedBlock=null;dirty=false;
    if(mode==='source'){source.hidden=false;preview.hidden=true;}
  }
  async function load(path) {
    remember();
    if(!safePath(path)){note('页面路径无效，请使用网站内的相对路径。');return;}
    if(modified.has(path)){showDocument(modified.get(path),path);return;}
    if(files.has(path)){showDocument(await files.get(path).text(),path);return;}
    if(location.protocol==='file:'){note('请先选择 dist 文件夹，再选择要编辑的页面。');return;}
    try{const r=await fetch(new URL(path,location.href));if(!r.ok)throw new Error(r.status);showDocument(await r.text(),path);}catch(e){note('无法加载页面。请先选择本地 dist 文件夹。');}
  }
  $('#folder-input').addEventListener('change', async e=>{
    remember();files.clear();
    const entries=[...e.target.files];
    const paths=entries.map(f=>f.webkitRelativePath.split('/').slice(1).join('/'));
    const prefix=paths.includes('dist/index.html')?'dist/':'';
    entries.forEach((f,i)=>{if(paths[i].startsWith(prefix)){const p=paths[i].slice(prefix.length);if(safePath(p))files.set(p,f);}});
    $('#folder-status').textContent='已载入 '+files.size+' 个文件。';populate([...files.keys()]);
    await load(files.has(currentPath)?currentPath:'index.html');
  });
  $('#file-input').addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;remember();const path=$('#page-path').value||f.name;showDocument(await f.text(),path);});
  pageSelect.addEventListener('change',()=>load(pageSelect.value));
  $('#page-title').addEventListener('input',()=>{dirty=true;});
  $('#mobile-preview').addEventListener('click',()=>{
    const mobile=preview.style.width==='390px';
    preview.style.width=mobile?'100%':'390px';preview.style.maxWidth='100%';preview.style.display='block';preview.style.margin='0 auto';
    $('#mobile-preview').textContent=mobile?'手机预览':'桌面预览';
  });
  $('#visual-mode').addEventListener('click',()=>{
    if(mode==='source'&&original){const text=serialized();mode='visual';showDocument(text,currentPath);dirty=true;}
    mode='visual';source.hidden=true;preview.hidden=false;$('#visual-mode').classList.add('active');$('#source-mode').classList.remove('active');
  });
  $('#source-mode').addEventListener('click',()=>{
    if(mode==='visual'&&original)source.value=preview.contentDocument.querySelector('main').innerHTML;
    mode='source';source.hidden=false;preview.hidden=true;$('#source-mode').classList.add('active');$('#visual-mode').classList.remove('active');
  });
  source.addEventListener('input',()=>{dirty=true;});
  for(const [id,command] of [['bold','bold'],['italic','italic'],['undo','undo']])$('#'+id).addEventListener('click',()=>{if(mode!=='visual')return;preview.contentWindow.focus();preview.contentDocument.execCommand(command);dirty=true;});
  $('#clone-item').addEventListener('click',()=>{
    if(!selectedBlock||mode!=='visual'){note('请先点击右侧的一个论文、活动或经历条目。');return;}
    const clone=selectedBlock.cloneNode(true);clone.removeAttribute('id');clone.querySelectorAll('[id]').forEach(x=>x.removeAttribute('id'));selectedBlock.after(clone);selectedBlock=clone;dirty=true;note('已复制条目。请修改标题、作者、日期及详情链接；新增详情页请参考说明。');
  });
  $('#apply-url').addEventListener('click',()=>{
    if(!selected){note('请先点击右侧的链接或图片。');return;}
    const val=$('#selected-url').value.trim();
    if(!val||/^(?:javascript|vbscript|data):/i.test(val)){note('请输入有效的网址或相对路径。');return;}
    selected.setAttribute(selected.tagName==='IMG'?'src':'href',val);dirty=true;note('地址已更新。下载时会保留相对路径。');
  });
  function download(name,blob) {
    const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),30000);
  }
  $('#download-page').addEventListener('click',()=>{
    if(!original){note('请先加载一个 HTML 页面。');return;}
    const path=$('#page-path').value.trim();if(!safePath(path)){note('请输入有效的站内相对路径。');return;}
    const result=serialized();modified.set(path,result);dirty=false;
    download(path.split('/').pop(),new Blob([result],{type:'text/html;charset=utf-8'}));
    note('已生成 HTML 下载文件。请用它替换 dist/'+path+'；原子目录需要保持不变。');
  });
  // Small dependency-free ZIP writer (STORE method, standard CRC-32, UTF-8 filenames).
  const table=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
  function crc(bytes){let c=0xffffffff;for(const b of bytes)c=table[(c^b)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
  function zip(entries) {
    const chunks=[],central=[];let offset=0;
    for(const {name,data} of entries){
      const n=encode(name),checksum=crc(data),h=new Uint8Array(30+n.length),v=new DataView(h.buffer);
      v.setUint32(0,0x04034b50,true);v.setUint16(4,20,true);v.setUint16(6,0x800,true);v.setUint32(14,checksum,true);v.setUint32(18,data.length,true);v.setUint32(22,data.length,true);v.setUint16(26,n.length,true);h.set(n,30);
      const c=new Uint8Array(46+n.length),cv=new DataView(c.buffer);cv.setUint32(0,0x02014b50,true);cv.setUint16(4,20,true);cv.setUint16(6,20,true);cv.setUint16(8,0x800,true);cv.setUint32(16,checksum,true);cv.setUint32(20,data.length,true);cv.setUint32(24,data.length,true);cv.setUint16(28,n.length,true);cv.setUint32(42,offset,true);c.set(n,46);
      chunks.push(h,data);central.push(c);offset+=h.length+data.length;
    }
    const end=new Uint8Array(22),v=new DataView(end.buffer),centralSize=central.reduce((n,x)=>n+x.length,0);
    v.setUint32(0,0x06054b50,true);v.setUint16(8,entries.length,true);v.setUint16(10,entries.length,true);v.setUint32(12,centralSize,true);v.setUint32(16,offset,true);
    return new Blob([...chunks,...central,end],{type:'application/zip'});
  }
  $('#download-site').addEventListener('click',async()=>{
    if(!files.has('index.html')){note('导出完整网站前，请选择解压后的 dist 文件夹。');return;}
    remember();const b=$('#download-site');b.disabled=true;note('正在整理所有页面、图片和更新后的搜索索引…');
    try {
      const payload=new Map();for(const [path,file] of files)payload.set(path,new Uint8Array(await file.arrayBuffer()));
      for(const [path,text] of modified)payload.set(path,encode(text));
      const index=[];
      for(const [path,data] of payload){if(!path.endsWith('.html')||['editor.html','maintenance.html'].includes(path))continue;
        const doc=new DOMParser().parseFromString(new TextDecoder().decode(data),'text/html');const main=doc.querySelector('main');if(!main)continue;
        index.push({title:doc.querySelector('h1')?.textContent||doc.title,kind:'page',href:path,text:main.textContent.replace(/\s+/g,' ').trim()});
      }
      payload.set('assets/search-data.js',encode('window.SITE_SEARCH = '+JSON.stringify(index).replace(/<\//g,'<\\/')+';\n'));
      const pages=index.map(x=>({title:x.title,path:x.href}));payload.set('assets/editor-pages.js',encode('window.EDIT_PAGES = '+JSON.stringify(pages)+';\n'));
      download('WentaoChen-Website-Updated.zip',zip([...payload].map(([name,data])=>({name,data}))));
      note('完整网站 ZIP 已生成，包含 '+payload.size+' 个文件。解压后可直接预览或重新上传部署。');
    }catch(e){note('导出失败：'+e.message);}finally{b.disabled=false;}
  });
  populate();load('index.html');
})();
