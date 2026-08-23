# Authentication API - Token Endpoint

## `POST /token`

Generates a JWT access token for authenticated users.

### Request

**URL**: `/api/v2/token`  
**Method**: `POST`  
**Content-Type**: `application/x-www-form-urlencoded`

#### Form Data
| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| username  | string | Yes      | User's login name    |
| password  | string | Yes      | User's password      |
| grant_type| string | No       | Should be "password" |

### Response

**Success Response**  
**Status Code**: `200 OK`  
**Content-Type**: `application/json`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}