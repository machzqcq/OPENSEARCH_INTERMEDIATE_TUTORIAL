# OpenSearch API Explanations

This document provides a 1-to-1 mapping of every API call in `text_search.sh` to a detailed explanation.

## 1. Mapping and Basic Search

### 1. Retrieve Mapping
```bash
GET ecommerce/_mapping
```
**Explanation:**
Retrieves the complete schema definition (mapping) for the `ecommerce` index. The mapping shows:
- **Field names and data types**: text (analyzed), keyword (exact match), integer, date, nested, etc.
- **Analyzer configuration**: Which analyzer is used for tokenization and search
- **Field properties**: Whether fields are indexed, stored, have doc_values enabled
- **Multi-fields**: Sub-fields like `.keyword` versions of text fields

**Business Use Cases:**
- **Schema validation**: Verify that data ingestion mapped fields correctly before running production queries
- **Query optimization**: Understand which fields support full-text search vs exact match to write efficient queries
- **Troubleshooting**: Debug why queries aren't returning expected results by confirming field types
- **Data governance**: Audit what data structures exist in the index for compliance documentation

### 2. Default Search
```bash
POST ecommerce/_search
```
**Explanation:**
Executes a search against the `ecommerce` index without any query body. This implicitly uses a `match_all` query with default parameters:
- **Default size**: Returns 10 documents (OpenSearch default)
- **Default from**: Starts at document 0
- **Score**: All documents receive a score of 1.0 since no relevance calculation is performed
- **Sort order**: Documents are returned in index order

**Business Use Cases:**
- **Data exploration**: Quick check to see sample documents when first connecting to an index
- **Index health validation**: Verify that documents exist and are accessible after data ingestion
- **API connectivity testing**: Simplest query to test that your application can communicate with OpenSearch
- **Preview data structure**: Examine document schema before building complex queries

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
Explicitly defines a `match_all` query that retrieves all documents without filtering. The explicit form is useful when you need to:
- **Combine with other parameters**: Add sorting, pagination, aggregations, or source filtering
- **Document intent**: Make it clear in code that you want all documents, not an empty/missing query
- **Baseline queries**: Use as the foundation to add filters or scoring modifications

**Business Use Cases:**
- **Dashboard initialization**: Load initial dataset for analytics dashboards that show "all products" or "all orders"
- **Bulk data export**: Retrieve all documents for backup, migration, or reporting purposes
- **Testing aggregations**: When you want to test facets/aggregations across the entire dataset
- **Admin interfaces**: Power admin tools that need to display all records with custom filtering UI

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
Field collapsing groups search results by a specified field and returns only one document per unique field value. Key parameters:
- **field**: Must be a keyword or numeric field (not text). Specifies the field to collapse on
- **inner_hits**: Optional parameter to retrieve additional documents from each collapsed group
- **max_concurrent_group_searches**: Controls parallelism for inner_hits retrieval
- **sort**: Determines which document represents each group (the "best" one based on sort criteria)

In this example:
- Searches for "Men's Shoes" in the category field
- Groups results by the `type` field (e.g., sneakers, boots, loafers)
- Returns only the top document from each type based on `day_of_week` sorting

**Business Use Cases:**
- **Product diversity**: E-commerce search showing one product per brand/manufacturer to avoid overwhelming users with similar items
- **Deduplication**: News aggregation sites showing one article per source/publisher
- **Category browsing**: Show one representative product from each subcategory when browsing a parent category
- **Author diversity**: Job boards showing one job posting per company in search results
- **Geographic distribution**: Real estate sites showing one property per neighborhood in a city search

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
Standard offset-based pagination using from/size parameters. This is the simplest pagination method but has limitations:
- **from**: Zero-based offset specifying which document to start from (default: 0)
- **size**: Number of documents to return (default: 10, max: 10,000)
- **max_result_window**: By default, from + size cannot exceed 10,000 to prevent resource exhaustion
- **Performance**: Deep pagination (high `from` values) is expensive because OpenSearch must retrieve and sort all preceding documents on each shard

**Limitations:**
- Not suitable for deep pagination (e.g., page 1000)
- Can cause memory issues and slow queries for large offsets
- Results may be inconsistent if index is updated between page requests

**Business Use Cases:**
- **Simple search results**: User-facing search with pages 1-10 where users rarely go deep
- **Small datasets**: Product catalogs with few hundred items where deep pagination isn't needed
- **Admin pagination**: Back-office tools where you control page depth limits
- **Mobile apps**: Initial results pages where infinite scroll is limited to first few pages

### 6. URI Pagination
```bash
GET ecommerce/_search?from=0&size=10
```
**Explanation:**
Identical functionality to body-based pagination, but parameters are passed as URL query parameters. This approach:
- **Simplicity**: Easier to construct URLs programmatically
- **Caching**: Better suited for HTTP caching strategies
- **Logging**: Easier to log and debug since parameters are visible in URLs
- **Limitations**: Complex queries cannot be expressed in URL parameters

**Business Use Cases:**
- **RESTful APIs**: When building API endpoints that follow REST conventions
- **Cacheable requests**: Simple searches that benefit from HTTP cache headers
- **Bookmarkable URLs**: Search interfaces where users can bookmark or share specific result pages
- **Simple GET requests**: When POST requests are not preferred for read operations

### 7. Scroll Initialization
```bash
GET ecommerce/_search?scroll=10m
{
  "size": 5
}
```
**Explanation:**
The Scroll API creates a consistent snapshot of the index for iterating through large result sets. Key parameters:
- **scroll**: Time value (e.g., `10m`, `1h`) indicating how long the search context should be kept alive
- **size**: Number of documents returned per batch (per shard)
- **scroll_id**: Returned in response, used to fetch subsequent batches
- **Snapshot consistency**: Creates a point-in-time view, so new/updated documents won't appear mid-scroll

Process:
1. First request creates the scroll context and returns initial results + scroll_id
2. Subsequent requests use the scroll_id to retrieve next batches
3. Context expires after inactivity period or when explicitly cleared

**Important Notes:**
- Scroll contexts consume memory; always clear them when done
- Not intended for real-time user requests (use search_after instead)
- Each shard returns `size` documents, so total = size × shard_count

**Business Use Cases:**
- **Data export**: Export millions of documents for backup, migration, or ETL processing
- **Batch processing**: Process all documents for machine learning training, reindexing, or bulk updates
- **Reporting**: Generate comprehensive reports requiring all matching documents
- **Data analytics**: Feed all data into analytics pipelines or data warehouses
- **Index migration**: Move data from one cluster to another

### 8. Scroll Retrieval
```bash
GET _search/scroll
{
  "scroll": "10m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAAUWdmpUZDhnRFBUcWFtV21nMmFwUGJEQQ=="
}
```
**Explanation:**
Retrieves the next batch of results using the scroll_id from the previous response. Parameters:
- **scroll**: Refreshes the scroll context for another 10 minutes. Should match or be shorter than the original scroll time
- **scroll_id**: Unique identifier for this scroll session. Each response returns an updated scroll_id

**Process Flow:**
1. Use the scroll_id from the previous response (not the original one)
2. Keep requesting until no documents are returned (hits array is empty)
3. Each request resets the scroll timeout
4. Clear the scroll when done: `DELETE _search/scroll` with the scroll_id

**Best Practices:**
- Always clear scroll contexts to free resources: `DELETE _search/scroll`
- Monitor scroll context count: `GET _nodes/stats/indices/search`
- Use appropriate timeout values (long enough for processing, short enough to avoid memory issues)

**Business Use Cases:**
- **Continuous data synchronization**: Regularly export data to external systems
- **Audit log extraction**: Extract all audit logs for compliance reporting
- **Full-text index rebuilding**: Retrieve all documents to rebuild search indexes with new analyzers
- **Data quality checks**: Scan entire dataset for validation or cleanup operations

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
Search After is the recommended approach for deep pagination and real-time scrolling through results. Key parameters:
- **size**: Number of results per page
- **sort**: **REQUIRED** - Must define explicit sort order. Include `_id` as tie-breaker for deterministic ordering
- **search_after**: (Used in subsequent requests) Array of sort values from the last document

**Why use Search After:**
- **Efficient deep pagination**: No offset calculation, constant performance regardless of page depth
- **Real-time consistency**: Can be combined with Point-in-Time (PIT) for stable pagination
- **Stateless**: No server-side context to maintain (unlike scroll)
- **Live data**: Can reflect index updates between pages (without PIT)

**Sort Requirements:**
- Must have at least one unique field (like `_id`) as tie-breaker
- All sort fields must have single values per document (not arrays)
- Sort values must be returned in response to use in next request

**Business Use Cases:**
- **Infinite scroll UI**: Social media feeds, product listings, search results with "load more" functionality
- **API pagination**: RESTful APIs serving paginated data to mobile apps or frontend clients
- **Deep result navigation**: Allow users to navigate to page 500+ without performance degradation
- **Real-time feeds**: Activity feeds or notification systems that need to reflect new content
- **Export with progress tracking**: Large data exports where users can pause and resume

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
Retrieves the next page by providing the sort values of the last document from the previous response:
- **search_after**: Array of values corresponding to the sort fields [category_value, id_value]
- **Must maintain same sort order**: The sort array must be identical to the initial query
- **Direction**: Results after these sort values, exclusive (last document not included)

**Implementation Pattern:**
1. Make initial query with sort order
2. Extract sort values from the last document in `hits.hits[last].sort`
3. Use those values in `search_after` parameter for next request
4. Repeat until no more results

**Advantages over from/size:**
- Performance doesn't degrade with page depth
- Memory efficient (no need to keep track of previous pages)
- Works well with PIT for consistency

**Business Use Cases:**
- **Mobile app pagination**: Efficiently paginate through thousands of products or articles
- **Data streaming interfaces**: Continuously load data as user scrolls
- **API rate limiting**: Provide cursor-based pagination for external API consumers
- **Large dataset exploration**: Allow data scientists to navigate through millions of records efficiently

### 11. Point In Time (PIT) Initialization
```bash
POST /ecommerce/_search/point_in_time?keep_alive=100m
```
**Explanation:**
Point in Time (PIT) creates a lightweight, immutable snapshot view of an index that remains consistent across multiple search requests. Key parameters:
- **keep_alive**: Duration the PIT should remain open (e.g., `1m`, `10m`, `1h`)
- **pit_id**: Returned in response, used in subsequent searches
- **Lightweight**: Unlike scroll, PIT doesn't keep result sets in memory, just index state

