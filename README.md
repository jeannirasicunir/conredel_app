# Monitoring and Task Management System

## Project Overview

This project implements a comprehensive monitoring and task management system with the following key components:

1. **Backend Service**: A Django-based REST API that handles task management and system monitoring
2. **Monitoring Stack**: Prometheus and Grafana setup for metrics collection and visualization
3. **Traffic Simulators**: Tools to test system behavior under various conditions
4. **Infrastructure as Code**: Terraform configurations for AWS deployment

## System Architecture

The system is containerized using Docker and can be deployed either locally or to AWS ECS Fargate. It consists of:

- Django Backend API
- Prometheus Metrics Server
- Grafana Dashboards
- Nginx Reverse Proxy

## Repository Structure

```
├── backend/                 # Django backend application
│   ├── apps/               # Django apps
│   │   ├── monitoring/     # Monitoring and metrics
│   │   ├── tasks/         # Task management
│   │   └── users/         # User management
│   ├── traffic_simulator/  # Traffic simulation tools
│   └── README.md          # Backend setup and configuration
├── deployment/             # Infrastructure deployment
│   └── terraform/         # Terraform configurations
│       └── README.md      # Deployment guide and workflows
├── monitoring/            # Monitoring stack setup
│   ├── grafana/          # Grafana configuration and dashboards
│   └── README.md         # Monitoring stack documentation
├── docker-compose.yml    # Local development setup
└── nginx.conf            # Nginx reverse proxy configuration
```

## Component Documentation

### Backend Service ([backend/README.md](backend/README.md))
- Django REST API setup and configuration
- Application structure and endpoints
- Database models and migrations
- Testing instructions

### Traffic Simulator ([backend/traffic_simulator/README.md](backend/traffic_simulator/README.md))
- Tools for simulating various traffic patterns
- Rate limiting tests
- Slow request simulation
- General traffic load testing

### Deployment Guide ([deployment/terraform/README.md](deployment/terraform/README.md))
- AWS ECS Fargate deployment configuration
- GitHub Actions CI/CD workflow
- Infrastructure as Code with Terraform
- Security and access management
- Cost optimization strategies

### Monitoring Stack ([monitoring/README.md](monitoring/README.md))
- Prometheus configuration
- Grafana dashboards setup
- Metrics collection and visualization
- Alert configuration
- Performance monitoring

## Getting Started

1. **Environment Setup**
   Create a `.env` file in the `backend/` directory with the following variables:
   ```env
   DJANGO_SECRET_KEY=your_secret_key_here
   API_TOKEN=your_api_token_here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

2. **Local Development Setup**
   ```bash
   docker-compose up -d
   ```
   This will start:
   - Backend service on port 8000
   - Prometheus on port 9090
   - Grafana on port 3000

3. **Access Services**
   - Backend API: http://localhost:8000
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000

3. **Run Traffic Simulators**
   ```bash
   cd backend/traffic_simulator
   python simulate_traffic.py
   python simulate_traffic_rate_limit.py
   python simulate_traffic_slow.py
   ```

## Key Features

1. **Task Management**
   - REST API for task CRUD operations
   - Priority-based task scheduling
   - Task status tracking

2. **Monitoring**
   - Request rate monitoring
   - Response time tracking
   - Error rate visualization
   - System health checks

3. **Performance Analysis**
   - Custom Grafana dashboards
   - Real-time metrics
   - Historical data analysis
   - Alert configuration

## Development Tools

- **Backend**: Python 3.8+, Django 4.x
- **Monitoring**: Prometheus, Grafana
- **Infrastructure**: Terraform, AWS
- **CI/CD**: GitHub Actions
- **Containerization**: Docker, Docker Compose

## Metrics and Monitoring

The system collects and visualizes:
- API endpoint performance
- Request/response timing
- Error rates and types
- System resource usage
- Custom business metrics

## Security

- AWS IAM role-based access
- Secure secret management
- Network isolation
- API authentication
- Rate limiting

## Deployment

Deployment is automated through GitHub Actions and supports:
1. Continuous Integration testing
2. Automated builds and pushes to ECR
3. Infrastructure updates via Terraform
4. Zero-downtime deployments
5. Health check validation


## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file. 
