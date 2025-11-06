from sendgrid import SendGridAPIClient # type: ignore
from sendgrid.helpers.mail import Mail # type: ignore
from app.config import settings
from fastapi import HTTPException, status # type: ignore
import logging
import os
import certifi

# Setup logger
logger = logging.getLogger(__name__)

# Fix SSL certificate verification issues on Windows
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()


class EmailService:
    @staticmethod
    def send_password_reset_email(to_email: str, username: str, reset_token: str):
        """Send password reset email using SendGrid"""
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        # For local testing - print the reset link
        print("\n" + "="*80)
        print("🔑 PASSWORD RESET TOKEN")
        print("="*80)
        print(f"User: {username} ({to_email})")
        print(f"Reset Link: {reset_link}")
        print(f"Token: {reset_token}")
        print("="*80 + "\n")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hello {username},</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <center>
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4CAF50;">{reset_link}</p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Chatbot App. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject="Reset Your Password - Chatbot App",
            html_content=html_content
        )
        
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            logger.info(f"Password reset email sent successfully to {to_email}")
            print(f"✅ Password reset email sent successfully to {to_email}")
            return response
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            # For local development, don't fail if email doesn't send
            # Just log the error and continue (token is printed above for testing)
            print(f"⚠️ Email sending failed: {str(e)}")
            print(f"💡 For local testing, use the token printed above from console")
            # Don't raise exception - allow password reset to work without email in dev
            return None
    
    @staticmethod
    def send_welcome_email(to_email: str, username: str):
        """Send welcome email to new user"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Chatbot App! 🎉</h1>
                </div>
                <div class="content">
                    <h2>Hello {username},</h2>
                    <p>Thank you for registering with Chatbot App!</p>
                    <p>You can now start chatting with our AI assistant in both English and Roman Urdu. You can also upload images for analysis.</p>
                    <p><strong>Features you can enjoy:</strong></p>
                    <ul>
                        <li>Chat in English and Roman Urdu</li>
                        <li>Upload and analyze images</li>
                        <li>View your chat history</li>
                        <li>Get intelligent responses powered by Google Gemini</li>
                    </ul>
                    <p>Start chatting now and explore the possibilities!</p>
                </div>
                <div class="footer">
                    <p>© 2025 Chatbot App. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=to_email,
            subject="Welcome to Chatbot App!",
            html_content=html_content
        )
        
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
            logger.info(f"Welcome email sent successfully to {to_email}")
            print(f"✅ Welcome email sent successfully to {to_email}")
        except Exception as e:
            # Don't raise exception for welcome email failures
            logger.warning(f"Error sending welcome email: {str(e)}")
            print(f"⚠️ Welcome email failed (user registered successfully anyway)")

