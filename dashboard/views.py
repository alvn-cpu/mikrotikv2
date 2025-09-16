from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from billing.models import WifiUser, WifiPlan
from payments.models import PaymentTransaction
from radius.models import RadiusAccounting, RadiusPostAuth, NasClient
from mikrotik_integration.models import RouterConfig
from .station_config_generator import (
    generate_station_mikrotik_config, 
    generate_station_login_page, 
    generate_station_readme
)
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd
import zipfile
import io


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with analytics and visualizations"""
    
    # Calculate date ranges
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic statistics
    stats = {
        'total_users': WifiUser.objects.count(),
        'active_users': WifiUser.objects.filter(status='active').count(),
        'total_plans': WifiPlan.objects.filter(is_active=True).count(),
        'total_transactions': PaymentTransaction.objects.count(),
        'successful_payments': PaymentTransaction.objects.filter(status='completed').count(),
        'total_revenue': PaymentTransaction.objects.filter(status='completed').aggregate(
            total=Sum('amount'))['total'] or 0,
        'active_sessions': RadiusAccounting.objects.filter(
            acctstarttime__isnull=False, acctstoptime__isnull=True).count(),
    }
    
    # Today's statistics
    today_stats = {
        'new_users': WifiUser.objects.filter(created_at__date=today).count(),
        'transactions': PaymentTransaction.objects.filter(created_at__date=today).count(),
        'revenue': PaymentTransaction.objects.filter(
            created_at__date=today, status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'sessions': RadiusAccounting.objects.filter(acctstarttime__date=today).count(),
    }
    
    # Week statistics
    week_stats = {
        'new_users': WifiUser.objects.filter(created_at__date__gte=week_ago).count(),
        'transactions': PaymentTransaction.objects.filter(created_at__date__gte=week_ago).count(),
        'revenue': PaymentTransaction.objects.filter(
            created_at__date__gte=week_ago, status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'sessions': RadiusAccounting.objects.filter(acctstarttime__date__gte=week_ago).count(),
    }
    
    # Revenue chart (last 30 days)
    revenue_data = PaymentTransaction.objects.filter(
        created_at__date__gte=month_ago,
        status='completed'
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(
        revenue=Sum('amount'),
        count=Count('id')
    ).order_by('day')
    
    # Prepare revenue chart
    revenue_chart = create_revenue_chart(revenue_data)
    
    # User registration chart (last 30 days)
    user_data = WifiUser.objects.filter(
        created_at__date__gte=month_ago
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    user_chart = create_user_chart(user_data)
    
    # Plan popularity chart
    plan_data = PaymentTransaction.objects.filter(
        status='completed'
    ).values(
        'plan__name'
    ).annotate(
        count=Count('id'),
        revenue=Sum('amount')
    ).order_by('-count')
    
    plan_chart = create_plan_chart(plan_data)
    
    # Session duration analysis
    session_data = RadiusAccounting.objects.filter(
        acctstarttime__date__gte=week_ago,
        acctsessiontime__isnull=False
    )
    
    session_chart = create_session_chart(session_data)
    
    # Recent activities
    recent_users = WifiUser.objects.order_by('-created_at')[:10]
    recent_transactions = PaymentTransaction.objects.order_by('-created_at')[:10]
    recent_sessions = RadiusAccounting.objects.filter(
        acctstarttime__isnull=False
    ).order_by('-acctstarttime')[:10]
    
    # NAS status
    nas_clients = NasClient.objects.filter(is_active=True)
    
    # WiFi Plans for plans management
    wifi_plans = WifiPlan.objects.all().order_by('-created_at')
    
    # Router configs for stations management
    router_configs = RouterConfig.objects.all().order_by('-created_at')
    
    context = {
        'stats': stats,
        'today_stats': today_stats,
        'week_stats': week_stats,
        'revenue_chart': revenue_chart,
        'user_chart': user_chart,
        'plan_chart': plan_chart,
        'session_chart': session_chart,
        'recent_users': recent_users,
        'recent_transactions': recent_transactions,
        'recent_sessions': recent_sessions,
        'nas_clients': nas_clients,
        'wifi_plans': wifi_plans,
        'router_configs': router_configs,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


def create_revenue_chart(revenue_data):
    """Create revenue chart using Plotly"""
    if not revenue_data:
        return json.dumps({})
    
    dates = [item['day'] for item in revenue_data]
    revenues = [float(item['revenue']) for item in revenue_data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=revenues,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Revenue Trend (Last 30 Days)',
        xaxis_title='Date',
        yaxis_title='Revenue (KES)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333'),
        height=350
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_user_chart(user_data):
    """Create user registration chart"""
    if not user_data:
        return json.dumps({})
    
    dates = [item['day'] for item in user_data]
    counts = [item['count'] for item in user_data]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates,
        y=counts,
        name='New Users',
        marker_color='#007bff'
    ))
    
    fig.update_layout(
        title='User Registrations (Last 30 Days)',
        xaxis_title='Date',
        yaxis_title='New Users',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333'),
        height=350
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_plan_chart(plan_data):
    """Create plan popularity chart"""
    if not plan_data:
        return json.dumps({})
    
    plans = [item['plan__name'] for item in plan_data]
    counts = [item['count'] for item in plan_data]
    
    fig = go.Figure(data=[go.Pie(
        labels=plans,
        values=counts,
        hole=.3,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title='Plan Popularity',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333'),
        height=400
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_session_chart(session_data):
    """Create session duration analysis chart"""
    if not session_data:
        return json.dumps({})
    
    # Convert to minutes and create ranges
    durations = []
    for session in session_data:
        if session.acctsessiontime:
            minutes = session.acctsessiontime / 60
            durations.append(minutes)
    
    if not durations:
        return json.dumps({})
    
    # Create duration ranges
    ranges = ['0-15m', '15-30m', '30-60m', '1-2h', '2-4h', '4h+']
    counts = [0] * 6
    
    for duration in durations:
        if duration <= 15:
            counts[0] += 1
        elif duration <= 30:
            counts[1] += 1
        elif duration <= 60:
            counts[2] += 1
        elif duration <= 120:
            counts[3] += 1
        elif duration <= 240:
            counts[4] += 1
        else:
            counts[5] += 1
    
    fig = go.Figure(data=[go.Bar(
        x=ranges,
        y=counts,
        marker_color='#ffc107'
    )])
    
    fig.update_layout(
        title='Session Duration Distribution',
        xaxis_title='Duration Range',
        yaxis_title='Number of Sessions',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333'),
        height=350
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


# Plan Management Views
@staff_member_required
@csrf_exempt
def create_plan(request):
    """Create a new WiFi plan"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            price = request.POST.get('price')
            duration_value = request.POST.get('duration_value', 0)
            duration_unit = request.POST.get('duration_unit', 'minutes')
            data_limit = request.POST.get('data_limit')
            upload_speed = request.POST.get('upload_speed', 1024)
            download_speed = request.POST.get('download_speed', 1024)
            description = request.POST.get('description', '')
            plan_type = request.POST.get('plan_type', 'time')
            
            # Convert duration to minutes
            duration_minutes = None
            if duration_value and duration_value != '0':
                duration_value = int(duration_value)
                if duration_unit == 'minutes':
                    duration_minutes = duration_value
                elif duration_unit == 'hours':
                    duration_minutes = duration_value * 60
                elif duration_unit == 'days':
                    duration_minutes = duration_value * 60 * 24
            
            # Convert data limit to MB
            data_limit_mb = None
            if data_limit and data_limit != '0':
                data_limit_mb = int(data_limit)
            
            plan = WifiPlan.objects.create(
                name=name,
                price=price,
                plan_type=plan_type,
                duration_minutes=duration_minutes,
                data_limit_mb=data_limit_mb,
                upload_speed_kbps=int(upload_speed),
                download_speed_kbps=int(download_speed),
                description=description,
                is_active=True
            )
            
            return JsonResponse({'success': True, 'message': 'Plan created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@staff_member_required
@csrf_exempt
def update_plan(request, plan_id):
    """Update a WiFi plan"""
    plan = get_object_or_404(WifiPlan, id=plan_id)
    
    if request.method == 'POST':
        try:
            plan.name = request.POST.get('name', plan.name)
            plan.price = request.POST.get('price', plan.price)
            plan.description = request.POST.get('description', plan.description)
            plan.plan_type = request.POST.get('plan_type', plan.plan_type)
            
            # Handle duration updates
            duration_value = request.POST.get('duration_value')
            duration_unit = request.POST.get('duration_unit', 'minutes')
            if duration_value and duration_value != '0':
                duration_value = int(duration_value)
                if duration_unit == 'minutes':
                    plan.duration_minutes = duration_value
                elif duration_unit == 'hours':
                    plan.duration_minutes = duration_value * 60
                elif duration_unit == 'days':
                    plan.duration_minutes = duration_value * 60 * 24
            else:
                plan.duration_minutes = None
            
            # Handle data limit updates
            data_limit = request.POST.get('data_limit')
            if data_limit and data_limit != '0':
                plan.data_limit_mb = int(data_limit)
            else:
                plan.data_limit_mb = None
            
            # Handle speed limits
            upload_speed = request.POST.get('upload_speed')
            download_speed = request.POST.get('download_speed')
            if upload_speed:
                plan.upload_speed_kbps = int(upload_speed)
            if download_speed:
                plan.download_speed_kbps = int(download_speed)
            
            plan.is_active = request.POST.get('is_active') == 'true'
            plan.save()
            
            return JsonResponse({'success': True, 'message': 'Plan updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@staff_member_required
@csrf_exempt
def delete_plan(request, plan_id):
    """Delete a WiFi plan"""
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
        
    plan = get_object_or_404(WifiPlan, id=plan_id)
    
    try:
        # Check if plan is being used by any users
        users_with_plan = plan.wifiuser_set.count()
        if users_with_plan > 0:
            return JsonResponse({
                'success': False, 
                'message': f'Cannot delete plan. {users_with_plan} users are currently using this plan.'
            })
        
        plan_name = plan.name
        plan.delete()
        return JsonResponse({'success': True, 'message': f'Plan "{plan_name}" deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error deleting plan: {str(e)}'})


@staff_member_required
def get_plan(request, plan_id):
    """Get plan details for editing"""
    plan = get_object_or_404(WifiPlan, id=plan_id)
    
    # Convert duration_minutes back to value and unit for frontend
    duration_value = ''
    duration_unit = 'minutes'
    if plan.duration_minutes:
        if plan.duration_minutes >= 1440 and plan.duration_minutes % 1440 == 0:  # Days
            duration_value = str(plan.duration_minutes // 1440)
            duration_unit = 'days'
        elif plan.duration_minutes >= 60 and plan.duration_minutes % 60 == 0:  # Hours
            duration_value = str(plan.duration_minutes // 60)
            duration_unit = 'hours'
        else:  # Minutes
            duration_value = str(plan.duration_minutes)
            duration_unit = 'minutes'
    
    return JsonResponse({
        'id': str(plan.id),
        'name': plan.name,
        'price': str(plan.price),
        'plan_type': plan.plan_type,
        'duration_value': duration_value,
        'duration_unit': duration_unit,
        'data_limit': str(plan.data_limit_mb) if plan.data_limit_mb else '',
        'upload_speed': str(plan.upload_speed_kbps),
        'download_speed': str(plan.download_speed_kbps),
        'description': plan.description,
        'is_active': plan.is_active
    })


# Station Management Views
@staff_member_required
@csrf_exempt
def create_station(request):
    """Create a new MikroTik station"""
    if request.method == 'POST':
        try:
            # Basic station fields
            name = request.POST.get('name')
            host = request.POST.get('host')
            api_port = request.POST.get('api_port', 8728)
            username = request.POST.get('username')
            password = request.POST.get('password')
            hotspot_interface = request.POST.get('hotspot_interface', 'wlan1')
            address_pool = request.POST.get('address_pool', 'dhcp_pool1')
            
            # Payment configuration fields
            business_name = request.POST.get('business_name', '')
            payment_method = request.POST.get('payment_method', 'paybill')
            enable_payments = request.POST.get('enable_payments') == 'on'
            paybill_number = request.POST.get('paybill_number', '')
            account_number = request.POST.get('account_number', '')
            till_number = request.POST.get('till_number', '')
            
            # KCB Account configuration (replacing individual API credentials)
            kcb_account_type = request.POST.get('kcb_account_type', 'paybill')
            kcb_account_number = request.POST.get('kcb_account_number', '')
            account_name = request.POST.get('account_name', '')
            
            # Create router configuration with payment settings
            RouterConfig.objects.create(
                name=name,
                host=host,
                api_port=api_port,
                username=username,
                password=password,
                hotspot_interface=hotspot_interface,
                address_pool=address_pool,
                business_name=business_name,
                payment_method=payment_method,
                enable_payments=enable_payments,
                paybill_number=paybill_number,
                account_number=account_number,
                till_number=till_number,
                kcb_account_type=kcb_account_type,
                kcb_account_number=kcb_account_number,
                account_name=account_name,
                is_active=True
            )
            return JsonResponse({'success': True, 'message': 'Station created successfully with payment configuration'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@staff_member_required
@csrf_exempt
def update_station(request, station_id):
    """Update a MikroTik station"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    if request.method == 'POST':
        try:
            # Basic station fields
            station.name = request.POST.get('name', station.name)
            station.host = request.POST.get('host', station.host)
            station.api_port = int(request.POST.get('api_port', station.api_port))
            station.username = request.POST.get('username', station.username)
            if request.POST.get('password'):
                station.password = request.POST.get('password')
            station.hotspot_interface = request.POST.get('hotspot_interface', station.hotspot_interface)
            station.address_pool = request.POST.get('address_pool', station.address_pool)
            station.is_active = request.POST.get('is_active') == 'true'
            
            # Payment configuration fields
            station.business_name = request.POST.get('business_name', station.business_name)
            station.payment_method = request.POST.get('payment_method', station.payment_method)
            station.enable_payments = request.POST.get('enable_payments') == 'on'
            station.paybill_number = request.POST.get('paybill_number', station.paybill_number)
            station.account_number = request.POST.get('account_number', station.account_number)
            station.till_number = request.POST.get('till_number', station.till_number)
            
            # KCB Account configuration (replacing individual API credentials)
            if request.POST.get('kcb_account_type'):
                station.kcb_account_type = request.POST.get('kcb_account_type')
            if request.POST.get('kcb_account_number'):
                station.kcb_account_number = request.POST.get('kcb_account_number')
            if request.POST.get('account_name'):
                station.account_name = request.POST.get('account_name')
            
            station.save()
            
            return JsonResponse({'success': True, 'message': 'Station updated successfully with payment configuration'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@staff_member_required
def delete_station(request, station_id):
    """Delete a MikroTik station"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    try:
        station.delete()
        return JsonResponse({'success': True, 'message': 'Station deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@staff_member_required
def get_station(request, station_id):
    """Get station details for editing"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    return JsonResponse({
        'id': station.id,
        'name': station.name,
        'host': station.host,
        'api_port': station.api_port,
        'username': station.username,
        'hotspot_interface': station.hotspot_interface,
        'address_pool': station.address_pool,
        'is_active': station.is_active,
        
        # Payment configuration
        'business_name': station.business_name,
        'payment_method': station.payment_method,
        'enable_payments': station.enable_payments,
        'paybill_number': station.paybill_number,
        'account_number': station.account_number,
        'till_number': station.till_number,
        
        # KCB Account configuration
        'kcb_account_type': getattr(station, 'kcb_account_type', 'paybill'),
        'kcb_account_number': getattr(station, 'kcb_account_number', ''),
        'account_name': getattr(station, 'account_name', ''),
    })


@staff_member_required
def download_station_config(request, station_id):
    """Generate and download complete station configuration package as ZIP"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    # Auto-detect Django server URL (works for both local and production)
    # The generator functions will automatically detect the environment
    
    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Generate and add MikroTik configuration script (auto-detects URL)
        config_content = generate_station_mikrotik_config(station)
        zip_file.writestr(f'{station.name}_config.rsc', config_content)
        
        # Generate and add custom login page (auto-detects URL)
        login_content = generate_station_login_page(station)
        zip_file.writestr(f'{station.name}_login.html', login_content)
        
        # Generate and add README instructions
        readme_content = generate_station_readme(station)
        zip_file.writestr(f'{station.name}_README.txt', readme_content)
    
    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{station.name}_complete_config.zip"'
    
    return response


@staff_member_required
def download_station_config_file(request, station_id):
    """Download only the MikroTik configuration file (.rsc)"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    # Generate MikroTik configuration script (auto-detects URL)
    config_content = generate_station_mikrotik_config(station)
    
    response = HttpResponse(config_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{station.name}_config.rsc"'
    
    return response


@staff_member_required
def download_station_login_page(request, station_id):
    """Download only the custom login page (.html)"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    # Generate custom login page (auto-detects URL)
    login_content = generate_station_login_page(station)
    
    response = HttpResponse(login_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{station.name}_login.html"'
    
    return response


# Additional Views for New Dashboard Sections
@staff_member_required
def get_users_data(request):
    """Get users data for the users section"""
    users = WifiUser.objects.all().order_by('-created_at')
    user_data = []
    
    for user in users:
        user_data.append({
            'id': str(user.id),
            'phone_number': user.phone_number,
            'mac_address': user.mac_address or 'No MAC',
            'status': user.status,
            'current_plan': user.current_plan.name if user.current_plan else 'No Plan',
            'data_used_mb': user.data_used_mb,
            'plan_expires_at': user.plan_expires_at.isoformat() if user.plan_expires_at else None,
            'created_at': user.created_at.isoformat(),
        })
    
    return JsonResponse({'users': user_data})


@staff_member_required
def get_transactions_data(request):
    """Get transactions data for the transactions section"""
    transactions = PaymentTransaction.objects.all().order_by('-created_at')[:100]
    transaction_data = []
    
    for txn in transactions:
        transaction_data.append({
            'id': str(txn.id),
            'transaction_id': txn.transaction_id,
            'phone_number': txn.phone_number if hasattr(txn, 'phone_number') else 'Unknown',
            'plan_name': txn.plan.name if hasattr(txn, 'plan') and txn.plan else 'No Plan',
            'amount': float(txn.amount),
            'status': txn.status,
            'created_at': txn.created_at.isoformat(),
        })
    
    return JsonResponse({'transactions': transaction_data})


@staff_member_required
def get_sessions_data(request):
    """Get active sessions data"""
    try:
        sessions = RadiusAccounting.objects.filter(
            acctstoptime__isnull=True
        ).order_by('-acctstarttime')[:50]
        
        session_data = []
        for session in sessions:
            session_data.append({
                'username': session.username,
                'nasipaddress': session.nasipaddress,
                'acctstarttime': session.acctstarttime.isoformat() if session.acctstarttime else None,
                'acctsessiontime': session.acctsessiontime or 0,
                'acctinputoctets': session.acctinputoctets or 0,
                'acctoutputoctets': session.acctoutputoctets or 0,
            })
        
        return JsonResponse({'sessions': session_data})
    except Exception as e:
        return JsonResponse({'sessions': [], 'error': str(e)})


@staff_member_required
def export_transactions_csv(request):
    """Export transactions to CSV"""
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'Phone', 'Plan', 'Amount', 'Status', 'Date'])
    
    transactions = PaymentTransaction.objects.all().order_by('-created_at')
    for txn in transactions:
        writer.writerow([
            txn.transaction_id,
            getattr(txn, 'phone_number', 'Unknown'),
            getattr(txn.plan, 'name', 'No Plan') if hasattr(txn, 'plan') and txn.plan else 'No Plan',
            txn.amount,
            txn.status,
            txn.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@staff_member_required
def test_payment_credentials(request, station_id):
    """Test KCB payment credentials for a station"""
    station = get_object_or_404(RouterConfig, id=station_id)
    
    try:
        from payments.kcb_buni_service import KCBBuniService
        
        # Initialize KCB service with station credentials
        kcb_service = KCBBuniService(station_config=station)
        
        # Validate credentials
        validation_result = kcb_service.validate_payment_credentials()
        
        if validation_result['valid']:
            return JsonResponse({
                'success': True,
                'message': validation_result['message']
            })
        else:
            return JsonResponse({
                'success': False,
                'message': validation_result['message']
            })
            
    except ImportError:
        return JsonResponse({
            'success': False,
            'message': 'KCB Buni service not available. Please check the integration.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error testing credentials: {str(e)}'
        })
