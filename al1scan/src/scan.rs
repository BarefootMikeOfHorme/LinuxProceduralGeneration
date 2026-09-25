use serde::Serialize;
use std::{
    collections::{BTreeMap, HashMap},
    fs,
    io::Read,
    path::Path,
    time::{Duration, Instant, SystemTime},
};

pub const DEFAULT_MAX_ENTRIES: usize = 100_000;
pub const DEFAULT_MAX_TOTAL_BYTES: u64 = 8 * 1024 * 1024 * 1024;
pub const DEFAULT_MAX_DURATION_SECS: u64 = 120;

#[derive(Clone, Debug)]
pub struct ScanLimits {
    pub max_depth: usize,
    pub max_entries: usize,
    pub max_total_bytes: u64,
    pub max_duration: Duration,
}

impl ScanLimits {
    pub fn for_depth(max_depth: usize) -> Self {
        Self {
            max_depth,
            max_entries: DEFAULT_MAX_ENTRIES,
            max_total_bytes: DEFAULT_MAX_TOTAL_BYTES,
            max_duration: Duration::from_secs(DEFAULT_MAX_DURATION_SECS),
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct ScanWarning {
    pub kind: String,
    pub path: String,
    pub message: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ScanReport {
    pub root: Node,
    pub summary: ScanSummary,
    pub warnings: Vec<ScanWarning>,
    pub complete: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct ScanReportSummary {
    pub summary: ScanSummary,
    pub warnings: Vec<ScanWarning>,
    pub complete: bool,
}

struct ScanState {
    started: Instant,
    entries: usize,
    bytes: u64,
    warnings: Vec<ScanWarning>,
    limit_hit: bool,
}

/// Coarse tier guess for a scanned node, based on naming heuristics only.
/// This is advisory — a suggestion for a human/AI to confirm, never an
/// authoritative classification.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum Tier {
    L1,
    L2,
    L3,
    L4,
    L5,
    L6,
    Untagged,
}

impl Tier {
    pub fn label(&self) -> &'static str {
        match self {
            Tier::L1 => "L1",
            Tier::L2 => "L2",
            Tier::L3 => "L3",
            Tier::L4 => "L4",
            Tier::L5 => "L5",
            Tier::L6 => "L6",
            Tier::Untagged => "--",
        }
    }

    /// Guess a tier from a folder/file name using simple keyword matching.
    /// Order matters: more specific tiers are checked before generic ones.
    fn guess(name: &str) -> Tier {
        let n = name.to_lowercase();
        let has_any = |words: &[&str]| words.iter().any(|w| n.contains(w));

        if has_any(&["l1", "root", "authority", "governance", "l1root"]) {
            Tier::L1
        } else if has_any(&[
            "l4",
            "contract",
            "schema",
            "validation",
            "safety",
            "guardrail",
        ]) {
            Tier::L4
        } else if has_any(&["l2", "shell", "env", "venv", "wsl", "powershell"]) {
            Tier::L2
        } else if has_any(&["l3", "program", "tool", "service", "src", "app", "forge"]) {
            Tier::L3
        } else if has_any(&["l5", "doc", "readme", "template", "example"]) {
            Tier::L5
        } else if has_any(&[
            "l6",
            "content",
            "artifact",
            "asset",
            "model",
            "output",
            "generated",
        ]) {
            Tier::L6
        } else {
            Tier::Untagged
        }
    }
}

/// Presence/health status for a node, computed from lightweight,
/// read-only checks (presence-ladder rung 1 only — no code execution,
/// no parsing beyond a couple of well-known manifest file names).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum Status {
    Ok,
    Empty,
    Truncated,
    MissingExpected,
    Unclassified,
    Unmanaged,
}

impl Status {
    pub fn label(&self) -> &'static str {
        match self {
            Status::Ok => "ok",
            Status::Empty => "empty",
            Status::Truncated => "truncated",
            Status::MissingExpected => "missing-expected",
            Status::Unclassified => "unclassified",
            Status::Unmanaged => "unmanaged",
        }
    }
}

/// How a node compares to the previous scan (populated on rescan only).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum UpdateState {
    Unchanged,
    New,
    Modified,
    Removed,
}

