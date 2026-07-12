from openai import OpenAI
from anthropic import Anthropic


class ModelAdapter:
    def __init__(self, model):
        self.model = model
        self.client = self._create_client()

    def _create_client(self):
        if self.model.api_type == "OpenAI":
            return OpenAI(
                api_key = self.model.api_key,
                base_url=self.model.model_url) \
            if self.model.model_url is not None else OpenAI(api_key = self.model.api_key)

        elif self.model.api_type == "Anthropic":
            return Anthropic(
                api_key = self.model.api_key,
                base_url=self.model.model_url) \
            if self.model.model_url is not None else Anthropic(api_key = self.model.api_key)

        else:
            raise ValueError(f"Unsupported API type: {self.model.api_type}")

    def send_request(self, message: str, history: list = None):
        if self.model.api_type == "OpenAI":
            return self._send_openai(message, history)
        elif self.model.api_type == "Anthropic":
            return self._send_anthropic(message, history)
        else:
            raise ValueError(f"Unsupported API type: {self.model.api_type}")

    def _send_openai(self, message: str, history: list = None):
        messages = []
        messages.append({"role": "system", "content": self.model.system})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model = self.model.model_name,
            messages = messages,
            max_tokens = self.model.max_tokens,
            temperature = self.model.temperature
        )

        return response.choices[0].message.content

    def _send_anthropic(self, message: str, history: list = None):
        messages = []

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model = self.model.model_name,
            max_tokens = self.model.max_tokens,
            temperature = self.model.temperature,
            system = self.model.system,
            messages = messages
        )

        return response.content[0].text