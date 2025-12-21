# OpenSearch API Explanations

This document provides a 1-to-1 mapping of every API call in `text_search.sh` to a detailed explanation.

## 1. Mapping and Basic Search

### 1. Retrieve Mapping
```bash
GET ecommerce/_mapping
```
**Explanation:**
Retrieves the schema definition (mapping) for the `ecommerce` index. This shows fields, data types (text, keyword, integer, etc.), and analyzer settings.

### 2. Default Search
```bash
POST ecommerce/_search
```
**Explanation:**
Executes a search against the `ecommerce` index. Without a body, it defaults to a `match_all` query and returns the first 10 documents sorted by relevance score (which will be 1.0 for all).

### 3. Explicit Match All
```bash
GET /ecommerce/_search
{
  "query": {
    "match_all": {}
  }
}
```
**Explanation:**
Explicitly defines a `match_all` query. This is useful when you want to retrieve all documents (paginated) without any filtering or scoring bias.

### 4. Field Collapsing
```bash
GET ecommerce/_search
{
    "query": {
        "match": {
            "category.keyword": "Men's Shoes"
        }
    },
    "collapse": {
        "field": "type"
    },
    "sort": ["day_of_week"]
}
```
**Explanation:**
Groups results by the `type` field. Only the top document (based on the `sort` order of `day_of_week`) for each unique `type` is returned. Useful for "distinct" style queries.

## 2. Pagination

### 5. Basic Pagination (From/Size)
```bash
GET ecommerce/_search
{
  "from": 0,
  "size": 10,
  "query": {
    "match": {
      "manufacturer": "Elitelligence"
    }
  }
}
```
**Explanation:**
Retrieves results starting from index 0 (`from`) and returns 10 documents (`size`). This is standard pagination.

### 6. URI Pagination
```bash
GET ecommerce/_search?from=0&size=10
```
**Explanation:**
Same as above, but parameters are passed in the URL query string instead of the request body.

### 7. Scroll Initialization
```bash
GET ecommerce/_search?scroll=10m
{
  "size": 5
}
```
**Explanation:**
Initializes a "scroll" context valid for 10 minutes (`10m`). This snapshots the index state. Returns the first batch of 5 results and a `_scroll_id`.

### 8. Scroll Retrieval
```bash
GET _search/scroll
{
  "scroll": "10m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAAUWdmpUZDhnRFBUcWFtV21nMmFwUGJEQQ=="
}
```
**Explanation:**
Uses the `scroll_id` from the previous response to fetch the next batch of results. The `scroll` parameter refreshes the context timer.

### 9. Search After (Initialization)
```bash
GET ecommerce/_search
{
  "size": 3,
  "query": {
    "match": {
      "manufacturer": "Elitelligence"
    }
  },
  "sort": [
    { "products.category.keyword": "asc" },
    { "_id": "asc" } 
  ]
}
```
**Explanation:**
The first step in "Search After" pagination. You must define a deterministic sort order (including `_id` is best practice). Returns the first page and "sort values" for each document.

### 10. Search After (Next Page)
```bash
GET ecommerce/_search
{
  "size": 10,
  "query": {
    "match": {
      "manufacturer": "Elitelligence"
    }
  },
  "search_after": [ "Men's Accessories", "1047"],
  "sort": [
    { "products.category.keyword": "asc" },
    { "_id": "asc" } 
  ]
}
```
**Explanation:**
Fetches the next page. `search_after` takes the sort values of the *last* document from the previous response.

### 11. Point In Time (PIT) Initialization
```bash
POST /ecommerce/_search/point_in_time?keep_alive=100m
```
**Explanation:**
Creates a lightweight, consistent view of the index (PIT) that persists for 100 minutes. Returns a `pit_id`.

