import io
def test_register_login_username_only(client, users):
    (a,aid),(b,bid)=users
    assert client.post('/api/v1/auth/register', json={'username':'alice','password':'x123456'}).status_code==409
    assert client.post('/api/v1/auth/login', json={'username':'alice','password':'wrong'}).status_code==401
    assert client.post('/api/v1/auth/login', json={'username':'alice','password':'secret123'}).status_code==200
    # no phone/email/profile fields exposed
    me=client.get('/api/v1/users/me', headers=a).json['user']
    assert 'mobile' not in str(me).lower() and 'email' not in me and 'bio' not in me and 'avatar' not in me
def test_chat_text_edit_two_sided_but_delete_self_only(client, users):
    (a,aid),(b,bid)=users
    c=client.post('/api/v1/chats', headers=a, json={'chat_type':'private','target_user_id':bid}).json['chat']
    m=client.post(f"/api/v1/messages/chat/{c['id']}", headers=a, json={'message_type':'text','content':'hello'}).json['message']
    assert client.get(f"/api/v1/messages/chat/{c['id']}", headers=b).json['messages'][0]['content']=='hello'
    e=client.put(f"/api/v1/messages/{m['id']}", headers=a, json={'content':'edited'})
    assert e.json['message']['is_edited'] is True
    # Editing IS two-sided: the other user sees the edited text
    assert client.get(f"/api/v1/messages/chat/{c['id']}", headers=b).json['messages'][0]['content']=='edited'
    # Delete-for-everyone is NOT in Lite (sender or not) -> 403
    assert client.delete(f"/api/v1/messages/{m['id']}", headers=a, json={'for_all':True}).status_code==403
    assert client.delete(f"/api/v1/messages/{m['id']}", headers=a, json={'delete_for_all':True}).status_code==403
    assert client.delete(f"/api/v1/messages/{m['id']}?for_all=true", headers=a).status_code==403
    # Delete-for-me works, and only hides it for the deleter
    assert client.delete(f"/api/v1/messages/{m['id']}", headers=a, json={}).status_code==200
    assert client.get(f"/api/v1/messages/chat/{c['id']}", headers=a).json['messages']==[]
    assert client.get(f"/api/v1/messages/chat/{c['id']}", headers=b).json['messages'][0]['content']=='edited'
def test_rejected_features(client, users):
    (a,aid),(b,bid)=users
    c=client.post('/api/v1/chats', headers=a, json={'chat_type':'private','target_user_id':bid}).json['chat']
    for payload in [{'message_type':'poll','content':'q'},{'message_type':'gif','content':'x'},{'message_type':'file'},{'message_type':'video_note'},{'message_type':'text','content':'x','is_spoiler':True},{'message_type':'text','content':'x','scheduled_at':'2030-01-01'}]:
        assert client.post(f"/api/v1/messages/chat/{c['id']}", headers=a, json=payload).status_code in (400,403), payload
def test_group_admin_member(client, users):
    (a,aid),(b,bid)=users
    g=client.post('/api/v1/chats', headers=a, json={'chat_type':'group','name':'G','username':'mygroup'}).json['chat']
    assert client.post(f"/api/v1/chats/{g['id']}/members", headers=a, json={'user_id':bid}).status_code==200
    assert client.post(f"/api/v1/chats/{g['id']}/admins/{bid}", headers=a, json={'role':'admin'}).status_code==200
    ch=client.post('/api/v1/chats', headers=a, json={'chat_type':'channel','name':'C','username':'mychan'}).json['chat']
    # member cannot post in channel
    assert client.post(f"/api/v1/messages/chat/{ch['id']}", headers=b, json={'message_type':'text','content':'hi'}).status_code in (403,404)
