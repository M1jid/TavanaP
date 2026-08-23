**Description**: Retrieve all queries defined by the currently authenticated user.

**Method**: GET  
**Endpoint**: /own/all  
**Permissions Required**: read.own.query

**Response**
- **Status Code**: 200 OK
- **Content-Type**: application/json
- **Response Model**: List[UserQuery]

**Example**:
```json
[
  {
    "user_id": 4,
    "query": {
      "must": ["economy"],
      "should": ["news"],
      "must_not": ["spam"]
    },
    "raw_query": [
      {
        "must": ["economy"],
        "should": ["news"],
        "must_not": ["spam"]
      }
    ],
    "id": 17
  }
]
