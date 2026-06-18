FROM grafana/grafana:latest

# Copy dashboards
COPY dashboards /etc/grafana/dashboards

# Copy provisioning configurations
COPY provisioning /etc/grafana/provisioning

# Environment variables
ENV GF_INSTALL_PLUGINS="grafana-clock-panel,grafana-simple-json-datasource"
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_PATHS_PROVISIONING=/etc/grafana/provisioning
ENV GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH="/etc/grafana/dashboards/general_metrics.json"