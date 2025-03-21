import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from dotenv import load_dotenv
import requests
import schedule
import time
from datetime import datetime
import threading
import csv
import io
from werkzeug.utils import secure_filename
import sqlite3
import pandas as pd
from contextlib import contextmanager
from monitor_schedule import init_db, get_monitor_schedules, export_monitor_schedules, run_schedule_updates

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('monitor.db', timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_app_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        # Create monitors table
        c.execute('''CREATE TABLE IF NOT EXISTS monitors
                     (AlertName TEXT PRIMARY KEY,
                      Connection TEXT NOT NULL,
                      ServiceType TEXT NOT NULL,
                      HealthCheck TEXT NOT NULL,
                      Response TEXT NOT NULL,
                      Description TEXT NOT NULL,
                      Status TEXT NOT NULL DEFAULT 'DOWN',
                      CheckTime TEXT NOT NULL,
                      ScheduleTime TEXT NOT NULL,
                      Frequency INTEGER NOT NULL DEFAULT 1)''')
        
        # Create services table
        c.execute('''CREATE TABLE IF NOT EXISTS services
                     (AlertName TEXT PRIMARY KEY,
                      ServiceType TEXT NOT NULL,
                      HostName TEXT NOT NULL,
                      CheckStatus TEXT NOT NULL DEFAULT 'DOWN')''')
        
        # Create monitorSchedule table
        c.execute('''CREATE TABLE IF NOT EXISTS monitorSchedule
                     (AlertName TEXT PRIMARY KEY,
                      HealthCheck TEXT NOT NULL,
                      ScheduleTime TEXT NOT NULL,
                      Frequency INTEGER NOT NULL,
                      HostName TEXT NOT NULL,
                      LastCheckTime TEXT NOT NULL,
                      Status TEXT NOT NULL DEFAULT 'DOWN')''')
        conn.commit()

# Initialize databases on startup
init_app_db()
init_db()

def check_service(monitor):
    try:
        service_type = monitor['ServiceType'].upper()
        if service_type in ['HTTP', 'HTTPS']:
            response = requests.get(monitor['Connection'], timeout=5)
            status = 'UP' if str(response.status_code) == monitor['Response'] else 'DOWN'
        elif service_type in ['TCP', 'UDP']:
            # Implement TCP/UDP check logic here
            status = 'UP'  # Placeholder
        else:
            # For custom service types, try HTTP check by default
            try:
                response = requests.get(monitor['Connection'], timeout=5)
                status = 'UP' if str(response.status_code) == monitor['Response'] else 'DOWN'
            except:
                status = 'DOWN'
        
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE monitors SET Status=?, CheckTime=? WHERE AlertName=?',
                     (status, datetime.now().isoformat(), monitor['AlertName']))
            conn.commit()
    except Exception as e:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE monitors SET Status=?, CheckTime=? WHERE AlertName=?',
                     ('DOWN', datetime.now().isoformat(), monitor['AlertName']))
            conn.commit()

def should_check_monitor(monitor):
    if not monitor.get('CheckTime'):
        return True
    
    last_check = datetime.fromisoformat(monitor['CheckTime'])
    now = datetime.now()
    
    frequency_seconds = monitor['Frequency'] * 60
    return (now - last_check).total_seconds() >= frequency_seconds

def run_health_checks():
    while True:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM monitors')
            monitors = [dict(zip(['AlertName', 'Connection', 'ServiceType', 'HealthCheck', 'Response', 'Description', 'Status', 'CheckTime', 'ScheduleTime', 'Frequency'], row)) 
                        for row in c.fetchall()]
        
        for monitor in monitors:
            if should_check_monitor(monitor):
                check_service(monitor)
        time.sleep(60)  # Check every minute

@app.route('/')
def home():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM monitors')
            monitors = [dict(zip(['AlertName', 'Connection', 'ServiceType', 'HealthCheck', 'Response', 'Description', 'Status', 'CheckTime', 'ScheduleTime', 'Frequency'], row)) 
                        for row in c.fetchall()]
        return render_template('index.html', monitors=monitors)
    except Exception as e:
        return render_template('index.html', monitors=[], message=f"Error loading monitors: {str(e)}")

