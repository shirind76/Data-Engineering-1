-- Bucket name: shirind76-wikidata
-- Database name: shirind76

CREATE EXTERNAL TABLE shirind76.raw_views (
    title STRING,
    views INT,
    rank INT,
    date STRING,
    retrieved_at STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://shirind76-wikidata/raw-views/';