**How PIT Works:**
- Creates a consistent view of the index at the moment of creation
- Any documents added, updated, or deleted after PIT creation won't affect results
- Must be explicitly closed or will auto-expire after `keep_alive` period
- Can be refreshed by specifying `keep_alive` in subsequent searches

**PIT vs Scroll:**
- **PIT**: Stateless pagination, combines with search_after, better for interactive use
- **Scroll**: Stateful, holds result batches in memory, better for batch export

**Resource Management:**
- Close PIT when done: `DELETE _search/point_in_time` with pit_id
- Monitor open PITs: `GET _nodes/stats/indices/search`
- PITs consume shard-level resources

**Business Use Cases:**
- **Consistent pagination**: E-commerce search where results shouldn't change as user navigates pages
- **Report generation**: Multi-page reports that need consistent data throughout generation
- **Data export with resume**: Allow users to pause/resume exports with consistent results
- **Audit trails**: Ensure compliance reports reflect a specific point in time
- **A/B testing**: Ensure test users see consistent results during testing sessions

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
Combines Point in Time with search_after for optimal pagination. Key aspects:
- **No index name in URL**: When using PIT, query endpoint is `_search` (not `index/_search`)
- **pit.id**: The PIT identifier from initialization
- **pit.keep_alive**: Extends the PIT expiration time with each request
- **search_after**: Used for efficient pagination within the consistent snapshot

**Best Practice Pattern:**
1. Create PIT for the index
2. First search with PIT (no search_after)
3. Subsequent searches use both PIT and search_after
4. Refresh keep_alive on each request
5. Close PIT when pagination complete

**Consistency Guarantees:**
- All pages show same data snapshot, even if index is updated
- User won't see duplicates or miss results due to concurrent updates
- Perfect for financial transactions, audit logs, or legal discovery

**Business Use Cases:**
- **Financial reporting**: Ensure transaction reports are consistent even during active trading
- **Legal e-discovery**: Paginate through millions of documents with guaranteed consistency
- **Shopping cart searches**: Prevent items from appearing/disappearing as user browses
- **Inventory snapshots**: Generate reports on inventory at specific moment in time
- **SLA monitoring**: Ensure metrics calculations use consistent dataset throughout analysis

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
Another example demonstrating search_after pagination without PIT. This approach:
- **Reflects live data**: New documents added between requests may appear
- **Potential inconsistency**: Results might shift if documents are indexed/deleted during pagination
- **Simpler**: No PIT management overhead
- **Use case dependent**: Good for live feeds where some inconsistency is acceptable

**Business Use Cases:**
- **Social media feeds**: Activity streams where seeing new content mid-scroll is desired
- **News aggregators**: Real-time news where latest articles should appear even during browsing
- **Monitoring dashboards**: Log viewers that should show newly ingested logs

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
Sorting controls the order of search results. Key parameters:
- **order**: `asc` (ascending) or `desc` (descending)
- **mode**: For multi-value fields, use `min`, `max`, `avg`, `sum`, or `median`
- **missing**: Specify where documents without the field appear (`_first` or `_last`)
- **unmapped_type**: Define type for sorting on fields that may not exist in all indices

**Field Type Considerations:**
- **Keyword fields**: Required for text sorting (`.keyword` sub-field)
- **Numeric fields**: Direct sorting on integers, floats, dates
- **Nested fields**: Requires special nested sorting syntax

**Performance Impact:**
- Sorting requires field data or doc values
- Text fields without .keyword cannot be sorted
- Multiple sort levels increase computation cost

**Business Use Cases:**
- **Product listings**: Sort by price (low to high), rating (high to low), newest first
- **Customer management**: Sort users alphabetically, by registration date, or by purchase volume
- **Log analysis**: Sort logs chronologically (newest first) or by severity
- **Leaderboards**: Rank users by score, points, or achievements
- **Inventory management**: Sort by stock level to identify items needing reorder

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
Highlighting wraps matching query terms in HTML tags to emphasize them in search results. Key parameters:
- **fields**: Object specifying which fields to highlight (can be empty {} for defaults)
- **pre_tags**: HTML tags to insert before matched terms (default: `["<em>"]`)
- **post_tags**: HTML tags to insert after matched terms (default: `["</em>"]`)
- **fragment_size**: Character length of each highlighted snippet (default: 100)
- **number_of_fragments**: How many fragments to return per field (default: 5)
- **type**: Highlighter type - `unified` (default, fast), `plain`, or `fvh` (fast vector highlighter)
- **require_field_match**: If true, only highlights if query matched the field

**Highlighter Types:**
- **unified**: Best general-purpose highlighter, fast and accurate
- **plain**: Works with all field types but slower
- **fvh**: Fastest for large fields, requires `term_vector: with_positions_offsets`

**Business Use Cases:**
- **Search results UX**: Show users why documents matched their query
- **E-commerce search**: Highlight matched product names, descriptions, or attributes
- **Document search**: Show relevant excerpts from long documents
- **Log search**: Highlight error messages, IPs, or specific patterns in log entries
- **Legal discovery**: Show context around searched terms in legal documents
- **Customer support**: Highlight matching terms in knowledge base articles

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
Custom highlighting allows you to control the HTML markup for emphasized terms:
- **pre_tags/post_tags**: Can use any HTML tags (`<strong>`, `<mark>`, `<span class="highlight">`)
- **Multiple tags**: Can specify multiple pre/post tags for different highlighting styles
- **CSS integration**: Use custom classes to style highlights with CSS

**Advanced Options:**
- **matched_fields**: Combine matches from multiple fields for unified highlighting
- **phrase_limit**: Limit number of phrases to consider for highlighting
- **order**: Sort fragments by `score` (relevance) or `none` (document order)
- **boundary_scanner**: Control fragment boundaries (`chars`, `sentence`, `word`)
- **boundary_chars**: Characters to use as boundaries (default: `.,!? \t\n`)

**Business Use Cases:**
- **Custom UI themes**: Match highlight styling to your brand colors and design system
- **Accessibility**: Use semantic HTML (`<mark>`) for screen readers
- **Rich text display**: Use `<span>` with classes for JavaScript interaction
- **Multiple highlight types**: Different colors for different query terms or field types
- **Mobile optimization**: Use touch-friendly highlight styles for mobile interfaces

## 4. Autocomplete and Suggesters

### 17. Delete Index
```bash
DELETE ecommerce
```
**Explanation:**
Deletes the `ecommerce` index completely, including all documents, mappings, and settings. This is typically done to:
- **Schema changes**: Recreate index with different mappings or analyzers
- **Testing**: Clean slate for testing new configurations
- **Reindexing**: Prepare for data reload with updated settings

**Business Use Cases:**
- **Development/testing**: Reset test environments between test runs
- **Index redesign**: Implement breaking changes to mapping or analysis configuration
- **Data refresh**: Complete data replacement in non-production environments

### 18. Analyze (Autocomplete)
```bash
POST ecommerce/_analyze
{
  "analyzer": "autocomplete",
  "text": "summer"
}
```
**Explanation:**
The `_analyze` API tests how an analyzer tokenizes text, useful for understanding and debugging search behavior. Key aspects:
- **analyzer**: Name of the analyzer to test (must be defined in index settings)
- **text**: The input text to analyze
- **Returns**: Array of tokens generated, with positions, offsets, and types

**Autocomplete Analyzer Pattern:**
Typically uses edge n-grams to create prefix tokens:
- Input: "summer"
- Tokens: ["s", "su", "sum", "summ", "summe", "summer"]

**Configuration Example:**
```json
{
  "filter": {
    "autocomplete_filter": {
      "type": "edge_ngram",
      "min_gram": 1,
      "max_gram": 20
    }
  },
  "analyzer": {
    "autocomplete": {
      "tokenizer": "standard",
      "filter": ["lowercase", "autocomplete_filter"]
    }
  }
}
```

**Business Use Cases:**
- **Debugging search issues**: Understand why searches aren't matching as expected
- **Analyzer design**: Test custom analyzers before indexing data
- **Documentation**: Show stakeholders how search tokenization works
- **Quality assurance**: Verify analyzer behavior for different languages or special characters

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
**INCORRECT APPROACH** - This applies the edge n-gram analyzer to the query string, which generates too many tokens:
- Query "sum" becomes: ["s", "su", "sum"]
- Matches anything containing "s", "su", or "sum" = too many results

**Problem**: Using the same analyzer at index and search time for edge n-grams causes over-matching.

**Correct pattern**: Index with edge n-gram analyzer, search with standard analyzer (see next example).

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
**CORRECT APPROACH** for edge n-gram autocomplete:
- **Index time**: Field indexed with edge n-gram analyzer (creates ["s", "su", "sum", "summ", "summe", "summer"])
- **Search time**: Query uses standard analyzer (keeps "sum" as single token)
- **Result**: Query "sum" matches all documents with edge n-grams starting with "sum"

**Best Practice Configuration:**
```json
"mappings": {
  "properties": {
    "product_name": {
      "type": "text",
      "analyzer": "autocomplete",
      "search_analyzer": "standard"
    }
  }
}
```

**Business Use Cases:**
- **Search box autocomplete**: Show matching products as user types
- **Command palettes**: IDE or application command search
- **Address lookup**: Find addresses as user types street names
- **Product SKU search**: Match product codes with partial input
- **Tag/category suggestions**: Help users find categories by typing prefixes

### 21. Delete Index
```bash
DELETE ecommerce
```
**Explanation:**
Cleans up the index again to prepare for completion suggester examples.

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
The `completion` field type is specially optimized for fast prefix suggestions and autocomplete. Key characteristics:
- **In-memory structure**: Uses FST (Finite State Transducer) for blazing-fast lookups
- **Prefix-only**: Only supports prefix matching, not infix or suffix
- **Weighted results**: Supports boost weights for result ranking
- **Context-aware**: Can filter suggestions by context (e.g., category, user type)

**Completion Type Parameters:**
- **analyzer**: Analyzer for indexing suggestions (default: simple)
- **search_analyzer**: Analyzer for query (default: same as analyzer)
- **preserve_separators**: Keep separators like spaces (default: true)
- **preserve_position_increments**: Affects phrase queries (default: true)
- **max_input_length**: Maximum chars to index (default: 50)

**Advanced Features:**
```json
"product_suggestion": {
  "type": "completion",
  "contexts": [
    {
      "name": "category",
      "type": "category"
    }
  ]
}
```

