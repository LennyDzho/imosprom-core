import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def test_schemas():
    """Тестирование создания схем"""
    print("🧪 Тестирование схем Pydantic...")

    try:
        from src.core.infra.schemas import (
            UserCreate, UserLogin, UserResponse, TokenResponse,
            AgentRequest, AgentResponse
        )

        # Тест UserCreate
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        user_create = UserCreate(**user_data)
        print("✅ UserCreate создана успешно")

        # Тест UserLogin
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        user_login = UserLogin(**login_data)
        print("✅ UserLogin создана успешно")

        # Тест AgentRequest
        agent_request_data = {
            "dialog_id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
            "task_id": "b2c3d4e5-2345-6789-0000-bcdefabcdefa",
            "trace_id": "c3d4e5f6-3456-7890-1111-cdefabcdefab",
            "message": {
                "text": "Тестовое сообщение",
                "lang": "ru"
            },
            "context": {
                "history": [],
                "kb_filters": {}
            }
        }
        agent_request = AgentRequest(**agent_request_data)
        print("✅ AgentRequest создана успешно")

        print("🎉 Все схемы работают корректно!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_schemas()