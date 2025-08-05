#!/usr/bin/env python3
"""
Comprehensive database backup and recovery system for Cibozer
Supports automated backups, restoration, and integrity verification
"""

import os
import sys
import json
import gzip
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from flask import current_app


class DatabaseBackupManager:
    """Comprehensive database backup and recovery manager."""
    
    def __init__(self, app=None):
        self.app = app or create_app()
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup retention settings
        self.retention_policy = {
            'daily': 30,    # Keep 30 daily backups
            'weekly': 12,   # Keep 12 weekly backups  
            'monthly': 12   # Keep 12 monthly backups
        }
        
    def get_database_info(self) -> Dict:
        """Get database connection information."""
        with self.app.app_context():
            db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
            
            if db_url.startswith('sqlite:'):
                return {
                    'type': 'sqlite',
                    'path': db_url.replace('sqlite:///', '').replace('sqlite://', ''),
                    'url': db_url
                }
            elif db_url.startswith('postgresql:'):
                # Parse PostgreSQL URL
                from urllib.parse import urlparse
                parsed = urlparse(db_url)
                return {
                    'type': 'postgresql',
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'database': parsed.path[1:],  # Remove leading /
                    'username': parsed.username,
                    'password': parsed.password,
                    'url': db_url
                }
            elif db_url.startswith('mysql:'):
                # Parse MySQL URL
                from urllib.parse import urlparse
                parsed = urlparse(db_url)
                return {
                    'type': 'mysql',
                    'host': parsed.hostname,
                    'port': parsed.port or 3306,
                    'database': parsed.path[1:],  # Remove leading /
                    'username': parsed.username,
                    'password': parsed.password,
                    'url': db_url
                }
            else:
                raise ValueError(f"Unsupported database type: {db_url}")
    
    def create_backup(self, backup_type: str = 'manual', compress: bool = True) -> Dict:
        """Create a database backup."""
        timestamp = datetime.now(timezone.utc)
        backup_name = f"cibozer_backup_{backup_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            db_info = self.get_database_info()
            
            if db_info['type'] == 'sqlite':
                result = self._backup_sqlite(db_info, backup_name, compress)
            elif db_info['type'] == 'postgresql':
                result = self._backup_postgresql(db_info, backup_name, compress)
            elif db_info['type'] == 'mysql':
                result = self._backup_mysql(db_info, backup_name, compress)
            else:
                raise ValueError(f"Backup not supported for {db_info['type']}")
            
            # Create metadata
            metadata = {
                'backup_name': backup_name,
                'backup_type': backup_type,
                'database_type': db_info['type'],
                'created_at': timestamp.isoformat(),
                'file_path': str(result['file_path']),
                'file_size': result['file_size'],
                'compressed': compress,
                'integrity_hash': result.get('hash'),
                'app_version': '1.0.0'  # Could be dynamic
            }
            
            # Save metadata
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            result['metadata'] = metadata
            print(f"✅ Backup created successfully: {backup_name}")
            return result
            
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            raise
    
    def _backup_sqlite(self, db_info: Dict, backup_name: str, compress: bool) -> Dict:
        """Create SQLite backup."""
        source_path = Path(db_info['path'])
        if not source_path.exists():
            raise FileNotFoundError(f"Database file not found: {source_path}")
        
        # Create backup using SQLite's backup API for consistency
        backup_path = self.backup_dir / f"{backup_name}.db"
        
        # Use SQLite's online backup
        source_conn = sqlite3.connect(str(source_path))
        backup_conn = sqlite3.connect(str(backup_path))
        
        try:
            source_conn.backup(backup_conn)
        finally:
            source_conn.close()
            backup_conn.close()
        
        # Compress if requested
        if compress:
            compressed_path = self.backup_dir / f"{backup_name}.db.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed version
            backup_path.unlink()
            final_path = compressed_path
        else:
            final_path = backup_path
        
        return {
            'file_path': final_path,
            'file_size': final_path.stat().st_size,
            'hash': self._calculate_file_hash(final_path)
        }
    
    def _backup_postgresql(self, db_info: Dict, backup_name: str, compress: bool) -> Dict:
        """Create PostgreSQL backup using pg_dump."""
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            f"--host={db_info['host']}",
            f"--port={db_info['port']}",
            f"--username={db_info['username']}",
            '--no-password',
            '--verbose',
            '--clean',
            '--no-acl',
            '--no-owner',
            db_info['database']
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_info['password']
        
        # Execute pg_dump
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, 
                                  env=env, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
        
        # Compress if requested
        if compress:
            compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_path.unlink()
            final_path = compressed_path
        else:
            final_path = backup_path
        
        return {
            'file_path': final_path,
            'file_size': final_path.stat().st_size,
            'hash': self._calculate_file_hash(final_path)
        }
    
    def _backup_mysql(self, db_info: Dict, backup_name: str, compress: bool) -> Dict:
        """Create MySQL backup using mysqldump."""
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        # Build mysqldump command
        cmd = [
            'mysqldump',
            f"--host={db_info['host']}",
            f"--port={db_info['port']}",
            f"--user={db_info['username']}",
            f"--password={db_info['password']}",
            '--single-transaction',
            '--routines',
            '--triggers',
            '--add-drop-table',
            db_info['database']
        ]
        
        # Execute mysqldump
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise Exception(f"mysqldump failed: {result.stderr}")
        
        # Compress if requested
        if compress:
            compressed_path = self.backup_dir / f"{backup_name}.sql.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_path.unlink()
            final_path = compressed_path
        else:
            final_path = backup_path
        
        return {
            'file_path': final_path,
            'file_size': final_path.stat().st_size,
            'hash': self._calculate_file_hash(final_path)
        }
    
    def restore_backup(self, backup_name: str, confirm: bool = False) -> Dict:
        """Restore database from backup."""
        if not confirm:
            raise ValueError("Restoration requires explicit confirmation (confirm=True)")
        
        # Load metadata
        metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Backup metadata not found: {metadata_path}")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        backup_file = Path(metadata['file_path'])
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        try:
            db_info = self.get_database_info()
            
            if db_info['type'] != metadata['database_type']:
                raise ValueError(f"Database type mismatch: current={db_info['type']}, backup={metadata['database_type']}")
            
            # Verify backup integrity
            if not self._verify_backup_integrity(backup_file, metadata.get('integrity_hash')):
                raise ValueError("Backup integrity verification failed")
            
            if db_info['type'] == 'sqlite':
                result = self._restore_sqlite(db_info, backup_file, metadata)
            elif db_info['type'] == 'postgresql':
                result = self._restore_postgresql(db_info, backup_file, metadata)
            elif db_info['type'] == 'mysql':
                result = self._restore_mysql(db_info, backup_file, metadata)
            else:
                raise ValueError(f"Restore not supported for {db_info['type']}")
            
            print(f"✅ Database restored successfully from: {backup_name}")
            return result
            
        except Exception as e:
            print(f"❌ Restoration failed: {str(e)}")
            raise
    
    def _restore_sqlite(self, db_info: Dict, backup_file: Path, metadata: Dict) -> Dict:
        """Restore SQLite database."""
        current_db = Path(db_info['path'])
        
        # Create backup of current database
        if current_db.exists():
            backup_current = current_db.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2(current_db, backup_current)
        
        # Decompress if needed
        if metadata.get('compressed'):
            temp_file = backup_file.with_suffix('')
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            restore_file = temp_file
        else:
            restore_file = backup_file
        
        # Replace current database
        shutil.copy2(restore_file, current_db)
        
        # Cleanup temp file if created
        if metadata.get('compressed'):
            temp_file.unlink()
        
        return {'status': 'success', 'restored_from': str(backup_file)}
    
    def _restore_postgresql(self, db_info: Dict, backup_file: Path, metadata: Dict) -> Dict:
        """Restore PostgreSQL database."""
        # Decompress if needed
        if metadata.get('compressed'):
            temp_file = backup_file.with_suffix('')
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            restore_file = temp_file
        else:
            restore_file = backup_file
        
        # Build psql command
        cmd = [
            'psql',
            f"--host={db_info['host']}",
            f"--port={db_info['port']}",
            f"--username={db_info['username']}",
            '--no-password',
            '--quiet',
            db_info['database']
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_info['password']
        
        # Execute restoration
        with open(restore_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, 
                                  env=env, text=True)
        
        # Cleanup temp file if created
        if metadata.get('compressed'):
            temp_file.unlink()
        
        if result.returncode != 0:
            raise Exception(f"psql restore failed: {result.stderr}")
        
        return {'status': 'success', 'restored_from': str(backup_file)}
    
    def _restore_mysql(self, db_info: Dict, backup_file: Path, metadata: Dict) -> Dict:
        """Restore MySQL database."""
        # Decompress if needed
        if metadata.get('compressed'):
            temp_file = backup_file.with_suffix('')
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            restore_file = temp_file
        else:
            restore_file = backup_file
        
        # Build mysql command
        cmd = [
            'mysql',
            f"--host={db_info['host']}",
            f"--port={db_info['port']}",
            f"--user={db_info['username']}",
            f"--password={db_info['password']}",
            db_info['database']
        ]
        
        # Execute restoration
        with open(restore_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        # Cleanup temp file if created
        if metadata.get('compressed'):
            temp_file.unlink()
        
        if result.returncode != 0:
            raise Exception(f"mysql restore failed: {result.stderr}")
        
        return {'status': 'success', 'restored_from': str(backup_file)}
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []
        
        for metadata_file in self.backup_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check if backup file still exists
                backup_file = Path(metadata['file_path'])
                metadata['file_exists'] = backup_file.exists()
                metadata['file_size_mb'] = round(metadata['file_size'] / (1024 * 1024), 2)
                
                backups.append(metadata)
            except Exception as e:
                print(f"Warning: Could not read metadata from {metadata_file}: {e}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def cleanup_old_backups(self) -> Dict:
        """Clean up old backups according to retention policy."""
        backups = self.list_backups()
        now = datetime.now(timezone.utc)
        deleted_count = 0
        deleted_size = 0
        
        for backup in backups:
            created_at = datetime.fromisoformat(backup['created_at'].replace('Z', '+00:00'))
            age_days = (now - created_at).days
            backup_type = backup['backup_type']
            
            should_delete = False
            
            if backup_type == 'daily' and age_days > self.retention_policy['daily']:
                should_delete = True
            elif backup_type == 'weekly' and age_days > self.retention_policy['weekly'] * 7:
                should_delete = True
            elif backup_type == 'monthly' and age_days > self.retention_policy['monthly'] * 30:
                should_delete = True
            
            if should_delete:
                try:
                    # Delete backup file
                    backup_file = Path(backup['file_path'])
                    if backup_file.exists():
                        deleted_size += backup_file.stat().st_size
                        backup_file.unlink()
                    
                    # Delete metadata file
                    metadata_file = self.backup_dir / f"{backup['backup_name']}_metadata.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    deleted_count += 1
                    print(f"Deleted old backup: {backup['backup_name']}")
                    
                except Exception as e:
                    print(f"Failed to delete backup {backup['backup_name']}: {e}")
        
        return {
            'deleted_count': deleted_count,
            'freed_space_mb': round(deleted_size / (1024 * 1024), 2),
            'remaining_backups': len(backups) - deleted_count
        }
    
    def verify_backup(self, backup_name: str) -> Dict:
        """Verify backup integrity."""
        metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
        if not metadata_path.exists():
            return {'valid': False, 'error': 'Metadata file not found'}
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            backup_file = Path(metadata['file_path'])
            if not backup_file.exists():
                return {'valid': False, 'error': 'Backup file not found'}
            
            # Verify file size
            current_size = backup_file.stat().st_size
            if current_size != metadata['file_size']:
                return {'valid': False, 'error': f'File size mismatch: expected {metadata["file_size"]}, got {current_size}'}
            
            # Verify hash if available
            if metadata.get('integrity_hash'):
                current_hash = self._calculate_file_hash(backup_file)
                if current_hash != metadata['integrity_hash']:
                    return {'valid': False, 'error': 'Integrity hash mismatch'}
            
            return {
                'valid': True,
                'backup_name': backup_name,
                'file_size': current_size,
                'created_at': metadata['created_at']
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _verify_backup_integrity(self, backup_file: Path, expected_hash: Optional[str]) -> bool:
        """Verify backup file integrity."""
        if not expected_hash:
            return True  # No hash to verify
        
        current_hash = self._calculate_file_hash(backup_file)
        return current_hash == expected_hash


def main():
    """CLI interface for backup management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cibozer Database Backup Manager')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'verify', 'cleanup'],
                       help='Action to perform')
    parser.add_argument('--backup-name', help='Backup name for restore/verify operations')
    parser.add_argument('--type', default='manual', choices=['manual', 'daily', 'weekly', 'monthly'],
                       help='Backup type')
    parser.add_argument('--no-compress', action='store_true',
                       help='Skip compression')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirm destructive operations')
    
    args = parser.parse_args()
    
    manager = DatabaseBackupManager()
    
    try:
        if args.action == 'backup':
            result = manager.create_backup(args.type, compress=not args.no_compress)
            print(f"Backup created: {result['metadata']['backup_name']}")
            print(f"File size: {result['metadata']['file_size_mb']} MB")
        
        elif args.action == 'restore':
            if not args.backup_name:
                print("Error: --backup-name required for restore")
                sys.exit(1)
            
            if not args.confirm:
                print("Error: --confirm required for restore operation")
                sys.exit(1)
            
            manager.restore_backup(args.backup_name, confirm=True)
        
        elif args.action == 'list':
            backups = manager.list_backups()
            if not backups:
                print("No backups found")
            else:
                print(f"{'Name':<40} {'Type':<10} {'Size (MB)':<10} {'Created':<20} {'Status':<10}")
                print("-" * 100)
                for backup in backups:
                    status = "OK" if backup['file_exists'] else "MISSING"
                    created = backup['created_at'][:19].replace('T', ' ')
                    print(f"{backup['backup_name']:<40} {backup['backup_type']:<10} "
                          f"{backup['file_size_mb']:<10} {created:<20} {status:<10}")
        
        elif args.action == 'verify':
            if not args.backup_name:
                print("Error: --backup-name required for verify")
                sys.exit(1)
            
            result = manager.verify_backup(args.backup_name)
            if result['valid']:
                print(f"✅ Backup {args.backup_name} is valid")
            else:
                print(f"❌ Backup {args.backup_name} is invalid: {result['error']}")
                sys.exit(1)
        
        elif args.action == 'cleanup':
            result = manager.cleanup_old_backups()
            print(f"Deleted {result['deleted_count']} old backups")
            print(f"Freed {result['freed_space_mb']} MB of space")
            print(f"{result['remaining_backups']} backups remaining")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()