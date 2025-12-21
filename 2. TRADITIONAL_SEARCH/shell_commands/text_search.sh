# Retrieve the mapping definitions for the 'ecommerce' index
GET ecommerce/_mapping

# Perform a search on the 'ecommerce' index matching all documents (default behavior)
POST ecommerce/_search

# Perform a search on the 'ecommerce' index with an explicit match_all query
# match_all: Matches all documents. Default query if none is specified.
# Returns all documents with a score of 1.0.
GET /ecommerce/_search
{
  "query": {
    "match_all": {}
  }
}

# Search for "Men's Shoes" and collapse results by the "type" field to show one representative per type
# collapse: Allows collapsing search results based on field values.
# field: The field to collapse on.
# sort: Sorts the results. In this case, sorts the collapsed groups by 'day_of_week'.
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

#Paginate
# Search for manufacturer "Elitelligence" returning results 0-10
# from: Starting offset (default 0).
# size: Number of hits to return (default 10).
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

# Search with pagination parameters in the URI
GET ecommerce/_search?from=0&size=10

# Initialize a scroll search context for 10 minutes, retrieving 5 documents per batch
# scroll: Specifies how long the search context should be kept alive (e.g., 10m = 10 minutes).
# size: Number of results per batch.
GET ecommerce/_search?scroll=10m
{
  "size": 5
}

# Retrieve the next batch of results using the scroll ID
GET _search/scroll
{
  "scroll": "10m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAAAUWdmpUZDhnRFBUcWFtV21nMmFwUGJEQQ=="
}

# Search after
# Initial search to retrieve the first page of results and sort values
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

# Fetch the next page of results using the sort values from the previous response in 'search_after'
# search_after: Retrieves the next page of hits using a set of sort values from the previous page.
# Requires the same 'sort' order as the previous request.
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


# PIT (point in time)
# Create a Point In Time (PIT) to preserve the index state for consistent pagination
POST /ecommerce/_search/point_in_time?keep_alive=100m


# Search using the PIT ID and 'search_after' for deep pagination
# pit: Point In Time configuration.
#   id: The ID of the PIT to use.
#   keep_alive: Extends the validity of the PIT.
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


# Search
# Another example of using 'search_after' for pagination
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

# Search matching all documents, sorted by manufacturer in descending order
GET ecommerce/_search
{
   "query" : {
      "match_all": {}
   },
   "sort" : [
      {"manufacturer.keyword": {"order" : "desc"}}
   ]
}

# Highlight
# Search for "blue" in product name and highlight matches with default tags (<em>)
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

# Search for "blue" and highlight matches with custom tags (<strong>)
# highlight: Highlights search terms in the results.
#   pre_tags/post_tags: Custom tags to wrap highlighted text (default is <em>).
#   fields: Specifies which fields to highlight.
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

# AUTOCOMPLETE
# Delete the 'ecommerce' index to prepare for autocomplete setup
DELETE ecommerce

# Use python script create_ecommerce_original_edge_ngrams.py to create mapping and load data

# Test the 'autocomplete' analyzer to see how it tokenizes the text "summer"
POST ecommerce/_analyze
{
  "analyzer": "autocomplete",
  "text": "summer"
}

# Search using the 'autocomplete' analyzer on the query string (matches n-grams)
# analyzer: Overrides the search analyzer. Here, 'autocomplete' produces n-grams from the query "sum".
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

# Too many hits above : Use the standard analyzer at search time. Otherwise, the search query splits into edge n-grams and you get results for everything that matches s, u, and m etc

# Search using 'standard' analyzer on query string to match against indexed n-grams (better for prefix search)
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

# Fuzzy search
# Delete the 'ecommerce' index to prepare for fuzzy search setup
DELETE ecommerce
# Create 'ecommerce' index with 'completion' type for suggesters
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

# Use python script create_ecommerce_original_edge_ngrams.py to create mapping and load data

# Use completion suggester to find suggestions for prefix "summer"
# suggest: Defines a suggester execution.
#   prefix: The prefix to search for.
#   completion: The type of suggester (optimized for speed).
#     field: The field to suggest from (must be type 'completion').
#     size: Max number of suggestions.
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