**Business Use Cases:**
- **Type-ahead search**: Fast as-you-type suggestions for search boxes
- **Product name completion**: Suggest full product names from partial input
- **Command completion**: IDE or CLI command suggestions
- **Email address completion**: Suggest email addresses in messaging apps
- **Location autocomplete**: City/address suggestions for booking or shipping forms

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
Completion suggester provides ultra-fast prefix-based suggestions. Key parameters:
- **prefix**: The text to find suggestions for
- **field**: Must be a `completion` type field
- **size**: Number of suggestions to return (default: 5)
- **skip_duplicates**: Remove duplicate suggestions (default: false)
- **fuzzy**: Enable fuzzy matching for typo tolerance

**Response Structure:**
```json
{
  "suggest": {
    "autocomplete": [
      {
        "text": "summer",
        "offset": 0,
        "length": 6,
        "options": [
          {"text": "Summer Dress", "_score": 1.0},
          {"text": "Summer Sandals", "_score": 1.0}
        ]
      }
    ]
  }
}
```

**Performance:**
- Sub-millisecond response times
- Scales to millions of suggestions
- Minimal memory overhead per suggestion

**Business Use Cases:**
- **E-commerce search bar**: Instant product suggestions
- **Travel booking**: Airport, city, or hotel name completion
- **Social media**: Username or hashtag suggestions
- **Music/video platforms**: Song, artist, or playlist suggestions
- **Enterprise search**: Document title or project name completion

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
Fuzzy completion handles typos and misspellings in autocomplete queries. Key fuzzy parameters:
- **fuzziness**: Edit distance - `0`, `1`, `2`, or `AUTO` (recommended)
  - `AUTO`: Based on term length: 0 for 1-2 chars, 1 for 3-5 chars, 2 for 6+ chars
- **transpositions**: Allow character transpositions (default: true)
- **min_length**: Minimum prefix length before fuzzy matching applies (default: 3)
- **prefix_length**: Number of initial characters that must match exactly (default: 1)
- **unicode_aware**: UTF-8 character handling (default: false)

**Example:**
- Input: "smmer" (missing 'u')
- Matches: "summer" (edit distance of 1)

**Performance Considerations:**
- Fuzzy matching is slower than exact prefix matching
- Higher fuzziness values = more CPU usage
- Use `prefix_length` to improve performance by requiring exact initial match

**Trade-offs:**
- **With fuzzy**: Better user experience, tolerates typos
- **Without fuzzy**: Faster, requires exact spelling

**Business Use Cases:**
- **Mobile search**: Compensate for small keyboard typos
- **International users**: Handle spelling variations and transliteration differences
- **Fast typing**: Accommodate users typing quickly with errors
- **Voice-to-text**: Handle speech recognition errors
- **Accessibility**: Support users with dyslexia or motor challenges

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
Attempts to use wildcard pattern `sum*` with completion suggester. However:
- **Completion suggester does NOT support regex/wildcards in prefix**
- The `*` is treated as a literal character, not a wildcard
- For regex matching, use `regexp` query on text fields instead

**Alternative for Patterns:**
For true wildcard/regex suggestions, use:
```json
{
  "query": {
    "wildcard": {
      "product_name.keyword": "sum*"
    }
  }
}
```

**Business Use Cases:**
- **Understanding limitations**: This example shows what NOT to do with completion suggester
- **Complex pattern matching**: Use wildcard/regex queries for advanced patterns
- **SKU search**: When product codes follow patterns, use wildcard on keyword fields

### 26. Delete Index
```bash
DELETE ecommerce
```
**Explanation:**
Cleans up the index to prepare for search_as_you_type examples.

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
The `search_as_you_type` field type provides optimized autocomplete with phrase awareness. It automatically creates multiple sub-fields:

**Auto-generated Fields:**
- **Base field**: Standard analyzed text field
- **._2gram**: Bigrams (2-word shingles) with edge n-grams on last term
- **._3gram**: Trigrams (3-word shingles) with edge n-grams on last term  
- **._index_prefix**: Edge n-grams of the base field

**Example for "blue cotton shirt":**
- Base: ["blue", "cotton", "shirt"]
- _2gram: ["blue cotton", "cotton shirt"]
- _3gram: ["blue cotton shirt"]
- Each with edge n-grams on final term

**Parameters:**
- **max_shingle_size**: Max words in shingles (default: 3, max: 4)
- **analyzer**: Analyzer for indexing (default: standard)

**Advantages over basic edge n-grams:**
- **Phrase-aware**: Understands multi-word queries better
- **Context preservation**: Maintains word relationships
- **Automatic sub-fields**: No manual mapping configuration needed

**Storage Trade-off:**
- Uses more disk space (multiple sub-fields)
- Provides better autocomplete quality
- Faster queries than match_phrase_prefix

**Business Use Cases:**
- **Product search**: E-commerce autocomplete with multi-word product names
- **Document titles**: Search technical documentation or article titles
- **Movie/book search**: Find media content with complex multi-word titles
- **Recipe finder**: Search recipes like "chocolate chip cookies"
- **Job search**: Find positions like "senior software engineer"

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
The `bool_prefix` multi_match query is specifically designed for search_as_you_type fields. How it works:

**Query Breakdown for "shirt black":**
- All terms except last are treated as exact matches: `match("shirt")`
- Last term is treated as prefix: `prefix("black")` matches "black", "blackout", "blacks"
- Constructs bool query combining matches across all specified fields

**Field Strategy:**
- **Base field**: Matches individual words
- **_2gram**: Boosts 2-word phrases
- **_3gram**: Boosts 3-word phrases
- Result: Multi-word queries score higher when terms appear as phrases

**Scoring:**
- Documents with exact phrase matches score higher
- Documents with terms close together score higher
- Last term can be incomplete (prefix match)

**Parameters:**
- **query**: The search text
- **fields**: List of base and shingle fields
- **type**: Must be "bool_prefix"
- **operator**: AND or OR (default: OR for all but last term)

**Comparison to other approaches:**
- **vs match_phrase_prefix**: Faster, more flexible, better phrase scoring
- **vs completion**: Supports multi-word better, more flexible, slightly slower
- **vs edge n-grams**: Automatic phrase handling, easier to configure

**Business Use Cases:**
- **E-commerce search bars**: Real-time product search as users type
- **Content management**: Find articles, blog posts with multi-word titles
- **Customer support**: Search knowledge base articles by typing questions
- **Media libraries**: Find songs, movies, shows with descriptive titles
- **Code search**: Find functions, classes with multi-word names

### 29. Analyze (Did You Mean)
```bash
GET ecommerce/_analyze
{
  "text": "Casual lace-ups - dark brown , Basic T-shirt - white",
  "field": "products.produce_name"
}
```
**Explanation:**
Tests how text is tokenized for a specific field to understand spell check behavior:
- **field**: Uses the analyzer configured for that field
- Shows token breakdown for debugging spell correction logic
- Helps understand why certain suggestions appear

**Use for debugging:**
- Verify field analyzer configuration
- Understand tokenization before implementing suggesters
- Test analyzer behavior with real product data

**Business Use Cases:**
- **Quality assurance**: Validate that product names tokenize correctly for spell check
- **Troubleshooting**: Debug why spell corrections aren't working as expected
- **Analyzer tuning**: Test analyzer changes before reindexing

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
Term suggester provides spell correction for individual terms by finding similar terms in the index. Key parameters:

**Basic Parameters:**
- **text**: The term to spell-check
- **field**: Field to search for suggestions (must be analyzed)
- **size**: Number of suggestions per term (default: 5)

**Advanced Parameters:**
- **suggest_mode**: When to suggest alternatives:
  - `missing` (default): Only suggest if term not in index
  - `popular`: Suggest terms more frequent than original
  - `always`: Always suggest alternatives
- **max_edits**: Maximum edit distance (1 or 2, default: 2)
- **min_word_length**: Minimum term length to spell-check (default: 4)
- **max_inspections**: Limit docs examined per shard (default: 5)
- **min_doc_freq**: Minimum docs a suggestion must appear in (default: 0)
- **max_term_freq**: Maximum frequency of input term to suggest (default: 0.01)
- **prefix_length**: Number of initial characters that must match (default: 1)

**How it works:**
- Calculates edit distance (Levenshtein) to find similar terms
- Ranks suggestions by document frequency in the index
- Each term in text is checked independently (no phrase context)

**Limitations:**
- **No phrase context**: "New York" checked as separate words
- **Frequency based**: Only suggests terms that exist in the index
- **Not semantic**: Won't suggest synonyms, only spelling variations

**Business Use Cases:**
- **Simple spell check**: Basic "Did you mean" for search boxes
- **Product name correction**: Suggest correct product names from catalog
- **Tag correction**: Fix misspelled tags or categories
- **Log analysis**: Correct command names or error codes in log search
- **Internal search**: Employee directory or knowledge base spell correction

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
Multiple suggesters can run in a single request for efficiency:
- **Named suggesters**: Each suggester has a unique name
- **Parallel execution**: All run simultaneously
- **Different configurations**: Each can have different parameters
- **Separate responses**: Results organized by suggester name

**Use Cases:**
- Check multiple misspelled words in one request
- Apply different suggest_modes to different fields
- Spell-check multiple form fields simultaneously
- Compare suggestion quality across different configurations

**Business Use Cases:**
- **Multi-field forms**: Spell-check multiple input fields in one API call
- **Query expansion**: Generate alternatives for multiple query terms
- **Batch processing**: Correct multiple product names or titles efficiently
- **A/B testing**: Compare different suggester configurations simultaneously

### 32. Create Index (Shingles)
```bash
PUT books2
{
  "settings": { ... },
  "mappings": { ... }
}
```
**Explanation:**
Creates `books2` index with custom analyzer for phrase suggestions. The mapping includes:

**Shingle Configuration:**
```json
"filter": {
  "shingle_filter": {
    "type": "shingle",
    "min_shingle_size": 2,
    "max_shingle_size": 3,
    "output_unigrams": true
  }
}
```

**What are Shingles:**
- **Shingles**: N-grams of words (word combinations)
- Input: "Design Patterns"
- Output: ["Design", "Patterns", "Design Patterns"]

**Why for Phrase Suggestions:**
- Phrase suggester uses shingles to understand word collocations
- Identifies which words commonly appear together
- Provides context-aware corrections ("Design Patterns" not "Design Paterns")

**Parameters:**
- **min_shingle_size**: Minimum words in shingle (default: 2)
- **max_shingle_size**: Maximum words (default: 2)
- **output_unigrams**: Include single words (default: true)