def test_media_limits_and_admin(client, users, png):
    (a,aid),(b,bid)=users
    up=client.post('/api/v1/media/upload', headers=a, data={'file':(io.BytesIO(png),'x.png'),'type':'image'})
    assert up.status_code==201
    big=b'\x00'*(10*1024*1024)
    assert client.post('/api/v1/media/upload', headers=a, data={'file':(io.BytesIO(big),'v.mp4'),'type':'video'}).status_code==413
    assert client.post('/api/v1/media/upload', headers=a, data={'file':(io.BytesIO(b'GIF89a'),'x.gif'),'type':'gif'}).status_code==400
    tok=client.post('/api/v1/admin/login', json={'username':'admin','password':'adminpass123'}).json['access_token']
    h={'Authorization':f'Bearer {tok}'}
    nu=client.post('/api/v1/admin/users', headers=h, json={'username':'carol','password':'secret123'}); assert nu.status_code==201
    assert client.delete('/api/v1/admin/users/carol', headers=h).status_code==200
    assert client.post('/api/v1/admin/storage/clear', headers=h, json={'mode':'expired'}).status_code==200
def test_static_location_and_block(client, users):
    (a,aid),(b,bid)=users
    c=client.post('/api/v1/chats', headers=a, json={'chat_type':'private','target_user_id':bid}).json['chat']
    r=client.post(f"/api/v1/messages/chat/{c['id']}", headers=a, json={'message_type':'location','latitude':35.7,'longitude':51.4})
    assert r.status_code==201 and r.json['message']['is_live_location'] is False
    assert client.post(f"/api/v1/messages/chat/{c['id']}", headers=a, json={'message_type':'location','latitude':35,'longitude':51,'is_live':True}).status_code==400
    assert client.post(f'/api/v1/users/block/{bid}', headers=a, json={}).status_code==200
def test_retention_expires_media_only_never_messages_or_chats(client, users, png, app):
    from datetime import datetime, timedelta
    from app import db
    from app.models.message import Message
    from app.models.media import MediaFile
    from app.services.retention_maintenance import run_retention_maintenance
    (a,aid),(b,bid)=users
    c=client.post('/api/v1/chats', headers=a, json={'chat_type':'private','target_user_id':bid}).json['chat']
    t=client.post(f"/api/v1/messages/chat/{c['id']}", headers=a, json={'message_type':'text','content':'old text stays'}).json['message']
    up=client.post('/api/v1/media/upload', headers=a, data={'file':(io.BytesIO(png),'x.png'),'type':'image'})
    mid=up.json['media']['id']
    im=client.post(f"/api/v1/messages/chat/{c['id']}", headers=a, json={'message_type':'image','media_id':mid,'content':'caption stays'}).json['message']
    with app.app_context():
        old=datetime.utcnow()-timedelta(hours=100)
        Message.query.filter(Message.id.in_([t['id'],im['id']])).update({'created_at':old}, synchronize_session=False)
        MediaFile.query.filter_by(id=mid).update({'created_at':old}, synchronize_session=False)
        db.session.commit()
        r=run_retention_maintenance()
        assert r['purged_messages']==0 and r['purged_chats']==0 and r['purged_media_files']==1
    msgs=client.get(f"/api/v1/messages/chat/{c['id']}", headers=b).json['messages']
    assert [m['content'] for m in msgs]==['old text stays','caption stays']  # nothing deleted
    img=[m for m in msgs if m['id']==im['id']][0]
    assert img['media_expired'] is True and img['media_url'] is None
    assert client.get(f"/api/v1/media/{mid}", headers=b).status_code in (404,410)
    # chat itself still exists in the list with its last message
    chats=client.get('/api/v1/chats', headers=b).json
    lst=chats.get('chats', chats) if isinstance(chats, dict) else chats
    assert any(x['id']==c['id'] for x in lst)
    # admin clear-storage is also media-only
    tok=client.post('/api/v1/admin/login', json={'username':'admin','password':'adminpass123'}).json['access_token']
    h={'Authorization':f'Bearer {tok}'}
    assert client.post('/api/v1/admin/storage/clear', headers=h, json={'mode':'all'}).status_code==200
    assert len(client.get(f"/api/v1/messages/chat/{c['id']}", headers=b).json['messages'])==2
