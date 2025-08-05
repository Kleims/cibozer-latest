#!/usr/bin/env python3
"""
Production Secrets Management System
Secure handling of environment variables and secrets for Cibozer
"""

import os
import json
import base64
import hashlib
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argparse
import getpass
import subprocess


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


@dataclass
class SecretEntry:
    """Represents a secret entry"""
    name: str
    value: str
    description: str = ""
    environment: str = "production"
    sensitive: bool = True
    created_at: str = ""
    updated_at: str = ""


class SecretsManager:
    """Manages encrypted secrets for production deployment"""
    
    def __init__(self, secrets_file: Path = None):
        self.root_dir = Path(__file__).parent.parent
        self.secrets_file = secrets_file or self.root_dir / "secrets" / "encrypted_secrets.json"
        self.key_file = self.root_dir / "secrets" / ".secret_key"
        self.ensure_secrets_directory()
    
    def ensure_secrets_directory(self):
        """Ensure secrets directory exists with proper permissions"""
        secrets_dir = self.secrets_file.parent
        secrets_dir.mkdir(exist_ok=True, parents=True)
        
        # Set restrictive permissions on Unix systems
        if os.name != 'nt':  # Not Windows
            os.chmod(secrets_dir, 0o700)
    
    def generate_key(self, password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode())), salt
    
    def get_encryption_key(self, password: str = None) -> Fernet:
        """Get or create encryption key"""
        if password is None:
            password = getpass.getpass("Enter master password: ")
        
        if self.key_file.exists():
            # Load existing key data
            with open(self.key_file, 'rb') as f:
                key_data = json.loads(f.read().decode())
            
            salt = base64.b64decode(key_data['salt'])
            key, _ = self.generate_key(password, salt)
            
            # Verify password is correct
            try:
                fernet = Fernet(key)
                test_encrypted = base64.b64decode(key_data['test'])
                fernet.decrypt(test_encrypted)
                return fernet
            except Exception:
                raise ValueError("Invalid password")
        else:
            # Create new key
            key, salt = self.generate_key(password)
            fernet = Fernet(key)
            
            # Create test encrypted data to verify password later
            test_data = fernet.encrypt(b"test")
            
            key_data = {
                'salt': base64.b64encode(salt).decode(),
                'test': base64.b64encode(test_data).decode()
            }
            
            with open(self.key_file, 'wb') as f:
                f.write(json.dumps(key_data).encode())
            
            # Set restrictive permissions
            if os.name != 'nt':
                os.chmod(self.key_file, 0o600)
            
            return fernet
    
    def encrypt_secret(self, value: str, password: str = None) -> str:
        """Encrypt a secret value"""
        fernet = self.get_encryption_key(password)
        encrypted_data = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_secret(self, encrypted_value: str, password: str = None) -> str:
        """Decrypt a secret value"""
        fernet = self.get_encryption_key(password)
        encrypted_data = base64.b64decode(encrypted_value.encode())
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode()
    
    def store_secret(self, name: str, value: str, description: str = "", 
                    environment: str = "production", password: str = None):
        """Store a secret securely"""
        encrypted_value = self.encrypt_secret(value, password)
        
        # Load existing secrets
        secrets = self.load_secrets(password)
        
        # Create or update secret entry
        from datetime import datetime
        now = datetime.now().isoformat()
        
        secrets[name] = {
            'name': name,
            'value': encrypted_value,
            'description': description,
            'environment': environment,
            'sensitive': True,
            'created_at': secrets.get(name, {}).get('created_at', now),
            'updated_at': now
        }
        
        # Save secrets
        self.save_secrets(secrets, password)
        print(f"{Colors.GREEN}✅ Secret '{name}' stored successfully{Colors.END}")
    
    def retrieve_secret(self, name: str, password: str = None) -> Optional[str]:
        """Retrieve and decrypt a secret"""
        secrets = self.load_secrets(password)
        
        if name not in secrets:
            print(f"{Colors.RED}❌ Secret '{name}' not found{Colors.END}")
            return None
        
        secret_data = secrets[name]
        decrypted_value = self.decrypt_secret(secret_data['value'], password)
        return decrypted_value
    
    def list_secrets(self, password: str = None, environment: str = None) -> List[Dict[str, Any]]:
        """List all secrets (without values)"""
        secrets = self.load_secrets(password)
        
        result = []
        for name, data in secrets.items():
            if environment and data.get('environment') != environment:
                continue
            
            result.append({
                'name': name,
                'description': data.get('description', ''),
                'environment': data.get('environment', 'production'),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', '')
            })
        
        return sorted(result, key=lambda x: x['name'])
    
    def delete_secret(self, name: str, password: str = None):
        """Delete a secret"""
        secrets = self.load_secrets(password)
        
        if name not in secrets:
            print(f"{Colors.RED}❌ Secret '{name}' not found{Colors.END}")
            return False
        
        del secrets[name]
        self.save_secrets(secrets, password)
        print(f"{Colors.GREEN}✅ Secret '{name}' deleted successfully{Colors.END}")
        return True
    
    def load_secrets(self, password: str = None) -> Dict[str, Any]:
        """Load all secrets from encrypted file"""
        if not self.secrets_file.exists():
            return {}
        
        try:
            with open(self.secrets_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.RED}❌ Error loading secrets: {e}{Colors.END}")
            return {}
    
    def save_secrets(self, secrets: Dict[str, Any], password: str = None):
        """Save secrets to encrypted file"""
        try:
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets, f, indent=2)
            
            # Set restrictive permissions
            if os.name != 'nt':
                os.chmod(self.secrets_file, 0o600)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error saving secrets: {e}{Colors.END}")
            raise
    
    def export_secrets_to_env(self, environment: str = "production", 
                             output_file: Path = None, password: str = None):
        """Export secrets as environment variables"""
        secrets = self.load_secrets(password)
        
        if not output_file:
            output_file = self.root_dir / f".env.{environment}"
        
        env_vars = []
        env_vars.append(f"# Cibozer Environment Variables - {environment.title()}")
        env_vars.append(f"# Generated: {os.popen('date').read().strip()}")
        env_vars.append(f"# WARNING: Contains sensitive data - keep secure!")
        env_vars.append("")
        
        for name, data in secrets.items():
            if data.get('environment') != environment:
                continue
            
            try:
                decrypted_value = self.decrypt_secret(data['value'], password)
                description = data.get('description', '')
                
                if description:
                    env_vars.append(f"# {description}")
                
                env_vars.append(f"{name}={decrypted_value}")
                env_vars.append("")
                
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Warning: Could not decrypt {name}: {e}{Colors.END}")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(env_vars))
        
        # Set restrictive permissions
        if os.name != 'nt':
            os.chmod(output_file, 0o600)
        
        print(f"{Colors.GREEN}✅ Secrets exported to {output_file}{Colors.END}")
    
    def import_from_env_file(self, env_file: Path, environment: str = "production", 
                           password: str = None):
        """Import secrets from environment file"""
        if not env_file.exists():
            print(f"{Colors.RED}❌ Environment file not found: {env_file}{Colors.END}")
            return
        
        imported_count = 0
        
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#') or '=' not in line:
                    continue
                
                try:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    if key and value:
                        self.store_secret(
                            name=key,
                            value=value,
                            description=f"Imported from {env_file.name}",
                            environment=environment,
                            password=password
                        )
                        imported_count += 1
                
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️  Warning: Error on line {line_num}: {e}{Colors.END}")
        
        print(f"{Colors.GREEN}✅ Imported {imported_count} secrets from {env_file}{Colors.END}")
    
    def rotate_encryption_key(self, old_password: str = None, new_password: str = None):
        """Rotate the master encryption key"""
        print(f"{Colors.YELLOW}🔄 Rotating encryption key...{Colors.END}")
        
        # Load secrets with old password
        if old_password is None:
            old_password = getpass.getpass("Enter current master password: ")
        
        try:
            secrets = self.load_secrets(old_password)
            
            # Decrypt all secrets with old key
            decrypted_secrets = {}
            for name, data in secrets.items():
                decrypted_value = self.decrypt_secret(data['value'], old_password)
                decrypted_secrets[name] = {**data, 'value': decrypted_value}
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error with current password: {e}{Colors.END}")
            return False
        
        # Get new password
        if new_password is None:
            new_password = getpass.getpass("Enter new master password: ")
            confirm_password = getpass.getpass("Confirm new master password: ")
            
            if new_password != confirm_password:
                print(f"{Colors.RED}❌ Passwords do not match{Colors.END}")
                return False
        
        # Backup old key file
        backup_key_file = self.key_file.with_suffix('.backup')
        if self.key_file.exists():
            self.key_file.rename(backup_key_file)
        
        try:
            # Generate new key
            new_fernet = self.get_encryption_key(new_password)
            
            # Re-encrypt all secrets with new key
            for name, data in decrypted_secrets.items():
                encrypted_value = self.encrypt_secret(data['value'], new_password)
                secrets[name]['value'] = encrypted_value
                secrets[name]['updated_at'] = datetime.now().isoformat()
            
            # Save with new encryption
            self.save_secrets(secrets, new_password)
            
            # Remove backup
            if backup_key_file.exists():
                backup_key_file.unlink()
            
            print(f"{Colors.GREEN}✅ Encryption key rotated successfully{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error rotating key: {e}{Colors.END}")
            
            # Restore backup
            if backup_key_file.exists():
                backup_key_file.rename(self.key_file)
            
            return False
    
    def generate_strong_secret(self, length: int = 32) -> str:
        """Generate a cryptographically strong secret"""
        return secrets.token_urlsafe(length)
    
    def validate_secret_strength(self, secret_value: str) -> Tuple[bool, List[str]]:
        """Validate secret strength"""
        issues = []
        
        if len(secret_value) < 16:
            issues.append("Secret should be at least 16 characters long")
        
        if secret_value.lower() in ['password', 'secret', 'key', 'changeme', 'admin']:
            issues.append("Secret uses common/weak values")
        
        if secret_value == secret_value.lower():
            issues.append("Secret should contain mixed case characters")
        
        if not any(c.isdigit() for c in secret_value):
            issues.append("Secret should contain numbers")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret_value):
            issues.append("Secret should contain special characters")
        
        return len(issues) == 0, issues