# Misspelings 

# Use completion suggester with fuzziness to find suggestions for misspelled prefix "smmer"
# fuzzy: Enables fuzzy matching for the completion suggester.
#   fuzziness: "AUTO" allows edit distance based on term length.
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

# Regex
# Use completion suggester with regex prefix "sum*"
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

# SEARCH AS YOU TYPE
# Delete 'ecommerce' index to prepare for search_as_you_type setup
DELETE ecommerce
# Create 'ecommerce' index with 'search_as_you_type' field type
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

# Multi-match query using 'bool_prefix' type on 'search_as_you_type' subfields for efficient prefix matching
# multi_match: Matches the same query against multiple fields.
# type: "bool_prefix" creates a bool query where the last term is a prefix query.
# fields: The fields to query. 'search_as_you_type' creates subfields like ._2gram, ._3gram.
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

# DID YOU MEAN
# Analyze text using the analyzer configured for 'products.produce_name'
GET ecommerce/_analyze
{
  "text": "Casual lace-ups - dark brown , Basic T-shirt - white",
  "field": "products.produce_name"
}

#Misspelt
# Use term suggester to find corrections for misspelled word "blzr"
# term: The term suggester looks for terms that are similar to the provided text (spell check).
#   text: The text to find suggestions for.
#   field: The field to check against.
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

# Use multiple term suggesters in a single request
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

#Phrase suggestor
# Create 'books2' index with a custom shingle analyzer for phrase suggestion
PUT books2
{
  "settings": {
    "index": {
      "analysis": {
        "analyzer": {
          "trigram": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
              "lowercase",
              "shingle"
            ]
          }
        },
        "filter": {
          "shingle": {
            "type": "shingle",
            "min_shingle_size": 2,
            "max_shingle_size": 3
          }
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "trigram": {
            "type": "text",
            "analyzer": "trigram"
          }
        }
      }
    }
  }
}

# Index a document into 'books2'
PUT books2/_doc/1
{
  "title": "Design Patterns"
}

# Index another document into 'books2'
PUT books2/_doc/2
{
  "title": "Software Architecture Patterns Explained"
}

# Use phrase suggester to find corrections for "design paterns"
# phrase: The phrase suggester adds logic to select entire corrected phrases instead of individual terms.
#   field: The field to check against (often uses shingle filters).
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

# Use phrase suggester with highlighting for the corrected phrase
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

# RETRIEVE SPECIFIC FIELDS

# Disable source
# Search returning only metadata (id, score, etc.) without the _source field
GET /ecommerce/_search
{
    "_source": false,
    "query": {
        "match_all": {}
  }
}

# source filtering
# Search returning specific fields in _source using includes/excludes
# _source: Controls which fields of the source document are returned.
#   includes: List of fields to include.
#   excludes: List of fields to exclude.
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

# Search returning specific stored fields (using 'fields' param) and disabling _source
GET /ecommerce/_search?pretty
{
    "_source": false,
    "fields": ["customer_last_name", "product*"],
    "query": {
        "match_all": {}
  }
}

## FEW MORE EXAMPLES
# Delete 'tasks' index
DELETE tasks

# Index task document 1
POST /tasks/_doc/1
{
  "TASK_NAME": "App & code optimization(1)",
  "RELATED_AI_DATA_NAMES_LIST": [
    "App Builder Pro"
  ],
  "RELATED_TASKS_NAMES_LIST": [
    "Code optimization",
    "AppStore optimization",
    "Software performance optimization",
    "Programming language optimization",
    "App development & deployment",
    "App development",
    "Performance optimization",
    "Ui5 code optimization",
    "Java code optimization",
    "Multilingual code optimization",
    "App design",
    "Project optimization",
    "React code optimization",
    "Swift code optimization",
    "Routine optimization",
    "Content optimization",
    "Model optimization",
    "App modernization",
    "App development guidance",
    "App development automation",
    "Blockchain code optimization",
    "Code refactoring",
    "Code quality improvement"
  ],
  "FIRST_SEEN_DATE": "Jan 8 2024",
  "RELATED_AI_DATA_IDS_LIST": [
    "36571"
  ]
}

