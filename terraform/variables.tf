
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

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
  description = "GitHub repository allowed to assume the deployment role"
  type        = string
  default     = "rishi0143/aws-project"
}

variable "github_branch" {
  type    = string
  default = "main"
}

