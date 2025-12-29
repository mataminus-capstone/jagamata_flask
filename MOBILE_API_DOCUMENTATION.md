# Jagamata Backend API - Mobile Integration Guide

Dokumentasi lengkap untuk integrasi Android/iOS client dengan backend API Jagamata. Panduan ini mencakup semua endpoint yang dibutuhkan untuk implementasi user-only (tanpa admin features).

## Daftar Isi
1. [Setup & Konfigurasi](#setup--konfigurasi)
2. [Authentication Flow](#authentication-flow)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Testing di Postman](#testing-di-postman)

---

## Setup & Konfigurasi

### Base URL
```
Production: https://jagamata.leapcell.app
Development: http://localhost:8080
```

### Headers (untuk semua authenticated requests)
```
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
```

### Environment Variables yang Diperlukan
```
GOOGLE_MOBILE_CLIENT_ID=<your_google_client_id>
DATABASE_URL=<your_database_url>
JWT_SECRET=<your_jwt_secret>
```

---

## Authentication Flow

### 1. OAuth Google untuk Mobile

OAuth Google untuk aplikasi native tidak memerlukan client secret. Flow berikut adalah yang benar:

#### Step 1: Dapatkan Authorization Code dari Google

Gunakan Google Sign-In SDK di mobile app:
- **Android**: `com.google.android.gms:play-services-auth`

Google akan return authorization code.

#### Step 2: Exchange Authorization Code dengan Backend

Kirim authorization code ke backend untuk mendapatkan JWT token.

**Endpoint:**
```
POST /api/auth/oauth/mobile/callback
```

**Request Body:**
```json
{
  "code": "4/0AX4XfWj..."
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Login berhasil! Selamat datang username_anda",
  "data": {
    "user_id": 1,
    "username": "email_prefix",
    "email": "user@example.com",
    "role": "user",
    "email_verified": true,
    "oauth_provider": "google",
    "created_at": "2025-01-15T10:30:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response Error (400/500):**
```json
{
  "success": false,
  "message": "Gagal memproses OAuth atau error lainnya"
}
```

**Penjelasan:**
- `code`: Authorization code dari Google OAuth
- Token di response adalah JWT yang berlaku selamanya (atau sampai diset expiry)
- Email otomatis terverifikasi untuk OAuth users
- Jika email sudah terdaftar, account akan di-link dengan OAuth
- Username otomatis generated dari email prefix jika user baru

---

### 2. Register dengan Email & Password

**⚠️ UPDATED: Username tidak lagi harus unique!**

**Endpoint:**
```
POST /api/auth/register
```

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Registrasi berhasil! Silakan cek email untuk verifikasi.",
  "data": {
    "user_id": 2,
    "username": "john_doe",
    "email": "john@example.com",
    "email_verified": false
  }
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "Email sudah terdaftar!" // atau error validation lainnya
}
```

**Validasi:**
- Username: required, **dapat duplikat** (semua orang bisa punya username yang sama)
- Email: required, **unique**, valid format
- Password: minimum 6 character

**Flow:**
1. User menerima email verifikasi
2. Klik link untuk verify email
3. Setelah verified, baru bisa login

---

### 3. Login dengan Email & Password

**⚠️ UPDATED: Login menggunakan EMAIL, bukan USERNAME!**

**Endpoint:**
```
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Login berhasil! Selamat datang john_doe",
  "data": {
    "user_id": 2,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-01-15T10:30:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response Error (401):**
```json
{
  "success": false,
  "message": "Email atau password salah!"
}
```

**Response Error (403) - Email belum verified:**
```json
{
  "success": false,
  "message": "Email belum diverifikasi. Silakan cek email Anda untuk link verifikasi.",
  "data": {
    "user_id": 2,
    "email": "john@example.com",
    "needs_verification": true
  }
}
```

---

### 4. Verify Email

**Endpoint:**
```
GET /api/auth/verify-email/<token>
```

**Parameters:**
- `token`: Token dari email verification link

**Response Success (200):**
```json
{
  "success": true,
  "message": "Email berhasil diverifikasi!",
  "data": {
    "user_id": 2,
    "username": "john_doe",
    "email_verified": true
  }
}
```

**Catatan:** 
- Token dikirim via email setelah register
- User bisa open link di mobile app atau browser
- Setelah verified, user bisa login

---

### 5. Forgot Password

**Endpoint:**
```
POST /api/auth/forgot-password
```

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200) - Always success (for security):**
```json
{
  "success": true,
  "message": "Jika email terdaftar, link reset password telah dikirim."
}
```

**Catatan:**
- Response selalu success, bahkan jika email tidak terdaftar (security measure)
- Email berisi link untuk reset password
- Link valid selama 1 jam
- OAuth users tidak bisa reset password via endpoint ini

---

### 6. Reset Password

**Endpoint:**
```
POST /api/auth/reset-password/<token>
```

**Parameters:**
- `token`: Token dari password reset email

**Request Body:**
```json
{
  "password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Password berhasil direset! Silakan login."
}
```

**Response Error (400):**
```json
{
  "success": false,
  "message": "Token reset tidak valid atau sudah kadaluarsa!"
}
```

**Validasi:**
- Password minimum 6 character
- Password dan confirm_password harus sama
- Token harus valid dan belum expired (1 jam)

---

### 7. Get Current User Info

Gunakan endpoint ini untuk get data user yang sedang login.

**Endpoint:**
```
GET /api/auth/me
```

**Headers (Required):**
```
Authorization: Bearer <JWT_TOKEN>
```

**Response Success (200):**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-01-15T10:30:00"
  }
}
```

**Response Error (401) - Token invalid/expired:**
```json
{
  "success": false,
  "message": "Token tidak valid atau sudah kadaluarsa."
}
```

---

### 8. Logout

**Endpoint:**
```
POST /api/auth/logout
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logout berhasil!"
}
```

**Catatan:**
- API adalah stateless, cukup hapus JWT token dari client
- Server tidak menyimpan session
- Token tetap valid di server sampai expired (jangan dikhawatirkan)

---

## API Endpoints

### User Endpoints

#### Get User Profile

**Endpoint:**
```
GET /api/auth/me
```

**Headers (Required):**
```
Authorization: Bearer <JWT_TOKEN>
```

**Response Success (200):**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-01-15T10:30:00"
  }
}
```

---

### Article Endpoints

#### Get All Articles (Public)

Endpoint publik untuk get daftar artikel dengan pagination.

**Endpoint:**
```
GET /api/articles?page=1&per_page=10
```

**Query Parameters (Optional):**
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| page | int | 1 | - | Page number |
| per_page | int | 10 | 100 | Items per page |

**Response Success (200):**
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": 1,
        "title": "Cara Menjaga Kesehatan",
        "content": "Lorem ipsum dolor sit amet...",
        "author": {
          "id": 1,
          "username": "doctor_admin"
        },
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T11:00:00"
      },
      {
        "id": 2,
        "title": "Tips Olahraga Teratur",
        "content": "Lorem ipsum dolor sit amet...",
        "author": {
          "id": 1,
          "username": "doctor_admin"
        },
        "created_at": "2025-01-14T09:15:00",
        "updated_at": null
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 25,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

**Response Error (500):**
```json
{
  "success": false,
  "message": "Terjadi kesalahan saat mengambil artikel."
}
```

**Catatan:**
- Endpoint ini public, tidak perlu authentication
- Articles diurutkan dari terbaru ke terlama
- Pagination info berguna untuk infinite scroll atau pagination UI

---

#### Get Article Detail

Get artikel spesifik berdasarkan ID.

**Endpoint:**
```
GET /api/articles/<article_id>
```

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| article_id | int | ID artikel |

**Response Success (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Cara Menjaga Kesehatan",
    "content": "Lorem ipsum dolor sit amet consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua...",
    "author": {
      "id": 1,
      "username": "doctor_admin"
    },
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T11:00:00"
  }
}
```

