**Description**: Retrieve all saved user queries with both structured and raw formats.

**200 OK – Success Response**

- **Status Code**: `200 OK`  
- **Content-Type**: `application/json`  
- **Response Schema**: `List[UserQuery]`

**Example Response**:
```json
[
  {
    "user_id": 2,
    "query": {
      "must": ["technology"],
      "should": ["startup"],
      "must_not": ["political"]
    },
    "raw_query": [
      {
        "must": ["technology"],
        "should": ["startup"],
        "must_not": ["political"]
      }
    ],
    "id": 102
  }
]
