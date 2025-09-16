from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Set up Google OAuth integration automatically'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth Client ID',
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Google OAuth Client Secret',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔑 Setting up Google OAuth integration...")
        
        dry_run = options['dry_run']
        
        # Get credentials from command line or environment
        client_id = options['client_id'] or os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = options['client_secret'] or os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Google OAuth credentials not provided. Either use:\n"
                    "   --client-id and --client-secret arguments\n"
                    "   OR set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET environment variables"
                )
            )
            return
        
        self.stdout.write(f"📍 Client ID: {client_id[:20]}...{client_id[-20:] if len(client_id) > 40 else client_id}")
        self.stdout.write(f"📍 Client Secret: {'*' * len(client_secret)}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        # Step 1: Ensure Site exists
        try:
            site, created = Site.objects.get_or_create(
                id=settings.SITE_ID,
                defaults={
                    'domain': 'beat-production-5003.up.railway.app',
                    'name': 'BROADCOM NETWORKS'
                }
            )
            
            if not dry_run:
                if not created:
                    site.domain = 'beat-production-5003.up.railway.app'
                    site.name = 'BROADCOM NETWORKS'
                    site.save()
                    self.stdout.write("✅ Updated Site configuration")
                else:
                    self.stdout.write("✅ Created Site configuration")
            else:
                self.stdout.write("🧪 Would update/create Site configuration")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error setting up site: {e}"))
            return
        
        # Step 2: Set up Google Social Application
        try:
            from allauth.socialaccount.models import SocialApp
            
            app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google OAuth',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            if not dry_run:
                if not created:
                    # Update existing app
                    app.client_id = client_id
                    app.secret = client_secret
                    app.name = 'Google OAuth'
                    app.save()
                    self.stdout.write("✅ Updated Google Social Application")
                else:
                    self.stdout.write("✅ Created Google Social Application")
                
                # Add site to the app
                app.sites.add(site)
                self.stdout.write("✅ Associated Google app with site")
            else:
                self.stdout.write("🧪 Would create/update Google Social Application")
                self.stdout.write("🧪 Would associate app with site")
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR("❌ django-allauth not properly installed")
            )
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error setting up Google Social Application: {e}"))
            return
        
        # Step 3: Verify configuration
        self.stdout.write("\n" + "="*50)
        self.stdout.write("GOOGLE OAUTH CONFIGURATION SUMMARY")
        self.stdout.write("="*50)
        
        if not dry_run:
            try:
                from allauth.socialaccount.models import SocialApp
                app = SocialApp.objects.get(provider='google')
                
                self.stdout.write(f"✅ Provider: {app.provider}")
                self.stdout.write(f"✅ Name: {app.name}")
                self.stdout.write(f"✅ Client ID: {app.client_id}")
                self.stdout.write(f"✅ Secret: {'*' * len(app.secret)}")
                self.stdout.write(f"✅ Sites: {', '.join([s.name for s in app.sites.all()])}")
                
                self.stdout.write("\n🎉 Google OAuth setup completed successfully!")
                
                # Show next steps
                self.stdout.write("\n📋 NEXT STEPS:")
                self.stdout.write("1. Ensure Google Cloud Console is configured with:")
                self.stdout.write("   - Authorized JavaScript origins: https://beat-production-5003.up.railway.app")
                self.stdout.write("   - Authorized redirect URIs: https://beat-production-5003.up.railway.app/accounts/google/login/callback/")
                self.stdout.write("2. Test the login: https://beat-production-5003.up.railway.app/auth/login/")
                self.stdout.write("3. Click 'Continue with Google' to test OAuth flow")
                
                self.stdout.write("\n🚨 TROUBLESHOOTING:")
                self.stdout.write("If you get errors, check:")
                self.stdout.write("- Google Cloud Console OAuth settings")
                self.stdout.write("- Railway environment variables")
                self.stdout.write("- Django admin Social Applications")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error verifying configuration: {e}"))
        else:
            self.stdout.write("🧪 DRY RUN - Run without --dry-run to apply changes")
        
        self.stdout.write("\n🔗 USEFUL LINKS:")
        self.stdout.write("- Google Cloud Console: https://console.cloud.google.com")
        self.stdout.write("- OAuth Setup Guide: See GOOGLE_OAUTH_SETUP.md")
        self.stdout.write("- Admin Panel: https://beat-production-5003.up.railway.app/admin/")