**Description**: Retrieve a specific query (by `query_id`) defined by the currently authenticated user.

**Method**: GET  
**Endpoint**: /own  
**Query Parameters**:  
- `query_id` (int): ID of the query to retrieve

**Permissions Required**: read.own.query

**Response**
- **Status Code**: 200 OK
- **Content-Type**: application/json
- **Response Model**: UserQuery

**Example**:
```json
[
  {
    "user_id": 4,
    "query": {
      "must": ["climate"],
      "should": ["change"],
      "must_not": ["denial"]
    },
    "raw_query": [
      {
        "must": ["climate"],
        "should": ["change"],
        "must_not": ["denial"]
      }
    ],
    "id": 29
  }
]
