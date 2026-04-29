### Flet Routing
```
pip install flet
pip install flet_route
pip install fastapi uvicorn
pip install httpx
```

### Uvicorn reload
```
uvicorn main:app --reload
```

### Fast API test
```
http://localhost:8000/docs
```

### Endpoints

```
GET  /api/health
POST /api/auth/register
POST /api/auth/login
PUT  /api/users/{user_id}
GET  /api/dashboard
```

### Run Flet Hot Run
```
flet main.py -r
```

Run on localhost 
```
flet run --web --port 8000 main.py
```

### Test

```
cd "D:\Central Data\flet-university\src"
uvicorn smartpark.main:app --reload

http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
```

```json
{
  "full_name": "Test User",
  "email": "test@example.com",
  "password": "1234"
}

{
  "email": "test@example.com",
  "password": "1234"
}

```

