# 🚀 Build in Public Log

This file is automatically managed by your local `.git/hooks/pre-push` hook.
Every time you push code, the hook summarizes your diff and appends it to the `UNPOSTED PROGRESS` section.
3-4 times a day, the background scheduler reads the unposted progress, writes a massive LinkedIn post, and moves the logs to `ARCHIVED PROGRESS`.

---

## UNPOSTED PROGRESS
*(New entries will be automatically appended here by the Git Hook)*


## ARCHIVED PROGRESS
## [2026-06-14] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
638519f fix: archived_content NameError in bip_scheduler

Diff Summary:
workers/bip_scheduler.py | 1 +
 1 file changed, 1 insertion(+)


## [2026-06-14] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
638519f fix: archived_content NameError in bip_scheduler

Diff Summary:
workers/bip_scheduler.py | 1 +
 1 file changed, 1 insertion(+)


## [2026-06-13] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
f87bc17 add huggingface config to readme

Diff Summary:
README.md | 10 +++++++++-
 1 file changed, 9 insertions(+), 1 deletion(-)


## [2026-06-13] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
f87bc17 add huggingface config to readme

Diff Summary:
README.md | 10 +++++++++-
 1 file changed, 9 insertions(+), 1 deletion(-)


## [2026-06-13] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
1e604cc feat: implement autonomous build in public and fix dispatcher
db1cb18 chore: include .env for HF Space deployment
c0f5de8 feat: dynamic 30-template carousel engine, updated persona, Dockerfile for HF deployment