**Response Error (404):**
```json
{
  "success": false,
  "message": "Artikel tidak ditemukan."
}
```

---

### Chatbot Endpoints

#### Send Message to Chatbot

Kirim pesan ke chatbot untuk mendapatkan respons. Chatbot menggunakan AI model untuk memberikan respons yang relevan.

**Endpoint:**
```
POST /api/chatbot
```

**Request Body:**
```json
{
  "message": "Saya sakit kepala, apa yang harus saya lakukan?"
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Berhasil mendapatkan respons.",
  "data": {
    "response": "Sakit kepala bisa disebabkan oleh berbagai faktor. Coba istirahat yang cukup, minum air putih, dan hindari stress. Jika berlanjut, konsultasikan dengan dokter.",
    "doctor": "Dr. AI Assistant",
    "confidence": 0.95
  }
}
```

**Response Error (400) - Empty message:**
```json
{
  "success": false,
  "message": "Pesan tidak boleh kosong.",
  "data": {
    "response": "Pesan tidak boleh kosong.",
    "doctor": "System",
    "confidence": 0
  }
}
```

**Catatan:**
- Endpoint ini public, tidak perlu authentication
- Confidence score menunjukkan seberapa yakin model dengan respons (0-1)
- Doctor field menunjukkan specialist yang memberikan respons
- Response bisa berupa saran umum atau rekomendasi konsultasi