impl UpdateState {
    pub fn label(&self) -> &'static str {
        match self {
            UpdateState::Unchanged => "unchanged",
            UpdateState::New => "new",
            UpdateState::Modified => "modified",
            UpdateState::Removed => "removed",
        }
    }
}

/// Basic compatibility facts pulled from a well-known manifest file, if
/// present. Files are read as text only — never executed, never a .env.
#[derive(Clone, Default, Debug, Serialize)]
pub struct CompatInfo {
    pub manifest_file: Option<String>,
    pub package_name: Option<String>,
    pub package_version: Option<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct ScanSummary {
    pub total_nodes: usize,
    pub directories: usize,
    pub files: usize,
    pub total_bytes: u64,
    pub truncated_nodes: usize,
    pub warnings: usize,
    pub status_counts: BTreeMap<String, usize>,
    pub tier_counts: BTreeMap<String, usize>,
}

impl ScanSummary {
    pub fn short_line(&self) -> String {
        let status = |key: &str| self.status_counts.get(key).copied().unwrap_or(0);
        format!(
            "nodes={} dirs={} files={} bytes={} ok={} missing={} truncated={} unmanaged={} warnings={}",
            self.total_nodes,
            self.directories,
            self.files,
            self.total_bytes,
            status("ok"),
            status("missing-expected"),
            status("truncated"),
            status("unmanaged"),
            self.warnings,
        )
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct Node {
    pub name: String,
    pub rel_path: String,
    pub is_dir: bool,
    pub tier: Tier,
    pub status: Status,
    pub update_state: UpdateState,
    pub size_bytes: u64,
    pub modified_unix: u64,
    pub key_files: Vec<String>,
    pub compat: CompatInfo,
    pub repair_note: Option<String>,
    pub children: Vec<Node>,
}

impl Node {
    pub fn descendant_count(&self) -> usize {
        1 + self
            .children
            .iter()
            .map(|c| c.descendant_count())
            .sum::<usize>()
    }
}

pub fn summarize(root: &Node) -> ScanSummary {
    let mut summary = ScanSummary {
        total_nodes: 0,
        directories: 0,
        files: 0,
        total_bytes: 0,
        truncated_nodes: 0,
        warnings: 0,
        status_counts: BTreeMap::new(),
        tier_counts: BTreeMap::new(),
    };
    summarize_node(root, &mut summary);
    summary
}

fn summarize_node(node: &Node, summary: &mut ScanSummary) {
    summary.total_nodes += 1;
    if node.is_dir {
        summary.directories += 1;
    } else {
        summary.files += 1;
        summary.total_bytes = summary.total_bytes.saturating_add(node.size_bytes);
    }
    if node.status == Status::Truncated {
        summary.truncated_nodes += 1;
    }
    *summary
        .status_counts
        .entry(node.status.label().to_string())
        .or_insert(0) += 1;
    *summary
        .tier_counts
        .entry(node.tier.label().to_string())
        .or_insert(0) += 1;
    for child in &node.children {
        summarize_node(child, summary);
    }
}

/// Fingerprint of a single path used to diff against a previous scan.
#[derive(Clone, Copy)]
struct Fingerprint {
    size: u64,
    modified: u64,
}

/// Files whose presence we note directly on a node without reading content.
/// `.env` and anything that looks like a secret is deliberately excluded.
const KEY_FILE_NAMES: &[&str] = &[
    "readme.md",
    "readme.txt",
    "pyproject.toml",
    "cargo.toml",
    "package.json",
    "requirements.txt",
    "gameplan.md",
    "agents.md",
    "manifest.json",
    "manifest.jsonc",
];

const MANIFEST_FILES_FOR_COMPAT: &[&str] = &["pyproject.toml", "cargo.toml", "package.json"];

const MAX_MANIFEST_BYTES: u64 = 64 * 1024;

const OPAQUE_DIRS: &[&str] = &[
    "node_modules",
    "target",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".al1scan_reports",
    ".al1-incoming",
    "build",
    "dist",
    "output",
    "outputs",
    "logs",
    "uploads",
];

fn is_sensitive_name(name: &str) -> bool {
    let lower = name.to_ascii_lowercase();
    lower == ".env"
        || lower.starts_with(".env.")
        || lower == "id_rsa"
        || lower == "id_ed25519"
        || lower == ".npmrc"
        || lower == ".pypirc"
        || lower == "credentials.json"
        || lower.ends_with(".pem")
        || lower.ends_with(".key")
        || lower == ".aws"
        || lower == ".ssh"
        || lower == "secrets"
}

fn is_opaque_dir(name: &str) -> bool {
    OPAQUE_DIRS
        .iter()
        .any(|candidate| name.eq_ignore_ascii_case(candidate))
}

pub fn is_link_like(metadata: &fs::Metadata) -> bool {
    if metadata.file_type().is_symlink() {
        return true;
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    false
}

fn unix_time_nanos(t: SystemTime) -> u64 {
    t.duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_nanos().min(u64::MAX as u128) as u64)
        .unwrap_or(0)
}

/// Reads a small manifest file as plain text (never executed) and pulls out
/// a `name`/`version` pair with a minimal, tolerant line scan. Good enough
/// for a presence-level compatibility hint, not a real TOML/JSON parser.
fn read_compat_info(dir: &Path) -> CompatInfo {
    for fname in MANIFEST_FILES_FOR_COMPAT {
        let p = dir.join(fname);
        if let Ok(mut file) = fs::File::open(&p) {
            let mut text = String::new();
            if file
                .by_ref()
                .take(MAX_MANIFEST_BYTES)
                .read_to_string(&mut text)
                .is_err()
            {
                continue;
            }
            let mut name = None;
            let mut version = None;
            for line in text.lines().take(200) {
                let t = line.trim();
                if name.is_none() {
                    if let Some(v) = extract_kv(t, "name") {
                        name = Some(v);
                    }
                }
                if version.is_none() {
                    if let Some(v) = extract_kv(t, "version") {
                        version = Some(v);
                    }
                }
                if name.is_some() && version.is_some() {
                    break;
                }
            }
            return CompatInfo {
                manifest_file: Some(fname.to_string()),
                package_name: name,
                package_version: version,
            };
        }
    }
    CompatInfo::default()
}

/// Extracts a bare `key = "value"` or `"key": "value"` style line's value.
/// Deliberately dumb — no code execution, no full parser dependency.
fn extract_kv(line: &str, key: &str) -> Option<String> {
    let toml_form = format!("{key} =");
    let json_form = format!("\"{key}\"");
    if line.starts_with(&toml_form) || line.starts_with(&json_form) {
        let after_colon = line.split_once([':', '='])?.1;
        let cleaned = after_colon
            .trim()
            .trim_matches(',')
            .trim_matches('"')
            .trim();
        if !cleaned.is_empty() {
            return Some(cleaned.to_string());
        }
    }
    None
}

fn compute_status(
    tier: Tier,
    is_dir: bool,
    key_files: &[String],
    child_count: usize,
    truncated: bool,
) -> Status {
    if truncated {
        return Status::Truncated;
    }
    if is_dir && child_count == 0 {
        return Status::Empty;
    }
    // Tier-specific presence expectations (deliberately shallow — v1).
    match tier {
        Tier::L4 => {
            let has_schema = key_files
                .iter()
                .any(|k| k.contains("schema") || k.contains("manifest"));
            if is_dir && !has_schema && child_count > 0 {
                Status::MissingExpected
            } else {
                Status::Ok
            }
        }
        Tier::L5 => {
            let has_readme = key_files.iter().any(|k| k.starts_with("readme"));
            if is_dir && !has_readme {
                Status::MissingExpected
            } else {
                Status::Ok
            }
        }
        Tier::Untagged => Status::Unclassified,
        _ => Status::Ok,
    }
}

fn repair_note_for(tier: Tier, status: Status) -> Option<String> {
    match (tier, status) {
        (_, Status::Empty) => {
            Some("Empty directory — remove, or populate per expected schema.".into())
        }
        (_, Status::Truncated) => {
            Some("Directory was not fully scanned because the depth limit was reached.".into())
        }
        (Tier::L4, Status::MissingExpected) => Some(
            "L4 node has no schema/manifest file — add one or confirm it's intentionally bare."
                .into(),
        ),
        (Tier::L5, Status::MissingExpected) => {
            Some("L5 (docs) node has no README — add one for discoverability.".into())
        }
        (Tier::Untagged, Status::Unclassified) => {
            Some("No tier keyword matched — confirm manually or add a naming hint.".into())
        }
        _ => None,
    }
}

/// Recursively, read-only walks `root`, producing a tiered manifest tree.
/// Never opens `.env` files and never executes anything it finds.
pub fn scan_root_with_limits(root: &Path, limits: ScanLimits) -> std::io::Result<ScanReport> {
    let canonical_root = root.canonicalize()?;
    let mut state = ScanState {
        started: Instant::now(),
        entries: 0,
        bytes: 0,
        warnings: Vec::new(),
        limit_hit: false,
    };
    let root_node = scan_dir(&canonical_root, &canonical_root, 0, &limits, &mut state)?;
    let mut summary = summarize(&root_node);
    summary.warnings = state.warnings.len();
    Ok(ScanReport {
        root: root_node,
        summary,
        complete: !state.limit_hit,
        warnings: state.warnings,
    })
}

fn scan_dir(
    root: &Path,
    dir: &Path,
    depth: usize,
    limits: &ScanLimits,
    state: &mut ScanState,
) -> std::io::Result<Node> {
    let name = dir
        .file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_else(|| dir.to_string_lossy().to_string());
    let rel_path = dir
        .strip_prefix(root)
        .unwrap_or(dir)
        .to_string_lossy()
        .to_string();

    let meta = fs::metadata(dir)?;
    let modified_unix = meta.modified().map(unix_time_nanos).unwrap_or(0);

    let mut key_files = Vec::new();
    let mut children = Vec::new();

    if depth < limits.max_depth && !state.limit_hit {
        let mut entries = Vec::new();
        for entry in fs::read_dir(dir)? {
            if state.started.elapsed() >= limits.max_duration {
                state.limit_hit = true;
                state.warnings.push(ScanWarning {
                    kind: "duration-limit".into(),
                    path: dir.display().to_string(),
                    message: "scan duration limit reached".into(),
                });
                break;
            }
            match entry {
                Ok(entry) => {
                    if state.entries >= limits.max_entries {
                        state.limit_hit = true;
                        state.warnings.push(ScanWarning {
                            kind: "entry-limit".into(),
                            path: dir.display().to_string(),
                            message: "scan entry limit reached".into(),
                        });
                        break;
                    }
                    state.entries += 1;
                    entries.push(entry.path());
                }
                Err(error) => {
                    state.limit_hit = true;
                    state.warnings.push(ScanWarning {
                        kind: "unreadable-entry".into(),
                        path: dir.display().to_string(),
                        message: format!("directory entry could not be read: {error}"),
                    });
                }
            }
        }
        entries.sort();

        for path in entries {
            if state.started.elapsed() >= limits.max_duration {
                state.limit_hit = true;
                state.warnings.push(ScanWarning {
                    kind: "duration-limit".into(),
                    path: path.display().to_string(),
                    message: "scan duration limit reached".into(),
                });
                break;
            }

            let display_name = path
                .file_name()
                .map(|n| n.to_string_lossy().to_string())
                .unwrap_or_default();
            let fname = display_name.to_ascii_lowercase();

            // Never open or descend into secret material.
            if is_sensitive_name(&fname) {
                continue;
            }

            let metadata = fs::symlink_metadata(&path)?;
            if is_link_like(&metadata) {
                state.warnings.push(ScanWarning {
                    kind: "symlink-skipped".into(),
                    path: path.display().to_string(),
                    message: "symbolic link/junction was not followed".into(),
                });
                children.push(Node {
                    name: display_name,
                    rel_path: path
                        .strip_prefix(root)
                        .unwrap_or(&path)
                        .to_string_lossy()
                        .to_string(),
                    is_dir: false,
                    tier: Tier::Untagged,
                    status: Status::Unmanaged,
                    update_state: UpdateState::Unchanged,
                    size_bytes: 0,
                    modified_unix: metadata.modified().map(unix_time_nanos).unwrap_or(0),
                    key_files: vec![],
                    compat: CompatInfo::default(),
                    repair_note: Some(
                        "Symbolic link/junction was not followed; review its target explicitly."
                            .into(),
                    ),
                    children: vec![],
                });
                continue;
            }

            if metadata.is_dir() {
                let canonical_path = path.canonicalize()?;
                if !canonical_path.starts_with(root) {
                    state.warnings.push(ScanWarning {
                        kind: "external-directory-skipped".into(),
                        path: path.display().to_string(),
                        message: "directory resolved outside the approved scan root".into(),
                    });
                    children.push(Node {
                        name: display_name,
                        rel_path: path
                            .strip_prefix(root)
                            .unwrap_or(&path)
                            .to_string_lossy()
                            .to_string(),
                        is_dir: true,
                        tier: Tier::Untagged,
                        status: Status::Unmanaged,
                        update_state: UpdateState::Unchanged,
                        size_bytes: 0,
                        modified_unix: metadata.modified().map(unix_time_nanos).unwrap_or(0),
                        key_files: vec![],
                        compat: CompatInfo::default(),
                        repair_note: Some("Directory resolved outside the approved scan root and was not scanned.".into()),
                        children: vec![],
                    });
                    continue;
                }

                // Treat dependency, build, cache, and report directories as
                // opaque leaves instead of recursively scanning them.
                if is_opaque_dir(&fname) {
                    state.warnings.push(ScanWarning {
                        kind: "opaque-directory".into(),
                        path: path.display().to_string(),
                        message: "generated/dependency/cache directory was not scanned into".into(),
                    });
                    children.push(Node {
                        name: display_name,
                        rel_path: path
                            .strip_prefix(root)
                            .unwrap_or(&path)
                            .to_string_lossy()
                            .to_string(),
                        is_dir: true,
                        tier: Tier::guess(&fname),
                        status: Status::Ok,
                        update_state: UpdateState::Unchanged,
                        size_bytes: 0,
                        modified_unix: metadata.modified().map(unix_time_nanos).unwrap_or(0),
                        key_files: vec![],
                        compat: CompatInfo::default(),
                        repair_note: Some(
                            "Opaque directory (dependency/build/cache/report) — not scanned into."
                                .into(),
                        ),
                        children: vec![],
                    });
                    continue;
                }
                match scan_dir(root, &path, depth + 1, limits, state) {
                    Ok(child) => children.push(child),
                    Err(error) => {
                        state.limit_hit = true;
                        state.warnings.push(ScanWarning {
                            kind: "unreadable-directory".into(),
                            path: path.display().to_string(),
                            message: format!("directory could not be scanned: {error}"),
                        });
                        children.push(Node {
                            name: display_name,
                            rel_path: path
                                .strip_prefix(root)
                                .unwrap_or(&path)
                                .to_string_lossy()
                                .to_string(),
                            is_dir: true,
                            tier: Tier::guess(&fname),
                            status: Status::Truncated,
                            update_state: UpdateState::Unchanged,
                            size_bytes: 0,
                            modified_unix: metadata.modified().map(unix_time_nanos).unwrap_or(0),
                            key_files: vec![],
                            compat: CompatInfo::default(),
                            repair_note: Some(
                                "Directory could not be scanned; see warnings.".into(),
                            ),
                            children: vec![],
                        });
                    }
                }
            } else {
                if KEY_FILE_NAMES.contains(&fname.as_str()) {
                    key_files.push(fname.clone());
                } else if fname.contains("schema") || fname.contains("manifest") {
                    // Not on the fixed key-file list, but its name signals
                    // exactly what an L4 presence check is looking for.
                    key_files.push(fname.clone());
                }
                if state.bytes.saturating_add(metadata.len()) > limits.max_total_bytes {
                    state.limit_hit = true;
                    state.warnings.push(ScanWarning {
                        kind: "byte-limit".into(),
                        path: path.display().to_string(),
                        message: "scan byte limit reached".into(),
                    });
                    break;
                }
                state.bytes = state.bytes.saturating_add(metadata.len());
                children.push(Node {
                    name: display_name,
                    rel_path: path
                        .strip_prefix(root)
                        .unwrap_or(&path)
                        .to_string_lossy()
                        .to_string(),
                    is_dir: false,
                    tier: Tier::Untagged,
                    status: if Tier::guess(&fname) == Tier::Untagged {
                        Status::Unclassified
                    } else {
                        Status::Ok
                    },
                    update_state: UpdateState::Unchanged,
                    size_bytes: metadata.len(),
                    modified_unix: metadata.modified().map(unix_time_nanos).unwrap_or(0),
                    key_files: vec![],
                    compat: CompatInfo::default(),
                    repair_note: None,
                    children: vec![],
                });
            }
        }
    }

    let tier = Tier::guess(&name);
    let compat = if depth < limits.max_depth && !state.limit_hit {
        read_compat_info(dir)
    } else {
        CompatInfo::default()
    };
    let truncated = depth >= limits.max_depth || state.limit_hit;
    let status = compute_status(tier, true, &key_files, children.len(), truncated);
    let repair_note = repair_note_for(tier, status);

    Ok(Node {
        name,
        rel_path: if rel_path == "." {
            String::new()
        } else {
            rel_path
        },
        is_dir: true,
        tier,
        status,
        update_state: UpdateState::Unchanged,
        size_bytes: 0,
        modified_unix,
        key_files,
        compat,
        repair_note,
        children,
    })
}

/// Flattens a tree into a fingerprint map keyed by relative path, for
/// diffing between scans.
fn fingerprint_map(node: &Node, out: &mut HashMap<String, Fingerprint>) {
    out.insert(
        node.rel_path.clone(),
        Fingerprint {
            size: node.size_bytes,
            modified: node.modified_unix,
        },
    );
    for c in &node.children {
        fingerprint_map(c, out);
    }
}

/// Applies rescan diffing in place: marks each node in `new_tree` as
/// New/Modified/Unchanged relative to `old_tree`, and appends synthetic
/// Removed leaf entries for paths present in `old_tree` but gone now.
pub fn diff_against(new_tree: &mut Node, old_tree: &Node) {
    let mut old_map = HashMap::new();
    fingerprint_map(old_tree, &mut old_map);
    mark_update_state(new_tree, &old_map);

    let mut new_map = HashMap::new();
    fingerprint_map(new_tree, &mut new_map);
    let removed: Vec<&String> = old_map
        .keys()
        .filter(|k| !new_map.contains_key(*k))
        .collect();
    if !removed.is_empty() {
        for path in removed {
            new_tree.children.push(Node {
                name: format!("(removed) {path}"),
                rel_path: path.clone(),
                is_dir: false,
                tier: Tier::Untagged,
                status: Status::MissingExpected,
                update_state: UpdateState::Removed,
                size_bytes: 0,
                modified_unix: 0,
                key_files: vec![],
                compat: CompatInfo::default(),
                repair_note: Some(
                    "Present in last scan, missing now — confirm intentional deletion.".into(),
                ),
                children: vec![],
            });
        }
    }
}

fn mark_update_state(node: &mut Node, old_map: &HashMap<String, Fingerprint>) {
    match old_map.get(&node.rel_path) {
        None => node.update_state = UpdateState::New,
        Some(fp) => {
            if fp.size != node.size_bytes || fp.modified != node.modified_unix {
                node.update_state = UpdateState::Modified;
            } else {
                node.update_state = UpdateState::Unchanged;
            }
        }
    }
    for c in &mut node.children {
        mark_update_state(c, old_map);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{thread::sleep, time::Duration};

    fn write(path: &Path, content: &str) {
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, content).unwrap();
    }

    fn find<'a>(node: &'a Node, rel_path: &str) -> Option<&'a Node> {
        if node.rel_path == rel_path {
            return Some(node);
        }
        node.children.iter().find_map(|c| find(c, rel_path))
    }

