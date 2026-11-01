#!/usr/bin/env python3
"""Архивирует старые monster.moved и удаляет их партиями после проверки архива.

По умолчанию выводит только оценку объёма. Для удаления нужен --apply.
Боевые события и новые события после --before не затрагиваются.
"""

import argparse
import csv
import datetime as dt
import gzip
import os
import shutil
import subprocess
from pathlib import Path


def psql(container: str, query: str, *, output=None) -> str:
    command = ["docker", "exec", "-i", container, "psql", "-X", "-q", "-At", "-v", "ON_ERROR_STOP=1",
               "-U", "real_city", "-d", "real_city", "-c", query]
    if output is not None:
        with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
            assert process.stdout is not None
            shutil.copyfileobj(process.stdout, output)
            if process.wait() != 0:
                raise subprocess.CalledProcessError(process.returncode, command)
        return ""
    return subprocess.check_output(command, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="UTC cutoff, например 2026-11-01T11:00:00+00:00")
    parser.add_argument("--archive", type=Path, help="путь к новому .csv.gz на хосте")
    parser.add_argument("--container", default="real-city-test-postgres-1")
    parser.add_argument("--batch-size", type=int, default=20000)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    cutoff = dt.datetime.fromisoformat(args.before.replace("Z", "+00:00"))
    if cutoff.tzinfo is None or args.batch_size < 1 or args.batch_size > 100000:
        parser.error("нужны timezone в --before и batch-size 1..100000")
    if args.apply and (args.archive is None or args.archive.exists()):
        parser.error("для --apply нужен новый, ещё не существующий --archive")
    sql_cutoff = cutoff.astimezone(dt.timezone.utc).isoformat().replace("'", "")
    predicate = f"type = 'monster.moved' AND created_at < TIMESTAMPTZ '{sql_cutoff}'"
    count = int(psql(args.container, f"SELECT count(*) FROM monster_events WHERE {predicate}"))
    print(f"Подходящих monster.moved: {count}", flush=True)
    if not args.apply or count == 0:
        return
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(args.archive, "xb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb") as compressed:
                psql(args.container, "COPY (SELECT id, monster_id, type, target_id, tile_x, tile_y, created_at "
                     f"FROM monster_events WHERE {predicate} ORDER BY created_at, id) "
                     "TO STDOUT WITH (FORMAT csv, HEADER true)", output=compressed)
            raw.flush()
            os.fsync(raw.fileno())
        with gzip.open(args.archive, "rt", newline="") as source:
            rows = sum(1 for _ in csv.DictReader(source))
        if rows != count:
            raise RuntimeError(f"архив содержит {rows} строк вместо {count}; удаление отменено")
        print(f"Архив проверен: {args.archive} ({args.archive.stat().st_size} байт)", flush=True)
        deleted = 0
        while True:
            result = psql(args.container, "WITH batch AS (SELECT ctid FROM monster_events "
                          f"WHERE {predicate} LIMIT {args.batch_size} FOR UPDATE SKIP LOCKED), "
                          "deleted AS (DELETE FROM monster_events e USING batch "
                          "WHERE e.ctid = batch.ctid RETURNING 1) SELECT count(*) FROM deleted")
            n = int(result)
            deleted += n
            if n == 0:
                break
            if deleted % 100000 < args.batch_size:
                print(f"Удалено: {deleted}", flush=True)
        remaining = int(psql(args.container, f"SELECT count(*) FROM monster_events WHERE {predicate}"))
        print(f"Удалено: {deleted}; осталось под cutoff: {remaining}", flush=True)
        if remaining:
            raise RuntimeError("после очистки остались строки; архив сохранён")
        psql(args.container, "VACUUM (ANALYZE) monster_events")
        print("VACUUM ANALYZE завершён; для возврата места ОС нужен отдельный pg_repack или VACUUM FULL.")
    except BaseException:
        print(f"Архив сохранён по пути {args.archive}; проверьте результат перед повтором.")
        raise


if __name__ == "__main__":
    main()
