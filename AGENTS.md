# AI Assistant Rules for FAST-OAD

This file defines the mandatory rules for any AI-assisted contribution
(tests, documentation, refactoring, ...) to FAST-OAD, regardless of the
AI tool or model used.

When asked to perform one of the tasks described below, an AI assistant
MUST follow these rules. If a rule conflicts with the user's request,
the assistant must say so instead of silently breaking it.

Project context:
- Python >= 3.10, OpenMDAO-based framework for aircraft design.
- Code style: PEP8, line length <= 100 characters, enforced by Ruff
  (fixed version, configuration in `pyproject.toml`).
- Docstrings: reStructuredText (PEP 287).
- Tests: pytest, unit tests in `src/*/tests`, integration tests in `tests/`.
- Documentation: Sphinx (.rst only), bibliography via sphinxcontrib-bibtex.
- License: GPL-3.0.
- Target reader: contributors and users may NOT be professional developers.
  Keep everything readable and understandable.

## 0. Transversal rules (apply to EVERY AI-assisted task)

1. **Scope**: do ONLY what is asked. No extra file, no extra feature, no
   drive-by fix, no reformatting of untouched code.
2. **Never modify source code** in a test or documentation task. If you find
   a bug, a wrong docstring, or a suspicious result: do NOT fix it, report
   it in a separate "Findings" list in your answer.
3. **No new dependency** without explicit user approval.
4. **Traceability of values**: every numeric value you introduce (tolerance,
   reference result, default input) must come from the provided code, an
   existing test, repository data, or cited literature. If you had to
   choose a value by yourself, flag it as `[TO VALIDATE]` so a human can
   check it.
5. **Simplicity**: FAST-OAD aims at being readable by non-professional
   developers. No metaprogramming, no cryptic one-liners, no clever
   tricks when a plain loop is clearer.
6. **Style**: PEP8, lines <= 100 chars, type hints encouraged, reST
   docstrings. Ruff and pre-commit will reject violations anyway.
7. **Output format**: give only the requested files/artifacts as the main
   answer, then an optional short "Findings / To validate by a human"
   list. No unrequested tutorial or advice.
8. **Attribution**: the contribution is AI-assisted. The contributor (a
   human) remains responsible: they must mention "Assisted-by-AI" in the
   PR description and review the generated content before submitting.
   AI output is never merged without human review and green CI.
9. **License**: generated content is a contribution to FAST-OAD under
   GPL-3.0, like any other contribution. Never include code or text
   copied from proprietary sources.

## 1. Unit test generation

Apply the transversal rules, plus:

1. **Framework**: pytest only, no new test dependency.
2. **Location and naming**:
   - Unit tests go next to the tested code, following the existing
     structure of the package (look at neighboring `tests/` folders).
   - File: `test_<module>.py`. Functions: `test_<behavior>` where
     `<behavior>` describes the physical or functional property verified.
3. **Test content**:
   - One test per behavior. Name must state what property is verified.
   - Each test has a short reST docstring stating the physical relation
     verified and its source (report, bibliography, analytical relation).
   - Nominal case: compare against an analytical result, repository
     reference data, or a value from literature, using `pytest.approx()`
     with an explicit tolerance. Justify the tolerance in a comment.
   - Boundary cases: zero, negative, out-of-domain inputs must be tested
     for the *expected* behavior (raised error, NaN, clipped value...),
     not merely for "does not crash".
   - If reference values exist in the repository (XML files, existing
     tests, docs), prefer them over invented values.
4. **OpenMDAO specifics**:
   - Test components through `setup()` / `compute()` (or
     `setup_partials()` / `compute_partials()`) with explicit inputs.
   - When the component declares partials, add a test using OpenMDAO's
     `assert_check_partials` against finite differences, unless the
     user says otherwise.
   - No dependency on the plugin registry or external files unless the
     tested code itself requires it; if needed, use the repository's
     existing test fixtures and resources.
5. **Isolation**: tests must pass with only the package installed
   (`poetry install`, `pytest`). No network access, no absolute paths.
6. **Completeness**: the test file must pass as-is. It is OK (and
   expected) to start from the docstrings and `add_input`/`add_output`
   declarations rather than guessing behavior that is not documented;
   in that case, list the unclear points in "Findings".

## 2. Documentation generation (.rst)

Apply the transversal rules, plus:

1. **Format**: reStructuredText only, using the Sphinx directives already
   used in `docs/` (`autoclass`, `automodule`, `math`, `figure`,
   `bibliography`...). No Markdown.
2. **Consistency**: reuse the structure of the existing documentation
   pages of the same package/topic (browse `docs/source/` first) so the
   new page blends in.
3. **Scope**: document only the public API of the provided module. No
   new tutorial, no new section, no page you were not asked for.
4. **Physics content** — for each model, the documentation must give:
   - the governing equation(s) with a `:math:` directive,
   - the meaning of each variable, WITH its unit (use the units declared
     in `add_input`/`add_output`),
   - the assumptions and the domain of validity,
   - the source of the model, cited through the existing
     sphinxcontrib-bibtex keys. Never invent a bibliography entry;
     if no suitable key exists, put `[TO VALIDATE: reference]`.
5. **Readability**: short sentences, defined acronyms, no implicit
   jargon. The reader may be an engineering student using FAST-OAD for
   the first time.
6. **Docstrings**: in a documentation task, do not rewrite existing
   docstrings; the .rst page and the docstrings must stay consistent.
   If a docstring is missing, wrong, or inconsistent with the code,
   report it in "Findings" instead of editing the source.
7. **Build check**: the generated .rst must build with
   `poetry run sphinx-build -b html docs docs/_build/html` without new
   warnings. Report anything you could not verify.

## 3. Workflow & test execution (good practices for working in FAST-OAD)

Apply the transversal rules, plus:

1. **Unit tests**: after generating or modifying unit tests, run them
   (they are fast) and iterate until they pass. Report the result.
2. **Integration tests** (`tests/` at repository root): they are long
   (up to 10 minutes). Do NOT run them systematically. Run them only
   if legacy code (existing source code, configuration files, or test
   files other than the ones you created) has been modified — in that
   case, run them at the END of your work, once all other tasks are
   complete, and report the result.
3. If your task does not require touching legacy code, skip the
   integration tests and say so explicitly: "Integration tests not run
   (no legacy code modified)."

## 3. Mandatory final self-check

Before returning your answer, verify and confirm:
- [ ] I did not modify any source file.
- [ ] I added no dependency and created only the requested files.
- [ ] Every numeric value is traceable or tagged `[TO VALIDATE]`.
- [ ] Style rules (PEP8, <= 100 chars) are respected.
- [ ] I listed findings and uncertainties for human review.