---

#### Get Chatbot Status

Check apakah chatbot siap digunakan.

**Endpoint:**
```
GET /api/chatbot/status
```

**Response Success (200):**
```json
{
  "success": true,
  "data": {
    "status": "ready",
    "message": "Chatbot siap digunakan",
    "model_loaded": true,
    "gemini_configured": true
  }
}
```

**Response Error (200) - Model not loaded:**
```json
{
  "success": true,
  "data": {
    "status": "not_loaded",
    "message": "Model belum dimuat",
    "model_loaded": false,
    "gemini_configured": false
  }
}
```

**Catatan:**
- Gunakan endpoint ini untuk check chatbot availability sebelum send message
- `model_loaded`: Apakah model ML sudah dimuat di memory
- `gemini_configured`: Apakah Gemini API sudah dikonfigurasi

---

## Data Models

### User Model

```json
{
  "id": "int",
  "username": "string (CAN BE DUPLICATE - semua orang bisa punya username yang sama)",
  "email": "string (UNIQUE - harus unik)",
  "password_hash": "string (bcrypt hash, nullable untuk OAuth users)",
  "role": "enum (user, moderator, admin)",
  "created_at": "ISO 8601 datetime",
  "oauth_provider": "string (google, null jika manual register)",
  "oauth_id": "string (Google user ID, nullable)",
  "email_verified": "boolean",
  "verification_token": "string (nullable)",
  "reset_token": "string (nullable)",
  "reset_token_expiry": "datetime (nullable)"
}
```

**Contoh User Object:**
```json
{
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "email_verified": true,
  "oauth_provider": null,
  "created_at": "2025-01-15T10:30:00"
}
```

---

### Article Model

```json
{
  "id": "int",
  "title": "string",
  "content": "text (long content)",
  "author_id": "int (foreign key to User)",
  "created_at": "ISO 8601 datetime",
  "updated_at": "ISO 8601 datetime"
}
```

**Contoh Article Object:**
```json
{
  "id": 1,
  "title": "Cara Menjaga Kesehatan",
  "content": "Lorem ipsum dolor sit amet consectetur...",
  "author": {
    "id": 1,
    "username": "doctor_admin"
  },
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T11:00:00"
}
```

---

### Chatbot Message Model

```json
{
  "message": "string (user message)",
  "response": "string (chatbot response)",
  "doctor": "string (specialist name/type)",
  "confidence": "float (0-1, confidence score)"
}
```

