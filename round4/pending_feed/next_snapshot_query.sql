SELECT spawn_id, status, md5(final_response) AS fr_md5,
       length(final_response) AS fr_len, created_at AS created_epoch
FROM agent.subagent_spawns WHERE spawn_id > 432 ORDER BY spawn_id
