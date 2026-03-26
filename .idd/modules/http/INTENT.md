# Module Intent: http

> Build HTTP requests from command context, send them to the API,
> and parse responses into structured data.

## Structure

```
http/
├── client.go           Build + send HTTP requests
├── auth.go             Auth providers (API key, bearer token)
└── response.go         Parse response body, detect error patterns
```

## Constraints

| Rule | Rationale | Verified by |
|---|---|---|
| HTTP module is generic — no OpenAPI knowledge | Clean boundary: spec knows OpenAPI, http knows HTTP | CI lint |
| Default Content-Type: application/json for requests with body | Most APIs expect JSON | BDD step assertion |
| Accept header: application/json by default | Request JSON responses | BDD step assertion |
| Timeout: 30 seconds default, configurable | Prevent hanging on unresponsive APIs | BDD scenario |
| Auth credentials loaded from config profile | Never hardcoded, never prompted at request time | BDD scenario |
| Response body parsed based on Content-Type | Support JSON and YAML responses | BDD scenario |
| Binary responses (audio/*, image/*, application/octet-stream, application/pdf) MUST be saved to a local file automatically, not printed to terminal | Prevents garbled binary output and data loss | BDD scenario |
| When a binary response is saved, display the file path + size instead of the body | Human-friendly confirmation | BDD scenario |
| HTTP errors (4xx, 5xx) return structured error, never panic | Graceful degradation | BDD step assertion |

## Examples

### Request Building

| Input (method, path, params, body, auth) | Output (HTTP request) |
|---|---|
| GET, `/pets`, query:`{status:"available"}`, no body, api_key:`abc` | `GET /pets?status=available` + header `X-API-Key: abc` |
| POST, `/pets`, no query, body:`{name:"Buddy"}`, bearer:`tok123` | `POST /pets` + body `{"name":"Buddy"}` + header `Authorization: Bearer tok123` |
| PUT, `/pets/42`, no query, body:`{status:"sold"}`, no auth | `PUT /pets/42` + body `{"status":"sold"}` |
| DELETE, `/pets/42`, no query, no body, api_key:`abc` | `DELETE /pets/42` + header `X-API-Key: abc` |

### Response Parsing

| Input (status, content-type, body) | Output |
|---|---|
| 200, `application/json`, `{"id":1,"name":"Buddy"}` | `Response{Status:200, Body:map, IsError:false}` |
| 201, `application/json`, `{"id":3}` | `Response{Status:201, Body:map, IsError:false}` |
| 204, no body | `Response{Status:204, Body:nil, IsError:false}` |
| 404, `application/json`, `{"message":"not found"}` | `Response{Status:404, Body:map, IsError:true}` |
| 422, `application/json`, `{"errors":[...]}` | `Response{Status:422, Body:map, IsError:true}` |
| 500, `text/plain`, `Internal Server Error` | `Response{Status:500, Body:"Internal Server Error", IsError:true}` |
| Connection refused | `Response{IsError:true, NetworkError:"connection refused"}` |

### Auth

| Auth config | Applied as |
|---|---|
| `{type:"api-key", header:"X-API-Key", value:"abc123"}` | Header `X-API-Key: abc123` |
| `{type:"api-key", query:"api_key", value:"abc123"}` | Query param `?api_key=abc123` |
| `{type:"bearer", token:"tok123"}` | Header `Authorization: Bearer tok123` |
| No auth configured | No auth header/param added |
