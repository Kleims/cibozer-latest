#!/usr/bin/env python3
"""
Production Backup and Disaster Recovery System
Comprehensive backup management for Cibozer
"""

import os
import sys
import json
import gzip
import shutil
import hashlib
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import argparse
import psycopg2
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


@dataclass
class BackupMetadata:
    """Backup metadata information"""
    backup_id: str
    backup_type: str
    timestamp: str
    size_bytes: int
    checksum: str
    database_name: str
    table_count: int
    record_count: int
    compression: str
    encryption: bool
    storage_location: str
    retention_until: str
    backup_duration: float
    status: str = "completed"
    error_message: str = ""


class BackupManager:
    """Manages production backups and disaster recovery"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.backup_dir = self.root_dir / "backups"
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.config_file = self.root_dir / "config" / "backup_config.json"
        self.ensure_backup_directory()
        self.config = self.load_config()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists with proper permissions"""
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Set restrictive permissions on Unix systems
        if os.name != 'nt':
            os.chmod(self.backup_dir, 0o700)
    
    def load_config(self) -> Dict[str, Any]:
        """Load backup configuration"""
        default_config = {
            "retention_policy": {
                "daily_backups": 7,
                "weekly_backups": 4,
                "monthly_backups": 12
            },
            "compression": {
                "enabled": True,
                "algorithm": "gzip",
                "level": 6
            },
            "encryption": {
                "enabled": False,
                "key_file": "backup_encryption_key"
            },
            "storage": {
                "local": True,
                "s3": {
                    "enabled": False,
                    "bucket": "",
                    "prefix": "cibozer-backups/",
                    "region": "us-east-1"
                }
            },
            "notifications": {
                "enabled": False,
                "webhook_url": "",
                "email": ""
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Warning: Could not load config, using defaults: {e}{Colors.END}")
        
        return default_config
    
    def save_config(self):
        """Save backup configuration"""
        self.config_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        return f"backup_{timestamp}_{random_suffix}"
    
    def get_database_connection(self, database_url: str = None):
        """Get database connection"""
        if not database_url:
            database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL not provided")
        
        return psycopg2.connect(database_url)
    
    def create_database_backup(self, database_url: str = None, 
                             backup_type: str = "full") -> BackupMetadata:
        """Create database backup"""
        start_time = datetime.now()
        backup_id = self.generate_backup_id()
        
        print(f"{Colors.BLUE}🗄️  Creating {backup_type} database backup: {backup_id}{Colors.END}")
        
        try:
            if not database_url:
                database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                raise ValueError("DATABASE_URL not provided")
            
            # Parse database URL
            parsed = urlparse(database_url)
            db_name = parsed.path.lstrip('/')
            
            # Create backup file path
            backup_filename = f"{backup_id}_database.sql"
            if self.config["compression"]["enabled"]:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            # Create pg_dump command
            dump_command = [
                "pg_dump",
                database_url,
                "--verbose",
                "--no-password",
                "--format=custom",
                "--compress=9" if not self.config["compression"]["enabled"] else "--compress=0"
            ]
            
            if backup_type == "schema_only":
                dump_command.append("--schema-only")
            elif backup_type == "data_only":
                dump_command.append("--data-only")
            
            # Execute backup
            with open(backup_path, 'wb') as f:
                if self.config["compression"]["enabled"]:
                    # Use gzip compression
                    process = subprocess.Popen(dump_command, stdout=subprocess.PIPE)
                    with gzip.GzipFile(fileobj=f, mode='wb', 
                                     compresslevel=self.config["compression"]["level"]) as gz_file:
                        shutil.copyfileobj(process.stdout, gz_file)
                    process.wait()
                else:
                    subprocess.run(dump_command, stdout=f, check=True)
            
            # Calculate file size and checksum
            file_size = backup_path.stat().st_size
            checksum = self.calculate_checksum(backup_path)
            
            # Get database statistics
            conn = self.get_database_connection(database_url)
            cursor = conn.cursor()
            
            # Count tables
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0]
            
            # Estimate record count (approximate)
            cursor.execute("""
                SELECT SUM(n_tup_ins + n_tup_upd + n_tup_del) 
                FROM pg_stat_user_tables
            """)
            result = cursor.fetchone()
            record_count = result[0] if result and result[0] else 0
            
            conn.close()
            
            # Calculate retention date
            retention_days = self.config["retention_policy"]["daily_backups"]
            retention_until = (datetime.now() + timedelta(days=retention_days)).isoformat()
            
            # Create metadata
            backup_duration = (datetime.now() - start_time).total_seconds()
            
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=start_time.isoformat(),
                size_bytes=file_size,
                checksum=checksum,
                database_name=db_name,
                table_count=table_count,
                record_count=record_count,
                compression="gzip" if self.config["compression"]["enabled"] else "none",
                encryption=self.config["encryption"]["enabled"],
                storage_location=str(backup_path),
                retention_until=retention_until,
                backup_duration=backup_duration,
                status="completed"
            )
            
            # Save metadata
            self.save_backup_metadata(metadata)
            
            # Upload to S3 if configured
            if self.config["storage"]["s3"]["enabled"]:
                self.upload_to_s3(backup_path, backup_id)
            
            print(f"{Colors.GREEN}✅ Database backup completed: {backup_id}{Colors.END}")
            print(f"   Size: {self.format_size(file_size)}")
            print(f"   Tables: {table_count}")
            print(f"   Duration: {backup_duration:.2f}s")
            
            return metadata
            
        except Exception as e:
            error_metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=start_time.isoformat(),
                size_bytes=0,
                checksum="",
                database_name=db_name if 'db_name' in locals() else "unknown",
                table_count=0,
                record_count=0,
                compression="none",
                encryption=False,
                storage_location="",
                retention_until="",
                backup_duration=(datetime.now() - start_time).total_seconds(),
                status="failed",
                error_message=str(e)
            )
            
            self.save_backup_metadata(error_metadata)
            print(f"{Colors.RED}❌ Database backup failed: {e}{Colors.END}")
            raise
    
    def create_application_backup(self) -> BackupMetadata:
        """Create application files backup"""
        start_time = datetime.now()
        backup_id = self.generate_backup_id()
        
        print(f"{Colors.BLUE}📦 Creating application backup: {backup_id}{Colors.END}")
        
        try:
            # Files to backup
            backup_items = [
                "app/",
                "static/",
                "templates/",
                "config/",
                "requirements.txt",
                "wsgi.py",
                "Dockerfile",
                "docker-compose.yml",
                "nginx/",
                ".env.example"
            ]
            
            # Create backup archive
            backup_filename = f"{backup_id}_application.tar"
            if self.config["compression"]["enabled"]:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            # Create tar command
            tar_command = ["tar"]
            if self.config["compression"]["enabled"]:
                tar_command.extend(["-czf", str(backup_path)])
            else:
                tar_command.extend(["-cf", str(backup_path)])
            
            # Add files that exist
            existing_items = []
            for item in backup_items:
                item_path = self.root_dir / item
                if item_path.exists():
                    existing_items.append(item)
            
            if not existing_items:
                raise ValueError("No application files found to backup")
            
            # Execute backup from project root
            subprocess.run(
                tar_command + existing_items,
                cwd=self.root_dir,
                check=True
            )
            
            # Calculate file size and checksum
            file_size = backup_path.stat().st_size
            checksum = self.calculate_checksum(backup_path)
            
            # Calculate retention date
            retention_days = self.config["retention_policy"]["daily_backups"]
            retention_until = (datetime.now() + timedelta(days=retention_days)).isoformat()
            
            # Create metadata
            backup_duration = (datetime.now() - start_time).total_seconds()
            
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type="application",
                timestamp=start_time.isoformat(),
                size_bytes=file_size,
                checksum=checksum,
                database_name="N/A",
                table_count=0,
                record_count=len(existing_items),
                compression="gzip" if self.config["compression"]["enabled"] else "none",
                encryption=self.config["encryption"]["enabled"],
                storage_location=str(backup_path),
                retention_until=retention_until,
                backup_duration=backup_duration,
                status="completed"
            )
            
            # Save metadata
            self.save_backup_metadata(metadata)
            
            # Upload to S3 if configured
            if self.config["storage"]["s3"]["enabled"]:
                self.upload_to_s3(backup_path, backup_id)
            
            print(f"{Colors.GREEN}✅ Application backup completed: {backup_id}{Colors.END}")
            print(f"   Size: {self.format_size(file_size)}")
            print(f"   Files: {len(existing_items)}")
            print(f"   Duration: {backup_duration:.2f}s")
            
            return metadata
            
        except Exception as e:
            print(f"{Colors.RED}❌ Application backup failed: {e}{Colors.END}")
            raise
    
    def restore_database_backup(self, backup_id: str, database_url: str = None, 
                              target_database: str = None):
        """Restore database from backup"""
        print(f"{Colors.BLUE}🔄 Restoring database backup: {backup_id}{Colors.END}")
        
        try:
            # Find backup metadata
            metadata = self.get_backup_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup {backup_id} not found")
            
            backup_path = Path(metadata["storage_location"])
            if not backup_path.exists():
                # Try to download from S3
                if self.config["storage"]["s3"]["enabled"]:
                    backup_path = self.download_from_s3(backup_id)
                else:
                    raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            if not database_url:
                database_url = os.environ.get('DATABASE_URL')
            
            if not database_url:
                raise ValueError("DATABASE_URL not provided")
            
            # Create restore command
            restore_command = ["pg_restore", "--verbose", "--clean", "--if-exists"]
            
            if target_database:
                # Parse URL and replace database name
                parsed = urlparse(database_url)
                new_url = database_url.replace(parsed.path, f"/{target_database}")
                restore_command.extend(["--dbname", new_url])
            else:
                restore_command.extend(["--dbname", database_url])
            
            # Handle compressed files
            if backup_path.suffix == '.gz':
                # Decompress first
                with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
                    with gzip.open(backup_path, 'rb') as gz_file:
                        shutil.copyfileobj(gz_file, temp_file)
                    restore_command.append(temp_file.name)
            else:
                restore_command.append(str(backup_path))
            
            # Execute restore
            result = subprocess.run(restore_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ Database restore completed successfully{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠️  Restore completed with warnings:{Colors.END}")
                if result.stderr:
                    print(result.stderr)
            
            # Clean up temporary file
            if backup_path.suffix == '.gz' and 'temp_file' in locals():
                os.unlink(temp_file.name)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Database restore failed: {e}{Colors.END}")
            raise
    
    def list_backups(self, backup_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List available backups"""
        metadata_list = self.load_all_backup_metadata()
        
        # Filter by type if specified
        if backup_type:
            metadata_list = [m for m in metadata_list if m.get("backup_type") == backup_type]
        
        # Sort by timestamp (newest first)
        metadata_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit results
        return metadata_list[:limit]
    
    def cleanup_old_backups(self):
        """Clean up old backups according to retention policy"""
        print(f"{Colors.BLUE}🧹 Cleaning up old backups...{Colors.END}")
        
        metadata_list = self.load_all_backup_metadata()
        now = datetime.now()
        deleted_count = 0
        
        for metadata in metadata_list:
            try:
                retention_until = datetime.fromisoformat(metadata.get("retention_until", ""))
                
                if now > retention_until:
                    backup_id = metadata["backup_id"]
                    backup_path = Path(metadata["storage_location"])
                    
                    # Delete local file
                    if backup_path.exists():
                        backup_path.unlink()
                        print(f"   Deleted local backup: {backup_id}")
                    
                    # Delete from S3 if configured
                    if self.config["storage"]["s3"]["enabled"]:
                        self.delete_from_s3(backup_id)
                    
                    # Remove from metadata
                    self.remove_backup_metadata(backup_id)
                    deleted_count += 1
                    
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Warning: Could not clean up backup {metadata.get('backup_id')}: {e}{Colors.END}")
        
        print(f"{Colors.GREEN}✅ Cleaned up {deleted_count} old backups{Colors.END}")
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify backup file integrity"""
        print(f"{Colors.BLUE}🔍 Verifying backup integrity: {backup_id}{Colors.END}")
        
        try:
            metadata = self.get_backup_metadata(backup_id)
            if not metadata:
                print(f"{Colors.RED}❌ Backup metadata not found{Colors.END}")
                return False
            
            backup_path = Path(metadata["storage_location"])
            if not backup_path.exists():
                print(f"{Colors.RED}❌ Backup file not found: {backup_path}{Colors.END}")
                return False
            
            # Verify checksum
            current_checksum = self.calculate_checksum(backup_path)
            expected_checksum = metadata["checksum"]
            
            if current_checksum != expected_checksum:
                print(f"{Colors.RED}❌ Checksum mismatch:{Colors.END}")
                print(f"   Expected: {expected_checksum}")
                print(f"   Current:  {current_checksum}")
                return False
            
            # Verify file size
            current_size = backup_path.stat().st_size
            expected_size = metadata["size_bytes"]
            
            if current_size != expected_size:
                print(f"{Colors.RED}❌ File size mismatch:{Colors.END}")
                print(f"   Expected: {self.format_size(expected_size)}")
                print(f"   Current:  {self.format_size(current_size)}")
                return False
            
            # Test file readability
            try:
                if backup_path.suffix == '.gz':
                    with gzip.open(backup_path, 'rb') as f:
                        f.read(1024)  # Read first chunk
                else:
                    with open(backup_path, 'rb') as f:
                        f.read(1024)  # Read first chunk
            except Exception as e:
                print(f"{Colors.RED}❌ Backup file is corrupted: {e}{Colors.END}")
                return False
            
            print(f"{Colors.GREEN}✅ Backup integrity verified{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Integrity verification failed: {e}{Colors.END}")
            return False
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata"""
        metadata_list = self.load_all_backup_metadata()
        metadata_list.append(asdict(metadata))
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_list, f, indent=2)
    
    def load_all_backup_metadata(self) -> List[Dict[str, Any]]:
        """Load all backup metadata"""
        if not self.metadata_file.exists():
            return []
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: Could not load metadata: {e}{Colors.END}")
            return []
    
    def get_backup_metadata(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for specific backup"""
        metadata_list = self.load_all_backup_metadata()
        for metadata in metadata_list:
            if metadata.get("backup_id") == backup_id:
                return metadata
        return None
    
    def remove_backup_metadata(self, backup_id: str):
        """Remove backup metadata"""
        metadata_list = self.load_all_backup_metadata()
        metadata_list = [m for m in metadata_list if m.get("backup_id") != backup_id]
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_list, f, indent=2)
    
    def upload_to_s3(self, file_path: Path, backup_id: str):
        """Upload backup to S3"""
        if not self.config["storage"]["s3"]["enabled"]:
            return
        
        try:
            s3_client = boto3.client('s3')
            bucket = self.config["storage"]["s3"]["bucket"]
            prefix = self.config["storage"]["s3"]["prefix"]
            key = f"{prefix}{backup_id}/{file_path.name}"
            
            s3_client.upload_file(str(file_path), bucket, key)
            print(f"{Colors.GREEN}✅ Uploaded to S3: s3://{bucket}/{key}{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: S3 upload failed: {e}{Colors.END}")
    
    def download_from_s3(self, backup_id: str) -> Path:
        """Download backup from S3"""
        if not self.config["storage"]["s3"]["enabled"]:
            raise ValueError("S3 storage not configured")
        
        try:
            s3_client = boto3.client('s3')
            bucket = self.config["storage"]["s3"]["bucket"]
            prefix = self.config["storage"]["s3"]["prefix"]
            
            # List objects with backup_id prefix
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=f"{prefix}{backup_id}/"
            )
            
            if 'Contents' not in response or len(response['Contents']) == 0:
                raise FileNotFoundError(f"Backup {backup_id} not found in S3")
            
            # Download the backup file
            s3_object = response['Contents'][0]
            key = s3_object['Key']
            filename = Path(key).name
            local_path = self.backup_dir / filename
            
            s3_client.download_file(bucket, key, str(local_path))
            print(f"{Colors.GREEN}✅ Downloaded from S3: {filename}{Colors.END}")
            
            return local_path
            
        except Exception as e:
            print(f"{Colors.RED}❌ S3 download failed: {e}{Colors.END}")
            raise
    
    def delete_from_s3(self, backup_id: str):
        """Delete backup from S3"""
        if not self.config["storage"]["s3"]["enabled"]:
            return
        
        try:
            s3_client = boto3.client('s3')
            bucket = self.config["storage"]["s3"]["bucket"]
            prefix = self.config["storage"]["s3"]["prefix"]
            
            # List and delete all objects with backup_id prefix
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=f"{prefix}{backup_id}/"
            )
            
            if 'Contents' in response:
                delete_objects = [{'Key': obj['Key']} for obj in response['Contents']]
                s3_client.delete_objects(
                    Bucket=bucket,
                    Delete={'Objects': delete_objects}
                )
                print(f"   Deleted from S3: {backup_id}")
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Warning: S3 deletion failed: {e}{Colors.END}")


