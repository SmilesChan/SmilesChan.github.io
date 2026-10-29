"""Exercise a real content-only update through build and generated cross-links."""
import json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ContentUpdates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory(prefix='wentao-content-test-')
        cls.folder=Path(cls.temporary.name)
        shutil.copy2(ROOT/'build.py',cls.folder/'build.py')
        shutil.copytree(ROOT/'content',cls.folder/'content')
        shutil.copytree(ROOT/'static',cls.folder/'static')
        cls.original=(cls.folder/'content/site.json').read_text(encoding='utf-8')
        cls.settings=(cls.folder/'content/settings.json').read_text(encoding='utf-8')
    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()
    def setUp(self):
        (self.folder/'content/site.json').write_text(self.original,encoding='utf-8')
        (self.folder/'content/settings.json').write_text(self.settings,encoding='utf-8')
    def build(self,**environment):
        env={**os.environ,**environment};env.pop('SITE_URL',None)
        env.update(environment)
        return subprocess.run([sys.executable,'build.py'],cwd=self.folder,env=env,text=True,capture_output=True)
    def test_content_only_title_propagates_to_home_archive_detail_search(self):
        site=json.loads(self.original)
        item=next(r for r in site['records'] if r['kind']=='project' and r['path']==site['home_lists']['projects'][0]['path'])
        item['title']='Content-only update & automated publication test'
        item['fund_details']['name']='Updated fund test';item['fund_details']['url']='https://www.nsfc.gov.cn/'
        (self.folder/'content/site.json').write_text(json.dumps(site),encoding='utf-8')
        result=self.build();self.assertEqual(result.returncode,0,result.stderr)
        for relative in ['index.html','project/index.html',item['path'].lstrip('/')+'index.html']:
            self.assertIn('Content-only update &amp; automated publication test',(self.folder/'public'/relative).read_text())
        self.assertIn(item['title'],(self.folder/'public/assets/search-data.js').read_text())
        self.assertIn('Updated fund test',(self.folder/'public'/item['path'].lstrip('/')/'index.html').read_text())
    def test_preview_repository_path_and_custom_domain_metadata(self):
        result=self.build(SITE_URL='https://example.github.io/academic')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('https://example.github.io/academic/project/',(self.folder/'public/sitemap.xml').read_text())
        self.assertIn('https://example.github.io/academic/sitemap.xml',(self.folder/'public/robots.txt').read_text())
        page=(self.folder/'public/project/index.html').read_text()
        self.assertIn('href="../index.html#about"',page)
        self.assertIn('https://example.github.io/academic/project/',page)
    def test_missing_body_and_bad_json_fail_before_replacing_last_good_build(self):
        good=self.build();self.assertEqual(good.returncode,0,good.stderr)
        original=(self.folder/'public/index.html').read_bytes()
        site=json.loads(self.original);site['pages'][0]['body_file']='pages/does-not-exist.html'
        (self.folder/'content/site.json').write_text(json.dumps(site))
        self.assertNotEqual(self.build().returncode,0)
        self.assertEqual((self.folder/'public/index.html').read_bytes(),original)
        (self.folder/'content/site.json').write_text('{bad json')
        self.assertNotEqual(self.build().returncode,0)
        self.assertEqual((self.folder/'public/index.html').read_bytes(),original)
    def test_duplicate_page_and_unsafe_counter_endpoint_are_rejected(self):
        site=json.loads(self.original);site['pages'].append(site['pages'][0].copy())
        (self.folder/'content/site.json').write_text(json.dumps(site))
        self.assertNotEqual(self.build().returncode,0)
        (self.folder/'content/site.json').write_text(self.original)
        settings=json.loads(self.settings);settings['counter']['endpoint']='http://unsafe.example/counter'
        (self.folder/'content/settings.json').write_text(json.dumps(settings))
        self.assertNotEqual(self.build().returncode,0)

if __name__=='__main__':unittest.main()
