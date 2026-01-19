# Quick Start - AI Email GUI

## 🚀 Launch in 3 Steps

### Step 1: Open Terminal
```powershell
cd C:\Users\prate\Desktop\EmailAgent\EmailAgent
```

### Step 2: Run the GUI
```powershell
C:/Users/prate/Desktop/EmailAgent/.venv/Scripts/python.exe -m streamlit run gui_app.py
```

### Step 3: Open Browser
- Go to: **http://localhost:8502**
- Or click the link in terminal output

## ⚡ Quick Actions

### Process Emails
1. On Dashboard page
2. Command box has default: "Process my inbox from last 7 days and create drafts"
3. Click **"🚀 Process with AI"**
4. Watch AI analyze emails
5. See metrics populate

### View Priority Emails
1. Click **"📥 Priority Inbox"** in sidebar
2. See all emails sorted by AI priority (highest first)
3. Use filters to narrow down
4. Expand emails to see AI drafts

### Review AI Drafts
1. In Priority Inbox
2. Find emails with **"✍️ AI-Generated Draft Reply"**
3. Expand to see draft
4. Options: **Send / Edit / Discard**

### Check Analytics
1. Click **"📈 Analytics"** in sidebar
2. See charts and graphs
3. Analyze email patterns

## 🎨 Features at a Glance

### Dashboard Page
- **Metric Cards**: Total emails, drafts, priorities, time saved
- **Category Pie Chart**: Visual distribution
- **Priority Bar Chart**: High/Medium/Low breakdown
- **AI Insights**: Quick summary

### Priority Inbox Page
- **Filters**: Priority / Category / Actionable / Has Drafts
- **Email Cards**: Rich display with AI reasoning
- **Evidence Tags**: Why AI made decisions
- **Hidden Urgency Warnings**: Time-sensitive alerts
- **Draft Replies**: AI-generated responses
- **Reply-All Risk**: External recipient warnings

### Compose Page
- **AI Writing Assistant**: Real-time analysis
- **Tone Selector**: Professional / Friendly / Formal / Casual
- **Length Options**: Short / Medium / Long
- **Quick Templates**: Meeting / Introduction / Follow-up

### Analytics Page
- **Volume Over Time**: Daily email trends
- **Top Senders**: Who emails you most
- **Priority Distribution**: How emails are prioritized
- **Category Breakdown**: Email type analysis

## 💡 Pro Tips

1. **Default Command Works**: The pre-filled command creates drafts automatically
2. **Sort by Priority**: Emails are sorted highest priority first
3. **Use Filters**: Narrow down to specific emails quickly
4. **Check Evidence**: See why AI made each decision
5. **Watch for Hidden Urgency**: AI detects subtle deadline hints
6. **Review Reply-All Risks**: Prevent embarrassing email mistakes

## 🎯 Common Commands

```
Process my inbox from last 7 days and create drafts
Show urgent emails from last 30 days
Get high priority emails and generate replies
Process inbox and create drafts for actionable emails
Show emails requiring action
```

## 🛠️ Troubleshooting

### GUI Won't Start?
```powershell
# Check if streamlit is installed
C:/Users/prate/Desktop/EmailAgent/.venv/Scripts/python.exe -m pip list | Select-String streamlit

# Reinstall if needed
C:/Users/prate/Desktop/EmailAgent/.venv/Scripts/python.exe -m pip install streamlit plotly pandas
```

### No Emails Showing?
1. Make sure you processed emails first (Dashboard → Process with AI)
2. Check filters aren't too restrictive
3. Ensure Gmail authentication is working

### Drafts Not Created?
1. Include "create drafts" or "generate drafts" in command
2. Or use the default command provided
3. Check Priority Inbox → filter "Has Drafts"

## 📱 Navigation

- **Dashboard**: Main hub, process emails here
- **Priority Inbox**: Review and manage emails
- **Compose & Draft**: Write new emails
- **Analytics**: See insights and trends
- **Search**: (Work in progress)

## 🎉 Enjoy!

Your AI Email Intelligence Agent is ready to save you hours of email management time! 🚀