### 12. Search with PIT
```bash
GET _search
{
  "size": 10,
  "query": {
    "match": {
      "manufacturer": "Elitelligence"
    }
  },
  "search_after": [ "Men's Accessories", "1047"],
  "sort": [
    { "products.category.keyword": "asc" },
    { "_id": "asc" } 
  ],
  "pit": {
    "id":  "87mEQQEJZWNvbW1lcmNlFmVWMTdBdE9TU1hTS29pa1lXVmxQb2cAFi1sV1huazZoVHcybzd1MkxnMHlqZWcAAAAAAAAAADUWQXFpajZzWERSRzZxRlhnekZrc1RCUQEWZVYxN0F0T1NTWFNLb2lrWVdWbFBvZwAA", 
    "keep_alive": "100m"
  }
}
```
**Explanation:**
Performs a search using the PIT ID. This ensures pagination consistency even if the index changes during user navigation.

### 13. Search After (Alternative Example)
```bash
GET ecommerce/_search
{
  "size": 10,
  "query": {
    "match": {
      "manufacturer": "Elitelligence"
    }
  },
  "sort": [
    { "products.category.keyword": "asc" },
    { "_id": "asc" } 
  ],
    "search_after": [ "Men's Accessories", "1047"]
}
```
**Explanation:**
Another example of fetching the next page using `search_after` values.

## 3. Sorting and Highlighting

### 14. Sort Descending
```bash
GET ecommerce/_search
{
   "query" : {
      "match_all": {}
   },
   "sort" : [
      {"manufacturer.keyword": {"order" : "desc"}}
   ]
}
```
**Explanation:**
Sorts all documents by `manufacturer.keyword` in descending alphabetical order.

### 15. Default Highlighting
```bash
GET ecommerce/_search
{
  "query": {
    "match": {
      "products.product_name": "blue"
    }
  },
  "size": 3,
  "highlight": {
    "fields": {
      "products.product_name": {}
    }
  }
}
```
**Explanation:**
Highlights the term "blue" in the `products.product_name` field. Returns a `highlight` field in the response with `<em>blue</em>`.

### 16. Custom Highlighting
```bash
GET ecommerce/_search
{
  "query": {
    "match": {
      "products.product_name": "blue"
    }
  },
  "size": 3,
  "highlight": {
    "pre_tags": [
      "<strong>"
    ],
    "post_tags": [
      "</strong>"
    ],
    "fields": {
      "products.product_name": {}
    }
  }
}
```
**Explanation:**
Same as above, but wraps the highlighted term in `<strong>` tags instead of the default `<em>`.

## 4. Autocomplete and Suggesters

### 17. Delete Index
```bash
DELETE ecommerce
```
**Explanation:**
Deletes the `ecommerce` index to prepare for a new mapping configuration.

### 18. Analyze (Autocomplete)
```bash
POST ecommerce/_analyze
{
  "analyzer": "autocomplete",
  "text": "summer"
}
```
**Explanation:**
Tests the `autocomplete` analyzer (assumed to be defined in the index settings) to see how it tokenizes "summer" (likely into edge n-grams like "s", "su", "sum", "summ", "summe", "summer").

### 19. Search with Autocomplete Analyzer
```bash
GET ecommerce/_search
{
  "query": {
    "match": {
      "products.product_name": {
        "query": "sum",
        "analyzer": "autocomplete"
      }
    }
  }
}
```
**Explanation:**
Searches using the `autocomplete` analyzer on the query string "sum". This might produce too many tokens if not careful.

### 20. Search with Standard Analyzer
```bash
GET ecommerce/_search
{
  "query": {
    "match": {
      "products.product_name": {
        "query": "sum",
        "analyzer": "standard"
      }
    }
  }
}
```
**Explanation:**
Searches for "sum" using the `standard` analyzer against the field (which is indexed with edge n-grams). This is the correct way to match a prefix "sum" against indexed tokens like "s", "su", "sum".

### 21. Delete Index
```bash
DELETE ecommerce
```
**Explanation:**
Cleans up the index again.

