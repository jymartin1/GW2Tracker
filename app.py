from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import json
import threading
from datetime import datetime, timedelta
from gw2_api import GW2API
from legendary_data import LEGENDARY_REQUIREMENTS
from progress_calculator import ProgressCalculator
from progress_tracker import progress_tracker
from account_cache import account_cache
from data_fetcher import DataFetcher

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

@app.route('/')
def index():
    if 'api_key' not in session:
        return render_template('index.html')
    
    gw2_api = GW2API(session['api_key'])
    try:
        account_info = gw2_api.get_account_info()
        return render_template('index.html', account=account_info, legendaries=LEGENDARY_REQUIREMENTS.keys())
    except Exception as e:
        flash(f'Error accessing GW2 API: {str(e)}', 'error')
        session.pop('api_key', None)  # Remove invalid key
        return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    api_key = request.form.get('api_key')
    if not api_key:
        flash('Please enter your API key', 'error')
        return redirect(url_for('index'))
    
    # Check if we already have cached data
    if account_cache.is_cached(api_key):
        cached_data = account_cache.get_cached_data(api_key)
        account_info = cached_data['account_info']
        session['api_key'] = api_key
        flash(f'Welcome back, {account_info["name"]}!', 'success')
        return redirect(url_for('index'))
    
    # Validate API key first
    gw2_api = GW2API(api_key)
    try:
        account_info = gw2_api.get_account_info()
        session['api_key'] = api_key
        
        # Start background data fetching
        task_id = progress_tracker.create_task(f"account_scan_{account_info['name']}")
        
        def fetch_data_async():
            try:
                fetcher = DataFetcher(api_key, progress_tracker, task_id)
                data = fetcher.fetch_all_account_data()
                account_cache.set_cached_data(api_key, data)
                progress_tracker.complete_task(task_id, True, {"message": "Account data cached successfully"})
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error fetching account data: {error_details}")
                progress_tracker.complete_task(task_id, False, error=str(e))
        
        thread = threading.Thread(target=fetch_data_async)
        thread.daemon = True
        thread.start()
        
        flash(f'Welcome, {account_info["name"]}! Scanning your account data in the background...', 'success')
        return redirect(url_for('account_scan_status', task_id=task_id))
        
    except Exception as e:
        flash(f'Invalid API key or API error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/account-scan/<task_id>')
def account_scan_status(task_id):
    """Show account scanning progress"""
    if 'api_key' not in session:
        return redirect(url_for('index'))
    
    return render_template('account_scan.html', task_id=task_id)

@app.route('/refresh-data')
def refresh_data():
    """Refresh account data"""
    if 'api_key' not in session:
        return redirect(url_for('index'))
    
    api_key = session['api_key']
    
    # Invalidate existing cache
    account_cache.invalidate_cache(api_key)
    
    # Get account info for task naming
    try:
        gw2_api = GW2API(api_key)
        account_info = gw2_api.get_account_info()
        account_name = account_info.get('name', 'Unknown')
    except:
        account_name = 'Unknown'
    
    # Start background data fetching
    task_id = progress_tracker.create_task(f"refresh_{account_name}")
    
    def fetch_data_async():
        try:
            fetcher = DataFetcher(api_key, progress_tracker, task_id)
            data = fetcher.fetch_all_account_data()
            account_cache.set_cached_data(api_key, data)
            progress_tracker.complete_task(task_id, True, {"message": "Account data refreshed successfully"})
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error refreshing account data: {error_details}")
            progress_tracker.complete_task(task_id, False, error=str(e))
    
    thread = threading.Thread(target=fetch_data_async)
    thread.daemon = True
    thread.start()
    
    flash('Refreshing account data...', 'info')
    return redirect(url_for('account_scan_status', task_id=task_id))

@app.route('/logout')
def logout():
    session.pop('api_key', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/legendary/<legendary_name>')
def legendary_progress(legendary_name):
    if 'api_key' not in session:
        return redirect(url_for('index'))
    
    if legendary_name not in LEGENDARY_REQUIREMENTS:
        flash('Legendary not found', 'error')
        return redirect(url_for('index'))
    
    api_key = session['api_key']
    
    # Check if we have cached data
    if not account_cache.is_cached(api_key):
        flash('Account data not available. Please refresh your data.', 'warning')
        return redirect(url_for('index'))
    
    # Get cached data
    cached_data = account_cache.get_cached_data(api_key)
    
    # Calculate progress using cached data (this should be fast now)
    try:
        calculator = ProgressCalculator(None)  # No API needed, using cached data
        progress = calculator.calculate_progress_from_cache(legendary_name, cached_data)
        return render_template('legendary_progress.html', 
                             legendary_name=legendary_name,
                             progress=progress,
                             requirements=LEGENDARY_REQUIREMENTS[legendary_name])
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error calculating progress: {error_details}")
        flash(f'Error calculating progress: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """AJAX endpoint to get progress updates"""
    status = progress_tracker.get_task_status(task_id)
    if not status:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)