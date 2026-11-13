
# RDS Security Group
resource "aws_security_group" "rds_sg" {
  name        = "bus-booking-rds-sg"
  description = "Allow MySQL from EKS worker nodes"
  vpc_id      = var.vpc_id

  ingress {
    description     = "MySQL access from EKS nodes"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.eks_node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "bus-booking-rds-sg"
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "bus_booking_subnet" {
  name       = "bus-booking-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "bus-booking-rds-subnet"
  }
}

# RDS MySQL Database
resource "aws_db_instance" "bus_booking_db" {
  identifier = "bus-booking-mysql"

  engine         = "mysql"
  engine_version = "8.0"

  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "busbooking"
  username = var.db_username
  password = var.db_password

  port = 3306

  db_subnet_group_name   = aws_db_subnet_group.bus_booking_subnet.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = false
  multi_az            = false

  backup_retention_period = 7
  skip_final_snapshot     = true
  deletion_protection     = false

  auto_minor_version_upgrade = true

  tags = {
    Name        = "bus-booking-rds"
    Environment = "dev"
    Project     = "bus-booking"
  }
}
