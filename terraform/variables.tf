
# AWS Configuration

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

# EKS Configuration

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "my-eks-cluster5"
}

variable "cluster_version" {
  type    = string
  default = "1.34"
}

variable "github_repo" {
  description = "GitHub repository"
  type        = string
  default     = "rishi0143/aws-project"
}

variable "github_branch" {
  type    = string
  default = "main"
}

# RDS Configuration

variable "vpc_id" {
  description = "Existing AWS VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "RDS private subnet IDs in different AZs"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least two subnet IDs are required."
  }
}

variable "db_username" {
  description = "RDS MySQL username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS MySQL password"
  type        = string
  sensitive   = true
}
