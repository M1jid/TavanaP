from utils import db_handler as db


async def get_users():
    return db.get_users()

async def update_user(
    user_id: int,
    data: dict,
):
    return db.update_user(user_id, data)

async def create_user(
    data: dict,
):
    return db.create_user([data])

async def delete_user(
    user_id: int,
):
    return db.delete_user(user_id)

async def toggle_user_status(
    user_id: int,
):
    return db.toggle_user_status(user_id)

async def get_user_queries(
    query_ids: int,
):
    result = []
    for query_id in query_ids:
        query = db.get_user_query_id(query_id)
        result.append(query)
    return result

async def get_user_queries_all():
    return db.get_user_query_id_all()

async def create_user_query(
    data,
):
    return db.create_user_query_id([data])

async def update_user_query(
    q_id: int,
    data: dict,
):
    return db.update_user_query_id(q_id, [data])