**Business Use Cases:**
- **Book/article titles**: Correct multi-word titles
- **Brand names**: Handle misspelled brand phrases
- **Technical terms**: Correct industry-specific multi-word terms
- **Product descriptions**: Spell-check marketing copy

### 33. Index Document 1
```bash
PUT books2/_doc/1
{
  "title": "Design Patterns"
}
```
**Explanation:**
Adds sample document for phrase suggester testing. The document is indexed with:
- Standard analysis for the base field
- Shingle analysis for the trigram field (used by phrase suggester)

### 34. Index Document 2
```bash
PUT books2/_doc/2
{
  "title": "Software Architecture Patterns Explained"
}
```
**Explanation:**
Adds another document with overlapping terms to demonstrate phrase suggestion quality.

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
Phrase suggester provides context-aware spell correction for multi-word queries. Key parameters:

**Basic Parameters:**
- **text**: The phrase to correct
- **field**: Must be a shingle field (trigrams, bigrams)
- **size**: Number of phrase suggestions (default: 5)

**Advanced Parameters:**
- **gram_size**: Size of shingles in the field (2 or 3)
- **real_word_error_likelihood**: Probability term is misspelled despite being in index (default: 0.95)
- **confidence**: Minimum score threshold (default: 1.0)
- **max_errors**: Maximum percentage of terms that can be misspellings (default: 1.0)
- **separator**: Character separating terms in output (default: space)
- **direct_generator**: Configure individual term suggestions:
  - **suggest_mode**: missing, popular, always
  - **max_edits**: 1 or 2
  - **min_word_length**: Minimum length
  - **prefix_length**: Required prefix match

**How it Works:**
1. Breaks phrase into terms
2. Generates suggestions for each term
3. Uses shingle frequencies to score phrase combinations
4. Returns best phrase combinations based on bigram/trigram probabilities

**Advantages over Term Suggester:**
- **Context-aware**: "new york" corrected as phrase, not separate words
- **Phrase likelihood**: Uses word collocation frequency
- **Better accuracy**: "patterns" preferred over "paterns" in "Design patterns"

**Business Use Cases:**
- **Search queries**: "Did you mean" for multi-word searches
- **Book/movie search**: Correct titles like "harry poter" → "harry potter"
- **Address validation**: Correct street names and city phrases
- **Medical/legal search**: Correct technical multi-word terms
- **Academic search**: Correct paper titles or author names
- **Product search**: "red running shoze" → "red running shoes"

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
Adds highlighting to phrase suggestions to show which words were corrected:
- **pre_tag**: HTML tag before corrected words (default: `<em>`)
- **post_tag**: HTML tag after corrected words (default: `</em>`)
- **gram_size**: Must match the shingle size of the field

**Output Example:**
```json
{
  "text": "design paterns",
  "highlighted": "design <em>patterns</em>"
}
```

**Business Use Cases:**
- **User feedback**: Show users exactly what was corrected
- **Confidence display**: Visual indication of spell corrections
- **Learning systems**: Help users learn correct spellings
- **Debug tool**: Identify which corrections were applied

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
Excludes the `_source` field from search results, returning only metadata (\_id, \_index, \_score). Key aspects:
- **_source**: Contains the original JSON document
- **false**: Completely disables source retrieval
- **Metadata only**: Returns document IDs and scores without content

**Performance Benefits:**
- Reduces network bandwidth significantly
- Faster response times for large documents
- Lower memory usage on coordination node
- Ideal when you only need IDs for subsequent operations

**Use Cases:**
- **Count operations**: When you only need to know which documents match
- **ID collection**: Gather document IDs for bulk operations
- **Aggregation-only queries**: When only aggregation results matter
- **Existence checks**: Verify documents exist without retrieving content

**Business Use Cases:**
- **Bulk deletion**: Collect IDs of documents to delete based on criteria
- **Data synchronization**: Compare ID sets between systems
- **Analytics queries**: Run aggregations without document overhead
- **Cache invalidation**: Get IDs of documents to invalidate from cache
- **Metrics calculation**: Pure scoring/counting operations

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
Selectively includes/excludes specific fields from the `_source`. Key parameters:

**Includes:**
- **Explicit fields**: List specific fields by name
- **Wildcards**: Use `*` for pattern matching (e.g., `reviews.*`)
- **Nested paths**: Use dot notation for nested fields
- **Multiple patterns**: Array of patterns to include

**Excludes:**
- **Applied after includes**: Excludes take precedence
- **Remove sensitive data**: Exclude PII or large text fields
- **Fine-grained control**: Remove specific nested fields

**Pattern Examples:**
- `"user.*"`: All fields under user object
- `"*.email"`: Any email field at any level
- `"reviews.*.text"`: Text field in all review objects

**Processing Order:**
1. Apply includes (if specified, only these fields considered)
2. Apply excludes (remove from included set)
3. Return resulting field set

**Performance Considerations:**
- Less data transferred = faster response
- Still requires reading full `_source` from disk
- More efficient than post-processing in application
- Filtering happens on the coordinating node

**Business Use Cases:**
- **PII compliance**: Exclude sensitive fields like SSN, credit cards from search results
- **Mobile APIs**: Return minimal data for bandwidth-constrained devices
- **Public APIs**: Remove internal-only fields before exposing data
- **Performance optimization**: Exclude large text blobs (descriptions, comments)
- **Frontend optimization**: Return only fields needed for UI rendering
- **Role-based access**: Show different field sets based on user permissions
- **Audit logging**: Exclude large binary or text fields from logs

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
Retrieves specific fields using `fields` parameter instead of `_source`. Key differences:

**Fields vs _source:**
- **fields**: Uses doc values or stored fields, more efficient for specific fields
- **_source**: Reads full JSON document from storage
- **fields**: Returns normalized field values (arrays, dates formatted)
- **_source**: Returns original document as indexed

**Fields Parameter Features:**
- **Doc values**: Automatically uses column-oriented storage
- **Wildcards**: Support patterns like `product*`
- **Format**: Can specify date/number formatting
- **Multi-fields**: Can retrieve sub-fields like `.keyword`

**Example with Formatting:**
```json
{
  "fields": [
    "customer_last_name",
    {
      "field": "order_date",
      "format": "yyyy-MM-dd"
    }
  ]
}
```

**When to Use Fields:**
- **Aggregation fields**: Fields with doc_values already in memory
- **Specific field retrieval**: Need only a few fields from large documents
- **Formatted output**: Need dates/numbers in specific format
- **Keyword fields**: Retrieving .keyword versions more efficient

**Performance:**
- **Faster**: Doc values avoid JSON parsing
- **Memory efficient**: Column-oriented access
- **Cached**: Doc values often cached by OS

**Limitations:**
- Requires `store: true` or doc_values enabled
- Text fields without doc_values can't be retrieved
- Nested field retrieval is limited

**Business Use Cases:**
- **High-performance APIs**: Fast field retrieval for specific use cases
- **Real-time dashboards**: Quick access to metric fields
- **Export operations**: Efficient extraction of specific columns
- **Reporting**: Formatted date/number output for reports
- **Search suggestions**: Retrieve only necessary display fields
- **Mobile apps**: Minimize processing for battery efficiency

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

**Detailed Explanation:**
The `match` query is the foundation of full-text search. It analyzes the query string and searches for matching terms. Key parameters:

**Basic Behavior:**
- **Analyzes query**: "Code optimization" → ["code", "optimization"] (lowercase, tokenized)
- **Default operator**: OR - matches documents containing "code" OR "optimization" (at least one)
- **Scoring**: Documents with both terms score higher
- **Field analyzer**: Uses the analyzer configured for the field

**Important Parameters:**
- **operator**: `OR` (default) or `AND`
  - OR: Any term must match (more results, lower precision)
  - AND: All terms must match (fewer results, higher precision)
- **minimum_should_match**: Fine-grained control over required terms
  - Examples: `2` (at least 2 terms), `75%` (at least 75% of terms)
- **fuzziness**: Enable fuzzy matching for typos
  - Values: `0`, `1`, `2`, or `AUTO`
- **analyzer**: Override default field analyzer
- **boost**: Increase/decrease relevance score (default: 1.0)
- **lenient**: Ignore format errors like text in numeric fields (default: false)

**Example with Parameters:**
```json
{
  "match": {
    "RELATED_TASKS_NAMES_LIST": {
      "query": "Code optimization",
      "operator": "AND",
      "fuzziness": "AUTO"
    }
  }
}
```

**Business Use Cases:**
- **General search bars**: Primary query type for user-facing search
- **Document search**: Find documents mentioning key terms
- **E-commerce search**: Find products matching search keywords
- **Log search**: Find log entries containing error terms or IDs
- **Knowledge base**: Search articles by topic keywords
- **Job search**: Match job descriptions with skill keywords
- **Customer support**: Find tickets mentioning product names or issues

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

**Detailed Explanation:**
`match_phrase` searches for terms in order, with slop controlling how close they must be. Key parameters:

**Slop Parameter:**
- **slop: 0** (default): Terms must be adjacent with no words between
- **slop: 1**: Up to 1 word can appear between terms
- **slop: N**: Up to N positions of movement allowed

**How Slop Works:**
- Counts the number of position movements needed to match the phrase
- Includes gaps between words and word reordering
- Example: "Ui5 optimization" with slop 1 matches "Ui5 code optimization" (1 word gap)

**Scoring with Slop:**
- Exact phrases (slop 0) score highest
- Closer terms score higher than distant ones
- Encourages relevant proximity without requiring exact adjacency

**Other Parameters:**
- **analyzer**: Override field analyzer
- **zero_terms_query**: Behavior when all terms removed by analyzer (`none` or `all`)

**Slop Use Cases by Value:**
- **slop: 0**: Exact phrases ("New York", "machine learning")
- **slop: 1-3**: Related concepts that should be close ("python programming", "data analysis")
- **slop: 10-50**: Conceptual proximity in longer text ("tax" near "deduction")
- **slop: 100+**: Broader proximity search, almost like AND query with position boost

**Business Use Cases:**
- **Brand name search**: "Nike Air" should match "Nike Air Max" and "Nike's Air technology"
- **Medical records**: Find "heart attack" allowing for "heart muscle attack"  
- **Legal documents**: Search for "breach of contract" allowing inserted adjectives
- **Technical docs**: "Python programming" matches "Python 3 programming"
- **Product descriptions**: "memory foam" matches "memory gel foam"
- **Recipe search**: "chocolate chip" matches "chocolate chip cookies" or "dark chocolate chips"

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

