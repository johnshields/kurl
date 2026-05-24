"""
Event Queries
SQL statements for the events table.
"""

INSERT = """
    INSERT INTO events (uid, type, source_url, platform, via, referrer, user_agent, country)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

MATCH_QUALITY = """
    SELECT
        platform,
        SUM(CASE WHEN via IN ('isrc','upc','name','search_api','direct') THEN 1 ELSE 0 END) AS exact_count,
        SUM(CASE WHEN via = 'search' THEN 1 ELSE 0 END) AS approx_count,
        COUNT(*) AS total
    FROM events
    WHERE type = 'kurl_success'
      AND platform != ''
      AND created_at >= ?
    GROUP BY platform
    ORDER BY total DESC
"""

APPROX_PAIRS = """
    SELECT source_url, platform, COUNT(*) AS misses
    FROM events
    WHERE type = 'kurl_success'
      AND via = 'search'
      AND created_at >= ?
    GROUP BY source_url, platform
    ORDER BY misses DESC
    LIMIT 50
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
