# Прикладное программирование if..else
# Приложение

from fastapi import Request, FastAPI, HTTPException, Query
import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import sqlalchemy
#import sqlite3 as sl
from datetime import *
from random import randint
from base64 import b64encode, b64decode
import re
from time import sleep
from os import system

# host.docker.internal
app = FastAPI()
db = sqlalchemy.create_engine('postgresql+psycopg2://postgres:root@localhost:5432/animal_chipization')
#db = sl.connect("db.db", isolation_level = None)
email_re = re.compile(r"[^@]+@[^@]+\.[^@]+")
auth_re = re.compile(r"[^]:[^]")

db.execute('''
DROP TABLE visitedlocations;
DROP TABLE animaltypes;
DROP TABLE animal;
DROP TABLE endpoint;
DROP TABLE area;
DROP TABLE type;
DROP TABLE location_;
DROP TABLE account;

CREATE TABLE IF NOT EXISTS account (
	id BIGSERIAL PRIMARY KEY,
	firstName VARCHAR(256),
	lastName VARCHAR(256),
	email VARCHAR(256) UNIQUE,
	password VARCHAR(256),
	role VARCHAR(256) DEFAULT 'USER'
);

CREATE TABLE IF NOT EXISTS location_ (
	id BIGSERIAL PRIMARY KEY,
	latitude DOUBLE PRECISION,
	longitude DOUBLE PRECISION,
	UNIQUE (latitude, longitude)
);

CREATE TABLE IF NOT EXISTS area (
	id BIGSERIAL PRIMARY KEY,
	name VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS endpoint (
	areaId BIGINT REFERENCES area (id),
	locationId BIGINT REFERENCES location_ (id)
);

CREATE TABLE IF NOT EXISTS type (
	id BIGSERIAL PRIMARY KEY,
	type VARCHAR(256) UNIQUE
);

CREATE TABLE IF NOT EXISTS animal (
	id BIGSERIAL PRIMARY KEY,
	-- animalTypes [long],
	weight FLOAT,
	length FLOAT,
	height FLOAT,
	gender INT, -- MALE, FEMALE, OTHER: [0, 1, 2]
	lifeStatus INT, -- ALIVE, DEAD: [0, 1]
	chippingDateTime TIMESTAMP,
	chipperId INT,
	chippingLocationId BIGINT,
	-- visitedLocations [long],
	deathDateTime TIMESTAMP,
	FOREIGN KEY (chippingLocationId) REFERENCES location_ (id),
	FOREIGN KEY (chipperId) REFERENCES account (id)
);

CREATE TABLE IF NOT EXISTS animaltypes (
	animalId BIGINT,
	typeId BIGINT,
	UNIQUE (animalId, typeId),
	FOREIGN KEY (animalId) REFERENCES animal (id),
	FOREIGN KEY (typeId) REFERENCES type (id)
);
	
CREATE TABLE IF NOT EXISTS visitedlocations (
	id BIGSERIAL PRIMARY KEY,
	animalId BIGINT,
	locationId BIGINT,
	visitDateTime TIMESTAMP,
	UNIQUE (animalId, locationId),
	FOREIGN KEY (animalId) REFERENCES animal (id),
	FOREIGN KEY (locationId) REFERENCES location_ (id)
);

INSERT INTO account (firstName, lastName, email, password, role) VALUES ('adminFirstName', 'adminLastName', 'admin@simbirsoft.com', 'qwerty123', 'ADMIN');
INSERT INTO account (firstName, lastName, email, password, role) VALUES ('chipperFirstName', 'chipperLastName', 'chipper@simbirsoft.com', 'qwerty123', 'CHIPPER');
INSERT INTO account (firstName, lastName, email, password, role) VALUES ('userFirstName', 'userLastName', 'user@simbirsoft.com', 'qwerty123', 'USER');
''')

# ПОСТОЯННЫЕ ВЫРАЖЕНИЯ

# Подготовка к сборке
params = ["id", "animalTypes", "weight", "length", "height",
      "gender", "lifeStatus", "chippingDateTime", "chipperId",
      "chippingLocationId", "visitedLocations", "deathDateTime"]
      
# 0. КЛАССЫ

# 0.0. Пользователь для администратора
class Account2(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    email: str | None = None
    password: str | None = None
    role: str | None = None

# 0.1. Пользователь
class Account(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    email: str | None = None
    password: str | None = None

# 0.2. Локация
class Location(BaseModel):
    latitude: float | None = None
    longitude: float | None = None

# 0.3. Тип животного
class AnimalType(BaseModel):
    type: str | None = None

# 0.4. Животное
class Animal(BaseModel):
    animalTypes: list | None = None
    weight: float | None = None
    length: float | None = None
    height: float | None = None
    gender: str | None = None
    chippingDateTime: str | None = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()
    chippingLocationId: int | None = None
    chipperId: int | None = None

# 0.5. Животное
class Animal2(BaseModel):
    weight: float | None = None
    length: float | None = None
    height: float | None = None
    gender: str | None = None
    lifeStatus: str | None = None
    chippingLocationId: int | None = None
    chipperId: int | None = None

# 0.6. Смена типов
class changeType(BaseModel):
    oldTypeId: int | None = None
    newTypeId: int | None = None

# 0.7. Смена локаций
class changeLoc(BaseModel):
    visitedLocationPointId: int | None = None
    locationPointId: int | None = None

# 0.8. Зона
class Area(BaseModel):
    name: str
    areaPoints: list

# 1. ФУНКЦИИ

# 1.1. Авторизация
def auth(request):

    try:
        auth = request.headers.get("authorization")
        if auth[:6] != "Basic ":
            return "inv"
        
        auth = b64decode(auth[6:]).decode().split(":")
        
        if len(db.execute("""SELECT id FROM account WHERE
                         email = %s AND password = %s""",
            (auth[0], auth[1])).fetchall()) == 0:
            return "inv"
        
        return True
            
    except Exception as e:
        return False

# 1.2. Проверка на пробелы
def ws(x):
    if x.replace(" ", "") == "":
        return True
    else:
        return False

# 1.3. Перевод почты в Id
def to_id(request):
    email = b64decode(request.headers.get("authorization")[6:]
        ).decode().split(":")[0]
    
    return db.execute("SELECT id FROM account WHERE email = %s",
        (email)).fetchall()[0][0]

# 1.4. Проверка на DateTime (если не совпадает!)
def dt(x):
    if re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}').match(x):
        return False
    
    else:
        return True

# 1.5. Проверка на None
def is_none(x):
    for keys, values in x.__dict__.items():
        keys = str(keys)
        if ([keys[0:2], keys[-2:]] != ['__'] * 2 and
            keys not in ["chippingDateTime"]):
            if values is None or values in ["\n", "\t"]:
                return True

# 1.6. Получение информации о животном
def get_an(animalId):
    (id, weight, length, height, gender, lifeStatus, chippingDateTime,
    chipperId, chippingLocationId,
    deathDateTime) = db.execute("SELECT * FROM animal WHERE id = %s",
        (animalId, )).fetchall()[0]
    
    lifeStatus = "ALIVE" if lifeStatus == 0 else "DEAD"
    gender = ["MALE", "FEMALE", "OTHER"][gender]
    
    visitedLocations = [i[0] for i in db.execute("""SELECT id FROM
        visitedlocations WHERE animalId = %s""", (animalId, )).fetchall()] # locationId!
        
    animalTypes = [i[0] for i in db.execute("""SELECT typeId FROM
        animaltypes WHERE animalId = %s""", (animalId, )).fetchall()]
        
    chippingDateTime = chippingDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if deathDateTime is not None:
        deathDateTime = deathDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
    return dict(zip(params, (id, animalTypes, weight, length, height,
        gender, lifeStatus, chippingDateTime, chipperId,
        chippingLocationId, visitedLocations + [chippingLocationId],
        deathDateTime)))

# 1.7. Проверка на Null или < 1
def null_check(x):
    if x is None:
        return True
    if x < 1:
        return True
    return False

# 1.8. Получение роли
def get_role(request):
    return db.execute("SELECT role FROM account WHERE Id = %s", 
        (to_id(request), )).fetchall()[0][0]

# 1.9. Перемножить все элементы массива
mul = lambda arr:arr[0] * mul(arr[1:]) if arr else 1

# 1.10. Проверка на пересечение линий
def ccw(a, b, c):
	return ((c["latitude"] - a["latitude"]) * (b["longitude"] - a["longitude"])
        > (c["longitude"] - a["longitude"]) * (b["latitude"] - a["latitude"]))

def intersect(a, b, c, d):
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)

