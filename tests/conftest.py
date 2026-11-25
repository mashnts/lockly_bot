import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test"
os.environ["BOT_TOKEN"] = "123:test"
os.environ["CRYPTOBOT_TOKEN"] = "cryptobot-test"
os.environ["SECRET_KEY"] = "test"
os.environ["INTERNAL_API_TOKEN"] = "internal-test"
os.environ["BACKEND_URL"] = "http://backend.test"