**Detailed Explanation:**
The `term` query performs exact matching on the inverted index without analyzing the query string. Critical differences from `match`:

**Key Characteristics:**
- **No analysis**: Query string "Theses" stays as "Theses" (not lowercased)
- **Exact term matching**: Must match a term in the inverted index exactly
- **Case-sensitive**: "theses" ≠ "Theses" ≠ "THESES"
- **Binary scoring**: Document either matches (score calculated) or doesn't match
- **Fast**: No analysis overhead, direct index lookup

**Parameters:**
- **value**: The exact term to search for
- **boost**: Score multiplier (default: 1.0)
- **case_insensitive**: Make matching case-insensitive (default: false)

**Common Pitfalls:**
```json
// ❌ WRONG - Won't match analyzed text fields
{"term": {"product_name": "Blue Shirt"}}
// Text field indexed as: ["blue", "shirt"]
// Query searches for: "Blue Shirt" (not analyzed)
// Result: No match

// ✅ CORRECT - Use on keyword fields
{"term": {"product_name.keyword": "Blue Shirt"}}
// or lowercase for analyzed fields
{"term": {"product_name": "blue"}}
```

**When to Use Term vs Match:**
- **Use term for:**
  - Keyword fields (exact matching)
  - Enums, status codes, IDs
  - Tags, categories
  - Boolean values
  - Numeric/date ranges
- **Use match for:**
  - Full-text search on analyzed text fields
  - User search queries
  - Natural language content

**Business Use Cases:**
- **Status filtering**: Filter orders by status (`"pending"`, `"completed"`, `"cancelled"`)
- **Category filtering**: Exact category match in e-commerce (`"Electronics"`, `"Clothing"`)
- **ID lookup**: Find documents by exact ID, SKU, or product code
- **Tag filtering**: Match exact tags (`"featured"`, `"sale"`, `"new-arrival"`)
- **User type filtering**: Filter by exact user role (`"admin"`, `"customer"`, `"vendor"`)
- **Boolean filters**: `is_active: true`, `is_featured: false`
- **Dropdown filters**: Exact matches for filter dropdowns (size, color, brand)

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

**Detailed Explanation:**
`terms` query matches documents where the field contains ANY of the specified exact terms (OR logic). Parameters:

**Key Features:**
- **Multiple values**: Pass an array of values to match
- **Exact matching**: Like `term`, no analysis performed
- **OR logic**: Document matches if it contains ANY of the terms
- **Efficient**: Single query instead of multiple `term` queries with `should`

**Parameters:**
- **field**: Array of exact values to match
- **boost**: Score multiplier for all matching documents

**Example with More Terms:**
```json
{
  "terms": {
    "status.keyword": ["pending", "processing", "shipped"]
  }
}
```

**Performance:**
- More efficient than bool query with multiple `should` clauses
- Terms are looked up in parallel
- Good for moderate list sizes (up to ~1000 terms)
- For very large term lists (10,000+), consider `terms` lookup from another index

**Terms Lookup (Advanced):**
```json
{
  "terms": {
    "user.id": {
      "index": "authorized_users",
      "id": "group1",
      "path": "user_ids"
    }
  }
}
```
Fetches the list of terms from another document.

**Business Use Cases:**
- **Multi-select filters**: User selects multiple brands, categories, or colors
- **Batch ID lookup**: Find multiple products/users by ID list
- **Status filtering**: Show orders in multiple statuses ("pending", "processing", "shipped")
- **Tag filtering**: Match documents with any of selected tags
- **Permission checks**: Match users with any of allowed role IDs
- **Geographic filter**: Match documents from multiple cities/regions
- **Time-based filters**: Match documents from specific days of week/hours
- **Campaign filtering**: Find products in multiple promotional campaigns
- **Inventory lookup**: Check stock for multiple SKUs simultaneously

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

**Detailed Explanation:**
Bool query is the most powerful query type in OpenSearch, combining multiple query clauses with different logical operators. Key clauses:

**Bool Query Clauses:**

1. **must**: All clauses must match (AND logic)
   - Contributes to relevance scoring
   - Example: Document must contain "code" AND have date > Jan 7 2024
   
2. **filter**: All clauses must match (AND logic)
   - **NO scoring impact** - pure filtering
   - **Faster**: Can be cached effectively
   - Use for exact matches, ranges, existence checks
   
3. **should**: At least one clause should match (OR logic)
   - Contributes to scoring if matches
   - Use `minimum_should_match` to require N matches
   - Boosts documents that match more clauses
   
4. **must_not**: No clauses can match (NOT logic)
   - **NO scoring impact** - pure exclusion
   - Efficient negation filter

**Key Parameters:**
- **minimum_should_match**: Controls how many `should` clauses must match
  - Integer: Exact number (e.g., `2`)
  - Percentage: Proportion (e.g., `"75%"`)
  - Combinations: `"3<90%"` (if 3+ terms, 90% must match)
- **boost**: Multiply the score of entire bool query
- **_name**: Name this clause for debugging

**Must vs Filter - Critical Difference:**
```json
{
  "bool": {
    "must": [
      {"match": {"description": "laptop"}}  // Affects score
    ],
    "filter": [
      {"range": {"price": {"lte": 1000}}},  // No score impact
      {"term": {"in_stock": true}}           // No score impact
    ]
  }
}
```

**Scoring Behavior:**
- **must**: Each clause contributes to final score
- **should**: Matching clauses boost score
- **filter**: No impact on score
- **must_not**: No impact on score

**Performance Optimization:**
- Use `filter` instead of `must` when scoring doesn't matter
- Filters are cached automatically
- Put most restrictive filters first
- Combine multiple `term` filters into single `terms` filter

**Complex Bool Query Structure:**
```json
{
  "bool": {
    "must": [
      {"match": {"title": "smartphone"}}
    ],
    "should": [
      {"match": {"brand": "Samsung"}},
      {"match": {"brand": "Apple"}}
    ],
    "filter": [
      {"range": {"price": {"gte": 200, "lte": 1000}}},
      {"term": {"in_stock": true}}
    ],
    "must_not": [
      {"term": {"refurbished": true}}
    ],
    "minimum_should_match": 1,
    "boost": 1.5
  }
}
```

**Business Use Cases:**
- **E-commerce product search**:
  - `must`: Match search query "running shoes"
  - `should`: Boost preferred brands
  - `filter`: Price range, in stock, size available
  - `must_not`: Exclude discontinued items
  
- **Job search**:
  - `must`: Match required skills
  - `should`: Nice-to-have skills (boost if present)
  - `filter`: Location, salary range, job type
  - `must_not`: Expired listings
  
- **Real estate search**:
  - `must`: Location match
  - `should`: Amenities (pool, garage) - each boosts score
  - `filter`: Price range, bedrooms, square footage
  - `must_not`: Sold properties
  
- **Content recommendations**:
  - `must`: User's interests
  - `should`: Trending topics, similar to liked content
  - `filter`: Published after date, language, content type
  - `must_not`: Already viewed/purchased
  
- **Log analysis**:
  - `must`: Error level
  - `should`: Specific error codes
  - `filter`: Time range, service name
  - `must_not`: Test environments

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

**Detailed Explanation:**
Complex bool query demonstrating all four clause types working together. Understanding the execution flow:

**Execution Order:**
1. **must_not**: Exclude documents first (most efficient)
2. **filter**: Apply non-scoring filters (cached)
3. **must**: Score and filter matching documents
4. **should**: Boost scores of documents (if `minimum_should_match` satisfied)

**minimum_should_match Deep Dive:**

**When NO must/filter clauses exist:**
- `should` clauses are required (at least one must match)
- `minimum_should_match` defaults to 1

**When must/filter clauses exist:**
- `should` clauses become optional (pure boost)
- `minimum_should_match` defaults to 0
- Set explicitly to require should matches

**Examples:**
```json
// At least 2 of 5 should clauses
{"minimum_should_match": 2}

// At least 75% of should clauses
{"minimum_should_match": "75%"}

// Conditional: if 4+ should clauses, 3 must match
{"minimum_should_match": "3<75%"}

// Negative: all but 1 must match
{"minimum_should_match": "-1"}
```

**Advanced Patterns:**

**1. Boosting Specific Conditions:**
```json
{
  "bool": {
    "must": [{"match": {"content": "search query"}}],
    "should": [
      {"term": {"featured": true}, "boost": 2.0},
      {"range": {"publish_date": {"gte": "now-7d"}}, "boost": 1.5},
      {"match": {"author": "popular_author"}, "boost": 1.2}
    ]
  }
}
```

**2. Multi-layered Filtering:**
```json
{
  "bool": {
    "must": [{"match": {"description": "laptop"}}],
    "filter": [
      {"bool": {
        "should": [
          {"term": {"brand": "Dell"}},
          {"term": {"brand": "HP"}}
        ]
      }},
      {"range": {"price": {"lte": 1500}}}
    ]
  }
}
```

**3. Negative Boosting Pattern:**
```json
{
  "bool": {
    "must": [{"match": {"title": "python"}}],
    "should": [
      {"match": {"tags": "tutorial"}, "boost": 2},
      {"match": {"tags": "advanced"}, "boost": 0.5}
    ]
  }
}
```

**Common Patterns:**

**Search with Facet Filters:**
```json
{
  "bool": {
    "must": [
      {"multi_match": {
        "query": "red shoes",
        "fields": ["title", "description"]
      }}
    ],
    "filter": [
      {"terms": {"category": ["footwear", "accessories"]}},
      {"range": {"price": {"gte": 50, "lte": 200}}},
      {"term": {"in_stock": true}}
    ]
  }
}
```

**Personalized Search:**
```json
{
  "bool": {
    "must": [
      {"match": {"content": "machine learning"}}
    ],
    "should": [
      {"term": {"author_id": "user_123"}, "boost": 3},
      {"terms": {"tags": ["user_interests"]}, "boost": 2},
      {"range": {"created_at": {"gte": "now-30d"}}, "boost": 1.5}
    ],
    "filter": [
      {"term": {"language": "en"}},
      {"term": {"is_published": true}}
    ],
    "must_not": [
      {"terms": {"id": ["viewed_doc_ids"]}}
    ]
  }
}
```

**Business Use Cases:**

