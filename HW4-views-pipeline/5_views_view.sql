CREATE VIEW shirind76.views AS
SELECT
    title,
    views,
    rank,
    date,
    cast(from_iso8601_timestamp(retrieved_at) AS TIMESTAMP) AS retrieved_at
FROM raw_views
ORDER BY
    date ASC,
    rank ASC;

