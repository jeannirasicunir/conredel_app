terraform {
  required_version = ">= 1.4.2"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }

  backend "s3" {
    bucket         = "monitoring-terraform-state-819743217287"
    key            = "monitoring.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock-table"
    skip_metadata_api_check = true
  }
}

provider "aws" {
  region = "us-east-1"
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_lock" {
  name         = "terraform-lock-table"
  hash_key     = "LockID"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "Terraform Lock Table"
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      billing_mode
    ]
  }
}

# Data source to handle existing table
data "aws_dynamodb_table" "terraform_lock" {
  name = "terraform-lock-table"

  # This allows the data source to be created even if the table doesn't exist yet
  depends_on = [aws_dynamodb_table.terraform_lock]
}

# VPC and Network Configuration
resource "aws_vpc" "monitoring_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "MonitoringVPC"
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.monitoring_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "MonitoringPublicSubnet1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.monitoring_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "MonitoringPublicSubnet2"
  }
}

resource "aws_internet_gateway" "monitoring_igw" {
  vpc_id = aws_vpc.monitoring_vpc.id

  tags = {
    Name = "MonitoringIGW"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.monitoring_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.monitoring_igw.id
  }

  tags = {
    Name = "MonitoringPublicRT"
  }
}

resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# Security Groups
resource "aws_security_group" "monitoring_sg" {
  name        = "monitoring-sg"
  description = "Security group for monitoring services"
  vpc_id      = aws_vpc.monitoring_vpc.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "MonitoringSG"
  }
}

# Import data blocks to reference existing ECR repositories
data "aws_ecr_repository" "backend" {
  name = "monitoring/backend"
}

data "aws_ecr_repository" "prometheus" {
  name = "monitoring/prometheus"
}

data "aws_ecr_repository" "grafana" {
  name = "monitoring/grafana"
}

# ECR Repositories with improved handling
resource "aws_ecr_repository" "backend" {
  name                 = "monitoring/backend"
  force_delete        = true
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    prevent_destroy = false
    ignore_changes = [
      name,
      image_tag_mutability,
      image_scanning_configuration,
    ]
    create_before_destroy = true
  }
}

resource "aws_ecr_repository" "prometheus" {
  name                 = "monitoring/prometheus"
  force_delete        = true
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    prevent_destroy = false
    ignore_changes = [
      name,
      image_tag_mutability,
      image_scanning_configuration,
    ]
    create_before_destroy = true
  }
}

resource "aws_ecr_repository" "grafana" {
  name                 = "monitoring/grafana"
  force_delete        = true
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    prevent_destroy = false
    ignore_changes = [
      name,
      image_tag_mutability,
      image_scanning_configuration,
    ]
    create_before_destroy = true
  }
}

# ECR Repository Policies
resource "aws_ecr_repository_policy" "backend_policy" {
  repository = aws_ecr_repository.backend.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPushPull"
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
      }
    ]
  })
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "monitoring-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "monitoring-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_role_policy" {
  name = "monitoring-ecs-task-role-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Cluster
resource "aws_ecs_cluster" "monitoring" {
  name = "monitoring-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "monitoring" {
  cluster_name = aws_ecs_cluster.monitoring.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# Task Definition
resource "aws_ecs_task_definition" "monitoring" {
  family                   = "monitoring"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "4096"
  memory                   = "8192"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${coalesce(try(data.aws_ecr_repository.backend.repository_url, ""), aws_ecr_repository.backend.repository_url)}:latest"
      essential = true
      entryPoint = ["sh", "-c"]
      command = ["python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DJANGO_SECRET_KEY"
          value = var.django_secret_key
        },
        {
          name  = "DJANGO_DEBUG"
          value = var.django_debug
        },
        {
          name  = "DJANGO_ALLOWED_HOSTS"
          value = "localhost,127.0.0.1,10.0.0.0/16,monitoring-alb-1585801177.us-east-1.elb.amazonaws.com"
        },
        {
          name  = "API_TOKEN"
          value = var.api_token
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/monitoring"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "backend"
        }
      }
    },
    {
      name  = "prometheus"
      image = "${coalesce(try(data.aws_ecr_repository.prometheus.repository_url, ""), aws_ecr_repository.prometheus.repository_url)}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 9090
          hostPort      = 9090
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/monitoring"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "prometheus"
        }
      }
    },
    {
      name  = "grafana"
      image = "${coalesce(try(data.aws_ecr_repository.grafana.repository_url, ""), aws_ecr_repository.grafana.repository_url)}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/monitoring"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "grafana"
        }
      }
    }
  ])
}

# Load Balancer
resource "aws_lb" "monitoring" {
  name               = "monitoring-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.monitoring_sg.id]
  subnets           = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
}

# Target Groups
resource "aws_lb_target_group" "backend" {
  name        = "backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.monitoring_vpc.id
  target_type = "ip"

  health_check {
    path                = "/api/health/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 10
    matcher             = "200-299"
  }
}

resource "aws_lb_target_group" "prometheus" {
  name        = "prometheus-tg"
  port        = 9090
  protocol    = "HTTP"
  vpc_id      = aws_vpc.monitoring_vpc.id
  target_type = "ip"

  health_check {
    path                = "/-/healthy"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 10
    matcher             = "200-299"
  }
}

resource "aws_lb_target_group" "grafana" {
  name        = "grafana-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.monitoring_vpc.id
  target_type = "ip"

  health_check {
    path                = "/api/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 10
    matcher             = "200-299"
  }
}

# Listeners
resource "aws_lb_listener" "backend" {
  load_balancer_arn = aws_lb.monitoring.arn
  port              = 8000
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

resource "aws_lb_listener" "prometheus" {
  load_balancer_arn = aws_lb.monitoring.arn
  port              = 9090
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.prometheus.arn
  }
}

resource "aws_lb_listener" "grafana" {
  load_balancer_arn = aws_lb.monitoring.arn
  port              = 3000
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana.arn
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "monitoring" {
  name              = "/ecs/monitoring"
  retention_in_days = 14
}

# ECS Service
resource "aws_ecs_service" "monitoring" {
  name            = "monitoring-service"
  cluster         = aws_ecs_cluster.monitoring.id
  task_definition = aws_ecs_task_definition.monitoring.arn
  desired_count   = var.desired_count

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.monitoring_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.prometheus.arn
    container_name   = "prometheus"
    container_port   = 9090
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.grafana.arn
    container_name   = "grafana"
    container_port   = 3000
  }

  deployment_controller {
    type = "ECS"
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 1
    base            = 1
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  force_new_deployment              = true
  wait_for_steady_state            = true

  # Enable health check grace period and debugging
  health_check_grace_period_seconds = 120
  enable_execute_command = true

  depends_on = [
    aws_lb_listener.backend,
    aws_lb_listener.prometheus,
    aws_lb_listener.grafana,
    aws_cloudwatch_log_group.monitoring
  ]
}