# Index task document 2
POST /tasks/_doc/2
{
  "TASK_NAME": "Blockchain code optimization(1)",
  "RELATED_AI_DATA_NAMES_LIST": [
    "Solidity Sage"
  ],
  "RELATED_TASKS_NAMES_LIST": [
    "Blockchain coding support",
    "Code optimization",
    "Programming language optimization",
    "App & code optimization",
    "Blockchain analytics",
    "Swift code optimization",
    "Blockchain data analysis",
    "React code optimization",
    "Blockchain transactions analysis",
    "Blockchain education",
    "Multilingual code optimization",
    "Blockchain development consulting",
    "Code simplification",
    "Bitcoin simplification",
    "Blockchain security",
    "Code complexity analysis",
    "Instruction optimization",
    "Java code optimization",
    "Blockchain consulting",
    "Smart contract programming"
  ],
  "FIRST_SEEN_DATE": "Dec 23 2023",
  "RELATED_AI_DATA_IDS_LIST": [
    "18879"
  ]
}



# Index task document 3
POST /tasks/_doc/3
{
  "TASK_NAME": "Building codes research(3)",
  "RELATED_AI_DATA_NAMES_LIST": [
    "CA Title 24 Wizard",
    "Utah Building Code GPT",
    "UpCodes"
  ],
  "RELATED_TASKS_NAMES_LIST": [
    "Civil engineering research",
    "Building safety guidance",
    "Building design",
    "Building analysis",
    "Research papers coding",
    "Computer science research",
    "Sanitary engineering research",
    "Code testing",
    "Mechanical engineering research",
    "Construction project analysis",
    "Building advice",
    "Sustainable construction guidance",
    "Research papers exploration",
    "Engineering inquiries",
    "Academic research",
    "Research papers analysis",
    "Architectural insights",
    "Code security analysis",
    "Research",
    "Construction documents Q&A",
    "Code search",
    "Theses research",
    "Project coding",
    "Construction guidance",
    "Sustainable architecture guidance"
  ],
  "FIRST_SEEN_DATE": "Jul 2 2023",
  "RELATED_AI_DATA_IDS_LIST": [
    "15514",
    "25068",
    "5807"
  ]
}

# Retrieve mapping for 'tasks' index
GET tasks/_mapping

# Search all documents in 'tasks' index
POST tasks/_search
{
  "query": {
    "match_all": {}
  }
}

# MATCH_ALL

# Explicit match_all query on 'tasks' index
GET tasks/_search
{
  "query": {
    "match_all": {}
  }
}



# The key differences between using GET and POST for search queries are:
# Parameter limitations:
# GET requests have limitations on URL length (typically 2000-8000 characters), which can restrict complex search queries with many parameters.
# POST requests can send larger amounts of data in the request body, allowing for more complex search criteria.
# Caching:
# GET requests are cacheable by default, which can improve performance for repeated searches.
# POST requests are not cached by default, though this can be changed with additional headers.
# Bookmarking and sharing:
# GET requests put parameters in the URL, making searches easy to bookmark and share.
# POST request parameters are in the body, so searches are not as easily bookmarked or shared.
# Security:
# GET parameters are visible in the URL, which may expose sensitive data.
# POST parameters are in the request body, providing slightly more security for sensitive search criteria.
# Idempotency:
# GET is idempotent, meaning repeated requests should produce the same result.
# POST is not idempotent by default.
# Browser behavior:
# Browsers handle back/forward navigation and history better with GET requests.
# POST may cause issues with page reloads and navigation.
# Best practices:
# Use GET for simple searches with few parameters.
# Consider POST for complex searches, very long queries, or when sending sensitive data.
# Some APIs use POST to a /search endpoint as a compromise.

# MATCH vs. MATCH_PHRASE vs. MATCH_PHRASE_PREFIX vs. TERM

# Match query: searches for "Code optimization" in 'RELATED_TASKS_NAMES_LIST' (analyzed)
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "Code optimization"
    }
  },
  "fields" : ["*"]
}

# This also matches "Code optimization" as a substring (think about tokenization done by analyzer)
# Match query: searches for "Ui5 code optimization" (analyzed)
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "Ui5 code optimization"
    }
  },
  "fields" : ["*"]
}


