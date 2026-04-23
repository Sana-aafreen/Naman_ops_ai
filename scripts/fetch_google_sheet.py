import requests

url = 'https://docs.google.com/spreadsheets/d/1Jy6EodrePHe-KRmlIECcx4h76YaNSuaG8pbaI4COeZk/export?format=csv&gid=0'
print('URL:', url)
resp = requests.get(url, allow_redirects=True, timeout=15)
print('Status:', resp.status_code)
print('Final URL:', resp.url)
print('Content-Type:', resp.headers.get('content-type'))
print('Length:', len(resp.content))
print('Text preview:')
print(resp.text[:1500])
