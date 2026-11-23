import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('export_notes.py')

class ExportTests(unittest.TestCase):
    def test_selective_stable_export_and_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root / 'source', root / 'content'
            source.mkdir()
            (source / 'index.md').write_text('# Учебник\n\n[Тема](topic.md#What%20is%20Context%3F)\n')
            (source / 'topic.md').write_text('---\ntags: [test]\n---\n# Тема\n\n## What is Context?\nТекст\n')
            (source / 'AGENTS.md').write_text('Private instructions')
            (source / '.secret.md').write_text('secret')
            (source / 'credentials.json').write_text('secret')
            (source / 'outside.md').symlink_to('/etc/hosts')
            def run():
                return subprocess.run([sys.executable, str(SCRIPT), str(source), str(dest)], capture_output=True, text=True)
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({p.name for p in dest.iterdir()}, {'index.md', 'topic.md'})
            text = (dest / 'topic.md').read_text()
            self.assertIn('title: "Тема"', text)
            self.assertIn('(topic.md#what-is-context)', (dest / 'index.md').read_text())
            self.assertIn('tags: [test]', text)
            self.assertNotIn('\n# Тема\n', text)
            snapshot = {p.name: p.read_bytes() for p in dest.iterdir()}
            self.assertEqual(run().returncode, 0)
            self.assertEqual(snapshot, {p.name: p.read_bytes() for p in dest.iterdir()})
            (source / 'topic.md').unlink()
            (source / 'index.md').write_text('# Учебник\n')
            self.assertEqual(run().returncode, 0)
            self.assertFalse((dest / 'topic.md').exists())

    def test_course_sections_keep_numeric_order_in_menu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root / 'source', root / 'content'
            (source / '01-foundations').mkdir(parents=True)
            (source / 'index.md').write_text('# Course\n')
            (source / '01-foundations/index.md').write_text('# Основы\n')
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(dest)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('title: "01. Основы"', (dest / '01-foundations/index.md').read_text())

    def test_broken_link_keeps_existing_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, dest = root / 'source', root / 'content'
            source.mkdir()
            dest.mkdir()
            (dest / 'index.md').write_text('previous version')
            (source / 'index.md').write_text('# Test\n[Missing](missing.md)\n')
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), str(dest)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('missing.md', result.stderr)
            self.assertEqual((dest / 'index.md').read_text(), 'previous version')

if __name__ == '__main__':
    unittest.main()