# This returns only 1 document (since only document 1 has ui5 as a token)
# Match query: searches for "Ui5"
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "Ui5"
    }
  },
  "fields" : ["*"]
}

# If you want exact match, you can use .keyword field since RELATED_TASKS_NAMES_LIST is also a keyword field
# Exact match on keyword field
POST tasks/_search
{
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST.keyword": "Ui5 code optimization"
    }
  },
  "fields" : ["*"]
}

# OR you could use match_phrase
# Match phrase on keyword field (effectively exact match here)
POST tasks/_search
{
  "query": {
    "match_phrase": {
      "RELATED_TASKS_NAMES_LIST.keyword": "Ui5 code optimization"
    }
  },
  "fields" : ["*"]
}

# match_phrase with slop - don't care if certain words are in between, including reverse
# slop = 1 means at most 1 word can be in between 

# Match phrase with slop: allows "Ui5" and "optimization" to be separated by up to 1 word
# match_phrase: Matches a phrase (terms in specific order).
# slop: Number of positions terms can be moved to match the phrase (allows for gaps or reordering).
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

# To match in reverse, slop value should be 2 greater than number of words in between
# Match phrase with slop for reverse order
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

# PROXIMITY SEARCH
# Find documents that have tokens "code" and "optimization" within n words
# documents that have tokens "code" and "optimization" within n words, but score the ones that are more closer

# Proximity search using match_phrase with large slop
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


# match_phrase_prefix is useful when you want to match a prefix of a phrase
# Match phrase prefix: matches phrases starting with "theses"
# match_phrase_prefix: Matches a phrase where the last term is treated as a prefix.
POST tasks/_search
{
  "query": {
    "match_phrase_prefix": {
      "RELATED_TASKS_NAMES_LIST": "theses"
    }
  },
  "fields" : ["*"]
}

# TERM
# Term Query:
# Matches documents that contain an exact term in a specified field
# Searches for a single value
# Does not analyze the search term
# Term query: exact match for "theses" (must match token in inverted index)
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

# Simplified term query syntax
POST tasks/_search
{
  "query": {
    "term": {
      "RELATED_TASKS_NAMES_LIST": "theses"
    }
  },
  "fields" : ["RELATED_TASKS_NAMES_LIST"]
}

# at least one term match
# Terms query: matches documents containing "theses" OR "Multilingual"
POST tasks/_search
{
  "query": {
    "terms": {
      "RELATED_TASKS_NAMES_LIST": ["theses","Multilingual"]
    }
  },
  "fields" : ["RELATED_TASKS_NAMES_LIST"]
}

# FILTER
# Applies in the last stage of resultset (i.e. doesn't give server performance benefits, just prunes)

# Filter context: filter by term "theses" (no scoring)
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

# BOOL
# Must, Must_not, Should
# Bool query combining 'must' (match) and 'filter' (range) clauses
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

# MIX-MATCH
# Documents must satisfy all conditions in the "must" array
# Documents matching "should" conditions get a higher score
# Documents matching "must_not" conditions are excluded
# "minimum_should_match" ensures at least one "should" condition is met

# Complex bool query with must, should, must_not, and minimum_should_match
# bool: Combines multiple queries.
#   must: Clauses that MUST match (contributes to score).
#   should: Clauses that SHOULD match (increases score).
#   must_not: Clauses that MUST NOT match (filter context).
#   minimum_should_match: Specifies the number of 'should' clauses that must match.
GET /tasks/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "RELATED_TASKS_NAMES_LIST": "code" } },
        { "range": { "FIRST_SEEN_DATE": { "gte": "Jan 1 2023"} } }
      ],
      "should": [
        { "term": { "RELATED_TASKS_NAMES_LIST.keyword": "Ui5 code optimization" } }
      ],
      "must_not": [
        { "term": { "RELATED_AI_DATA_IDS_LIST.keyword": "12345" } }
      ],
      "minimum_should_match": 1
    }
  }
}

# PAGINATION
# from: 0, size: 10
# Deep pagination can be quite performance heavy, every results must be retrieved, scored and sorted

