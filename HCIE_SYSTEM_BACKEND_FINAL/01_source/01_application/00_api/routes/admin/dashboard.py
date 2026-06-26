"""
Health Dashboard API Routes
Integrated web dashboard for monitoring all services
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from datetime import datetime

router = APIRouter(prefix="/admin/dashboard", tags=["dashboard"])

# HTML Template for Dashboard (integrated into FastAPI)
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HCIE Service Health Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .summary {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            text-align: center;
        }
        
        .summary-item {
            padding: 15px;
            border-radius: 10px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        
        .summary-item h3 {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .summary-item p {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .service-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .service-card:hover {
            transform: translateY(-5px);
        }
        
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .service-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        
        .service-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-healthy {
            background: #4CAF50;
            color: white;
        }
        
        .status-unhealthy {
            background: #f44336;
            color: white;
        }
        
        .service-description {
            color: #666;
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        
        .service-details {
            font-size: 0.85em;
            color: #555;
        }
        
        .service-details pre {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .refresh-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            margin: 20px auto;
            display: block;
            transition: background 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #45a049;
        }
        
        .timestamp {
            text-align: center;
            color: white;
            opacity: 0.8;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        .actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        
        .action-btn {
            padding: 5px 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            transition: background 0.3s ease;
        }
        
        .restart-btn {
            background: #ff9800;
            color: white;
        }
        
        .restart-btn:hover {
            background: #e68900;
        }
        
        .logs-btn {
            background: #2196F3;
            color: white;
        }
        
        .logs-btn:hover {
            background: #1976D2;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 800px;
            max-height: 80%;
            overflow-y: auto;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        .logs-content {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .api-status {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .api-endpoints {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .endpoint-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
        }
        
        .endpoint-method {
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }
        
        .endpoint-path {
            font-family: monospace;
            color: #333;
            margin-bottom: 5px;
        }
        
        .endpoint-description {
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>HCIE Service Health Dashboard</h1>
            <p>Real-time monitoring for HCIE infrastructure services</p>
        </div>
        
        <div class="api-status">
            <h3>Available API Endpoints</h3>
            <div class="api-endpoints">
                <div class="endpoint-card">
                    <div class="endpoint-method">GET</div>
                    <div class="endpoint-path">/admin/services/status</div>
                    <div class="endpoint-description">Get status of all services</div>
                </div>
                <div class="endpoint-card">
                    <div class="endpoint-method">GET</div>
                    <div class="endpoint-path">/admin/services/status/{service}</div>
                    <div class="endpoint-description">Get status of specific service</div>
                </div>
                <div class="endpoint-card">
                    <div class="endpoint-method">POST</div>
                    <div class="endpoint-path">/admin/services/restart/{service}</div>
                    <div class="endpoint-description">Restart specific service</div>
                </div>
                <div class="endpoint-card">
                    <div class="endpoint-method">GET</div>
                    <div class="endpoint-path">/admin/services/logs/{service}</div>
                    <div class="endpoint-description">Get service logs</div>
                </div>
                <div class="endpoint-card">
                    <div class="endpoint-method">POST</div>
                    <div class="endpoint-path">/admin/services/setup-cdc</div>
                    <div class="endpoint-description">Setup Debezium CDC connector</div>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-grid">
                <div class="summary-item">
                    <h3 id="total-services">-</h3>
                    <p>Total Services</p>
                </div>
                <div class="summary-item">
                    <h3 id="healthy-services">-</h3>
                    <p>Healthy Services</p>
                </div>
                <div class="summary-item">
                    <h3 id="unhealthy-services">-</h3>
                    <p>Unhealthy Services</p>
                </div>
                <div class="summary-item">
                    <h3 id="health-percentage">-</h3>
                    <p>Health %</p>
                </div>
            </div>
        </div>
        
        <div id="services-container" class="services">
            <!-- Service cards will be populated here -->
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">Refresh Data</button>
        
        <div class="timestamp" id="timestamp">Last updated: -</div>
    </div>
    
    <!-- Logs Modal -->
    <div id="logsModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeLogsModal()">&times;</span>
            <h2 id="logs-title">Service Logs</h2>
            <div class="logs-content" id="logs-content">Loading...</div>
        </div>
    </div>
    
    <script>
        let currentData = null;
        
        function refreshData() {
            fetch('/admin/services/status')
                .then(response => response.json())
                .then(data => {
                    currentData = data;
                    updateDashboard(data);
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    showError('Failed to fetch service status');
                });
        }
        
        function showError(message) {
            const servicesContainer = document.getElementById('services-container');
            servicesContainer.innerHTML = `<div style="background: white; padding: 20px; border-radius: 10px; color: #f44336;">${message}</div>`;
        }
        
        function updateDashboard(data) {
            // Update summary
            const summary = data.summary;
            document.getElementById('total-services').textContent = summary.total_services;
            document.getElementById('healthy-services').textContent = summary.healthy_services;
            document.getElementById('unhealthy-services').textContent = summary.unhealthy_services;
            document.getElementById('health-percentage').textContent = summary.health_percentage.toFixed(1) + '%';
            
            // Update timestamp
            document.getElementById('timestamp').textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleString();
            
            // Update services
            const servicesContainer = document.getElementById('services-container');
            servicesContainer.innerHTML = '';
            
            for (const [serviceName, serviceData] of Object.entries(data.services)) {
                const serviceCard = createServiceCard(serviceName, serviceData);
                servicesContainer.appendChild(serviceCard);
            }
        }
        
        function createServiceCard(serviceName, serviceData) {
            const card = document.createElement('div');
            card.className = 'service-card';
            
            let statusClass = 'status-unhealthy';
            let statusText = 'Unknown';
            
            if (serviceData.health) {
                statusClass = serviceData.health.status === 'healthy' ? 'status-healthy' : 'status-unhealthy';
                statusText = serviceData.health.status.toUpperCase();
            } else if (serviceData.error) {
                statusClass = 'status-unhealthy';
                statusText = 'ERROR';
            }
            
            const description = getServiceDescription(serviceName);
            
            card.innerHTML = `
                <div class="service-header">
                    <div class="service-name">${serviceName}</div>
                    <div class="service-status ${statusClass}">${statusText}</div>
                </div>
                <div class="service-description">${description}</div>
                <div class="service-details">
                    <pre>${JSON.stringify(serviceData.health || serviceData.error, null, 2)}</pre>
                </div>
                <div class="actions">
                    <button class="action-btn restart-btn" onclick="restartService('${serviceName}')">Restart</button>
                    <button class="action-btn logs-btn" onclick="showLogs('${serviceName}')">View Logs</button>
                </div>
            `;
            
            return card;
        }
        
        function getServiceDescription(serviceName) {
            const descriptions = {
                'redis': 'Redis Cache Layer',
                'postgres': 'PostgreSQL Database',
                'kafka': 'Kafka Event Streaming',
                'api': 'HCIE API Service',
                'schema-registry': 'Kafka Schema Registry',
                'kafka-connect': 'Kafka Connect (Debezium)',
                'kafka-ui': 'Kafka Management UI',
                'prometheus': 'Prometheus Metrics',
                'grafana': 'Grafana Visualization'
            };
            return descriptions[serviceName] || 'Service';
        }
        
        function restartService(serviceName) {
            if (confirm(`Are you sure you want to restart ${serviceName}?`)) {
                fetch(`/admin/services/restart/${serviceName}`, {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert(JSON.stringify(data, null, 2));
                        setTimeout(refreshData, 2000); // Refresh after 2 seconds
                    })
                    .catch(error => {
                        console.error('Error restarting service:', error);
                        alert('Error restarting service: ' + error);
                    });
            }
        }
        
        function showLogs(serviceName) {
            document.getElementById('logs-title').textContent = `${serviceName} Logs`;
            document.getElementById('logs-content').textContent = 'Loading...';
            document.getElementById('logsModal').style.display = 'block';
            
            fetch(`/admin/services/logs/${serviceName}`)
                .then(response => response.json())
                .then(data => {
                    const logsContent = document.getElementById('logs-content');
                    if (data.logs) {
                        logsContent.textContent = data.logs;
                    } else if (data.error) {
                        logsContent.textContent = 'Error: ' + data.error;
                    } else {
                        logsContent.textContent = 'No logs available';
                    }
                })
                .catch(error => {
                    console.error('Error fetching logs:', error);
                    document.getElementById('logs-content').textContent = 'Error fetching logs: ' + error;
                });
        }
        
        function closeLogsModal() {
            document.getElementById('logsModal').style.display = 'none';
        }
        
        // Auto-refresh every 10 seconds
        setInterval(refreshData, 10000);
        
        // Initial load
        refreshData();
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('logsModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
async def health_dashboard():
    """Main health dashboard page"""
    return DASHBOARD_TEMPLATE

@router.get("/api-status")
async def api_status_info():
    """Get API status information"""
    return {
        "api_name": "HCIE Service Management API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/admin/dashboard/",
            "all_services": "/admin/services/status",
            "single_service": "/admin/services/status/{service_name}",
            "restart_service": "/admin/services/restart/{service_name}",
            "service_logs": "/admin/services/logs/{service_name}",
            "setup_cdc": "/admin/services/setup-cdc"
        },
        "timestamp": datetime.now().isoformat()
    }
