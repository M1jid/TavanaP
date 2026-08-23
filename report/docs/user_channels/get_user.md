**Description**: Retrieve user query data by either `user_id` or `query_id`. Returns queries created by users, including both parsed (`query`) and raw structured (`raw_query`) representations. At least one of the query parameters (`user_id` or `query_id`) must be provided.

**Query Parameters**:
- `user_id` (int, optional): Return all queries created by this user.
- `query_id` (int, optional): Return a specific query by its ID.

**Permissions**: Requires `read.user.query` access.

**200 OK – Success Response**

- **Content-Type**: `application/json`  
- **Response Schema**: `List[UserQuery]`

**Example Response**:
```json
[
  {
    "user_id": 1,
    "query": {
      "must": ["telegram", "channel"],
      "should": ["news"],
      "must_not": ["group"]
    },
    "raw_query": [
      {
        "must": ["telegram", "channel"],
        "should": ["news"],
        "must_not": ["group"]
      }
    ],
    "id": 101
  }
]
