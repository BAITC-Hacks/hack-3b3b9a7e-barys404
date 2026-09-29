"""Manage local MedFlow accounts. Secrets are prompted, never passed on the command line."""
import argparse
import getpass
import json
import secrets

import psycopg

from backend.core.config import ANALYTICAL_PATH, ROOT
from backend.modules.auth import store


def sync():
    from backend.modules.analytics import dashboard_data as db
    rows = db.aggregate_query(ANALYTICAL_PATH, "SELECT DISTINCT hospital_mo FROM read_parquet(?) WHERE hospital_mo IS NOT NULL ORDER BY hospital_mo")
    store.sync_organizations(rows.hospital_mo.tolist())


def seed_demo():
    from backend.modules.analytics import dashboard_data as db
    sync()
    top = db.aggregate_query(ANALYTICAL_PATH, "SELECT hospital_mo FROM read_parquet(?) WHERE hospital_mo IS NOT NULL GROUP BY hospital_mo ORDER BY count(*) DESC, hospital_mo LIMIT 2")
    catalog = {item["name"]: item["id"] for item in store.organizations()}
    if len(top) < 2:
        raise ValueError("Для демонстрации нужны две больницы с данными.")
    specs = [("government.demo", "Аналитик госоргана", "government_analyst", None),
             ("hospital.a", "Сотрудник больницы A", "hospital_analyst", catalog[top.iloc[0].hospital_mo]),
             ("hospital.b", "Сотрудник больницы B", "hospital_analyst", catalog[top.iloc[1].hospital_mo]),
             ("admin.demo", "Администратор", "platform_admin", None)]
    existing = {row["login"] for row in store.list_users()}
    created = []
    for login, name, role, hospital_id in specs:
        if login in existing:
            continue
        password = secrets.token_urlsafe(18)
        store.create_user(login, name, password, role, hospital_id, must_change=False)
        organization = next((row["name"] for row in store.organizations(hospital_id)), "") if hospital_id else "Все больницы" if role == "government_analyst" else "Управление платформой"
        created.append({"login": login, "password": password, "role": role, "organization": organization})
    if created:
        directory = ROOT / ".runtime"
        directory.mkdir(exist_ok=True)
        path = directory / "demo-accounts.json"
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        path.write_text(json.dumps([*previous, *created], ensure_ascii=False, indent=2), encoding="utf-8")
        with (directory / "demo-accounts.md").open("a", encoding="utf-8") as output:
            if output.tell() == 0:
                output.write("# Тестовые аккаунты MedFlow AI\n\nТолько для локального хакатонного показа. Не публикуйте файл и пароли.\n\n")
            for item in created:
                output.write(f"## {item['login']}\n\nПароль: `{item['password']}`\n\nРоль: `{item['role']}`\n\nОрганизация: {item['organization']}\n\n")
    print(f"Created {len(created)} accounts. Existing accounts unchanged. Credentials: .runtime/demo-accounts.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("migrate", "sync-organizations", "seed-demo", "users", "organizations", "audit"):
        commands.add_parser(name)
    create = commands.add_parser("create-user")
    create.add_argument("login"); create.add_argument("--name", required=True)
    create.add_argument("--role", choices=list(store.PERMISSIONS), required=True)
    create.add_argument("--hospital-id")
    for name in ("disable", "enable", "reset-password", "revoke"):
        command = commands.add_parser(name); command.add_argument("login")
    assign = commands.add_parser("assign")
    assign.add_argument("login"); assign.add_argument("--role", choices=list(store.PERMISSIONS), required=True)
    assign.add_argument("--hospital-id")
    args = parser.parse_args()
    if args.command == "migrate":
        store.migrate(); print("Database migrations applied.")
    elif args.command == "sync-organizations":
        sync(); print("Organization catalog synchronized.")
    elif args.command == "seed-demo":
        seed_demo()
    elif args.command in {"users", "organizations"}:
        print(json.dumps(store.list_users() if args.command == "users" else store.organizations(), ensure_ascii=False, indent=2))
    elif args.command == "audit":
        with store.connection() as con:
            print(json.dumps([dict(row) for row in con.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 100")], ensure_ascii=False, indent=2))
    elif args.command == "create-user":
        store.create_user(args.login, args.name, getpass.getpass("Temporary password (12+ characters): "), args.role, args.hospital_id)
        print("User created. Password change required on first login.")
    elif args.command == "assign":
        store.update_user(args.login, role=args.role, hospital_id=args.hospital_id)
    elif args.command == "reset-password":
        store.update_user(args.login, password=getpass.getpass("New temporary password (12+ characters): "))
    else:
        store.update_user(args.login, active=False if args.command == "disable" else True if args.command == "enable" else None)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, psycopg.Error, RuntimeError) as error:
        print(str(error) if isinstance(error, (ValueError, RuntimeError)) else "Database operation failed. Check configuration, migrations and uniqueness of the login.")
        raise SystemExit(1)
