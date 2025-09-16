from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up Django Site for allauth integration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain name for the site',
            default='beat-production-5003.up.railway.app'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Site name',
            default='BROADCOM NETWORKS'
        )
    
    def handle(self, *args, **options):
        domain = options['domain']
        name = options['name']
        
        try:
            # Update or create the Site with SITE_ID = 1
            site, created = Site.objects.get_or_create(
                id=settings.SITE_ID,
                defaults={
                    'domain': domain,
                    'name': name
                }
            )
            
            if not created:
                # Update existing site
                site.domain = domain
                site.name = name
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Updated Site: {site.name} ({site.domain})')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created Site: {site.name} ({site.domain})')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Site ID {settings.SITE_ID} is now configured for allauth')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error setting up site: {str(e)}')
            )