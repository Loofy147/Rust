import json

def create_jsonrpc_request(method, params, request_id=None):
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

def create_jsonrpc_response(result, request_id):
    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    }

def create_jsonrpc_error(code, message, request_id=None):
    return {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        },
        "id": request_id
    }

def parse_jsonrpc(jsonrpc_string):
    try:
        jsonrpc_data = json.loads(jsonrpc_string)
    except json.JSONDecodeError:
        return create_jsonrpc_error(-32700, "Parse error")

    if "method" in jsonrpc_data:
        # It's a request
        return jsonrpc_data
    elif "result" in jsonrpc_data or "error" in jsonrpc_data:
        # It's a response
        return jsonrpc_data
    else:
        return create_jsonrpc_error(-32600, "Invalid Request")