### 22. Create Index (Completion Type)
```bash
PUT ecommerce
{
  "mappings": {
    "properties": {
      "products.product_name": {
        "type": "completion"
      }
    }
  }
}
```
**Explanation:**
Creates the index with `products.product_name` mapped as a `completion` type, which is optimized for fast prefix suggestions.

### 23. Completion Suggester
```bash
GET ecommerce/_search
{
  "suggest": {
    "autocomplete": {
      "prefix": "summer",
      "completion": {
        "field": "products.product_name",
        "size": 3
      }
    }
  }
}
```
**Explanation:**
Requests suggestions for the prefix "summer" from the `products.product_name` field.

### 24. Completion Suggester (Fuzzy)
```bash
GET ecommerce/_search
{
  "suggest": {
    "autocomplete": {
      "prefix": "smmer",
      "completion": {
        "field": "products.product_name",
        "size": 3,
        "fuzzy": {
          "fuzziness": "AUTO"
        }
      }
    }
  }
}
```
**Explanation:**
Requests suggestions for "smmer" (misspelled) using fuzzy matching to find "summer".

### 25. Completion Suggester (Regex)
```bash
GET ecommerce/_search
{
  "suggest": {
    "autocomplete": {
      "prefix": "sum*",
      "completion": {
        "field": "products.product_name",
        "size": 3,
        "fuzzy": {
          "fuzziness": "AUTO"
        }
      }
    }
  }
}
```
**Explanation:**
Uses a regex pattern `sum*` to find suggestions.

### 26. Delete Index
```bash
DELETE ecommerce
```
**Explanation:**
Cleans up.

### 27. Create Index (Search As You Type)
```bash
PUT ecommerce
{
  "mappings": {
    "properties": {
      "products.product_name": {
        "type": "search_as_you_type"
      }
    }
  }
}
```
**Explanation:**
Creates index with `search_as_you_type` field, which automatically creates sub-fields for n-grams and shingles.

### 28. Bool Prefix Query
```bash
GET ecommerce/_search
{
  "query": {
    "multi_match": {
      "query": "shirt black",
      "type": "bool_prefix",
      "fields": [
        "products.product_name",
        "products.product_name._2gram",
        "products.product_name._3gram"
      ]
    }
  },
  "size": 3
}
```
**Explanation:**
Optimized search-as-you-type query. Matches "shirt" exactly and "black" as a prefix, using shingle fields (`_2gram`, `_3gram`) to boost phrase relevance.

### 29. Analyze (Did You Mean)
```bash
GET ecommerce/_analyze
{
  "text": "Casual lace-ups - dark brown , Basic T-shirt - white",
  "field": "products.produce_name"
}
```
**Explanation:**
Analyzes the text to see how it breaks down into tokens, useful for debugging "Did you mean" logic.

### 30. Term Suggester (Spell Check)
```bash
GET ecommerce/_search
{
  "suggest": {
    "spell-check": {
      "text": "blzr",
      "term": {
        "field": "products.product_name"
      }
    }
  }
}
```
**Explanation:**
Suggests corrections for the single term "blzr" (e.g., "blazer").

### 31. Multiple Term Suggesters
```bash
GET ecommerce/_search
{
  "suggest": {
    "spell-check1": {
      "text": "blzr",
      "term": {
        "field": "products.product_name"
      }
    },
    "spell-check2": {
      "text": "blck",
      "term": {
        "field": "products.product_name"
      }
    }
  }
}
```
**Explanation:**
Runs two separate spell checks in one request: one for "blzr" and one for "blck".

### 32. Create Index (Shingles)
```bash
PUT books2
{
  "settings": { ... },
  "mappings": { ... }
}
```
**Explanation:**
Creates `books2` index with a custom analyzer that produces shingles (word pairs/triplets) for the `title` field.

### 33. Index Document 1
```bash
PUT books2/_doc/1
{
  "title": "Design Patterns"
}
```
**Explanation:**
Adds a document.