def main():
    """CLI interface for backup management"""
    parser = argparse.ArgumentParser(description='Cibozer Backup Management')
    parser.add_argument('command', choices=[
        'create', 'restore', 'list', 'verify', 'cleanup', 'config'
    ])
    
    # Create command options
    parser.add_argument('--type', choices=['database', 'application', 'full'],
                       default='database', help='Backup type')
    parser.add_argument('--database-url', help='Database URL for backup/restore')
    
    # Restore command options
    parser.add_argument('--backup-id', help='Backup ID to restore')
    parser.add_argument('--target-database', help='Target database name for restore')
    
    # List command options
    parser.add_argument('--limit', type=int, default=50, help='Limit number of results')
    
    # General options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    try:
        if args.command == 'create':
            if args.type in ['database', 'full']:
                manager.create_database_backup(args.database_url)
            
            if args.type in ['application', 'full']:
                manager.create_application_backup()
            
            print(f"{Colors.GREEN}✅ Backup creation completed{Colors.END}")
        
        elif args.command == 'restore':
            if not args.backup_id:
                print(f"{Colors.RED}❌ Backup ID required for restore{Colors.END}")
                return 1
            
            manager.restore_database_backup(
                args.backup_id,
                args.database_url,
                args.target_database
            )
        
        elif args.command == 'list':
            backups = manager.list_backups(limit=args.limit)
            
            if not backups:
                print("No backups found")
                return 0
            
            print(f"\n{Colors.BOLD}Available Backups:{Colors.END}")
            print("=" * 80)
            
            for backup in backups:
                status_color = Colors.GREEN if backup.get("status") == "completed" else Colors.RED
                print(f"{Colors.BLUE}{backup.get('backup_id')}{Colors.END}")
                print(f"  Type: {backup.get('backup_type')}")
                print(f"  Status: {status_color}{backup.get('status', 'unknown')}{Colors.END}")
                print(f"  Timestamp: {backup.get('timestamp')}")
                print(f"  Size: {manager.format_size(backup.get('size_bytes', 0))}")
                print(f"  Database: {backup.get('database_name')}")
                if backup.get('error_message'):
                    print(f"  Error: {Colors.RED}{backup.get('error_message')}{Colors.END}")
                print()
        
        elif args.command == 'verify':
            if not args.backup_id:
                print(f"{Colors.RED}❌ Backup ID required for verification{Colors.END}")
                return 1
            
            if manager.verify_backup_integrity(args.backup_id):
                return 0
            else:
                return 1
        
        elif args.command == 'cleanup':
            manager.cleanup_old_backups()
        
        elif args.command == 'config':
            print(f"\n{Colors.BOLD}Current Backup Configuration:{Colors.END}")
            print("=" * 40)
            print(json.dumps(manager.config, indent=2))
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled{Colors.END}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())