## 🚀 API Endpoints

### Authentication (`/api/auth`)

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/verify-email/<token>` - Verify email
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password/<token>` - Reset password
- `GET /api/auth/oauth/google` - Google OAuth login
- `GET /api/auth/oauth/callback` - OAuth callback
- `POST /api/auth/logout` - Logout user

### Chatbot (`/api/chatbot`)
     
- `POST /api/chatbot/` - Send message to chatbot
- `GET /api/chatbot/status` - Get chatbot status

### Articles (`/api/articles`)

- `GET /api/articles/` - Get all articles (with pagination)
- `GET /api/articles/<id>` - Get article by ID
- `POST /api/articles/` - Create article (admin only)
- `PUT /api/articles/<id>` - Update article (admin only)
- `DELETE /api/articles/<id>` - Delete article (admin only)