### 34. Index Document 2
```bash
PUT books2/_doc/2
{
  "title": "Software Architecture Patterns Explained"
}
```
**Explanation:**
Adds another document.

### 35. Phrase Suggester
```bash
GET books2/_search
{
  "suggest": {
    "phrase-check": {
      "text": "design paterns",
      "phrase": {
        "field": "title.trigram"
      }
    }
  }
}
```
**Explanation:**
Suggests corrections for the entire phrase "design paterns" -> "Design Patterns", using the shingle field to understand word context.

### 36. Phrase Suggester with Highlight
```bash
GET books2/_search
{
  "suggest": {
    "phrase-check": {
      "text": "design paterns",
      "phrase": {
        "field": "title.trigram",
        "gram_size": 3,
        "highlight": {
          "pre_tag": "<em>",
          "post_tag": "</em>"
        }
      }
    }
  }
}
```
**Explanation:**
Same as above, but highlights the corrected words in the suggestion response.

## 5. Source Filtering

### 37. Disable Source
```bash
GET /ecommerce/_search
{
    "_source": false,
    "query": {
        "match_all": {}
  }
}
```
**Explanation:**
Returns search hits but excludes the `_source` JSON body. Useful for performance if you only need IDs.

### 38. Source Includes/Excludes
```bash
GET /products/_search
{
  "_source": {
    "includes": ["name", "price", "reviews.*", "supplier.*"],
    "excludes": ["reviews.comment", "supplier.contact_email"]
  },
  "query": {
    "match": {
      "category": "Electronics"
    }
  }
}
```
**Explanation:**
Returns only specific fields in the `_source`. Includes `name`, `price`, etc., and explicitly removes sensitive/large fields like `contact_email`.

### 39. Stored Fields
```bash
GET /ecommerce/_search?pretty
{
    "_source": false,
    "fields": ["customer_last_name", "product*"],
    "query": {
        "match_all": {}
  }
}
```
**Explanation:**
Retrieves specific fields that were stored separately (using `store: true` in mapping) or doc values, while disabling `_source`.

## 6. Full Text Queries (Tasks Index)

### 40. Delete Tasks
```bash
DELETE tasks
```
**Explanation:**
Cleans up `tasks` index.

### 41-43. Index Documents
```bash
POST /tasks/_doc/1 ...
POST /tasks/_doc/2 ...
POST /tasks/_doc/3 ...
```
**Explanation:**
Indexes sample task documents with fields like `TASK_NAME`, `RELATED_TASKS_NAMES_LIST`, etc.

### 44. Get Mapping
```bash
GET tasks/_mapping
```
**Explanation:**
Checks the auto-generated mapping for the `tasks` index.

### 45. Match All (POST)
```bash
POST tasks/_search
{
  "query": {
    "match_all": {}
  }
}
```
**Explanation:**
Returns all task documents.

### 46. Match All (GET)
```bash
GET tasks/_search
{
  "query": {
    "match_all": {}
  }
}
```
**Explanation:**
Same as above, using GET.

### 47. Match Query
```bash
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "Code optimization"
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Searches for "Code" OR "optimization" in the `RELATED_TASKS_NAMES_LIST` field.

### 48. Match Query (Substring)
```bash
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "Ui5 code optimization"
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Searches for "Ui5" OR "code" OR "optimization".

### 49. Match Query (Single Token)
```bash
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "Ui5"
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Searches for the single token "Ui5".

### 50. Match Query (Keyword)
```bash
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST.keyword": "Ui5 code optimization"
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Exact match on the `.keyword` sub-field. Must match the entire string "Ui5 code optimization" exactly (case-sensitive).

