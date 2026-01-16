"""
Quick test to verify email sending functionality
"""
import logging
from email_agent import EmailAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_send():
    """Test draft creation and sending"""
    agent = EmailAgent()
    
    print("\n" + "="*60)
    print("Testing Email Draft Creation and Sending")
    print("="*60 + "\n")
    
    # Step 1: Create a test draft
    print("Step 1: Creating a test draft...")
    draft = agent.compose_email(
        recipients=["ptyadav5@gmail.com"],  # Send to yourself for testing
        subject="Test Email from EmailAgent",
        body_intent="This is a test email to verify the send functionality is working properly."
    )
    
    if not draft:
        print("❌ Failed to create draft")
        return False
    
    print(f"✅ Draft created successfully!")
    print(f"   Draft ID: {draft.draft_id}")
    print(f"   Subject: {draft.subject}")
    print(f"   To: {draft.recipients}")
    print(f"   Body preview: {draft.body[:100]}...")
    
    # Step 2: Confirm sending
    print("\n" + "-"*60)
    confirm = input("\n🚀 Do you want to SEND this draft? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Send cancelled by user")
        return False
    
    # Step 3: Send the draft
    print("\nStep 2: Sending the draft...")
    success = agent.send_draft(draft.draft_id)
    
    if success:
        print("✅ Email sent successfully!")
        print("   Check your inbox at ptyadav5@gmail.com")
        return True
    else:
        print("❌ Failed to send email")
        print("   Check the logs above for error details")
        return False

if __name__ == "__main__":
    test_send()