# 1.11. Проверка на нахождение точки в прямоугольнике
def point_in_polygon(point, polygon):
    x, y = point
    intersections = 0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        if ((y1 <= y < y2 or y2 <= y < y1) and
                x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            intersections += 1
    return intersections % 2 == 1

# Проверка на Date (если не совпадает!)
def dte(x):
    if re.compile(r'^\d{4}-\d{2}-\d{2}').match(x):
        return False
        
    else:
        return True

# 2. ЗАПРОСЫ

# 2.1. РЕГИСТРАЦИЯ
@app.post("/registration", status_code = 201)
async def registration(request: Request, acc: Account):
    
    if "authorization" in request.headers:
        raise HTTPException(status_code = 403)
    
    if is_none(acc):
        raise HTTPException(status_code = 400)
        
    if (ws(acc.firstName) or ws(acc.lastName) or
        not email_re.match(acc.email)
        or acc.password == "" or ws(acc.password)):
        raise HTTPException(status_code = 400)
    
    if len(db.execute("SELECT id FROM account WHERE email = %s",
        (acc.email, )).fetchall()) != 0:
        raise HTTPException(status_code = 409)
    
    db.execute("INSERT INTO account (firstName, lastName, email, password) VALUES (%s, %s, %s, %s)",
        (acc.firstName, acc.lastName, acc.email, acc.password, ))
    
    id = db.execute("SELECT MAX(id) FROM account").fetchall()[0][0]
    
    return dict(zip(["id", "firstName", "lastName", "email", "role"],
        [id, acc.firstName, acc.lastName, acc.email, "USER"]))

# 2.2. АККАУНТ ПОЛЬЗОВАТЕЛЯ

# 2.2.0. Добавление аккаунта пользователя
@app.post("/accounts", status_code = 201)
async def add_account(request: Request, acc: Account2):

    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)

    if (ws(acc.firstName) or ws(acc.lastName) or
        not email_re.match(acc.email) or ws(acc.password) or
        acc.role not in ["USER", "CHIPPER", "ADMIN"]):
        raise HTTPException(status_code = 400)
    
    if len(db.execute("SELECT id FROM account WHERE email = %s",
        (acc.email, )).fetchall()) != 0:
        raise HTTPException(status_code = 409)
    
    db.execute("""INSERT INTO account (firstName, lastName,
                  email, password, role) VALUES (%s, %s, %s, %s, %s)""",
        (acc.firstName, acc.lastName, acc.email, acc.password, acc.role))
    
    id = db.execute("SELECT MAX(id) FROM account").fetchall()[0][0]
    
    return dict(zip(["id", "firstName", "lastName", "email", "role"],
        [id, acc.firstName, acc.lastName, acc.email, acc.role]))
    

# 2.2.1. Получение информации об аккаунте пользователя
@app.get("/accounts/{accountId}")
async def get_account_id(request: Request,
    accountId: int | str | None = None, firstName: str | None = "",
    lastName: str | None = "", email: str | None = "",
    from_: int = Query(default = 0, alias = "from"), size: int | None = 10):
    
    exc = 0
    
    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if accountId == "search":
        return RedirectResponse(f'/search?firstName={firstName}&lastName={lastName}&email={email}&from={from_}&size={size}', status_code = 302)
    
    if null_check(accountId):
        raise HTTPException(status_code = 400)
    
    try:
        role = db.execute("SELECT role FROM account WHERE Id = %s", 
            (to_id(request), )).fetchall()[0][0]
    
        if (db.execute("SELECT role FROM account WHERE Id = %s", 
            (accountId, )).fetchall()[0][0] == "ADMIN"
            and get_role(request) != "ADMIN"):
            raise HTTPException(status_code = 404)
        
        if (accountId != to_id(request) and
            get_role(request) in ["USER", "CHIPPER"]):
            exc = 1
            raise HTTPException(status_code = 403)
        
        return dict(zip(["id", "firstName", "lastName", "email", "role"],
            list(db.execute("""SELECT id, firstName, lastName, email,
                               role FROM account WHERE Id = %s""", 
            (accountId, )).fetchall()[0])))
            
    except Exception as e:
        if exc == 1:
            raise HTTPException(status_code = 403)
        else:
            raise HTTPException(status_code = 404)

# 2.2.2. Поиск аккаунтов пользователей по параметрам
@app.get("/search")
async def search_accounts(request: Request, firstName: str | None = "",
    lastName: str | None = "", email: str | None = "",
    from_: int = Query(default = 0, alias = "from"), size: int | None = 10):
    
    if (from_ < 0 or size <= 0 or '"' in firstName + lastName + email):
        raise HTTPException(status_code = 400)
    
    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)
    
    sql = "SELECT id, firstName, lastName, email, role FROM account"
    if firstName + lastName + email != "":
        sql += " WHERE"
        sc = 0
        if firstName != "":
            sc = 1
            sql += f" firstName ILIKE '%%{firstName}%%'"
        if lastName != "":
            if sc == 1:
                sql += f" AND lastName ILIKE '%%{lastName}%%'"
            else:
                sql += f" lastName ILIKE '%%{lastName}%%'"
                sc = 1
        if email != "":
            if sc == 1:
                sql += f" AND email ILIKE '%%{email}%%'"
            else:
                sql += f" email ILIKE '%%{email}%%'"
    
    sql += f" ORDER BY id ASC LIMIT {size} OFFSET {from_}" ###################### SIZE, FROM ###################
    
    res = []
    
    for i in db.execute(sql).fetchall():
        res.append({"id": i[0], "firstName": i[1], "lastName": i[2],
            "email": i[3], "role": i[4]})
    
    return res

