Network Monitoring - Manual Deploy Commands (Learning Mode)

Goal:
- Run deployment one command at a time.
- See output at each step and understand what each command does.

Notes:
- Run from CloudShell or any terminal with AWS CLI access.
- Replace values only where marked.
- If a step fails, stop and fix before continuing.

==================================================
1) Set region and basic variables
==================================================

REGION="ap-southeast-1"
KEY_NAME="nm-spot-key"
KEY_FILE="$HOME/nm-spot-key.pem"
APP_PORT="8000"
INSTANCE_NAME="network-monitoring-spot"
SG_NAME="network-monitoring-sg"
REPO_URL="https://github.com/Christmas27/network-monitoring-platform.git"

echo "REGION=$REGION"

Expected:
- Prints REGION=ap-southeast-1


==================================================
2) Validate AWS identity and region
==================================================

aws sts get-caller-identity
aws configure get region

Expected:
- JSON with your Account/UserArn.
- Region output should match REGION above (or blank if not configured globally).


==================================================
3) Resolve Ubuntu 24.04 AMI (reliable method)
==================================================

AMI_ID=$(aws ssm get-parameter \
	--name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
	--query 'Parameter.Value' \
	--output text \
	--region "$REGION")

echo "Using AMI: $AMI_ID"

Expected:
- AMI like ami-xxxxxxxxxxxxxxxxx (not None).


==================================================
4) Ensure key file permissions are correct
==================================================

chmod 400 "$KEY_FILE"
ls -l "$KEY_FILE"

Expected:
- Permission shows read-only for owner, for example: -r--------


==================================================
5) Create or reuse Security Group
==================================================

SG_ID=$(aws ec2 describe-security-groups \
	--filters "Name=group-name,Values=$SG_NAME" \
	--query 'SecurityGroups[0].GroupId' \
	--output text \
	--region "$REGION")

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
	SG_ID=$(aws ec2 create-security-group \
		--group-name "$SG_NAME" \
		--description "Network Monitoring SG" \
		--query 'GroupId' \
		--output text \
		--region "$REGION")
fi

echo "Using SG: $SG_ID"

Expected:
- SG like sg-xxxxxxxxxxxxxxxxx.


==================================================
6) Ensure SG inbound rules (SSH + app)
==================================================

aws ec2 authorize-security-group-ingress \
	--group-id "$SG_ID" \
	--protocol tcp --port 22 --cidr 0.0.0.0/0 \
	--region "$REGION" || true

aws ec2 authorize-security-group-ingress \
	--group-id "$SG_ID" \
	--protocol tcp --port "$APP_PORT" --cidr 0.0.0.0/0 \
	--region "$REGION" || true

echo "Ingress rules ensured for ports 22 and $APP_PORT"

Expected:
- If already exists, AWS may return InvalidPermission.Duplicate; safe because of || true.


==================================================
7) Launch Spot instance (one-time + terminate)
==================================================

INSTANCE_ID=$(aws ec2 run-instances \
	--image-id "$AMI_ID" \
	--instance-type t3a.small \
	--key-name "$KEY_NAME" \
	--security-group-ids "$SG_ID" \
	--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time,InstanceInterruptionBehavior=terminate}' \
	--block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":16,"VolumeType":"gp3"}}]' \
	--tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
	--query 'Instances[0].InstanceId' \
	--output text \
	--region "$REGION")

echo "Launched instance: $INSTANCE_ID"

Expected:
- Instance ID like i-xxxxxxxxxxxxxxxxx.


==================================================
8) Wait until instance is running
==================================================

aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
echo "Instance is running"

Expected:
- No output during wait, then "Instance is running".


==================================================
9) Get public IP
==================================================

PUBLIC_IP=$(aws ec2 describe-instances \
	--instance-ids "$INSTANCE_ID" \
	--query 'Reservations[0].Instances[0].PublicIpAddress' \
	--output text \
	--region "$REGION")

echo "Public IP: $PUBLIC_IP"

Expected:
- Public IPv4 value.


==================================================
10) Wait for SSH readiness
==================================================

sleep 20
ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ubuntu@"$PUBLIC_IP" "echo SSH OK"

Expected:
- Prints SSH OK.


