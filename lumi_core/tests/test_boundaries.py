import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
class BoundaryTests(unittest.TestCase):
    def test_labs_depend_on_core_only(self):
        for package, forbidden in [('lumi_core', {'mbti_lab','tarot_lab'}), ('tarot_lab', {'mbti_lab'})]:
            for path in (ROOT/package).rglob('*.py'):
                for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                    modules = [alias.name for alias in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
                    for module in modules:
                        self.assertNotIn(module.split('.')[0], forbidden, str(path))

    def test_shared_embedding_has_no_graph_adapter_dependency(self):
        text=(ROOT/'lumi_core/embedding/litert.py').read_text(encoding='utf-8')
        self.assertNotIn('neo4j_graphrag',text)
