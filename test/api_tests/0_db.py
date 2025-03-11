import requests
import pytest
from data import BASE_URL

CLEAN_DB_URL = f"{BASE_URL}/test/clean-db"

class TestDatabaseCleanup:
    """
    Класс для очистки базы данных перед выполнением других тестов.
    """

    def test_cleanup_database(self):
        """Очистка базы данных перед запуском других тестов"""
        response = requests.delete(CLEAN_DB_URL)
        
        assert response.status_code == 200, f"Не удалось очистить БД. Код ответа: {response.status_code}, текст: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "База данных очищена"
        
        print("✅ База данных успешно очищена перед запуском тестов")
