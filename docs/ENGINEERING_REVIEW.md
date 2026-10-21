# Engineering review — October 21, 2026

## Confirmed improvements on the portfolio branch
- Preserve the original Ames Housing `Order` identifier in `house_id` after removing outliers, rather than recreating IDs from DataFrame positions.
- Write the prepared CSV into the directory exposed to the HDFS NameNode.
- Use PostgreSQL host port 5433 for host-side scripts (matching Docker Compose).
- Import properties with keyed UPSERT rather than clearing tables and training history.
- Connect Spark containers to the PostgreSQL Docker network in addition to HDFS.
- Rename the training metrics in the initial SQL schema as `*_train` (and retain legacy column mapping in the writer).
- Add a guard in the visualization script for mismatched sale prices in prediction joins.
- Provide introductory English documentation with an architecture diagram, explicit limits, and a verification recipe.

## Validation limits
The code was reviewed against the remote source tree, but no full service-level stack was executed in the GitHub connector session. Tests are included for local execution; successful full integration is **not claimed**.

## Known blockers / next actions
1. Verify Docker Compose configuration on a developer's machine.
2. Wire a compatible PostgreSQL JDBC driver into `spark-submit`.
3. Run an isolated fresh development database; persistent volumes do not receive schema changes automatically.
4. Do not blindly migrate or discard existing `*_cv` columns/data.
5. Re-run the complete dataset import and Spark training, then regenerate charts.
6. Improve ML methodology by fitting imputers and encoders on training data only.
7. Reconcile any unpublished Codex local workspace changes before applying this branch locally.
8. Distinguish historical UI concepts from working apps and historical metrics from reproduced experiments.
