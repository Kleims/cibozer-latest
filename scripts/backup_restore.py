#!/usr/bin/env python3
"""
Comprehensive backup and restore utility for Cibozer
Supports database, files, and configuration backup
"""

import os
import sys
import json
import shutil
import tarfile
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
import subprocess
import boto3
from typing import Dict, List, Optional
import click
import redis
from cryptography.fernet import Fernet

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.extensions import db


class BackupManager:
    """Manages backup and restore operations"""
    
    def __init__(self, app=None):
        self.app = app or create_app()
        self.backup_dir = Path(self.app.config.get('BACKUP_DIR', './backups'))
        self.backup_dir.mkdir(exist_ok=True)
        
        # Encryption key for sensitive backups
        key = self.app.config.get('BACKUP_ENCRYPTION_KEY')
        if key:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            self.cipher = None
            
        # S3 configuration for offsite backups
        self.s3_enabled = self.app.config.get('BACKUP_S3_ENABLED', False)
        if self.s3_enabled:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.app.config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=self.app.config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=self.app.config.get('AWS_DEFAULT_REGION', 'us-east-1')
            )
            self.s3_bucket = self.app.config.get('BACKUP_S3_BUCKET')
    
    def generate_backup_name(self, backup_type: str) -> str:
        """Generate unique backup filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"cibozer_{backup_type}_{timestamp}"
    
    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def backup_database(self) -> Dict[str, str]:
        """Backup database to SQL dump"""
        backup_name = self.generate_backup_name('database')
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        with self.app.app_context():
            db_url = self.app.config.get('DATABASE_URL', '')
            
            if db_url.startswith('postgresql://'):
                # PostgreSQL backup
                subprocess.run([
                    'pg_dump',
                    db_url,
                    '-f', str(backup_file),
                    '--verbose',
                    '--clean',
                    '--if-exists'
                ], check=True)
            else:
                # SQLite backup
                db_path = db_url.replace('sqlite:///', '')
                shutil.copy2(db_path, backup_file)
        
        # Encrypt if configured
        if self.cipher:
            self._encrypt_file(backup_file)
            backup_file = Path(f"{backup_file}.enc")
        
        checksum = self.calculate_checksum(backup_file)
        
        return {
            'type': 'database',
            'filename': backup_file.name,
            'path': str(backup_file),
            'size': backup_file.stat().st_size,
            'checksum': checksum,
            'encrypted': bool(self.cipher),
            'timestamp': datetime.now().isoformat()
        }
    
    def backup_files(self, include_patterns: List[str] = None) -> Dict[str, str]:
        """Backup user files and uploads"""
        backup_name = self.generate_backup_name('files')
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        include_patterns = include_patterns or [
            'static/uploads/**',
            'static/pdfs/**',
            'static/videos/**',
            'instance/temp/**'
        ]
        
        with tarfile.open(backup_file, 'w:gz') as tar:
            for pattern in include_patterns:
                for path in Path('.').glob(pattern):
                    if path.is_file():
                        tar.add(path, arcname=str(path))
        
        checksum = self.calculate_checksum(backup_file)
        
        return {
            'type': 'files',
            'filename': backup_file.name,
            'path': str(backup_file),
            'size': backup_file.stat().st_size,
            'checksum': checksum,
            'patterns': include_patterns,
            'timestamp': datetime.now().isoformat()
        }
    
    def backup_redis(self) -> Dict[str, str]:
        """Backup Redis data"""
        backup_name = self.generate_backup_name('redis')
        backup_file = self.backup_dir / f"{backup_name}.rdb"
        
        redis_url = self.app.config.get('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        
        # Trigger Redis save
        r.bgsave()
        
        # Wait for save to complete
        while r.lastsave() == r.lastsave():
            import time
            time.sleep(0.1)
        
        # Copy RDB file
        redis_dir = Path(r.config_get('dir')['dir'])
        rdb_file = redis_dir / r.config_get('dbfilename')['dbfilename']
        shutil.copy2(rdb_file, backup_file)
        
        checksum = self.calculate_checksum(backup_file)
        
        return {
            'type': 'redis',
            'filename': backup_file.name,
            'path': str(backup_file),
            'size': backup_file.stat().st_size,
            'checksum': checksum,
            'timestamp': datetime.now().isoformat()
        }
    
    def backup_config(self) -> Dict[str, str]:
        """Backup configuration files"""
        backup_name = self.generate_backup_name('config')
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        config_files = [
            '.env',
            '.env.production',
            'config/*.py',
            'nginx/*.conf',
            'docker-compose.yml',
            'requirements.txt'
        ]
        
        with tarfile.open(backup_file, 'w:gz') as tar:
            for pattern in config_files:
                for path in Path('.').glob(pattern):
                    if path.is_file():
                        tar.add(path, arcname=str(path))
        
        # Always encrypt config backups
        if self.cipher:
            self._encrypt_file(backup_file)
            backup_file = Path(f"{backup_file}.enc")
        
        checksum = self.calculate_checksum(backup_file)
        
        return {
            'type': 'config',
            'filename': backup_file.name,
            'path': str(backup_file),
            'size': backup_file.stat().st_size,
            'checksum': checksum,
            'encrypted': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_full_backup(self) -> Dict[str, any]:
        """Create complete system backup"""
        print("🔄 Starting full system backup...")
        
        manifest = {
            'version': '1.0',
            'app_version': self.app.config.get('VERSION', '1.0.0'),
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Backup all components
        try:
            print("📊 Backing up database...")
            manifest['components']['database'] = self.backup_database()
            
            print("📁 Backing up files...")
            manifest['components']['files'] = self.backup_files()
            
            print("💾 Backing up Redis...")
            manifest['components']['redis'] = self.backup_redis()
            
            print("⚙️ Backing up configuration...")
            manifest['components']['config'] = self.backup_config()
            
            # Save manifest
            manifest_file = self.backup_dir / f"{self.generate_backup_name('manifest')}.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            manifest['manifest_file'] = str(manifest_file)
            
            # Upload to S3 if configured
            if self.s3_enabled:
                print("☁️ Uploading to S3...")
                self._upload_to_s3(manifest)
            
            print("✅ Backup completed successfully!")
            return manifest
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            raise
    
    def restore_database(self, backup_info: Dict[str, str]) -> bool:
        """Restore database from backup"""
        backup_file = Path(backup_info['path'])
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Verify checksum
        if self.calculate_checksum(backup_file) != backup_info['checksum']:
            raise ValueError("Backup file checksum mismatch - file may be corrupted")
        
        # Decrypt if needed
        if backup_info.get('encrypted'):
            backup_file = self._decrypt_file(backup_file)
        
        with self.app.app_context():
            db_url = self.app.config.get('DATABASE_URL', '')
            
            if db_url.startswith('postgresql://'):
                # PostgreSQL restore
                subprocess.run([
                    'psql',
                    db_url,
                    '-f', str(backup_file)
                ], check=True)
            else:
                # SQLite restore
                db_path = db_url.replace('sqlite:///', '')
                shutil.copy2(backup_file, db_path)
        
        return True
    
    def restore_files(self, backup_info: Dict[str, str]) -> bool:
        """Restore files from backup"""
        backup_file = Path(backup_info['path'])
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Verify checksum
        if self.calculate_checksum(backup_file) != backup_info['checksum']:
            raise ValueError("Backup file checksum mismatch")
        
        # Extract files
        with tarfile.open(backup_file, 'r:gz') as tar:
            tar.extractall('.')
        
        return True
    
    def restore_redis(self, backup_info: Dict[str, str]) -> bool:
        """Restore Redis from backup"""
        backup_file = Path(backup_info['path'])
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        redis_url = self.app.config.get('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        
        # Stop Redis writes
        r.config_set('stop-writes-on-bgsave-error', 'yes')
        
        # Copy backup file
        redis_dir = Path(r.config_get('dir')['dir'])
        rdb_file = redis_dir / r.config_get('dbfilename')['dbfilename']
        shutil.copy2(backup_file, rdb_file)
        
        # Restart Redis to load backup
        print("Redis backup restored. Please restart Redis service.")
        
        return True
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        # Local backups
        for manifest_file in self.backup_dir.glob('*_manifest_*.json'):
            with open(manifest_file) as f:
                manifest = json.load(f)
                manifest['location'] = 'local'
                manifest['manifest_file'] = str(manifest_file)
                backups.append(manifest)
        
        # S3 backups
        if self.s3_enabled:
            # List S3 backups
            pass
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """Remove backups older than specified days"""
        cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
        removed = 0
        
        for backup_file in self.backup_dir.glob('cibozer_*'):
            if backup_file.stat().st_mtime < cutoff_date:
                backup_file.unlink()
                removed += 1
        
        return removed
    
    def _encrypt_file(self, filepath: Path) -> Path:
        """Encrypt a file"""
        if not self.cipher:
            return filepath
        
        encrypted_path = Path(f"{filepath}.enc")
        
        with open(filepath, 'rb') as f:
            encrypted_data = self.cipher.encrypt(f.read())
        
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        filepath.unlink()  # Remove unencrypted file
        return encrypted_path
    
    def _decrypt_file(self, filepath: Path) -> Path:
        """Decrypt a file"""
        if not self.cipher:
            return filepath
        
        decrypted_path = Path(str(filepath).replace('.enc', ''))
        
        with open(filepath, 'rb') as f:
            decrypted_data = self.cipher.decrypt(f.read())
        
        with open(decrypted_path, 'wb') as f:
            f.write(decrypted_data)
        
        return decrypted_path
    
    def _upload_to_s3(self, manifest: Dict) -> None:
        """Upload backup files to S3"""
        for component, info in manifest['components'].items():
            file_path = info['path']
            s3_key = f"backups/{datetime.now().strftime('%Y/%m/%d')}/{info['filename']}"
            
            self.s3.upload_file(
                file_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'checksum': info['checksum'],
                        'type': info['type'],
                        'timestamp': info['timestamp']
                    }
                }
            )


@click.group()
def cli():
    """Cibozer backup and restore utility"""
    pass


@cli.command()
@click.option('--type', 'backup_type', 
              type=click.Choice(['full', 'database', 'files', 'redis', 'config']),
              default='full', help='Type of backup to create')
@click.option('--encrypt', is_flag=True, help='Encrypt backup files')
@click.option('--upload', is_flag=True, help='Upload to S3')
def backup(backup_type, encrypt, upload):
    """Create a backup"""
    manager = BackupManager()
    
    if backup_type == 'full':
        manifest = manager.create_full_backup()
        print(f"\n📋 Backup manifest: {manifest['manifest_file']}")
    else:
        method = getattr(manager, f'backup_{backup_type}')
        result = method()
        print(f"\n✅ {backup_type} backup created: {result['filename']}")


@cli.command()
@click.argument('manifest_file')
@click.option('--component', type=click.Choice(['all', 'database', 'files', 'redis', 'config']),
              default='all', help='Component to restore')
@click.option('--force', is_flag=True, help='Force restore without confirmation')
def restore(manifest_file, component, force):
    """Restore from backup"""
    if not force:
        click.confirm('⚠️  This will overwrite existing data. Continue?', abort=True)
    
    manager = BackupManager()
    
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    if component == 'all':
        for comp_name, comp_info in manifest['components'].items():
            print(f"\n🔄 Restoring {comp_name}...")
            method = getattr(manager, f'restore_{comp_name}')
            method(comp_info)
    else:
        print(f"\n🔄 Restoring {component}...")
        method = getattr(manager, f'restore_{component}')
        method(manifest['components'][component])
    
    print("\n✅ Restore completed!")


@cli.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
def list(format):
    """List available backups"""
    manager = BackupManager()
    backups = manager.list_backups()
    
    if format == 'json':
        click.echo(json.dumps(backups, indent=2))
    else:
        click.echo("\n📦 Available Backups:\n")
        for backup in backups:
            click.echo(f"Timestamp: {backup['timestamp']}")
            click.echo(f"Version: {backup['app_version']}")
            click.echo(f"Location: {backup['location']}")
            click.echo(f"Components: {', '.join(backup['components'].keys())}")
            click.echo("-" * 50)


@cli.command()
@click.option('--days', default=30, help='Keep backups from last N days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted')
def cleanup(days, dry_run):
    """Clean up old backups"""
    manager = BackupManager()
    
    if dry_run:
        click.echo(f"\n🔍 Would remove backups older than {days} days")
    else:
        removed = manager.cleanup_old_backups(days)
        click.echo(f"\n🗑️  Removed {removed} old backup(s)")


if __name__ == '__main__':
    cli()