# 2.2.3. Обновление данных аккаунта пользователя
@app.put("/accounts/{accountId}")
async def update_account(request: Request, accountId: int, acc: Account2):
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
    
    if is_none(acc):
        raise HTTPException(status_code = 400)
    
    if (ws(acc.firstName) or ws(acc.lastName) or
        not email_re.match(acc.email) or ws(acc.password)):
        raise HTTPException(status_code = 400)
    
    email = b64decode(request.headers.get("authorization")[6:]).decode().split(":")[0]
    
    if db.execute("SELECT id FROM account WHERE id = %s",
        (accountId, )).fetchall() == []:
        raise HTTPException(status_code = 404)
    
    if db.execute("SELECT role FROM account WHERE Id = %s", 
        (accountId, )).fetchall()[0][0] == "ADMIN":
        raise HTTPException(status_code = 404)
    
    if to_id(request) != accountId and get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)
        
    if db.execute("""UPDATE account SET firstName = %s, lastName = %s,
                     email = %s, password = %s
                     WHERE id = %s AND email = %s""",
        (acc.firstName, acc.lastName, acc.email, acc.password, accountId,
        email, )).rowcount == -1:
        raise HTTPException(status_code = 409)
    
    else:
        return dict(zip(["id", "firstName", "lastName", "email", "role"],
                [accountId, acc.firstName, acc.lastName, acc.email, acc.role]))

# 2.2.4. Удаление аккаунта пользователя
@app.delete("/accounts/{accountId}")
async def delete_account(request: Request, accountId: int | str | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
    
    if null_check(accountId):
        raise HTTPException(status_code = 400)
        
    try:
        if db.execute("SELECT role FROM account WHERE Id = %s", 
            (accountId, )).fetchall()[0][0] == "ADMIN":
            raise HTTPException(status_code = 404)
    except:
        raise HTTPException(status_code = 404)
    
    email = b64decode(request.headers.get("authorization")[6:]
        ).decode().split(":")[0]
    
    if db.execute("SELECT id FROM animal WHERE chipperId = %s",
        (accountId, )).fetchall() != []:
        raise HTTPException(status_code = 400)
    
    if get_role(request) == "ADMIN":
        db.execute("DELETE FROM account WHERE id = %s", (accountId, ))
        return HTTPException(status_code = 200)
    
    else:
        if to_id(request) != accountId:
            raise HTTPException(status_code = 403)
        db.execute("DELETE FROM account WHERE id = %s AND email = %s",
            (accountId, email, ))
    

# 2.3. ТОЧКА ЛОКАЦИИ ЖИВОТНЫХ

# 2.3.1. Получение информации о точке локации животных
@app.get("/locations/{pointId}")
async def get_location(request: Request, pointId: int | None = None):
    
    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if null_check(pointId):
        raise HTTPException(status_code = 400)
    
    try:
        return dict(zip(["id", "latitude", "longitude"],
            db.execute("SELECT * FROM location_ WHERE id = %s",
            (pointId, )).fetchall()[0]))
        
    except Exception as e:
        raise HTTPException(status_code = 404)

# 2.3.2. Добавление точки локации животных
@app.post("/locations", status_code = 201)
async def add_location(request: Request, location: Location):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if is_none(location):
        raise HTTPException(status_code = 400)
    
    if (location.latitude < -90 or location.latitude > 90 or
       location.longitude < -180 or location.longitude > 180):
       raise HTTPException(status_code = 400)
    
    try:
        db.execute("INSERT INTO location_ (latitude, longitude) VALUES (%s, %s)",
            (location.latitude, location.longitude, ))
    
    except Exception as e:
        raise HTTPException(status_code = 409)
        
    id = db.execute("SELECT MAX(id) FROM location_").fetchall()[0][0]
    
    return dict(zip(["id", "latitude", "longitude"],
            [id, location.latitude, location.longitude]))

# 2.3.3. Изменение точки локации животных
@app.put("/locations/{pointId}")
async def update_location(request: Request, location: Location,
    pointId: int | None = None):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if is_none(location):
        raise HTTPException(status_code = 400)
    
    if (location.latitude < -90 or location.latitude > 90 or
       location.longitude < -180 or location.longitude > 180
       or null_check(pointId)):
       raise HTTPException(status_code = 400)
    
    if len(db.execute("SELECT id FROM location_ WHERE id = %s",
        (pointId, )).fetchall()) == 0:
        raise HTTPException(status_code = 404)
    
    try:
        db.execute("""UPDATE location_ SET latitude = %s, longitude = %s
                      WHERE id = %s""", (location.latitude,
                      location.longitude, pointId, ))
        
        return dict(zip(["id", "latitude", "longitude"],
            [pointId, location.latitude, location.longitude]))
    
    except Exception as e:
        raise HTTPException(status_code = 409)

# 2.3.4. Удаление точки локации животных
@app.delete("/locations/{pointId}")
async def delete_location(request: Request, pointId: int | None = None):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)
    
    if null_check(pointId):
        raise HTTPException(status_code = 400)
        
    if (db.execute("SELECT chippingLocationId FROM animal WHERE chippingLocationId = %s",
        (pointId, )).fetchall() != [] or
        db.execute("SELECT locationId FROM visitedlocations WHERE locationId = %s",
        (pointId, )).fetchall() != []):
        raise HTTPException(status_code = 400)
    
    if db.execute("DELETE FROM location_ WHERE id = %s",
        (pointId, )).rowcount != 1:
        t = 1
        raise HTTPException(status_code = 404)
    
    else:
        return HTTPException(status_code = 200)


# 2.4. ТИПЫ ЖИВОТНЫХ

# 2.4.1. Получение информации о типе животного
@app.get("/animals/types/{typeId}")
async def get_animal_type(request: Request, typeId: int | None = None):

    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if null_check(typeId):
        raise HTTPException(status_code = 400)
    
    try:
        return dict(zip(["id", "type"],
            db.execute("SELECT * FROM type WHERE id = %s",
                (typeId, )).fetchall()[0]))
    
    except Exception as e:
        raise HTTPException(status_code = 404)

# 2.4.2. Добавление типа животного
@app.post("/animals/types", status_code = 201)
async def add_animal_type(request: Request, at: AnimalType):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if is_none(at):
        raise HTTPException(status_code = 400)
        
    if ws(at.type):
        raise HTTPException(status_code = 400)
    
    try:
        db.execute("INSERT INTO type (type) VALUES (%s)", (at.type, ))
        
    except Exception as e:
        raise HTTPException(status_code = 409)
    
    id = db.execute("SELECT MAX(id) FROM type").fetchall()[0][0]
    
    return dict(zip(["id", "type"], [id, at.type]))

