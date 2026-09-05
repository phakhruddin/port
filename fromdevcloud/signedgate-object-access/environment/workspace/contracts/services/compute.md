# ALB and ECS

Create one internet-facing Application Load Balancer in exactly the public
subnets and one HTTP listener on port 80. Its default action forwards to an IP
target group on port 8080 with health path `/health/ready`.

Create one ECS cluster, one Fargate task definition and one ECS service. The
task definition uses `awsvpc`, contains exactly one supplied API container and
exposes TCP 8080. Run at least two API tasks in exactly the private subnets,
attach only the API security group, and set `assign_public_ip = false`.

A completed deployment has at least two running tasks and two healthy targets.