**1. Marketplace Search:**
```json
{
  "bool": {
    "must": [
      {"match": {"product_name": "wireless headphones"}}
    ],
    "should": [
      {"term": {"seller_rating": "5_star"}, "boost": 2},
      {"range": {"review_count": {"gte": 100}}, "boost": 1.5},
      {"term": {"prime_eligible": true}, "boost": 1.3}
    ],
    "filter": [
      {"range": {"price": {"lte": 150}}},
      {"term": {"availability": "in_stock"}}
    ],
    "must_not": [
      {"term": {"seller_id": "blocked_sellers"}}
    ],
    "minimum_should_match": 1
  }
}
```

**2. Job Portal:**
- **must**: Required skills and experience level
- **should**: Preferred skills (each boosts score), remote work, benefits
- **filter**: Location, salary range, job type (full-time/contract)
- **must_not**: Expired posts, companies user blocked
- **minimum_should_match**: At least 2 preferred skills

**3. News Aggregator:**
- **must**: Query terms in title or body
- **should**: Recent articles, from followed sources, trending topics
- **filter**: Language, publication date range, content type
- **must_not**: Already read, hidden sources, paywalled

**4. Healthcare Search:**
- **must**: Symptom or condition keywords
- **should**: Specialist type, highly rated, nearby
- **filter**: Accepts insurance, availability, within distance
- **must_not**: Closed practices, blacklisted providers

**5. E-learning Platform:**
- **must**: Course topic match
- **should**: User's skill level, popular courses, instructor rating
- **filter**: Course duration, price range, has certificate
- **must_not**: Already completed, prerequisites not met
- **minimum_should_match**: "50%"

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

**Detailed Explanation:**
Sorting by `_score` explicitly controls relevance ordering. Key points:

**Score Sorting:**
- **Default behavior**: Without explicit sort, results are sorted by `_score` desc automatically
- **Ascending order**: Least relevant documents first (unusual, rarely useful)
- **Descending order**: Most relevant first (default and most common)

**When Score Matters:**
- Full-text search queries (match, multi_match)
- Bool queries with should clauses
- Function score queries
- Boosted queries

**When Score Doesn't Matter:**
- Filter-only queries (all docs score 0 or 1)
- Term/terms queries without scoring context
- Constant score queries

**Performance Note:**
- Sorting by _score is fast when it's the only sort criterion
- Combining _score with field sorts requires score calculation for all results

**Business Use Cases:**
- **Least relevant first**: Debug queries, find low-quality matches for ML training
- **Most relevant first** (default): Standard search results, recommendations
- **Score + recency**: Combine relevance with time-based sorting

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

**Detailed Explanation:**
Sorting by date fields overrides relevance-based ordering. Key parameters:

**Date Sorting Parameters:**
- **order**: `asc` (oldest first) or `desc` (newest first)
- **mode**: For multi-value date fields - `min`, `max`, `avg`, `median`
- **missing**: Where to place docs without this field - `_first` or `_last`
- **format**: Date format for sorting (rarely needed)
- **numeric_type**: Treat dates as `long` or `double` for performance

**Date Field Types:**
- **date**: Standard date field (milliseconds since epoch)
- **date_nanos**: Nanosecond precision
- **String dates**: Must be in proper format or use `format` parameter

**Important Notes:**
- Sorting by date disables score-based ordering unless score is also in sort criteria
- Date fields use doc values for fast sorting (enabled by default)
- Sorting by dates is very efficient (column-oriented storage)

**Business Use Cases:**
- **News/blog**: Most recent articles first
- **E-commerce**: New arrivals, recently updated products
- **Logging**: Latest logs first for troubleshooting
- **Tickets**: Oldest unresolved tickets first (FIFO processing)
- **Events**: Upcoming events sorted chronologically
- **Social media**: Latest posts/updates
- **Audit logs**: Chronological audit trail

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

**Detailed Explanation:**
Multi-level sorting applies multiple sort criteria in order. How it works:

**Sorting Precedence:**
1. **Primary sort**: `FIRST_SEEN_DATE` desc - newest first
2. **Secondary sort**: `_score` asc - if dates are equal, least relevant first
3. **Tie-breaker**: If both match, `_id` is used implicitly

**Multi-Sort Patterns:**
```json
[
  {"featured": "desc"},           // Featured items first
  {"_score": "desc"},             // Then by relevance
  {"price": "asc"},               // Then by price low to high
  {"created_at": "desc"}          // Then by newest
]
```

**Performance Considerations:**
- Each sort level adds computation overhead
- Use fields with doc_values enabled
- First sort criterion is most impactful
- Limit to 3-4 sort levels maximum for performance

**Common Multi-Sort Patterns:**

**1. Featured + Relevance + Price:**
```json
{"sort": [
  {"is_featured": "desc"},
  {"_score": "desc"},
  {"price": "asc"}
]}
```

**2. Category + Rating + Date:**
```json
{"sort": [
  {"category.keyword": "asc"},
  {"rating": "desc"},
  {"created_at": "desc"}
]}
```

**3. Distance + Rating:**
```json
{"sort": [
  {"_geo_distance": {
    "location": "40.7128,-74.0060",
    "order": "asc"
  }},
  {"rating": "desc"}
]}
```

**Business Use Cases:**
- **E-commerce**: Featured products, then by relevance, then by price/rating
- **Job boards**: Relevance first, then recency, then salary
- **Real estate**: Location match, then by price, then by square footage
- **Restaurants**: Distance first, then rating, then price range
- **Hotel booking**: Availability, price, rating, distance
- **Event listings**: Date/time, then relevance, then popularity
- **Marketplace**: Seller rating, price, shipping time
- **Content feeds**: Personalization score, engagement, recency

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

**Detailed Explanation:**
**INCORRECT APPROACH** - Attempting to sort on a `text` field fails or produces unexpected results:

**Why Text Fields Can't Be Sorted:**
- **Text fields are analyzed**: "Machine Learning" → ["machine", "learning"]
- **Multiple tokens**: OpenSearch doesn't know which token to use for sorting
- **No doc_values**: Text fields don't have column-oriented storage for sorting by default
- **Error or unpredictable**: May throw error or sort by first token (inconsistent)

**The Problem:**
```json
// Document 1: "Zebra Animal"
// Indexed as: ["zebra", "animal"]
// Sort by which? "zebra" or "animal"?

// Document 2: "Apple Fruit"
// Indexed as: ["apple", "fruit"]
```

**Solution:** Use the `.keyword` sub-field (see next example)

**Business Impact:**
- User expectations broken ("Zebra" not appearing in Z section)
- Unpredictable ordering in listings
- Different results across OpenSearch versions

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

**Detailed Explanation:**
**CORRECT APPROACH** - Sort using the `.keyword` sub-field which preserves the original string:

**How Keyword Fields Work:**
- **Not analyzed**: "Machine Learning" stored as single token "Machine Learning"
- **Exact value**: Preserves capitalization, spaces, special characters
- **Doc values enabled**: Optimized column-oriented storage for sorting/aggregations
- **Sortable**: Single value per document, deterministic ordering

**Keyword vs Text for Sorting:**
```json
// Text field (analyzed)
"Machine Learning" → ["machine", "learning"] // Can't sort

// Keyword field (not analyzed)  
"Machine Learning" → "Machine Learning" // Can sort alphabetically
```

**Multi-field Pattern:**
```json
"mappings": {
  "properties": {
    "product_name": {
      "type": "text",              // For search
      "fields": {
        "keyword": {                // For sorting/aggregations
          "type": "keyword"
        }
      }
    }
  }
}
```

**Performance:**
- Keyword sorting is fast (doc values are cached)
- Memory efficient (column-oriented)
- Supports all collation/locale options

**Business Use Cases:**
- **Product listings**: Sort by product name alphabetically
- **User directories**: Sort by username, email, full name
- **Category navigation**: Alphabetical category lists
- **Brand filtering**: Sort brands A-Z
- **Location sorting**: City/state alphabetical order
- **Document management**: Sort by filename, title
- **Dropdown menus**: Sorted options for better UX

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

**Detailed Explanation:**
**DISCOURAGED APPROACH** - Direct fuzzy query on text fields is problematic:

**Problems with Fuzzy on Text:**
- **Token-by-token matching**: Fuzzy applies to each analyzed token independently
- **Unpredictable**: Results depend on analyzer behavior
- **Poor scoring**: Doesn't consider term frequency properly
- **Performance**: Less optimized than match with fuzziness

**Why Match with Fuzziness is Better:**
```json
// ❌ Don't use:
{"fuzzy": {"description": {"value": "machne learning"}}}

// ✅ Use instead:
{"match": {"description": {
  "query": "machne learning",
  "fuzziness": "AUTO"
}}}
```

**Match with Fuzziness Advantages:**
- Respects field analyzer
- Better scoring algorithm
- Works with phrases
- Handles multiple terms correctly

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

**Detailed Explanation:**
Fuzzy query on keyword fields is useful for exact-match fields with typos. Key parameters:

**Fuzziness Parameters:**
- **value**: The search term (not analyzed)
- **fuzziness**: Edit distance - `0`, `1`, `2`, or `AUTO`
  - AUTO: 0 for 1-2 chars, 1 for 3-5 chars, 2 for 6+ chars
- **prefix_length**: Characters at start that must match exactly (default: 0)
- **max_expansions**: Max number of terms to match (default: 50)
- **transpositions**: Allow swapping adjacent chars (default: true)

**Edit Distance (Levenshtein):**
- **0**: No errors allowed (exact match)
- **1**: One character difference (insert, delete, substitute, transpose)
- **2**: Two character differences

**Examples:**
```json
// Fuzziness 1
"machine" matches: "machne", "machin", "machien"

// Fuzziness 2
"machine" matches: "macine", "machene", "mahcine"
```

**Prefix Length Optimization:**
```json
{
  "fuzzy": {
    "product_sku.keyword": {
      "value": "PROD12345",
      "fuzziness": 1,
      "prefix_length": 4  // "PROD" must match exactly
    }
  }
}
```

**When to Use Fuzzy on Keyword:**
- **SKU/Product codes**: Handle typos in exact codes
- **Email addresses**: Find emails with typos
- **Username search**: Tolerate spelling errors
- **Tag matching**: Flexible tag search
- **Exact phrase with typos**: When keyword field stores phrases

**When NOT to Use:**
- Full-text search (use match with fuzziness)
- Long text content
- When performance is critical (fuzzy is slower)

