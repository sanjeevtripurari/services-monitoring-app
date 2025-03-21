import sqlite3
import time
from datetime import datetime
import threading
from contextlib import contextmanager
import pandas as pd
import io
import csv
import os

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('monitor.db', timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        # Create monitorSchedule table
        c.execute('''CREATE TABLE IF NOT EXISTS monitorSchedule
                     (AlertName TEXT PRIMARY KEY,
                      HealthCheck TEXT NOT NULL,
                      ScheduleTime TEXT NOT NULL,
                      Frequency INTEGER NOT NULL,
                      HostName TEXT NOT NULL,
                      LastCheckTime TEXT,
                      Status TEXT NOT NULL)''')
        conn.commit()

def update_monitor_schedule():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # Get all monitors and services with UP status
            c.execute('''
                SELECT m.AlertName, m.HealthCheck, m.ScheduleTime, m.Frequency, s.HostName
                FROM monitors m
                JOIN services s ON m.AlertName = s.AlertName
                WHERE m.Status = 'UP' AND s.CheckStatus = 'UP'
            ''')
            active_monitors = c.fetchall()
            
            # Update monitorSchedule table
            for monitor in active_monitors:
                c.execute('''
                    INSERT OR REPLACE INTO monitorSchedule 
                    (AlertName, HealthCheck, ScheduleTime, Frequency, HostName, LastCheckTime, Status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (monitor['AlertName'], monitor['HealthCheck'], monitor['ScheduleTime'],
                      monitor['Frequency'], monitor['HostName'], datetime.now().isoformat(), 'UP'))
            conn.commit()
    except Exception as e:
        print(f"Error updating monitor schedule: {str(e)}")

def get_monitor_schedules():
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM monitorSchedule')
            return [dict(zip(['AlertName', 'HealthCheck', 'ScheduleTime', 'Frequency', 
                            'HostName', 'LastCheckTime', 'Status'], row)) 
                    for row in c.fetchall()]
    except Exception as e:
        print(f"Error getting monitor schedules: {str(e)}")
        return []

def export_monitor_schedules():
    try:
        schedules = get_monitor_schedules()
        if not schedules:
            return None, "No schedules to export"
        
        # Create CSV in memory
        si = io.StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow(['AlertName', 'HealthCheck', 'ScheduleTime', 'Frequency', 
                        'HostName', 'LastCheckTime', 'Status'])
        
        # Write data
        for schedule in schedules:
            writer.writerow([
                schedule['AlertName'],
                schedule['HealthCheck'],
                schedule['ScheduleTime'],
                schedule['Frequency'],
                schedule['HostName'],
                schedule['LastCheckTime'],
                schedule['Status']
            ])
        
        # Create response
        output = si.getvalue()
        si.close()
        
        return output, None
    except Exception as e:
        return None, f"Error exporting schedules: {str(e)}"

def run_schedule_updates():
    while True:
        update_monitor_schedule()
        time.sleep(60)  # Update every minute 