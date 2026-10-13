from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app, parse_fields

client = TestClient(app)

def test_health():
    assert client.get('/health').json()['status'] == 'ok'

def test_parse():
    assert parse_fields('SKU: ABCD1234\nLOT: ZX902\nEXP: 2027-12') == ('ABCD1234','ZX902','2027-12')

def test_missing():
    assert parse_fields('nothing here') == (None,None,None)

def test_reject_text():
    response=client.post('/inspect',files={'file':('x.txt',b'hello','text/plain')})
    assert response.status_code == 415

def test_reject_invalid_image():
    response=client.post('/inspect',files={'file':('x.png',b'broken','image/png')})
    assert response.status_code == 400

def test_inspect_image(monkeypatch):
    monkeypatch.setattr('app.main.pytesseract.image_to_string',lambda *_args,**_kw: 'SKU: ABCD1234\nLOT: ZX902\nEXP: 2027-12')
    b=BytesIO();Image.new('RGB',(100,100),'white').save(b,format='PNG')
    r=client.post('/inspect',files={'file':('test.png',b.getvalue(),'image/png')})
    assert r.status_code==200
    assert r.json()['passed'] is True
    assert r.json()['batch']=='ZX902'
