# dir structure
  ```python
    s&k
    ├───backend
    │   ├───doctor
    │   │   ├───app
    │   │   │   ├───api
    │   │   │   │   └───v1
    │   │   │   │       └───endpoints
    │   │   │   ├───core
    │   │   │   ├───models
    │   │   │   ├───repositories
    │   │   │   ├───schemas
    │   │   │   └───services
    │   │   └───db
    │   └───patient
    │       ├───app
    │       │   ├───api
    │       │   │   └───v1
    │       │   │       └───endpoints
    │       │   ├───core
    │       │   ├───models
    │       │   ├───repositories
    │       │   ├───schemas
    │       │   └───services
    │       └───db
    └───frontend
  ```  

## Doctor password reset

`POST /api/v1/doctors/request-password-reset` accepts an email address and
sends a time-limited reset link when the address belongs to a registered
doctor. The response is the same whether or not an account exists.

Configure the doctor backend environment with:

- `SMTP_HOST`
- `SMTP_PORT` (defaults to `465` with SSL or `587` with STARTTLS)
- `SMTP_USE_SSL` (`true` by default; set `false` for SMTP with STARTTLS)
- `SMTP_FROM` (a sender address authorized by the mail provider)
- `SMTP_USERNAME` and `SMTP_PASSWORD` (both optional, but set them together
  when the provider requires authentication)
- `PASSWORD_RESET_URL` (the frontend password-reset page; must use HTTPS,
  except for localhost development)

Email delivery failures are logged by the backend. Reset links expire after
15 minutes. The frontend should submit the link's `token` and the new password
to `POST /api/v1/doctors/reset-password`.