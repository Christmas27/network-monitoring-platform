#!/bin/bash
# deploy.sh — Network Monitoring Spot Deploy (from scratch)
# Usage: ./deploy.sh
# Requirements: aws cli configured, nm-spot-key.pem in same dir

set -e

KEY_FILE="./nm-spot-key.pem"
REPO_URL="https://github.com/Christmas27/network-monitoring-platform.git"
APP_PORT=8000
REGION="ap-southeast-1"
KEY_NAME="nm-spot-key"
SG_NAME="network-monitoring-sg"

# ---------- 1. Resolve latest Ubuntu 24.04 AMI ----------
echo "Resolving latest Ubuntu 24.04 AMI..."
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters 'Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*' \
            'Name=state,Values=available' \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text --region "$REGION")

echo "Using AMI: $AMI_ID"

# ---------- 2. Create or reuse Security Group ----------
echo "Checking security group..."
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SG_NAME" \
  --query 'SecurityGroups[0].GroupId' \
  --output text --region "$REGION" 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
  echo "Creating new security group: $SG_NAME"
  SG_ID=$(aws ec2 create-security-group \
    --group-name "$SG_NAME" \
    --description "Network Monitoring Platform SG" \
    --query 'GroupId' \
    --output text --region "$REGION")

  # Allow SSH
  aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port 22 --cidr 0.0.0.0/0 \
    --region "$REGION"

  # Allow app port
  aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp --port "$APP_PORT" --cidr 0.0.0.0/0 \
    --region "$REGION"

  echo "Created SG: $SG_ID"
else
  echo "Reusing existing SG: $SG_ID"
fi

# ---------- 3. Launch spot instance ----------
echo "Launching spot instance..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3a.small \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":16,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=network-monitoring-spot}]' \
  --query 'Instances[0].InstanceId' --output text --region "$REGION")

echo "Launched: $INSTANCE_ID — waiting for running state..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# ---------- 4. Get public IP ----------
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text --region "$REGION")

echo "Public IP: $PUBLIC_IP"

# ---------- 5. Bootstrap the instance ----------
echo "Waiting for SSH to be ready..."
sleep 25

ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ubuntu@"$PUBLIC_IP" << 'REMOTE'
  set -e
  sudo apt-get update -qq
  sudo apt-get install -y docker.io docker-compose python3-pip python3-venv git ansible -qq

  sudo systemctl enable docker
  sudo usermod -aG docker ubuntu

  git clone https://github.com/Christmas27/network-monitoring-platform.git ~/app
  cd ~/app

  python3 -m venv .venv
  source .venv/bin/activate
  pip install -q -r requirements.txt

  # Start network lab
  sudo docker-compose up -d --build

  # Fix zebra daemons (known FRR container issue)
  sleep 10
  sudo docker exec frr-router1 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf || true
  sudo docker exec frr-router2 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf || true

  # Start app in background
  nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/app.log 2>&1 &

  echo "Done!"
REMOTE

echo ""
echo "================================================"
echo "App deployed at: http://$PUBLIC_IP:$APP_PORT"
echo "SSH:  ssh -i $KEY_FILE ubuntu@$PUBLIC_IP"
echo "Logs: ssh -i $KEY_FILE ubuntu@$PUBLIC_IP 'tail -f ~/app.log'"
echo "================================================"

chmod +x deploy.sh
./deploy.sh