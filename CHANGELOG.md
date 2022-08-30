Changelog

## 0.9.20

- [x]: feat: xlmr.py, adding support for feature engineering with prompts.

## 0.9.19

- [x]: feat: AddressParser plugin using google maps and map my india.

## 0.9.18

- [x] fix: Stanza download instructions removed from `ListSearchPlugin`.


## 0.9.17

- [x] feat: A [DSL](https://github.com/skit-ai/dialogy/pull/155) for error-recovery and transitions.

## 0.9.16

- [x] update: multiple slots can be filled if multiple entities are supposed to fill each slot.

## 0.9.15

- [x] fix: Filling multiple slots with multiple entities was disabled.
- [x] feat: We fill slots using `expected_slots` if present.

## 0.9.14

- [x] fix: slots returned in sorted order of scores.

## 0.9.13

- [x] fix: duckling datetime parsing for year > 9999. [We won't return entities](https://github.com/skit-ai/dialogy/issues/148) in these cases.
- [x] feat: A rule engine to define intent transitions.

## 0.9.11

- [x] fix: https://github.com/skit-ai/dialogy/issues/148

## 0.9.10

- [x] add: Support python for 3.10.

## 0.9.9

- [x] fix: `XLMRMultiClass::inference` type signature for `state`.

## 0.9.8

- [x] fix: **Exceptions that leak over turns**. [#136](https://github.com/skit-ai/dialogy/issues/136)
- [x] add: Support for grouping by regex match. [#135](https://github.com/skit-ai/dialogy/issues/135)
- [x] fix: Remove zen of python from all commands.

## 0.9.7

- [x] refactor: Faster test runs.
- [x] refactor: Deserializer avoids if-else hell.
- [x] update: Plugin debug flags are _anded_ with Workflow's debug flags.
- [x] feat: XLMR plugin now supports state as a feature.

## 0.9.6

- [x] add: `original_intent` to store the initial classifier output.
- [x] add: plugin to track `original_intent`.

## 0.9.5

- [x] fix: DucklingPlugin's unreliable use of latent entities.
- [x] feat: Temperature scaling for XLMR classifier.

## 0.9.4

- [x] fix: Slot structure need not be redefined in templates.
- [x] update: Type-casted Time entities acquire score from the original (Numerical, Duration) entities.

## 0.9.3

- [x] update: Numerical entities can be casted as time.

## 0.9.2
- [x] fix: Plugins don't overwrite the Output object unless they are _meant_ to.

## 0.9.1

- [x] feat: `DurationEntity` are cast as `TimeEntity` by default.
  - [x] `DucklingPlugin` uses temporal intents to understand cast direction i.e. add duration to reference time or subtract.
- [x]: docs: Heavy addition of examples for types, plugins and base types.
- [x]: fix: Entity structures are uniform in terms of `value` and `values` attributes.
- [x]: feat: Guards prevent plugins from running.

## 0.9.0
- [x] fix: `entity.entity_type` and `entity.type` hold separate meaning.
- [x] update: Plugins no longer need `access` or `mutate` functions.
- [x] update: `Workflow` has `Input` and `Output` objects.

## 0.8.11
- [x] feat: plugin to merge previously tracked datetime entities with currently extracted datetime entities. 
- [x] feat: New entity type credit-card / debit-card supported via `PlasticCurrencyEntity`.

## 0.8.10
- [x] feat: Sklearn based MLP classifier added as a plugin with gridsearch.

## 0.8.9
- [x] fix: XLM classifier wasn't using xlmrobert, but bert instead.

## 0.8.8

- [x] feat: ListSearchPlugin can find keyword entities via fuzzy search.

## 0.8.7

- [x] feat: LBPlugin a Duckling extension that has dedicated selection strategies for date, time and datetime.

## 0.8.6

- [x] feat: conditional latent entities.

## 0.8.4

- [x] feat: WER calibration plugin.

## 0.8.3

- [x] fix: ListEntityPlugin performed aggregation over entities twice leading to lesser than actual scores.

## 0.8.2

- [x] **fix: Workflow is thread safe.**
- [x] fix: Merge asr plugin on non-json inputs crashes workflow runs.
- [x] feat: Canonicalization plugin.
- [x] update: DucklingPlugin, ListEntityPlugin have transform methods.
- [x] docs: Explain plugins in terms of workflow lifecycle.

## 0.8.1

- [x] update: dialogy cli has updated project creation and migration.
- [x] add: dialogy cli can also train and test workflows.

## 0.8.0

- [x] update: WER calibration refactored to contain core logic.
- [x] update: **Deprecated** post-processors and pre-processors.
- [x] feat: trainable plugins.
- [x] update: **Drop support for python 3.7**

## 0.7.4

- [x] update: WER calibration as a plugin.

## 0.7.3

- [x] add: WER calibration. This plugin can eliminate ASR alternatives if acoustic model and language model scores are available.

## 0.7.2

- [x] add: Template migration `dialogy update <project>`.
- [x] add: `DucklingPlugin` tracks network issues and optionally returns entities collected till failure.

## 0.7.1

- [x] [fix](https://github.com/Vernacular-ai/dialogy/issues/60): Entity scoring within `EntityExtractor` and `DucklingPlugin`.
- [x] [fix](https://github.com/Vernacular-ai/dialogy/issues/58): CurrencyEntity added to operate on `amount-of-money` dimension.
- [x] add: TimeIntervalEntities sometimes may contain a hybrid structure that resembles some values as `TimeEntities`.

## 0.7.0

- [x] add: `KeywordEntity` entity-type class.
- [x] refactor: `ListEntityPlugin` doesn't need an entity map. Uses `KeywordEntity` instead.
- [x] refactor: **breaking** All plugins are now available under: `dialogy.plugins`.
- [x] refactor: `Workflow` can be serialized.

## 0.6.4

- [x] docs: Better error message for -- `DucklingPlugin` comparison requires reference time to be unix timestamp.
- [x] fix: `DucklingPlugin` doesn't return duplicate entities when a list of strings is input.
- [x] add: `DucklingPlugin` produces a score that can be compared against a threshold.
- [x] fix: `DucklingPlugin` doesn't remove other entities if `datetime_filter` is used.

## 0.6.3

- [x] fix: #46 `ListEntityPlugin` overwrites if there are mutliple `entity_value` patterns for the same `entity_type`.
- [x] fix: #47 `DucklingPlugin` compares int vs int for `Duckling.FUTURE` and `Duckling.PAST` feature comparison.

## 0.6.2

- [x] fix: `ListEntityPlugin`
  - Now supports a map for entity-type, entity-values for keyword based entities.
  - Fixed bug that returns `None` when custom entity classes are required.

## 0.6.1

- [x] feat: future or past datetime only support from `DucklingPlugin`.

## 0.6.0

- [x] feat: spacy, pattern entity parsing from list support.
- [x] refactor: Plugin class to prevent repeated code in subclasses.
- [x] refactor: @debug -> @dbg to prevent name collisions.
- [x] feat: support for building from local git templates optionally, `--vcs` takes `"TAG"` or `"HEAD"`. if the user provides `--vcs` as
`"TAG"`, then `dialogy` takes the template's latest released tag commit. if the user provides `--vcs` as `"HEAD"`, then `dialogy` takes the template's present git branch's recent commit.
- [x] update: **[BREAKING]** `DucklingPlugin` expects the locale from the access method as well.

## 0.5.5

- [x] feat: `dialogy create <project-name>`, we can drop the template name!
- [x] deprecate: DucklingParser set for deprecation.
- [x] add: DucklingPlugin. ([#28](https://github.com/Vernacular-ai/dialogy/pull/28))
- [x] add: DucklingPlugin supports association of [custom entities with dimensions](https://github.com/Vernacular-ai/dialogy/issues/21). ([8d7fbc47](https://github.com/Vernacular-ai/dialogy/commit/8d7fbc47f08da9384add9d850aeadbb08b3de0d9))
- [x] refactor: [DucklingParser had methods that parsed and restructured json](https://github.com/Vernacular-ai/dialogy/issues/26) to be compatible with a certain class structure. This made it hard to execute `BaseEntity.from_dict(duckling_json)`.
  These methods are now part of individual `Entity` class. ([#28](https://github.com/Vernacular-ai/dialogy/pull/28))

## 0.5.0

- [x] fix: `entity.entity_type` and `entity.type` mirror each other till one of them is deprecated. ([#15](https://github.com/Vernacular-ai/dialogy/pull/15))
- [x] update: Slot filling doesn't require entities to contain slot related information. ([#16](https://github.com/Vernacular-ai/dialogy/pull/16))
- [x] add: `debug_logs` decorators available to all plugin methods.

## 0.4.5

- [x] docs: moved from pycco to sphinx. ([bed0a6](https://github.com/Vernacular-ai/dialogy/commit/bed0a664550a620cac24ce7b35c72bdb7a93a01f))
- [x] update: reference time made to be an optional parameter for `DucklingParser`. ([d7d8b39](https://github.com/Vernacular-ai/dialogy/commit/d7d8b39ddce3a0e3bf2618d8ee1d4ba2ce96d093))
- [x] add: Means to `normalize` 4 formats in which alternatives are usually presented. ([5b6c8c](https://github.com/Vernacular-ai/dialogy/commit/5b6c8ce7da6eb66bd17e4419594a51352fbac7ed))
- [x] update: Prevents accidental loss of data if template fails. ([e2be8c](https://github.com/Vernacular-ai/dialogy/commit/e2be8c222b155e5121044325b878f75b0c4b7c95))

## 0.2.4

- [x] add: Scaffolding generator using [copier](https://copier.readthedocs.io/en/stable/) ([17077a2](https://github.com/Vernacular-ai/dialogy/commit/17077a2276029e534f5aa3b2af566d68c130a331)).

## 0.1.0

- [x] add: Slot filler plugin via ([#7](https://github.com/Vernacular-ai/dialogy/pull/7)).
