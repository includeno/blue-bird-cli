import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.check_distribution import check


class DistributionTest(unittest.TestCase):
    def test_missing_artifacts_and_native_resources_fail_before_tests(self):
        with tempfile.TemporaryDirectory() as directory, patch('scripts.check_distribution.subprocess.run') as run:
            root=Path(directory)
            with self.assertRaisesRegex(ValueError,'one wheel'):check(root)
            (root/'source.tar.gz').touch()
            with zipfile.ZipFile(root/'package.whl','w') as archive:
                archive.writestr('bluebird_cli/__init__.py','')
            with self.assertRaisesRegex(ValueError,'Wheel missing native/ax.swift'):check(root)
            run.assert_not_called()

    def test_source_archive_cannot_escape_extraction_directory(self):
        with tempfile.TemporaryDirectory() as directory, patch('scripts.check_distribution.subprocess.run') as run:
            root=Path(directory)
            with zipfile.ZipFile(root/'package.whl','w') as archive:
                for name in ('native/ax.swift','web_assets/index.html','web_assets/app.js','web_assets/style.css'):
                    archive.writestr('bluebird_cli/'+name,'')
            with tarfile.open(root/'source.tar.gz','w:gz') as archive:
                member=tarfile.TarInfo('../escape')
                member.size=1
                archive.addfile(member,io.BytesIO(b'x'))
            with self.assertRaisesRegex(ValueError,'escapes extraction directory'):check(root)
            run.assert_not_called()


if __name__=='__main__':unittest.main()
