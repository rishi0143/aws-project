
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
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.34"
}

variable "github_repo" {
  description = "GitHub repository"
  type        = string
  default     = "rishi0143/aws-project"
}

variable "github_branch" {
  description = "GitHub branch"
  type        = string
  default     = "main"
}

# RDS Configuration

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

variable "db_name" {
  description = "RDS database name"
  type        = string
  default     = "busbooking"
}