# Pagination: retrieve results 0-2
POST tasks/_search
{
  "from": 0,
  "size": 2,
  "query": {
    "match_all": {}
  }
}


# SORTING
# Sort by score in ascending order
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

# Sort by date field in descending order
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

# Multi-level sorting: first by date, then by score
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

# cannot sort on text field , exception: illegal_argument_exception
# because text is already split into terms/tokens and can't be sorted
# Attempt to sort on a text field (will fail)
POST tasks/_search
{
  "sort": {
    "RELATED_AI_DATA_NAMES_LIST": {"order": "desc"}
  },
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "code"
    }
  }
}

# workaround: use keyword field
# assumes that RELATED_AI_DATA_NAMES_LIST is a also a keyword field
# on an existing index, for the sort field that is already analyzed only as text, it cannot be updated unless index is deleted and mappings defined again
# Sort using the keyword subfield
POST tasks/_search
{
  "sort": {
    "RELATED_AI_DATA_NAMES_LIST.keyword": {"order": "desc"}
  },
  "query": {
    "match": {
      "RELATED_TASKS_NAMES_LIST": "code"
    }
  }
}


# FUZZY MATCHING - ONLY TERM LEVEL QUERY
# Fuzzy matching is a technique used in search queries to find results that are similar to the search term, even if the term is misspelled or has minor variations. Fuzzy matching can be useful for handling typos, variations in spelling, or other small differences in text data.
# Levnshtein edit distance: number of single-character edits (insertions, deletions, or substitutions) required to change one word into another

# An edit distance is the number of one-character changes needed to turn one term into another. These changes can include:

# Changing a character (box → fox)
# Removing a character (black → lack)
# Inserting a character (sic → sick)
# Transposing two adjacent characters (act → cat)


# Below will not work since RELATED_TASKS_NAMES_LIST is text
# Fuzzy query on text field (not supported, use match with fuzziness instead)
POST tasks/_search
{
  "query": {
    "fuzzy": {
      "RELATED_TASKS_NAMES_LIST": {
        "value": "code optmization",
        "fuzziness": "AUTO"
      }
    }
  }
}

# Below will work since RELATED_TASKS_NAMES_LIST.keyword is keyword
# Fuzzy query on keyword field
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

#https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#fuzziness
# Generally leave AUTO as value for fuzziness


## COMPOUND QUERIES
# List all indices
GET _cat/indices


# Bool query with multiple 'must' clauses (AND logic) and a filter
GET tasks/_search
{
  "query": { 
    "bool": { 
      "must": [
        { "match": { "RELATED_TASKS_NAMES_LIST":   "code"        }},
        { "match": { "TASK_NAME": "code" }}
      ],
      "filter": [ 
        { "range": { "FIRST_SEEN_DATE": { "gte": "01/01/2023" }}}
      ]
    }
  }
}

# Complex bool query with boosting
POST tasks/_search
{
  "query": {
    "bool" : {
      "must" : {
        "match" : { "TASK_NAME" : "code" }
      },
      "filter": {
        "match" : { "RELATED_TASKS_NAMES_LIST" : "code" }
      },
      "must_not" : {
        "range" : {
          "FIRST_SEEN_DATE" : { "gte" : "01/01/2023" }
        }
      },
      "should" : [
        { "term" : { "RELATED_AI_DATA_NAMES_LIST.keyword" : "App Builder Pro" } }
      ],
      "minimum_should_match" : 1,
      "boost" : 1.0
    }
  }
}

# bool filter: Queries specified under the filter element have no effect on scoring — scores are returned as 0
# match_all gives score of 1.0

# Filter only query (implicit match_all)
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

# Filter query with explicit match_all
GET tasks/_search
{
  "query": {
    "bool": {
      "must": {
        "match_all": {}
      },
      "filter": {
        "term": {
          "RELATED_TASKS_NAMES_LIST.keyword": "Code optimization"
        }
      }
    }
  }
}

