# Security Features & Considerations

## Input Validation & Sanitization

### Request Size Limits
- **Maximum request body size**: 10 MB
- **Status code**: 413 Payload Too Large
- **Purpose**: Prevents denial-of-service (DOS) attacks via oversized payloads
- **Configuration**: `MAX_REQUEST_SIZE` constant in `app/main.py`

### Input Validation
All API request bodies are validated using Pydantic V2:

#### Account Names
- **Length**: 1-255 characters
- **Sanitization**: 
  - Whitespace trimming
  - Control character removal (except newlines and tabs)
  - Empty/whitespace-only names rejected

#### Transaction Amounts
- **Type**: 64-bit signed integer
- **Range**: 1 to 99,999,999,999 (prevents integer overflow)
- **Overflow Protection**: Pydantic validates `le=MAX_TRANSACTION_AMOUNT`
- **Unit**: Smallest unit (e.g., cents for USD)

#### Description Fields
- **Length**: Max 500 characters
- **Sanitization**:
  - Whitespace trimming
  - Control character removal (preserves newlines/tabs)
  - Invalid descriptions converted to `None`

#### Idempotency Keys
- **Length**: Max 255 characters
- **Purpose**: Enable safe retries without duplicate transactions
- **Storage**: Cached in database with full response

### String Sanitization Strategy
**Control characters** (ASCII 0-31, except Tab=9 and Newline=10) are automatically removed from:
- Account names
- Transaction descriptions

This prevents:
- Injection attacks via special characters
- Unicode-based encoding attacks
- Terminal/console manipulation via escape sequences

## Rate Limiting

All sensitive endpoints are rate-limited per IP address using **slowapi**:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /api/v1/mint` | 60 requests | 1 minute |
| `POST /api/v1/transfer` | 60 requests | 1 minute |
| `POST /api/v1/accounts` | 30 requests | 1 minute |
| `GET /api/v1/accounts` | 100 requests | 1 minute |
| `GET /api/v1/transactions` | 100 requests | 1 minute |

**Status code**: 429 Too Many Requests

### Rate Limit Headers
Responses include standard rate limit headers:
```
RateLimit-Limit: 60
RateLimit-Remaining: 55
RateLimit-Reset: 1643276400
```

## Database Security

### Integrity Constraints
- **NOT NULL constraints**: All critical fields required
- **CHECK constraints**: Balance amounts must be >= 0
- **UNIQUE constraints**: Account IDs, Idempotency keys
- **Foreign keys**: Referential integrity for transactions

### Transaction Safety
- **ACID Compliance**: All operations wrapped in database transactions
- **Row-Level Locking**: `SELECT FOR UPDATE` prevents race conditions during transfers
- **Append-Only Ledger**: Transactions never modified or deleted (immutable audit trail)

### No Double-Spending
The system prevents double-spending through:
1. **Atomic transactions**: All-or-nothing updates
2. **Row-level locks**: Exclusive access during balance updates
3. **Constraint checking**: Balance cannot go negative

## API Security Best Practices

### CORS Configuration
- **Default**: `*` (all origins) for development
- **Production**: Specify exact origins in `CORS_ORIGINS` env variable
- **Example**: `CORS_ORIGINS=https://example.com,https://app.example.com`

### Error Handling
- **Generic messages**: Production errors don't leak internal details
- **Debug mode**: Only shows detailed errors when `DEBUG=true`
- **Structured responses**: All errors return consistent JSON format

### Idempotency
- **Safe retries**: Duplicate requests return cached response
- **No side effects**: Same idempotency key always returns identical result
- **Prevent race conditions**: Guarantees exactly-once semantics

## Deployment Recommendations

### Production Checklist
- [ ] Set `DEBUG=false` in environment
- [ ] Configure `CORS_ORIGINS` with specific domains
- [ ] Use PostgreSQL (not SQLite) for multi-process deployments
- [ ] Enable HTTPS/TLS for all API endpoints
- [ ] Use reverse proxy (nginx, Cloudflare) for additional DDoS protection
- [ ] Monitor rate limit usage via logging
- [ ] Implement request logging with correlation IDs
- [ ] Set up alerts for unusual transaction patterns
- [ ] Regular database backups with point-in-time recovery
- [ ] Use connection pooling (min_size, max_size, pool_recycle)

### Environment Variables
Never commit `.env` files to version control. Use `.env.example` as template:
```bash
cp .env.example .env
# Edit .env with production values
```

## Known Limitations & Future Improvements

### Current Version (v1.0.0)
- Rate limits are per-IP (no per-account limits)
- No API authentication/authorization
- No request signing or mutual TLS
- Single-instance deployment (in-memory limiter)

### Recommended Future Enhancements
1. **API Key Authentication**: Validate requests with API keys
2. **Request Signing**: HMAC-SHA256 request signatures
3. **Distributed Rate Limiting**: Redis-backed limiter for multi-instance
4. **Audit Logging**: Structured JSON logs with request context
5. **Per-Account Rate Limits**: Limit by API key, not just IP
6. **WAF Integration**: Cloudflare, AWS WAF, or similar
7. **Database Encryption**: Encrypt sensitive fields at rest
8. **Field-Level Encryption**: Encrypt account names, descriptions

## Reporting Security Issues

Please do not report security vulnerabilities in public issues. Instead:
1. Document the vulnerability clearly
2. Include reproduction steps
3. Email details to security contact (if available)
4. Allow time for patch before disclosure

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [slowapi Rate Limiting](https://github.com/laurents/slowapi)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.text)
