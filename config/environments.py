"""
Environment configuration management for Cibozer
Provides validation, templating, and management of environment configurations
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class EnvironmentType(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class EnvironmentVariable:
    """Environment variable configuration"""
    name: str
    description: str
    required: bool = True
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None
    sensitive: bool = False
    environment_specific: bool = False
    
    def validate(self, value: str) -> Tuple[bool, str]:
        """Validate environment variable value"""
        if not value and self.required and not self.default_value:
            return False, f"Required environment variable {self.name} is not set"
        
        if self.validation_pattern and value:
            import re
            if not re.match(self.validation_pattern, value):
                return False, f"Environment variable {self.name} does not match required pattern"
        
        return True, ""


class EnvironmentManager:
    """Manages environment configurations and validation"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.env_variables = self._define_environment_variables()
    
    def _define_environment_variables(self) -> Dict[str, EnvironmentVariable]:
        """Define all environment variables used by Cibozer"""
        variables = {
            # Core Flask Configuration
            'SECRET_KEY': EnvironmentVariable(
                name='SECRET_KEY',
                description='Flask secret key for session security',
                required=True,
                validation_pattern=r'^.{32,}$',  # At least 32 characters
                sensitive=True
            ),
            'FLASK_ENV': EnvironmentVariable(
                name='FLASK_ENV',
                description='Flask environment mode',
                required=True,
                default_value='production',
                validation_pattern=r'^(development|staging|production|testing)$'
            ),
            'DEBUG': EnvironmentVariable(
                name='DEBUG',
                description='Enable debug mode',
                required=False,
                default_value='false',
                validation_pattern=r'^(true|false)$'
            ),
            
            # Database Configuration
            'DATABASE_URL': EnvironmentVariable(
                name='DATABASE_URL',
                description='Database connection URL',
                required=True,
                validation_pattern=r'^postgresql://.*',
                sensitive=True
            ),
            'DB_POOL_SIZE': EnvironmentVariable(
                name='DB_POOL_SIZE',
                description='Database connection pool size',
                required=False,
                default_value='10',
                validation_pattern=r'^\d+$'
            ),
            'DB_MAX_OVERFLOW': EnvironmentVariable(
                name='DB_MAX_OVERFLOW',
                description='Database connection pool overflow',
                required=False,
                default_value='20',
                validation_pattern=r'^\d+$'
            ),
            
            # Cache Configuration
            'REDIS_URL': EnvironmentVariable(
                name='REDIS_URL',
                description='Redis connection URL for caching',
                required=False,
                validation_pattern=r'^redis://.*'
            ),
            'CACHE_DEFAULT_TIMEOUT': EnvironmentVariable(
                name='CACHE_DEFAULT_TIMEOUT',
                description='Default cache timeout in seconds',
                required=False,
                default_value='300',
                validation_pattern=r'^\d+$'
            ),
            
            # Email Configuration
            'MAIL_SERVER': EnvironmentVariable(
                name='MAIL_SERVER',
                description='SMTP server hostname',
                required=False,
                default_value='smtp.sendgrid.net'
            ),
            'MAIL_PORT': EnvironmentVariable(
                name='MAIL_PORT',
                description='SMTP server port',
                required=False,
                default_value='587',
                validation_pattern=r'^\d+$'
            ),
            'MAIL_USERNAME': EnvironmentVariable(
                name='MAIL_USERNAME',
                description='SMTP username',
                required=False,
                default_value='apikey'
            ),
            'MAIL_PASSWORD': EnvironmentVariable(
                name='MAIL_PASSWORD',
                description='SMTP password (SendGrid API key)',
                required=False,
                sensitive=True
            ),
            'MAIL_USE_TLS': EnvironmentVariable(
                name='MAIL_USE_TLS',
                description='Use TLS for email',
                required=False,
                default_value='true',
                validation_pattern=r'^(true|false)$'
            ),
            
            # Stripe Configuration
            'STRIPE_PUBLISHABLE_KEY': EnvironmentVariable(
                name='STRIPE_PUBLISHABLE_KEY',
                description='Stripe publishable key',
                required=True,
                validation_pattern=r'^pk_.*',
                environment_specific=True
            ),
            'STRIPE_SECRET_KEY': EnvironmentVariable(
                name='STRIPE_SECRET_KEY',
                description='Stripe secret key',
                required=True,
                validation_pattern=r'^sk_.*',
                sensitive=True,
                environment_specific=True
            ),
            'STRIPE_WEBHOOK_SECRET': EnvironmentVariable(
                name='STRIPE_WEBHOOK_SECRET',
                description='Stripe webhook endpoint secret',
                required=False,
                validation_pattern=r'^whsec_.*',
                sensitive=True
            ),
            'STRIPE_PRICE_ID_PRO': EnvironmentVariable(
                name='STRIPE_PRICE_ID_PRO',
                description='Stripe price ID for Pro subscription',
                required=False,
                validation_pattern=r'^price_.*'
            ),
            'STRIPE_PRICE_ID_PREMIUM': EnvironmentVariable(
                name='STRIPE_PRICE_ID_PREMIUM',
                description='Stripe price ID for Premium subscription',
                required=False,
                validation_pattern=r'^price_.*'
            ),
            
            # OpenAI Configuration
            'OPENAI_API_KEY': EnvironmentVariable(
                name='OPENAI_API_KEY',
                description='OpenAI API key for meal generation',
                required=False,
                validation_pattern=r'^sk-.*',
                sensitive=True
            ),
            
            # Security Configuration
            'SESSION_COOKIE_SECURE': EnvironmentVariable(
                name='SESSION_COOKIE_SECURE',
                description='Secure session cookies (HTTPS only)',
                required=False,
                default_value='true',
                validation_pattern=r'^(true|false)$'
            ),
            'SESSION_COOKIE_HTTPONLY': EnvironmentVariable(
                name='SESSION_COOKIE_HTTPONLY',
                description='HTTP-only session cookies',
                required=False,
                default_value='true',
                validation_pattern=r'^(true|false)$'
            ),
            'SESSION_COOKIE_SAMESITE': EnvironmentVariable(
                name='SESSION_COOKIE_SAMESITE',
                description='SameSite attribute for session cookies',
                required=False,
                default_value='Strict',
                validation_pattern=r'^(Strict|Lax|None)$'
            ),
            'WTF_CSRF_SSL_STRICT': EnvironmentVariable(
                name='WTF_CSRF_SSL_STRICT',
                description='Strict CSRF SSL checking',
                required=False,
                default_value='true',
                validation_pattern=r'^(true|false)$'
            ),
            
            # Server Configuration
            'SERVER_NAME': EnvironmentVariable(
                name='SERVER_NAME',
                description='Server name/domain',
                required=False,
                environment_specific=True
            ),
            'PREFERRED_URL_SCHEME': EnvironmentVariable(
                name='PREFERRED_URL_SCHEME',
                description='Preferred URL scheme',
                required=False,
                default_value='https',
                validation_pattern=r'^(http|https)$'
            ),
            'PORT': EnvironmentVariable(
                name='PORT',
                description='Server port',
                required=False,
                default_value='5000',
                validation_pattern=r'^\d+$'
            ),
            
            # SSL Configuration
            'SSL_CERT_PATH': EnvironmentVariable(
                name='SSL_CERT_PATH',
                description='SSL certificate file path',
                required=False
            ),
            'SSL_KEY_PATH': EnvironmentVariable(
                name='SSL_KEY_PATH',
                description='SSL private key file path',
                required=False
            ),
            
            # Monitoring and Logging
            'LOG_LEVEL': EnvironmentVariable(
                name='LOG_LEVEL',
                description='Logging level',
                required=False,
                default_value='INFO',
                validation_pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$'
            ),
            'LOG_TO_STDOUT': EnvironmentVariable(
                name='LOG_TO_STDOUT',
                description='Log to stdout instead of files',
                required=False,
                default_value='false',
                validation_pattern=r'^(true|false)$'
            ),
            'SENTRY_DSN': EnvironmentVariable(
                name='SENTRY_DSN',
                description='Sentry DSN for error tracking',
                required=False,
                sensitive=True
            ),
            
            # Backup Configuration
            'BACKUP_S3_BUCKET': EnvironmentVariable(
                name='BACKUP_S3_BUCKET',
                description='S3 bucket for backups',
                required=False
            ),
            'AWS_ACCESS_KEY_ID': EnvironmentVariable(
                name='AWS_ACCESS_KEY_ID',
                description='AWS access key ID',
                required=False,
                sensitive=True
            ),
            'AWS_SECRET_ACCESS_KEY': EnvironmentVariable(
                name='AWS_SECRET_ACCESS_KEY',
                description='AWS secret access key',
                required=False,
                sensitive=True
            ),
            'AWS_REGION': EnvironmentVariable(
                name='AWS_REGION',
                description='AWS region',
                required=False,
                default_value='us-east-1'
            ),
            
            # Admin Configuration
            'ADMIN_EMAIL': EnvironmentVariable(
                name='ADMIN_EMAIL',
                description='Admin user email',
                required=False,
                validation_pattern=r'^[^@]+@[^@]+\.[^@]+$'
            ),
            'ADMIN_PASSWORD': EnvironmentVariable(
                name='ADMIN_PASSWORD',
                description='Admin user password',
                required=False,
                validation_pattern=r'^.{8,}$',  # At least 8 characters
                sensitive=True
            ),
            
            # Rate Limiting
            'RATELIMIT_STORAGE_URL': EnvironmentVariable(
                name='RATELIMIT_STORAGE_URL',
                description='Rate limiting storage URL',
                required=False,
                default_value='memory://'
            ),
            
            # Asset Management
            'MINIFY_JS': EnvironmentVariable(
                name='MINIFY_JS',
                description='Minify JavaScript assets',
                required=False,
                default_value='true',
                validation_pattern=r'^(true|false)$'
            ),
            'MINIFY_CSS': EnvironmentVariable(
                name='MINIFY_CSS',
                description='Minify CSS assets',
                required=False,
                default_value='true',
                validation_pattern=r'^(true|false)$'
            ),
        }
        
        return variables
    
    def validate_environment(self, environment: EnvironmentType) -> Tuple[bool, List[str], List[str]]:
        """Validate current environment configuration"""
        errors = []
        warnings = []
        
        for var_name, var_config in self.env_variables.items():
            value = os.environ.get(var_name)
            
            # Use default value if not set
            if not value and var_config.default_value:
                value = var_config.default_value
            
            # Validate the value
            is_valid, error_message = var_config.validate(value)
            
            if not is_valid:
                if var_config.required:
                    errors.append(error_message)
                else:
                    warnings.append(error_message)
            
            # Environment-specific validations
            if environment == EnvironmentType.PRODUCTION:
                self._validate_production_specific(var_name, value, errors, warnings)
        
        return len(errors) == 0, errors, warnings
    
    def _validate_production_specific(self, var_name: str, value: str, errors: List[str], warnings: List[str]):
        """Production-specific validations"""
        if var_name == 'DEBUG' and value and value.lower() == 'true':
            errors.append("DEBUG must be false in production")
        
        if var_name == 'SECRET_KEY' and value:
            if len(value) < 32:
                errors.append("SECRET_KEY must be at least 32 characters in production")
            elif value in ['dev-secret-key', 'changeme', 'secret']:
                errors.append("SECRET_KEY must not use default/weak values in production")
        
        if var_name == 'FLASK_ENV' and value != 'production':
            warnings.append("FLASK_ENV should be 'production' in production environment")
        
        if var_name == 'SESSION_COOKIE_SECURE' and value and value.lower() != 'true':
            errors.append("SESSION_COOKIE_SECURE must be true in production")
    
    def generate_env_template(self, environment: EnvironmentType, include_optional: bool = False) -> str:
        """Generate environment template file"""
        template_lines = [
            f"# Cibozer Environment Configuration - {environment.value.title()}",
            f"# Generated on: {os.popen('date').read().strip()}",
            "",
            "# ====================================",
            "# REQUIRED VARIABLES",
            "# ===================================="
        ]
        
        # Group variables by category
        categories = {
            'Core Flask': ['SECRET_KEY', 'FLASK_ENV', 'DEBUG'],
            'Database': ['DATABASE_URL', 'DB_POOL_SIZE', 'DB_MAX_OVERFLOW'],
            'Cache': ['REDIS_URL', 'CACHE_DEFAULT_TIMEOUT'],
            'Email': ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_USE_TLS'],
            'Stripe Payment': ['STRIPE_PUBLISHABLE_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_PRICE_ID_PRO', 'STRIPE_PRICE_ID_PREMIUM'],
            'OpenAI': ['OPENAI_API_KEY'],
            'Security': ['SESSION_COOKIE_SECURE', 'SESSION_COOKIE_HTTPONLY', 'SESSION_COOKIE_SAMESITE', 'WTF_CSRF_SSL_STRICT'],
            'Server': ['SERVER_NAME', 'PREFERRED_URL_SCHEME', 'PORT'],
            'SSL': ['SSL_CERT_PATH', 'SSL_KEY_PATH'],
            'Monitoring': ['LOG_LEVEL', 'LOG_TO_STDOUT', 'SENTRY_DSN'],
            'Backup': ['BACKUP_S3_BUCKET', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION'],
            'Admin': ['ADMIN_EMAIL', 'ADMIN_PASSWORD'],
            'Performance': ['RATELIMIT_STORAGE_URL', 'MINIFY_JS', 'MINIFY_CSS']
        }
        
        for category, var_names in categories.items():
            template_lines.extend([
                "",
                f"# {category} Configuration",
                f"# {'-' * (len(category) + 14)}"
            ])
            
            for var_name in var_names:
                if var_name in self.env_variables:
                    var_config = self.env_variables[var_name]
                    
                    # Skip optional variables if not requested
                    if not include_optional and not var_config.required:
                        continue
                    
                    # Add description as comment
                    template_lines.append(f"# {var_config.description}")
                    
                    # Add validation info if present
                    if var_config.validation_pattern:
                        template_lines.append(f"# Pattern: {var_config.validation_pattern}")
                    
                    # Add environment-specific note
                    if var_config.environment_specific:
                        template_lines.append(f"# Environment-specific value required")
                    
                    # Add sensitive data warning
                    if var_config.sensitive:
                        template_lines.append("# ⚠️ SENSITIVE DATA - Keep secure!")
                    
                    # Generate the variable line
                    if var_config.default_value and environment != EnvironmentType.PRODUCTION:
                        template_lines.append(f"{var_name}={var_config.default_value}")
                    else:
                        placeholder = self._get_placeholder_value(var_name, var_config, environment)
                        template_lines.append(f"{var_name}={placeholder}")
                    
                    template_lines.append("")
        
        return "\n".join(template_lines)
    
    def _get_placeholder_value(self, var_name: str, var_config: EnvironmentVariable, environment: EnvironmentType) -> str:
        """Generate placeholder value for environment variable"""
        if var_config.sensitive:
            return "your-secret-value-here"
        
        if var_name == 'DATABASE_URL':
            if environment == EnvironmentType.PRODUCTION:
                return "postgresql://username:password@host:port/database"
            else:
                return "postgresql://cibozer:password@localhost:5432/cibozer_dev"
        
        if var_name == 'REDIS_URL':
            return "redis://localhost:6379/0"
        
        if var_name == 'SERVER_NAME':
            if environment == EnvironmentType.PRODUCTION:
                return "yourdomain.com"
            else:
                return "localhost:5000"
        
        if var_name.endswith('_EMAIL'):
            return "admin@yourdomain.com"
        
        if var_config.default_value:
            return var_config.default_value
        
        return "your-value-here"
    
    def load_environment_config(self, config_file: Path) -> Dict[str, str]:
        """Load environment configuration from file"""
        if not config_file.exists():
            raise FileNotFoundError(f"Environment config file not found: {config_file}")
        
        env_vars = {}
        
        if config_file.suffix == '.json':
            with open(config_file, 'r') as f:
                env_vars = json.load(f)
        elif config_file.suffix in ['.yaml', '.yml']:
            with open(config_file, 'r') as f:
                env_vars = yaml.safe_load(f)
        else:  # .env file
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def export_environment_config(self, environment: EnvironmentType, output_file: Path, format: str = 'env'):
        """Export current environment configuration"""
        config_data = {}
        
        for var_name in self.env_variables:
            value = os.environ.get(var_name)
            if value:
                config_data[var_name] = value
        
        if format == 'json':
            with open(output_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        elif format in ['yaml', 'yml']:
            with open(output_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:  # env format
            with open(output_file, 'w') as f:
                f.write(f"# Cibozer Environment Configuration Export\n")
                f.write(f"# Environment: {environment.value}\n")
                f.write(f"# Exported: {os.popen('date').read().strip()}\n\n")
                
                for var_name, value in sorted(config_data.items()):
                    f.write(f"{var_name}={value}\n")
    
    def compare_environments(self, env1_file: Path, env2_file: Path) -> Dict[str, Any]:
        """Compare two environment configurations"""
        env1_config = self.load_environment_config(env1_file)
        env2_config = self.load_environment_config(env2_file)
        
        all_keys = set(env1_config.keys()) | set(env2_config.keys())
        
        comparison = {
            'common': {},
            'env1_only': {},
            'env2_only': {},
            'different': {},
            'summary': {
                'total_vars': len(all_keys),
                'common_vars': 0,
                'env1_only_vars': 0,
                'env2_only_vars': 0,
                'different_vars': 0
            }
        }
        
        for key in all_keys:
            env1_value = env1_config.get(key)
            env2_value = env2_config.get(key)
            
            if env1_value and env2_value:
                if env1_value == env2_value:
                    comparison['common'][key] = env1_value
                    comparison['summary']['common_vars'] += 1
                else:
                    comparison['different'][key] = {
                        'env1': env1_value,
                        'env2': env2_value
                    }
                    comparison['summary']['different_vars'] += 1
            elif env1_value:
                comparison['env1_only'][key] = env1_value
                comparison['summary']['env1_only_vars'] += 1
            else:
                comparison['env2_only'][key] = env2_value
                comparison['summary']['env2_only_vars'] += 1
        
        return comparison


def main():
    """CLI interface for environment management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cibozer Environment Management')
    parser.add_argument('command', choices=['validate', 'template', 'export', 'compare'])
    parser.add_argument('--environment', choices=['development', 'staging', 'production', 'testing'],
                       default='production', help='Target environment')
    parser.add_argument('--include-optional', action='store_true',
                       help='Include optional variables in template')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['env', 'json', 'yaml'], default='env',
                       help='Output format')
    parser.add_argument('--compare-with', help='File to compare with (for compare command)')
    
    args = parser.parse_args()
    
    manager = EnvironmentManager()
    environment = EnvironmentType(args.environment)
    
    if args.command == 'validate':
        is_valid, errors, warnings = manager.validate_environment(environment)
        
        if warnings:
            print("⚠️ Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
            print()
        
        if errors:
            print("❌ Errors:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print("✅ Environment validation passed!")
            return 0
    
    elif args.command == 'template':
        template = manager.generate_env_template(environment, args.include_optional)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(template)
            print(f"✅ Environment template saved to {args.output}")
        else:
            print(template)
    
    elif args.command == 'export':
        if not args.output:
            print("❌ Output file required for export command")
            return 1
        
        output_path = Path(args.output)
        manager.export_environment_config(environment, output_path, args.format)
        print(f"✅ Environment configuration exported to {args.output}")
    
    elif args.command == 'compare':
        if not args.output or not args.compare_with:
            print("❌ Both --output and --compare-with required for compare command")
            return 1
        
        comparison = manager.compare_environments(Path(args.output), Path(args.compare_with))
        
        print("📊 Environment Comparison Summary:")
        print(f"  Total variables: {comparison['summary']['total_vars']}")
        print(f"  Common variables: {comparison['summary']['common_vars']}")
        print(f"  Different values: {comparison['summary']['different_vars']}")
        print(f"  File 1 only: {comparison['summary']['env1_only_vars']}")
        print(f"  File 2 only: {comparison['summary']['env2_only_vars']}")
        
        if comparison['different']:
            print("\n🔄 Different Values:")
            for key, values in comparison['different'].items():
                print(f"  {key}:")
                print(f"    File 1: {values['env1']}")
                print(f"    File 2: {values['env2']}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())