# you can set a boost value to the constant_score query
# Constant score query: wraps a filter query and assigns a constant score to every matching document
GET tasks/_search
{
  "query": {
    "constant_score": {
      "filter": {
        "term": {
          "RELATED_TASKS_NAMES_LIST.keyword": "Code optimization"
        }
      },
      "boost": 1.2
    }
  }
}

## Named queries..to explain how much contribution each matching criteria provides to the score
# Named queries: assign names to query clauses to see which ones matched in the response
POST tasks/_search
{
  "query": {
    "bool" : {
      "must" : {
        "match" : { "TASK_NAME" : {"query":"code","_name":"match_task_name"} }
      },
      "filter": {
        "match" : { "RELATED_TASKS_NAMES_LIST" : {"query":"code","_name":"filter_task_related"} }
      },
      "must_not" : {
        "range" : {
          "FIRST_SEEN_DATE" : { "gte" : "02/01/2024","_name":"date_gt_2024" }
        }
      },
      "should" : [
        { "term" : { "RELATED_AI_DATA_NAMES_LIST.keyword" : "App Builder Pro"}}
      ],
      "minimum_should_match" : 1,
      "boost" : 1.0
    }
  }
}

# shows score contributed by matched clauses
# Request named queries score to see contribution of each named query to the final score
POST tasks/_search?include_named_queries_score
{
  "query": {
    "bool" : {
      "must" : {
        "match" : { "TASK_NAME" : {"query":"code","_name":"match_task_name"} }
      },
      "filter": {
        "match" : { "RELATED_TASKS_NAMES_LIST" : {"query":"code","_name":"filter_task_related"} }
      },
      "must_not" : {
        "range" : {
          "FIRST_SEEN_DATE" : { "gte" : "02/01/2024","_name":"date_gt_2024" }
        }
      },
      "should" : [
        { "term" : { "RELATED_AI_DATA_NAMES_LIST.keyword" : "App Builder Pro"}}
      ],
      "minimum_should_match" : 1,
      "boost" : 1.0
    }
  }
}

# BOOSTING QUERY
# DISJUNCTION MAX QUERY
# FUNCTION SCORE QUERY

# FULL TEXT QUERIES

# This search would match a my_text value of my favorite food is cold
# porridge but not when it's cold my favorite food is porridge.

#Valid rules include:

    # match
    # prefix
    # wildcard
    # fuzzy
    # all_of
    # any_of



# Intervals query: fine-grained control over order and proximity of matching terms
# intervals: Allows fine-grained control over the order and proximity of matching terms.
#   all_of: Matches if all sub-rules match.
#   ordered: If true, intervals must appear in the specified order.
#   max_gaps: Maximum number of positions between matching intervals.
#   any_of: Matches if any of the sub-rules match.
POST _search
{
  "query": {
    "intervals" : {
      "my_text" : {
        "all_of" : {
          "ordered" : true,
          "intervals" : [
            {
              "match" : {
                "query" : "my favorite food",
                "max_gaps" : 0,
                "ordered" : true
              }
            },
            {
              "any_of" : {
                "intervals" : [
                  { "match" : { "query" : "hot water" } },
                  { "match" : { "query" : "cold porridge" } }
                ]
              }
            }
          ]
        }
      }
    }
  }
}

# Intervals query on 'RELATED_TASKS_NAMES_LIST': "code" followed by "search" OR "simplification"
POST /tasks/_search
{
  "query": {
    "intervals" : {
      "RELATED_TASKS_NAMES_LIST" : {
        "all_of" : {
          "ordered" : true,
          "intervals" : [
            {
              "match" : {
                "query" : "code",
                "max_gaps" : 0,
                "ordered" : true
              }
            },
            {
              "any_of" : {
                "intervals" : [
                  { "match" : { "query" : "search" } },
                  { "match" : { "query" : "simplification" } }
                ]
              }
            }
          ]
        }
      }
    }
  }
}

# code quality with one space
# Intervals query: "code quality" followed by "improvement" OR "simplification"
POST /tasks/_search
{
  "query": {
    "intervals" : {
      "RELATED_TASKS_NAMES_LIST" : {
        "all_of" : {
          "ordered" : true,
          "intervals" : [
            {
              "match" : {
                "query" : "code quality",
                "max_gaps" : 0,
                "ordered" : true
              }
            },
            {
              "any_of" : {
                "intervals" : [
                  { "match" : { "query" : "improvement" } },
                  { "match" : { "query" : "simplification" } }
                ]
              }
            }
          ]
        }
      }
    }
  }
}

