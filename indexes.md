# Database Indexes

## Vector Search Index

| Élément | Valeur |
| --- | --- |
| Collection | Documents |
| Index Name | vector_index |
| Field | embedding |
| Dimensions | 384 |
| Similarity | cosine |

---

## Configuration

```json
{
  "fields": [
    {
      "numDimensions": 384,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
