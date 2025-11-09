from app import app


def run():
    client = app.test_client()

    # Test home page
    r = client.get('/')
    print('GET / ->', r.status_code)

    # Test chat endpoint
    r2 = client.post('/get', data={'msg': 'I am feeling anxious and overwhelmed'})
    print('\nPOST /get (mental health) ->', r2.status_code)
    try:
        print('Response JSON:', r2.get_json())
    except Exception:
        print('Response text (non-json):', r2.data[:200])

    # Test out-of-scope message
    r3 = client.post('/get', data={'msg': 'Tell me a joke about cats'})
    print('\nPOST /get (out-of-scope) ->', r3.status_code)
    try:
        print('Response JSON:', r3.get_json())
    except Exception:
        print('Response text (non-json):', r3.data[:200])

    # Test history endpoint
    r3 = client.get('/history')
    print('GET /history ->', r3.status_code, r3.get_json())


if __name__ == '__main__':
    run()
