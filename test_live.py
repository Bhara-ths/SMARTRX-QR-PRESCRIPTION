import requests
import re

session = requests.Session()
resp = session.get('http://127.0.0.1:5000/login')
match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', resp.text)
if not match:
    print('CSRF Token not found in login page!')
    print(resp.text[:500])
    exit(1)
csrf_token = match.group(1)

login_data = {
    'csrf_token': csrf_token,
    'email': 'gunav4946@gmail.com',
    'password': 'Password123!',
    'role': 'doctor'
}
resp2 = session.post('http://127.0.0.1:5000/login', data=login_data, allow_redirects=True)
print('LOGIN POST STATUS:', resp2.status_code)
if resp2.status_code == 500:
    print('LOGIN 500 ERROR:')
    print(resp2.text)

resp3 = session.get('http://127.0.0.1:5000/doctor/dashboard')
print('DASHBOARD GET STATUS:', resp3.status_code)
if resp3.status_code == 500:
    print('DASHBOARD 500 ERROR:')
    print(resp3.text)
else:
    print('DASHBOARD GET OK')
