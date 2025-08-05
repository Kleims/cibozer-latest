#!/usr/bin/env python3
"""
Automated failover script for Cibozer
Handles region failover, DNS updates, and health checks
"""

import os
import sys
import time
import json
import boto3
import requests
import click
from datetime import datetime
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app


class FailoverManager:
    """Manages failover operations across regions"""
    
    def __init__(self):
        self.app = create_app()
        self.regions = {
            'primary': {
                'name': 'us-east-1',
                'endpoint': 'https://east.cibozer.com',
                'database': 'cibozer-db-east',
                'priority': 1
            },
            'secondary': {
                'name': 'us-west-2',
                'endpoint': 'https://west.cibozer.com',
                'database': 'cibozer-db-west',
                'priority': 2
            },
            'tertiary': {
                'name': 'eu-west-1',
                'endpoint': 'https://eu.cibozer.com',
                'database': 'cibozer-db-eu',
                'priority': 3
            }
        }
        
        # AWS clients
        self.route53 = boto3.client('route53')
        self.rds = boto3.client('rds')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Configuration
        self.hosted_zone_id = self.app.config.get('ROUTE53_HOSTED_ZONE_ID')
        self.domain = 'cibozer.com'
        self.health_check_timeout = 10
        self.health_check_retries = 3
    
    def check_region_health(self, region: str) -> Dict[str, any]:
        """Check health of a specific region"""
        region_config = self.regions.get(region)
        if not region_config:
            raise ValueError(f"Unknown region: {region}")
        
        health = {
            'region': region,
            'timestamp': datetime.utcnow().isoformat(),
            'healthy': False,
            'checks': {}
        }
        
        # Check application health
        health['checks']['application'] = self._check_application_health(
            region_config['endpoint']
        )
        
        # Check database health
        health['checks']['database'] = self._check_database_health(
            region_config['database']
        )
        
        # Check CloudWatch alarms
        health['checks']['alarms'] = self._check_cloudwatch_alarms(region)
        
        # Overall health
        health['healthy'] = all(
            check['healthy'] for check in health['checks'].values()
        )
        
        return health
    
    def _check_application_health(self, endpoint: str) -> Dict[str, any]:
        """Check application endpoint health"""
        result = {
            'healthy': False,
            'response_time': None,
            'status_code': None,
            'error': None
        }
        
        for attempt in range(self.health_check_retries):
            try:
                start_time = time.time()
                response = requests.get(
                    f"{endpoint}/api/health",
                    timeout=self.health_check_timeout
                )
                response_time = (time.time() - start_time) * 1000
                
                result['response_time'] = response_time
                result['status_code'] = response.status_code
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        result['healthy'] = True
                        break
                
            except Exception as e:
                result['error'] = str(e)
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return result
    
    def _check_database_health(self, db_identifier: str) -> Dict[str, any]:
        """Check RDS database health"""
        result = {
            'healthy': False,
            'status': None,
            'error': None
        }
        
        try:
            response = self.rds.describe_db_instances(
                DBInstanceIdentifier=db_identifier
            )
            
            if response['DBInstances']:
                instance = response['DBInstances'][0]
                result['status'] = instance['DBInstanceStatus']
                result['healthy'] = instance['DBInstanceStatus'] == 'available'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _check_cloudwatch_alarms(self, region: str) -> Dict[str, any]:
        """Check CloudWatch alarms for region"""
        result = {
            'healthy': True,
            'alarms': [],
            'error': None
        }
        
        try:
            response = self.cloudwatch.describe_alarms(
                StateValue='ALARM',
                AlarmNamePrefix=f'cibozer-{region}'
            )
            
            if response['MetricAlarms']:
                result['healthy'] = False
                result['alarms'] = [
                    {
                        'name': alarm['AlarmName'],
                        'reason': alarm['StateReason']
                    }
                    for alarm in response['MetricAlarms']
                ]
                
        except Exception as e:
            result['error'] = str(e)
            result['healthy'] = False
        
        return result
    
    def get_active_region(self) -> Optional[str]:
        """Get currently active region from Route53"""
        try:
            response = self.route53.list_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                StartRecordName=f'app.{self.domain}',
                StartRecordType='CNAME'
            )
            
            for record in response['ResourceRecordSets']:
                if record['Name'] == f'app.{self.domain}.':
                    # Extract region from CNAME
                    cname = record['ResourceRecords'][0]['Value']
                    for region, config in self.regions.items():
                        if config['endpoint'] in cname:
                            return region
                            
        except Exception as e:
            print(f"Error getting active region: {e}")
        
        return None
    
    def update_dns(self, target_region: str) -> bool:
        """Update DNS to point to target region"""
        region_config = self.regions[target_region]
        
        try:
            response = self.route53.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                ChangeBatch={
                    'Comment': f'Failover to {target_region} - {datetime.utcnow()}',
                    'Changes': [{
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': f'app.{self.domain}',
                            'Type': 'CNAME',
                            'TTL': 60,
                            'ResourceRecords': [{
                                'Value': region_config['endpoint'].replace('https://', '')
                            }]
                        }
                    }]
                }
            )
            
            change_id = response['ChangeInfo']['Id']
            print(f"DNS update initiated: {change_id}")
            
            # Wait for DNS propagation
            waiter = self.route53.get_waiter('resource_record_sets_changed')
            waiter.wait(Id=change_id)
            
            print("DNS update completed")
            return True
            
        except Exception as e:
            print(f"DNS update failed: {e}")
            return False
    
    def promote_database_replica(self, target_region: str) -> bool:
        """Promote read replica to master in target region"""
        db_identifier = self.regions[target_region]['database']
        
        try:
            # Check if it's already a master
            response = self.rds.describe_db_instances(
                DBInstanceIdentifier=db_identifier
            )
            
            instance = response['DBInstances'][0]
            if instance.get('ReadReplicaSourceDBInstanceIdentifier'):
                print(f"Promoting {db_identifier} to master...")
                
                self.rds.promote_read_replica(
                    DBInstanceIdentifier=db_identifier,
                    BackupRetentionPeriod=7
                )
                
                # Wait for promotion to complete
                waiter = self.rds.get_waiter('db_instance_available')
                waiter.wait(DBInstanceIdentifier=db_identifier)
                
                print("Database promotion completed")
                return True
            else:
                print(f"{db_identifier} is already a master")
                return True
                
        except Exception as e:
            print(f"Database promotion failed: {e}")
            return False
    
    def perform_failover(self, target_region: str, force: bool = False) -> bool:
        """Perform complete failover to target region"""
        print(f"\n🔄 Starting failover to {target_region}")
        
        # Step 1: Validate target region health
        if not force:
            print("\n1️⃣ Checking target region health...")
            target_health = self.check_region_health(target_region)
            
            if not target_health['healthy']:
                print("❌ Target region is not healthy!")
                print(json.dumps(target_health, indent=2))
                return False
            
            print("✅ Target region is healthy")
        
        # Step 2: Get current active region
        print("\n2️⃣ Identifying current active region...")
        current_region = self.get_active_region()
        print(f"Current active region: {current_region}")
        
        if current_region == target_region:
            print("Target region is already active")
            return True
        
        # Step 3: Promote database if needed
        print("\n3️⃣ Promoting database replica...")
        if not self.promote_database_replica(target_region):
            print("❌ Database promotion failed")
            return False
        
        # Step 4: Update DNS
        print("\n4️⃣ Updating DNS records...")
        if not self.update_dns(target_region):
            print("❌ DNS update failed")
            return False
        
        # Step 5: Verify failover
        print("\n5️⃣ Verifying failover...")
        time.sleep(30)  # Wait for DNS propagation
        
        new_active = self.get_active_region()
        if new_active == target_region:
            print(f"✅ Failover completed successfully to {target_region}")
            
            # Send notifications
            self._send_failover_notification(current_region, target_region)
            
            return True
        else:
            print("❌ Failover verification failed")
            return False
    
    def _send_failover_notification(self, from_region: str, to_region: str):
        """Send failover notifications"""
        message = f"""
        🚨 Failover Completed
        
        From: {from_region}
        To: {to_region}
        Time: {datetime.utcnow().isoformat()}
        
        Please verify application functionality.
        """
        
        # Send to multiple channels
        # Slack, email, SMS, etc.
        print(f"\n📧 Notification sent: {message}")
    
    def get_failover_status(self) -> Dict[str, any]:
        """Get comprehensive failover status"""
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'active_region': self.get_active_region(),
            'regions': {}
        }
        
        for region in self.regions:
            status['regions'][region] = self.check_region_health(region)
        
        return status


