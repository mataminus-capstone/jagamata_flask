## 🚀 API Endpoints

### Authentication (`/api/auth`)

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/verify-email/<token>` - Verify email
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password/<token>` - Reset password
- `GET /api/auth/oauth/google` - Google OAuth login (returns OAuth URL)
- `GET /api/auth/oauth/callback` - OAuth callback for web apps (redirect-based)
- `POST /api/auth/oauth/mobile/callback` - OAuth callback for mobile apps (JSON-based)
  - Request: `{ "code": "auth_code_from_google" }`
  - Response: JWT token and user data
- `GET /api/auth/me` - Get current user info (requires JWT token)
- `POST /api/auth/logout` - Logout user

### Chatbot (`/api/chatbot`)
     
- `POST /api/chatbot/` - Send message to chatbot
- `GET /api/chatbot/status` - Get chatbot status

### Articles (`/api/articles`)

- `GET /api/articles/` - Get all articles (public, with pagination)
- `GET /api/article/<id>` - Get article by ID (public)
- `GET /api/dashboard/articles` - Get all articles for admin dashboard (admin only, requires JWT)
- `POST /api/articles/` - Create article (admin only, requires JWT)
- `PUT /api/articles/<id>` - Update article (admin only, requires JWT, must be author or admin)
- `DELETE /api/articles/<id>` - Delete article (admin only, requires JWT, must be author or admin)

### User (`/api/user`)

- `GET /api/user/profile` - Get user profile (requires JWT token)
- `PUT /api/user/profile` - Update user profile (requires JWT token)
