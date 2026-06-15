# AWS Elastic Beanstalk Deployment

This project is ready for a simple public AWS deployment using Elastic Beanstalk's Docker platform.

## What This Deploys

The root `Dockerfile` runs the Streamlit web app on port `8080`.

The Streamlit app uses built-in local analysis mode by default, so it does not require a separate FastAPI service for the demo deployment.

## Prerequisites

- An AWS account
- An AWS region selected, for example `ap-south-1` or `us-east-1`
- The GitHub repository connected or this project downloaded as a ZIP

## Console Deployment Steps

1. Open AWS Elastic Beanstalk.
2. Choose **Create application**.
3. Application name: `insurance-document-risk-analyzer`.
4. Platform: **Docker**.
5. Application code: upload a ZIP of this repository or connect your source bundle.
6. Service access: let AWS create the required service role if prompted.
7. Instance profile: let AWS create one if prompted.
8. Create the environment.

Elastic Beanstalk will build the root `Dockerfile` and expose the Streamlit app publicly.

## Environment Variables

For the default demo deployment, no secrets are required.

Recommended environment variables:

```text
STORAGE_BACKEND=local
MAX_UPLOAD_MB=20
```

Do not put API keys, AWS secrets, or passwords in GitHub. Add them only in AWS environment properties or AWS Secrets Manager.

## Optional Production Setup

For a more production-like deployment:

- Deploy the FastAPI backend separately with `Dockerfile.api`.
- Set `API_BASE_URL` in the Streamlit environment to the backend URL.
- Set `STORAGE_BACKEND=s3`.
- Set `S3_BUCKET` to your bucket name.
- Store LLM keys in AWS Secrets Manager or environment properties, not in source control.

