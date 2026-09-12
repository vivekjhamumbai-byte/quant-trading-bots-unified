# AWS DEPLOYMENT GUIDE

## QUICK START

### Create EC2 Instance
- Region: ap-south-1 (Mumbai)
- Instance: t2.micro (Free tier)
- OS: Ubuntu 22.04 LTS

### Run Deployment
ssh -i key.pem ubuntu@your-ip
./aws_deployment.sh
nano .env  # Add credentials
sudo systemctl start trading-bots.service

### Access Dashboard
http://your-ec2-ip:8765

Enter 6-digit TOTP code from authenticator app

---

## DASHBOARD (Phone-Accessible)

- Real-time bot status
- Live P&L tracking
- Trade history
- Emergency STOP button
- Auto-refresh every 3 seconds

---

## MARKET HOURS

Start: 09:00 IST (automatic)
Stop: 15:30 IST (automatic)

---

## MONITORING

Dashboard: http://your-ip:8765
Logs: sudo journalctl -u trading-bots.service -f
Status: systemctl status trading-bots.service

---

## COST

Free Tier: 12 months free
Then: approx Rs500-800/month

---

## EMERGENCY STOP

Method 1: Dashboard click STOP ALL
Method 2: SSH kill command
Method 3: Terminate instance

---

See full guide: AWS_DEPLOYMENT_GUIDE_FULL.md
