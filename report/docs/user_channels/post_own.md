**Description**: Create a new query for the authenticated user.

**Method**: POST  
**Endpoint**: /own  
**Authentication**: Required  
**Permissions**: create.own.query

**Request Body**:  
- `raw_query`: List of QueryClause objects (each with `must`, `should`, `must_not` arrays of strings)

**Response**:  
- **Status Code**: 200 OK  
- **Content-Type**: application/json  
- **Response Model**: UserQuery

**Example Request**:
```json
{
  "raw_query": [
    {
      "must": ["news", "technology"],
      "should": ["innovation"],
      "must_not": ["politics"]
    }
  ]
}
