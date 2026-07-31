# Aggregation Pipeline

## Vector Search

| Élément | Valeur |
| --- | --- |
| Collection | Documents |
| Index | vector_index |
| Vector Field | embedding |
| Number of Candidates | 100 |
| Result Limit | 1 |

---

## Configuration

```json
{
  "index": "vector_index",
  "path": "embedding",
  "numCandidates": 100,
  "limit": 1
}
