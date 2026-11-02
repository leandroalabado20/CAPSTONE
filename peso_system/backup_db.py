"""Run manually or via cron to create a dated backup of peso.db."""
import shutil, pathlib, datetime

BASE = pathlib.Path(__file__).parent
DB   = BASE / 'peso.db'
DEST = BASE / 'backups'
DEST.mkdir(exist_ok=True)

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
out   = DEST / f'peso_{stamp}.db'
shutil.copy2(DB, out)
print(f'Backup saved: {out}')
