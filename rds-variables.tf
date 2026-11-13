
variable "vpc_id" {
  description = "Existing project VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "At least two private subnet IDs in different AZs"
  type        = list(string)
}

variable "eks_node_security_group_id" {
  description = "EKS worker node security group ID"
  type        = string
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}
