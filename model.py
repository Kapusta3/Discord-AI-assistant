from PIL import Image as Img
from errors import init_errors
from model_adapter import ModelAdapter

class Model:
    def __init__(self,
                 model_name: str = "Not initialized",
                 model_url: str = None,
                 model_icon: Img.Image = None,
                 max_context_size: int = 2048,
                 max_tokens: int = 1024,
                 temperature: float = 1.0,
                 system:str = "You are a helpful assistant.",
                 api_key: str = "Not initialized",
                 api_type: str = "OpenAI"):

        self.model_name = model_name
        self.model_url = model_url
        self.model_icon = model_icon if model_icon is not None else Img.open("img/question_logo.png")
        self.max_context_size = max_context_size
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system = system
        self.api_key = api_key
        self.api_type = api_type

        #Проверка инициализации
        init_errors(self.model_name, self.model_url, self.max_context_size, self.max_tokens, self.temperature, self.api_key, self.api_type)

        self.adapter = ModelAdapter(self)

    #Информация о модели
    def get_info(self) -> str:
        if self.api_key == "Your Token Here" or len(self.api_key) <= 1:
            token_display = self.api_key
        else:
            token_display = self.api_key[:1] + "#" * (len(self.api_key) - 1)

        return (f"\nModel name: '{self.model_name}'\n"
                f"Model url: '{self.model_url}'\n"
                f"Icon Size: '{self.model_icon.size}'\n"
                f"Max context size: '{self.max_context_size}'\n"
                f"Max tokens: '{self.max_tokens}'\n"
                f"Temperature: '{self.temperature}'\n"
                f"System: '{self.system}'\n"
                f"API key: '{token_display}'\n"
                f"API type: '{self.api_type}'")

    #Длинное сообщение
    def send_request(self, message: str, history: list = None) -> str:
        try:
            return self.adapter.send_request(message, history)
        except Exception as e:
            return f"Error: {e}"

    #Короткое сообщение
    def chat(self, message: str) -> str:
        try:
            return self.send_request(message)
        except Exception as e:
            return f"Error: {e}"

    #Удобное обращение к моделе
    def __repr__(self) -> str:
        return f"Model(name='{self.model_name}', type='{self.api_type}')"

RP_Role = Model("Sainemo", "http://127.0.0.1:5710/v1",api_key="kapustiiik", api_type="OpenAI")

print(RP_Role.get_info())
print(RP_Role)
print(RP_Role.chat("hi"))