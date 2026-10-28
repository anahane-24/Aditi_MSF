from pathlib import Path

from dotenv import dotenv_values


config = dotenv_values(Path(__file__).with_name(".env"))
print(config["API_KEY"][:4] + "...")
print(config["SEC_USER_AGENT"])
