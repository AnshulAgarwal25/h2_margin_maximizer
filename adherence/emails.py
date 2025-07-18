# import os
# import requests
# from dotenv import load_dotenv
# from params import email_list
#
#
# def send_email_mailgun(subject, body, to_emails):
#     load_dotenv()
#
#     MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
#     MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
#
#     response = requests.post(
#         f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
#         auth=("api", MAILGUN_API_KEY),
#         data={
#             "from": f"H2 Margin Maximizer <mailgun@{MAILGUN_DOMAIN}>",
#             "to": to_emails,
#             "subject": subject,
#             "text": body
#         }
#     )
#     return response.status_code, response.text
#
#
# def load_message(data, total_df, total_value_df):
#     to_emails = email_list
#     subject = "H2 Margin Maximizer | Optimizer Run Results"
#     body = (f"Hi, \nPlease find below the H2 Margin Maximizer Optimizer results: "
#             f"\n {data} \n {total_df} \n {total_value_df} \nThank you!")
#     send_email_mailgun(subject, body, to_emails)
