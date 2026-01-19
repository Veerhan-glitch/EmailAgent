# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd EmailAgent
pip install -r requirements.txt
```

### Step 2: Set Up Gmail API

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** (or select existing)
3. **Enable Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app"
   - Download the JSON file
5. **Save as `credentials.json`** in the EmailAgent folder

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
notepad .env  # or use your favorite editor
```

**Minimum required:**
```env
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
OPENAI_API_KEY=your_openai_key_here
```

### Step 4: Run Demo

```bash
python demo.py
```

This will:
- ✅ Check your Gmail API permissions
- ✅ Authenticate (opens browser first time)
- ✅ Show demo options
- ✅ Process sample emails

### Step 5: Run Full Agent

```bash
python email_agent.py
```

Or use in your code:

```python
from email_agent import EmailAgent

agent = EmailAgent()

result = agent.run(
    user_command="Handle my inbox from today. Show urgent items.",
    user_scope={'time_range_days': 1}
)

print(result['queue']['summary'])
```

## 🔑 Getting API Keys

### OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Go to API keys section
4. Create new secret key
5. Copy to `.env` file

### Alternative: Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API keys
4. Create new key
5. Copy to `.env` file

## 🧪 Test Your Setup

Run the permission check:

```bash
python -c "from demo import demo_check_permissions; demo_check_permissions()"
```

You should see:
```
✅ All required permissions granted!
Operating Mode: full
```

## 📝 Common Issues

### Issue: "credentials.json not found"
**Solution**: Download OAuth credentials from Google Cloud Console

### Issue: "Missing OPENAI_API_KEY"
**Solution**: Add API key to `.env` file or use Anthropic instead

### Issue: "Token expired"
**Solution**: Delete `tokens/token.json` and re-authenticate

### Issue: "Permission denied"
**Solution**: Re-run OAuth flow and grant all requested permissions

## 🎯 Next Steps

1. **Customize VIP list**: Edit `config.py` or use `agent.classifier.add_vip()`
2. **Set domain restrictions**: Update `ALLOWED_DOMAINS` in `.env`
3. **Enable DND mode**: Use `agent.dnd_handler.set_dnd_mode(True)`
4. **Review output**: Check `logs/` directory for detailed processing logs

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

## 💡 Example Commands

```python
# Process urgent emails only
agent.run("Show urgent emails", {'time_range_days': 1})

# VIP emails from this week
agent.run("VIP emails this week", {'time_range_days': 7})

# Unread emails with drafts
agent.run("Draft replies for unread", {'query': 'is:unread'})

# DND mode
agent.dnd_handler.set_dnd_mode(True)
agent.run("Process inbox while away", {'time_range_days': 1})
```

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Gmail API enabled in Google Cloud Console
- [ ] `credentials.json` downloaded and in project folder
- [ ] `.env` file created with API keys
- [ ] Demo script runs without errors
- [ ] Successfully authenticated with Gmail

## 🆘 Need Help?

1. Check logs in `logs/` directory
2. Run demo with verbose output: `python demo.py`
3. Review [README.md](README.md) for detailed info
4. Check configuration with `python -c "from config import Config; print(Config.validate())"`

---

**You're all set! 🎉**

Start processing emails with:
```bash
python email_agent.py
```