Diff Summary:
.gitignore                                         |    54 +-
 linkedin/BUILD_LOG.md => BUILD_LOG.md              |     0
 Dockerfile                                         |    19 +-
 Guides/AGENTS.md                                   |  1049 -
 Guides/GAPS_AND_FIXES.md                           |  2340 --
 Guides/GAPS_FINAL.md                               |  1929 -
 Guides/OYBIT_GAP_SOLUTIONS.md                      |  2322 --
 Guides/TESTS.md                                    |   756 -
 Guides/architecture.md                             |   327 -
 Guides/deployment_and_runbook.md                   |   423 -
 Guides/features.md                                 |   422 -
 Guides/ffff.md                                     |  1735 -
 Guides/gaps_list.txt                               |   141 -
 Guides/how_it_works.md                             |   269 -
 Guides/integrations_and_apis.md                    |   579 -
 Guides/last.md                                     |  1879 -
 Guides/persona_learning_and_trend_engine.md        |   455 -
 Guides/platforms.md                                |   250 -
 Guides/product.md                                  |   139 -
 PHASE_2_ROADMAP.md                                 |    35 -
 README.md                                          |    92 +-
 alembic.ini                                        |    37 -
 alembic/env.py                                     |     4 +-
 {backend => analytics}/__init__.py                 |     0
 .../analytics => analytics}/advanced_analytics.py  |     0
 {linkedin/analytics => analytics}/aggregator.py    |     0
 .../analytics => analytics}/audience_quality.py    |     0
 {linkedin/analytics => analytics}/cold_start.py    |     0
 .../analytics => analytics}/comment_sentiment.py   |     0
 .../analytics => analytics}/follows_tracker.py     |     0
 .../analytics => analytics}/pattern_detector.py    |     0
 {linkedin/analytics => analytics}/scorer.py        |     0
 {backend/analytics => api_routes}/__init__.py      |     0
 {linkedin/api_routes => api_routes}/analytics.py   |     0
 {linkedin/api_routes => api_routes}/content.py     |     0
 {linkedin/api_routes => api_routes}/growth.py      |     0
 {linkedin/api_routes => api_routes}/guardian.py    |     0
 .../api_routes => api_routes}/intelligence.py      |     0
 {linkedin/api_routes => api_routes}/media.py       |     0
 {linkedin/api_routes => api_routes}/mirofish.py    |     0
 {linkedin/api_routes => api_routes}/persona.py     |     0
 {linkedin/api_routes => api_routes}/personas.py    |     0
 {linkedin/api_routes => api_routes}/system.py      |     0
 {linkedin/api_routes => api_routes}/webhooks.py    |     0
 {linkedin/api_routes => api_routes}/workers.py     |     0
 backend/alerts/telegram.py                         |    66 -
 backend/analytics/aggregator.py                    |   205 -
 backend/analytics/audience_quality.py              |   151 -
 backend/analytics/cold_start.py                    |    71 -
 backend/analytics/comment_sentiment.py             |   142 -
 backend/analytics/follows_tracker.py               |    91 -
 backend/analytics/pattern_detector.py              |    47 -
 backend/analytics/scorer.py                        |    18 -
 backend/analytics_worker.py                        |    72 -
 backend/api/agent_a_routes.py                      |   215 -
 backend/api/agent_b_routes.py                      |   485 -
 backend/api/auth.py                                |   103 -
 backend/api/events.py                              |    22 -
 backend/api/external_events.py                     |    98 -
 backend/api/feedback.py                            |    22 -
 backend/api/health.py                              |    28 -
 backend/api/media_routes.py                        |   175 -
 backend/api/onboarding_routes.py                   |   117 -
 backend/api/pipeline.py                            |   694 -
 backend/api/pipeline_routes.py                     |   330 -
 backend/api/rate_limit_manager.py                  |   127 -
 backend/api/schemas.py                             |   133 -
 backend/api/ux_helpers.py                          |    95 -
 backend/api/vlog_upload.py                         |   110 -
 backend/api/waitlist.py                            |    36 -
 backend/brand_voice_guardian/checker.py            |   275 -
 backend/brand_voice_guardian/drift_detector.py     |    61 -
 backend/config.py                                  |    96 -
 backend/content/bulk.py                            |   108 -
 backend/content/deduplication.py                   |    44 -
 backend/content/generator.py                       |   251 -
 backend/content/parallel_gen.py                    |    32 -
 backend/content/poll_generator.py                  |   116 -
 backend/content/repurposer.py                      |   156 -
 backend/content/stories_generator.py               |   133 -
 backend/content/transcriber.py                     |   187 -
 backend/content/variation_enforcer.py              |   100 -
 backend/db/models.py                               |   383 -
 backend/db/session.py                              |    51 -
 backend/e2e_dry_run.py                             |   119 -
 backend/event_ingestion/telegram_listener.py       |   127 -
 backend/feedback_loop/archiver.py                  |    40 -
 backend/feedback_loop/buffer_manager.py            |   167 -
 backend/feedback_loop/learning_engine.py           |   332 -
 backend/feedback_loop/persona_patcher.py           |    80 -
 backend/feedback_worker.py                         |    75 -
 ...292834c28f54ff177096fc7902b7c59b7e8c5cf351.json |     1 -
 ...43d5754b8b8001a9cff3820c9f6c94e689f4e2c7de.json |     1 -
 ...0bf81aa713301f5ccce2f155cbe8521681083e06de.json |     1 -
 ...b5221886cc05ef100bd60b8d0f2dda86cb7d8455a7.json |     1 -
 ...e63e66696e82f1cf7f770c6ba4a89b8a0a2e96a5e3.json |     1 -
 ...c3a046e971d7b9980514fbafc2253a4a085c0d964d.json |     1 -
 ...75140c0ee8c42f055f92413396d5c607af66648366.json |     1 -
 ...be30231bd2ea700a3e9515b308b50a9053c06a19a7.json |     1 -
 ...606215d32c056c646be3dbfec8a8a385f9b9b22314.json |     1 -
 ...3b3f749665a17cd527d875816e498395008d947460.json |     1 -
 ...c45d2923e4ca3c44862e9d82f7f1964ea40a2cc6ec.json |     1 -
 ...6468e6ed221881ab90d1dc8cd6a342f0c1ed80c6c8.json |     1 -
 ...eff6c555a30420631015dc70b7a952be19c7d2b74c.json |     1 -
 ...f6fffd78aa3e1a1a21d0588af5a4bd9f65ba9d8acf.json |     1 -
 ...877e58b548dc7ec238098b1a83850e28985f7b335d.json |     1 -
 ...f7cb6415afcf41c0a1447eb75638c8121904106a6d.json |     1 -
 ...217512a9b1e8bdd152ddc1732a2bfddbdedf5600ff.json |     1 -
 ...eeadaf70b0b818c0a0ffe1942360b7082c50c65dfa.json |     1 -
 ...8e971c945b0d623457652632f170788bef3192e733.json |     1 -
 ...e86915158ea5cb8b51e454171839c9a672b5f2950d.json |     1 -
 ...683260fc440926a6f0affe00c496e3dd3b8a070434.json |     1 -
 ...bbb0492e8765915b0a5e2b9cda6ac223473df6ec08.json |     1 -
 ...23ca9f41b6f729a23ec5a07695e8ea7cc67a5660ba.json |     1 -
 ...153b148f93f0728a7a21b997b3e669c81b351b13f5.json |     1 -
 ...abb7401a13afd2a287ecef49f316e16678a796d2f2.json |     1 -
 ...df274388f8288461a72425f0104a41ed4922a52823.json |     1 -
 ...04bf50dc966a0585535b294a6ea8f70f7a6c42ee0a.json |     1 -
 ...ce04a5bcdbe9994c985a89f47dafbd30b100a0d971.json |     1 -
 ...ec0cbd46c78f3a2249c76da5826363b65470adaede.json |     1 -
 ...fb5f5bfbd2ad408f2f8407e7898bfa065a36a3566c.json |     1 -
 ...51387cb81a4c11850b5d099fc1c60adb3b4eea0eb0.json |     1 -
 ...b1d66d12b2b319d9811aa970dbe1764b8470049615.json |     1 -
 ...17802c9e05a604dec8f0abf00113bb40ba92cd05f1.json |     1 -
 ...6bec4163edf89015381d2b141082e0f44ff76316f6.json |     1 -
 ...937b0fcaf5e7a562bb8acc4fd97aeda7adae335c37.json |     1 -
 ...db328bc1cdadc9496c5999789e8601821665ab7dec.json |     1 -
 ...f3e50ce0ea69485d84cfb8227c221f8f98d0d4ddd4.json |     1 -
 ...9ee3d0b00f32118283b0ca2a900a32131e29f663ec.json |     1 -
 ...9acf444f84bac15cfa15f5e6ed8e51004508448e6d.json |     1 -
 ...80758d31deab9413fa0dd007c88a0c69d0165f55fb.json |     1 -
 ...5bc0437ff79f762f49909359114f9daf35be430dbe.json |     1 -
 ...53156e6f730eaa475b5cb14fcf0878a751924505cd.json |     1 -
 ...6d9ba2b3b6663c1295ac57c1f5d7fa03a5e3a7d055.json |     1 -
 ...4f2853e5cd5618d4189170191be6d9ebddae145a68.json |     1 -
 ...93c1c01a6c3598f516d8bffb4d1570cff70b24e1ec.json |     1 -
 ...cc18369d804789b1bff1424622b061651576f8f6a8.json |     1 -
 ...9abea4420a2ac618037cd685deeea942f74422e578.json |     1 -
 ...36675a449a3f6fc97027c205642f79e7a10c7d216e.json |     1 -
 ...555ecb235b2ecb00f2fedfab0194bc11b9e3b9fff0.json |     1 -
 ...75c55757c3c0e483de72fa13f98985365a8a7f1318.json |     1 -
 ...082e9de40de4673096a3c61fa105113d03bb6e043b.json |     1 -
 ...26cc61616735bff7dac60a09f61715a16605dc142a.json |     1 -
 ...73d462c83a6305e1d223dd747144cb565403a296f6.json |     1 -
 ...8c8559eb27fafb5ed9b67423e62a37216a6aa65f5f.json |     1 -
 ...88d4bf59482f2af029669bd270547d7f4c8d4e9d12.json |     1 -
 ...60ec564982bdb9153484015cc713b844383a59d7e9.json |     1 -
 ...b1f76d36d0b9702a83dd87c824975c6f22541d452e.json |     1 -
 ...c32b86d014c82b4625c5d487b38ffc47103692f316.json |     1 -
 ...4aecd921b399fab369aeac851ebfdacbc46e376c65.json |     1 -
 ...b810381bb4caac0b4a1bc6282a623cfdfd1711d33a.json |     1 -
 ...81b421908e7ad3a0ab3a1e099537568650a3f0242d.json |     1 -
 ...baf32999a9070ccc100f7f0ed5273872a2fc7df87a.json |     1 -
 ...0ec02c3b42b7691bafd6b652b5571cfc6bcd3377a9.json |     1 -
 ...f9d60cd7efc0948578610ba4f54a5519c7c7d7ecc0.json |     1 -
 ...e7644b51917ecb0690ade74dc515ff4bf1eb484df5.json |     1 -
 ...1b985d0b0074058f30bbab9bd60c097924ee8d6bf4.json |     1 -
 ...c89a5e61e53b1dc6e4f5eeb1eb414d1d0382a9b1a1.json |     1 -
 ...5c1ca6c001a34f78fe7261457967d90c3699de347b.json |     1 -
 ...19e20e93221516ef4e3091756614f244e2de959724.json |     1 -
 ...0a100a1c05ecf94b6df53d638b32ad7a173610cfb5.json |     1 -
 ...7f6f0642aab2eda9a22b8e3d78eb1d6d8fc0706786.json |     1 -
 ...fd5b54c87701c161fa5fbae51962ef6161cab1d018.json |     1 -
 ...e6a6c826fafd9632c4c4d079c19c362d9a6984f4b7.json |     1 -
 ...a0a2ad68372871b4d3f4101f0a0075fbce84ff8727.json |     1 -
 ...1bb34abc56b21ae35c5e3445ebbf926f39599fd3fc.json |     1 -
 ...ed894665de47e730c655a2bee57a4948d81a9fe45c.json |     1 -
 ...dfc941f4b226980b5f731ce0943748d29711b9067d.json |     1 -
 ...3047eb3aebfc15a20485e64437adadd247521f2072.json |     1 -
 ...249b35192ebc43a1dde71efe07d4944db922928d23.json |     1 -
 ...0c2a88464ed2a254eec978affb7563ad62db01a111.json |     1 -
 ...8fe1478e0508fbf6ed031bb52b78fbd15f8b873838.json |     1 -
 ...0dbecf15638337a4321ff9128dd59806b43b9a1f50.json |     1 -
 ...3a966774841b414c92fcebde9ab0fbc46a77ce332f.json |     1 -
 ...e9abd57b2e39d226a3a66f16ae0eef92546ff23c01.json |     1 -
 ...cfe0b245e2a56745731f274f5e7689a2be0df62d39.json |     1 -
 ...a032e9775b23039c8d2c743aa7abd4eaa7ff976b5e.json |     1 -
 ...342ce8c2d1ee3eb5def21b510f426a50c8db6d411a.json |     1 -
 ...29960cf68236927f16b1cbc562048dc8ba4a1ab960.json |     1 -
 ...d6b0c9eb395e1812fdd3b859b8deeec63b273ae209.json |     1 -
 ...4366ffb6710624d8788936f5bd38dbd7d2996116d2.json |     1 -
 ...4e47e19d6dae948f8abfbff7158018b2064c06c9b8.json |     1 -
 ...9888b3aee39ff0d31a2a31a7d9eabf0869d15ad157.json |     1 -
 ...f03e6df244234ec5f3d672070039e44cf64767dd10.json |     1 -
 ...5549cdad9d0879b118d341bf8801689679f9e31fa2.json |     1 -
 ...d9e31c41cd7236033a1477828e7f8acd35b941742a.json |     1 -
 ...59bfd483404464ecf817ef665fefef9af65a787715.json |     1 -
 ...4b665974eecd208faf707a51a1e7a958850402f6d7.json |     1 -
 ...a44bd6fe01e23d16344d4baa4c8e045e6571a81b99.json |     1 -
 ...a239f79359990cd152936169334b93446c69ca80ac.json |     1 -
 ...0369422d119f039a5372078f31f13bf26df4eb1d69.json |     1 -
 ...7b0f46b4c2860e6fd6f20bd4db17589466e6a33bf8.json |     1 -
 ...6631f3fbd87e1a63b067ea3c8a111a03ac22762968.json |     1 -
 ...98552a728895245ce05bc9b801970427917c3cbef7.json |     1 -
 ...4e521eb0cdcbe2a5a6c5d1803c6345efb2f0a9d7b7.json |     1 -
 ...7366fce5afaa4e2c9fa9129662393cedc628cb30a1.json |     1 -
 ...29dbb0d1346488899ddb1091c9f150cab6db6d2558.json |     1 -
 ...a4c5f0161ed77abf0a8ef91bf4e9f51705f4c9ab1e.json |     1 -
 ...7344e82d3d5d1a4e5c9b4bdc894f7881f984910d1a.json |     1 -
 ...2e1e51260e0f6bd435a5d0cf361a2444b504e94f39.json |     1 -
 ...7a92efed75e710269039a5b5f481e3aaf99e725522.json |     1 -
 ...2ff88e76fa9e389a8653b304ed7a0b22fb9326464c.json |     1 -
 ...450f77c399746d28556efeb894df05868ad596ad7a.json |     1 -
 ...5828c5d8c7b175885e9d735c4339cccbcda0f880da.json |     1 -
 ...6177e266d410fafb434b2ccc6f00a37b1586fa90f4.json |     1 -
 ...ebffabb2e42045e85fe248d2344884ee420cef1f2a.json |     1 -
 ...32a83e10f0fdc9261b21dadebb6e61bb500ecd4f07.json |     1 -
 ...76fa9ba90147fa868761789939ec36185d4ae698f8.json |     1 -
 ...54bb7fbb02a35a4be533dde07b9f8bd86e35148074.json |     1 -
 ...5888f7cb0722650bc264905ef3cf39cb1f918e639e.json |     1 -
 ...baaeee61085dea9bd09687e83f1aea382d95931b44.json |     1 -
 ...09674571394199fa33e705778426f5c48e5d67581a.json |     1 -
 ...e3247af99cf67071bfbeae39384de3b4d5f25366d0.json |     1 -
 ...25887495c60caccaa26c09f82db9534a55c09d4d2d.json |     1 -
 ...4a87a2d7b19dcd3b658ba7e82e2e0a3b3f197164ce.json |     1 -
 ...03f05e14cf9dfeb0bc7877c8b521b1c6fc58e895ea.json |     1 -
 ...2490662a5876c7f76e7080b5120ec2a61b1f8c352f.json |     1 -
 ...780afd672cab05a9575c2a82f1839c21597668cc09.json |     1 -
 ...afcd1489c5ff7797c536d51780293a82de7da3d6eb.json |     1 -
 ...7a5753e1190cf7bcdba8ec194f228fe2c6c4ff6c31.json |     1 -
 ...0538484c45fc471bc77e46c750ac7729cc3357e6a5.json |     1 -
 ...02bf62e4a0158d8dfe4cf7285013c2deab06024daf.json |     1 -
 ...827bd227cc7b96ba431d5166693fafe97719a4f39f.json |     1 -
 ...db35d90935a07a134a87af55cdab9f10dd494a2484.json |     1 -
 ...07d9dd34740a860204d871873df866b65b55f5b6b3.json |     1 -
 ...09e1e4cf78f4f79a1fd239178f7ecf5a0a34be1891.json |     1 -
 ...0937b2c5482a844b651624c6612fac38957499b2b9.json |     1 -
 ...0f48c6cf64f636aa1df55d5c1724e4451995578a7f.json |     1 -
 ...7599d2b1e8523d5a94285e75d952e69f5ce71415d1.json |     1 -
 ...3c40f36867b4336cd9bf2b5deb480a5733a5ddb255.json |     1 -
 ...0ebc3ef0a78636e1cab3b0cdf9c635c50d8a17604c.json |     1 -
 ...44ace449d1633a7d9415677475bd5f78439230b9f7.json |     1 -
 ...7279c9ea5bb6c9650ee9a13c8decd3fc7b29ad5f23.json |     1 -
 ...952613d2d3b8efef01232228fb0de245541d6ff384.json |     1 -
 ...c51743360e275e64bc953523b05bcdd936a8b7710c.json |     1 -
 ...1dcf1b5e8f4fa9ecd70bd912ac80e3a7e420b3afab.json |     1 -
 ...dd8702524b8c6763d7cd0854313d7b3acf1fc6e4c4.json |     1 -
 ...3f482822b1da9557e6d7489492ccef268cf4f53963.json |     1 -
 ...1b1dc196618c96e8c6fe5438fa7f632fc686253b94.json |     1 -
 ...9710c98f512292877fbc911251038457a30f91d4d8.json |     1 -
 ...ed415e1682711e460a278ef75c43a4efd3fb94fe3e.json |     1 -
 ...7e6d9b68f5b4766b1260d78e18d9c1da491ce2f9f9.json |     1 -
 ...332de44cd25719da43c2599ecece2167a00647304f.json |     1 -
 ...d9405d1e56627ed2c4358e6fd54ba6c56fb004f049.json |     1 -
 ...cf32e8b57c7f742ebffbd2731f7049a3bb63efa65c.json |     1 -
 ...2793126957dcf74aa0886a35db5c952b578d2a9940.json |     1 -
 ...49e1a6e13301bb4abbdea1f4adb4eb2c262f6d1d6f.json |     1 -
 ...6ba1673e3c71fff1348096a31d49c6daf1ae6d8b9c.json |     1 -
 ...6af4849f881f247c40ab70de96a56fb2afb872513b.json |     1 -
 ...79566a013509c56a348e17599449ea303e9957374c.json |     1 -
 backend/growth/comment_opportunities.py            |    45 -
 backend/growth/follow_strategy.py                  |   174 -
 backend/growth/reddit_commenter.py                 |    47 -
 backend/intelligence/cultural_calendar.py          |    82 -
 backend/intelligence/mirofish/agent_spawner.py     |   218 -
 .../intelligence/mirofish/narrative_forecaster.py  |   158 -
 backend/intelligence/mirofish/pre_publish_gate.py  |   309 -
 backend/intelligence/mirofish/simulation_runner.py |   301 -
 backend/intelligence/mirofish_client.py            |   556 -
 backend/intelligence/opportunity_detector.py       |   188 -
 backend/intelligence/persona_generator.py          |   114 -
 backend/intelligence/scorer.py                     |   142 -
 backend/intelligence/sensitive_moment_detector.py  |    85 -
 backend/intelligence/trend_aggregator.py           |   184 -
 backend/logger.py                                  |    77 -
 backend/main.py                                    |   260 -
 backend/mirofish/stability.py                      |   115 -
 backend/mirofish_worker.py                         |    94 -
 backend/notifications/telegram_alerter.py          |    40 -
 backend/onboarding/calibration.py                  |   204 -
 backend/onboarding/questions.py                    |   290 -
 backend/onboarding/scenario_bank/tech_founder.json |    26 -
 backend/onboarding/sim_engine.py                   |   345 -
 backend/onboarding/waitlist.py                     |   139 -
 backend/opportunity_worker.py                      |   164 -
 backend/persona_data/fb_brand_strategy.md          |   277 -
 backend/persona_data/fb_personal_strategy.md       |   248 -
 backend/persona_data/ig_brand_strategy.md          |   241 -
 backend/persona_data/ig_personal_strategy.md       |   232 -
 backend/persona_data/linkedin_personal_strategy.md |   289 -
 backend/persona_data/linkedin_strategy.md          |    87 -
 backend/persona_data/master_strategy.md            |    60 -
 backend/persona_data/master_strategy_doc.md        |   295 -
 backend/persona_engine/builder.py                  |   257 -
 backend/persona_engine/drift_detector.py           |    97 -
 backend/publishers/__init__.py                     |    35 -
 backend/publishers/dispatcher.py                   |    87 -
 backend/publishers/instagram_brand.py              |   128 -
 backend/publishers/instagram_personal.py           |   224 -
 backend/publishers/linkedin_polls.py               |    46 -
 backend/publishers/meta_error_handler.py           |    25 -
 backend/render_engine/__init__.py                  |     0
 backend/render_engine/asset_manager.py             |    81 -
 backend/render_engine/carousel.py                  |   190 -
 backend/render_engine/image.py                     |    74 -
 backend/render_engine/prompt_builder.py            |   151 -
 backend/render_engine/render_fixes.py              |   121 -
 backend/render_engine/render_queue.py              |    52 -
 backend/render_engine/templates/__init__.py        |   331 -
 backend/render_engine/templates/carousel_base.html |    25 -
 .../render_engine/templates/carousel_brand_ig.html |   201 -
 .../templates/carousel_brutalist.html              |   181 -
 .../render_engine/templates/carousel_glass.html    |   198 -
 .../render_engine/templates/carousel_gradient.html |   184 -
 .../render_engine/templates/carousel_linkedin.html |   277 -
 backend/render_engine/templates/trending_take.html |   113 -
 backend/render_engine/templates/video/__init__.py  |     0
 backend/render_engine/video.py                     |   147 -
 backend/reply_manager/__init__.py                  |     0
 backend/reply_manager/drafter.py                   |   103 -
 backend/reply_manager/monitor.py                   |   165 -
 backend/reply_manager/sender.py                    |   124 -
 backend/reply_manager/templates.py                 |   239 -
 backend/reply_worker.py                            |   105 -
 backend/safety/crisis_pause.py                     |    69 -
 backend/safety/sanitizer.py                        |    47 -
 backend/scheduler_worker/__init__.py               |     0
 backend/scheduler_worker/autonomous_loop.py        |   209 -
 backend/scheduler_worker/cron.py                   |    96 -
 backend/scheduler_worker/dispatcher.py             |   138 -
 backend/scheduler_worker/queue.py                  |   129 -
 backend/security/breach_runbook.py                 |    54 -
 backend/test.jpg                                   |   Bin 10113 -> 0 bytes
 backend/test_pw.py                                 |    32 -
 backend/token_store/__init__.py                    |     0
 backend/token_store/refresher.py                   |   243 -
 backend/token_store/store.py                       |   138 -
 backend/trend_worker.py                            |    71 -
 backend/trigger_carousel.py                        |    29 -
 backend/utils/algorithm_rules.py                   |    91 -
 backend/utils/archive.py                           |    48 -
 backend/utils/audit_log.py                         |    64 -
 backend/utils/content_guards.py                    |   132 -
 backend/utils/exceptions.py                        |    40 -
 backend/utils/file_ops.py                          |    31 -
 backend/utils/heartbeat.py                         |    54 -
 backend/utils/logger.py                            |    58 -
 backend/utils/ops.py                               |   166 -
 backend/utils/rate_limiter.py                      |   101 -
 backend/utils/shell.py                             |    19 -
 linkedin/config.py => config.py                    |     0
 .../data => data}/media_library/sample_founder.png |     0
 {linkedin/data => data}/media_library/tags.json    |     0
 data/personas/_template.md                         |   148 -
 data/personas/ahmad/persona.md                     |   466 +-
 {linkedin/data => data}/templates/dark_themes.html |     0
 .../data => data}/templates/light_themes.html      |     0
 {linkedin/data => data}/theme_state.json           |     0
 {backend/api => db}/__init__.py                    |     0
 {backend/db => db}/base.py                         |     0
 {linkedin/db => db}/models.py                      |     0
 {linkedin/db => db}/session.py                     |     0
 diagram.md                                         |   224 -
 docs/TOKEN_BREACH_RUNBOOK.md                       |    29 -
 .../__init__.py                                    |     0
 .../feedback_loop => feedback_loop}/archiver.py    |     0
 .../buffer_manager.py                              |     0
 .../learning_engine.py                             |     0
 .../mirofish_refiner.py                            |     0
 .../persona_patcher.py                             |     0
 frontend                                           |     1 -
 graphify-out/.graphify_analysis.json               |  1933 -
 graphify-out/.graphify_ast.json                    | 35007 ------------------
 graphify-out/.graphify_ast_frontend.json           |  2333 --
 graphify-out/.graphify_detect.json                 |     1 -
 graphify-out/.graphify_detect_frontend.json        |     1 -
 graphify-out/.graphify_extract.json                | 35008 ------------------
 graphify-out/.graphify_extract_frontend.json       |  2334 --
 graphify-out/.graphify_python                      |     1 -
 graphify-out/.graphify_uncached.txt                |   168 -
 graphify-out/GRAPH_REPORT.md                       |   715 -
 graphify-out/backend_graph.html                    |   266 -
 graphify-out/frontend_graph.html                   |   266 -
 graphify-out/graph.json                            | 36326 -------------------
 .../growth => growth}/comment_opportunities.py     |     0
 {backend/growth => growth}/event_ingestion.py      |     0
 {backend/growth => growth}/facebook_groups.py      |     0
 {linkedin/growth => growth}/follow_strategy.py     |     0
 {backend/growth => growth}/growth_modules.py       |     0
 {backend/growth => growth}/instagram_collab.py     |     0
 {backend/growth => growth}/linkedin_groups.py      |     0
 {backend/growth => growth}/linkedin_newsletter.py  |     0
 {linkedin/growth => growth}/reddit_commenter.py    |     0
 {backend/content => guardian}/__init__.py          |     0
 {linkedin/guardian => guardian}/checker.py         |     0
 {linkedin/guardian => guardian}/drift_detector.py  |     0
 {backend/db => intelligence}/__init__.py           |     0
 .../content_dna_checker.py                         |     0
 .../cultural_calendar.py                           |     0
 .../mirofish}/__init__.py                          |     0
 .../mirofish/agent_spawner.py                      |     0
 .../mirofish/graph_builder.py                      |     0
 .../mirofish/narrative_forecaster.py               |     0
 .../mirofish/pre_publish_gate.py                   |     0
 .../mirofish/report_agent.py                       |     0
 .../mirofish/seed_builder.py                       |     0
 .../mirofish/simulation_runner.py                  |     0
 .../mirofish_client.py                             |     0
 .../opportunity_detector.py                        |     0
 .../persona_generator.py                           |     0
 .../intelligence => intelligence}/persona_intel.py |     0
 {linkedin/intelligence => intelligence}/scorer.py  |     0
 .../sensitive_moment_detector.py                   |     0
 .../trend_aggregator.py                            |     0
 linkedin/.env                                      |    82 -
 linkedin/.env.example                              |    81 -
 linkedin/.gitignore                                |     9 -
 linkedin/Dockerfile                                |    26 -
 linkedin/README.md                                 |    41 -
 linkedin/alembic/env.py                            |    68 -
 linkedin/alembic/script.py.mako                    |    24 -
 linkedin/alembic/versions/.gitkeep                 |     1 -
 linkedin/analytics/__init__.py                     |     0
 linkedin/analytics/advanced_analytics.py           |   105 -
 linkedin/api_routes/__init__.py                    |     0
 linkedin/data/personas/ahmad/persona.md            |   425 -
 linkedin/data/personas/ahmad/simulation_log.md     |     3 -
 linkedin/db/__init__.py                            |     0
 linkedin/db/base.py                                |     3 -
 linkedin/feedback_loop/__init__.py                 |     0
 linkedin/feedback_loop/mirofish_refiner.py         |    44 -
 linkedin/growth/event_ingestion.py                 |    80 -
 linkedin/growth/facebook_groups.py                 |    53 -
 linkedin/growth/growth_modules.py                  |   104 -
 linkedin/growth/instagram_collab.py                |    35 -
 linkedin/growth/linkedin_groups.py                 |    50 -
 linkedin/growth/linkedin_newsletter.py             |    58 -
 linkedin/guardian/__init__.py                      |     0
 linkedin/intelligence/__init__.py                  |     0
 linkedin/intelligence/content_dna_checker.py       |   199 -
 linkedin/intelligence/mirofish/__init__.py         |     0
 linkedin/intelligence/persona_intel.py             |   148 -
 linkedin/llm/__init__.py                           |     0
 linkedin/llm/content_rules.py                      |   126 -
 linkedin/llm/platform_rules.py                     |    61 -
 linkedin/llm/prompt_injection.py                   |    31 -
 linkedin/mirofish/__init__.py                      |     0
 linkedin/mirofish/graph_builder.py                 |   270 -
 linkedin/mirofish/report_agent.py                  |    66 -
 linkedin/mirofish/seed_builder.py                  |   231 -
 linkedin/persona_engine/__init__.py                |     0
 linkedin/persona_engine/prompt_builder.py          |   232 -
 linkedin/persona_engine/rotation_trigger.py        |    80 -
 linkedin/persona_engine/updater.py                 |   301 -
 linkedin/publishers/bluesky_facets.py              |    87 -
 linkedin/publishers/facebook.py                    |    87 -
 linkedin/publishers/facebook_reels.py              |    71 -
 linkedin/publishers/instagram.py                   |   161 -
 linkedin/publishers/instagram_stories.py           |    70 -
 linkedin/publishers/linkedin.py                    |   225 -
 linkedin/publishers/payload_builders.py            |    87 -
 linkedin/publishers/pinterest.py                   |    80 -
 linkedin/publishers/post_verify.py                 |    49 -
 linkedin/publishers/reddit_safety.py               |    60 -
 linkedin/publishers/youtube.py                     |    90 -
 linkedin/requirements.txt                          |    54 -
 linkedin/scheduler_worker/__init__.py              |     0
 linkedin/scripts/bootstrap_pattern_db.py           |    58 -
 linkedin/scripts/check_tokens.py                   |   107 -
 linkedin/scripts/read_gap.py                       |    21 -
 linkedin/scripts/refresh_token.py                  |    84 -
 linkedin/scripts/retry_post.py                     |    74 -
 linkedin/scripts/setup_graphrag.py                 |    31 -
 linkedin/scripts/tests/run_all_agent_a.py          |   373 -
 .../scripts/tests/test_analytics_aggregator.py     |    26 -
 linkedin/scripts/tests/test_api_endpoints.py       |    23 -
 .../scripts/tests/test_brand_voice_guardian.py     |    70 -
 linkedin/scripts/tests/test_carousel_renderer.py   |    29 -
 linkedin/scripts/tests/test_content_dna_checker.py |    88 -
 linkedin/scripts/tests/test_content_generator.py   |    27 -
 linkedin/scripts/tests/test_image_generator.py     |    19 -
 .../scripts/tests/test_image_prompt_builder.py     |    30 -
 .../scripts/tests/test_independent_verification.py |   143 -
 linkedin/scripts/tests/test_learning_engine.py     |    98 -
 .../scripts/tests/test_mirofish_graph_builder.py   |    51 -
 .../tests/test_mirofish_pre_publish_gate.py        |    62 -
 .../scripts/tests/test_mirofish_seed_builder.py    |    55 -
 .../scripts/tests/test_opportunity_detector.py     |    48 -
 linkedin/scripts/tests/test_persona_builder.py     |    61 -
 linkedin/scripts/tests/test_persona_updater.py     |    82 -
 linkedin/scripts/tests/test_prompt_builder.py      |    57 -
 linkedin/scripts/tests/test_publishers.py          |    37 -
 linkedin/scripts/tests/test_real_api_calls.py      |   154 -
 linkedin/scripts/tests/test_reply_manager.py       |    26 -
 linkedin/scripts/tests/test_repurposer.py          |    19 -
 .../scripts/tests/test_scheduler_dispatcher.py     |    18 -
 linkedin/scripts/tests/test_scheduler_queue.py     |    21 -
 linkedin/scripts/tests/test_scorer.py              |    49 -
 linkedin/scripts/tests/test_sim_engine.py          |    67 -
 linkedin/scripts/tests/test_token_refresher.py     |    20 -
 linkedin/scripts/tests/test_token_store.py         |    30 -
 linkedin/scripts/tests/test_video_renderer.py      |    19 -
 linkedin/scripts/verify_connections.py             |   172 -
 linkedin/token_store/__init__.py                   |     0
 linkedin/workers/analytics_worker.py               |    38 -
 linkedin/workers/archive_worker.py                 |    70 -
 linkedin/workers/feedback_worker.py                |    97 -
 linkedin/workers/follow_worker.py                  |   125 -
 linkedin/workers/health_pinger.py                  |    44 -
 linkedin/workers/keepalive_worker.py               |    29 -
 linkedin/workers/mirofish_worker.py                |    72 -
 linkedin/workers/scheduler_worker.py               |    19 -
 linkedin/workers/token_refresher.py                |    43 -
 linkedin/workers/trend_worker.py                   |    43 -
 {backend/feedback_loop => llm}/__init__.py         |     0
 {linkedin/llm => llm}/bulk.py                      |     0
 {backend/content => llm}/content_rules.py          |     0
 {linkedin/llm => llm}/deduplication.py             |     0
 {linkedin/llm => llm}/generator.py                 |     0
 {linkedin/llm => llm}/parallel_gen.py              |     0
 {backend/content => llm}/platform_rules.py         |     0
 {linkedin/llm => llm}/poll_generator.py            |     0
 {backend/content => llm}/prompt_injection.py       |     0
 {linkedin/llm => llm}/repurposer.py                |     0
 {linkedin/llm => llm}/stories_generator.py         |     0
 {linkedin/llm => llm}/transcriber.py               |     0
 {linkedin/llm => llm}/variation_enforcer.py        |     0
 linkedin/logger.py => logger.py                    |     0
 linkedin/main.py => main.py                        |     0
 migrate_db.py                                      |    38 -
 mirofish                                           |     1 -
 {backend/intelligence => mirofish}/__init__.py     |     0
 {linkedin/mirofish => mirofish}/agent_spawner.py   |     0
 .../mirofish => mirofish}/graph_builder.py         |     0
 .../mirofish => mirofish}/narrative_forecaster.py  |     0
 {linkedin/mirofish => mirofish}/native/__init__.py |     0
 .../mirofish => mirofish}/native/graph_builder.py  |     0
 .../native/oasis_profile_generator.py              |     0
 .../native/ontology_generator.py                   |     0
 .../mirofish => mirofish}/native/report_agent.py   |     0
 .../native/simulation_config_generator.py          |     0
 .../mirofish => mirofish}/native/simulation_ipc.py |     0
 .../native/simulation_manager.py                   |     0
 .../native/simulation_runner.py                    |     0
 .../mirofish => mirofish}/native/text_processor.py |     0
 .../native/zep_entity_reader.py                    |     0
 .../native/zep_graph_memory_updater.py             |     0
 .../mirofish => mirofish}/native/zep_tools.py      |     0
 .../mirofish => mirofish}/pre_publish_gate.py      |     0
 .../mirofish => mirofish}/report_agent.py          |     0
 .../mirofish => mirofish}/seed_builder.py          |     0
 .../mirofish => mirofish}/simulation_runner.py     |     0
 new                                                |   293 -
 nixpacks.toml                                      |    35 -
 ...persona_60q.md => oybit_linkedin_persona_60q.md |     0
 .../mirofish => persona_engine}/__init__.py        |     0
 .../persona_engine => persona_engine}/builder.py   |     0
 .../drift_detector.py                              |     0
 .../prompt_builder.py                              |     0
 .../rotation_trigger.py                            |     0
 .../persona_engine => persona_engine}/updater.py   |     0
 {linkedin/publishers => publishers}/__init__.py    |     0
 .../publishers => publishers}/bluesky_facets.py    |     0
 {linkedin/publishers => publishers}/dispatcher.py  |     0
 {backend/publishers => publishers}/facebook.py     |     0
 .../publishers => publishers}/facebook_reels.py    |     0
 {backend/publishers => publishers}/instagram.py    |     0
 .../publishers => publishers}/instagram_brand.py   |     0
 .../instagram_personal.py                          |     0
 .../publishers => publishers}/instagram_stories.py |     0
 {backend/publishers => publishers}/linkedin.py     |     0
 .../publishers => publishers}/linkedin_polls.py    |     0
 .../meta_error_handler.py                          |     0
 .../publishers => publishers}/payload_builders.py  |     0
 {backend/publishers => publishers}/pinterest.py    |     0
 {backend/publishers => publishers}/post_verify.py  |     0
 .../publishers => publishers}/reddit_safety.py     |     0
 {backend/publishers => publishers}/youtube.py      |     0
 read_test_out.py                                   |    16 -
 render.yaml                                        |    45 -
 .../render_engine => render_engine}/__init__.py    |     0
 .../render_engine => render_engine}/carousel.py    |     0
 .../onboarding => scheduler_worker}/__init__.py    |     0
 .../autonomous_loop.py                             |     0
 .../scheduler_worker => scheduler_worker}/cron.py  |     0
 .../dispatcher.py                                  |     0
 .../scheduler_worker => scheduler_worker}/queue.py |     0
 scripts/bootstrap_pattern_db.py                    |     4 +-
 scripts/retry_post.py                              |     6 +-
 scripts/setup_graphrag.py                          |     2 +-
 scripts/tests/run_all_agent_a.py                   |    26 +-
 scripts/tests/test_analytics_aggregator.py         |     2 +-
 scripts/tests/test_brand_voice_guardian.py         |    10 +-
 scripts/tests/test_carousel_renderer.py            |     2 +-
 scripts/tests/test_content_dna_checker.py          |     2 +-
 scripts/tests/test_content_generator.py            |     2 +-
 scripts/tests/test_image_prompt_builder.py         |     2 +-
 scripts/tests/test_independent_verification.py     |    10 +-
 scripts/tests/test_learning_engine.py              |     2 +-
 scripts/tests/test_mirofish_graph_builder.py       |     6 +-
 scripts/tests/test_mirofish_pre_publish_gate.py    |     8 +-
 scripts/tests/test_mirofish_seed_builder.py        |     8 +-
 scripts/tests/test_opportunity_detector.py         |     6 +-
 scripts/tests/test_persona_builder.py              |     6 +-
 scripts/tests/test_persona_updater.py              |     4 +-
 .../scripts => scripts}/tests/test_pipeline.py     |     0
 scripts/tests/test_prompt_builder.py               |     6 +-
 scripts/tests/test_publishers.py                   |     4 +-
 scripts/tests/test_reply_manager.py                |     2 +-
 scripts/tests/test_scheduler_queue.py              |     2 +-
 scripts/tests/test_scorer.py                       |     6 +-
 scripts/tests/test_sim_engine.py                   |     8 +-
 scripts/tests/test_token_store.py                  |     2 +-
 {linkedin/services => services}/llm.py             |     0
 {linkedin/services => services}/media_selector.py  |     0
 {linkedin/services => services}/persona_engine.py  |     0
 .../services => services}/persona_questions.py     |     0
 start.bat                                          |    22 -
 .../persona_engine => token_store}/__init__.py     |     0
 {linkedin/token_store => token_store}/refresher.py |     0
 {linkedin/token_store => token_store}/store.py     |     0
 workers/analytics_worker.py                        |     4 +-
 workers/archive_worker.py                          |     4 +-
 {linkedin/workers => workers}/bip_scheduler.py     |     0
 workers/feedback_worker.py                         |    23 +-
 workers/follow_worker.py                           |     8 +-
 workers/health_pinger.py                           |     6 +-
 workers/mirofish_worker.py                         |    17 +-
 workers/scheduler_worker.py                        |     2 +-
 workers/token_refresher.py                         |    14 +-
 workers/trend_worker.py                            |    14 +-
 621 files changed, 599 insertions(+), 156502 deletions(-)


