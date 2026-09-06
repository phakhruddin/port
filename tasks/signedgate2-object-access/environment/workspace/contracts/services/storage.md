# S3 and DynamoDB

Create one S3 object bucket. Enable versioning, block every form of public
access, and enable default SSE-KMS encryption with the object KMS key. The
bucket policy must deny insecure transport and must not grant public access.

Create one DynamoDB metadata table with string partition key `file_id`. Use
on-demand billing and enable server-side encryption with the metadata KMS key.

The bucket must be removable after versioned objects and delete markers exist.
Do not place object contents in DynamoDB.