### 51. Match Phrase (Keyword)
```bash
POST tasks/_search
{
  "query": {
    "match_phrase": {
      "RELATED_TASKS_NAMES_LIST.keyword": "Ui5 code optimization"
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Functionally similar to exact match on a keyword field.

### 52. Match Phrase (Slop 1)
```bash
POST tasks/_search
{
  "query": {
    "match_phrase": {
      "RELATED_TASKS_NAMES_LIST": { 
        "query": "Ui5 optimization",
        "slop": 1
      }
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Matches if "Ui5" and "optimization" appear within 1 word of each other (e.g., "Ui5 code optimization").

### 53. Match Phrase (Reverse Slop)
```bash
POST tasks/_search
{
  "query": {
    "match_phrase": {
      "RELATED_TASKS_NAMES_LIST": { 
        "query": "optimization Ui5",
        "slop": 3
      }
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Matches "Ui5 ... optimization" even if the query is "optimization Ui5", provided the `slop` is high enough to account for the reordering.

### 54. Proximity Search
```bash
POST tasks/_search
{
  "query": {
    "match_phrase": {
      "RELATED_TASKS_NAMES_LIST": { 
        "query": "code optimization",
        "slop": 100
      }
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Matches "code" and "optimization" anywhere within 100 words of each other. Closer matches score higher.

### 55. Match Phrase Prefix
```bash
POST tasks/_search
{
  "query": {
    "match_phrase_prefix": {
      "RELATED_TASKS_NAMES_LIST": "theses"
    }
  },
  "fields" : ["*"]
}
```
**Explanation:**
Matches phrases starting with "theses". Useful for "type-ahead" on the last word of a phrase.

### 56. Term Query (Object)
```bash
POST tasks/_search
{
  "query": {
    "term": {
      "RELATED_TASKS_NAMES_LIST": {
        "value": "theses"
      }
    }
  },
  "fields" : ["RELATED_TASKS_NAMES_LIST"]
}
```
**Explanation:**
Exact term match for "theses". No analysis performed on the query string.

### 57. Term Query (Simple)
```bash
POST tasks/_search
{
  "query": {
    "term": {
      "RELATED_TASKS_NAMES_LIST": "theses"
    }
  },
  "fields" : ["RELATED_TASKS_NAMES_LIST"]
}
```
**Explanation:**
Simplified syntax for the term query.

### 58. Terms Query
```bash
POST tasks/_search
{
  "query": {
    "terms": {
      "RELATED_TASKS_NAMES_LIST": ["theses","Multilingual"]
    }
  },
  "fields" : ["RELATED_TASKS_NAMES_LIST"]
}
```
**Explanation:**
Matches documents containing *either* "theses" OR "Multilingual".

### 59. Bool Filter
```bash
POST tasks/_search
{
  "query": {
    "bool": {
      "filter": {
        "term": {
          "RELATED_TASKS_NAMES_LIST": "theses"
        }
      }
    }
  },
  "fields" : ["RELATED_TASKS_NAMES_LIST"]
}
```
**Explanation:**
Filters documents containing "theses". No relevance score is calculated (score is 0).

### 60. Bool Must + Filter
```bash
POST tasks/_search
{
    "query" : {
        "bool" : {
            "must" : {
                "match" : {
                    "RELATED_TASKS_NAMES_LIST" : "code" 
                }
            },
            "filter" : {
                "range" : {
                    "FIRST_SEEN_DATE": { "gt" : "Jan 7 2024" } 
                }
            }
        }
    }
}
```
**Explanation:**
Finds documents matching "code" (scored) AND having a date greater than Jan 7 2024 (filtered, not scored).

### 61. Complex Bool Query
```bash
GET /tasks/_search
{
  "query": {
    "bool": {
      "must": [ ... ],
      "should": [ ... ],
      "must_not": [ ... ],
      "minimum_should_match": 1
    }
  }
}
```
**Explanation:**
Combines `must` (AND), `should` (OR), and `must_not` (NOT) logic. `minimum_should_match: 1` enforces that at least one `should` clause must match.

### 62. Pagination (Tasks)
```bash
POST tasks/_search
{
  "from": 0,
  "size": 2,
  "query": {
    "match_all": {}
  }
}
```
**Explanation:**
Returns the first 2 documents from the tasks index.

### 63. Sort by Score
```bash
POST tasks/_search
{
  "sort": {
    "_score": {"order": "asc"}
  },
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "code"
    }
  }
}
```
**Explanation:**
Sorts results by relevance score in ascending order (least relevant first).

### 64. Sort by Date
```bash
POST tasks/_search
{
  "sort": {
    "FIRST_SEEN_DATE": {"order": "desc"}
  },
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "code"
    }
  }
}
```
**Explanation:**
Sorts by `FIRST_SEEN_DATE` descending.

### 65. Multi-Sort
```bash
POST tasks/_search
{
  "sort": [
    {"FIRST_SEEN_DATE": "desc"},
    {"_score": "asc"}
  ],
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "code"
    }
  }
}
```
**Explanation:**
Sorts primarily by date, and secondarily by score.

### 66. Sort Text (Fail)
```bash
POST tasks/_search
{
  "sort": {
    "RELATED_AI_DATA_NAMES_LIST": {"order": "desc"}
  },
  ...
}
```
**Explanation:**
Attempts to sort on a `text` field. This usually fails because text fields are tokenized.

### 67. Sort Keyword
```bash
POST tasks/_search
{
  "sort": {
    "RELATED_AI_DATA_NAMES_LIST.keyword": {"order": "desc"}
  },
  ...
}
```
**Explanation:**
Correctly sorts using the `.keyword` sub-field, which contains the untokenized string.

### 68. Fuzzy Text (Fail)
```bash
POST tasks/_search
{
  "query": {
    "fuzzy": {
      "RELATED_TASKS_NAMES_LIST": { ... }
    }
  }
}
```
**Explanation:**
Fuzzy query on a text field. This is generally discouraged or unsupported; `match` with `fuzziness` is preferred.

### 69. Fuzzy Keyword
```bash
POST tasks/_search
{
  "query": {
    "fuzzy": {
      "RELATED_TASKS_NAMES_LIST.keyword": {
        "value": "code optmization",
        "fuzziness": "AUTO"
      }
    }
  }
}
```
**Explanation:**
Fuzzy search on a keyword field. Finds "code optimization" even if input is "code optmization".

### 70. List Indices
```bash
GET _cat/indices
```
**Explanation:**
Lists all indices in the cluster.

### 71. Bool Must Filter
```bash
GET tasks/_search
{
  "query": { 
    "bool": { 
      "must": [ ... ],
      "filter": [ ... ]
    }
  }
}
```
**Explanation:**
Combines multiple `must` clauses (AND) with a `filter`.

### 72. Bool Boost
```bash
POST tasks/_search
{
  "query": {
    "bool" : {
      ...
      "boost" : 1.0
    }
  }
}
```
**Explanation:**
A complex bool query where the entire query is given a boost factor of 1.0.

### 73. Bool Filter Only
```bash
GET tasks/_search
{
  "query": {
    "bool": {
      "filter": {
        "term": {
          "RELATED_TASKS_NAMES_LIST.keyword": "Code optimization"
        }
      }
    }
  }
}
```
**Explanation:**
A pure filter query. Implicitly includes a `match_all` for the scoring part (which is ignored).

### 74. Bool Must Match All + Filter
```bash
GET tasks/_search
{
  "query": {
    "bool": {
      "must": {
        "match_all": {}
      },
      "filter": { ... }
    }
  }
}
```
**Explanation:**
Explicitly states `match_all` in `must` and applies a filter. Functionally same as above.

### 75. Constant Score
```bash
GET tasks/_search
{
  "query": {
    "constant_score": {
      "filter": { ... },
      "boost": 1.2
    }
  }
}
```
**Explanation:**
Wraps a filter and assigns a constant score of 1.2 to every matching document.

### 76. Named Queries
```bash
POST tasks/_search
{
  "query": {
    "bool" : {
      "must" : {
        "match" : { "TASK_NAME" : {"query":"code","_name":"match_task_name"} }
      },
      ...
    }
  }
}
```
**Explanation:**
Assigns names (e.g., `match_task_name`) to query clauses. The response will indicate which clauses matched for each document.

### 77. Named Queries Score
```bash
POST tasks/_search?include_named_queries_score
```
**Explanation:**
Requests the detailed score contribution for each named query.

## 7. Intervals and Query String

### 78. Intervals (Basic)
```bash
POST _search
{
  "query": {
    "intervals" : {
      "my_text" : { ... }
    }
  }
}
```
**Explanation:**
Demonstrates the `intervals` query structure for finding ordered terms "my favorite food" followed by "hot water" or "cold porridge".

### 79. Intervals (Related Tasks)
```bash
POST /tasks/_search
{
  "query": {
    "intervals" : {
      "RELATED_TASKS_NAMES_LIST" : { ... }
    }
  }
}
```
**Explanation:**
Finds "code" followed by "search" OR "simplification" in the `RELATED_TASKS_NAMES_LIST` field.

### 80. Intervals (Code Quality)
```bash
POST /tasks/_search
{
  "query": {
    "intervals" : { ... "query" : "code quality" ... }
  }
}
```
**Explanation:**
Finds "code quality" followed by "improvement" or "simplification".

### 81. Intervals (Fuzzy)
```bash
POST /tasks/_search
{
  "query": {
    "intervals" : { ... "fuzzy" : { "term" : "serch" } ... }
  }
}
```
**Explanation:**
Uses a fuzzy term "serch" (matching "search") inside an intervals query.

### 82. Intervals (Prefix)
```bash
POST /tasks/_search
{
  "query": {
    "intervals" : { ... "prefix" : { "prefix" : "impr" } ... }
  }
}
```
**Explanation:**
Uses a prefix "impr" (matching "improvement") inside an intervals query.

### 83. Intervals (Wildcard)
```bash
POST /tasks/_search
{
  "query": {
    "intervals" : { ... "wildcard" : { "pattern" : "code*" ... } ... }
  }
}
```
**Explanation:**
Uses a wildcard "code*" inside an intervals query.

### 84. Intervals (Filter)
```bash
POST _search
{
  "query": {
    "intervals" : {
      "my_text" : {
        "match" : {
          "query" : "hot porridge",
          "max_gaps" : 10,
          "filter" : {
            "not_containing" : {
              "match" : {
                "query" : "salty"
              }
            }
          }
        }
      }
    }
  }
}
```
**Explanation:**
Finds "hot porridge" with up to 10 words between them, but filters out results where "salty" appears in that gap.

### 85. Query String (AND)
```bash
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Ui5) AND (blockchain)",
      "default_field": "RELATED_TASKS_NAMES_LIST"
    }
  }
}
```
**Explanation:**
Uses Lucene syntax to find documents containing both "Ui5" AND "blockchain".

### 86. Query String (OR)
```bash
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Ui5) OR (blockchain)",
      "default_field": "RELATED_TASKS_NAMES_LIST"
    }
  }
}
```
**Explanation:**
Finds documents containing "Ui5" OR "blockchain".

### 87. Query String (OR - Civil Engineering)
```bash
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Civil engineering) OR (theses)",
      "default_field": "RELATED_TASKS_NAMES_LIST"
    }
  }
}
```
**Explanation:**
Finds "Civil engineering" OR "theses".

### 88. Query String (Fields)
```bash
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Civil engineering) OR (theses)",
      "fields": ["RELATED_TASKS*"]
    }
  }
}
```
**Explanation:**
Searches across all fields matching the pattern `RELATED_TASKS*`.

### 89. Query String (Wildcard)
```bash
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Civil\\*) OR (theses)",
      "fields": ["RELATED_TASKS*"]
    }
  }
}
```
**Explanation:**
Uses an escaped wildcard `Civil\*` in the query string to match terms starting with "Civil".
