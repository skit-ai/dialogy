# 0.5.5

- [x] feat: `dialogy create <project-name>`, we can drop the template name!
- [x] deprecate: DucklingParser set for deprecation.
- [x] add: DucklingPlugin. ([#28](https://github.com/Vernacular-ai/dialogy/pull/28))
- [x] add: DucklingPlugin supports association of [custom entities with dimensions](https://github.com/Vernacular-ai/dialogy/issues/21). ([8d7fbc47](https://github.com/Vernacular-ai/dialogy/commit/8d7fbc47f08da9384add9d850aeadbb08b3de0d9))
- [x] refactor: [DucklingParser had methods that parsed and restructured json](https://github.com/Vernacular-ai/dialogy/issues/26) to be compatible with a certain class structure. This made it hard to execute `BaseEntity.from_dict(duckling_json)`. 
  These methods are now part of individual `Entity` class. ([#28](https://github.com/Vernacular-ai/dialogy/pull/28))

# 0.5.0

- [x] fix: `entity.entity_type` and `entity.type` mirror each other till one of them is deprecated. ([#15](https://github.com/Vernacular-ai/dialogy/pull/15))
- [x] update: Slot filling doesn't require entities to contain slot related information. ([#16](https://github.com/Vernacular-ai/dialogy/pull/16))
- [x] add: `debug_logs` decorators available to all plugin methods.

# 0.4.5

- [x] docs: moved from pycco to sphinx. ([bed0a6](https://github.com/Vernacular-ai/dialogy/commit/bed0a664550a620cac24ce7b35c72bdb7a93a01f))
- [x] update: reference time made to be an optional parameter for `DucklingParser`. ([d7d8b39](https://github.com/Vernacular-ai/dialogy/commit/d7d8b39ddce3a0e3bf2618d8ee1d4ba2ce96d093))
- [x] add: Means to `normalize` 4 formats in which alternatives are usually presented. ([5b6c8c](https://github.com/Vernacular-ai/dialogy/commit/5b6c8ce7da6eb66bd17e4419594a51352fbac7ed))
- [x] update: Prevents accidental loss of data if template fails. ([e2be8c](https://github.com/Vernacular-ai/dialogy/commit/e2be8c222b155e5121044325b878f75b0c4b7c95))

# 0.2.4
- [x] add: Scaffolding generator using [copier](https://copier.readthedocs.io/en/stable/) ([17077a2](https://github.com/Vernacular-ai/dialogy/commit/17077a2276029e534f5aa3b2af566d68c130a331)).

# 0.1.0
- [x] add: Slot filler plugin via ([#7](https://github.com/Vernacular-ai/dialogy/pull/7)).
