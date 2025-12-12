# MVP Spec

Экраны:
1) Операции: список + фильтры + добавление/редактирование/удаление (soft).
2) Дашборд: агрегации по категориям и по дням (бек отдаёт готовые данные).
3) Справочники: категории (CRUD + архив).

Backend: FastAPI + Postgres, Alembic migrations.
Frontend: Vue 3 + Vite.
Storage: receipts folder (volume), ссылку хранить в БД.
