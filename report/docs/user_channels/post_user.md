**Description**: Create a new query for a specific user by providing a `user_id` and a structured `raw_query`. The system also stores a parsed `query` representation from the input.

**Query Parameters**:
- `user_id` (int, required): The ID of the user for whom the query is being created.

**Request Body Schema**: `CreateUserQuery`
```json
{
  "raw_query": [
    {
      "must": ["telegram", "channel"],
      "should": ["news"],
      "must_not": ["group"]
    }
  ]
}
