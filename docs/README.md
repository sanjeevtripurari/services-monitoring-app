# Technical Documentation

## Application Structure

### Core Components

1. **Flask Application (`app.py`)**
   - Main application entry point
   - Route definitions and request handlers
   - Database initialization and management
   - Health check scheduling and execution

2. **Templates**
   - `base.html`: Base template with common layout and styles
   - `index.html`: Monitor management interface
   - `services.html`: Service management interface
   - `monitor_schedule.html`: Monitor schedule view

3. **Database**
   - SQLite database with three main tables:
     - `monitors`: Service monitor configurations
     - `services`: Service status tracking
     - `monitorSchedule`: Active monitor schedules

### Key Functions

#### Database Management
```python
def init_db():
    """Initialize database tables if they don't exist."""
    with get_db_connection() as conn:
        # Create monitors table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS monitors (
                AlertName TEXT PRIMARY KEY,
                Connection TEXT NOT NULL,
                ServiceType TEXT NOT NULL,
                HealthCheck TEXT NOT NULL,
                Response TEXT NOT NULL,
                Description TEXT NOT NULL,
                Status TEXT NOT NULL,
                ScheduleTime TEXT NOT NULL,
                Frequency INTEGER NOT NULL
            )
        ''')
        
        # Create services table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS services (
                AlertName TEXT PRIMARY KEY,
                ServiceType TEXT NOT NULL,
                HostName TEXT NOT NULL,
                CheckStatus TEXT NOT NULL
            )
        ''')
        
        # Create monitorSchedule table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS monitorSchedule (
                AlertName TEXT PRIMARY KEY,
                HealthCheck TEXT NOT NULL,
                ScheduleTime TEXT NOT NULL,
                Frequency INTEGER NOT NULL,
                HostName TEXT NOT NULL,
                LastCheckTime TEXT NOT NULL,
                Status TEXT NOT NULL
            )
        ''')
```

#### Health Check System
```python
def check_service(monitor):
    """Perform health check for a service."""
    try:
        # Implementation of health check logic
        # Returns True if service is healthy, False otherwise
        pass
    except Exception as e:
        print(f"Error checking service {monitor['AlertName']}: {str(e)}")
        return False

def should_check_monitor(monitor):
    """Determine if a monitor should be checked based on schedule."""
    try:
        # Implementation of schedule checking logic
        # Returns True if monitor should be checked, False otherwise
        pass
    except Exception as e:
        print(f"Error checking schedule for {monitor['AlertName']}: {str(e)}")
        return False
```

#### Schedule Management
```python
def update_monitor_schedule():
    """Update monitor schedule based on active monitors and services."""
    try:
        # Implementation of schedule update logic
        # Updates monitorSchedule table with active monitors
        pass
    except Exception as e:
        print(f"Error updating monitor schedule: {str(e)}")
```

### Frontend Components

#### Base Template (`base.html`)
- Common layout structure
- CSS variables for consistent styling
- Responsive design implementation
- Navigation menu
- Message display system

#### Monitor Interface (`index.html`)
- Monitor creation form
- Monitor list with status indicators
- Export functionality
- Edit/Delete operations

#### Service Interface (`services.html`)
- Service creation form
- Service list with status indicators
- Export functionality
- Edit/Delete operations

#### Schedule Interface (`monitor_schedule.html`)
- Active schedule display
- Status indicators
- Auto-refresh functionality
- Export functionality

### JavaScript Functions

#### Common Functions
```javascript
function toggleAll(source) {
    // Toggle all checkboxes in a table
}

function exportSelected() {
    // Export selected items to CSV
}

function resetForm() {
    // Reset form fields to default values
}
```

#### Monitor-specific Functions
```javascript
function editMonitor(alertName) {
    // Load monitor data into edit form
}

function deleteMonitor(alertName) {
    // Delete monitor with confirmation
}
```

#### Service-specific Functions
```javascript
function editService(alertName) {
    // Load service data into edit form
}

function deleteService(alertName) {
    // Delete service with confirmation
}
```

### CSS Styling

#### Color Variables
```css
:root {
    --primary-color: #007bff;
    --primary-hover: #0056b3;
    --success-color: #28a745;
    --success-hover: #218838;
    --danger-color: #dc3545;
    --danger-hover: #c82333;
    --light-bg: #f8f9fa;
    --border-color: #dee2e6;
    --text-color: #333;
    --text-muted: #6c757d;
}
```

#### Responsive Design
```css
@media (max-width: 768px) {
    .container {
        margin: 10px;
        padding: 15px;
    }
    
    .header {
        flex-direction: column;
        gap: 15px;
        text-align: center;
    }
    
    .nav-links {
        flex-wrap: wrap;
        justify-content: center;
    }
    
    table {
        display: block;
        overflow-x: auto;
    }
}
```

## Error Handling

### Database Errors
- Connection management using context managers
- Transaction handling for data integrity
- Error logging and user feedback

### Health Check Errors
- Exception handling for network requests
- Timeout handling
- Status reporting

### Frontend Errors
- Form validation
- API error handling
- User feedback messages

## Security Considerations

1. **Input Validation**
   - Form data validation
   - SQL injection prevention
   - XSS prevention

2. **File Operations**
   - Secure file handling
   - File type validation
   - Size limits

3. **Database Security**
   - Connection pooling
   - Prepared statements
   - Error handling

## Performance Optimization

1. **Database**
   - Indexed columns
   - Efficient queries
   - Connection pooling

2. **Frontend**
   - Minified CSS/JS
   - Efficient DOM updates
   - Lazy loading

3. **Health Checks**
   - Asynchronous execution
   - Timeout handling
   - Resource management

## Deployment

### Requirements
- Python 3.8+
- SQLite3
- Required Python packages

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Configuration
```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
```

### Running the Application
```bash
python app.py
```

## Maintenance

### Database Maintenance
- Regular backups
- Index optimization
- Data cleanup

### Log Management
- Error logging
- Access logging
- Performance monitoring

### Updates
- Package updates
- Security patches
- Feature additions 