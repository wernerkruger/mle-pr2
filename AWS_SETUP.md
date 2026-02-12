# AWS CLI Install and Key Setup

This project uses **AWS SageMaker**, **S3**, **Lambda**, and **Step Functions**. You can run the notebook on **SageMaker Studio** (recommended) or configure the AWS CLI locally to sync data and use the same account.

---

## 1. Install AWS CLI

### Option A: Install via pip (Linux/macOS/Windows)

```bash
pip install awscli
# or
pip install awscliv2
```

### Option B: Official installer (Linux x86_64)

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

### Option C: Package manager

- **Ubuntu/Debian:** `sudo apt install awscli`
- **Fedora:** `sudo dnf install awscli`
- **macOS:** `brew install awscli`

---

## 2. Configure credentials (access keys)

You need an **Access Key ID** and **Secret Access Key** from the AWS console.

### Create access keys (if you don’t have them)

1. Sign in to [AWS Console](https://console.aws.amazon.com/) → **IAM** → **Users** → your user.
2. **Security credentials** tab → **Create access key**.
3. Choose **Command Line Interface (CLI)** → Next → Create.
4. Copy the **Access Key ID** and **Secret Access Key** (you won’t see the secret again).

### Configure the CLI

Run:

```bash
aws configure
```

Then enter:

- **AWS Access Key ID:** your Access Key ID  
- **AWS Secret Access Key:** your Secret Access Key  
- **Default region name:** e.g. `us-east-1` (same region you use for SageMaker).  
- **Default output format:** e.g. `json` (optional).

This writes to `~/.aws/credentials` and `~/.aws/config`.

### Verify

```bash
aws sts get-caller-identity
aws s3 ls
```

If these work, the CLI and keys are set up.

---

## 3. What you need for this project

- **SageMaker Studio** (or a SageMaker notebook instance) in one region (e.g. `us-east-1`).
- **IAM role** for the notebook/Studio with permissions for:  
  SageMaker, S3, Lambda, Step Functions, IAM (as needed for execution roles).
- **S3 bucket** in the same region (the notebook creates/uses the default bucket if you use `session.default_bucket()`).
- When creating **Lambdas**, attach the same (or equivalent) permissions as your SageMaker execution role so they can read S3 and invoke the SageMaker endpoint.

---

## 4. Running the notebook

- **Recommended:** Run the notebook inside **SageMaker Studio** (or a SageMaker notebook instance) with the **Python 3 (Data Science)** kernel and an **ml.t3.medium** instance. The notebook will use the Studio/instance role; you don’t need to set access keys there.
- If you run **locally**, set the same region and ensure your CLI credentials have the permissions above. Data staging (extract, transform) can run locally; training, deployment, and S3 sync require AWS and the correct role/keys.

---

## 5. Lambda deployment note

For the **classifier** Lambda that calls SageMaker, you must **package the SageMaker SDK** (and its dependencies) in the deployment package. See:  
[Creating deployment packages for Python Lambdas with dependencies](https://docs.aws.amazon.com/lambda/latest/dg/python-package-create.html#python-package-create-with-dependency).

In `lambda.py`, set `ENDPOINT` in `classifier_handler` to your deployed image classification endpoint name before deploying that Lambda.

---

## 6. ResourceLimitExceeded (e.g. ml.p3.2xlarge quota is 0)

If training fails with **ResourceLimitExceeded** for an instance type (e.g. `ml.p3.2xlarge for training job usage`):

- **Fast fix:** Use an instance type that has quota. This project is set to use **ml.g4dn.xlarge** (G4dn GPU), which often has default quota. The notebook uses that; no change needed unless you prefer P3.

- **Request a quota increase via CLI** (for P3 or other types):

  1. Find the Service Quotas service code and quota code for SageMaker (they are fixed values):

  ```bash
  # List SageMaker quotas to find the one for "ml.p3.2xlarge for training job usage"
  aws service-quotas list-service-quotas --service-code sagemaker --query "Quotas[?QuotaName=='ml.p3.2xlarge for training job usage']" --output table
  ```

  2. Request an increase (replace `REGION` and the quota code if different):

  ```bash
  # Get the quota code (QuotaCode) from the list above, then:
  aws service-quotas request-service-quota-increase \
    --service-code sagemaker \
    --quota-code "your-quota-code" \
    --desired-value 1 \
    --region REGION
  ```

  Or use the **Service Quotas** console: **AWS Console → Service Quotas → AWS Services → SageMaker** → find “ml.p3.2xlarge for training job usage” → **Request quota increase**. Approval can take a business day; using **ml.g4dn.xlarge** in the notebook avoids waiting.