# with fuzzy
# Avoid mixing fuzziness with wildcards

# Intervals query with fuzzy matching: "code" followed by fuzzy "serch" OR "simplification"
POST /tasks/_search
{
  "query": {
    "intervals" : {
      "RELATED_TASKS_NAMES_LIST" : {
        "all_of" : {
          "ordered" : true,
          "intervals" : [
            {
              "match" : {
                "query" : "code",
                "max_gaps" : 0,
                "ordered" : true
              }
            },
            {
              "any_of" : {
                "intervals" : [
                  { "fuzzy" : { "term" : "serch" } },
                  { "match" : { "query" : "simplification" } }
                ]
              }
            }
          ]
        }
      }
    }
  }
}

# with prefix
# Intervals query with prefix matching: "code quality" followed by prefix "impr" OR "simplification"
POST /tasks/_search
{
  "query": {
    "intervals" : {
      "RELATED_TASKS_NAMES_LIST" : {
        "all_of" : {
          "ordered" : true,
          "intervals" : [
            {
              "match" : {
                "query" : "code quality",
                "max_gaps" : 0,
                "ordered" : true
              }
            },
            {
              "any_of" : {
                "intervals" : [
                  { "prefix" : { "prefix" : "impr" } },
                  { "match" : { "query" : "simplification" } }
                ]
              }
            }
          ]
        }
      }
    }
  }
}

# with wildcard
# This parameter supports two wildcard operators:

#     ?, which matches any single character
#     *, which can match zero or more characters, including an empty one

# Intervals query with wildcard: "code*" followed by "improvement" OR "analysis"
POST /tasks/_search
{
  "query": {
    "intervals" : {
      "RELATED_TASKS_NAMES_LIST" : {
        "all_of" : {
          "ordered" : true,
          "intervals" : [
            {
              "wildcard" : {
                "pattern" : "code*",
                "analyzer": "standard"
              }
            },
            {
              "any_of" : {
                "intervals" : [
                  { "match" : { "query" : "improvement" } },
                  { "match" : { "query" : "analysis" } }
                ]
              }
            }
          ]
        }
      }
    }
  }
}

# Filter example

# The following search includes a filter rule. It returns documents that have the words hot and porridge within 10 positions of each other, without the word salty in between:

# Intervals query with filter: "hot porridge" within 10 words, NOT containing "salty" in between
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

# QUERY STRING QUERY
# This query uses a syntax to parse and split the provided query string based on operators, such as AND or NOT
# Because it returns an error for any invalid syntax, we don’t recommend using the query_string query for search boxes


# Query string query: "Ui5" AND "blockchain" in 'RELATED_TASKS_NAMES_LIST'
# query_string: Supports the full Lucene query syntax.
#   query: The query string to parse.
#   default_field: The field to search if no field is specified in the query string.
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Ui5) AND (blockchain)",
      "default_field": "RELATED_TASKS_NAMES_LIST"
    }
  }
}

# Query string query: "Ui5" OR "blockchain" in 'RELATED_TASKS_NAMES_LIST'
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Ui5) OR (blockchain)",
      "default_field": "RELATED_TASKS_NAMES_LIST"
    }
  }
}

# Query string query: "Civil engineering" OR "theses" in 'RELATED_TASKS_NAMES_LIST'
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Civil engineering) OR (theses)",
      "default_field": "RELATED_TASKS_NAMES_LIST"
    }
  }
}

# Query string query: "Civil engineering" OR "theses" across fields matching "RELATED_TASKS*"
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Civil engineering) OR (theses)",
      "fields": ["RELATED_TASKS*"]
    }
  }
}

# Query string query with wildcard: "Civil*" OR "theses" across fields matching "RELATED_TASKS*"
GET tasks/_search
{
  "query": {
    "query_string": {
      "query": "(Civil\\*) OR (theses)",
      "fields": ["RELATED_TASKS*"]
    }
  }
}