**Business Use Cases:**
- **SKU lookup**: "PROD-1234" finds "PROD-1235" or "PROD-12*34"
- **Email search**: "john@gmail" matches "john@gmai"
- **Username search**: "johndoe" matches "jhondoe" or "john_doe"
- **Product code**: Tolerate data entry errors in codes
- **Tag search**: Flexible tag matching for categorization
- **Order number**: Find orders with minor typos in order ID

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

**Detailed Explanation:**
Constant score query wraps a filter query and assigns the same score to all matching documents. Key aspects:

**Purpose:**
- **Uniform scoring**: All matching documents get the same score (the boost value)
- **Filter + score**: Combines filter efficiency with scoring capability
- **No relevance calculation**: Skips expensive scoring computations
- **Consistent ordering**: Documents score equally, sorted by other criteria or document order

**Parameters:**
- **filter**: Any query clause (will be executed in filter context)
- **boost**: Score assigned to all matching documents (default: 1.0)

**How It Works:**
```json
// Without constant_score
{
  "bool": {
    "filter": {"term": {"status": "active"}}
  }
}
// All docs score 0 (no scoring)

// With constant_score
{
  "constant_score": {
    "filter": {"term": {"status": "active"}},
    "boost": 1.0
  }
}
// All docs score 1.0
```

**Use Cases:**

**1. Equal Priority Items:**
```json
{
  "constant_score": {
    "filter": {"term": {"category": "featured"}},
    "boost": 2.0
  }
}
// All featured items boost by 2.0 equally
```

**2. Combining with Other Queries:**
```json
{
  "bool": {
    "should": [
      {"match": {"title": "laptop"}},  // Variable score
      {
        "constant_score": {           // Constant boost for premium
          "filter": {"term": {"is_premium": true}},
          "boost": 1.5
        }
      }
    ]
  }
}
```

**3. Multi-tier Boosting:**
```json
{
  "bool": {
    "should": [
      {"constant_score": {"filter": {"term": {"tier": "gold"}}, "boost": 3}},
      {"constant_score": {"filter": {"term": {"tier": "silver"}}, "boost": 2}},
      {"constant_score": {"filter": {"term": {"tier": "bronze"}}, "boost": 1}}
    ]
  }
}
```

**Performance Benefits:**
- Faster than scoring queries (no TF-IDF calculation)
- Filter clauses are cacheable
- Efficient for large result sets
- Good for binary features (is_featured, is_premium)

**Business Use Cases:**
- **Featured content**: Boost all featured items equally without complex scoring
- **Membership tiers**: Uniform boost for gold/silver/bronze members
- **Promotional tags**: Equal boost for items on sale or in promotions
- **Geographic preference**: Boost all items from specific regions equally
- **Vendor priority**: Give partner/verified vendors consistent boost
- **Content freshness**: Uniform boost for content from last 24 hours
- **Inventory priority**: Boost in-stock items uniformly over out-of-stock
- **Compliance filtering**: Filter required conditions while maintaining score

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

**Detailed Explanation:**
Named queries assign identifiers to query clauses to track which parts of the query matched for each document.

**Key Features:**
- **_name parameter**: Add to any query clause
- **matched_queries field**: Response includes array of matched query names
- **Debugging**: Understand why documents matched
- **Analytics**: Track which query components are effective
- **A/B testing**: Measure impact of different query clauses

**Response Format:**
```json
{
  "hits": {
    "hits": [
      {
        "_id": "1",
        "_score": 2.5,
        "_source": {...},
        "matched_queries": ["match_task_name", "filter_date"]
      }
    ]
  }
}
```

**Example with Multiple Named Queries:**
```json
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "title": {
              "query": "laptop",
              "_name": "title_match"
            }
          }
        }
      ],
      "should": [
        {
          "term": {
            "brand": {
              "value": "Dell",
              "_name": "brand_dell"
            }
          }
        },
        {
          "range": {
            "price": {
              "lte": 1000,
              "_name": "affordable"
            }
          }
        }
      ],
      "filter": [
        {
          "term": {
            "in_stock": {
              "value": true,
              "_name": "available"
            }
          }
        }
      ]
    }
  }
}
```

**Use Cases:**

**1. Understanding Match Reasons:**
- See which query components triggered matches
- Debug complex bool queries
- Verify filter logic

**2. Analytics and Optimization:**
- Track which should clauses are most effective
- Measure impact of boosting rules
- Identify underperforming query components

**3. Personalization Feedback:**
- Know which user preferences influenced results
- Track feature effectiveness
- Adjust ML models based on match patterns

**4. A/B Testing:**
- Compare effectiveness of different query variations
- Measure click-through rates per query component
- Optimize search relevance iteratively

**Business Use Cases:**
- **Search relevance tuning**: Identify which query clauses contribute to good results
- **Product recommendations**: Track which recommendation signals fired
- **Content discovery**: Understand match reasons for user feedback
- **Debugging production issues**: Diagnose why unexpected results appeared
- **Query optimization**: Remove ineffective query clauses
- **Feature engineering**: Identify valuable signals for ML models
- **Business intelligence**: Report on which filters/boosts are most used
- **Personalization**: Track which user preferences influence results

### 77. Named Queries Score
```bash
POST tasks/_search?include_named_queries_score
```
**Explanation:**
Requests the detailed score contribution for each named query.

**Detailed Explanation:**
Extends named queries to include individual score contributions from each named clause.

**Enhanced Response:**
```json
{
  "hits": {
    "hits": [
      {
        "_id": "1",
        "_score": 5.2,
        "matched_queries": [
          {
            "name": "title_match",
            "score": 3.5
          },
          {
            "name": "brand_boost",
            "score": 1.7
          }
        ]
      }
    ]
  }
}
```

**Value Proposition:**
- **Score breakdown**: See exact contribution of each clause
- **Debugging**: Understand scoring behavior
- **Optimization**: Identify which boosts are too strong/weak
- **Transparency**: Explain to users why results ranked as they did

**Analysis Use Cases:**
```json
// Find if boost is too strong
title_match: 0.5 (good baseline)
brand_boost: 10.0 (overwhelming other signals)

// Adjust boost values
"boost": 10.0 → "boost": 2.0
```

**Business Use Cases:**
- **Relevance tuning**: Precisely adjust boost values
- **Explain search results**: Show users why items ranked high
- **Quality assurance**: Verify scoring behaves as designed
- **Machine learning**: Feature importance analysis
- **Stakeholder reporting**: Demonstrate impact of business rules
- **Compliance**: Audit trail for search result ranking

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

**Detailed Explanation:**
Intervals query provides powerful, precise control over term positions and ordering in text. It's more sophisticated than match_phrase.

**Key Concepts:**
- **Position-aware**: Matches based on exact term positions
- **Ordered matching**: Terms must appear in specified sequence
- **Gap control**: Define maximum distance between terms
- **Complex patterns**: Combine multiple interval rules

**Interval Rule Types:**

**1. match**: Simple term or phrase
```json
{"match": {"query": "my favorite food"}}
```

**2. any_of**: Match any of several intervals (OR)
```json
{"any_of": {
  "intervals": [
    {"match": {"query": "hot water"}},
    {"match": {"query": "cold porridge"}}
  ]
}}
```

