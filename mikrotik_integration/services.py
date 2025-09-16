import routeros_api
import logging
import socket
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import RouterConfig, ActiveUser, RouterCommand
from billing.models import WifiUser
from radius.models import RadiusAccounting
import uuid

logger = logging.getLogger(__name__)


class MikroTikAPIError(Exception):
    """Custom exception for MikroTik API errors"""
    pass


class MikroTikManager:
    """MikroTik RouterOS API manager for user and session management"""
    
    def __init__(self, router_config=None):
        """
        Initialize MikroTik manager with router configuration
        
        Args:
            router_config: RouterConfig instance or None for default
        """
        if router_config:
            self.router_config = router_config
        else:
            # Get the first active router
            self.router_config = RouterConfig.objects.filter(is_active=True).first()
            
        if not self.router_config:
            raise MikroTikAPIError("No active router configuration found")
        
        self.connection = None
    
    def connect(self):
        """Establish connection to MikroTik router"""
        try:
            self.connection = routeros_api.RouterOsApi(
                self.router_config.host,
                username=self.router_config.username,
                password=self.router_config.password,
                port=self.router_config.api_port,
                plaintext_login=True
            )
            
            # Update router connection status
            self.router_config.connection_status = 'connected'
            self.router_config.last_connected = timezone.now()
            self.router_config.save()
            
            logger.info(f"Connected to MikroTik router: {self.router_config.host}")
            return True
            
        except Exception as e:
            self.router_config.connection_status = 'error'
            self.router_config.save()
            logger.error(f"Failed to connect to MikroTik router {self.router_config.host}: {str(e)}")
            raise MikroTikAPIError(f"Connection failed: {str(e)}")
    
    def disconnect(self):
        """Close connection to MikroTik router"""
        if self.connection:
            try:
                self.connection.disconnect()
                self.connection = None
                logger.info(f"Disconnected from MikroTik router: {self.router_config.host}")
            except Exception as e:
                logger.warning(f"Error during disconnect: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def create_hotspot_user(self, wifi_user, plan):
        """
        Create a hotspot user in MikroTik
        
        Args:
            wifi_user: WifiUser instance
            plan: WifiPlan instance
        """
        if not self.connection:
            self.connect()
        
        try:
            # Prepare user data
            username = wifi_user.mikrotik_username
            password = wifi_user.mikrotik_password
            
            # Calculate time limit for time-based plans
            time_limit = None
            if plan.plan_type == 'time' and plan.duration_minutes:
                time_limit = f"{plan.duration_minutes}m"
            
            # Calculate data limit for data-based plans
            data_limit = None
            if plan.plan_type == 'data' and plan.data_limit_mb:
                data_limit = f"{plan.data_limit_mb}M"
            
            # Create user profile name
            profile_name = f"plan_{plan.name.lower().replace(' ', '_')}"
            
            # User parameters
            user_params = {
                'name': username,
                'password': password,
                'profile': profile_name,
                'server': 'hotspot1'  # Default hotspot server name
            }
            
            if time_limit:
                user_params['limit-uptime'] = time_limit
            
            if data_limit:
                user_params['limit-bytes-total'] = data_limit
            
            # Create the user
            result = self.connection.get_resource('/ip/hotspot/user').add(**user_params)
            
            # Log the command
            RouterCommand.objects.create(
                router=self.router_config,
                wifi_user=wifi_user,
                command_type='create_user',
                command_data=user_params,
                success=True,
                response_data=result
            )
            
            logger.info(f"Created hotspot user: {username}")
            return True
            
        except Exception as e:
            # Log the failed command
            RouterCommand.objects.create(
                router=self.router_config,
                wifi_user=wifi_user,
                command_type='create_user',
                command_data={'username': username},
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Failed to create hotspot user {username}: {str(e)}")
            raise MikroTikAPIError(f"Failed to create user: {str(e)}")
    
    def create_user_profile(self, plan):
        """
        Create a user profile for a WiFi plan
        
        Args:
            plan: WifiPlan instance
        """
        if not self.connection:
            self.connect()
        
        try:
            profile_name = f"plan_{plan.name.lower().replace(' ', '_')}"
            
            # Convert speeds from Kbps to proper format
            upload_speed = f"{plan.upload_speed_kbps}K" if plan.upload_speed_kbps else "0"
            download_speed = f"{plan.download_speed_kbps}K" if plan.download_speed_kbps else "0"
            rate_limit = f"{upload_speed}/{download_speed}"
            
            profile_params = {
                'name': profile_name,
                'rate-limit': rate_limit,
                'session-timeout': '1d',  # Default 1 day
                'idle-timeout': '00:05:00',  # 5 minutes idle timeout
                'keepalive-timeout': '00:02:00',  # 2 minutes keepalive
                'status-autorefresh': '00:01:00',  # 1 minute status refresh
                'transparent-proxy': 'yes',
                'bind-mac-address': 'yes'
            }
            
            # Set session timeout for time-based plans
            if plan.plan_type == 'time' and plan.duration_minutes:
                hours = plan.duration_minutes // 60
                minutes = plan.duration_minutes % 60
                profile_params['session-timeout'] = f"{hours:02d}:{minutes:02d}:00"
            
            # Create the profile
            result = self.connection.get_resource('/ip/hotspot/user/profile').add(**profile_params)
            
            logger.info(f"Created user profile: {profile_name}")
            return profile_name
            
        except Exception as e:
            logger.error(f"Failed to create user profile for plan {plan.name}: {str(e)}")
            # Don't raise error for profile creation as it might already exist
            return None
    
    def get_active_users(self):
        """Get list of active hotspot users"""
        if not self.connection:
            self.connect()
        
        try:
            active_sessions = self.connection.get_resource('/ip/hotspot/active').get()
            
            users_data = []
            for session in active_sessions:
                users_data.append({
                    'username': session.get('user', ''),
                    'ip_address': session.get('address', ''),
                    'mac_address': session.get('mac-address', ''),
                    'server': session.get('server', ''),
                    'login_time': session.get('login-time', ''),
                    'uptime': session.get('uptime', ''),
                    'session_id': session.get('.id', ''),
                    'bytes_in': int(session.get('bytes-in', 0)),
                    'bytes_out': int(session.get('bytes-out', 0)),
                    'packets_in': int(session.get('packets-in', 0)),
                    'packets_out': int(session.get('packets-out', 0))
                })
            
            # Log the command
            RouterCommand.objects.create(
                router=self.router_config,
                command_type='get_active_users',
                command_data={'count': len(users_data)},
                success=True,
                response_data={'users_count': len(users_data)}
            )
            
            logger.info(f"Retrieved {len(users_data)} active users")
            return users_data
            
        except Exception as e:
            RouterCommand.objects.create(
                router=self.router_config,
                command_type='get_active_users',
                command_data={},
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Failed to get active users: {str(e)}")
            raise MikroTikAPIError(f"Failed to get active users: {str(e)}")
    
    def disconnect_user(self, username):
        """Disconnect a specific user"""
        if not self.connection:
            self.connect()
        
        try:
            # Find the active session
            active_sessions = self.connection.get_resource('/ip/hotspot/active').get()
            
            for session in active_sessions:
                if session.get('user') == username:
                    session_id = session.get('.id')
                    self.connection.get_resource('/ip/hotspot/active').remove(session_id)
                    
                    # Log the command
                    RouterCommand.objects.create(
                        router=self.router_config,
                        command_type='disconnect_user',
                        command_data={'username': username, 'session_id': session_id},
                        success=True
                    )
                    
                    logger.info(f"Disconnected user: {username}")
                    return True
            
            logger.warning(f"User {username} not found in active sessions")
            return False
            
        except Exception as e:
            RouterCommand.objects.create(
                router=self.router_config,
                command_type='disconnect_user',
                command_data={'username': username},
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Failed to disconnect user {username}: {str(e)}")
            raise MikroTikAPIError(f"Failed to disconnect user: {str(e)}")
    
    def delete_user(self, username):
        """Delete a hotspot user"""
        if not self.connection:
            self.connect()
        
        try:
            users = self.connection.get_resource('/ip/hotspot/user').get()
            
            for user in users:
                if user.get('name') == username:
                    user_id = user.get('.id')
                    self.connection.get_resource('/ip/hotspot/user').remove(user_id)
                    
                    # Log the command
                    RouterCommand.objects.create(
                        router=self.router_config,
                        command_type='delete_user',
                        command_data={'username': username, 'user_id': user_id},
                        success=True
                    )
                    
                    logger.info(f"Deleted user: {username}")
                    return True
            
            logger.warning(f"User {username} not found")
            return False
            
        except Exception as e:
            RouterCommand.objects.create(
                router=self.router_config,
                command_type='delete_user',
                command_data={'username': username},
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Failed to delete user {username}: {str(e)}")
            raise MikroTikAPIError(f"Failed to delete user: {str(e)}")
    
    def update_active_users_in_db(self):
        """Update active users data in database"""
        try:
            active_users_data = self.get_active_users()
            
            # Clear existing active users for this router
            ActiveUser.objects.filter(router=self.router_config).update(is_active=False)
            
            for user_data in active_users_data:
                # Try to find corresponding WiFi user
                wifi_user = None
                try:
                    wifi_user = WifiUser.objects.get(mikrotik_username=user_data['username'])
                except WifiUser.DoesNotExist:
                    # Create a temporary user record if not found
                    continue
                
                # Update or create active user record
                active_user, created = ActiveUser.objects.update_or_create(
                    wifi_user=wifi_user,
                    router=self.router_config,
                    mikrotik_session_id=user_data['session_id'],
                    defaults={
                        'username': user_data['username'],
                        'ip_address': user_data['ip_address'],
                        'mac_address': user_data['mac_address'],
                        'login_time': timezone.now(),  # Simplified - should parse login_time
                        'uptime': user_data['uptime'],
                        'bytes_in': user_data['bytes_in'],
                        'bytes_out': user_data['bytes_out'],
                        'packets_in': user_data['packets_in'],
                        'packets_out': user_data['packets_out'],
                        'is_active': True
                    }
                )
            
            logger.info(f"Updated {len(active_users_data)} active users in database")
            return len(active_users_data)
            
        except Exception as e:
            logger.error(f"Failed to update active users in database: {str(e)}")
            return 0
    
    def sync_radius_accounting(self):
        """Sync active sessions with RADIUS accounting"""
        try:
            active_users_data = self.get_active_users()
            
            for user_data in active_users_data:
                # Create or update RADIUS accounting record
                unique_id = f"mikrotik_{self.router_config.id}_{user_data['session_id']}"
                
                accounting, created = RadiusAccounting.objects.update_or_create(
                    acctuniqueid=unique_id,
                    defaults={
                        'acctsessionid': user_data['session_id'],
                        'username': user_data['username'],
                        'nasipaddress': self.router_config.host,
                        'framedipaddress': user_data['ip_address'],
                        'callingstationid': user_data['mac_address'],
                        'acctstarttime': timezone.now() if created else None,
                        'acctinputoctets': user_data['bytes_in'],
                        'acctoutputoctets': user_data['bytes_out']
                    }
                )
            
            logger.info(f"Synced {len(active_users_data)} sessions with RADIUS accounting")
            return len(active_users_data)
            
        except Exception as e:
            logger.error(f"Failed to sync RADIUS accounting: {str(e)}")
            return 0


def create_mikrotik_user(wifi_user):
    """
    Helper function to create a MikroTik user for a WiFi user
    
    Args:
        wifi_user: WifiUser instance with current_plan set
    """
    if not wifi_user.current_plan:
        logger.warning(f"No plan assigned to user {wifi_user.phone_number}")
        return False
    
    try:
        # Get the first active router
        router_config = RouterConfig.objects.filter(is_active=True).first()
        if not router_config:
            logger.error("No active router configuration found")
            return False
        
        with MikroTikManager(router_config) as mikrotik:
            # Create user profile if it doesn't exist
            mikrotik.create_user_profile(wifi_user.current_plan)
            
            # Create the user
            mikrotik.create_hotspot_user(wifi_user, wifi_user.current_plan)
            
            # Update WiFi user status
            wifi_user.status = 'active'
            wifi_user.plan_started_at = timezone.now()
            
            # Set expiration time
            if wifi_user.current_plan.plan_type == 'time' and wifi_user.current_plan.duration_minutes:
                wifi_user.plan_expires_at = timezone.now() + timedelta(minutes=wifi_user.current_plan.duration_minutes)
            else:
                # Default to 24 hours for other plan types
                wifi_user.plan_expires_at = timezone.now() + timedelta(hours=24)
            
            wifi_user.save()
            
            logger.info(f"Successfully created MikroTik user for {wifi_user.phone_number}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to create MikroTik user for {wifi_user.phone_number}: {str(e)}")
        return False


def disconnect_expired_users():
    """
    Check for expired users and disconnect them from MikroTik
    This should be called periodically (e.g., via cron job or Celery task)
    """
    expired_users = WifiUser.objects.filter(
        status='active',
        plan_expires_at__lt=timezone.now()
    )
    
    if not expired_users.exists():
        return 0
    
    disconnected_count = 0
    
    try:
        router_config = RouterConfig.objects.filter(is_active=True).first()
        if not router_config:
            logger.error("No active router configuration found")
            return 0
        
        with MikroTikManager(router_config) as mikrotik:
            for user in expired_users:
                try:
                    # Disconnect from MikroTik
                    if mikrotik.disconnect_user(user.mikrotik_username):
                        # Update user status
                        user.status = 'expired'
                        user.save()
                        disconnected_count += 1
                        
                        logger.info(f"Disconnected expired user: {user.phone_number}")
                    
                except Exception as e:
                    logger.error(f"Failed to disconnect user {user.phone_number}: {str(e)}")
                    continue
    
    except Exception as e:
        logger.error(f"Failed to disconnect expired users: {str(e)}")
    
    return disconnected_count