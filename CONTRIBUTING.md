# Contributing to COMET

Thank you for your interest in contributing to COMET (Carbon Ontology for Materials and Emissions Tracking). This document provides guidelines for reporting issues, contributing code, submitting extensions, and improving documentation.

## Getting Started

Before you begin, please:
1. Read our [Code of Conduct](CODE_OF_CONDUCT.md)
2. Review our [Governance charter](GOVERNANCE.md)
3. Set up your development environment (see [Getting Started guide](docs/getting-started.md))

## Reporting Issues

### Bug Reports

When reporting bugs, please include:
- **Title**: Clear, concise description of the issue
- **Environment**: COMET version, Python/tool version, OS
- **Steps to reproduce**: Minimal reproducible example
- **Expected behavior**: What should happen
- **Actual behavior**: What happens instead
- **Logs/error messages**: Full stack traces if applicable

Use the GitHub Issues template and label with `bug`.

### Feature Requests

For feature requests:
1. Check [existing issues](../../issues) to avoid duplicates
2. Provide use case and context
3. Explain why this feature is important
4. Use the `enhancement` label

### Translation Issues

For translation issues or to add support for new languages:
1. Check the [labels directory](labels/) for existing translations
2. See [Adding Translations](#adding-translations) section
3. File an issue with label `translation` and language code (e.g., `translation:de`)

## Adding Translations

COMET supports internationalization through RDFS labels in multiple languages. To add or improve translations:

1. **Locate translation files**: See [labels/](labels/) directory for language-specific RDF files
2. **Get translation done**: Use professional translation services or community volunteers
3. **Format**: Translations must follow RDFS label conventions with language tags (e.g., `@en`, `@es`)
4. **Submit PR**: Create a pull request with:
   - Branch: `translation/language-code`
   - Message: `Add/improve [Language Name] translations`
   - Include which domains/layers the translation covers

## Contributing Code

### Branch Naming

Use descriptive branch names:
- Features: `feature/short-description`
- Bug fixes: `bugfix/issue-number-short-desc`
- Documentation: `docs/description`
- Translations: `translation/language-code`

### Commit Messages

Follow conventional commits:

```
type(scope): subject

body (if needed)

footer (if needed)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(ontology): add ResponsibleSteel extension module

- Adds 31 new classes for steel supply chain tracking
- Integrates with core emissions layer
- Includes SHACL validation shapes

Closes #42
```

### Pull Request Process

1. **Fork and branch**: Create a feature branch from `main`
2. **Code**: Write clear, documented code
3. **Test**: Ensure all SHACL constraints pass, SPARQL queries work
4. **Document**: Update relevant docs in `docs/`
5. **Commit**: Use conventional commits
6. **Push and create PR**:
   - Link related issues
   - Describe changes and rationale
   - Include examples if applicable
   - Tag reviewers using @mentions

### Review Criteria

Your code will be reviewed on:
- **Correctness**: Does it solve the stated problem?
- **OWL Validity**: Ontology syntax and semantic constraints
- **SHACL Validation**: All shapes validate properly
- **Backwards Compatibility**: No breaking changes to stable extensions
- **Documentation**: Sufficient inline comments and external docs
- **Testing**: SPARQL queries and example data included
- **Accessibility**: Inclusive language, accessible documentation

## Creating Extensions

To create a COMET extension, follow our [Extension Creation Cookbook](docs/creating-extensions.md).

### Extension Submission Process

COMET extensions follow a structured lifecycle:

#### Stage 1: RFC (Request for Comments)
- **Goal**: Community feedback on scope and design
- **Process**:
  1. Open GitHub Discussion or Issue with label `extension-rfc`
  2. Describe: domain, core concepts, relationship to core layers
  3. Provide: glossary, example use cases, SHACL shape sketches
  4. Timeline: 2 weeks for community input
  5. Owner/Maintainers provide guidance

#### Stage 2: Draft
- **Goal**: Complete working extension
- **Requirements**:
  - Ontology file with all classes and properties
  - SHACL shape file with validation rules
  - Example RDF instance data (minimum 3 examples)
  - RDFS labels in English + 2+ languages
  - Documentation in `docs/extensions/`
  - Alignment to core COMET layers
- **Process**:
  1. Submit PR with label `extension-draft`
  2. Assign to Domain Expert reviewer
  3. Address feedback in PR comments
  4. Pass SHACL validation tests
  5. Timeline: 4-6 weeks review
- **Acceptance Criteria**:
  - Passes all technical reviews
  - Has community interest (issue comments, discussion)
  - Ready for beta use

#### Stage 3: Stable
- **Requirements**:
  - 2+ weeks in Draft with no issues reported
  - Documented use cases in production
  - Release notes prepared
- **Process**:
  1. Owner/Maintainer approves promotion
  2. Documented in CHANGELOG.md
  3. Version bump (see [Governance](GOVERNANCE.md))
- **Obligations**:
  - Backwards compatibility maintained
  - Regular maintenance expected
  - Community support commitment

#### Stage 4: Deprecated (optional)
- **Reason**: Superseded by newer extension, low usage, etc.
- **Timeline**: 6-month notice period
- **Documentation**: Clear migration path provided

#### Stage 5: Retired
- **Process**: Moved to `retired/` directory, archived on Zenodo
- **Access**: Still available in git history and permanent archives

## Improving Documentation

Documentation improvements are highly valuable:

1. **Fix typos/clarity**: Submit PR directly
2. **Add examples**: Create new docs or expand existing ones
3. **Improve tutorials**: Update `docs/tutorials/`
4. **API documentation**: Generated from ontology, file issues for missing docs

For major doc additions:
- Branch: `docs/description`
- Follow Markdown conventions (see existing docs)
- Include code examples that can be tested
- Link to related documentation

## Extension Maintenance

If you maintain an extension:

- **Respond to issues** within 2 weeks
- **Track compatibility** with core COMET changes
- **Update versions** when COMET core updates
- **Communicate changes** via GitHub Releases
- **Archive gracefully** if stepping down (find new maintainer or mark deprecated)

## Recognition

Contributors are recognized through:
- GitHub contributors page
- CHANGELOG.md entries
- `CONTRIBUTORS.md` file (coming soon)
- Acknowledgments in documentation
- Annual contributor spotlight

## Questions?

- **Technical questions**: Use GitHub Discussions with label `question`
- **Governance questions**: See [GOVERNANCE.md](GOVERNANCE.md)
- **Code of Conduct violations**: See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **General inquiries**: contact@comet.carbon

## Additional Resources

- [Getting Started Guide](docs/getting-started.md)
- [Extension Cookbook](docs/creating-extensions.md)
- [FAQ](docs/faq.md)
- [Architecture Decision Records](docs/adr/)
- [Governance Charter](GOVERNANCE.md)

Thank you for making COMET better!
