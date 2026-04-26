"""
Event Queries
SQL statements for the events table.
"""

INSERT = """
    INSERT INTO events (uid, type, source_url, platform, referrer, user_agent, country)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SUMMARY_BY_TYPE = """
    SELECT type, COUNT(*) as count
    FROM events
    WHERE created_at >= ?
    GROUP BY type
"""

TOP_PLATFORMS = """
    SELECT platform, COUNT(*) as count
    FROM events
    WHERE type = 'kurl'
      AND platform != ''
      AND created_at >= ?
    GROUP BY platform
    ORDER BY count DESC
"""

COUNTRY_BREAKDOWN = """
    SELECT country, COUNT(*) as count
    FROM events
    WHERE country != ''
      AND created_at >= ?
    GROUP BY country
    ORDER BY count DESC
    LIMIT 10
"""

RECENT = """
    SELECT * FROM events
    ORDER BY created_at DESC
    LIMIT 50
"""
