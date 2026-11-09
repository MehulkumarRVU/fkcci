#!/bin/sh
set -eu
umask 077

log() {
    level=$1
    event=$2
    file=${3:-}
    printf '{"timestamp":"%s","level":"%s","event":"%s","file":"%s"}\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$level" "$event" "$file"
}

notify_failure() {
    webhook=${BACKUP_FAILURE_WEBHOOK_URL:-}
    if [ -z "$webhook" ]; then
        return
    fi
    case "$webhook" in
        https://*) ;;
        *)
            log warning failure_notification_requires_https
            return
            ;;
    esac
    payload='{"text":"PocketCoach PostgreSQL backup failed; inspect the scheduled task logs."}'
    if command -v curl >/dev/null 2>&1; then
        curl --fail --silent --show-error --max-time 10 \
            -H 'Content-Type: application/json' --data "$payload" "$webhook" >/dev/null \
            || log warning backup_failure_notification_failed
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O /dev/null --timeout=10 --header='Content-Type: application/json' \
            --post-data="$payload" "$webhook" \
            || log warning backup_failure_notification_failed
    else
        log warning failure_notification_client_unavailable
    fi
}

for name in PGHOST PGUSER PGDATABASE BACKUP_DIRECTORY BACKUP_RETENTION_DAYS; do
    eval "value=\${$name:-}"
    if [ -z "$value" ]; then
        log error "missing_required_setting_$name"
        exit 2
    fi
done

case "$PGDATABASE" in
    *[!A-Za-z0-9_]*)
        log error invalid_database_name
        exit 2
        ;;
esac
case "$BACKUP_RETENTION_DAYS" in
    *[!0-9]* | "")
        log error invalid_retention_days
        exit 2
        ;;
esac
if [ "$BACKUP_RETENTION_DAYS" -lt 1 ]; then
    log error invalid_retention_days
    exit 2
fi

mkdir -p "$BACKUP_DIRECTORY"
chmod 700 "$BACKUP_DIRECTORY"
timestamp=$(date -u '+%Y%m%dT%H%M%SZ')
filename="${PGDATABASE}_${timestamp}_$$.dump"
temporary_file="$BACKUP_DIRECTORY/.${filename}.tmp.$$"
temporary_checksum="$BACKUP_DIRECTORY/.${filename}.sha256.tmp.$$"
final_file="$BACKUP_DIRECTORY/$filename"
checksum_file="$final_file.sha256"
completed=0

cleanup() {
    result=$?
    if [ -n "${temporary_file:-}" ] && [ -f "$temporary_file" ]; then
        rm -f "$temporary_file"
    fi
    if [ -n "${temporary_checksum:-}" ] && [ -f "$temporary_checksum" ]; then
        rm -f "$temporary_checksum"
    fi
    if [ "$result" -ne 0 ]; then
        if [ "$completed" -eq 0 ]; then
            rm -f "$final_file" "$checksum_file"
        fi
        log error backup_failed
        notify_failure
    fi
}
trap cleanup EXIT

log info backup_started "$filename"
pg_dump --format=custom --no-owner --no-acl --file="$temporary_file" "$PGDATABASE"
pg_restore --list "$temporary_file" >/dev/null
checksum=$(sha256sum "$temporary_file" | cut -d ' ' -f 1)
(
    cd "$BACKUP_DIRECTORY"
    printf '%s  %s\n' "$checksum" "$filename" > "$temporary_checksum"
)
chmod 600 "$temporary_file"
chmod 600 "$temporary_checksum"
mv "$temporary_file" "$final_file"
temporary_file=
mv "$temporary_checksum" "$checksum_file"
temporary_checksum=
(
    cd "$BACKUP_DIRECTORY"
    sha256sum -c "$(basename "$checksum_file")" >/dev/null
)
find "$BACKUP_DIRECTORY" -maxdepth 1 -type f \
    \( -name "${PGDATABASE}_*.dump" -o -name "${PGDATABASE}_*.dump.sha256" \) \
    -mtime "+$BACKUP_RETENTION_DAYS" -delete
completed=1
log info backup_verified "$filename"
