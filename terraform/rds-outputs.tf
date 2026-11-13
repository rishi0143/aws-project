
output "rds_endpoint" {
  description = "RDS MySQL endpoint"
  value       = aws_db_instance.bus_booking_db.address
}

output "rds_port" {
  description = "RDS MySQL port"
  value       = aws_db_instance.bus_booking_db.port
}

output "database_name" {
  value = aws_db_instance.bus_booking_db.db_name
}

output "rds_security_group_id" {
  value = aws_security_group.rds_sg.id
}