**3. all_of**: Match all intervals (AND, order doesn't matter)
```json
{"all_of": {
  "intervals": [
    {"match": {"query": "quick"}},
    {"match": {"query": "brown"}},
    {"match": {"query": "fox"}}
  ],
  "ordered": false
}}
```

**4. prefix**: Term prefix matching
```json
{"prefix": {"prefix": "comput"}}
```

**5. wildcard**: Pattern matching
```json
{"wildcard": {"pattern": "m*n"}}
```

**6. fuzzy**: Fuzzy term matching
```json
{"fuzzy": {"term": "machne", "fuzziness": 1}}
```

**Combining Intervals:**
```json
{
  "intervals": {
    "description": {
      "all_of": {
        "intervals": [
          {"match": {"query": "my favorite"}},
          {"any_of": {
            "intervals": [
              {"match": {"query": "hot water"}},
              {"match": {"query": "cold porridge"}}
            ]
          }}
        ],
        "ordered": true,
        "max_gaps": 5
      }
    }
  }
}
```

**Parameters:**
- **ordered**: Whether intervals must appear in order (default: true for all_of)
- **max_gaps**: Maximum positions between intervals
- **filter**: Additional constraints on the interval

**Business Use Cases:**
- **Legal documents**: "breach" followed by "contract" within 10 words
- **Medical records**: "heart" near "attack" but not near "prevention"
- **Compliance**: Specific phrase patterns in regulations
- **Technical documentation**: Code patterns or API sequences
- **Academic search**: Citations or reference patterns
- **Contract analysis**: Clause patterns like "party A" followed by "agrees to"

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

**Detailed Explanation:**
Applying intervals query to find specific word sequences in task descriptions.

**Example Pattern:**
```json
{
  "intervals": {
    "RELATED_TASKS_NAMES_LIST": {
      "all_of": {
        "intervals": [
          {"match": {"query": "code"}},
          {"any_of": {
            "intervals": [
              {"match": {"query": "search"}},
              {"match": {"query": "simplification"}}
            ]
          }}
        ],
        "ordered": true
      }
    }
  }
}
```

**This matches:**
- "code search"
- "code simplification"  
- "code optimization and search"
- "code quality and simplification"

**Business Use Cases:**
- **Task management**: Find tasks with specific action sequences
- **Project tracking**: Match milestone patterns
- **Workflow search**: Identify process steps
- **Documentation**: Find instruction sequences

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

**Detailed Explanation:**
Searching for "code quality" followed by related terms.

**Pattern Example:**
```json
{
  "intervals": {
    "RELATED_TASKS_NAMES_LIST": {
      "all_of": {
        "intervals": [
          {"match": {"query": "code quality"}},
          {"any_of": {
            "intervals": [
              {"match": {"query": "improvement"}},
              {"match": {"query": "simplification"}}
            ]
          }}
        ],
        "max_gaps": 3,
        "ordered": true
      }
    }
  }
}
```

**Matches:**
- "code quality improvement"
- "code quality and performance improvement"
- "code quality simplification"

**Business Use Cases:**
- **Code review**: Find specific improvement patterns
- **Technical debt**: Identify quality-related tasks
- **Sprint planning**: Search for quality initiatives

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

**Detailed Explanation:**
Combining interval matching with fuzzy term matching for typo tolerance.

**Example:**
```json
{
  "intervals": {
    "description": {
      "all_of": {
        "intervals": [
          {"match": {"query": "code"}},
          {"fuzzy": {
            "term": "serch",
            "fuzziness": "AUTO"
          }}
        ],
        "ordered": true
      }
    }
  }
}
```

**Matches:** "code search" even with typo "serch"

**Business Use Cases:**
- **User-generated content**: Handle common typos in search
- **OCR text**: Match scanned documents with OCR errors
- **International users**: Tolerate transliteration variations

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

**Detailed Explanation:**
Using prefix matching within interval queries for partial word matching.

**Example:**
```json
{
  "intervals": {
    "description": {
      "all_of": {
        "intervals": [
          {"match": {"query": "code"}},
          {"prefix": {"prefix": "impr"}}
        ],
        "max_gaps": 2
      }
    }
  }
}
```

**Matches:**
- "code improvements"
- "code improvisation"
- "code improved"

**Business Use Cases:**
- **Stemming alternative**: Match word variations without heavy analysis
- **Autocomplete in search**: Find phrases with partial words
- **Product search**: Match partial product names in phrases

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

**Detailed Explanation:**
Wildcard patterns within intervals for flexible matching.

**Example:**
```json
{
  "intervals": {
    "description": {
      "all_of": {
        "intervals": [
          {"wildcard": {"pattern": "code*"}},
          {"match": {"query": "optimization"}}
        ],
        "ordered": true
      }
    }
  }
}
```

**Matches:**
- "code optimization"
- "codebase optimization"
- "coding optimization"

**Business Use Cases:**
- **Product variants**: Match product codes with variations
- **Technical search**: Find related technical terms
- **Flexible matching**: When exact terms vary but pattern is consistent

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

**Detailed Explanation:**
Interval filters allow complex constraints on matched intervals.

**Filter Types:**

**1. not_containing**: Interval must NOT contain term
```json
{"not_containing": {"match": {"query": "salty"}}}
```

**2. containing**: Interval must contain term
```json
{"containing": {"match": {"query": "delicious"}}}
```

**3. not_contained_by**: Interval must NOT be contained by pattern
```json
{"not_contained_by": {"match": {"query": "not recommended"}}}
```

**4. contained_by**: Interval must be contained by pattern
```json
{"contained_by": {"match": {"query": "highly recommended"}}}
```

**5. not_overlapping**: Intervals must not overlap
**6. before**: First interval must appear before second
**7. after**: First interval must appear after second

**Complex Example:**
```json
{
  "intervals": {
    "review_text": {
      "match": {
        "query": "great product",
        "max_gaps": 5,
        "filter": {
          "not_containing": {
            "match": {"query": "but"}
          },
          "containing": {
            "match": {"query": "recommend"}
          }
        }
      }
    }
  }
}
```

**Matches:** "great product, highly recommend"
**Doesn't match:** "great product but expensive"

**Business Use Cases:**
- **Sentiment analysis**: Find positive phrases without negation
- **Contract clauses**: Match clauses with required terms, excluding certain conditions
- **Product reviews**: Find recommendations without caveats
- **Legal search**: Exclude conflicting terms from matches
- **Medical records**: Find diagnoses without excluding conditions
- **Quality control**: Match approval statements without rejection terms

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

**Detailed Explanation:**
Query string query uses Lucene query syntax, allowing users to write complex queries with operators. Key features:

**Lucene Query Syntax:**
- **AND**: Both terms must match
- **OR**: At least one term must match
- **NOT**: Term must not match
- **+**: Term must be present (required)
- **-**: Term must not be present (prohibited)
- **"phrase"**: Exact phrase match
- **field:value**: Search specific field
- **wildcards**: `*` (multiple chars), `?` (single char)
- **fuzzy**: `term~` or `term~2`
- **proximity**: `"phrase"~5`
- **ranges**: `[1 TO 100]`, `{1 TO 100}`
- **boosting**: `term^2`
- **grouping**: `(term1 OR term2) AND term3`

**Parameters:**
- **query**: The Lucene query string
- **default_field**: Field to search if none specified (default: _all)
- **fields**: Array of fields to search
- **default_operator**: AND or OR (default: OR)
- **analyzer**: Analyzer for query text
- **allow_leading_wildcard**: Allow `*term` queries (default: true)
- **analyze_wildcard**: Analyze wildcards (default: false)
- **enable_position_increments**: For phrase queries (default: true)
- **fuzziness**: AUTO, 0, 1, or 2
- **fuzzy_max_expansions**: Limit fuzzy term expansions (default: 50)
- **fuzzy_prefix_length**: Required exact prefix (default: 0)
- **phrase_slop**: Slop for phrase queries (default: 0)
- **boost**: Score multiplier (default: 1.0)
- **auto_generate_synonyms_phrase_query**: Use synonyms (default: true)
- **lenient**: Ignore format errors (default: false)

**Example: (Ui5) AND (blockchain)**
- Matches documents containing both "Ui5" AND "blockchain"
- Both terms are analyzed (lowercased)
- Order doesn't matter

**Advanced Syntax Examples:**
```json
// Multiple operators
"(javascript OR python) AND (tutorial OR guide) NOT beginner"

// Field-specific
"title:search AND author:john"

// Wildcards
"comp* AND (search OR find)"

// Fuzzy
"machne~ AND learning"

// Proximity
"\"machine learning\"~3"

// Boosting
"python^2 OR java"

// Ranges
"price:[100 TO 500] AND rating:[4 TO *]"

// Complex
"(title:(laptop OR notebook) AND price:[500 TO 1000]) OR featured:true^2"
```

**When to Use Query String:**
- **Power users**: Advanced search interfaces for technical users
- **Admin tools**: Internal tools where admins understand syntax
- **Search boxes with syntax**: Apps like Slack, GitHub, Gmail search
- **Migration from Lucene**: Porting existing Lucene queries

**When NOT to Use:**
- **End users**: Average users don't understand Lucene syntax
- **Untrusted input**: Can cause parsing errors or performance issues
- **Simple searches**: Bool query is clearer and more controlled

**Security Considerations:**
- Validate user input carefully
- Use `lenient: true` to handle errors gracefully
- Consider timeouts for complex queries
- Limit wildcard and fuzzy usage

**Business Use Cases:**
- **Developer tools**: IDE search, code search, log analysis
- **Admin interfaces**: Internal search tools for support teams
- **Power user features**: Advanced search for experienced users
- **Email/message search**: Gmail-style search syntax
- **JIRA/issue tracking**: Complex issue queries
- **Legal e-discovery**: Complex boolean searches in documents
- **Data analysis**: Ad-hoc queries for data scientists

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

**Detailed Explanation:**
OR operator finds documents matching at least one term.

**Behavior:**
- Matches if document contains "Ui5" OR "blockchain" OR both
- Documents with both terms score higher
- Default operator can be changed to AND globally

**Scoring:**
- Documents matching both terms: Higher score
- Documents matching one term: Lower score
- More frequent terms contribute less to score

**Equivalent Bool Query:**
```json
{
  "bool": {
    "should": [
      {"match": {"RELATED_TASKS_NAMES_LIST": "Ui5"}},
      {"match": {"RELATED_TASKS_NAMES_LIST": "blockchain"}}
    ],
    "minimum_should_match": 1
  }
}
```

**Business Use Cases:**
- **Synonym search**: Match any of several related terms
- **Multi-keyword search**: Broad search across related concepts
- **Fallback matching**: If primary term doesn't match, try alternatives

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

**Detailed Explanation:**
Query string handles multi-word phrases in parentheses.

**Phrase Handling:**
- "Civil engineering" treated as phrase (words must be adjacent)
- Equivalent to: `"Civil engineering" OR theses`
- Matches:
  - Documents with phrase "Civil engineering"
  - Documents with term "theses"
  - Documents with both

**For Exact Phrase:**
```json
{"query": "\"Civil engineering\" OR theses"}
```

**Business Use Cases:**
- **Academic search**: Find research on specific topics
- **Multi-discipline search**: Match across different fields
- **Category matching**: Broad category or specific item

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

**Detailed Explanation:**
Searching across multiple fields using wildcards.

**Fields Parameter:**
- **Wildcards**: `RELATED_TASKS*` matches all fields starting with "RELATED_TASKS"
- **Multiple fields**: `["title", "description", "tags"]`
- **Field boosting**: `["title^3", "description^2", "tags"]`
- **No default_field**: Must specify fields or use `default_field`

**Example with Boosting:**
```json
{
  "query_string": {
    "query": "search optimization",
    "fields": [
      "title^3",
      "description^2",
      "content"
    ]
  }
}
```

**Matches in title are 3x more important than content**

**Business Use Cases:**
- **Multi-field search**: Search across title, description, and content
- **Relevance tuning**: Boost matches in important fields
- **Flexible schema**: Use wildcards to match dynamic field patterns
- **Hierarchical data**: Search nested or dynamic fields

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

**Detailed Explanation:**
Using wildcards within query string syntax. Note the escaping:

**Wildcard Syntax:**
- **Asterisk (*)**: Matches zero or more characters
- **Question mark (?)**: Matches exactly one character
- **Escaping**: Use `\\` to escape special characters in JSON

**Examples:**
```json
// Match any word starting with "comp"
"comp*"  // computer, computing, compile

// Match variations
"test?"  // tests, testy

// Multiple wildcards
"*search*"  // search, researching, searchable

// Escaped wildcard (literal *)
"2\\*2"  // matches "2*2"
```

**Performance Warning:**
- **Leading wildcards** (`*term`) are expensive
- Disable with `allow_leading_wildcard: false`
- **Multiple wildcards** can cause slow queries
- Use prefix queries when possible

**Wildcard vs Other Approaches:**
```json
// Wildcard in query_string
{"query_string": {"query": "comp*"}}

// Dedicated wildcard query (better for single field)
{"wildcard": {"field": {"value": "comp*"}}}

// Prefix query (fastest for prefix matching)
{"prefix": {"field": "comp"}}
```

**Business Use Cases:**
- **Product code search**: Partial SKU matching like "PROD-*-2024"
- **Partial name search**: "John*" matches Johnson, Johansen
- **Flexible matching**: When exact term is unknown
- **Pattern matching**: File paths, URLs, technical identifiers
- **International names**: Handle spelling variations

**Best Practices:**
- Avoid leading wildcards when possible
- Use prefix queries for simple prefix matching
- Set `allow_leading_wildcard: false` for public-facing search
- Monitor query performance
- Consider edge n-grams for autocomplete instead of wildcards
- Use `max_determinized_states` to limit complex wildcards
