# COMET Governance Charter

This document describes the governance structure, roles, responsibilities, and decision-making processes for the COMET (Carbon Ontology for Materials and Emissions Tracking) project.

## Overview

COMET is an open-source semantic ontology for carbon accounting and emissions tracking across materials supply chains. Governance ensures that decisions are made transparently, inclusively, and in alignment with project values.

**Project values:**
- Transparency in all decisions
- Inclusive participation from diverse stakeholders
- Scientific rigor and evidence-based design
- Backward compatibility for stable components
- Community stewardship

## Decision-Making Process

COMET uses a **lazy consensus** model augmented with formal voting for major decisions:

### Lazy Consensus

For routine decisions (bug fixes, documentation improvements, minor enhancements):

1. **Proposal**: Maintainer or contributor proposes change (GitHub issue/PR)
2. **Review period**: 3-5 business days for comments
3. **Consensus**: If no substantive objections, decision proceeds
4. **Objections**: If raised, escalate to formal vote

**Examples**: Typo fixes, non-breaking documentation updates, translation improvements

### Formal Voting

For significant decisions requiring explicit agreement:

**Trigger conditions:**
- New major release (e.g., 0.2.0 to 1.0.0)
- Adoption of major architectural change
- Promotion of extension from Draft to Stable
- Change to governance structure itself
- Deprecation of core component
- Spending/resource allocation

**Process**:
1. **Proposal**: Owner/Maintainer opens discussion with detailed rationale
2. **Discussion period**: 1-2 weeks for community input
3. **Vote**: +1 (approve), 0 (abstain), -1 (object)
4. **Threshold**: 2/3 majority of Maintainers required
5. **Tie-breaker**: Owner has final decision

**Who votes:**
- Owner (1 vote, tie-breaker)
- Maintainers (1 vote each)
- Domain Experts (1 vote each on relevant domains)

## Project Roles

### Owner

**Count**: 1 (currently Nick Gogerty)

**Responsibilities:**
- Overall project vision and strategy
- Final decision authority on tie-breaks
- Resource allocation and priorities
- Major release approval
- Conflict resolution

**Permissions:**
- Merge code directly to main (with review from Maintainer)
- Promote extensions between lifecycle stages
- Change governance structure (with vote)
- Appoint/remove Maintainers

**Expectations:**
- Respond to escalated issues within 1 week
- Maintain project roadmap
- Annual review of governance effectiveness

### Maintainer

**Count**: 2-5 (appointed by Owner)

**Responsibilities:**
- Code review and quality assurance
- PR triage and merging (except core changes)
- Release management and versioning
- Community engagement and issue response
- Mentorship of Contributors

**Permissions:**
- Merge approved PRs
- Create releases (with Owner approval for major versions)
- Manage GitHub labels, milestones, projects
- Edit documentation and examples
- Approve extension promotions

**Expectations:**
- Respond to issues within 3 business days
- Review PRs within 5 business days
- Maintain code quality standards
- Update CHANGELOG for releases
- Attend monthly sync (async updates acceptable)

### Domain Expert

**Count**: 3-8 (appointed by Owner/Maintainers)

**Scope**: Specific domains (e.g., steel, textiles, automotive)

**Responsibilities:**
- Review extension PRs in their domain
- Validate scientific/technical accuracy
- Connect community experts
- Advise on standards alignment (ISO, PACT, CBAM, etc.)

**Permissions:**
- Vote on domain-specific extension promotions
- Request reviews on related PRs

**Expectations:**
- Respond to domain PRs within 2 weeks
- Provide quarterly domain health update
- Facilitate connections with industry bodies

### Contributor

**Count**: Unlimited

**Responsibilities:**
- Follow CONTRIBUTING.md guidelines
- Engage respectfully with community
- Test and document changes

**Permissions:**
- Submit PRs and issues
- Participate in discussions
- Propose extensions

## Release Cadence

### Version Numbering

COMET follows Semantic Versioning (semver):

```
MAJOR.MINOR.PATCH
  0.2.0
```

- **MAJOR**: Breaking changes (rare, <yearly)
- **MINOR**: New features, backward compatible (quarterly)
- **PATCH**: Bug fixes, hot fixes (as needed)

### Release Schedule

**Regular releases**: Quarterly (March, June, September, December)

**Content windows**:
- Feature freeze: 2 weeks before release
- RC period: 1 week, final testing
- Release: Tagged on main, announced to community

**Hot fixes**: Released within 1 week if critical bug discovered

**Security releases**: ASAP if vulnerability found

**Deprecation policy**: 2 release cycles (6 months minimum) notice before removal

## Semantic Versioning Policy

### Breaking Changes

Breaking changes ONLY allowed in MAJOR versions:
- Removing classes or properties from stable ontology
- Changing class hierarchy or semantic meaning
- Removing language translations
- SHACL constraint tightening (may break existing data)

