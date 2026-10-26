import io, pytest
from PIL import Image
from app import create_app, db
@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path/"t.db"}')
    monkeypatch.setenv('UPLOAD_FOLDER', str(tmp_path/'uploads'))
    monkeypatch.setenv('SECRET_KEY','test-secret-key-32-characters-long!!')
    monkeypatch.setenv('JWT_SECRET_KEY','test-jwt-secret-32-characters-long!')
    monkeypatch.setenv('ADMIN_USERNAME','admin'); monkeypatch.setenv('ADMIN_PASSWORD','adminpass123')
    a=create_app(); a.config.update(TESTING=True)
    yield a
    with a.app_context(): db.session.remove(); db.drop_all()
@pytest.fixture()
def client(app): return app.test_client()
def reg(client,u):
    r=client.post('/api/v1/auth/register', json={'username':u,'password':'secret123','display_name':u.title()}); assert r.status_code==201, r.data
    return {'Authorization':f"Bearer {r.json['access_token']}"}, r.json['user']['id']
@pytest.fixture()
def users(client):
    a,aid=reg(client,'alice'); b,bid=reg(client,'bob'); return (a,aid),(b,bid)
@pytest.fixture()
def png():
    s=io.BytesIO(); Image.new('RGB',(10,10),'red').save(s,format='PNG'); return s.getvalue()
