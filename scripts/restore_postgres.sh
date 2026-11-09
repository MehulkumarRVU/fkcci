#!/bin/sh
set -eu
umask 077

log() {
    level=$1
    event=$2
    printf '{"timestamp":"%s","level":"%s","event":"%s"}\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$level" "$event"
}

backup_file=${1:-${BACKUP_FILE:-}}
target_database=${RESTORE_TARGET_DB:-}
if [ -z "$PGHOST" ] || [ -z "$PGUSER" ] || [ -z "$PGDATABASE" ] || \
   [ -z "$backup_file" ] || [ -z "$target_database" ]; then
    log error missing_required_setting
    exit 2
fi

for database_name in "$PGDATABASE" "$target_database"; do
    case "$database_name" in
        *[!A-Za-z0-9_]*)
            log error invalid_database_name
            exit 2
            ;;
    esac
done
if [ "$PGDATABASE" = "$target_database" ]; then
    log error refusing_to_restore_over_source_database
    exit 2
fi
if [ ! -f "$backup_file" ]; then
    log error backup_file_not_found
    exit 2
fi

target_created=0
cleanup() {
    result=$?
    if [ "$result" -ne 0 ] && [ "$target_created" -eq 1 ]; then
        if dropdb --maintenance-db="$PGDATABASE" "$target_database"; then
            log warning failed_restore_target_removed
        else
            log error failed_restore_target_cleanup_failed
        fi
    fi
}
trap cleanup EXIT

if [ -f "$backup_file.sha256" ]; then
    if ! (cd "$(dirname "$backup_file")" && sha256sum -c "$(basename "$backup_file").sha256" >/dev/null); then
        log error backup_checksum_verification_failed
        exit 1
    fi
else
    log error backup_checksum_missing
    exit 2
fi
pg_restore --list "$backup_file" >/dev/null
exists=$(psql --dbname="$PGDATABASE" --tuples-only --no-align \
    --set=ON_ERROR_STOP=1 \
    --command="SELECT 1 FROM pg_database WHERE datname = '$target_database'")
if [ "$exists" = "1" ]; then
    log error restore_target_already_exists
    exit 2
fi

log info restore_started
createdb --maintenance-db="$PGDATABASE" "$target_database"
target_created=1
pg_restore --exit-on-error --no-owner --no-acl --dbname="$target_database" "$backup_file"
table_count=$(psql --dbname="$target_database" --tuples-only --no-align \
    --set=ON_ERROR_STOP=1 \
    --command="SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
foreign_key_count=$(psql --dbname="$target_database" --tuples-only --no-align \
    --set=ON_ERROR_STOP=1 \
    --command="SELECT count(*) FROM information_schema.table_constraints WHERE constraint_schema = 'public' AND constraint_type = 'FOREIGN KEY'")
if [ "$table_count" -lt 1 ] || [ "$foreign_key_count" -lt 1 ]; then
    log error restored_schema_validation_failed
    exit 1
fi
target_created=0
log info restore_completed
