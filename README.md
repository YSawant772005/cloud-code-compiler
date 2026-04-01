# ☁️ Cloud-Based Python Code Compiler (AWS)

A cloud-native online Python code execution platform built using AWS infrastructure.
Designed to demonstrate secure, scalable, and isolated code execution using modern cloud architecture.

---

## 🚀 Project Overview

This project focuses on **cloud architecture and secure execution**, rather than full-fledged user authentication or multi-language support.

Users can submit Python code through a web interface, which is executed in an isolated environment on AWS.

---

## 🏗️ Architecture

* **Frontend**: Simple web interface (no authentication)
* **Backend**: Flask API hosted on Amazon EC2 (Mumbai region)
* **Queue System**: Redis queue using Amazon ElastiCache
* **Database**: PostgreSQL on Amazon RDS
* **Execution Engine**: Docker containers for isolated execution
* **Storage**: Amazon S3 for logs
* **Monitoring**: Amazon CloudWatch
* **Networking**: Custom VPC with public and private subnets

---

## 🧩 System Architecture (Execution Flow)

The system follows an asynchronous job-processing architecture to ensure scalability and responsiveness.

### 🔄 Flow Overview

1. User submits Python code via frontend
2. Request is sent to Flask API (`/compile`)
3. API validates input and immediately pushes job to Redis queue
4. API returns a `job_id` (non-blocking response)
5. Worker service continuously listens to Redis queue
6. Worker pulls job and creates a fresh Docker container
7. Code executes in isolated environment with strict limits:
   - No internet access
   - CPU & memory constraints
   - Execution timeout
8. Output is captured:
   - Stored in PostgreSQL (RDS)
   - Logs uploaded to S3
9. Docker container is destroyed after execution
10. User fetches result via `/result/<job_id>`

---

## 🔐 Security Features

* Isolated execution using Docker containers
* No network access inside containers
* Resource limits (CPU, memory, timeout)
* Private subnet for database and Redis
* No public access to RDS
* Token-based access (manually generated via console)

---

## 🌐 AWS Architecture Design

* **VPC Setup**

  * Public Subnet → EC2 (Backend + API)
  * Private Subnet → RDS + Redis
* **Security Groups**

  * Restricted DB access (only from backend)
* **IAM Roles**

  * Secure access to S3 and other AWS services

---

## 📌 API Endpoints

| Method | Endpoint         | Description            |
| ------ | ---------------- | ---------------------- |
| POST   | /compile         | Submit Python code     |
| GET    | /result/<job_id> | Fetch execution result |
| GET    | /health          | Health check           |

---

## 🧠 Key Design Decisions

* Focused on **Python-only execution** for simplicity
* Used **Redis queue** for asynchronous processing
* Implemented **Docker isolation** for security
* Designed **cloud-first architecture (AWS VPC + services)**
* Prioritized **system reliability over UI features**

---

## ⚠️ Limitations (Honest Section)

* No user authentication system (no login/register)
* Only supports Python (no multi-language support)
* Token is manually generated (not automated auth)
* Basic frontend (not production UI)

---

## 🔮 Future Improvements

* Add JWT-based authentication system
* Support multiple languages (C++, Java, etc.)
* Replace polling with WebSockets
* Auto-scale workers using AWS Auto Scaling
* Add rate limiting and API gateway
* Improve frontend UI/UX

---

## 🛠️ Setup

1. Clone repository
2. Configure `.env` with AWS endpoints
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:

   ```bash
   flask db upgrade
   ```
5. Start backend:

   ```bash
   gunicorn -w 3 -b 0.0.0.0:5000 run:app
   ```
6. Start worker:

   ```bash
   python worker/worker.py
   ```

---

## ☁️ AWS Services Used

* EC2
* VPC
* RDS (PostgreSQL)
* ElastiCache (Redis)
* S3
* CloudWatch
* IAM

---
<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/22567f8b-7a61-405e-aa4c-321ba8ad3f61" />


## 👨‍💻 Author

Yash Ramesh Sawant
BE CSE (AI & ML), Mumbai University
