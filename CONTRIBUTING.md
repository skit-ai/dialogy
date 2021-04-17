# Contributions

We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Any contributions you make will be under the MIT Software License
In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/Vernacular-ai/dialogy/issues)
We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/Vernacular-ai/dialogy/issues).

## Reporting Issues
It is helpful to understand issues if they contain:

1. What was tried?
2. What was expected?
3. What actually happened?
4. OS/environment, python version, machine specs.

This followed by a brief description would help us resolve issues faster. Observations or hints around reproducibility
of the issue or its importance.

## Picking Issues
To help you get started we highly recommend going through the [documentation](https://vernacular-ai.github.io/dialogy)
it should be fairly helpful in terms of explaining the project, if not that's an issue! please report.

- Spend some time with the source code and try to think of cases to test.
- Add a few [parameterized tests](https://docs.pytest.org/en/stable/example/parametrize.html).
- Document code, not to describe the code that's written. Explain the high-level thought behind using a certain logic.
    
```python
# ❌ This in a PR will not pass a code-review.

# loop on haystack
for needles in haystack:
    # loop on needles
    for needle in needles:
        # if needle is short
        if needle["length"] > 45:
            needle["short"] = False
    if needle.get("short"):
        # exit loop, because we found short needle
        break   
```

The comments are barely helping. The same information can be read through code.

- We can't understand the shape of a haystack. Is it always a list? it's a list of what?
- What is the shape of needle?
- Why do needle lengths matter?
- Was creating "short" as a new key really needed?

If these questions make you feel, the solution should have been this:

```python
short_needles = [needle 
    for needles in haystack 
    for needle in needles if needle["length"] < 45]
```

Then no, while there is less code, the previous program tried to exit the first instance. 
If that had to be explained better, it should have:

```python
# We are trying to find anomalies in a record. 
# Records are: List[List[Dict[str, Any]]]
# a normal length value is 100 so we are using 45 for now, 
# it can be replaced with a threshold later.
for needles in haystack:
    # A needle looks like:
    # {
    #   "length": 121
    #   "name": "needle_X",
    #   "hash_": "$sadias20as=0q2=wsf"
    # }
    for needle in needles:
        if needle["length"] > 45:
            # We want to rank all the short keys later
            # once these are collected and exported.
            # it makes for an easier search 
            # within a bundle of mixed size needles.
            # since that would mean repeating 
            # this code again on larger volume of data.
            needle["short"] = False
    if needle.get("short"):
        break   
```
This is the same code, but it speaks so much more. Things can easily be corrected,
as a reviewer one quickly understands the intention and suggestions/feedback are far 
more efficient.

## Work style
We use Makefiles to ensure necessary things are not left out but no active involvement should be required.
We respect high-quality well-documented and tested code. To that effect we:

- Lint using `isort`, `pycln` and `black`.
- Test using `pytest`. Expect differing test inputs via parameterized sources.
- Automatic documentation using `sphinx`, so please produce docstrings accordingly it will greatly help the documentation quality.
- Create a fork of the project so that the CI pipeline isn't clogged.
- Commits must always be [readable and helpful](https://www.conventionalcommits.org/en/v1.0.0/).
- Sign your commits.
    - [Why you should sign your commits](https://softwareengineering.stackexchange.com/questions/212192/what-are-the-advantages-and-disadvantages-of-cryptographically-signing-commits-a)
    - [Generating a GPG Key](https://docs.github.com/en/github/authenticating-to-github/generating-a-new-gpg-key)
    - [Adding a key to your account](https://docs.github.com/en/github/authenticating-to-github/adding-a-new-gpg-key-to-your-github-account)
    - [Telling your git client about the key](https://docs.github.com/en/github/authenticating-to-github/telling-git-about-your-signing-key)
    - [Signed commits](https://docs.github.com/en/github/authenticating-to-github/signing-commits)
    - Verify using `git log --show-signature`
- Creating a branch also comes with a convention label/#issue.n/title. As an example, if you are working on a bug your branch could be named bug/#45/plugin_crash_on_
- All PRs must accompany tests. Healthy coverage is necessary, healthy is 100%.

## License
By contributing, you agree that your contributions will be licensed under its MIT License.

## References
This document was adapted from the open-source contribution guidelines for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)