## [2026-06-13] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
9e426af add root env for huggingface

Diff Summary:
.env | 82 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 82 insertions(+)

## [2026-06-13] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
3198c3b feat: implement autonomous build in public and fix dispatcher
5505007 chore: include .env for HF Space deployment
4e875e3 chore: remove .env from tracking â€” secrets must not be committed
5a65e5c feat: dynamic 30-template carousel engine, updated persona, Dockerfile for HF deployment

Diff Summary:
.env => linkedin/.env                              |    4 +-
 linkedin/.env.example                              |   81 +
 linkedin/.gitignore                                |    9 +
 linkedin/BUILD_LOG.md                              |   17 +
 linkedin/Dockerfile                                |   26 +
 linkedin/README.md                                 |   41 +
 linkedin/alembic/env.py                            |   68 +
 linkedin/alembic/script.py.mako                    |   24 +
 linkedin/alembic/versions/.gitkeep                 |    1 +
 linkedin/analytics/__init__.py                     |    0
 linkedin/analytics/advanced_analytics.py           |  105 +
 linkedin/analytics/aggregator.py                   |  205 ++
 linkedin/analytics/audience_quality.py             |  151 ++
 linkedin/analytics/cold_start.py                   |   71 +
 linkedin/analytics/comment_sentiment.py            |  142 ++
 linkedin/analytics/follows_tracker.py              |   91 +
 linkedin/analytics/pattern_detector.py             |   47 +
 linkedin/analytics/scorer.py                       |   18 +
 linkedin/api_routes/__init__.py                    |    0
 linkedin/api_routes/analytics.py                   |   45 +
 linkedin/api_routes/content.py                     |  234 ++
 linkedin/api_routes/growth.py                      |   24 +
 linkedin/api_routes/guardian.py                    |   19 +
 linkedin/api_routes/intelligence.py                |   27 +
 linkedin/api_routes/media.py                       |   15 +
 linkedin/api_routes/mirofish.py                    |  181 ++
 linkedin/api_routes/persona.py                     |   53 +
 linkedin/api_routes/personas.py                    |  326 +++
 linkedin/api_routes/system.py                      |   11 +
 linkedin/api_routes/webhooks.py                    |   86 +
 linkedin/api_routes/workers.py                     |   15 +
 linkedin/config.py                                 |   97 +
 linkedin/data/media_library/sample_founder.png     |    0
 linkedin/data/media_library/tags.json              |    1 +
 linkedin/data/personas/ahmad/persona.md            |  425 ++++
 linkedin/data/personas/ahmad/simulation_log.md     |    3 +
 linkedin/data/templates/dark_themes.html           |  463 ++++
 linkedin/data/templates/light_themes.html          |  464 ++++
 linkedin/data/theme_state.json                     |    1 +
 linkedin/db/__init__.py                            |    0
 linkedin/db/base.py                                |    3 +
 linkedin/db/models.py                              |  383 +++
 linkedin/db/session.py                             |   49 +
 linkedin/feedback_loop/__init__.py                 |    0
 linkedin/feedback_loop/archiver.py                 |   40 +
 linkedin/feedback_loop/buffer_manager.py           |  167 ++
 linkedin/feedback_loop/learning_engine.py          |  332 +++
 linkedin/feedback_loop/mirofish_refiner.py         |   44 +
 linkedin/feedback_loop/persona_patcher.py          |   80 +
 linkedin/growth/comment_opportunities.py           |   45 +
 linkedin/growth/event_ingestion.py                 |   80 +
 linkedin/growth/facebook_groups.py                 |   53 +
 linkedin/growth/follow_strategy.py                 |  174 ++
 linkedin/growth/growth_modules.py                  |  104 +
 linkedin/growth/instagram_collab.py                |   35 +
 linkedin/growth/linkedin_groups.py                 |   50 +
 linkedin/growth/linkedin_newsletter.py             |   58 +
 linkedin/growth/reddit_commenter.py                |   47 +
 linkedin/guardian/__init__.py                      |    0
 linkedin/guardian/checker.py                       |  275 +++
 linkedin/guardian/drift_detector.py                |   61 +
 linkedin/intelligence/__init__.py                  |    0
 linkedin/intelligence/content_dna_checker.py       |  199 ++
 linkedin/intelligence/cultural_calendar.py         |   82 +
 linkedin/intelligence/mirofish/__init__.py         |    0
 linkedin/intelligence/mirofish/agent_spawner.py    |  218 ++
 linkedin/intelligence/mirofish/graph_builder.py    |  270 ++
 .../intelligence/mirofish/narrative_forecaster.py  |  158 ++
 linkedin/intelligence/mirofish/pre_publish_gate.py |  309 +++
 linkedin/intelligence/mirofish/report_agent.py     |   66 +
 linkedin/intelligence/mirofish/seed_builder.py     |  231 ++
 .../intelligence/mirofish/simulation_runner.py     |  301 +++
 linkedin/intelligence/mirofish_client.py           |  556 +++++
 linkedin/intelligence/opportunity_detector.py      |  188 ++
 linkedin/intelligence/persona_generator.py         |  114 +
 linkedin/intelligence/persona_intel.py             |  148 ++
 linkedin/intelligence/scorer.py                    |  142 ++
 linkedin/intelligence/sensitive_moment_detector.py |   85 +
 linkedin/intelligence/trend_aggregator.py          |  184 ++
 linkedin/llm/__init__.py                           |    0
 linkedin/llm/bulk.py                               |  108 +
 linkedin/llm/content_rules.py                      |  126 +
 linkedin/llm/deduplication.py                      |   44 +
 linkedin/llm/generator.py                          |  251 ++
 linkedin/llm/parallel_gen.py                       |   32 +
 linkedin/llm/platform_rules.py                     |   61 +
 linkedin/llm/poll_generator.py                     |  116 +
 linkedin/llm/prompt_injection.py                   |   31 +
 linkedin/llm/repurposer.py                         |  156 ++
 linkedin/llm/stories_generator.py                  |  133 +
 linkedin/llm/transcriber.py                        |  187 ++
 linkedin/llm/variation_enforcer.py                 |  100 +
 linkedin/logger.py                                 |   77 +
 linkedin/main.py                                   |  128 +
 linkedin/mirofish/__init__.py                      |    0
 linkedin/mirofish/agent_spawner.py                 |  218 ++
 linkedin/mirofish/graph_builder.py                 |  270 ++
 linkedin/mirofish/narrative_forecaster.py          |  158 ++
 linkedin/mirofish/native/__init__.py               |   73 +
 linkedin/mirofish/native/graph_builder.py          |  506 ++++
 .../mirofish/native/oasis_profile_generator.py     | 1205 +++++++++
 linkedin/mirofish/native/ontology_generator.py     |  506 ++++
 linkedin/mirofish/native/report_agent.py           | 2572 ++++++++++++++++++++
 .../mirofish/native/simulation_config_generator.py |  992 ++++++++
 linkedin/mirofish/native/simulation_ipc.py         |  394 +++
 linkedin/mirofish/native/simulation_manager.py     |  529 ++++
 linkedin/mirofish/native/simulation_runner.py      | 1768 ++++++++++++++
 linkedin/mirofish/native/text_processor.py         |   71 +
 linkedin/mirofish/native/zep_entity_reader.py      |  437 ++++
 .../mirofish/native/zep_graph_memory_updater.py    |  554 +++++
 linkedin/mirofish/native/zep_tools.py              | 1736 +++++++++++++
 linkedin/mirofish/pre_publish_gate.py              |  322 +++
 linkedin/mirofish/report_agent.py                  |   66 +
 linkedin/mirofish/seed_builder.py                  |  231 ++
 linkedin/mirofish/simulation_runner.py             |  301 +++
 linkedin/oybit_linkedin_persona_60q.md             |  237 ++
 linkedin/persona_engine/__init__.py                |    0
 linkedin/persona_engine/builder.py                 |  257 ++
 linkedin/persona_engine/drift_detector.py          |   97 +
 linkedin/persona_engine/prompt_builder.py          |  232 ++
 linkedin/persona_engine/rotation_trigger.py        |   80 +
 linkedin/persona_engine/updater.py                 |  301 +++
 linkedin/publishers/__init__.py                    |   35 +
 linkedin/publishers/bluesky_facets.py              |   87 +
 linkedin/publishers/dispatcher.py                  |   78 +
 linkedin/publishers/facebook.py                    |   87 +
 linkedin/publishers/facebook_reels.py              |   71 +
 linkedin/publishers/instagram.py                   |  161 ++
 linkedin/publishers/instagram_brand.py             |  128 +
 linkedin/publishers/instagram_personal.py          |  224 ++
 linkedin/publishers/instagram_stories.py           |   70 +
 linkedin/publishers/linkedin.py                    |  225 ++
 linkedin/publishers/linkedin_polls.py              |   46 +
 linkedin/publishers/meta_error_handler.py          |   25 +
 linkedin/publishers/payload_builders.py            |   87 +
 linkedin/publishers/pinterest.py                   |   80 +
 linkedin/publishers/post_verify.py                 |   49 +
 linkedin/publishers/reddit_safety.py               |   60 +
 linkedin/publishers/youtube.py                     |   90 +
 linkedin/render_engine/__init__.py                 |    1 +
 linkedin/render_engine/carousel.py                 |  207 ++
 linkedin/requirements.txt                          |   54 +
 linkedin/scheduler_worker/__init__.py              |    0
 linkedin/scheduler_worker/autonomous_loop.py       |  209 ++
 linkedin/scheduler_worker/cron.py                  |   96 +
 linkedin/scheduler_worker/dispatcher.py            |  138 ++
 linkedin/scheduler_worker/queue.py                 |  129 +
 linkedin/scripts/bootstrap_pattern_db.py           |   58 +
 linkedin/scripts/check_tokens.py                   |  107 +
 linkedin/scripts/read_gap.py                       |   21 +
 linkedin/scripts/refresh_token.py                  |   84 +
 linkedin/scripts/retry_post.py                     |   74 +
 linkedin/scripts/setup_graphrag.py                 |   31 +
 linkedin/scripts/tests/run_all_agent_a.py          |  373 +++
 .../scripts/tests/test_analytics_aggregator.py     |   26 +
 linkedin/scripts/tests/test_api_endpoints.py       |   23 +
 .../scripts/tests/test_brand_voice_guardian.py     |   70 +
 linkedin/scripts/tests/test_carousel_renderer.py   |   29 +
 linkedin/scripts/tests/test_content_dna_checker.py |   88 +
 linkedin/scripts/tests/test_content_generator.py   |   27 +
 linkedin/scripts/tests/test_image_generator.py     |   19 +
 .../scripts/tests/test_image_prompt_builder.py     |   30 +
 .../scripts/tests/test_independent_verification.py |  143 ++
 linkedin/scripts/tests/test_learning_engine.py     |   98 +
 .../scripts/tests/test_mirofish_graph_builder.py   |   51 +
 .../tests/test_mirofish_pre_publish_gate.py        |   62 +
 .../scripts/tests/test_mirofish_seed_builder.py    |   55 +
 .../scripts/tests/test_opportunity_detector.py     |   48 +
 linkedin/scripts/tests/test_persona_builder.py     |   61 +
 linkedin/scripts/tests/test_persona_updater.py     |   82 +
 linkedin/scripts/tests/test_pipeline.py            |   31 +
 linkedin/scripts/tests/test_prompt_builder.py      |   57 +
 linkedin/scripts/tests/test_publishers.py          |   37 +
 linkedin/scripts/tests/test_real_api_calls.py      |  154 ++
 linkedin/scripts/tests/test_reply_manager.py       |   26 +
 linkedin/scripts/tests/test_repurposer.py          |   19 +
 .../scripts/tests/test_scheduler_dispatcher.py     |   18 +
 linkedin/scripts/tests/test_scheduler_queue.py     |   21 +
 linkedin/scripts/tests/test_scorer.py              |   49 +
 linkedin/scripts/tests/test_sim_engine.py          |   67 +
 linkedin/scripts/tests/test_token_refresher.py     |   20 +
 linkedin/scripts/tests/test_token_store.py         |   30 +
 linkedin/scripts/tests/test_video_renderer.py      |   19 +
 linkedin/scripts/verify_connections.py             |  172 ++
 linkedin/services/llm.py                           |  134 +
 linkedin/services/media_selector.py                |   46 +
 linkedin/services/persona_engine.py                |  100 +
 linkedin/services/persona_questions.py             |  494 ++++
 linkedin/token_store/__init__.py                   |    0
 linkedin/token_store/refresher.py                  |  243 ++
 linkedin/token_store/store.py                      |  138 ++
 linkedin/workers/analytics_worker.py               |   38 +
 linkedin/workers/archive_worker.py                 |   70 +
 linkedin/workers/bip_scheduler.py                  |  183 ++
 linkedin/workers/feedback_worker.py                |   97 +
 linkedin/workers/follow_worker.py                  |  125 +
 linkedin/workers/health_pinger.py                  |   44 +
 linkedin/workers/keepalive_worker.py               |   29 +
 linkedin/workers/mirofish_worker.py                |   72 +
 linkedin/workers/scheduler_worker.py               |   19 +
 linkedin/workers/token_refresher.py                |   43 +
 linkedin/workers/trend_worker.py                   |   43 +
 202 files changed, 31318 insertions(+), 2 deletions(-)