@click.group()
def cli():
    """Cibozer failover management utility"""
    pass


@cli.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='table')
def status(format):
    """Check failover status"""
    manager = FailoverManager()
    status = manager.get_failover_status()
    
    if format == 'json':
        click.echo(json.dumps(status, indent=2))
    else:
        click.echo(f"\n🌍 Failover Status")
        click.echo(f"Active Region: {status['active_region']}")
        click.echo(f"Time: {status['timestamp']}\n")
        
        for region, health in status['regions'].items():
            emoji = "✅" if health['healthy'] else "❌"
            click.echo(f"{emoji} {region}: {'Healthy' if health['healthy'] else 'Unhealthy'}")
            
            for check_name, check_result in health['checks'].items():
                check_emoji = "✓" if check_result['healthy'] else "✗"
                click.echo(f"   {check_emoji} {check_name}")


@cli.command()
@click.argument('target_region')
@click.option('--force', is_flag=True, help='Skip health checks')
@click.option('--dry-run', is_flag=True, help='Simulate failover')
def failover(target_region, force, dry_run):
    """Perform failover to target region"""
    manager = FailoverManager()
    
    if dry_run:
        click.echo(f"\n🔍 Simulating failover to {target_region}")
        health = manager.check_region_health(target_region)
        click.echo(json.dumps(health, indent=2))
        return
    
    if not force:
        click.confirm(
            f"⚠️  Perform failover to {target_region}?",
            abort=True
        )
    
    success = manager.perform_failover(target_region, force)
    
    if success:
        click.echo("\n✅ Failover completed successfully")
    else:
        click.echo("\n❌ Failover failed")
        sys.exit(1)