**Contoh Chatbot Response:**
```json
{
  "message": "Saya sakit kepala",
  "response": "Sakit kepala bisa disebabkan oleh...",
  "doctor": "Dr. AI Assistant",
  "confidence": 0.92
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Condition |
|------|---------|-----------|
| 200 | OK | Request berhasil |
| 201 | Created | Resource berhasil dibuat |
| 400 | Bad Request | Input validation error |
| 401 | Unauthorized | Token missing atau invalid |
| 403 | Forbidden | User tidak punya akses |
| 404 | Not Found | Resource tidak ditemukan |
| 500 | Server Error | Internal server error |

---

### Error Response Format

Semua error response mengikuti format ini:

```json
{
  "success": false,
  "message": "Deskripsi error dalam bahasa Indonesia"
}
```

**Contoh:**
```json
{
  "success": false,
  "message": "Token tidak valid atau sudah kadaluarsa."
}
```

---

### Common Error Scenarios

#### 1. Token Tidak Ada (401)
```json
{
  "success": false,
  "message": "Token tidak ditemukan. Gunakan header Authorization: Bearer <token>"
}
```
**Solusi:** Pastikan JWT token ada di header Authorization

#### 2. Token Expired (401)
```json
{
  "success": false,
  "message": "Token tidak valid atau sudah kadaluarsa."
}
```
**Solusi:** Refresh token atau ask user login ulang

#### 3. Invalid JSON (400)
```json
{
  "success": false,
  "message": "Invalid JSON format"
}
```
**Solusi:** Pastikan request body adalah valid JSON dengan Content-Type: application/json

#### 4. Validation Error (400)
```json
{
  "success": false,
  "message": "Email dan password harus diisi!"
}
```
**Solusi:** Lihat validasi requirements di dokumentasi endpoint

#### 5. Token Tidak Ditemukan (401) - UPDATED
```json
{
  "success": false,
  "message": "Token tidak ditemukan. Silakan login kembali!"
}
```
**Solusi:** Pastikan JWT token tersimpan di localStorage setelah login dan dikirim di header Authorization

#### 6. Unauthorized Access (403)
```json
{
  "success": false,
  "message": "Anda tidak punya akses untuk edit artikel ini!"
}
```
**Solusi:** Pastikan user punya role/permission yang tepat

#### 7. Resource Not Found (404)
```json
{
  "success": false,
  "message": "Artikel tidak ditemukan."
}
```
**Solusi:** Pastikan ID resource yang diakses valid

---

### Error Handling Best Practices

Untuk production app:

```java
// Android Example
try {
    Response response = client.newCall(request).execute();
    
    if (response.isSuccessful()) {
        String body = response.body().string();
        // Handle 200-299
    } else {
        // Handle 400-599
        switch (response.code()) {
            case 401:
                // Token invalid/not found, ask user to login
                navigateToLogin();
                clearStoredToken();
                break;
            case 403:
                // Forbidden, show error message
                showToast("Anda tidak punya akses");
                break;
            case 404:
                // Not found
                showToast("Resource tidak ditemukan");
                break;
            case 500:
                // Server error
                showToast("Server error, coba lagi nanti");
                break;
        }
    }
} catch (IOException e) {
    // Network error
    showToast("Network error");
}
```

```swift
// iOS Example
URLSession.shared.dataTask(with: request) { data, response, error in
    guard let httpResponse = response as? HTTPURLResponse else {
        print("Network error")
        return
    }
    
    if (200...299).contains(httpResponse.statusCode) {
        // Handle success
    } else if httpResponse.statusCode == 401 {
        // Token invalid/not found, navigate to login
        clearStoredToken()
        navigateToLogin()
    } else if httpResponse.statusCode == 403 {
        // Show forbidden message
    } else {
        // Handle other errors
    }
}.resume()
```

---

## Testing di Postman

### Setup Postman Environment

1. **Create New Environment:**
   - Click "Environments" → "Create"
   - Name: `Jagamata API`
   - Add variables:
     ```
     base_url: https://jagamata.leapcell.app
     token: (akan diisi setelah login)
     ```

2. **Create Base Variables:**
   ```
   {{base_url}} = https://jagamata.leapcell.app (production)
   {{base_url}} = http://localhost:5000 (development)
   {{token}} = (JWT token dari login response)
   ```

---

### Test Collections

#### 1. Authentication Flow

**1.1 Register User**
```
Method: POST
URL: {{base_url}}/api/auth/register
Headers:
  Content-Type: application/json

Body (raw):
{
  "username": "testuser123",
  "email": "test@example.com",
  "password": "Password123"
}
```

**Expected Response (201):**
```json
{
  "success": true,
  "message": "Registrasi berhasil! Silakan cek email untuk verifikasi.",
  "data": {
    "user_id": 1,
    "username": "testuser123",
    "email": "test@example.com",
    "email_verified": false
  }
}
```

---

**1.2 Login User - UPDATED (Email-based)**
```
Method: POST
URL: {{base_url}}/api/auth/login
Headers:
  Content-Type: application/json

