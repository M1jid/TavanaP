**Description**: Update an existing query defined by a user using the provided `query_id`. The new `raw_query` and `query` content must be sent in the request body.

**Query Parameters**:
- `query_id` (int, required): The ID of the query to update.

**Request Body Schema**: `UpdateUserQuery`
```json
{
  "raw_query": [
    {
      "must": ["telegram"],
      "should": ["iran"],
      "must_not": []
    }
  ],
  "query": {
    "category": "news"
  }
}
