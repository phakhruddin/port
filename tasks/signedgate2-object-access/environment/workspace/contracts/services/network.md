# VPC, Routing and Security Groups

- Create one non-default VPC.
- Create two public and two private subnets across at least two availability
  zones.
- Attach one internet gateway.
- Associate each public subnet with a route table whose `0.0.0.0/0` route
  targets the internet gateway.
- Associate each private subnet with a distinct private route table. Private
  route tables must not have a route to the internet gateway.
- Create an S3 gateway VPC endpoint and associate it with exactly the private
  route tables.
- Restrict the endpoint policy to the managed bucket and its objects.

Create separate ALB and API security groups. The ALB group accepts TCP 80 from
`0.0.0.0/0`. The API group accepts TCP 8080 only from the ALB group. Do not
attach additional groups to the ALB or ECS service.

## Emulator note

The S3 gateway endpoint's route-table association may need to be recreated,
rather than modified in place, when repairing drift — the emulated platform
does not support in-place route-table updates on an existing endpoint. Design
your recovery path assuming a delete-and-recreate is the correct response to
a missing or altered association, not a Terraform bug to work around.