Body (raw):
{
  "email": "test@example.com",
  "password": "Password123"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Login berhasil! Selamat datang testuser123",
  "data": {
    "user_id": 1,
    "username": "testuser123",
    "email": "test@example.com",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-01-15T10:30:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Save token ke environment:**
- Response → "token" → copy value
- Environments → Jagamata API → token → paste value
- Token akan otomatis tersimpan di localStorage di frontend

---

**1.3 OAuth Mobile**
```
Method: POST
URL: {{base_url}}/api/auth/oauth/mobile/callback
Headers:
  Content-Type: application/json

Body (raw):
{
  "code": "4/0AX4XfWj..." // Google authorization code
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Login berhasil! Selamat datang email_prefix",
  "data": {
    "user_id": 2,
    "username": "email_prefix",
    "email": "user@gmail.com",
    "role": "user",
    "email_verified": true,
    "oauth_provider": "google",
    "created_at": "2025-01-15T10:30:00",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

**1.4 Get Current User**
```
Method: GET
URL: {{base_url}}/api/auth/me
Headers:
  Authorization: Bearer {{token}}
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "testuser123",
    "email": "test@example.com",
    "role": "user",
    "email_verified": true,
    "created_at": "2025-01-15T10:30:00"
  }
}
```

---

#### 2. Articles

**2.1 Get All Articles**
```
Method: GET
URL: {{base_url}}/api/articles?page=1&per_page=10
Headers:
  Content-Type: application/json
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "articles": [...],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 5,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

**2.2 Get Article Detail**
```
Method: GET
URL: {{base_url}}/api/articles/1
Headers:
  Content-Type: application/json
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Cara Menjaga Kesehatan",
    "content": "Lorem ipsum...",
    "author": {
      "id": 1,
      "username": "doctor_admin"
    },
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T11:00:00"
  }
}
```

---

#### 3. Chatbot

**3.1 Send Message to Chatbot**
```
Method: POST
URL: {{base_url}}/api/chatbot
Headers:
  Content-Type: application/json

Body (raw):
{
  "message": "Saya sakit kepala"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Berhasil mendapatkan respons.",
  "data": {
    "response": "Sakit kepala bisa disebabkan oleh...",
    "doctor": "Dr. AI Assistant",
    "confidence": 0.92
  }
}
```

---

**3.2 Get Chatbot Status**
```
Method: GET
URL: {{base_url}}/api/chatbot/status
Headers:
  Content-Type: application/json
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "ready",
    "message": "Chatbot siap digunakan",
    "model_loaded": true,
    "gemini_configured": true
  }
}
```

---

## Troubleshooting

### Masalah Umum

#### 1. Token Tidak Ditemukan saat Create Article
**Penyebab:** Token tidak tersimpan di localStorage atau tidak dikirim di header Authorization
**Solusi:** 
- Pastikan login berhasil dan token tersimpan di localStorage
- Cek browser DevTools → Application → LocalStorage → key "jwt_token"
- Pastikan artikel creation request mengirim token di header Authorization: Bearer {token}

#### 2. Login Error "Email atau password salah"
**Penyebab:** Email atau password yang dimasukkan tidak sesuai
**Solusi:**
- Pastikan menggunakan EMAIL, bukan USERNAME
- Default email untuk testing: `admin@example.com` atau `user@example.com`
- Default password: `admin123` atau `user123`

#### 3. Email belum Diverifikasi
**Penyebab:** User belum mengklik link verifikasi di email
**Solusi:**
- Cek email inbox atau spam folder
- Klik link verifikasi
- Atau untuk development, bisa langsung set `email_verified = true` di database

#### 4. Token Sudah Expired
**Penyebab:** JWT token sudah kadaluarsa
**Solusi:**
- Login kembali untuk mendapatkan token baru
- Untuk development, adjust JWT expiry time di config

---

## Changelog - Terbaru (Versi 2.0)

### Changes:
- ✅ **Login Email-Based**: Ganti dari username menjadi email
- ✅ **Username Non-Unique**: Username bisa duplikat, hanya email yang harus unik
- ✅ **Token Management**: Perbaikan token handling di article creation
- ✅ **Base URL**: Ditambahkan production URL `https://jagamata.leapcell.app`
- ✅ **Error Handling**: Pesan error lebih jelas dan informatif
- ✅ **Database Schema**: Updated di setup.py dengan migration baru

### Migration Notes:
Jika mengupdate dari versi lama:
1. Run `python setup.py` untuk update database schema
2. Update client login logic untuk menggunakan email bukan username
3. Update token storage dan retrieval dari localStorage
4. Test semua authentication flow di Postman
