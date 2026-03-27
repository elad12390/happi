from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

_PETS: dict[str, dict[str, Any]] = {
    "1": {"id": 1, "name": "Buddy", "status": "available"},
    "2": {"id": 2, "name": "Rex", "status": "sold"},
    "3": {"id": 3, "name": "Luna", "status": "pending"},
}

_next_id = 4

SPEC: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "Test Petstore", "version": "1.0.0"},
    "servers": [{"url": ""}],
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "tags": ["pet"],
                "summary": "List all pets",
                "parameters": [
                    {"name": "status", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "operationId": "createPet",
                "tags": ["pet"],
                "summary": "Create a pet",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "status": {"type": "string"},
                                },
                                "required": ["name"],
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "showPet",
                "tags": ["pet"],
                "summary": "Show a pet",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "put": {
                "operationId": "updatePet",
                "tags": ["pet"],
                "summary": "Update a pet",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "delete": {
                "operationId": "deletePet",
                "tags": ["pet"],
                "summary": "Delete a pet",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/pets/{petId}/activate": {
            "post": {
                "operationId": "activatePet",
                "tags": ["pet"],
                "summary": "Activate a pet",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/pets/{petId}/upload-image": {
            "post": {
                "operationId": "uploadPetImage",
                "tags": ["pet"],
                "summary": "Upload an image for a pet",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"},
                                    "caption": {"type": "string"},
                                },
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/pets/{petId}/photo": {
            "get": {
                "operationId": "getPetPhoto",
                "tags": ["pet"],
                "summary": "Get pet photo",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK", "content": {"image/png": {}}}},
            },
        },
    },
    "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}},
}


class PetstoreHandler(BaseHTTPRequestHandler):
    require_auth: bool = False

    def do_GET(self) -> None:
        if self.path == "/openapi.json":
            self._json_response(200, SPEC)
            return
        if self.path.startswith("/pets") and "?" not in self.path and self.path.count("/") == 1:
            self._json_response(200, list(_PETS.values()))
            return
        if "/photo" in self.path and self.path.startswith("/pets/"):
            self._binary_response(200, b"\x89PNG\r\n\x1a\nFAKEPNGDATA", "image/png")
            return
        if self.path.startswith("/pets/"):
            pet_id = self.path.split("/")[2].split("?")[0]
            pet = _PETS.get(pet_id)
            if pet:
                self._json_response(200, pet)
            else:
                self._json_response(404, {"message": "Pet not found"})
            return
        self._json_response(404, {"message": "Not found"})

    def do_POST(self) -> None:
        if self.require_auth and not self._check_auth():
            return
        if "/upload-image" in self.path:
            content_type = self.headers.get("Content-Type", "")
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length > 0 else b""
            pet_id = self.path.split("/")[2]
            has_file = b"Content-Disposition" in raw and b"filename" in raw
            self._json_response(
                200,
                {
                    "pet_id": pet_id,
                    "uploaded": has_file,
                    "content_type": content_type.split(";")[0].strip(),
                    "size": length,
                },
            )
            return
        body = self._read_body()
        if "/activate" in self.path:
            pet_id = self.path.split("/")[2]
            pet = _PETS.get(pet_id)
            if pet:
                pet["status"] = "active"
                self._json_response(200, pet)
            else:
                self._json_response(404, {"message": "Pet not found"})
            return
        if self.path.rstrip("/") == "/pets":
            global _next_id
            new_pet = {
                "id": _next_id,
                "name": body.get("name", ""),
                "status": body.get("status", "available"),
            }
            _PETS[str(_next_id)] = new_pet
            _next_id += 1
            self._json_response(201, new_pet)
            return
        self._json_response(404, {"message": "Not found"})

    def do_PUT(self) -> None:
        body = self._read_body()
        if self.path.startswith("/pets/"):
            pet_id = self.path.split("/")[2]
            pet = _PETS.get(pet_id)
            if pet:
                pet.update(body)
                self._json_response(200, pet)
            else:
                self._json_response(404, {"message": "Pet not found"})
            return
        self._json_response(404, {"message": "Not found"})

    def do_DELETE(self) -> None:
        if self.path.startswith("/pets/"):
            pet_id = self.path.split("/")[2]
            removed = _PETS.pop(pet_id, None)
            if removed:
                self.send_response(204)
                self.end_headers()
            else:
                self._json_response(404, {"message": "Pet not found"})
            return
        self._json_response(404, {"message": "Not found"})

    def _check_auth(self) -> bool:
        auth_header = self.headers.get("Authorization", "")
        api_key = self.headers.get("X-API-Key", "")
        if not auth_header and not api_key:
            self._json_response(401, {"message": "Authentication required"})
            return False
        return True

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode()
        result: dict[str, Any] = json.loads(raw)
        return result

    def _json_response(self, status: int, data: object) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _binary_response(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


def start_test_server() -> tuple[HTTPServer, str]:
    server = HTTPServer(("127.0.0.1", 0), PetstoreHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = str(server.server_address[0])
    port = int(server.server_address[1])
    base_url = f"http://{host}:{port}"
    SPEC["servers"][0]["url"] = base_url
    return server, base_url