==================================================
11) Bootstrap software + clone project
==================================================

ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ubuntu@"$PUBLIC_IP" '
set -e
sudo apt-get update -qq
sudo apt-get install -y docker.io docker-compose python3-pip python3-venv git ansible -qq
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
if [ ! -d ~/app ]; then git clone "'"$REPO_URL"'" ~/app; fi
'

Expected:
- Package install output, no fatal errors.


==================================================
12) Create venv, install Python deps, run services
==================================================

ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ubuntu@"$PUBLIC_IP" '
set -e
cd ~/app
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
sudo docker-compose up -d --build
sleep 10
sudo docker exec frr-router1 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf || true
sudo docker exec frr-router2 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf || true
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/app.log 2>&1 &
'

Expected:
- Containers up, uvicorn running in background.


==================================================
13) Verify app is reachable
==================================================

echo "Open: http://$PUBLIC_IP:$APP_PORT"
curl -I "http://$PUBLIC_IP:$APP_PORT" || true

Expected:
- Browser should show dashboard.
- curl may return 200 or 307 depending on route behavior.


==================================================
14) Useful follow-up commands
==================================================

# SSH in
echo ssh -i "$KEY_FILE" ubuntu@"$PUBLIC_IP"

# Tail app logs
echo ssh -i "$KEY_FILE" ubuntu@"$PUBLIC_IP" "tail -f ~/app.log"

# Stop this instance later (save cost)
echo aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$REGION"


Common mistakes and quick fixes:
- AMI prints None:
	REGION likely wrong/unset. Run: echo "$REGION" and retry Step 3.
- Invalid endpoint ec2..amazonaws.com:
	REGION is empty. Set REGION first.
- Permission denied (publickey):
	Wrong key file, wrong key name, or wrong chmod. Recheck Steps 1 and 4.
- Can SSH but app not loading:
	Check logs: ssh -i "$KEY_FILE" ubuntu@"$PUBLIC_IP" "tail -n 100 ~/app.log"


==================================================
Failsafe: CloudShell session reset (lost variables)
==================================================

If CloudShell timed out, files are usually still there, but shell variables are gone.
Do this to recover without full redeploy.

1) Re-set minimum variables

REGION="ap-southeast-1"
KEY_FILE="$HOME/nm-spot-key.pem"
INSTANCE_NAME="network-monitoring-spot"
chmod 400 "$KEY_FILE"


2) Re-find running instance by Name tag

INSTANCE_ID=$(aws ec2 describe-instances \
	--filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running,pending,stopped,stopping" \
	--query 'Reservations[].Instances[].InstanceId' \
	--output text \
	--region "$REGION")

echo "Recovered INSTANCE_ID: $INSTANCE_ID"

Expected:
- One instance id like i-xxxxxxxxxxxxxxxxx.
- If blank, no matching instance exists. Start from Step 7 (launch).


3) Get state and public IP

STATE=$(aws ec2 describe-instances \
	--instance-ids "$INSTANCE_ID" \
	--query 'Reservations[0].Instances[0].State.Name' \
	--output text \
	--region "$REGION")

PUBLIC_IP=$(aws ec2 describe-instances \
	--instance-ids "$INSTANCE_ID" \
	--query 'Reservations[0].Instances[0].PublicIpAddress' \
	--output text \
	--region "$REGION")

echo "State: $STATE"
echo "Public IP: $PUBLIC_IP"


4) If state is stopped, start it and wait

if [ "$STATE" = "stopped" ]; then
	aws ec2 start-instances --instance-ids "$INSTANCE_ID" --region "$REGION" >/dev/null
	aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
	PUBLIC_IP=$(aws ec2 describe-instances \
		--instance-ids "$INSTANCE_ID" \
		--query 'Reservations[0].Instances[0].PublicIpAddress' \
		--output text \
		--region "$REGION")
	echo "New Public IP: $PUBLIC_IP"
fi


5) SSH and continue from update/restart steps

ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ubuntu@"$PUBLIC_IP"

Then on EC2:

cd ~/app
git pull
pkill -f "uvicorn app.main:app" || true
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > ~/app.log 2>&1 &
tail -n 40 ~/app.log


Tip:
- Do not rely on old PUBLIC_IP after stop/start. Always re-query it.
- If instance was terminated (spot reclaimed), launch a new one from Step 7.

http://13.212.150.108:8000