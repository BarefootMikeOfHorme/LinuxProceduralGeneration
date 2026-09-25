use crate::scan::{Node, Status, Tier};
use serde::{Deserialize, Serialize};

#[allow(dead_code)]
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum AuthorityState {
    Planned,
    Observed,
    Validated,
    Approved,
    Active,
    Partial,
    Conflicting,
    Missing,
    Quarantined,
    Revoked,
    Unknown,
}

#[derive(Clone, Debug, Serialize)]
pub struct AuthorityPaths {
    pub root_relative: Option<String>,
    pub resolved: Option<String>,
    pub schema: Option<String>,
    pub entrypoint: Option<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct AuthorityEntry {
    pub component_id: String,
    pub level: String,
    pub state: AuthorityState,
    pub aliases: Vec<String>,
    pub paths: AuthorityPaths,
    pub owner: Option<String>,
    pub schema: Option<String>,
    pub source: String,
    pub confidence: f32,
    pub digest: Option<String>,
    pub parent_id: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PromotionEvidence {
    pub schema_id: String,
    pub policy_profile: String,
    pub scan_complete: bool,
    pub schema_valid: bool,
    pub security_passed: bool,
    pub system_requirements_passed: bool,
    pub tier_closure_passed: bool,
    pub observed_digest: String,
    pub approved_digest: String,
    pub known_good_revision: Option<String>,
}

#[allow(dead_code)] // Promotion API is contract-first; CLI wiring follows the state machine.
#[derive(Clone, Debug, Serialize)]
#[serde(tag = "status", rename_all = "kebab-case")]
pub enum PromotionOutcome {
    Approved { entry: Box<AuthorityEntry> },
    Rejected { reasons: Vec<String> },
}

#[derive(Clone, Debug, Serialize)]
pub struct AuthorityConflict {
    pub component_id: String,
    pub reason: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct AuthorityIndex {
    pub schema_version: String,
    pub profile: String,
    pub generated_at: Option<String>,
    pub generator: String,
    pub scan_complete: bool,
    pub entries: Vec<AuthorityEntry>,
    pub conflicts: Vec<AuthorityConflict>,
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "status", rename_all = "kebab-case")]
pub enum Resolution {
    Resolved {
        entry: Box<AuthorityEntry>,
    },
    Ambiguous {
        query: String,
        candidates: Vec<String>,
    },
    NotFound {
        query: String,
    },
}

impl AuthorityIndex {
    pub fn new(profile: &str, scan_complete: bool) -> Self {
        Self {
            schema_version: "0.1.0".to_string(),
            profile: profile.to_string(),
            generated_at: None,
            generator: "al1scan".to_string(),
            scan_complete,
            entries: Vec::new(),
            conflicts: Vec::new(),
        }
    }

    pub fn insert(&mut self, mut entry: AuthorityEntry) {
        if let Some(existing) = self
            .entries
            .iter_mut()
            .find(|candidate| candidate.component_id == entry.component_id)
        {
            existing.state = AuthorityState::Conflicting;
            entry.state = AuthorityState::Conflicting;
            self.conflicts.push(AuthorityConflict {
                component_id: entry.component_id.clone(),
                reason: "duplicate component identity".to_string(),
            });
        }
        self.entries.push(entry);
    }

    pub fn resolve(&self, query: &str) -> Resolution {
        let normalized = normalize_query(query);
        let mut exact: Vec<&AuthorityEntry> = self
            .entries
            .iter()
            .filter(|entry| entry.component_id == normalized)
            .collect();
        if exact.len() == 1 {
            return Resolution::Resolved {
                entry: Box::new(exact.remove(0).clone()),
            };
        }
        if exact.len() > 1 {
            return Resolution::Ambiguous {
                query: query.to_string(),
                candidates: exact
                    .iter()
                    .map(|entry| entry.component_id.clone())
                    .collect(),
            };
        }

        let mut matches: Vec<&AuthorityEntry> = self
            .entries
            .iter()
            .filter(|entry| {
                entry
                    .aliases
                    .iter()
                    .any(|alias| normalize_query(alias) == normalized)
                    || entry
                        .paths
                        .root_relative
                        .as_deref()
                        .map(normalize_query)
                        .filter(|path| path == &normalized)
                        .is_some()
            })
            .collect();

        match matches.len() {
            0 => Resolution::NotFound {
                query: query.to_string(),
            },
            1 => Resolution::Resolved {
                entry: Box::new(matches.remove(0).clone()),
            },
            _ => Resolution::Ambiguous {
                query: query.to_string(),
                candidates: matches
                    .iter()
                    .map(|entry| entry.component_id.clone())
                    .collect(),
            },
        }
    }
}

pub fn build_candidates(profile: &str, root: &Node, scan_complete: bool) -> AuthorityIndex {
    let mut index = AuthorityIndex::new(profile, scan_complete);
    add_node(&mut index, root, None, scan_complete);
    index
}

#[allow(dead_code)] // Promotion API is contract-first; CLI wiring follows the state machine.
pub fn promote_to_approved(
    entry: &AuthorityEntry,
    evidence: &PromotionEvidence,
) -> PromotionOutcome {
    let mut reasons = Vec::new();

    if !matches!(
        entry.state,
        AuthorityState::Observed | AuthorityState::Validated
    ) {
        reasons.push(format!(
            "component state {:?} is not eligible for approval",
            entry.state
        ));
    }
    if !evidence.scan_complete {
        reasons.push("scan is incomplete".to_string());
    }
    if !evidence.schema_valid {
        reasons.push("schema validation failed or is missing".to_string());
    }
    if !evidence.security_passed {
        reasons.push("security validation failed or is missing".to_string());
    }
    if !evidence.system_requirements_passed {
        reasons.push("system requirements failed or are missing".to_string());
    }
    if !evidence.tier_closure_passed {
        reasons.push("tier closure validation failed or is missing".to_string());
    }
    if evidence.observed_digest.trim().is_empty() {
        reasons.push("observed digest is required".to_string());
    }
    if evidence.approved_digest.trim().is_empty() {
        reasons.push("approved digest is required".to_string());
    }
    if evidence
        .known_good_revision
        .as_deref()
        .map(str::trim)
        .filter(|revision| !revision.is_empty())
        .is_none()
    {
        reasons.push("known-good revision is required".to_string());
    }
    if let Some(entry_digest) = &entry.digest {
        if entry_digest != &evidence.observed_digest {
            reasons.push("observed digest does not match the component digest".to_string());
        }
    }

    if !reasons.is_empty() {
        return PromotionOutcome::Rejected { reasons };
    }

    let mut approved = entry.clone();
    approved.state = AuthorityState::Approved;
    approved.schema = Some(evidence.schema_id.clone());
    approved.digest = Some(evidence.approved_digest.clone());
    PromotionOutcome::Approved {
        entry: Box::new(approved),
    }
}

fn add_node(
    index: &mut AuthorityIndex,
    node: &Node,
    parent_id: Option<String>,
    scan_complete: bool,
) {
    let level = tier_name(node.tier);
    let level_key = level.to_ascii_lowercase();
    let relative = if node.rel_path.is_empty() {
        ".".to_string()
    } else {
        node.rel_path.clone()
    };
    let component_id = if parent_id.is_none() {
        format!("{}.l1.root", index.profile)
    } else {
        format!("{}.{}.{}", index.profile, level_key, path_slug(&relative))
    };
    let state = authority_state(node.status, scan_complete);
    let confidence = if node.tier == Tier::Untagged {
        0.25
    } else {
        0.70
    };
    let aliases = if parent_id.is_none() {
        vec![node.name.clone(), index.profile.clone(), "root".to_string()]
    } else {
        vec![node.name.clone()]
    };
    let entry = AuthorityEntry {
        component_id: component_id.clone(),
        level: level.to_string(),
        state,
        aliases,
        paths: AuthorityPaths {
            root_relative: Some(relative),
            resolved: None,
            schema: None,
            entrypoint: None,
        },
        owner: Some(format!("{}.l1.root", index.profile)),
        schema: None,
        source: "scanner".to_string(),
        confidence,
        digest: None,
        parent_id: parent_id.clone(),
    };
    index.insert(entry);

    for child in &node.children {
        add_node(index, child, Some(component_id.clone()), scan_complete);
    }
}

fn authority_state(status: Status, scan_complete: bool) -> AuthorityState {
    if !scan_complete || status == Status::Truncated {
        AuthorityState::Partial
    } else {
        match status {
            Status::MissingExpected => AuthorityState::Planned,
            Status::Empty | Status::Ok | Status::Unclassified | Status::Unmanaged => {
                AuthorityState::Observed
            }
            Status::Truncated => AuthorityState::Partial,
        }
    }
}

fn tier_name(tier: Tier) -> &'static str {
    match tier {
        Tier::L1 => "L1",
        Tier::L2 => "L2",
        Tier::L3 => "L3",
        Tier::L4 => "L4",
        Tier::L5 => "L5",
        Tier::L6 => "L6",
        Tier::Untagged => "Unclassified",
    }
}

fn path_slug(path: &str) -> String {
    path.split(['/', '\\'])
        .map(segment_slug)
        .filter(|segment| !segment.is_empty())
        .collect::<Vec<_>>()
        .join(".")
}

fn segment_slug(segment: &str) -> String {
    let mut output = String::new();
    for character in segment.chars() {
        if character.is_ascii_alphanumeric() {
            output.push(character.to_ascii_lowercase());
        } else if !output.ends_with('-') {
            output.push('-');
        }
    }
    output.trim_matches('-').to_string()
}

fn normalize_query(query: &str) -> String {
    query
        .chars()
        .map(|character| {
            if character.is_ascii_alphanumeric() || character == '.' || character == '-' {
                character.to_ascii_lowercase()
            } else {
                '_'
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scan::{scan_root_with_limits, ScanLimits};
    use std::{fs, path::Path};

    fn write(path: &Path, content: &str) {
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, content).unwrap();
    }

    fn observed_entry() -> AuthorityEntry {
        AuthorityEntry {
            component_id: "lpg-l1.l3.program.forge".to_string(),
            level: "L3".to_string(),
            state: AuthorityState::Observed,
            aliases: vec!["forge".to_string()],
            paths: AuthorityPaths {
                root_relative: Some("tools/forge".to_string()),
                resolved: None,
                schema: None,
                entrypoint: None,
            },
            owner: Some("lpg-l1.l1.root".to_string()),
            schema: None,
            source: "scanner".to_string(),
            confidence: 0.7,
            digest: Some("sha256:observed".to_string()),
            parent_id: Some("lpg-l1.l1.root".to_string()),
        }
    }

    fn complete_evidence() -> PromotionEvidence {
        PromotionEvidence {
            schema_id: "al1.schema.lpg-l1.component-manifest".to_string(),
            policy_profile: "lpg-l1.validation.default".to_string(),
            scan_complete: true,
            schema_valid: true,
            security_passed: true,
            system_requirements_passed: true,
            tier_closure_passed: true,
            observed_digest: "sha256:observed".to_string(),
            approved_digest: "sha256:approved".to_string(),
            known_good_revision: Some("lpg-l1.l3.program.forge@0.1.0".to_string()),
        }
    }

    #[test]
    fn builds_recursive_observed_candidates() {
        let dir = std::env::temp_dir().join(format!("al1_authority_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        write(&dir.join("forge").join("main.py"), "print('ok')");
        let report = scan_root_with_limits(&dir, ScanLimits::for_depth(8)).unwrap();
        let index = build_candidates("lpg-l1", &report.root, report.complete);

        assert!(index.scan_complete);
        assert!(index.entries.len() >= 3);
        assert!(matches!(
            index.resolve("lpg-l1.unclassified.forge.main-py"),
            Resolution::Resolved { .. }
        ));
        assert!(matches!(
            index.resolve("main.py"),
            Resolution::Resolved { .. }
        ));
        assert!(matches!(
            index.resolve("lpg-l1"),
            Resolution::Resolved { .. }
        ));

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn promotion_approves_only_complete_observation() {
        let entry = observed_entry();
        let evidence = complete_evidence();
        match promote_to_approved(&entry, &evidence) {
            PromotionOutcome::Approved { entry } => {
                assert_eq!(entry.state, AuthorityState::Approved);
                assert_eq!(entry.digest.as_deref(), Some("sha256:approved"));
                assert_eq!(
                    entry.schema.as_deref(),
                    Some("al1.schema.lpg-l1.component-manifest")
                );
            }
            PromotionOutcome::Rejected { reasons } => {
                panic!("expected approval, got {reasons:?}");
            }
        }
    }

    #[test]
    fn promotion_rejects_partial_or_incomplete_evidence() {
        let mut entry = observed_entry();
        entry.state = AuthorityState::Partial;
        let mut evidence = complete_evidence();
        evidence.scan_complete = false;
        evidence.security_passed = false;
        let outcome = promote_to_approved(&entry, &evidence);
        assert!(matches!(outcome, PromotionOutcome::Rejected { .. }));
    }

    #[test]
    fn promotion_rejects_missing_known_good_and_digest() {
        let entry = observed_entry();
        let mut evidence = complete_evidence();
        evidence.observed_digest.clear();
        evidence.known_good_revision = None;
        let outcome = promote_to_approved(&entry, &evidence);
        match outcome {
            PromotionOutcome::Rejected { reasons } => {
                assert!(reasons
                    .iter()
                    .any(|reason| reason.contains("observed digest")));
                assert!(reasons
                    .iter()
                    .any(|reason| reason.contains("known-good revision")));
            }
            PromotionOutcome::Approved { .. } => panic!("expected rejection"),
        }
    }

    #[test]
    fn partial_scan_is_not_observed() {
        let dir =
            std::env::temp_dir().join(format!("al1_authority_partial_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        write(&dir.join("one.txt"), "1");
        write(&dir.join("two.txt"), "2");
        let mut limits = ScanLimits::for_depth(8);
        limits.max_entries = 1;
        let report = scan_root_with_limits(&dir, limits).unwrap();
        let index = build_candidates("lpg-l1", &report.root, report.complete);

        assert!(!index.scan_complete);
        assert!(index
            .entries
            .iter()
            .all(|entry| entry.state == AuthorityState::Partial));

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn duplicate_identity_is_reported_as_conflict() {
        let mut index = AuthorityIndex::new("lpg-l1", true);
        let entry = AuthorityEntry {
            component_id: "lpg-l1.l3.program.forge".to_string(),
            level: "l3".to_string(),
            state: AuthorityState::Observed,
            aliases: vec!["forge".to_string()],
            paths: AuthorityPaths {
                root_relative: Some("one/forge".to_string()),
                resolved: None,
                schema: None,
                entrypoint: None,
            },
            owner: None,
            schema: None,
            source: "scanner".to_string(),
            confidence: 0.7,
            digest: None,
            parent_id: None,
        };
        index.insert(entry.clone());
        index.insert(entry);

        assert_eq!(index.conflicts.len(), 1);
        assert!(matches!(
            index.resolve("lpg-l1.l3.program.forge"),
            Resolution::Ambiguous { .. }
        ));
    }
}