    #[test]
    fn rescan_diff_flags_new_modified_removed() {
        let dir = std::env::temp_dir().join(format!("al1scan_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        write(&dir.join("keep.txt"), "same");
        write(&dir.join("change.txt"), "before");
        write(&dir.join("gone.txt"), "bye");

        let before = scan_root_with_limits(&dir, ScanLimits::for_depth(8))
            .unwrap()
            .root;

        // Ensure mtimes differ from the first scan.
        sleep(Duration::from_millis(20));
        write(&dir.join("change.txt"), "after-longer-content");
        write(&dir.join("added.txt"), "new");
        fs::remove_file(dir.join("gone.txt")).unwrap();

        let mut after = scan_root_with_limits(&dir, ScanLimits::for_depth(8))
            .unwrap()
            .root;
        diff_against(&mut after, &before);

        assert_eq!(
            find(&after, "keep.txt").unwrap().update_state,
            UpdateState::Unchanged
        );
        assert_eq!(
            find(&after, "change.txt").unwrap().update_state,
            UpdateState::Modified
        );
        assert_eq!(
            find(&after, "added.txt").unwrap().update_state,
            UpdateState::New
        );
        assert_eq!(
            find(&after, "gone.txt").unwrap().update_state,
            UpdateState::Removed
        );

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn resource_limits_produce_partial_report() {
        let dir = std::env::temp_dir().join(format!("al1scan_limit_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        write(&dir.join("one.txt"), "1");
        write(&dir.join("two.txt"), "2");

        let mut limits = ScanLimits::for_depth(8);
        limits.max_entries = 1;
        let report = scan_root_with_limits(&dir, limits).unwrap();

        assert!(!report.complete);
        assert!(report
            .warnings
            .iter()
            .any(|warning| warning.kind == "entry-limit"));
        assert!(report.summary.warnings > 0);

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn summary_reports_counts_and_statuses() {
        let dir = std::env::temp_dir().join(format!("al1scan_summary_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        write(&dir.join("notes.txt"), "hello");

        let tree = scan_root_with_limits(&dir, ScanLimits::for_depth(8))
            .unwrap()
            .root;
        let summary = summarize(&tree);

        assert_eq!(summary.total_nodes, 2);
        assert_eq!(summary.directories, 1);
        assert_eq!(summary.files, 1);
        assert_eq!(summary.total_bytes, 5);
        assert_eq!(summary.status_counts.get("unclassified"), Some(&1));

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn env_files_are_never_scanned() {
        let dir = std::env::temp_dir().join(format!("al1scan_env_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        write(&dir.join(".env"), "SECRET=1");
        write(&dir.join("normal.txt"), "ok");

        let tree = scan_root_with_limits(&dir, ScanLimits::for_depth(8))
            .unwrap()
            .root;
        assert!(find(&tree, ".env").is_none());
        assert!(find(&tree, "normal.txt").is_some());

        let _ = fs::remove_dir_all(&dir);
    }
}
