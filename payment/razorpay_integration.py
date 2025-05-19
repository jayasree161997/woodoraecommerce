# import razorpay
# from django.conf import settings



# client = razorpay.Client(auth=("rzp_test_4MBYamMKeUifHI", "jCW28TZMPhifXUXSBo4CVB8I"))



# def initiate_payment(amount, currency='INR'):
#     data = {
#         'amount': 100* 100000,  # Razorpay expects amount in paise (e.g., 100 INR = 10000 paise)
#         'currency': currency,
#         'payment_capture': '1'  # Auto capture the payment after successful authorization
#     }
#     response = client.order.create(data=data)
#     return response['id']