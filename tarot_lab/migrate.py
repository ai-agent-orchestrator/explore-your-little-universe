"""python -m tarot_lab.migrate; migrations and checkpoint schema are separate."""
from pathlib import Path
from lumi_core.settings import postgres

def migrate(dsn=None):
    import psycopg
    with psycopg.connect(dsn or postgres()) as connection:
        connection.execute('CREATE SCHEMA IF NOT EXISTS lumi')
        connection.execute('CREATE TABLE IF NOT EXISTS lumi.schema_migrations (name text PRIMARY KEY, applied_at timestamptz DEFAULT now())')
        connection.execute("SELECT pg_advisory_xact_lock(hashtext('lumi-migrations'))")
        for path in sorted((Path(__file__).parent/'migrations').glob('*.sql')):
            if connection.execute('SELECT 1 FROM lumi.schema_migrations WHERE name=%s',(path.name,)).fetchone():
                continue
            connection.execute(path.read_text(encoding='utf-8'))
            connection.execute('INSERT INTO lumi.schema_migrations(name) VALUES (%s)',(path.name,))
    print('Lumi service schema migrations applied')

if __name__=='__main__': migrate()