**Mitigation**:
- Provide clear migration guide
- Maintain deprecated version for 12 months
- Post-release hotline for migration help

### Backward Compatibility

**Guarantee for Stable extensions**:
- All classes/properties remain available
- Semantic meaning doesn't change
- New properties can be added
- Constraints can be loosened
- Documentation can be improved

**Guarantee for Draft extensions**:
- No guarantees, may change significantly

### Deprecation Path

```
Current → Deprecated → Removed
```

- **Current**: Default version, used in production
- **Deprecated**: Marked with `deprecated` tag, works but warns
- **Removed**: No longer distributed, available in archive

**Timeline**: 6 months between stages minimum

## Extension Lifecycle

Extensions progress through stages with specific requirements:

### Stage 1: RFC (Request for Comments)

**Definition**: Community feedback phase on proposed extension

**Entry criteria**:
- Domain identified
- Basic concept list drafted
- Author commits to further development

**Exit criteria** (→ Draft):
- 2+ weeks discussion completed
- Community interest demonstrated
- Technical feasibility confirmed

**Obligations**: None

### Stage 2: Draft

**Definition**: Working implementation, ready for beta use

**Entry criteria**:
- Complete ontology with all classes/properties
- SHACL shapes with validation rules
- Example instance data (3+ examples)
- English + 2+ language labels
- Documentation and use cases

**Review process**:
- Domain Expert or Maintainer assigned
- 2+ week review period
- All feedback addressed
- SHACL validation passes
- Examples demonstrate functionality

**Exit criteria** (→ Stable):
- 2+ weeks in Draft with no critical issues
- Production use documented
- Author commits to maintenance

**Obligations**: Respond to issues, track COMET core changes

### Stage 3: Stable

**Definition**: Production-ready, backward compatible

**Entry criteria**:
- Draft proven in production
- Maintenance plan documented
- Community consensus (vote if contested)

**Obligations**:
- Strict backward compatibility
- Respond to issues within 2 weeks
- Update for COMET core releases
- Maintain translation consistency
- Annual health check-in

**Promotion cadence**: Quarterly review, promote annually

### Stage 4: Deprecated

**Definition**: Superseded or no longer maintained

**Triggers**:
- Better replacement available
- Maintainer unable to continue
- Community consensus
- Security/semantic issues

**Timeline**: 6-month notice period

**Obligations**:
- Clear migration path documented
- Backward compatibility maintained
- Community support during transition

### Stage 5: Retired

**Definition**: No longer supported

**Final location**: `retired/` directory

**Access**:
- Available in git history
- Archived on Zenodo with DOI
- Documented in historical records

## Review Criteria for Code/Extensions

All contributions evaluated on:

**Technical**:
- OWL 2 syntax validity
- SHACL constraint correctness
- SPARQL query functionality
- RDF serialization soundness

**Quality**:
- Documentation completeness
- Example data provided
- Comments and docstrings
- Code consistency

**Design**:
- Alignment with COMET architecture
- Reuse of existing patterns
- Extensibility considered
- Standards alignment

**Testing**:
- SHACL validation shapes pass
- Example queries execute correctly
- No breaking changes (for stable)

**Community**:
- Issue discussion completed
- Feedback addressed
- Use case relevance demonstrated

## Conflict Resolution

**Escalation path**:

1. **Discussion**: Disagreeing parties discuss in GitHub issue (1 week)
2. **Mediation**: Maintainer facilitates compromise (1 week)
3. **Review team**: 2-3 Maintainers/Domain Experts review (1 week)
4. **Owner decision**: Owner makes final call if needed

**Guiding principle**: Focus on COMET's mission, not personal preferences

**Code of Conduct**: Always applies; violations escalated immediately to conduct@comet.carbon

## Amendment Process

**Governance changes** require:
1. GitHub issue describing proposed change and rationale
2. 2-week discussion period
3. Formal vote (2/3 Maintainer majority + Owner approval)
4. Documentation update

**Trigger frequency**: Annual review minimum, ad-hoc when needed

## Communication

**Primary channels**:
- **Issues**: Feature requests, bug reports
- **Discussions**: Questions, ideas, announcements
- **Releases**: Version updates and notes
- **Website**: Roadmap, status, news
- **Email**: conduct@comet.carbon for Code of Conduct issues

**Transparency**:
- Monthly status updates (async, GitHub Discussions)
- Quarterly release notes with rationale
- Annual governance review published
- Meeting notes archived publicly

## Appendix: Current Governance Configuration

**Owner**: Nick Gogerty

**Maintainers**: (To be appointed)

**Domain Experts**: (To be appointed)

**Release cycle**: Quarterly (Q1, Q2, Q3, Q4)

**Next governance review**: Q4 2026
