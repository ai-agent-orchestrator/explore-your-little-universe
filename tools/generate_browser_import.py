"""Generate a self-contained, model-free graph import for other Neo4j users."""
import json
import re
from pathlib import Path
from urllib.parse import urlencode, quote

ROOT = Path(__file__).resolve().parent.parent


def literal(value):
    if isinstance(value, dict):
        return '{' + ', '.join(key + ': ' + literal(item) for key, item in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ',\n    '.join(literal(item) for item in value) + ']'
    return json.dumps(value, ensure_ascii=False)


def main():
    data = json.loads((ROOT / 'frontend/public/data/graph.json').read_text(encoding='utf-8'))
    groups = [
        ('traits', data['traits'], '''MERGE (t:SharedTrait:MbtiTrait {key: row.id})
    SET t.title=row.title, t.name=row.title'''),
        ('types', data['types'], '''MERGE (m:MbtiType {code: row.code}) SET m.name=row.code
    WITH row, m UNWIND row.traits AS key
    MATCH (t:SharedTrait {key:key}) MERGE (m)-[:HAS_TRAIT]->(t)'''),
        ('signs', data['signs'], '''MERGE (z:ZodiacSign {id:row.id}) SET z.name=row.name, z.is_demo=true
    WITH row, z UNWIND row.traits AS key
    MATCH (t:SharedTrait {key:key}) MERGE (z)-[:HAS_TRAIT]->(t)'''),
        ('chunks', [{key: card.get(key, '') for key in ['id','title','text','category','document_id','document_title','source','traits','tips',
                                                       'kind','subject_kind','subject','facet','source_url','reviewed_on','editorial_note']}
                    for card in data['chunks']], '''MERGE (d:RagDocument {id:row.document_id})
    SET d.title=row.document_title, d.name=row.document_title, d.source=row.source, d.is_demo=true,
        d.source_url=row.source_url, d.reviewed_on=row.reviewed_on
    MERGE (c:RagChunk {id:row.id})
    SET c.title=row.title, c.name=row.title, c.text=row.text, c.category=row.category,
        c.kind=row.kind, c.subject_kind=row.subject_kind, c.subject=row.subject,
        c.facet=row.facet, c.source_url=row.source_url, c.reviewed_on=row.reviewed_on,
        c.editorial_note=row.editorial_note
    MERGE (c)-[:FROM_DOCUMENT]->(d)
    WITH row, c UNWIND row.traits AS key
    MATCH (t:SharedTrait {key:key}) MERGE (t)-[:FROM_CHUNK]->(c)'''),
        ('suggestions', data['suggestions'], '''MERGE (i:RagTip {id:row.id}) SET i.text=row.text, i.name=row.text
    WITH row, i MATCH (t:SharedTrait {key:row.trait}) MERGE (t)-[:SUGGESTS]->(i)'''),
        ('evidence', [{'id':c['id'],'tips':c['tips']} for c in data['chunks']], '''MATCH (c:RagChunk {id:row.id})
    WITH row, c UNWIND row.tips AS key
    MATCH (i:RagTip {id:key}) MERGE (i)-[:FROM_CHUNK]->(c)'''),
        ('mbti_profiles', [{'id':c['id'],'subject':c['subject']} for c in data['chunks'] if c.get('subject_kind') == 'mbti'],
         '''MATCH (m:MbtiType {code:row.subject}), (c:RagChunk {id:row.id})
    MERGE (m)-[:DESCRIBED_BY]->(c)'''),
        ('zodiac_profiles', [{'id':c['id'],'subject':c['subject']} for c in data['chunks'] if c.get('subject_kind') == 'zodiac'],
         '''MATCH (z:ZodiacSign {id:row.subject}), (c:RagChunk {id:row.id})
    MERGE (z)-[:DESCRIBED_BY]->(c)'''),
    ]
    parts = ['// Lumi editorial learning graph. Source-informed paraphrases and original fictional applications.',
             '// No password, model, embedding vectors, APOC or Python required.',
             '// Select your own learning database in Neo4j Browser, paste this ENTIRE file, then Run.',
             '// Does not delete data. Sequential re-runs reuse stable IDs; use a dedicated lab database.']
    for name, rows, query in groups:
        parts.append('CALL () {\n    UNWIND ' + literal(rows) + ' AS row\n    ' + query
                     + '\n    RETURN count(*) AS imported_' + name + '\n}')
    parts.append('RETURN ' + ', '.join('imported_' + name for name, _, _ in groups) + ';\n')
    (ROOT / 'cypher/lumi_graph_only_seed.cypher').write_text('\n'.join(parts), encoding='utf-8')
    graph_query = (ROOT / 'cypher/lumi_all_graph.cypher').read_text(encoding='utf-8')
    graph_query = '\n'.join(line for line in graph_query.splitlines() if not line.startswith('//'))
    link = 'http://localhost:7474/browser/?' + urlencode({'cmd':'edit','arg':graph_query}, quote_via=quote)
    (ROOT / 'docs/NEO4J_BROWSER_LINK.txt').write_text(link + '\n', encoding='utf-8')
    for relative in ['README.md','README.en.md','docs/OPEN_IN_NEO4J.md']:
        path = ROOT / relative
        if path.is_file():
            content = path.read_text(encoding='utf-8').replace('NEO4J_BROWSER_GRAPH_LINK',link)
            content = re.sub(r'http://localhost:7474/browser/\?[^)\s]+', lambda _: link, content)
            path.write_text(content,encoding='utf-8')
    print('Generated graph-only import and password-free Browser query link')


if __name__ == '__main__':
    main()
