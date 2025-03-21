# Services-Monitoring-App

A web-based application for monitoring services and managing health checks with a modern, responsive interface.

## Features

- **Alerts Management**
  - Create, read, update, and delete service monitors
  - Configure health checks with custom schedules
  - Support for HTTP, HTTPS, TCP, and UDP services
  - Real-time status monitoring
  - Export monitor data to CSV

- **Service Management**
  - Add and manage service configurations
  - Track service status (UP/DOWN)
  - Export service data to CSV
  - Bulk operations support

- **Monitor Schedule**
  - View active monitor schedules
  - Track last check times
  - Auto-refresh status every 5 minutes
  - Export schedule data to CSV

- **Modern UI/UX**
  - Responsive design that works on all devices
  - Real-time status updates
  - Intuitive forms and tables
  - Consistent styling across all pages
  - User-friendly navigation

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone services-monitoring-app

Directory Structure
-----------------------------

services-monitoring-app/
    ├── .env
    ├── .vscode
    ├── settings.json
    ├── app.py
    ├── docker-compose.yml
    ├── Dockerfile
    ├── docs/
    │   └── README.md
    ├── monitor.db
    ├── monitor_schedule.py
    ├── README.md
    ├── requirements.txt
    ├── templates/
    │   ├── base.html
    │   ├── index.html
    │   ├── monitor_schedule.html
    │   └── services.html
    └── uploads
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with the following variables:
```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
```

2. Configure database settings in `app.py` if needed.

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Application Structure

### Pages

1. **Monitors** (`/`)
   - Create and manage service monitors
   - Configure health checks and schedules
   - View monitor status and history

2. **Services** (`/services`)
   - Add and manage service configurations
   - Track service status
   - Export service data

3. **Monitor Schedule** (`/monitor-schedule`)
   - View active monitor schedules
   - Track last check times
   - Export schedule data

### Database Schema

#### Monitors Table
- AlertName (Primary Key)
- Connection
- ServiceType
- HealthCheck
- Response
- Description
- Status
- ScheduleTime
- Frequency

#### Services Table
- AlertName (Primary Key)
- ServiceType
- HostName
- CheckStatus

#### MonitorSchedule Table
- AlertName (Primary Key)
- HealthCheck
- ScheduleTime
- Frequency
- HostName
- LastCheckTime
- Status

## Features in Detail

### Monitor Management
- Create monitors with custom health check configurations
- Set up schedules for regular health checks
- Configure expected responses
- Track monitor status in real-time
- Export monitor data to CSV

### Service Management
- Add services with host information
- Track service status
- Configure service types (HTTP, HTTPS, TCP, UDP)
- Export service data to CSV
- Bulk operations for multiple services

### Monitor Schedule
- View all active monitor schedules
- Track last check times
- Monitor status updates
- Export schedule data
- Auto-refresh every 5 minutes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, please open an issue in the repository or contact the maintainers.

