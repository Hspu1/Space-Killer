CREATE KEYSPACE IF NOT EXISTS content_service
WITH replication = {'class': 'NetworkTopologyStrategy', 'dc1': 1};

CREATE TABLE IF NOT EXISTS content_service.posts (
    post_id uuid,
    author_id uuid,
    title text,
    text text,
    fid set<text>,
    is_edited boolean,
    PRIMARY KEY (post_id)
) WITH compaction = { 'class': 'LeveledCompactionStrategy' }
AND gc_grace_seconds = 0;

CREATE TABLE IF NOT EXISTS content_service.comments (
    post_id uuid,
    comment_id uuid,
    parent_id uuid,
    author_id uuid,
    body text,
    depth int,
    is_deleted boolean,
    PRIMARY KEY (post_id, comment_id)
) WITH CLUSTERING ORDER BY (comment_id DESC)
AND compaction = { 'class': 'LeveledCompactionStrategy' }
AND gc_grace_seconds = 0;

CREATE TABLE IF NOT EXISTS content_service.following (
    user_id uuid,
    following_id uuid,
    created_at timestamp,
    PRIMARY KEY (user_id, following_id)
) WITH compaction = { 'class': 'LeveledCompactionStrategy' }
AND gc_grace_seconds = 0;

CREATE TABLE IF NOT EXISTS content_service.followers (
    author_id uuid,
    follower_id uuid,
    created_at timestamp,
    PRIMARY KEY (author_id, follower_id)
) WITH compaction = { 'class': 'SizeTieredCompactionStrategy' }
AND gc_grace_seconds = 0;
