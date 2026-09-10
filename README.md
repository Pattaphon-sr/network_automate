# Cisco Router Web Console

โปรเจกต์ Lab สำหรับส่งคำสั่ง CLI จากเว็บเบราว์เซอร์ไปยัง Cisco 7200 ผ่าน SSH โดยใช้ Flask เป็น Web/API server และ Paramiko เป็น SSH client แอปทำงานภายใน Docker และบริหารด้วย Docker Compose

## ภาพรวมระบบ

```text
Web Browser
    | HTTP :8081
    v
Flask + Gunicorn (Docker Container)
    | SSH :22 ด้วย Paramiko
    v
Cisco 7200 Router
```

## ความสามารถ

- กรอก Router IP ผ่านหน้าเว็บ
- กรอกและส่งคำสั่ง Cisco CLI ครั้งละหนึ่งคำสั่ง
- แสดงผลลัพธ์หรือข้อผิดพลาดบนหน้าเว็บ
- ปิด terminal pagination ด้วย `terminal length 0`
- ตรวจสอบรูปแบบ IP และจำกัดความยาว command
- มี `/health` endpoint และ Docker health check
- ใช้ Gunicorn และรัน container ด้วย non-root user
- เริ่ม container ใหม่อัตโนมัติด้วย `restart: unless-stopped`

## โครงสร้างโปรเจกต์

```text
.
├── app.py                 # Flask API และ Paramiko SSH logic
├── templates/
│   └── index.html         # หน้าเว็บกรอก IP และ command
├── requirements.txt       # Python dependencies
├── Dockerfile             # ขั้นตอนสร้าง container image
├── compose.yaml           # Docker Compose และ health check
├── router.env             # ค่าเชื่อมต่อเราเตอร์สำหรับ Lab
├── .gitignore
└── README.md
```

## ค่าที่ใช้ใน Lab

ค่าการเชื่อมต่อกำหนดใน `router.env`

```dotenv
ROUTER_IP=192.168.40.129
ROUTER_USERNAME=admin
ROUTER_PASSWORD=cisco
SSH_TIMEOUT=10
```

> `router.env` ถูกเก็บใน repository เพื่อส่งงาน Lab เท่านั้น หากนำไปใช้จริงควรเปลี่ยนรหัสผ่านและใช้ Docker secrets หรือ secret manager แทนการ commit credentials ลง Git

## สิ่งที่ต้องมี

- Ubuntu Server หรือ Linux ที่ติดตั้ง Docker แล้ว
- Docker Compose plugin
- Server ต้องเชื่อมต่อ `192.168.40.129:22` ได้
- พอร์ต TCP `8081` ต้องว่างและเข้าถึงได้จากเครื่องผู้ใช้

ตรวจสอบโปรแกรมและพอร์ต:

```bash
docker --version
docker compose version
ss - -ltnp '( sport = :8081 )'
```

หากคำสั่งตรวจพอร์ตไม่แสดงรายการ แปลว่าพอร์ต `8081` ยังว่าง

## วิธีติดตั้งและรัน

```bash
git clone <GIT_REPOSITORY_URL>
cd <PROJECT_DIRECTORY>
docker compose up -d --build
```

ตรวจสอบสถานะ:

```bash
docker compose ps
docker compose logs --tail=50
curl http://127.0.0.1:8081/health
```

ผลลัพธ์ health check ที่ถูกต้อง:

```json
{"status":"ok"}
```

เปิดหน้าเว็บที่:

```text
http://<UBUNTU_SERVER_IP>:8081
```

สำหรับเครื่อง Lab ปัจจุบันคือ `http://192.168.80.131:8081`

ตัวอย่างคำสั่งทดสอบ:

```text
show ip interface brief
show version
show running-config
```

## ทดสอบ API โดยตรง

```bash
curl -X POST http://127.0.0.1:8081/api/execute \
  -H 'Content-Type: application/json' \
  -d '{"ip":"192.168.40.129","command":"show ip interface brief"}'
```

## คำสั่งบริหาร Container

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose up -d --build
docker compose down
```

## ขั้นตอนการทำงาน

1. ผู้ใช้กรอก Router IP และ Cisco CLI command บนหน้าเว็บ
2. JavaScript ส่ง JSON ไปที่ `POST /api/execute`
3. Flask ตรวจสอบ IP, ความยาว command และบรรทัดใหม่
4. Paramiko เชื่อมต่อเราเตอร์ผ่าน SSH ด้วยค่าจาก `router.env`
5. โปรแกรมเปิด interactive shell และส่ง `terminal length 0`
6. โปรแกรมส่ง command และรอรับผลลัพธ์
7. API ส่ง JSON กลับไปแสดงบนหน้าเว็บ

## ผลการทดสอบ

- Container: `router-web`
- Host port: `8081`
- Container health: `healthy`
- Health endpoint: ผ่าน
- SSH จาก Ubuntu Server ไป Router port 22: ผ่าน
- คำสั่ง `show ip interface brief`: ผ่าน
- Router interface `FastEthernet0/0`: `up/up`

## ข้อควรระวัง

หน้าเว็บนี้สามารถส่งคำสั่งไปยังอุปกรณ์เครือข่ายได้ จึงควรใช้เฉพาะใน Lab หรือเครือข่ายที่เชื่อถือได้ ไม่ควรเปิดพอร์ต `8081` สู่อินเทอร์เน็ตโดยตรง หากนำไปใช้งานจริงควรเพิ่ม authentication, HTTPS, command allowlist, audit log และ firewall rule

## Prompt สำหรับสั่ง AI ให้ติดตั้งและรัน

```text
ช่วยติดตั้งและรันโปรเจกต์ Cisco Router Web Console จาก repository นี้บน Ubuntu Server ให้ครบถ้วน โดยทำงานตามลำดับดังนี้:

1. ตรวจสอบว่า Docker และ Docker Compose พร้อมใช้งาน
2. อ่าน README.md, compose.yaml, Dockerfile, app.py และ router.env เพื่อทำความเข้าใจระบบก่อนดำเนินการ
3. ตรวจสอบว่าพอร์ต 8081 ว่าง หากไม่ว่างให้รายงาน process/container ที่ใช้อยู่และเลือกพอร์ตว่างใหม่ โดยแก้ compose.yaml และ URL ที่เกี่ยวข้องให้ตรงกัน
4. ตรวจสอบว่า Ubuntu Server ติดต่อ 192.168.40.129 port 22 ได้
5. รัน docker compose up -d --build
6. รอจน container มีสถานะ healthy และตรวจสอบ log ว่าไม่มี error
7. ทดสอบ GET /health
8. ทดสอบ POST /api/execute ด้วยคำสั่ง show ip interface brief
9. ห้ามหยุดหรือลบบริการ Docker อื่นที่มีอยู่เดิมบน Server
10. เมื่อเสร็จแล้วให้สรุป path โปรเจกต์, URL เข้าใช้งาน, port, container status, ผล health check, ผลทดสอบคำสั่ง Router และคำสั่งสำหรับดู log/restart/stop ระบบ
```
