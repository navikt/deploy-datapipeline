#!/usr/bin/env bash

set -e # Fail if one command fails

jq=$(command -v jq)
[[ -z "$jq" ]] && echo "You must have 'jq' installed to use this script." && exit 1

TERRAFORM_PROJECT_ID=nais-analyse-prod-2dcc
TERRAFORM_BUCKET_NAME=nais-analyse-tfstate
TERRAFORM_USERNAME=nais-analyse-user
RED='\033[0;31m'
NC='\033[0m' # No Color

gcloud config set project "$TERRAFORM_PROJECT_ID"
echo -e "Project set to \"$TERRAFORM_PROJECT_ID\"\n"

# Create terraform service account if it doesn't already exist
if $(gcloud iam service-accounts list --project="$TERRAFORM_PROJECT_ID" --format="json" --filter "email:$TERRAFORM_USERNAME@${TERRAFORM_PROJECT_ID}.iam.gserviceaccount.com" | $jq 'length == 0'); then
    gcloud iam service-accounts create "$TERRAFORM_USERNAME" --display-name="Terraform CI user" --project="$TERRAFORM_PROJECT_ID"
else
  echo -e "Service account already exists\n"
fi

# Adding roles to terraform service-account (to give access to whole bucket)
gcloud projects add-iam-policy-binding "${TERRAFORM_PROJECT_ID}" --member "serviceAccount:$TERRAFORM_USERNAME@${TERRAFORM_PROJECT_ID}.iam.gserviceaccount.com" --role roles/storage.admin
# Generating key file for service account
if $(gcloud iam service-accounts keys list --iam-account "$TERRAFORM_USERNAME"@"$TERRAFORM_PROJECT_ID".iam.gserviceaccount.com  --format="json" --managed-by=user | $jq 'length == 0'); then
  echo -e "\nGenerating key"
  gcloud iam service-accounts keys create service_account_key_to_be_copied_to_github_secret.json --iam-account "$TERRAFORM_USERNAME"@"$TERRAFORM_PROJECT_ID".iam.gserviceaccount.com
  echo "${RED}IMPORTANT: Remember to update the secret GCP_KEY at https://github.com/navikt/deploy-datapipeline/settings/secrets/GCP_KEY to give Terraform access to the GCP bucket!"
  echo "Copy the whole content of the file service_account_key_to_be_copied_to_github_secret.json into the secret.${NC}"
else
  echo -e "\n${RED}It already exists one or more user-managed keys. These must be deleted before creating a new key.${NC}"
  echo "This is to make sure the existing key stored in a Github secret is not unintentionally invalidated."
  echo "When a new key is created the Github secret has to be manually updated to ensure Terraform has access to the GCP bucket."
  gcloud iam service-accounts keys list --iam-account "$TERRAFORM_USERNAME"@"$TERRAFORM_PROJECT_ID".iam.gserviceaccount.com  --managed-by=user
  echo -e "\nTo delete existing keys, run this command manually with the correct key_id"
  echo "gcloud iam service-accounts keys delete <insert key_id to be deleted> --iam-account "$TERRAFORM_USERNAME"@"$TERRAFORM_PROJECT_ID".iam.gserviceaccount.com"
fi

# Create bucket for Terraform state if it doesn't already exist
echo -e "\nCheck if bucket already exist"
if ! gsutil ls -p "$TERRAFORM_PROJECT_ID" -b "gs://${TERRAFORM_BUCKET_NAME}"; then
  # region europe-north1 with uniform Bucket-Level Access turned on
  gsutil mb -c regional -l europe-north1 -b on -p "$TERRAFORM_PROJECT_ID" "gs://${TERRAFORM_BUCKET_NAME}"
  echo -e "Bucket created\n"
else
  echo -e "Bucket already exist\n"
fi

# Enable Object Versioning on bucket
gsutil versioning set on "gs://${TERRAFORM_BUCKET_NAME}"
# Apply lifecycle config to delete noncurrent versions of objects older than 90 days and having 5+ newer versions
gsutil lifecycle set gcp_lifecycle_rules.json "gs://${TERRAFORM_BUCKET_NAME}"
echo -e "Bucket versioning turned on and lifecycle config applied"