# 2.4.3. Изменение типа животного
@app.put("/animals/types/{typeId}")
async def update_animal_type(request: Request, at: AnimalType,
    typeId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if null_check(typeId) or is_none(at) or ws(at.type):
        raise HTTPException(status_code = 400)
    
    if db.execute("SELECT id FROM type WHERE id = %s",
        (typeId, )).fetchall() == []:
        raise HTTPException(status_code = 404)
    
    try:
        if db.execute("UPDATE type SET type = %s WHERE id = %s",
            (at.type, typeId, )).rowcount == -1:
            t = 1
            raise HTTPException(status_code = 404)
        
        else:
            return dict(zip(["id", "type"], [typeId, at.type]))
    
    except Exception as e:
        if t == 1:
            raise HTTPException(status_code = 404)
        raise HTTPException(status_code = 409)
    

# 2.4.4. Удаление типа животного
@app.delete("/animals/types/{typeId}")
async def delete_animal_type(request: Request, typeId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)
    
    if null_check(typeId):
        raise HTTPException(status_code = 400)
    
    if db.execute("SELECT id FROM type WHERE id = %s",
        (typeId, )).fetchall() == []:
        raise HTTPException(status_code = 404)
    
    try:
        if db.execute("DELETE FROM type WHERE id = %s",
            (typeId, )).rowcount != 1:
            t = 1
            raise HTTPException(status_code = 404)
        
        else:
            return HTTPException(status_code = 200)
    
    except:
        if t == 1:
            raise HTTPException(status_code = 404)
        raise HTTPException(status_code = 400)

# 2.5. ЖИВОТНОЕ

# 2.5.1. Получение информации о животном
@app.get("/animals/{animalId}")
async def get_animal(request: Request, animalId: int | str | None = None,
    typeId: int | None = None,
    startDateTime: str | None = "1970-01-01T00:00:00",
    endDateTime: str | None = datetime.now(tz=timezone.utc).isoformat()[:-13] + "Z",
    chipperId: int | None = None, chippingLocationId: int | None = None,
    lifeStatus: str | None = "", gender: str | None = "",
    from_: int = Query(default = 0, alias = "from"), size: int | None = 10):

    if auth(request) == "inv":
        raise HTTPException(status_code = 401)

    if animalId == "search":
        x = f"/asearch?startDateTime={startDateTime}&endDateTime={endDateTime}&lifeStatus={lifeStatus}&gender={gender}&from={from_}&size={size}"
                
        if chipperId is not None:
            x += f"&chipperId={chipperId}"
        if chippingLocationId is not None:
            x += f"&chippingLocationId={chippingLocationId}"
            
        return RedirectResponse(x, status_code = 302)
    
    if null_check(animalId):
        raise HTTPException(status_code = 400)
    
    try:
        return get_an(animalId)
    
    except Exception as e:
        raise HTTPException(status_code = 404)

# 2.5.2. Поиск животных по параметрам
@app.get("/asearch")
async def search_animals(request: Request,
    startDateTime: str | None = "1970-01-01T00:00:00",
    endDateTime: str | None = datetime.now(tz=timezone.utc).isoformat()[:-13] + "Z",
    chipperId: int | None = None, chippingLocationId: int | None = None,
    lifeStatus: str | None = "", gender: str | None = "",
    from_: int = Query(default = 0, alias = "from"), size: int | None = 10):
    
    if (from_ < 0 or size <= 0 or dt(startDateTime) or dt(endDateTime) or
        lifeStatus not in ["ALIVE", "DEAD", ""]
        or gender not in ["MALE", "FEMALE", "OTHER", ""]):
        raise HTTPException(status_code = 400)
        
    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
    
    if chipperId is not None:
        if chipperId < 1:
            raise HTTPException(status_code = 400)
    
    if chippingLocationId is not None:
        if chippingLocationId < 1:
            raise HTTPException(status_code = 400)
    
    sql = "SELECT * FROM animal WHERE"
    sc = 0
    
    if lifeStatus + gender != "":
        
        if lifeStatus != "":
            sc = 1
            l = ["ALIVE", "DEAD"].index(lifeStatus)
            sql += f" lifeStatus = {l}"
        if gender != "":
            g = ["MALE", "FEMALE", "OTHER"].index(gender)
            if sc == 1:
                sql += f" AND gender = {g}"
            else:
                sql += f" gender = {g}"
                sc = 1
    
    if chipperId is not None:
        if sc == 1:
            sql += f' AND chipperId = {chipperId}'
        else:
            sql += f' chipperId = {chipperId}'
            sc = 1
    
    if chippingLocationId is not None:
        if sc == 1:
            sql += f' AND chippingLocationId = {chippingLocationId}'
        else:
            sql += f' chippingLocationId = {chippingLocationId}'
            sc = 1
    
    if sc == 1:
        sql += f" AND chippingDateTime BETWEEN cast('{startDateTime}' AS TIMESTAMP) AND cast('{endDateTime}' AS TIMESTAMP) ORDER BY id ASC LIMIT {size} OFFSET {from_}"
    else:
        sql += f" chippingDateTime BETWEEN cast('{startDateTime}' AS TIMESTAMP) AND cast('{endDateTime}' AS TIMESTAMP) ORDER BY id ASC LIMIT {size} OFFSET {from_}"
    
    res = db.execute(sql).fetchall()
    ret = []
    
    for i in res:
        (id, weight, length, height, gender, lifeStatus, chippingDateTime,
            chipperId, chippingLocationId,
            deathDateTime) = i
            
        gender = ["MALE", "FEMALE", "OTHER"][gender]
        lifeStatus = ["ALIVE", "DEAD"][lifeStatus]
            
        visitedLocations = [j[0] for j in db.execute("""SELECT locationId FROM
            visitedlocations WHERE animalId = %s""", (id, )).fetchall()]
            
        animalTypes = [j[0] for j in db.execute("""SELECT typeId FROM
            animaltypes WHERE animalId = %s""", (id, )).fetchall()]
            
        chippingDateTime = chippingDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if deathDateTime is not None:
            deathDateTime = deathDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        ret.append(dict(zip(params, [id, animalTypes, weight, length, height,
                    gender, lifeStatus, chippingDateTime, chipperId,
                    chippingLocationId, visitedLocations, deathDateTime])))
    
    return ret

# 2.5.3. Добавление нового животного
@app.post("/animals", status_code = 201)
async def add_animal(request: Request, a: Animal):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if is_none(a):
        raise HTTPException(status_code = 400)
    
    if (len(a.animalTypes) < 1 or
        True in [i < 1 for i in a.animalTypes] or a.weight <= 0 or
        a.length <= 0 or a.height <= 0
        or a.gender not in ["MALE", "FEMALE", "OTHER"]
        or a.chipperId < 1 or a.chippingLocationId < 1):
        
        raise HTTPException(status_code = 400)
    
    if len(a.animalTypes) != len(list(set(a.animalTypes))):
        raise HTTPException(status_code = 409)
    
    try:
        g = ["MALE", "FEMALE", "OTHER"].index(a.gender)
        db.execute("""INSERT INTO animal (weight, length, height, gender,
                      lifeStatus, chippingDateTime, chipperId,
                      chippingLocationId, deathDateTime) VALUES
                      (%s, %s, %s, %s, 0, %s, %s, %s, null)""",
                      (a.weight, a.length, a.height,
            g, a.chippingDateTime, a.chipperId, a.chippingLocationId, ))
        
        id, chippingDateTime = db.execute(
            """SELECT (SELECT MAX(id) FROM animal),
              (SELECT chippingDateTime FROM animal
               ORDER BY id DESC LIMIT 1);""").fetchall()[0]
        
        chippingDateTime = chippingDateTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        for i in a.animalTypes:
            if db.execute("SELECT id FROM type WHERE id = %s",
                (i, )).fetchall() == []:
                raise HTTPException(status_code = 404)
                
            db.execute("INSERT INTO animaltypes VALUES (%s, %s)",
                (id, i, ))
        
        return dict(zip(params, [id, a.animalTypes, a.weight, a.length,
            a.height, a.gender, "ALIVE", chippingDateTime,
            a.chipperId, a.chippingLocationId, [a.chippingLocationId], None]))
        
    except Exception as e:
        raise HTTPException(status_code = 404)

# 2.5.4. Обновление информации о животном
@app.put("/animals/{animalId}")
async def update_animal(request: Request, a: Animal2,
    animalId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if (null_check(animalId) or is_none(a) or a.weight <= 0 or a.height <= 0
        or a.length <= 0 or a.gender not in ["MALE", "FEMALE", "OTHER"] or
        a.lifeStatus not in ["ALIVE", "DEAD"]):
        raise HTTPException(status_code = 400)
    
    g = ["MALE", "FEMALE", "OTHER"].index(a.gender)
    l = ["ALIVE", "DEAD"].index(a.lifeStatus)
    sc = 0
    
    try:
        get_an(animalId)
    except Exception as e:
        raise HTTPException(status_code = 404)
    
    try:
        if (db.execute("SELECT lifeStatus FROM animal WHERE id = %s",
            (animalId, )).fetchall()[0][0] == 1 and a.lifeStatus == "ALIVE"):
            t = 1
            raise HTTPException(status_code = 400)
        
        if (db.execute("SELECT lifeStatus FROM animal WHERE id = %s",
            (animalId, )).fetchall()[0][0] == 0 and a.lifeStatus == "DEAD"):
            sc = 1
        
        if len(db.execute("SELECT id FROM account WHERE id = %s",
            (a.chipperId, )).fetchall()) == 0:
            t = 2
            raise HTTPException(status_code = 404)
    
    except Exception as e:
        if t == 1:
            raise HTTPException(status_code = 400)
        raise HTTPException(status_code = 404)
    
    r = db.execute("""SELECT locationId FROM visitedlocations
                      WHERE animalId = %s LIMIT 1""", (animalId, ))
    m = r.fetchall()
    if len(m) != 0:
        if m[0][0] == a.chippingLocationId:
            raise HTTPException(status_code = 400)
    
    sql = """UPDATE animal SET weight = %s, height = %s, length = %s,
             gender = %s, chipperId = %s, lifeStatus = %s,
             chippingLocationId = %s"""
    
    deathDateTime = None
    if sc == 1:
        deathDateTime = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()
        sql += f", deathDateTime = '{deathDateTime}'"
        
    sql += " WHERE id = %s"
    
    try:
        db.execute(sql, (a.weight, a.height, a.length,
                      g, a.chipperId, l, a.chippingLocationId, animalId, ))
    
    except Exception as e:
        raise HTTPException(status_code = 404)
    
    return get_an(animalId)
    
# 2.5.5. Удаление животного
@app.delete("/animals/{animalId}")
async def delete_animal(request: Request, animalId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)
    
    if null_check(animalId):
        raise HTTPException(status_code = 400)
    
    try:
        get_an(animalId)
    except Exception as e:
        raise HTTPException(status_code = 404)
    
    if db.execute("SELECT id FROM visitedlocations WHERE animalId = %s",
        (animalId, )).fetchall() != []:
        raise HTTPException(status_code = 400)
    
    try:
        db.execute("DELETE FROM animaltypes WHERE animalId = %s",
           (animalId, ))
        if db.execute("DELETE FROM animal WHERE id = %s",
            (animalId, )).rowcount == -1:
            t = 1
            raise HTTPException(status_code = 404)
        
        else:
            return HTTPException(status_code = 200)
    
    except Exception as e:
        if t == 1:
            raise HTTPException(status_code = 404)
        raise HTTPException(status_code = 400)

# 2.5.6. Добавление типа животного к животному
@app.post("/animals/{animalId}/types/{typeId}", status_code = 201)
async def add_type_to_animal(request: Request, animalId: int | None = None,
    typeId: int | None = None):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
        
    if null_check(animalId) or null_check(typeId):
        raise HTTPException(status_code = 400)
        
    try:
        db.execute("INSERT INTO animaltypes VALUES (%s, %s)",
            (animalId, typeId, ))
            
        return get_an(animalId)
    
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code = 409)
        else:
            raise HTTPException(status_code = 404)
    

# 2.5.7. Изменение типа животного у животного
@app.put("/animals/{animalId}/types")
async def update_type_for_animal(request: Request,
    c: changeType | None = None, animalId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if c is None:
        raise HTTPException(status_code = 400)
        
    if (null_check(animalId) or null_check(c.oldTypeId)
        or null_check(c.newTypeId)):
        raise HTTPException(status_code = 400)
        
    try:
        get_an(animalId)
    except Exception as e:
        raise HTTPException(status_code = 404)
        
    if (db.execute("SELECT typeId FROM animaltypes WHERE typeId = %s and animalId = %s",
        (c.oldTypeId, animalId, )).fetchall() == [] or
        db.execute("SELECT type FROM type WHERE id = %s",
        (c.newTypeId, )).fetchall() == []):
        raise HTTPException(status_code = 404)
        
    try:
        if db.execute("""UPDATE animaltypes SET typeId = %s
                      WHERE animalId = %s AND typeId = %s""",
            (c.newTypeId, animalId, c.oldTypeId, )).rowcount == -1:
                t = 1
                raise HTTPException(status_code = 404)
        
        return get_an(animalId)
    
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code = 409)
        if t == 1:
            raise HTTPException(status_code = 404)


# 2.5.8. Удаление типа животного у животного
@app.delete("/animals/{animalId}/types/{typeId}")
async def delete_type_for_animal(request: Request,
    animalId: int | None = None, typeId: int | None = None):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
        
    if null_check(animalId) or null_check(typeId):
        raise HTTPException(status_code = 400)
    
    if db.execute("SELECT typeId FROM animaltypes WHERE typeId = %s AND animalId = %s",
        (typeId, animalId, )).fetchall() == []:
        raise HTTPException(status_code = 404)
    
    if db.execute("SELECT COUNT(*) FROM animaltypes WHERE animalId = %s",
        (animalId, )).fetchall()[0][0] == 1:
        raise HTTPException(status_code = 400)

    try:
        x = get_an(animalId)
    except:
        raise HTTPException(status_code = 404)
    
    if db.execute("""DELETE FROM animaltypes
                     WHERE animalId = %s AND typeId = %s""",
        (animalId, typeId, )).rowcount == -1:
        raise HTTPException(status_code = 404)
    
    else:
        return x


# 2.6. ТОЧКА ЛОКАЦИИ, ПОСЕЩЁННАЯ ЖИВОТНЫМ

# 2.6.1. Просмотр точек локации, посещенных животным
@app.get("/animals/{animalId}/locations")
async def view_visited(request: Request, animalId: int | None = None,
    startDateTime: str | None = None,
    endDateTime: str | None = None,
    from_: int = Query(default = 0, alias = "from"), size: int | None = 10):
    
    if auth(request) == "inv":
        raise HTTPException(status_code = 401)
    
    if null_check(animalId):
        raise HTTPException(status_code = 400)
        
    try:
        get_an(animalId)
    except Exception as e:
        raise HTTPException(status_code = 404)
    
    if startDateTime is not None and endDateTime is not None:
        res = db.execute("""SELECT visitedlocations.id, visitDateTime, locationId FROM visitedlocations
                            WHERE animalId = %s AND visitDateTime BETWEEN %s AND %s
                            ORDER BY visitDateTime ASC LIMIT %s OFFSET %s""",
            (animalId, startDateTime, endDateTime, size, from_, )).fetchall()
    
    elif startDateTime is not None:
        res = db.execute("""SELECT visitedlocations.id, visitDateTime, locationId FROM visitedlocations
                            WHERE animalId = %s AND visitDateTime >= %s
                            ORDER BY visitDateTime ASC LIMIT %s OFFSET %s""",
            (animalId, startDateTime, size, from_, )).fetchall()
    
    elif endDateTime is not None:
        res = db.execute("""SELECT visitedlocations.id, visitDateTime, locationId FROM visitedlocations
                            WHERE animalId = %s AND visitDateTime <= %s
                            ORDER BY visitDateTime ASC LIMIT %s OFFSET %s""",
            (animalId, endDateTime, size, from_, )).fetchall()
    
    else:
        res = db.execute("""SELECT visitedlocations.id, visitDateTime, locationId FROM visitedlocations
                            WHERE animalId = %s
                            ORDER BY visitDateTime ASC LIMIT %s OFFSET %s""",
            (animalId, size, from_, )).fetchall()
    
    return [dict(zip(["id", "dateTimeOfVisitLocationPoint", "locationPointId"],
        [i[0], i[1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), i[2]])) for i in res]
    
    
# 2.6.2. Добавление точки локации, посещенной животным
@app.post("/animals/{animalId}/locations/{pointId}", status_code = 201)
async def add_visited(request: Request, animalId: int | None = None,
    pointId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if null_check(animalId) or null_check(pointId):
        raise HTTPException(status_code = 400)
    
    if db.execute("SELECT id FROM location_ WHERE id = %s",
        (pointId, )).fetchall() == []:
        raise HTTPException(status_code = 404)
    
    try:
        c = db.execute("""SELECT lifeStatus, chippingLocationId
                          FROM animal WHERE id = %s""",
            (animalId, )).fetchall()[0]
        if c[0] == 1 or c[1] == pointId:
            t = 1
            raise HTTPException(status_code = 400)
    except:
        if t == 1:
            raise HTTPException(status_code = 400)
        raise HTTPException(status_code = 404)
    
    dt_ = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()
    
    try:
        db.execute("""INSERT INTO visitedlocations
                      (animalId, locationId, visitDateTime) VALUES (%s, %s, %s)""",
            (animalId, pointId, dt_, ))
        
        id = db.execute("""SELECT MAX(id)
                           FROM visitedlocations""").fetchall()[0][0]
        
        return dict(zip(["id", "locationPointId",
            "dateTimeOfVisitLocationPoint"], [id, pointId, dt_]))
    
    except Exception as e:
        if "foreign key" in str(e):
            raise HTTPException(status_code = 404)
        raise HTTPException(status_code = 400)

# 2.6.3. Изменение точки локации, посещённой животным
@app.put("/animals/{animalId}/locations")
async def update_visited(request: Request, a: changeLoc,
    animalId: int | None = None):
    t = 0
    
    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) == "USER":
        raise HTTPException(status_code = 403)
    
    if (null_check(animalId) or
        null_check(a.locationPointId)
        or null_check(a.visitedLocationPointId)):
        raise HTTPException(status_code = 400)
        
    try:
        if db.execute("""SELECT id FROM visitedlocations
                         WHERE animalId = %s ORDER BY id ASC""",
            (animalId, )).fetchall()[0][0] == a.visitedLocationPointId:
            
            if (a.locationPointId ==
            db.execute("""SELECT chippingLocationId FROM animal
                          WHERE id = %s""", (animalId, ))):
                
                raise HTTPException(status_code = 400)
    except:
        pass
    
    if db.execute("SELECT id FROM location_ WHERE id = %s",
        (a.locationPointId, )).fetchall() == []:
        raise HTTPException(status_code = 404)
    
    b = db.execute("""SELECT locationId FROM visitedlocations
                      WHERE id = %s AND animalId = %s""",
        (a.visitedLocationPointId, animalId, )).fetchall()
    
    if b == []:
        raise HTTPException(status_code = 404)
    
    if b[0][0] == a.locationPointId:
        raise HTTPException(status_code = 400)
        
    try:
        get_an(animalId)
    except Exception as e:
        raise HTTPException(status_code = 404)
    
    try:
        db.execute("""UPDATE visitedlocations SET locationId = %s
                      WHERE id = %s""",
            (a.locationPointId, a.visitedLocationPointId, ))
        
        dt_ = db.execute("""SELECT visitDateTime
                            FROM visitedlocations WHERE id = %s""",
            (a.visitedLocationPointId, )
            ).fetchall()[0][0].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        return dict(zip(["id", "locationPointId",
            "dateTimeOfVisitLocationPoint"],
            [a.visitedLocationPointId, a.locationPointId, dt_]))
    
    except Exception as e:
        if "foreign key" in str(e):
            raise HTTPException(status_code = 404)
        else:
            raise HTTPException(status_code = 400)
    

# 2.6.4. Удаление точки локации, посещённой животным
@app.delete("/animals/{animalId}/locations/{visitedPointId}")
async def delete_visited(request: Request, animalId: int | None = None,
    visitedPointId: int | None = None):

    if not auth(request) or auth(request) == "inv":
        raise HTTPException(status_code = 401)
        
    if get_role(request) != "ADMIN":
        raise HTTPException(status_code = 403)
    
    if null_check(animalId) or null_check(visitedPointId):
        raise HTTPException(status_code = 400)
        
    try:
        get_an(animalId)
    except Exception as e:
        raise HTTPException(status_code = 404)
    
    if db.execute("""DELETE FROM visitedlocations
                     WHERE animalId = %s AND id = %s""",
        (animalId, visitedPointId, )).rowcount == -1:
        raise HTTPException(status_code = 404)
    
    else:
        raise HTTPException(status_code = 200)

# 2.7. ЗОНЫ

# 2.7.1. Просмотр информации о зоне
@app.get("/areas/{areaId}")
async def view_area(request: Request, areaId: int | str | None = None,
    startDate: str | None = "1970-01-01",
    endDate: str | None = datetime.now(tz = timezone.utc).isoformat()[:10]):
    if not auth(request) or auth(request) == "inv": # Проверка на авторизацию
        raise HTTPException(status_code = 401)
    
    if null_check(areaId):
        raise HTTPException(status_code = 400)
    
    if areaId == "analytics":
        return RedirectResponse(f'/analytics?areaId={areaId}&startDate={startDate}&endDate={endDate}', status_code = 302)
    
    try:
        name = db.execute("SELECT name FROM area WHERE id = %s",
            (areaId)).fetchall()[0][0]
    except:
        raise HTTPException(status_code = 404)
    
    return {"id": areaId, "name": name,
           "areaPoints": [{"longitude": i[0], "latitude": i[1]}
           for i in db.execute(
           """SELECT longitude, latitude FROM endpoint
              INNER JOIN area ON area.id = areaId
              INNER JOIN location_ ON location_.id = locationId
              WHERE areaId = %s""", (areaId)).fetchall()]}
    

# 2.7.2. Добавление зоны
@app.post("/areas", status_code = 201)
async def add_area(request: Request, area: Area):
    exc = 0

    if not auth(request) or auth(request) == "inv": # Проверка на авторизацию
        raise HTTPException(status_code = 401)
    
    if get_role(request) != "ADMIN": # Проверка на админа
        raise HTTPException(status_code = 403)
    
    if is_none(area): # Проверка всех атрибутов на null в объекте Area
        raise HTTPException(status_code = 400)
        
    if ws(area.name) or len(area.areaPoints) < 3: # Проверка на null или < 3
        raise HTTPException(status_code = 400)
    
    # Проверка на longitude и latitude
    for i in area.areaPoints:
        if i["longitude"] is None or i["latitude"] is None:
            raise HTTPException(status_code = 400)
        if (not -90 <= i["latitude"] <= 90 or
            not -180 <= i["longitude"] <= 180):
            raise HTTPException(status_code = 400)

    # Проверка на нахождение точек на одной прямой
    chkstm = ''
    for i in area.areaPoints[1:]:
        chkstm += f'({i["longitude"] - area.areaPoints[0]["longitude"]}) * ({i["latitude"] - area.areaPoints[0]["latitude"]}) == '
    if eval(chkstm[:-4]):
        raise HTTPException(status_code = 400)

    for i in range(len(area.areaPoints) - 1): # Проверка на пересечение отрезков
        for j in range(len(area.areaPoints) - 1):
            if (intersect(area.areaPoints[i], area.areaPoints[i + 1],
                area.areaPoints[j], area.areaPoints[j + 1]) and
                area.areaPoints[i] != area.areaPoints[j + 1] and
                area.areaPoints[j] != area.areaPoints[i + 1]):
                raise HTTPException(status_code = 400)
    
    # Проверка на дубликаты точек
    dupp = [[i["longitude"], i["latitude"]] for i in area.areaPoints]
    for i in dupp:
        if dupp.count(i) > 1:
            raise HTTPException(status_code = 400)
    
    # Образование массива с точками всех зон
    e = db.execute(
           """SELECT areaId, longitude, latitude FROM endpoint
              INNER JOIN area ON area.id = areaId
              INNER JOIN location_ ON location_.id = locationId""").fetchall()
    areas = []
    
    for i in list(set([i[0] for i in e])):
        tmp = []
        for j in e:
            if j[0] == i:
                tmp.append(j[1:])
        areas.append(tmp)
    
    p = [[i["longitude"], i["latitude"]] for i in area.areaPoints]
    
    # Границы новой зоны находятся внутри границ существующей зоны.
    for i in areas:
        for j in p:
            if point_in_polygon(j, i) == True and j not in i:
                raise HTTPException(status_code = 400)
    
    # Границы существующей зоны находятся внутри границ новой зоны.
    for i in areas:
        for j in i:
            if point_in_polygon(j, p) == True:
                raise HTTPException(status_code = 400)
    
    # Зона, состоящая из таких точек, уже существует. (При этом важен порядок, в котором указаны точки, но не важна начальная точка).
    for i in areas:
        if p[1:] == i[1:]:
            raise HTTPException(status_code = 409)
    
    # Зона с таким name уже существует
    try:
        db.execute("INSERT INTO area (name) VALUES (%s)", (area.name))
    except:
        raise HTTPException(status_code = 409)
    
    aid = db.execute("SELECT max(id) FROM area").fetchall()[0][0]
    
    for i in p:
        db.execute("""INSERT INTO location_ (longitude, latitude)
                      VALUES (%s, %s)""", (i[0], i[1]))
        db.execute("""INSERT INTO endpoint (areaId, locationId)
                      VALUES (%s, (SELECT max(id) FROM location_))""", (aid))
    
    return {"id": aid, "name": area.name, "areaPoints": area.areaPoints}
    
    # Новая зона состоит из части точек существующей зоны и находится на площади существующей зоны.??????
    
# 2.7.3. Изменение зоны
@app.put("/areas/{areaId}", status_code = 200)
async def edit_area(request: Request, area: Area, areaId: int | None = None):
    exc = 0

    if not auth(request) or auth(request) == "inv": # Проверка на авторизацию
        raise HTTPException(status_code = 401)
    
    if get_role(request) != "ADMIN": # Проверка на админа
        raise HTTPException(status_code = 403)
    
    if is_none(area) or null_check(areaId): # Проверка всех атрибутов на null в объекте Area и проверка areaId на None
        raise HTTPException(status_code = 400)
    
    ###################### ДУБЛИКАТ ######################
    
    # Проверка на longitude и latitude
    for i in area.areaPoints:
        if i["longitude"] is None or i["latitude"] is None:
            raise HTTPException(status_code = 400)
        if (not -90 <= i["latitude"] <= 90 or
            not -180 <= i["longitude"] <= 180):
            raise HTTPException(status_code = 400)

    # Проверка на нахождение точек на одной прямой
    chkstm = ''
    for i in area.areaPoints[1:]:
        chkstm += f'({i["longitude"] - area.areaPoints[0]["longitude"]}) * ({i["latitude"] - area.areaPoints[0]["latitude"]}) == '
    if eval(chkstm[:-4]):
        raise HTTPException(status_code = 400)

    for i in range(len(area.areaPoints) - 1): # Проверка на пересечение отрезков
        for j in range(len(area.areaPoints) - 1):
            if (intersect(area.areaPoints[i], area.areaPoints[i + 1],
                area.areaPoints[j], area.areaPoints[j + 1]) and
                area.areaPoints[i] != area.areaPoints[j + 1] and
                area.areaPoints[j] != area.areaPoints[i + 1]):
                raise HTTPException(status_code = 400)
    
    # Проверка на дубликаты точек
    dupp = [[i["longitude"], i["latitude"]] for i in area.areaPoints]
    for i in dupp:
        if dupp.count(i) > 1:
            raise HTTPException(status_code = 400)
    
    # Образование массива с точками всех зон
    e = db.execute(
           """SELECT areaId, longitude, latitude FROM endpoint
              INNER JOIN area ON area.id = areaId
              INNER JOIN location_ ON location_.id = locationId""").fetchall()
    areas = []
    
    for i in list(set([i[0] for i in e])):
        tmp = []
        for j in e:
            if j[0] == i:
                tmp.append(j[1:])
        areas.append(tmp)
    
    p = [[i["longitude"], i["latitude"]] for i in area.areaPoints]
    
    # Границы новой зоны находятся внутри границ существующей зоны.
    for i in areas:
        for j in p:
            if point_in_polygon(j, i) == True and j not in i:
                raise HTTPException(status_code = 400)
    
    # Границы существующей зоны находятся внутри границ новой зоны.
    for i in areas:
        for j in i:
            if point_in_polygon(j, p) == True:
                raise HTTPException(status_code = 400)
    
    # Зона, состоящая из таких точек, уже существует. (При этом важен порядок, в котором указаны точки, но не важна начальная точка).
    for i in areas:
        if p[1:] == i[1:]:
            raise HTTPException(status_code = 409)
    
    # Зона с таким name уже существует
    try:
        db.execute("UPDATE area SET name = %s WHERE id = %s", (area.name, areaId))
    except:
        raise HTTPException(status_code = 409)
    
    db.execute("DELETE FROM endpoint WHERE areaId = %s", (areaId))
    
    for i in p:
        try:
            db.execute("""INSERT INTO location_ (longitude, latitude)
                          VALUES (%s, %s)""", (i[0], i[1]))
        except:
            pass
        db.execute("""INSERT INTO endpoint (areaId, locationId)
                      VALUES (%s, (SELECT max(id) FROM location_))""",
            (areaId))
    
    return {"id": areaId, "name": area.name, "areaPoints": area.areaPoints}

# 2.7.4. Удаление зоны
@app.delete("/areas/{areaId}", status_code = 200)
async def delete_area(request: Request, areaId: int | None = None):
    if not auth(request) or auth(request) == "inv": # Проверка на авторизацию
        raise HTTPException(status_code = 401)
    
    if get_role(request) != "ADMIN": # Проверка на админа
        raise HTTPException(status_code = 403)
    
    if null_check(areaId):
        raise HTTPException(status_code = 400)
    
    db.execute("DELETE FROM endpoint WHERE areaId = %s", (areaId))
    if db.execute("DELETE FROM area WHERE id = %s",
        (areaId)).rowcount != 1:
        raise HTTPException(status_code = 404)

# 2.8. АНАЛИТИКА ПО ЗОНАМ
@app.get("/analytics")
async def analytics(request: Request, areaId: int | str | None = None,
    startDate: str | None = "1970-01-01",
    endDate: str | None = datetime.now(tz = timezone.utc).isoformat()[:10]):
    
    if not auth(request) or auth(request) == "inv": # Проверка на авторизацию
        raise HTTPException(status_code = 401)
    
    if dte(startDate) or dte(endDate):
        raise HTTPException(status_code = 400)
    
    if datetime.fromisoformat(startDate) > datetime.fromisoformat(endDate):
        raise HTTPException(status_code = 400)
    
    totalQuantityAnimals = 0
    totalAnimalsArrived = 0
    totalAnimalsGone = 0
    animalAnalytics = []
    try:
        areaName = db.execute("SELECT name FROM area WHERE id = %s",
            (areaId)).fetchall()[0][0]
    except:
        raise HTTPException(status_code = 404)
    
    areaPoints = []
    
    # Берём массив из точек зоны
    for i in db.execute('''
        SELECT longitude, latitude FROM location_
        INNER JOIN endpoint ON locationId = location.id
        WHERE areaId = %s''', (areaId)).fetchall():
        areaPoints.append([i[0], i[1]])
    
    # Если животные нескольких типов и они повторяются
    repeatedQuantityAnimals = 0
    repeatedAnimalsArrived = 0
    repeatedAnimalsGone = 0
    
    # Итерация по каждому типу животных
    for type in db.execute("SELECT * FROM type").fetchall():
        quantityAnimals = 0
        animalsArrived = 0
        animalsGone = 0
        # Итерация по животным
        for animal in db.execute("SELECT animalId FROM animaltypes WHERE typeId = %s",
            (type[0])).fetchall():
            # Итерация по каждой посещённой в заданный интервал
            visited = 0
            gone = 0
            out = 0
            in_ = 0
            for location in db.execute('''
            SELECT longitude, latitude FROM location_
            INNER JOIN visitedlocations ON locationId = location_.id
            WHERE animalId = %s AND visitDateTime BETWEEN %s AND %s
            ''', (animal[0], startDate, endDate)).fetchall():
                # Проверка на локацию:
                if point_in_polygon([location[0], location[1]], areaPoints):
                    if out > 0:
                        visited += 1
                    else:
                        in_ += 1
                elif visited > 0 or in_ > 0:
                    gone += 1
                else:
                    out += 1
            # Распределение по статистике
            if visited > 0 or gone > 0 or in_ > 0:
                quantityAnimals += 1
                if animal[0] in animals:
                    repeatedQuantityAnimals += 1
            elif visited > 0:
                animalsArrived += 1
                if animal[0] in animals:
                    repeatedAnimalsArrived += 1
            elif gone > 0:
                animalsGone += 1
                if animal[0] in animals:
                    repeatedAnimalsGone += 1
        animals.append(animal[0])
        
        # Распределение по глобальной статистикке
        totalQuantityAnimals += quantityAnimals
        totalAnimalsArrived += animalsArrived
        totalAnimalsGone += animalsGone
        
        # Добавление в массив
        animalAnalytics.append({"animalType": type[1],
            "animalTypeId": type[0], "quantityAnimals": quantityAnimals,
            "animalsArrived": animalsArrived, "animalsGone": animalsGone})
    
    # Вычитаем повторы
    totalQuantityAnimals -= repeatedQuantityAnimals
    totalAnimalsArrived -= repeatedAnimalsArrived
    totalAnimalsGone -= repeatedAnimalsGone
    
    # Возвращаем значение
    return {"totalQuantityAnimals": totalQuantityAnimals,
        "totalAnimalsArrived": totalAnimalsArrived,
        "totalAnimalsGone": totalAnimalsGone,
        "animalAnalytics": animalAnalytics}