**Description**: Update a specific query previously defined by the authenticated user, identified by `query_id`.

**Method**: PUT  
**Endpoint**: /own  
**Authentication**: Required  
**Permissions**: update.own.query

**Query Parameters**:  
- `query_id` (int): ID of the query to update

**Request Body**:  
- `raw_query`: List of QueryClause objects  
- `query`: Dict (optional additional query info)

**Response**:  
- **Status Code**: 200 OK  
- **Content-Type**: application/json  
- **Response Model**: UserQuery

**Errors**:  
- 400 Bad Request if the query does not belong to the current user or if access denied

**Example Request**:
```json
{
  "raw_query": [
    {
      "must": ["update", "example"],
      "should": ["test"],
      "must_not": ["exclude"]
    }
  ],
  "query": {
    "extra": "data"
  }
}
