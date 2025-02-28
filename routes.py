import os
import csv
import io
import json
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
import pandas as pd

# Import these within functions to avoid circular imports
# from models import db, User, Product, PriceHistory, URL, PriceAlert
# from forms import LoginForm, RegisterForm, URLForm, URLBatchForm, ProductFilterForm, PriceAlertForm, ScheduleForm
# from extractors import get_product_info, detect_platform
# from tasks import update_product_price

def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route('/')
    def index():
        """Home page"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login"""
        from forms import LoginForm
        from models import User
        
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'danger')
                return redirect(url_for('login'))
                
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('dashboard'))
            
        return render_template('login.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration"""
        from forms import RegisterForm
        from models import db, User
        
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        form = RegisterForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is not None:
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))
                
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None:
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
                
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        """User logout"""
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard"""
        from models import Product, PriceHistory
        from forms import ProductFilterForm
        
        form = ProductFilterForm(request.args)
        
        # Get all products linked to the current user's URLs
        query = Product.query.join(Product.urls).filter_by(user_id=current_user.id)
        
        # Apply filters
        if form.platform.data and form.platform.data != 'all':
            query = query.join(Product.urls).filter_by(platform=form.platform.data)
            
        if form.price_min.data is not None:
            query = query.filter(Product.current_price >= form.price_min.data)
            
        if form.price_max.data is not None:
            query = query.filter(Product.current_price <= form.price_max.data)
            
        # Apply sorting
        if form.sort_by.data == 'name':
            query = query.order_by(Product.name)
        elif form.sort_by.data == 'price_asc':
            query = query.order_by(Product.current_price)
        elif form.sort_by.data == 'price_desc':
            query = query.order_by(Product.current_price.desc())
        elif form.sort_by.data == 'updated':
            query = query.order_by(Product.updated_at.desc())
        
        products = query.all()
        
        # For price change sorting (requires post-query processing)
        if form.sort_by.data == 'change_asc':
            products.sort(key=lambda p: p.last_price_change or 0)
        elif form.sort_by.data == 'change_desc':
            products.sort(key=lambda p: p.last_price_change or 0, reverse=True)
            
        # Get price history data for charts
        price_history_data = {}
        for product in products:
            history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.timestamp).all()
            if history:
                price_history_data[product.id] = {
                    'dates': [h.timestamp.strftime('%Y-%m-%d') for h in history],
                    'prices': [h.price for h in history]
                }
        
        return render_template(
            'dashboard.html', 
            products=products, 
            price_history=json.dumps(price_history_data),
            form=form
        )
    
    @app.route('/add-url', methods=['GET', 'POST'])
    @login_required
    def add_url():
        """Add a single URL to track"""
        from forms import URLForm
        from models import db, URL
        from extractors import detect_platform
        from tasks import update_product_price
        
        form = URLForm()
        if form.validate_on_submit():
            # Check if URL already exists
            existing_url = URL.query.filter_by(url=form.url.data).first()
            if existing_url:
                flash('This URL is already being tracked', 'warning')
                return redirect(url_for('urls'))
                
            # Detect platform
            platform = detect_platform(form.url.data)
            if not platform:
                flash('Unsupported platform. Currently only Salla and Zid are supported.', 'danger')
                return redirect(url_for('add_url'))
                
            # Add URL to database
            new_url = URL(
                url=form.url.data,
                platform=platform,
                user=current_user
            )
            db.session.add(new_url)
            db.session.commit()
            
            # Now update the product info right away
            success = update_product_price(new_url.id)
            
            if success:
                flash('URL added successfully and product info retrieved', 'success')
            else:
                flash('URL added but could not retrieve product info', 'warning')
                
            return redirect(url_for('urls'))
            
        return render_template('add_url.html', form=form, title='Add URL')
    
    @app.route('/urls', methods=['GET'])
    @login_required
    def urls():
        """Manage URLs"""
        from models import URL
        from forms import URLBatchForm
        
        urls = URL.query.filter_by(user_id=current_user.id).all()
        form = URLBatchForm()
        
        return render_template('urls.html', urls=urls, form=form, title='Manage URLs')
    
    @app.route('/batch-urls', methods=['POST'])
    @login_required
    def batch_urls():
        """Add multiple URLs in batch"""
        from forms import URLBatchForm
        from models import db, URL
        from extractors import detect_platform
        from tasks import update_product_price
        
        form = URLBatchForm()
        if form.validate_on_submit():
            url_list = form.urls.data.strip().split('\n')
            url_list = [url.strip() for url in url_list if url.strip()]
            
            added = 0
            invalid = 0
            duplicates = 0
            
            for url in url_list:
                # Check if URL already exists
                existing_url = URL.query.filter_by(url=url).first()
                if existing_url:
                    duplicates += 1
                    continue
                    
                # Detect platform
                platform = detect_platform(url)
                if not platform:
                    invalid += 1
                    continue
                    
                # Add URL to database
                new_url = URL(
                    url=url,
                    platform=platform,
                    user=current_user
                )
                db.session.add(new_url)
                added += 1
                
            db.session.commit()
            
            # Update prices synchronously for new URLs
            new_urls = URL.query.filter_by(user_id=current_user.id, last_checked=None).all()
            if new_urls:
                url_ids = [url.id for url in new_urls]
                for url_id in url_ids:
                    update_product_price(url_id)
            
            flash(f'Added {added} URLs. {invalid} invalid, {duplicates} duplicates.', 'info')
            return redirect(url_for('urls'))
            
        return redirect(url_for('urls'))
    
    @app.route('/delete-url/<int:url_id>', methods=['POST'])
    @login_required
    def delete_url(url_id):
        """Delete a URL"""
        from models import db, URL
        
        url = URL.query.get_or_404(url_id)
        
        # Check if URL belongs to current user
        if url.user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to delete this URL', 'danger')
            return redirect(url_for('urls'))
            
        db.session.delete(url)
        db.session.commit()
        
        flash('URL deleted successfully', 'success')
        return redirect(url_for('urls'))
    
    @app.route('/update-prices', methods=['POST'])
    @login_required
    def update_prices():
        """Manually trigger price updates"""
        from tasks import update_all_prices
        
        update_all_prices(app)
        
        flash('Price update initiated. This may take a few minutes.', 'info')
        return redirect(url_for('dashboard'))
    
    @app.route('/product/<int:product_id>')
    @login_required
    def product_detail(product_id):
        """Product detail page"""
        from models import Product, PriceHistory
        from forms import PriceAlertForm
        
        product = Product.query.get_or_404(product_id)
        
        # Check if product belongs to current user
        if not any(url.user_id == current_user.id for url in product.urls):
            flash('You do not have permission to view this product', 'danger')
            return redirect(url_for('dashboard'))
            
        # Get price history
        history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.timestamp).all()
        
        # Prepare data for price history chart
        chart_data = {
            'dates': [h.timestamp.strftime('%Y-%m-%d') for h in history],
            'prices': [h.price for h in history]
        }
        
        # Alert form
        alert_form = PriceAlertForm()
        
        return render_template(
            'product_detail.html',
            product=product,
            chart_data=json.dumps(chart_data),
            alert_form=alert_form
        )
    
    @app.route('/export-data', methods=['GET'])
    @login_required
    def export_data():
        """Export product data as CSV"""
        from models import Product, PriceHistory
        
        # Get all products linked to the current user's URLs
        products = Product.query.join(Product.urls).filter_by(user_id=current_user.id).all()
        
        # Create DataFrame for export
        data = []
        for product in products:
            # Get the URL(s) for this product
            urls = [url.url for url in product.urls if url.user_id == current_user.id]
            url_str = ', '.join(urls)
            
            # Get the platform(s) for this product
            platforms = [url.platform for url in product.urls if url.user_id == current_user.id]
            platform_str = ', '.join(platforms)
            
            # Get the last price change
            last_change = product.last_price_change
            
            # Get the price history
            history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.timestamp).all()
            price_history = ', '.join([f"{h.price} ({h.timestamp.strftime('%Y-%m-%d')})" for h in history])
            
            data.append({
                'Product Name': product.name,
                'Current Price': product.current_price,
                'Currency': product.currency,
                'Last Change %': last_change,
                'Platform': platform_str,
                'URLs': url_str,
                'Price History': price_history
            })
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            df = pd.DataFrame(data)
            df.to_csv(output, index=False)
        else:
            output.write('No data available')
            
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'price_data_export_{timestamp}.csv'
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    @app.route('/set-alert/<int:product_id>', methods=['POST'])
    @login_required
    def set_alert(product_id):
        """Set price alert for a product"""
        from models import db, Product, PriceAlert
        from forms import PriceAlertForm
        
        product = Product.query.get_or_404(product_id)
        
        # Check if product belongs to current user
        if not any(url.user_id == current_user.id for url in product.urls):
            flash('You do not have permission to set alerts for this product', 'danger')
            return redirect(url_for('dashboard'))
            
        form = PriceAlertForm()
        if form.validate_on_submit():
            alert_type = form.alert_type.data
            
            # Check if alert already exists
            existing_alert = PriceAlert.query.filter_by(
                product_id=product_id,
                user_id=current_user.id,
                alert_type=alert_type
            ).first()
            
            if existing_alert:
                # Update existing alert
                if alert_type == 'percentage_change':
                    existing_alert.percentage_threshold = form.percentage_threshold.data
                else:
                    existing_alert.target_price = form.target_price.data
                    
                existing_alert.is_active = True
                db.session.commit()
                flash('Alert updated successfully', 'success')
            else:
                # Create new alert
                new_alert = PriceAlert(
                    product_id=product_id,
                    user_id=current_user.id,
                    alert_type=alert_type
                )
                
                if alert_type == 'percentage_change':
                    new_alert.percentage_threshold = form.percentage_threshold.data
                else:
                    new_alert.target_price = form.target_price.data
                    
                db.session.add(new_alert)
                db.session.commit()
                flash('Alert set successfully', 'success')
                
        return redirect(url_for('product_detail', product_id=product_id))
    
    @app.route('/api/validate-url', methods=['POST'])
    @login_required
    def validate_url():
        """API endpoint to validate a URL"""
        from extractors import detect_platform, get_product_info
        
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'valid': False, 'message': 'No URL provided'})
            
        # Check platform
        platform = detect_platform(url)
        if not platform:
            return jsonify({'valid': False, 'message': 'Unsupported platform'})
            
        # Try to get product info
        product_data = get_product_info(url)
        
        if not product_data or 'price' not in product_data or product_data['price'] is None:
            return jsonify({'valid': False, 'message': 'Could not extract product information'})
            
        return jsonify({
            'valid': True,
            'platform': platform,
            'name': product_data.get('name', 'Unknown Product'),
            'price': product_data['price'],
            'currency': product_data.get('currency', 'SAR')
        })
    
    @app.route('/update-schedule', methods=['POST'])
    @login_required
    def update_schedule():
        """Update the price check schedule"""
        from forms import ScheduleForm
        
        form = ScheduleForm()
        if form.validate_on_submit():
            interval = form.interval.data
            
            # Handle custom interval
            if interval == 'custom' and form.custom_interval.data:
                interval = str(form.custom_interval.data)
                
            # Update in .env file
            with open('.env', 'r') as file:
                env_lines = file.readlines()
                
            with open('.env', 'w') as file:
                for line in env_lines:
                    if line.startswith('SCHEDULER_INTERVAL_MINUTES='):
                        file.write(f'SCHEDULER_INTERVAL_MINUTES={interval}\n')
                    else:
                        file.write(line)
            
            # Update scheduler dynamically
            app.apscheduler.remove_all_jobs()
            app.apscheduler.add_job(
                'tasks:update_all_prices',
                'interval',
                minutes=int(interval),
                args=[app]
            )
            
            flash('Schedule updated successfully', 'success')
            
        return redirect(url_for('dashboard'))

    # API endpoint to trigger price updates manually (for serverless environments)
    @app.route('/api/update-prices', methods=['POST'])
    def api_update_prices():
        # API key verification
        api_key = request.headers.get('X-API-Key')
        expected_api_key = os.environ.get('API_KEY')
        
        if not expected_api_key or api_key != expected_api_key:
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            from tasks import update_all_prices
            result = update_all_prices(app)
            return jsonify({'status': 'success', 'updated': result}), 200
        except Exception as e:
            app.logger.error(f"Error in API price update: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