## [2026-06-13] - Pushed Commits
**Tags**: #BuildInPublic #Engineering
**Details**:
Commits:
3198c3b feat: implement autonomous build in public and fix dispatcher
5505007 chore: include .env for HF Space deployment
4e875e3 chore: remove .env from tracking â€” secrets must not be committed
5a65e5c feat: dynamic 30-template carousel engine, updated persona, Dockerfile for HF deployment
e41c748 fix: resolve 7 production bugs â€” JSON repair, health 503, opportunity race condition, Google Trends caching, Reddit PRAW auth, OpenRouter 502 retry, pytrends FutureWarning
217f19e fix: raise 500 error on MiroFish gate failure and log raw JSON to assist debugging
a03735a chore: update environment variables

Diff Summary:
backend/analytics_worker.py                        |    1 +
 backend/api/agent_a_routes.py                      |    3 +-
 backend/api/health.py                              |   65 +-
 backend/content/generator.py                       |   17 +-
 backend/feedback_worker.py                         |    1 +
 backend/intelligence/mirofish/seed_builder.py      |   83 +-
 backend/intelligence/mirofish/simulation_runner.py |   27 +-
 backend/intelligence/trend_aggregator.py           |   33 +-
 backend/main.py                                    |    7 +
 backend/mirofish_worker.py                         |   26 +-
 backend/opportunity_worker.py                      |   25 +-
 backend/reply_worker.py                            |    1 +
 backend/trend_worker.py                            |    5 +-
 .env => linkedin/.env                              |    6 +-
 linkedin/.env.example                              |   81 +
 linkedin/.gitignore                                |    9 +
 linkedin/BUILD_LOG.md                              |   17 +
 linkedin/Dockerfile                                |   26 +
 linkedin/README.md                                 |   41 +
 linkedin/alembic/env.py                            |   68 +
 linkedin/alembic/script.py.mako                    |   24 +
 linkedin/alembic/versions/.gitkeep                 |    1 +
 linkedin/analytics/__init__.py                     |    0
 linkedin/analytics/advanced_analytics.py           |  105 +
 linkedin/analytics/aggregator.py                   |  205 ++
 linkedin/analytics/audience_quality.py             |  151 ++
 linkedin/analytics/cold_start.py                   |   71 +
 linkedin/analytics/comment_sentiment.py            |  142 ++
 linkedin/analytics/follows_tracker.py              |   91 +
 linkedin/analytics/pattern_detector.py             |   47 +
 linkedin/analytics/scorer.py                       |   18 +
 linkedin/api_routes/__init__.py                    |    0
 linkedin/api_routes/analytics.py                   |   45 +
 linkedin/api_routes/content.py                     |  234 ++
 linkedin/api_routes/growth.py                      |   24 +
 linkedin/api_routes/guardian.py                    |   19 +
 linkedin/api_routes/intelligence.py                |   27 +
 linkedin/api_routes/media.py                       |   15 +
 linkedin/api_routes/mirofish.py                    |  181 ++
 linkedin/api_routes/persona.py                     |   53 +
 linkedin/api_routes/personas.py                    |  326 +++
 linkedin/api_routes/system.py                      |   11 +
 linkedin/api_routes/webhooks.py                    |   86 +
 linkedin/api_routes/workers.py                     |   15 +
 linkedin/config.py                                 |   97 +
 linkedin/data/media_library/sample_founder.png     |    0
 linkedin/data/media_library/tags.json              |    1 +
 linkedin/data/personas/ahmad/persona.md            |  425 ++++
 linkedin/data/personas/ahmad/simulation_log.md     |    3 +
 linkedin/data/templates/dark_themes.html           |  463 ++++
 linkedin/data/templates/light_themes.html          |  464 ++++
 linkedin/data/theme_state.json                     |    1 +
 linkedin/db/__init__.py                            |    0
 linkedin/db/base.py                                |    3 +
 linkedin/db/models.py                              |  383 +++
 linkedin/db/session.py                             |   49 +
 linkedin/feedback_loop/__init__.py                 |    0
 linkedin/feedback_loop/archiver.py                 |   40 +
 linkedin/feedback_loop/buffer_manager.py           |  167 ++
 linkedin/feedback_loop/learning_engine.py          |  332 +++
 linkedin/feedback_loop/mirofish_refiner.py         |   44 +
 linkedin/feedback_loop/persona_patcher.py          |   80 +
 linkedin/growth/comment_opportunities.py           |   45 +
 linkedin/growth/event_ingestion.py                 |   80 +
 linkedin/growth/facebook_groups.py                 |   53 +
 linkedin/growth/follow_strategy.py                 |  174 ++
 linkedin/growth/growth_modules.py                  |  104 +
 linkedin/growth/instagram_collab.py                |   35 +
 linkedin/growth/linkedin_groups.py                 |   50 +
 linkedin/growth/linkedin_newsletter.py             |   58 +
 linkedin/growth/reddit_commenter.py                |   47 +
 linkedin/guardian/__init__.py                      |    0
 linkedin/guardian/checker.py                       |  275 +++
 linkedin/guardian/drift_detector.py                |   61 +
 linkedin/intelligence/__init__.py                  |    0
 linkedin/intelligence/content_dna_checker.py       |  199 ++
 linkedin/intelligence/cultural_calendar.py         |   82 +
 linkedin/intelligence/mirofish/__init__.py         |    0
 linkedin/intelligence/mirofish/agent_spawner.py    |  218 ++
 linkedin/intelligence/mirofish/graph_builder.py    |  270 ++
 .../intelligence/mirofish/narrative_forecaster.py  |  158 ++
 linkedin/intelligence/mirofish/pre_publish_gate.py |  309 +++
 linkedin/intelligence/mirofish/report_agent.py     |   66 +
 linkedin/intelligence/mirofish/seed_builder.py     |  231 ++
 .../intelligence/mirofish/simulation_runner.py     |  301 +++
 linkedin/intelligence/mirofish_client.py           |  556 +++++
 linkedin/intelligence/opportunity_detector.py      |  188 ++
 linkedin/intelligence/persona_generator.py         |  114 +
 linkedin/intelligence/persona_intel.py             |  148 ++
 linkedin/intelligence/scorer.py                    |  142 ++
 linkedin/intelligence/sensitive_moment_detector.py |   85 +
 linkedin/intelligence/trend_aggregator.py          |  184 ++
 linkedin/llm/__init__.py                           |    0
 linkedin/llm/bulk.py                               |  108 +
 linkedin/llm/content_rules.py                      |  126 +
 linkedin/llm/deduplication.py                      |   44 +
 linkedin/llm/generator.py                          |  251 ++
 linkedin/llm/parallel_gen.py                       |   32 +
 linkedin/llm/platform_rules.py                     |   61 +
 linkedin/llm/poll_generator.py                     |  116 +
 linkedin/llm/prompt_injection.py                   |   31 +
 linkedin/llm/repurposer.py                         |  156 ++
 linkedin/llm/stories_generator.py                  |  133 +
 linkedin/llm/transcriber.py                        |  187 ++
 linkedin/llm/variation_enforcer.py                 |  100 +
 linkedin/logger.py                                 |   77 +
 linkedin/main.py                                   |  128 +
 linkedin/mirofish/__init__.py                      |    0
 linkedin/mirofish/agent_spawner.py                 |  218 ++
 linkedin/mirofish/graph_builder.py                 |  270 ++
 linkedin/mirofish/narrative_forecaster.py          |  158 ++
 linkedin/mirofish/native/__init__.py               |   73 +
 linkedin/mirofish/native/graph_builder.py          |  506 ++++
 .../mirofish/native/oasis_profile_generator.py     | 1205 +++++++++
 linkedin/mirofish/native/ontology_generator.py     |  506 ++++
 linkedin/mirofish/native/report_agent.py           | 2572 ++++++++++++++++++++
 .../mirofish/native/simulation_config_generator.py |  992 ++++++++
 linkedin/mirofish/native/simulation_ipc.py         |  394 +++
 linkedin/mirofish/native/simulation_manager.py     |  529 ++++
 linkedin/mirofish/native/simulation_runner.py      | 1768 ++++++++++++++
 linkedin/mirofish/native/text_processor.py         |   71 +
 linkedin/mirofish/native/zep_entity_reader.py      |  437 ++++
 .../mirofish/native/zep_graph_memory_updater.py    |  554 +++++
 linkedin/mirofish/native/zep_tools.py              | 1736 +++++++++++++
 linkedin/mirofish/pre_publish_gate.py              |  322 +++
 linkedin/mirofish/report_agent.py                  |   66 +
 linkedin/mirofish/seed_builder.py                  |  231 ++
 linkedin/mirofish/simulation_runner.py             |  301 +++
 linkedin/oybit_linkedin_persona_60q.md             |  237 ++
 linkedin/persona_engine/__init__.py                |    0
 linkedin/persona_engine/builder.py                 |  257 ++
 linkedin/persona_engine/drift_detector.py          |   97 +
 linkedin/persona_engine/prompt_builder.py          |  232 ++
 linkedin/persona_engine/rotation_trigger.py        |   80 +
 linkedin/persona_engine/updater.py                 |  301 +++
 linkedin/publishers/__init__.py                    |   35 +
 linkedin/publishers/bluesky_facets.py              |   87 +
 linkedin/publishers/dispatcher.py                  |   78 +
 linkedin/publishers/facebook.py                    |   87 +
 linkedin/publishers/facebook_reels.py              |   71 +
 linkedin/publishers/instagram.py                   |  161 ++
 linkedin/publishers/instagram_brand.py             |  128 +
 linkedin/publishers/instagram_personal.py          |  224 ++
 linkedin/publishers/instagram_stories.py           |   70 +
 linkedin/publishers/linkedin.py                    |  225 ++
 linkedin/publishers/linkedin_polls.py              |   46 +
 linkedin/publishers/meta_error_handler.py          |   25 +
 linkedin/publishers/payload_builders.py            |   87 +
 linkedin/publishers/pinterest.py                   |   80 +
 linkedin/publishers/post_verify.py                 |   49 +
 linkedin/publishers/reddit_safety.py               |   60 +
 linkedin/publishers/youtube.py                     |   90 +
 linkedin/render_engine/__init__.py                 |    1 +
 linkedin/render_engine/carousel.py                 |  207 ++
 linkedin/requirements.txt                          |   54 +
 linkedin/scheduler_worker/__init__.py              |    0
 linkedin/scheduler_worker/autonomous_loop.py       |  209 ++
 linkedin/scheduler_worker/cron.py                  |   96 +
 linkedin/scheduler_worker/dispatcher.py            |  138 ++
 linkedin/scheduler_worker/queue.py                 |  129 +
 linkedin/scripts/bootstrap_pattern_db.py           |   58 +
 linkedin/scripts/check_tokens.py                   |  107 +
 linkedin/scripts/read_gap.py                       |   21 +
 linkedin/scripts/refresh_token.py                  |   84 +
 linkedin/scripts/retry_post.py                     |   74 +
 linkedin/scripts/setup_graphrag.py                 |   31 +
 linkedin/scripts/tests/run_all_agent_a.py          |  373 +++
 .../scripts/tests/test_analytics_aggregator.py     |   26 +
 linkedin/scripts/tests/test_api_endpoints.py       |   23 +
 .../scripts/tests/test_brand_voice_guardian.py     |   70 +
 linkedin/scripts/tests/test_carousel_renderer.py   |   29 +
 linkedin/scripts/tests/test_content_dna_checker.py |   88 +
 linkedin/scripts/tests/test_content_generator.py   |   27 +
 linkedin/scripts/tests/test_image_generator.py     |   19 +
 .../scripts/tests/test_image_prompt_builder.py     |   30 +
 .../scripts/tests/test_independent_verification.py |  143 ++
 linkedin/scripts/tests/test_learning_engine.py     |   98 +
 .../scripts/tests/test_mirofish_graph_builder.py   |   51 +
 .../tests/test_mirofish_pre_publish_gate.py        |   62 +
 .../scripts/tests/test_mirofish_seed_builder.py    |   55 +
 .../scripts/tests/test_opportunity_detector.py     |   48 +
 linkedin/scripts/tests/test_persona_builder.py     |   61 +
 linkedin/scripts/tests/test_persona_updater.py     |   82 +
 linkedin/scripts/tests/test_pipeline.py            |   31 +
 linkedin/scripts/tests/test_prompt_builder.py      |   57 +
 linkedin/scripts/tests/test_publishers.py          |   37 +
 linkedin/scripts/tests/test_real_api_calls.py      |  154 ++
 linkedin/scripts/tests/test_reply_manager.py       |   26 +
 linkedin/scripts/tests/test_repurposer.py          |   19 +
 .../scripts/tests/test_scheduler_dispatcher.py     |   18 +
 linkedin/scripts/tests/test_scheduler_queue.py     |   21 +
 linkedin/scripts/tests/test_scorer.py              |   49 +
 linkedin/scripts/tests/test_sim_engine.py          |   67 +
 linkedin/scripts/tests/test_token_refresher.py     |   20 +
 linkedin/scripts/tests/test_token_store.py         |   30 +
 linkedin/scripts/tests/test_video_renderer.py      |   19 +
 linkedin/scripts/verify_connections.py             |  172 ++
 linkedin/services/llm.py                           |  134 +
 linkedin/services/media_selector.py                |   46 +
 linkedin/services/persona_engine.py                |  100 +
 linkedin/services/persona_questions.py             |  494 ++++
 linkedin/token_store/__init__.py                   |    0
 linkedin/token_store/refresher.py                  |  243 ++
 linkedin/token_store/store.py                      |  138 ++
 linkedin/workers/analytics_worker.py               |   38 +
 linkedin/workers/archive_worker.py                 |   70 +
 linkedin/workers/bip_scheduler.py                  |  183 ++
 linkedin/workers/feedback_worker.py                |   97 +
 linkedin/workers/follow_worker.py                  |  125 +
 linkedin/workers/health_pinger.py                  |   44 +
 linkedin/workers/keepalive_worker.py               |   29 +
 linkedin/workers/mirofish_worker.py                |   72 +
 linkedin/workers/scheduler_worker.py               |   19 +
 linkedin/workers/token_refresher.py                |   43 +
 linkedin/workers/trend_worker.py                   |   43 +
 215 files changed, 31498 insertions(+), 118 deletions(-)

---

*(Logs that have already been posted are moved here)*

