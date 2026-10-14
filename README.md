---
title: "Accessibility and Inclusive Design Knowledge Base — README"
version: "1.1.0"
author: "Double FW; material by Gareth Ford Williams"
date: "2026-10-14"
license: "MIT"
language: "en-GB"
repository: "https://github.com/Double-FW/Accessibility-and-Inclusive-Design-Knowledge-Base"
artifact_type: "repository_readme"
use_case:
  - "inclusive_design_knowledge_retrieval"
  - "product_and_service_design"
  - "design_process_governance"
  - "accessibility_research_and_validation"
  - "ai_assisted_design_workflows"
schema_version: "1.0"
conceptual_entities:
  person: "A person with intentions, access needs, preferences, strategies and lived experience."
  design_context: "A task, journey, product, service, device, language, environment and set of constraints."
  barrier: "A design or process condition that obstructs access, understanding, choice or participation."
  interaction: "A sequence of inputs, choices, system states, feedback, recovery and handoffs."
  outcome: "Task achievement together with understanding, effort, agency, privacy, dignity and experience."
  evidence: "An attributed observation, report, test or argument with scope and limitations."
  design_decision: "An accountable choice linked to user outcomes, evidence, alternatives and validation."
  organisational_promise: "A commitment that the delivered product or service should make real."
---

# Accessibility and Inclusive Design Knowledge Base

This repository is a design-focused collection of articles, principles and practical guidance about accessibility, inclusive interaction, user experience, evidence and design governance. It supports people and AI systems involved in generating, evaluating, testing or managing designs and design processes.

## Scope

The knowledge base examines how product and service design can enable or obstruct people across different tasks, contexts, devices, channels and levels of resource. Its core themes include:

- designing around barriers and human intentions rather than assuming diagnoses;
- treating accessibility and user experience as connected disciplines with distinct evidence;
- designing equivalent outcomes, informed choices, proportionate effort, orientation and recovery;
- applying mobile-first and interaction requirements while retaining source limitations;
- measuring technical, behavioural, experiential and equity outcomes without reducing them to one score;
- considering language, connectivity, legacy technology and socioeconomic context;
- aligning organisational promises, product capabilities, journeys and handoffs;
- governing AI-assisted design decisions with privacy, evidence and accountable human review.

Employment, hiring and HR process guidance is outside the repository's current scope. The former employment article has been removed. Do not use this repository as an employment or candidate-assessment knowledge base.

## Articles

| File | Main contribution |
| --- | --- |
| `Accessibility Is Not Always Equal.md` | Socioeconomic, language, connectivity, legacy-technology and participation contexts that design and research can miss. |
| `Mobile First Accessibility Principles, Design Requirements and Testing Approaches.md` | Mobile-first principles, interface and content requirements, interaction modes, focus, structure and outcome-based validation. |
| `Stop_Counting_Start_Designing_Rethinking_Accessibility_Metrics.md` | Balanced measurement across technical, behavioural, experiential and equity evidence, with privacy and data limitations. |
| `Synchronistic_UX Design_Principles.md` | Design principles for aligning organisational promises, human intention, interaction, equivalent experience and recovery. |
| `The_Synchronicity_of_Good_Experience.md` | A conceptual account of how brand, product, service and lived experience meet across organisational boundaries. |
| `UX_and_Accessibility_as_Connected_but_Distinct_Disciplines.md` | Barrier-led UX and accessibility practice, research, lifecycle governance and AI-assisted UX safeguards. |
| `When_WCAG_Is_Not_Enough_Dark_Patterns_and_Interaction-Based_Exclusion.md` | Informed choice, interaction integrity, effort symmetry, recovery and evaluation of exclusion beyond technical conformance. |

## Start here

1. Read [`AGENTS.md`](AGENTS.md) before using the repository in an AI workflow or as structured decision support.
2. Identify the design task, the intended user outcome, affected contexts and the decision being made.
3. Retrieve the relevant articles through the catalogue in `AGENTS.md`; preserve the section, attribution and caveats with each retrieved passage.
4. Separate source guidance from adopted organisational policy, verified standards requirements, observations and inference.
5. Record evidence gaps, test the design with appropriate methods and people, and escalate material uncertainty to an accountable human.

## Using the material in design workflows

The articles can inform discovery, service and interaction design, content and component requirements, research plans, design reviews, accessibility testing, design-system governance, experiment design, remediation and live-service optimisation. AI systems can use the catalogue and machine-readable contracts in `AGENTS.md` to retrieve sources, structure outputs and route decisions.

The material is advisory. It does not establish that a design conforms to a law or standard, that an organisation has adopted a recommendation, or that an outcome has been validated. For compliance decisions, obtain current authoritative requirements and evidence for the applicable jurisdiction and product. Do not infer disability or assistive-technology use from behaviour or device signals.

## Agent guidance and operational controls

`AGENTS.md` defines:

- YAML front matter and machine-readable source, rule, trust and review metadata;
- a design-focused quick-start checklist and retrieval catalogue;
- structured rule results and a minimal decision flowgraph;
- short prompt/response examples and reusable design, decision and escalation templates;
- escalation event fields, redaction, access, retention and audit-delivery requirements;
- version, changelog and review checks that automation should evaluate before trusting rules.

The audit hooks describe requirements for a consuming system to implement. This repository does not itself run an agent, audit sink, retention service, approval process, evaluator or release control. Until an authorised maintainer approves the exact guide version and a deployment configures those controls, use the material for advisory analysis and drafting only.

## Repository conventions

- Markdown files are the primary knowledge format; article front matter describes the document and its intended use.
- Keep source attribution and limitations attached to retrieved content.
- Treat examples and quoted model dialogue as illustrative unless the article provides independent evidence.
- When adding, removing or materially changing an article, update the source catalogue, rules, integrity manifest, changelog and review status in `AGENTS.md`, then update this README if scope or navigation changes.

## Licence

This repository is licensed under the MIT License. See [`LICENSE`](LICENSE). The repository licence does not imply that all third-party material linked or discussed in an article is licensed for reuse under MIT.
