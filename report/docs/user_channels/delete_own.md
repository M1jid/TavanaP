**Description**: Delete a specific query previously defined by the authenticated user, identified by `query_id`.

**Method**: DELETE  
**Endpoint**: /own  
**Authentication**: Required  
**Permissions**: delete.own.query

**Query Parameters**:  
- `query_id` (int): ID of the query to delete

**Response**:  
- **Status Code**: 200 OK (or relevant status on success)  
- **Content-Type**: application/json  
- **Response**: Confirmation of deletion or deleted object info

**Errors**:  
- 400 Bad Request if the query does not belong to the current user or access is denied  
- Appropriate error if query not found

**Example Request**:  
`DELETE /own?query_id=15`

**Example Response**:
```json
{
  "detail": "Query deleted successfully."
}