@app.route('/monitor', methods=['POST'])
def create_monitor():
    try:
        data = request.form.to_dict()
        if 'CheckTime' not in data:
            data['CheckTime'] = datetime.now().isoformat()
        if 'ScheduleTime' in data:
            try:
                datetime.fromisoformat(data['ScheduleTime'])
            except ValueError:
                return "Invalid ScheduleTime format. Use ISO format.", 400
        if 'Frequency' not in data:
            data['Frequency'] = 1  # Default frequency of 1 minute
        else:
            try:
                data['Frequency'] = int(data['Frequency'])
                if data['Frequency'] < 1:
                    return "Frequency must be at least 1 minute", 400
            except ValueError:
                return "Frequency must be a number", 400

        with get_db_connection() as conn:
            c = conn.cursor()
            try:
                c.execute('''INSERT INTO monitors 
                           (AlertName, Connection, ServiceType, HealthCheck, Response, 
                            Description, Status, CheckTime, ScheduleTime, Frequency) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (data['AlertName'], data['Connection'], data['ServiceType'],
                          data['HealthCheck'], data['Response'], data['Description'],
                          data['Status'], data['CheckTime'], data['ScheduleTime'],
                          data['Frequency']))
                conn.commit()
                return redirect(url_for('home', message="Monitor added successfully!"))
            except sqlite3.IntegrityError:
                return redirect(url_for('home', message="Error: Alert Name already exists!"))
    except Exception as e:
        return redirect(url_for('home', message=f"Error adding monitor: {str(e)}"))

@app.route('/monitor/<AlertName>', methods=['POST', 'PUT'])
def update_monitor(AlertName):
    try:
        data = request.form.to_dict()
        if 'CheckTime' not in data:
            data['CheckTime'] = datetime.now().isoformat()
        if 'ScheduleTime' in data:
            try:
                datetime.fromisoformat(data['ScheduleTime'])
            except ValueError:
                return "Invalid ScheduleTime format. Use ISO format.", 400
        if 'Frequency' in data:
            try:
                data['Frequency'] = int(data['Frequency'])
                if data['Frequency'] < 1:
                    return "Frequency must be at least 1 minute", 400
            except ValueError:
                return "Frequency must be a number", 400

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''UPDATE monitors 
                       SET Connection=?, ServiceType=?, HealthCheck=?, Response=?,
                           Description=?, Status=?, CheckTime=?, ScheduleTime=?, Frequency=?
                       WHERE AlertName=?''',
                     (data['Connection'], data['ServiceType'], data['HealthCheck'],
                      data['Response'], data['Description'], data['Status'],
                      data['CheckTime'], data['ScheduleTime'], data['Frequency'],
                      AlertName))
            conn.commit()
        return redirect(url_for('home', message="Monitor updated successfully!"))
    except Exception as e:
        return redirect(url_for('home', message=f"Error updating monitor: {str(e)}"))

@app.route('/monitor/<AlertName>/delete', methods=['POST', 'DELETE'])
def delete_monitor(AlertName):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM monitors WHERE AlertName=?', (AlertName,))
            conn.commit()
        return redirect(url_for('home', message="Monitor deleted successfully!"))
    except Exception as e:
        return redirect(url_for('home', message=f"Error deleting monitor: {str(e)}"))

@app.route('/services')
def services():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM services')
            services = [dict(zip(['AlertName', 'ServiceType', 'HostName', 'CheckStatus'], row)) 
                        for row in c.fetchall()]
        return render_template('services.html', services=services)
    except Exception as e:
        return render_template('services.html', services=[], message=f"Error loading services: {str(e)}")

@app.route('/service', methods=['POST'])
def add_service():
    if request.method == 'POST':
        try:
            alert_name = request.form['AlertName']
            service_type = request.form['ServiceType']
            host_name = request.form['HostName']
            check_status = request.form['CheckStatus']
            
            with get_db_connection() as conn:
                c = conn.cursor()
                try:
                    c.execute('INSERT INTO services (AlertName, ServiceType, HostName, CheckStatus) VALUES (?, ?, ?, ?)',
                             (alert_name, service_type, host_name, check_status))
                    conn.commit()
                    message = "Service added successfully!"
                except sqlite3.IntegrityError:
                    message = "Error: Alert Name already exists!"
            
            return redirect(url_for('services', message=message))
        except Exception as e:
            return redirect(url_for('services', message=f"Error adding service: {str(e)}"))