def main():
    """CLI interface for secrets management"""
    parser = argparse.ArgumentParser(description='Cibozer Secrets Management')
    parser.add_argument('command', choices=[
        'store', 'retrieve', 'list', 'delete', 'export', 'import', 
        'rotate-key', 'generate', 'validate'
    ])
    parser.add_argument('--name', help='Secret name')
    parser.add_argument('--value', help='Secret value')
    parser.add_argument('--description', help='Secret description')
    parser.add_argument('--environment', default='production', 
                       choices=['development', 'staging', 'production'])
    parser.add_argument('--file', help='File path for import/export')
    parser.add_argument('--length', type=int, default=32, help='Length for generated secrets')
    parser.add_argument('--password', help='Master password (not recommended for CLI)')
    
    args = parser.parse_args()
    
    manager = SecretsManager()
    
    try:
        if args.command == 'store':
            if not args.name:
                args.name = input("Secret name: ")
            
            if not args.value:
                args.value = getpass.getpass("Secret value: ")
            
            if not args.description:
                args.description = input("Description (optional): ")
            
            manager.store_secret(
                name=args.name,
                value=args.value,
                description=args.description,
                environment=args.environment,
                password=args.password
            )
        
        elif args.command == 'retrieve':
            if not args.name:
                args.name = input("Secret name: ")
            
            value = manager.retrieve_secret(args.name, args.password)
            if value:
                print(f"{Colors.GREEN}Secret value: {value}{Colors.END}")
        
        elif args.command == 'list':
            secrets = manager.list_secrets(args.password, args.environment)
            
            print(f"\n{Colors.BOLD}Secrets for environment: {args.environment}{Colors.END}")
            print("=" * 60)
            
            if not secrets:
                print("No secrets found")
            else:
                for secret in secrets:
                    print(f"{Colors.BLUE}{secret['name']}{Colors.END}")
                    if secret['description']:
                        print(f"  Description: {secret['description']}")
                    print(f"  Environment: {secret['environment']}")
                    print(f"  Created: {secret['created_at']}")
                    print(f"  Updated: {secret['updated_at']}")
                    print()
        
        elif args.command == 'delete':
            if not args.name:
                args.name = input("Secret name to delete: ")
            
            confirm = input(f"Delete secret '{args.name}'? (y/N): ")
            if confirm.lower() == 'y':
                manager.delete_secret(args.name, args.password)
        
        elif args.command == 'export':
            output_file = Path(args.file) if args.file else None
            manager.export_secrets_to_env(args.environment, output_file, args.password)
        
        elif args.command == 'import':
            if not args.file:
                args.file = input("Path to environment file: ")
            
            env_file = Path(args.file)
            manager.import_from_env_file(env_file, args.environment, args.password)
        
        elif args.command == 'rotate-key':
            manager.rotate_encryption_key()
        
        elif args.command == 'generate':
            secret = manager.generate_strong_secret(args.length)
            print(f"{Colors.GREEN}Generated secret: {secret}{Colors.END}")
            
            # Optionally store it
            store = input("Store this secret? (y/N): ")
            if store.lower() == 'y':
                name = input("Secret name: ")
                description = input("Description (optional): ")
                manager.store_secret(name, secret, description, args.environment, args.password)
        
        elif args.command == 'validate':
            if not args.value:
                args.value = getpass.getpass("Secret value to validate: ")
            
            is_strong, issues = manager.validate_secret_strength(args.value)
            
            if is_strong:
                print(f"{Colors.GREEN}✅ Secret strength is good{Colors.END}")
            else:
                print(f"{Colors.YELLOW}⚠️  Secret strength issues:{Colors.END}")
                for issue in issues:
                    print(f"  - {issue}")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())