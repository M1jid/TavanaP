**Description**: Delete a specific user-defined query identified by `query_id`.

**Query Parameters**:
- `query_id` (int, required): The ID of the query to delete.

**Permissions**: Requires `delete.user.query` access.

**200 OK – Success Response**

- **Content-Type**: `application/json`  
- **Response Example**:
```json
{
  "detail": "Query deleted successfully",
  "id": 105
}
