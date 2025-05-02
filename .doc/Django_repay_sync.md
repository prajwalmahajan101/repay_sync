---
title: Django_repay_sync
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
code_clipboard: true
highlight_theme: darkula
headingLevel: 2
generator: "@tarslib/widdershins v4.0.30"

---

# Django_repay_sync

Base URLs:

# Authentication

- HTTP Authentication, scheme: bearer

# Auth

## POST Login

POST /api/token/

> Body Parameters

```json
{
  "username": "prajwal",
  "password": "Test@123"
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 200 Response

```json
{
  "refresh": "string",
  "access": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» refresh|string|true|none||none|
|» access|string|true|none||none|

## POST Refersh

POST /api/token/refresh/

> Body Parameters

```json
{
  "refresh": "{{refresh_token}}"
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 200 Response

```json
{
  "access": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» access|string|true|none||none|

# Users

## GET Profile

GET /api/users/profile/

> Response Examples

> 200 Response

```json
{
  "id": 0,
  "username": "string",
  "email": "string",
  "role": "string",
  "first_name": "string",
  "last_name": "string",
  "parent": null
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» username|string|true|none||none|
|» email|string|true|none||none|
|» role|string|true|none||none|
|» first_name|string|true|none||none|
|» last_name|string|true|none||none|
|» parent|null|true|none||none|

## GET Get Subordinates

GET /api/users/subordinates/

> Response Examples

> 200 Response

```json
[
  "string"
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

## POST Register Users

POST /api/users/register/

> Body Parameters

```json
{
  "username": "CAll-1",
  "email": "call1@text.com",
  "role": "CALLING_AGENT"
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 401 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **401**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

## GET Get Credentials with one time token

GET /api/users/credentials/{token}/

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|token|path|string| yes |none|

> Response Examples

> 200 Response

```json
{
  "username": "string",
  "password": "string",
  "created_at": "string",
  "created_by": 0
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» username|string|true|none||none|
|» password|string|true|none||none|
|» created_at|string|true|none||none|
|» created_by|integer|true|none||none|

## PUT Assign Parent

PUT /api/users/11/assign-parent/

> Body Parameters

```json
{
  "parent_id": 7
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 403 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|403|[Forbidden](https://tools.ietf.org/html/rfc7231#section-6.5.3)|none|Inline|

### Responses Data Schema

HTTP Status Code **403**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

# Customer

## GET Get Customer with deposition filter

GET /api/customers/

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|disposition|query|string| no |none|

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

## GET Get Customer Details

GET /api/customers/{id}/

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|id|path|string| yes |none|

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

## PATCH Update Customer

PATCH /api/customers/2/update/

> Body Parameters

```json
{
  "name": "Maria Mahajan",
  "phone_number": "+1-555-0102",
  "email": "m.garcia@email.com",
  "address": "456 Oak Ave Unit 7 Los Angeles CA 90012",
  "collection_officer": 8
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

## GET Get Customer without any Collection officers

GET /api/customers/unassigned/

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

## POST Assign Collection Officer to Customer

POST /api/customers/10/assign-officer/

> Body Parameters

```json
{
  "officer_id": 3
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

## GET Latest Interaction for Customer

GET /api/customers/10/latest-interaction/

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

## POST Register Customer

POST /api/customers/create/

> Body Parameters

```json
{
  "name": "Prajwal Mahajan",
  "phone_number": "+1-555-0103",
  "email": "d.williams@email.com",
  "address": "789 Pine St Chicago IL 60601",
  "collection_officer": 11
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 200 Response

```json
[
  {
    "id": 0,
    "name": "string",
    "phone_number": "string",
    "email": "string",
    "address": "string",
    "collection_officer": 0,
    "created_at": "string",
    "updated_at": "string",
    "is_active": true
  }
]
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **200**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» id|integer|true|none||none|
|» name|string|true|none||none|
|» phone_number|string|true|none||none|
|» email|string|true|none||none|
|» address|string|true|none||none|
|» collection_officer|integer|true|none||none|
|» created_at|string|true|none||none|
|» updated_at|string|true|none||none|
|» is_active|boolean|true|none||none|

# Interaction

## GET Get Interactions With customer Filter

GET /api/interactions/

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|customer|query|integer| no |none|

> Response Examples

> 401 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **401**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

## GET Get Interactions By Id

GET /api/interactions/{id}

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|id|path|integer| yes |none|

> Response Examples

> 401 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **401**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

## PATCH Update Interactions 

PATCH /api/interactions/{id}/update/

> Body Parameters

```json
"{\r\n    \"customer\": 3,\r\n    \"comment\": \"No response - voicemail left - Need to Connect again\",\r\n    \"disposition\": \"NOT_REACHABLE\",\r\n}"
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|id|path|integer| yes |none|
|body|body|object| no |none|

> Response Examples

> 401 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **401**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

## DELETE Delete Interactions

DELETE /api/interactions/{id}/delete/

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|id|path|integer| yes |none|

> Response Examples

> 401 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **401**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

## POST Create a  new Interaction

POST /api/interactions/create/

> Body Parameters

```json
{
  "customer": 3,
  "comment": "Promised to Pay next Month",
  "disposition": "PROMISE_TO_PAY"
}
```

### Params

|Name|Location|Type|Required|Description|
|---|---|---|---|---|
|body|body|object| no |none|

> Response Examples

> 401 Response

```json
{
  "detail": "string"
}
```

### Responses

|HTTP Status Code |Meaning|Description|Data schema|
|---|---|---|---|
|401|[Unauthorized](https://tools.ietf.org/html/rfc7235#section-3.1)|none|Inline|

### Responses Data Schema

HTTP Status Code **401**

|Name|Type|Required|Restrictions|Title|description|
|---|---|---|---|---|---|
|» detail|string|true|none||none|

# Data Schema

