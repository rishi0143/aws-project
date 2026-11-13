
# -----------------------------------------
# RDS Security Group
# -----------------------------------------

resource "aws_security_group" "rds_sg" {
  name        = "bus-booking-rds-sg"
  description = "Allow MySQL access from EKS worker nodes"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "MySQL access from EKS nodes"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  # No unrestricted egress rule.
  # Security groups are stateful.

  tags = {
    Name        = "bus-booking-rds-sg"
    Environment = "dev"
  }
}

# -----------------------------------------
# RDS DB Subnet Group
# -----------------------------------------

resource "aws_db_subnet_group" "bus_booking_subnet" {
  name        = "bus-booking-db-subnet"
  description = "Private subnets for Bus Booking RDS"

  subnet_ids = module.vpc.private_subnets

  tags = {
    Name        = "bus-booking-db-subnet"
    Environment = "dev"
  }
}

# -----------------------------------------
# AWS RDS MySQL Database
# -----------------------------------------

resource "aws_db_instance" "bus_booking_db" {
  identifier = "bus-booking-mysql"

  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 3306

  db_subnet_group_name   = aws_db_subnet_group.bus_booking_subnet.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  publicly_accessible = false
  multi_az            = false

  backup_retention_period = 7

  auto_minor_version_upgrade = true
  deletion_protection        = false
  skip_final_snapshot        = true

  tags = {
    Name        = "bus-booking-mysql"
    Environment = "dev"
    Project     = "BusBooking"
  }
}
