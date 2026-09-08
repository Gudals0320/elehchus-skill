"""Compare portable scan meaning while retaining live filesystem timestamps."""
from copy import deepcopy


def portable_report(report):
    result = deepcopy(report)
    for row in result['records']:
        if 'filesystem_mtime_ns' in row:
            value = row['filesystem_mtime_ns']
            if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
                raise ValueError('filesystem_mtime_ns must remain an integer or null')
            # File copies and archive extraction change this environment value.
            # Keep the key: dropping the field is still an output contract change.
            row['filesystem_mtime_ns'] = '<current-filesystem-value>'
    return result


def compare_reports(current, saved):
    old = {row['path']: row for row in saved['records']}
    changes = []
    for row in current['records']:
        previous = old.get(row['path'], {})
        if row.get('filesystem_mtime_ns') != previous.get('filesystem_mtime_ns'):
            changes.append({'path': row['path'], 'saved': previous.get('filesystem_mtime_ns'),
                            'current': row.get('filesystem_mtime_ns')})
    return {'portable_equal': portable_report(current) == portable_report(saved),
            'filesystem_mtime_differences': changes}
