def init_errors(model_name: str, model_url: str, max_context_size: int, max_tokens: int, temperature: float, api_token: str, api_type: str):
    errors = []

    if not model_name or model_name == "Not initialized":
        errors.append("'model_name' is not set")

    if max_context_size <= 0:
        errors.append("'max_context_size' is not correct. Use positive integer")

    if max_tokens <= 0:
        errors.append("'max_tokens' is not correct. Use positive integer")

    if temperature < 0 or temperature > 2.0:
        errors.append("'temperature' is not correct. Use between 0 and 2.0")

    if not api_token or api_token == "Not initialized":
        errors.append("'api_token' is not set")

    compatibles = {"Anthropic", "OpenAI"}
    if api_type not in compatibles:
        errors.append(f"'api_type' [{api_type}'] is not supported. Available: {compatibles}")

    if errors:
        print("[ERROR] Check your initialization parameters:")
        for error in errors:
            print(f"  - {error}")
        return 0

    return 1