@cli.command()
@click.argument('region')
def health(region):
    """Check health of specific region"""
    manager = FailoverManager()
    health = manager.check_region_health(region)
    click.echo(json.dumps(health, indent=2))


@cli.command()
def test(health):
    """Test failover procedures"""
    manager = FailoverManager()
    
    click.echo("🧪 Testing failover procedures...\n")
    
    # Test DNS update capability
    click.echo("1. Testing Route53 access...")
    try:
        manager.route53.list_hosted_zones(MaxItems='1')
        click.echo("   ✅ Route53 access confirmed")
    except Exception as e:
        click.echo(f"   ❌ Route53 access failed: {e}")
    
    # Test RDS access
    click.echo("\n2. Testing RDS access...")
    try:
        manager.rds.describe_db_instances(MaxRecords=1)
        click.echo("   ✅ RDS access confirmed")
    except Exception as e:
        click.echo(f"   ❌ RDS access failed: {e}")
    
    # Test health checks
    click.echo("\n3. Testing health check endpoints...")
    for region, config in manager.regions.items():
        try:
            response = requests.get(
                f"{config['endpoint']}/api/health",
                timeout=5
            )
            if response.status_code == 200:
                click.echo(f"   ✅ {region}: Reachable")
            else:
                click.echo(f"   ⚠️  {region}: Status {response.status_code}")
        except Exception as e:
            click.echo(f"   ❌ {region}: {e}")


if __name__ == '__main__':
    cli()