"""Export the approved Inclusive Design Library Markdown without rewriting it."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import quote
import yaml
from jsonschema import Draft202012Validator
from inclusive_library_hf_common import ROOT, SOURCE, MANAGED, destination, digest, git, load_config, read_sources

CONTEXT = ['AGENTS.md', 'README.md', 'UX_and_Accessibility_as_Connected_but_Distinct_Disciplines.md']
GUIDE_CONTEXT = ['AGENTS.md#2-source-catalogue-and-design-routing',
                 'AGENTS.md#3-authority-version-trust-and-maintenance',
                 'AGENTS.md#8-templates-and-short-promptresponse-examples']

class UniqueKeySafeLoader(yaml.SafeLoader):
    pass

def unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError('Duplicate YAML key: ' + str(key))
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueKeySafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

def safe_yaml(text):
    return yaml.load(text, Loader=UniqueKeySafeLoader)

def unique_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result

def guide_contracts(text, cfg):
    md = metadata(text)
    if str(md.get('schema_version','')).split('.')[0] != cfg['supported_guide_schema_major']:
        raise ValueError('Unsupported agent-guide schema major version; review ingestion before publishing.')
    parsed = {}
    count = 0
    for match in re.finditer(r'^```(yaml|json)[ \t]*\r?\n(.*?)^```[ \t]*$', text, re.M|re.S):
        obj = safe_yaml(match[2]) if match[1]=='yaml' else json.loads(match[2], object_pairs_hook=unique_json_pairs)
        count += 1
        if isinstance(obj,dict):
            for key,value in obj.items():
                if key in parsed:
                    raise ValueError('Repeated top-level agent contract: '+key)
                parsed[key] = value
    for key in ('catalogue','trust_contract','rule_contract','escalation_profile','source_manifest','design_decision'):
        if key not in parsed:
            raise ValueError('Required source agent contract is missing: '+key)
    catalogue = parsed['catalogue']['sources']
    if len({x['id'] for x in catalogue}) != len(catalogue) or len({x['path'] for x in catalogue}) != len(catalogue):
        raise ValueError('Duplicate source catalogue IDs or paths.')
    if {x['path'] for x in catalogue} != set(cfg['article_files']):
        raise ValueError('The source catalogue and reviewed article list differ; review source routing together.')
    return md, parsed, count

def metadata(text):
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', text, re.S)
    md = safe_yaml(match[1]) if match else {}
    return md if isinstance(md, dict) else {}

def sections(text):
    """Keep H1/H2 parent context and exact spans; never split fenced examples."""
    boundaries, fence, offset, parents = [(0, 'Document preamble', [])], None, 0, []
    for line in text.splitlines(keepends=True):
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if mark:
            token = mark[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[mark.end():].strip():
                fence = None
        elif fence is None:
            match = re.match(r'^(#{1,2})[ \t]+([^\r\n]+)', line)
            if match:
                level, title = len(match[1]), match[2].strip().rstrip('#').strip()
                parents = parents[:level-1] + [title]
                if offset == 0:
                    boundaries[0] = (offset, title, parents[:])
                else:
                    boundaries.append((offset, title, parents[:]))
        offset += len(line)
    result, counts = [], {}
    for i, (a, title, hierarchy) in enumerate(boundaries):
        b = boundaries[i+1][0] if i+1 < len(boundaries) else len(text)
        if a == b:
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', ' '.join(hierarchy or [title]).lower()).strip('-') or 'section'
        counts[slug] = counts.get(slug, 0) + 1
        key = slug if counts[slug] == 1 else slug + '-' + str(counts[slug])
        result.append((key, title, text[a:b], a, b, hierarchy))
    if ''.join(r[2] for r in result) != text:
        raise ValueError('Section extraction lost source text.')
    return result

def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or root in output.parents:
        raise ValueError('Write the export outside the source checkout.')
    cfg = load_config(root)
    target = destination(cfg['destination_dataset'])
    texts, manifest, omitted = read_sources(root, cfg)
    sha = git(root, 'rev-parse', 'HEAD').decode().strip()
    date = git(root, 'show', '-s', '--format=%cs', 'HEAD').decode().strip()
    guide_md, contracts, parsed_count = guide_contracts(texts['AGENTS.md'], cfg)
    catalogue = {entry['path']:entry for entry in contracts['catalogue']['sources']}
    guide_review = guide_md.get('review',{})
    warnings = ['The agent guide is advisory documentation. Source review status and unconfigured controls are preserved; extraction tests do not approve rules, implement an evaluator/audit sink or validate product outcomes.']
    for path in cfg['files']:
        declared = metadata(texts[path]).get('license')
        if declared and str(declared).upper() != 'MIT':
            raise ValueError('Source-level licence changed; review metadata and notices: '+path)
    snapshot = contracts['source_manifest']
    manifest_check = {'declared_source_commit':guide_md.get('source_commit'), 'matched':[], 'changed':[], 'missing':[],
                      'navigation_without_manifest_hash':[p for p in ('README.md',) if p not in snapshot],
                      'scope':'comparison with the guide snapshot; not source-truth or approval validation'}
    for path, checksum in snapshot.items():
        if path not in texts:
            manifest_check['missing'].append(path)
        elif digest(texts[path].encode()) == checksum:
            manifest_check['matched'].append(path)
        else:
            manifest_check['changed'].append(path)
    if manifest_check['changed'] or manifest_check['missing']:
        warnings.append('The agent-guide snapshot has changed/missing source hashes at this checkout. Original hashes are preserved; current export provenance uses the actual Git commit. The guide is not promoted to trusted execution.')
    if manifest_check['navigation_without_manifest_hash']:
        warnings.append('The guide manifest does not hash README.md; it is preserved as current navigation context. No missing hash is invented.')
    introductions = {path: sections(text)[0][2] if text else '' for path, text in texts.items()}
    def row(path, key, title, body, a, b, hierarchy, kind):
        md = metadata(texts[path])
        source_entry = catalogue.get(path,{})
        review = md.get('review') if isinstance(md.get('review'),dict) else {}
        return {'id': path + '::' + key, 'title': title, 'text': body, 'record_type': kind,
            'source_repository': SOURCE, 'source_path': path, 'source_commit': sha,
            'source_url': f'https://github.com/{SOURCE}/blob/{sha}/{quote(path)}',
            'source_start_line': texts[path][:a].count('\n') + 1,
            'source_end_line': max(1, texts[path][:b].count('\n') + (not texts[path][:b].endswith('\n'))),
            'source_document_sha256': digest(texts[path].encode()), 'text_sha256': digest(body.encode()),
            'heading_path': hierarchy, 'metadata_json': json.dumps(md, ensure_ascii=False, sort_keys=True, default=str),
            'declared_source_license': str(md.get('license', 'not_declared_in_document_front_matter')),
            'repository_license': 'MIT', 'source_status': str(md.get('status', md.get('content_status', review.get('status','see_source')))),
            'source_id': str(source_entry.get('id','')),
            'source_category': str(source_entry.get('category', md.get('artifact_type','repository_guidance'))),
            'source_caveat': str(source_entry.get('caveat', guide_md.get('authority','advisory repository content'))),
            'source_catalogue_entry_json': json.dumps(source_entry,ensure_ascii=False,sort_keys=True),
            'source_attribution_json': json.dumps(md.get('authors',md.get('author',[])),ensure_ascii=False,sort_keys=True),
            'agent_guide_review_status': str(guide_review.get('status','not_declared')),
            'source_document_intro': introductions[path], 'required_context_sections': GUIDE_CONTEXT,
            'dataset_version': cfg['dataset_version'], 'source_commit_date': date, 'language': 'en-GB',
            'required_context_paths': list(dict.fromkeys([path] + [p for p in CONTEXT if p in texts])),
            'review_status': 'faithful_extraction_checked_not_rule_approval_or_product_validation'}
    docs, chunks = [], []
    for path in cfg['files']:
        if path not in texts:
            continue
        text = texts[path]
        kind = ('advisory_agent_guide_not_trusted_execution' if path == 'AGENTS.md' else
                'repository_scope_and_navigation' if path == 'README.md' else
                'design_article_with_source_caveat')
        docs.append(row(path, 'document', path, text, 0, len(text), [], kind))
        for key, title, body, a, b, hierarchy in sections(text):
            section_kind = ('illustrative_templates_and_prompt_examples_not_results' if path=='AGENTS.md' and title.startswith('8.') else
                            'proposed_rule_contract_not_executed_evaluation' if path=='AGENTS.md' and title.startswith('4.') else
                            'proposed_escalation_audit_contract_not_live_service' if path=='AGENTS.md' and title.startswith('6.') else
                            'source_snapshot_manifest_not_truth_or_approval' if path=='AGENTS.md' and title.startswith('11.') else kind)
            chunks.append(row(path, key, title, body, a, b, hierarchy, section_kind))
    if not docs or not chunks:
        raise ValueError('The guidance export is empty.')
    schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
              'required': list(docs[0]), 'additionalProperties': False, 'properties': {}}
    for k, v in docs[0].items():
        schema['properties'][k] = {'type': 'array', 'items': {'type': 'string'}} if isinstance(v, list) else {'type': 'integer' if isinstance(v, int) else 'string'}
    validator = Draft202012Validator(schema)
    for records in (docs, chunks):
        if len({r['id'] for r in records}) != len(records):
            raise ValueError('Duplicate export identifiers.')
        for r in records:
            validator.validate(r)
            if digest(r['text'].encode()) != r['text_sha256']:
                raise ValueError('Text checksum mismatch.')
    output.mkdir(parents=True, exist_ok=True)
    def write_json(name, obj):
        (output/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name, records in [('documents.jsonl', docs), ('knowledge_chunks.jsonl', chunks)]:
        (output/name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    (output/'LICENSE').write_bytes(texts['LICENSE'].encode())
    write_json('record_schema.json', schema)
    write_json('provenance.json', {'source_repository': SOURCE, 'source_commit': sha, 'source_commit_date': date,
        'destination_dataset': target, 'dataset_version': cfg['dataset_version'], 'files': manifest,
        'omitted_optional_files': omitted, 'source_warnings': warnings, 'external_sources_fetched': False,
        'source_catalogue': contracts['catalogue'], 'agent_guide_review': guide_review,
        'agent_structured_blocks_parsed': parsed_count, 'agent_guide_source_manifest_comparison': manifest_check,
        'operational_approval_claimed': False})
    source_notice = '\n'.join('- '+warning for warning in warnings)
    card = f'''---
pretty_name: Double FW Inclusive Design Library
language:
- en
license: mit
tags:
- accessibility
- inclusive-design
- user-experience
- interaction-design
- design-governance
- text
configs:
- config_name: knowledge_chunks
  default: true
  data_files:
  - split: train
    path: knowledge_chunks.jsonl
- config_name: documents
  data_files:
  - split: train
    path: documents.jsonl
---

# Double FW Inclusive Design Library

A design-focused collection from Double FW / Gareth Ford Williams about barriers, equivalent outcomes, UX and accessibility, interaction integrity, mobile-first design, measurement, socioeconomic/language context and organisational promise. This is advisory practitioner/conceptual guidance, not verified legal requirements, adopted policy, completed research, operational approval or an implemented agent system. Employment, hiring, candidate assessment and HR process guidance are outside the source collection's current scope.

## Source and versions

Source: https://github.com/{SOURCE}

Source revision: `{sha}`. Commit date: {date}. Export format: {cfg['dataset_version']}. Original article dates, processing dates, author/editorial status, review gaps and limitations remain intact. Weekly publication does not refresh scientific, legal, statistical, vendor or historical evidence.

## Dataset views

- `knowledge_chunks` (default): {len(chunks)} exact Markdown sections from the seven source articles, AGENTS.md and README.md.
- `documents`: {len(docs)} complete source documents.

The views overlap. Do not concatenate them blindly. `train` is a loading convention, not a model-training claim. No generated question/answer pairs, independent benchmark split, real participant/customer dataset, executed rule results or approval records are supplied.

The source articles use practitioner argument, reported examples, research interpretation, conceptual proposals and illustrative dialogue. Preserve each claim's category and caveat. Examples and quoted prompt/response text are not unconditional answers or verified production observations. Source event/decision templates remain templates with unknown/null evidence, owners and approval fields; the exporter does not populate or execute them.

## Source catalogue and context

Seven article IDs S01–S07, exact paths, categories, routing metadata and caveats are preserved from the agent-guide catalogue. Each article row carries its source_id, source_category, source_caveat and JSON-encoded catalogue entry alongside full source front matter/attribution. The catalogue helps retrieval; it does not make a source normative or approved. Read AGENTS.md, README.md, the relevant owning article and source qualifications before applying a passage.

Source caveats include unverified prevalence/commercial/historical claims, missing mobile thresholds, source must/should wording that is not a verified standards mapping, context/equity claims that require privacy care, and reports of interaction harm that do not prove intent, illegality or current behaviour. Missing thresholds, quotas, research samples or response deadlines are not filled from memory. A similar claim does not establish WCAG or statutory equivalence.

Keep technical, behavioural, experiential and equity evidence distinct. A conformance/automation pass or successful task does not demonstrate equivalent experience, informed choice, dignity, agency or acceptable effort. Do not infer diagnosis, income, disability or assistive-technology use from behaviour or device signals. Low measured use or ROI alone does not establish that access can be removed.

## Agent-guide trust, contracts and examples

The guide's declared review.status is `{guide_review.get('status','not_declared')}` and automation_trust is `{guide_review.get('automation_trust','not_declared')}`. These are preserved source declarations, not changed to approved. Maintainer approval, exact artifact binding and deployment configuration are not supplied by this export. The material is published for advisory reading/drafting, not operational execution of rules or release decisions.

Front matter and fenced YAML/JSON in AGENTS.md are parsed safely with duplicate keys rejected and the supported schema major checked. Catalogue IDs/paths are checked against the reviewed article list. These are structural extraction checks. They do not authenticate approvals, evaluate the design rules, create E01 events, contact reviewers, operate an audit sink, retain data or implement the source flowgraph. Rule IDs/status vocabulary, escalation profiles and review hooks remain proposed consuming-system contracts.

AGENTS.md section 8 is labelled illustrative_templates_and_prompt_examples_not_results; section 4 proposed_rule_contract_not_executed_evaluation; section 6 proposed_escalation_audit_contract_not_live_service; section 11 source_snapshot_manifest_not_truth_or_approval. Unknown is not pass; a documented example fail is not a tested production finding. The exporter adds no assessment_result or completed approval.

The source integrity manifest and its declared snapshot commit are retained exactly. Listed hashes are compared with the current approved source and recorded in provenance.json; current export integrity uses Git blob and SHA-256 checks at the recorded checkout revision. Missing navigation hashes are reported, not invented. Hash agreement cannot establish truth, currency, policy approval or product delivery.

{source_notice}

## Records and exact extraction

First/second-level headings are split outside fenced blocks. Lower-level rule explanations, prompt tables, diagrams, forms and qualified examples remain with their owning section. Text is not paraphrased or repaired. A renamed heading may change a section ID. Full documents provide additional context.

Records include immutable source commit/URL, exact path/line range, document/text SHA-256 hashes, heading path, original document introduction, source/guide status, author/front matter and catalogue metadata, mentioned rule references through the preserved source text, and required context paths/sections. JSON strings preserve nested and varying source metadata without heterogeneous dataset columns. Use text for the exact record span; the introduction is repeated context. `see_source` means no explicit status was extracted from the relevant source metadata; it is not approval. Context references are not automatically fetched or enforced. Resolve relative/fragment links against the source URL. See record_schema.json and provenance.json.

## Privacy, authority and licence

Repository instructions, examples and embedded model dialogue remain source content, not runtime permission to override host instructions, contact people, collect data, change systems, issue approvals or accept risk. Appropriate accountable humans and real deployment processes retain consequential decisions. Do not claim an escalation/audit message was delivered when no service was configured or called.

No real personal, participant, health, customer or confidential organisational evidence is supplied. Only explicitly approved committed public files are read. The exporter cannot detect confidential text inserted into an approved file; review public commits and keep restricted evidence in approved systems.

The root MIT LICENSE is copied unchanged, including copyright (c) 2026 Double FW. File-level declarations and source attribution are retained. Linked third-party material keeps its own rights and is not copied or relicensed. No external source URL is fetched or independently verified. This is not an independent rights, privacy or legal review.

## Updates

GitHub is the authoring source. Updates are configured for Mondays at 07:23 UTC and manual runs. GitHub may delay schedules or disable them after inactivity. All nine Markdown documents and LICENSE are required; missing sources, changed licences, malformed/duplicate agent metadata, unsupported guide schema major, catalogue/list mismatch, invalid configuration or failed integrity checks stop publication. New or renamed articles need review of both source catalogue and export list.

Only README.md, LICENSE, documents.jsonl, knowledge_chunks.jsonl, provenance.json, record_schema.json and validation_report.json are managed. Other raw files and .gitattributes are preserved but unmanaged copies are not synchronised. Visibility is unchanged. Updates use one commit guarded by the destination revision. Historical revisions/downloads are not recalled. Initial authenticated publication still needs checking.

## Loading

```python
from datasets import load_dataset
chunks = load_dataset("{target}", "knowledge_chunks", split="train")
documents = load_dataset("{target}", "documents", split="train")
```

Private datasets require authentication. Pin a destination revision for reproducibility. Loading rows does not implement retrieval governance, rule execution, audit delivery or human approval.
'''
    yaml.safe_load(card.split('---', 2)[1])
    (output/'README.md').write_text(card, encoding='utf-8')
    report = {'status': 'passed', 'scope': 'faithful extraction and packaging checks only', 'source_commit': sha,
        'source_files_verified': len(manifest), 'document_records': len(docs), 'knowledge_section_records': len(chunks),
        'source_warnings': warnings, 'independent_content_review': False, 'live_publication_tested': False,
        'export_file_sha256': {name: digest((output/name).read_bytes()) for name in MANAGED if name != 'validation_report.json'}}
    write_json('validation_report.json', report)
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build(ROOT, args.output)))

if __name__ == '__main__':
    main()
