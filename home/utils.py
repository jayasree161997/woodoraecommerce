import random
from django.core.mail import send_mail

def send_otp_to_email(email):
    otp = str(random.randint(100000, 999999))
    send_mail(
        'Your OTP for Password Reset',
        f'Your OTP is {otp}. It will expire in 1 minute.',
        'noreply@example.com',
        [email],
        fail_silently=False,
    )
    return otp