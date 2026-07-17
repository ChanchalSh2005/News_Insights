from pydantic_settings import BaseSettings,SettingsConfigDict
from sqlalchemy.engine import URL



class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=NONE)
    DB_CONNECTION:str

setting=Settings()
print(setting.DB_CONNECTION)