@app.route('/service/<alert_name>', methods=['POST'])
def update_service(alert_name):
    if request.method == 'POST':
        try:
            service_type = request.form['ServiceType']
            host_name = request.form['HostName']
            check_status = request.form['CheckStatus']
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('UPDATE services SET ServiceType=?, HostName=?, CheckStatus=? WHERE AlertName=?',
                         (service_type, host_name, check_status, alert_name))
                conn.commit()
            return redirect(url_for('services', message="Service updated successfully!"))
        except Exception as e:
            return redirect(url_for('services', message=f"Error updating service: {str(e)}"))

@app.route('/service/<alert_name>/delete', methods=['POST'])
def delete_service(alert_name):
    if request.method == 'POST':
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('DELETE FROM services WHERE AlertName=?', (alert_name,))
                conn.commit()
            return redirect(url_for('services', message="Service deleted successfully!"))
        except Exception as e:
            return redirect(url_for('services', message=f"Error deleting service: {str(e)}"))

@app.route('/export', methods=['GET'])
def export_csv():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM monitors')
            monitors = [dict(zip(['AlertName', 'Connection', 'ServiceType', 'HealthCheck', 'Response', 'Description', 'Status', 'CheckTime', 'ScheduleTime', 'Frequency'], row)) 
                        for row in c.fetchall()]
        
        # Check if specific monitors were requested
        selected_monitors = request.args.get('monitors')
        if selected_monitors:
            selected_names = selected_monitors.split(',')
            monitors = [m for m in monitors if m['AlertName'] in selected_names]
        
        if not monitors:
            return redirect(url_for('home', message="No monitors to export"))
        
        # Create CSV in memory
        si = io.StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow(['AlertName', 'Connection', 'ServiceType', 'HealthCheck', 'Response', 
                        'Description', 'Status', 'ScheduleTime', 'Frequency'])
        
        # Write data
        for monitor in monitors:
            writer.writerow([
                monitor['AlertName'],
                monitor['Connection'],
                monitor['ServiceType'],
                monitor['HealthCheck'],
                monitor['Response'],
                monitor['Description'],
                monitor['Status'],
                monitor['ScheduleTime'],
                monitor['Frequency']
            ])
        
        # Create response
        output = si.getvalue()
        si.close()
        
        return send_file(
            io.BytesIO(output.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='monitors.csv'
        )
    except Exception as e:
        return redirect(url_for('home', message=f"Error exporting monitors: {str(e)}"))

@app.route('/import', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return redirect(url_for('home', message="Error: No file uploaded"))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('home', message="Error: No file selected"))
    
    if not file.filename.endswith('.csv'):
        return redirect(url_for('home', message="Error: Please upload a CSV file"))
    
    try:
        df = pd.read_csv(file)
        required_columns = ['AlertName', 'Connection', 'ServiceType', 'HealthCheck', 
                          'Response', 'Description', 'Status', 'ScheduleTime', 'Frequency']
        
        if not all(col in df.columns for col in required_columns):
            return redirect(url_for('home', message=f"Error: CSV must contain columns: {', '.join(required_columns)}"))
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        with get_db_connection() as conn:
            c = conn.cursor()
            for _, row in df.iterrows():
                try:
                    # Convert ScheduleTime string to datetime
                    if pd.notna(row.get('ScheduleTime')):
                        try:
                            datetime.fromisoformat(str(row['ScheduleTime']))
                        except ValueError:
                            error_messages.append(f"Invalid ScheduleTime format for {row.get('AlertName', 'Unknown')}: {row['ScheduleTime']}")
                            error_count += 1
                            continue
                    
                    # Convert Frequency to integer
                    if pd.notna(row.get('Frequency')):
                        try:
                            frequency = int(row['Frequency'])
                            if frequency < 1:
                                error_messages.append(f"Invalid Frequency value for {row.get('AlertName', 'Unknown')}: {frequency}")
                                error_count += 1
                                continue
                        except ValueError:
                            error_messages.append(f"Invalid Frequency format for {row.get('AlertName', 'Unknown')}: {row['Frequency']}")
                            error_count += 1
                            continue
                    else:
                        row['Frequency'] = 1  # Default frequency
                    
                    c.execute('''INSERT OR REPLACE INTO monitors 
                               (AlertName, Connection, ServiceType, HealthCheck, Response, 
                                Description, Status, ScheduleTime, Frequency) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (row['AlertName'], row['Connection'], row['ServiceType'],
                              row['HealthCheck'], row['Response'], row['Description'],
                              row['Status'], row['ScheduleTime'], row['Frequency']))
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Error in row {_ + 1}: {str(e)}")
            conn.commit()
        
        message = f"Import completed. Successfully processed: {success_count}"
        if error_count > 0:
            message += f"\nFailed: {error_count}\nErrors:\n" + "\n".join(error_messages)
        
        return redirect(url_for('home', message=message))
    
    except Exception as e:
        return redirect(url_for('home', message=f"Error processing CSV file: {str(e)}"))

@app.route('/service/import', methods=['POST'])
def import_services():
    if 'file' not in request.files:
        return redirect(url_for('services', message="Error: No file uploaded"))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('services', message="Error: No file selected"))
    
    if not file.filename.endswith('.csv'):
        return redirect(url_for('services', message="Error: Please upload a CSV file"))
    
    try:
        df = pd.read_csv(file)
        required_columns = ['AlertName', 'ServiceType', 'HostName', 'CheckStatus']
        
        if not all(col in df.columns for col in required_columns):
            return redirect(url_for('services', message="Error: CSV must contain columns: AlertName, ServiceType, HostName, CheckStatus"))
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        with get_db_connection() as conn:
            c = conn.cursor()
            for _, row in df.iterrows():
                try:
                    c.execute('INSERT OR REPLACE INTO services (AlertName, ServiceType, HostName, CheckStatus) VALUES (?, ?, ?, ?)',
                             (row['AlertName'], row['ServiceType'], row['HostName'], row['CheckStatus']))
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Error in row {_ + 1}: {str(e)}")
            conn.commit()
        
        message = f"Import completed. Successfully processed: {success_count}"
        if error_count > 0:
            message += f"\nFailed: {error_count}\nErrors:\n" + "\n".join(error_messages)
        
        return redirect(url_for('services', message=message))
    
    except Exception as e:
        return redirect(url_for('services', message=f"Error processing CSV file: {str(e)}"))

@app.route('/service/export')
def export_services():
    try:
        selected_services = request.args.get('services', '').split(',')
        selected_services = [s for s in selected_services if s]
        
        with get_db_connection() as conn:
            c = conn.cursor()
            if selected_services:
                placeholders = ','.join(['?' for _ in selected_services])
                c.execute(f'SELECT * FROM services WHERE AlertName IN ({placeholders})', selected_services)
            else:
                c.execute('SELECT * FROM services')
            
            services = c.fetchall()
        
        if not services:
            return redirect(url_for('services', message="No services to export"))
        
        df = pd.DataFrame(services, columns=['AlertName', 'ServiceType', 'HostName', 'CheckStatus'])
        
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='services.csv'
        )
    except Exception as e:
        return redirect(url_for('services', message=f"Error exporting services: {str(e)}"))

@app.route('/monitor-schedule')
def monitor_schedule():
    try:
        schedules = get_monitor_schedules()
        return render_template('monitor_schedule.html', schedules=schedules)
    except Exception as e:
        print(f"Error in monitor_schedule route: {str(e)}")
        return render_template('monitor_schedule.html', schedules=[], 
                             message=f"Error loading monitor schedules: {str(e)}")

@app.route('/monitor-schedule/export')
def export_schedule():
    try:
        output, error = export_monitor_schedules()
        if error:
            return redirect(url_for('monitor_schedule', message=error))
        
        return send_file(
            io.BytesIO(output.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='monitor_schedule.csv'
        )
    except Exception as e:
        return redirect(url_for('monitor_schedule', message=f"Error exporting schedules: {str(e)}"))

if __name__ == '__main__':
    # Start health check thread
    health_check_thread = threading.Thread(target=run_health_checks, daemon=True)
    health_check_thread.start()
    
    # Start schedule update thread
    schedule_thread = threading.Thread(target=run_schedule_updates, daemon=True)
    schedule_thread.start()
    
    app.run(debug=True)
