mod authority;
mod scan;

use crossterm::{
    cursor::Show,
    event::{
        self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyModifiers, MouseButton,
        MouseEventKind,
    },
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Clear, List, ListItem, ListState, Paragraph, Wrap},
    Frame, Terminal,
};
use scan::{
    Node, ScanLimits, ScanReport, ScanReportSummary, ScanSummary, ScanWarning, Status, Tier,
    UpdateState, DEFAULT_MAX_DURATION_SECS, DEFAULT_MAX_ENTRIES, DEFAULT_MAX_TOTAL_BYTES,
};
use std::{
    env, fs, io, panic,
    path::{Component, Path, PathBuf},
    process::Command,
    time::{Duration, Instant},
};

const MAX_DEPTH: usize = 12;
const MAX_PROMOTION_EVIDENCE_BYTES: u64 = 256 * 1024;

#[derive(Debug, Clone, PartialEq, Eq)]
struct CliOptions {
    root: PathBuf,
    scope: Option<PathBuf>,
    dump: bool,
    summary: bool,
    authority: bool,
    resolve: Option<String>,
    impact: Option<String>,
    validate_promotion: Option<String>,
    evidence: Option<PathBuf>,
    max_depth: usize,
    max_entries: usize,
    max_seconds: u64,
    help: bool,
}

impl CliOptions {
    fn parse(args: &[String]) -> io::Result<Self> {
        let mut root: Option<PathBuf> = None;
        let mut scope = None;
        let mut dump = false;
        let mut summary = false;
        let mut authority = false;
        let mut resolve = None;
        let mut impact = None;
        let mut validate_promotion = None;
        let mut evidence = None;
        let mut max_depth = MAX_DEPTH;
        let mut max_entries = DEFAULT_MAX_ENTRIES;
        let mut max_seconds = DEFAULT_MAX_DURATION_SECS;
        let mut help = false;
        let mut index = 0;

        while index < args.len() {
            match args[index].as_str() {
                "--help" | "-h" => help = true,
                "--dump" => dump = true,
                "--summary" => summary = true,
                "--authority" => authority = true,
                "--resolve" => {
                    index += 1;
                    resolve = Some(Self::next_value(args, index, "--resolve")?);
                }
                "--impact" => {
                    index += 1;
                    impact = Some(Self::next_value(args, index, "--impact")?);
                }
                "--validate-promotion" => {
                    index += 1;
                    validate_promotion =
                        Some(Self::next_value(args, index, "--validate-promotion")?);
                }
                "--evidence" => {
                    index += 1;
                    evidence = Some(PathBuf::from(Self::next_value(args, index, "--evidence")?));
                }
                "--root" => {
                    index += 1;
                    root = Some(PathBuf::from(Self::next_value(args, index, "--root")?));
                }
                "--scope" => {
                    index += 1;
                    scope = Some(PathBuf::from(Self::next_value(args, index, "--scope")?));
                }
                "--max-depth" => {
                    index += 1;
                    let value = Self::next_value(args, index, "--max-depth")?;
                    max_depth = value.parse::<usize>().map_err(|_| {
                        io::Error::new(
                            io::ErrorKind::InvalidInput,
                            format!("--max-depth must be a positive integer: {value}"),
                        )
                    })?;
                    if max_depth == 0 || max_depth > 128 {
                        return Err(io::Error::new(
                            io::ErrorKind::InvalidInput,
                            "--max-depth must be between 1 and 128",
                        ));
                    }
                }
                "--max-entries" => {
                    index += 1;
                    let value = Self::next_value(args, index, "--max-entries")?;
                    max_entries = value.parse::<usize>().map_err(|_| {
                        io::Error::new(
                            io::ErrorKind::InvalidInput,
                            format!("--max-entries must be a positive integer: {value}"),
                        )
                    })?;
                    if max_entries == 0 || max_entries > 10_000_000 {
                        return Err(io::Error::new(
                            io::ErrorKind::InvalidInput,
                            "--max-entries must be between 1 and 10000000",
                        ));
                    }
                }
                "--max-seconds" => {
                    index += 1;
                    let value = Self::next_value(args, index, "--max-seconds")?;
                    max_seconds = value.parse::<u64>().map_err(|_| {
                        io::Error::new(
                            io::ErrorKind::InvalidInput,
                            format!("--max-seconds must be a positive integer: {value}"),
                        )
                    })?;
                    if max_seconds == 0 || max_seconds > 86_400 {
                        return Err(io::Error::new(
                            io::ErrorKind::InvalidInput,
                            "--max-seconds must be between 1 and 86400",
                        ));
                    }
                }
                value if value.starts_with('-') => {
                    return Err(io::Error::new(
                        io::ErrorKind::InvalidInput,
                        format!("unknown option: {value}"),
                    ));
                }
                value => {
                    if root.replace(PathBuf::from(value)).is_some() {
                        return Err(io::Error::new(
                            io::ErrorKind::InvalidInput,
                            "only one scan root may be provided",
                        ));
                    }
                }
            }
            index += 1;
        }

        if validate_promotion.is_some() != evidence.is_some() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "--validate-promotion and --evidence must be provided together",
            ));
        }

        if let Some(scope) = &scope {
            if scope.is_absolute()
                || scope
                    .components()
                    .any(|component| matches!(component, Component::ParentDir | Component::RootDir))
            {
                return Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    "--scope must be a relative path inside the scan root",
                ));
            }
        }

        Ok(Self {
            root: root.unwrap_or_else(|| PathBuf::from(".")),
            scope,
            dump,
            summary,
            authority,
            resolve,
            impact,
            validate_promotion,
            evidence,
            max_depth,
            max_entries,
            max_seconds,
            help,
        })
    }

    fn next_value(args: &[String], index: usize, option: &str) -> io::Result<String> {
        args.get(index).cloned().ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidInput,
                format!("{option} requires a value"),
            )
        })
    }

    fn scan_limits(&self) -> ScanLimits {
        let mut limits = ScanLimits::for_depth(self.max_depth);
        limits.max_entries = self.max_entries;
        limits.max_total_bytes = DEFAULT_MAX_TOTAL_BYTES;
        limits.max_duration = Duration::from_secs(self.max_seconds);
        limits
    }

    fn print_help() {
        println!(
            "al1scan [OPTIONS] [ROOT]\n\n\
             Read-only AL1/LPG monitor and repair station.\n\n\
             Options:\n  \
                 --dump                 emit the scan tree as JSON\n  \
                 --summary              emit scan counts and status summary JSON\n  \
                 --authority            emit observed LPG-L1 authority candidates JSON\n  \
                 --resolve QUERY        resolve an ID, alias, or path in the observed index\n  \
                 --impact ID            show transitive dependents from observed dependencies\n  \
                 --validate-promotion ID check promotion evidence read-only\n  \
                 --evidence PATH         JSON promotion evidence file, relative to root\n  \
                 --root PATH            set the LPG/program root\n  \
                 --scope PATH           scan a relative subtree only\n  \
                 --max-depth N          set the scan depth (1-128)\n  \
                 --max-entries N        set the maximum scanned entries\n  \
                 --max-seconds N        set the maximum scan duration\n  \
                 -h, --help             show this help"
        );
    }
}

/// A mutating action recognized as safe by policy: additive-only, never
/// overwrites or deletes existing content, always reversible by hand
/// (delete the file it created), and never applied without an explicit
/// confirmation step.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum RepairAction {
    Gitkeep,
    ReadmeStub,
    SchemaStub,
}

impl RepairAction {
    /// Chooses a safe repair for a node, if one is recognized. Returns
    /// `None` for anything this tool won't touch automatically.
    fn for_node(node: &Node) -> Option<RepairAction> {
        match (node.tier, node.status) {
            (_, Status::Empty) if node.is_dir => Some(RepairAction::Gitkeep),
            (Tier::L5, Status::MissingExpected) => Some(RepairAction::ReadmeStub),
            (Tier::L4, Status::MissingExpected) => Some(RepairAction::SchemaStub),
            _ => None,
        }
    }

    fn menu_label(&self) -> &'static str {
        match self {
            RepairAction::Gitkeep => "Apply repair: add .gitkeep",
            RepairAction::ReadmeStub => "Apply repair: add README.md stub",
            RepairAction::SchemaStub => "Apply repair: add schema stub",
        }
    }

    /// Exact description of what will be written, shown in the confirm
    /// popup before anything touches disk.
    fn describe(&self, abs_path: &Path) -> String {
        match self {
            RepairAction::Gitkeep => {
                format!(
                    "Create empty file:\n{}",
                    abs_path.join(".gitkeep").display()
                )
            }
            RepairAction::ReadmeStub => {
                format!(
                    "Create stub file:\n{}",
                    abs_path.join("README.md").display()
                )
            }
            RepairAction::SchemaStub => {
                let name = abs_path
                    .file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_else(|| "component".to_string());
                format!(
                    "Create valid placeholder schema:\n{}",
                    abs_path.join(format!("{name}.schema.json")).display()
                )
            }
        }
    }

    /// Performs the write. Uses `create_new` so it can never clobber an
    /// existing file, even if called twice.
    fn apply(&self, abs_path: &Path, node_name: &str) -> io::Result<String> {
        use std::fs::OpenOptions;
        use std::io::Write;

        let (target, contents): (PathBuf, String) = match self {
            RepairAction::Gitkeep => (abs_path.join(".gitkeep"), String::new()),
            RepairAction::ReadmeStub => (
                abs_path.join("README.md"),
                format!("# {node_name}\n\nTODO: describe this component.\n"),
            ),
            RepairAction::SchemaStub => {
                let target = abs_path.join(format!("{node_name}.schema.json"));
                let schema = serde_json::json!({
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": format!("TODO.{node_name}"),
                    "title": node_name,
                    "type": "object",
                    "additionalProperties": true
                });
                let contents = format!(
                    "{}\n",
                    serde_json::to_string_pretty(&schema)
                        .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))?
                );
                (target, contents)
            }
        };

        let mut f = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&target)?;
        f.write_all(contents.as_bytes())?;
        Ok(format!("Created {}", target.display()))
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum MenuAction {
    BrowseLocal,
    OpenReport,
    CopyNode,
    CopyTree,
    ApplyRepair,
    Close,
}

struct ContextMenu {
    anchor: (u16, u16),
    node_path: Vec<usize>,
    items: Vec<(String, MenuAction)>,
    selected: usize,
}

struct ConfirmDialog {
    message: String,
    node_path: Vec<usize>,
    action: RepairAction,
}

/// Opens `path` in the OS's file browser/manager, selecting it if possible.
/// Never touches file content — this only shells out to the OS shell.
fn reveal_in_file_manager(path: &Path) -> io::Result<()> {
    if cfg!(target_os = "windows") {
        Command::new("explorer")
            .arg(format!("/select,{}", path.display()))
            .spawn()?;
    } else if cfg!(target_os = "macos") {
        Command::new("open").arg("-R").arg(path).spawn()?;
    } else {
        let target = if path.is_dir() {
            path.to_path_buf()
        } else {
            path.parent()
                .map(Path::to_path_buf)
                .unwrap_or_else(|| path.to_path_buf())
        };
        Command::new("xdg-open").arg(target).spawn()?;
    }
    Ok(())
}

/// Opens `path` with whatever the OS considers the default handler for it.
fn open_with_default_app(path: &Path) -> io::Result<()> {
    if cfg!(target_os = "windows") {
        Command::new("explorer.exe").arg(path).spawn()?;
    } else if cfg!(target_os = "macos") {
        Command::new("open").arg(path).spawn()?;
    } else {
        Command::new("xdg-open").arg(path).spawn()?;
    }
    Ok(())
}

fn ensure_safe_directory(root: &Path, dir: &Path) -> io::Result<()> {
    let canonical_root = root.canonicalize()?;
    let parent = dir.parent().ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("write target has no parent: {}", dir.display()),
        )
    })?;
    let canonical_parent = parent.canonicalize()?;
    if !canonical_parent.starts_with(&canonical_root) {
        return Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            format!("write target is outside the scan root: {}", dir.display()),
        ));
    }
    if let Ok(metadata) = fs::symlink_metadata(dir) {
        if scan::is_link_like(&metadata) {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                format!("write target is a symlink or junction: {}", dir.display()),
            ));
        }
        let canonical_dir = dir.canonicalize()?;
        if !canonical_dir.starts_with(&canonical_root) {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                format!(
                    "write target resolves outside the scan root: {}",
                    dir.display()
                ),
            ));
        }
    }
    Ok(())
}

fn read_promotion_evidence(
    root: &Path,
    relative_path: &Path,
) -> io::Result<authority::PromotionEvidence> {
    if relative_path.is_absolute()
        || relative_path
            .components()
            .any(|component| matches!(component, Component::ParentDir | Component::RootDir))
    {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "promotion evidence must be a relative path inside the scan root",
        ));
    }
    let path = root.join(relative_path);
    let parent = path.parent().ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::InvalidInput,
            "promotion evidence has no parent directory",
        )
    })?;
    ensure_safe_directory(root, parent)?;
    let metadata = fs::metadata(&path)?;
    if !metadata.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("promotion evidence is not a file: {}", path.display()),
        ));
    }
    if metadata.len() > MAX_PROMOTION_EVIDENCE_BYTES {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "promotion evidence exceeds the 256 KiB read limit",
        ));
    }
    let text = fs::read_to_string(&path)?;
    serde_json::from_str(&text).map_err(|error| {
        io::Error::new(
            io::ErrorKind::InvalidData,
            format!("invalid promotion evidence JSON: {error}"),
        )
    })
}

/// Writes a small human-readable Markdown report for a node (and a summary
/// of its direct children) into `<root>/.al1scan_reports/`, returning the
/// path written. This only ever creates new, uniquely-named files.
fn write_report(node: &Node, root: &Path) -> io::Result<PathBuf> {
    let reports_dir = root.join(".al1scan_reports");
    ensure_safe_directory(root, &reports_dir)?;
    fs::create_dir_all(&reports_dir)?;

    let safe_name: String = node
        .name
        .chars()
        .map(|c| {
            if c.is_alphanumeric() || c == '.' || c == '-' {
                c
            } else {
                '_'
            }
        })
        .collect();
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::SystemTime::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let path = reports_dir.join(format!("{safe_name}_{ts}.md"));

    let mut out = String::new();
    out.push_str(&format!("# AL1 Readout Report — {}\n\n", node.name));
    out.push_str(&format!(
        "- Path: `{}`\n",
        if node.rel_path.is_empty() {
            "."
        } else {
            &node.rel_path
        }
    ));
    out.push_str(&format!("- Tier (guess): {}\n", node.tier.label()));
    out.push_str(&format!("- Presence status: {}\n", node.status.label()));
    out.push_str(&format!("- Update status: {}\n", node.update_state.label()));
    if let Some(mf) = &node.compat.manifest_file {
        out.push_str(&format!("- Compat manifest: {mf}\n"));
        if let Some(n) = &node.compat.package_name {
            out.push_str(&format!("  - name: {n}\n"));
        }
        if let Some(v) = &node.compat.package_version {
            out.push_str(&format!("  - version: {v}\n"));
        }
    }
    if !node.key_files.is_empty() {
        out.push_str("- Key files:\n");
        for k in &node.key_files {
            out.push_str(&format!("  - {k}\n"));
        }
    }
    if let Some(note) = &node.repair_note {
        out.push_str(&format!("\n**Repair suggestion:** {note}\n"));
    }
    if node.is_dir && !node.children.is_empty() {
        out.push_str(&format!("\n## Children ({})\n\n", node.children.len()));
        out.push_str("| name | tier | status | update |\n|---|---|---|---|\n");
        for c in &node.children {
            out.push_str(&format!(
                "| {} | {} | {} | {} |\n",
                c.name,
                c.tier.label(),
                c.status.label(),
                c.update_state.label()
            ));
        }
    }

    use std::fs::OpenOptions;
    use std::io::Write;

    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)?;
    file.write_all(out.as_bytes())?;
    Ok(path)
}

/// One flattened, indented row derived from the tree for list rendering.
/// Kept separate from `Node` so the tree itself never needs interior
/// mutability just to be displayed.
struct FlatRow {
    depth: usize,
    node_path: Vec<usize>, // indices from root to this node, for lookup
}

struct App {
    root_path: PathBuf,
    limits: ScanLimits,
    tree: Node,
    summary: ScanSummary,
    warnings: Vec<ScanWarning>,
    complete: bool,
    prev_tree: Option<Node>,
    flat: Vec<FlatRow>,
    list_state: ListState,
    expanded: std::collections::HashSet<String>, // rel_path of expanded dirs
    filter: String,
    filtering: bool,
    status_msg: Option<(String, Instant)>,
    last_scan: Instant,
    tree_area: Rect,
    frame_size: Rect,
    context_menu: Option<ContextMenu>,
    confirm: Option<ConfirmDialog>,
}

impl App {
    fn new(root_path: PathBuf, limits: ScanLimits) -> io::Result<Self> {
        let report = scan::scan_root_with_limits(&root_path, limits.clone())?;
        let tree = report.root;
        let summary = report.summary;
        let warnings = report.warnings;
        let complete = report.complete;
        let mut expanded = std::collections::HashSet::new();
        expanded.insert(tree.rel_path.clone());
        let mut app = Self {
            root_path,
            limits,
            tree,
            summary,
            warnings,
            complete,
            prev_tree: None,
            flat: Vec::new(),
            list_state: ListState::default(),
            expanded,
            filter: String::new(),
            filtering: false,
            status_msg: None,
            last_scan: Instant::now(),
            tree_area: Rect::default(),
            frame_size: Rect::default(),
            context_menu: None,
            confirm: None,
        };
        app.rebuild_flat();
        app.list_state.select(Some(0));
        Ok(app)
    }

    fn flash(&mut self, msg: impl Into<String>) {
        self.status_msg = Some((msg.into(), Instant::now()));
    }

    fn current_status(&mut self) -> Option<String> {
        if let Some((msg, at)) = &self.status_msg {
            if at.elapsed() < Duration::from_secs(3) {
                return Some(msg.clone());
            }
            self.status_msg = None;
        }
        None
    }

    fn node_at(&self, path: &[usize]) -> &Node {
        let mut n = &self.tree;
        for &i in path {
            n = &n.children[i];
        }
        n
    }

    fn rebuild_flat(&mut self) {
        self.flat.clear();
        let query = self.filter.to_lowercase();
        let root_path = vec![];
        Self::walk(
            &self.tree,
            0,
            root_path,
            &self.expanded,
            &query,
            &mut self.flat,
        );
        if self.flat.is_empty() {
            self.list_state.select(None);
        } else {
            let cur = self
                .list_state
                .selected()
                .unwrap_or(0)
                .min(self.flat.len() - 1);
            self.list_state.select(Some(cur));
        }
    }

    fn walk(
        node: &Node,
        depth: usize,
        path: Vec<usize>,
        expanded: &std::collections::HashSet<String>,
        query: &str,
        out: &mut Vec<FlatRow>,
    ) {
        let matches = query.is_empty()
            || node.name.to_lowercase().contains(query)
            || node.tier.label().to_lowercase() == query;

        // Include this row if it matches, or if any descendant matches
        // (so filtering doesn't hide the path to a match).
        let child_matches = node.children.iter().any(|c| subtree_has_match(c, query));

        if matches || child_matches || query.is_empty() {
            out.push(FlatRow {
                depth,
                node_path: path.clone(),
            });
            if node.is_dir && (expanded.contains(&node.rel_path) || !query.is_empty()) {
                for (i, c) in node.children.iter().enumerate() {
                    let mut p = path.clone();
                    p.push(i);
                    Self::walk(c, depth + 1, p, expanded, query, out);
                }
            }
        }
    }

    fn selected_path(&self) -> Option<&[usize]> {
        self.list_state
            .selected()
            .and_then(|i| self.flat.get(i))
            .map(|r| r.node_path.as_slice())
    }

    fn toggle_expand(&mut self) {
        if let Some(path) = self.selected_path() {
            let path = path.to_vec();
            let node = self.node_at(&path);
            if node.is_dir {
                let rel = node.rel_path.clone();
                if self.expanded.contains(&rel) {
                    self.expanded.remove(&rel);
                } else {
                    self.expanded.insert(rel);
                }
                self.rebuild_flat();
            }
        }
    }

    fn rescan(&mut self) -> io::Result<()> {
        let report = scan::scan_root_with_limits(&self.root_path, self.limits.clone())?;
        if !report.complete {
            self.summary = report.summary;
            self.warnings = report.warnings;
            self.complete = false;
            self.last_scan = Instant::now();
            self.flash("Partial scan: previous baseline retained");
            return Ok(());
        }
        let mut new_tree = report.root;
        scan::diff_against(&mut new_tree, &self.tree);
        self.summary = report.summary;
        self.warnings = report.warnings;
        self.complete = true;
        self.prev_tree = Some(std::mem::replace(&mut self.tree, new_tree));
        self.last_scan = Instant::now();
        self.rebuild_flat();
        self.flash("Rescanned");
        Ok(())
    }

    fn abs_path_for(&self, node_path: &[usize]) -> PathBuf {
        let node = self.node_at(node_path);
        if node.rel_path.is_empty() {
            self.root_path.clone()
        } else {
            self.root_path.join(&node.rel_path)
        }
    }

    /// Maps a terminal row (as reported by a mouse event) to a flat-tree
    /// index, accounting for the list's current scroll offset and the
    /// tree pane's border. Returns `None` if the row is outside the pane.
    fn row_at(&self, screen_row: u16) -> Option<usize> {
        let inner_top = self.tree_area.y + 1; // border
        let inner_bottom = self.tree_area.y + self.tree_area.height.saturating_sub(1);
        if screen_row < inner_top || screen_row >= inner_bottom {
            return None;
        }
        let visible_row = (screen_row - inner_top) as usize;
        let idx = self.list_state.offset() + visible_row;
        if idx < self.flat.len() {
            Some(idx)
        } else {
            None
        }
    }

    fn open_context_menu(&mut self, node_path: Vec<usize>, anchor: (u16, u16)) {
        let node = self.node_at(&node_path).clone();
        let mut items = vec![
            ("Browse local".to_string(), MenuAction::BrowseLocal),
            ("Open report".to_string(), MenuAction::OpenReport),
            ("Copy node (JSON)".to_string(), MenuAction::CopyNode),
            ("Copy whole tree (JSON)".to_string(), MenuAction::CopyTree),
        ];
        if let Some(repair) = RepairAction::for_node(&node) {
            items.push((repair.menu_label().to_string(), MenuAction::ApplyRepair));
        }
        items.push(("Close menu".to_string(), MenuAction::Close));

        self.context_menu = Some(ContextMenu {
            anchor,
            node_path,
            items,
            selected: 0,
        });
    }

    fn run_menu_action(&mut self, action: MenuAction, node_path: Vec<usize>) {
        match action {
            MenuAction::BrowseLocal => {
                let abs = self.abs_path_for(&node_path);
                match reveal_in_file_manager(&abs) {
                    Ok(_) => self.flash(format!("Opened file manager at {}", abs.display())),
                    Err(e) => self.flash(format!("Couldn't open file manager: {e}")),
                }
            }
            MenuAction::OpenReport => {
                let node = self.node_at(&node_path).clone();
                match write_report(&node, &self.root_path) {
                    Ok(path) => match open_with_default_app(&path) {
                        Ok(_) => self.flash(format!("Report opened: {}", path.display())),
                        Err(e) => self.flash(format!("Report written but couldn't open: {e}")),
                    },
                    Err(e) => self.flash(format!("Couldn't write report: {e}")),
                }
            }
            MenuAction::CopyNode => {
                let node = self.node_at(&node_path).clone();
                match serde_json::to_string_pretty(&node) {
                    Ok(json) => self.copy_text(json, "Copied selected node"),
                    Err(e) => self.flash(format!("Copy failed: {e}")),
                }
            }
            MenuAction::CopyTree => self.copy_tree(),
            MenuAction::ApplyRepair => {
                let node = self.node_at(&node_path).clone();
                if let Some(repair) = RepairAction::for_node(&node) {
                    let abs = self.abs_path_for(&node_path);
                    let message = format!(
                        "{}\n\nThis only creates a new file — it never overwrites or \
                         deletes anything. Proceed?",
                        repair.describe(&abs)
                    );
                    self.confirm = Some(ConfirmDialog {
                        message,
                        node_path,
                        action: repair,
                    });
                } else {
                    self.flash("No automated repair available for this node");
                }
            }
            MenuAction::Close => {}
        }
        self.context_menu = None;
    }

    fn confirm_yes(&mut self) {
        if let Some(dialog) = self.confirm.take() {
            let abs = self.abs_path_for(&dialog.node_path);
            let node_name = self.node_at(&dialog.node_path).name.clone();
            if let Err(error) = ensure_safe_directory(&self.root_path, &abs) {
                self.flash(format!("Repair blocked: {error}"));
                return;
            }
            match dialog.action.apply(&abs, &node_name) {
                Ok(msg) => {
                    self.flash(msg);
                    if let Err(error) = self.rescan() {
                        self.flash(format!("Repair created, but rescan failed: {error}"));
                    }
                }
                Err(e) => self.flash(format!("Repair failed: {e}")),
            }
        }
    }

    fn confirm_no(&mut self) {
        self.confirm = None;
        self.flash("Cancelled");
    }
    fn copy_selected(&mut self) {
        if let Some(path) = self.selected_path() {
            let node = self.node_at(path);
            match serde_json::to_string_pretty(node) {
                Ok(json) => self.copy_text(json, "Copied selected node"),
                Err(e) => self.flash(format!("Copy failed: {e}")),
            }
        } else {
            self.flash("Nothing selected");
        }
    }

    fn copy_tree(&mut self) {
        let report = ScanReport {
            root: self.tree.clone(),
            summary: self.summary.clone(),
            warnings: self.warnings.clone(),
            complete: self.complete,
        };
        match serde_json::to_string_pretty(&report) {
            Ok(json) => self.copy_text(json, "Copied scan report"),
            Err(e) => self.flash(format!("Copy failed: {e}")),
        }
    }

    fn copy_text(&mut self, text: String, ok_msg: &str) {
        match arboard::Clipboard::new() {
            Ok(mut cb) => match cb.set_text(text) {
                Ok(_) => self.flash(ok_msg.to_string()),
                Err(e) => self.flash(format!("Clipboard error: {e}")),
            },
            Err(e) => self.flash(format!("No clipboard: {e}")),
        }
    }
}

fn subtree_has_match(node: &Node, query: &str) -> bool {
    if query.is_empty() {
        return true;
    }
    if node.name.to_lowercase().contains(query) || node.tier.label().to_lowercase() == query {
        return true;
    }
    node.children.iter().any(|c| subtree_has_match(c, query))
}

fn tier_color(t: Tier) -> Color {
    match t {
        Tier::L1 => Color::Red,
        Tier::L2 => Color::Yellow,
        Tier::L3 => Color::Green,
        Tier::L4 => Color::Magenta,
        Tier::L5 => Color::Cyan,
        Tier::L6 => Color::Blue,
        Tier::Untagged => Color::DarkGray,
    }
}

fn status_color(s: Status) -> Color {
    match s {
        Status::Ok => Color::Green,
        Status::Empty => Color::DarkGray,
        Status::Truncated => Color::Magenta,
        Status::MissingExpected => Color::Yellow,
        Status::Unclassified => Color::DarkGray,
        Status::Unmanaged => Color::Red,
    }
}

fn update_marker(u: UpdateState) -> (&'static str, Color) {
    match u {
        UpdateState::Unchanged => ("", Color::DarkGray),
        UpdateState::New => ("[NEW]", Color::Green),
        UpdateState::Modified => ("[MOD]", Color::Yellow),
        UpdateState::Removed => ("[DEL]", Color::Red),
    }
}

fn human_size(bytes: u64) -> String {
    const KB: f64 = 1024.0;
    const MB: f64 = KB * 1024.0;
    const GB: f64 = MB * 1024.0;
    let b = bytes as f64;
    if b >= GB {
        format!("{:.2} GB", b / GB)
    } else if b >= MB {
        format!("{:.2} MB", b / MB)
    } else if b >= KB {
        format!("{:.1} KB", b / KB)
    } else {
        format!("{bytes} B")
    }
}

fn main() -> io::Result<()> {
    let args: Vec<String> = env::args().skip(1).collect();
    let options = CliOptions::parse(&args)?;
    if options.help {
        CliOptions::print_help();
        return Ok(());
    }

    let requested_root = options.root.clone();
    let root_path = requested_root.canonicalize().map_err(|error| {
        io::Error::new(
            io::ErrorKind::NotFound,
            format!(
                "unable to resolve scan root {}: {error}",
                requested_root.display()
            ),
        )
    })?;
    if !root_path.is_dir() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("scan root is not a directory: {}", root_path.display()),
        ));
    }

    let scan_root = if let Some(scope) = &options.scope {
        let requested_scope = root_path.join(scope);
        let resolved_scope = requested_scope.canonicalize().map_err(|error| {
            io::Error::new(
                io::ErrorKind::NotFound,
                format!(
                    "unable to resolve scan scope {}: {error}",
                    requested_scope.display()
                ),
            )
        })?;
        if !resolved_scope.starts_with(&root_path) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "scan scope resolved outside the program root",
            ));
        }
        if !resolved_scope.is_dir() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                format!(
                    "scan scope is not a directory: {}",
                    resolved_scope.display()
                ),
            ));
        }
        resolved_scope
    } else {
        root_path
    };

    if let Some(changed_id) = &options.impact {
        let report = scan::scan_root_with_limits(&scan_root, options.scan_limits())?;
        let index = authority::build_candidates("lpg-l1", &report.root, report.complete);
        let graph = authority::DependencyGraph::from_index(&index);
        println!(
            "{}",
            serde_json::to_string_pretty(&graph.impacted_by(changed_id))?
        );
        return Ok(());
    }

    if let Some(component_id) = &options.validate_promotion {
        let report = scan::scan_root_with_limits(&scan_root, options.scan_limits())?;
        let index = authority::build_candidates("lpg-l1", &report.root, report.complete);
        let evidence_path = options.evidence.as_ref().expect("validated by CLI parser");
        match index.resolve(component_id) {
            authority::Resolution::Resolved { entry } => {
                let evidence = read_promotion_evidence(&scan_root, evidence_path)?;
                let outcome = authority::promote_to_approved(&entry, &evidence);
                println!("{}", serde_json::to_string_pretty(&outcome)?);
            }
            other => println!("{}", serde_json::to_string_pretty(&other)?),
        }
        return Ok(());
    }

    if let Some(query) = &options.resolve {
        let report = scan::scan_root_with_limits(&scan_root, options.scan_limits())?;
        let index = authority::build_candidates("lpg-l1", &report.root, report.complete);
        println!("{}", serde_json::to_string_pretty(&index.resolve(query))?);
        return Ok(());
    }

    if options.authority {
        let report = scan::scan_root_with_limits(&scan_root, options.scan_limits())?;
        let index = authority::build_candidates("lpg-l1", &report.root, report.complete);
        println!("{}", serde_json::to_string_pretty(&index)?);
        return Ok(());
    }

    if options.summary {
        let report = scan::scan_root_with_limits(&scan_root, options.scan_limits())?;
        let output = ScanReportSummary {
            summary: report.summary,
            warnings: report.warnings,
            complete: report.complete,
        };
        println!("{}", serde_json::to_string_pretty(&output)?);
        return Ok(());
    }

    if options.dump {
        let report = scan::scan_root_with_limits(&scan_root, options.scan_limits())?;
        println!("{}", serde_json::to_string_pretty(&report)?);
        return Ok(());
    }

    let default_hook = panic::take_hook();
    panic::set_hook(Box::new(move |info| {
        let _ = disable_raw_mode();
        let _ = execute!(io::stdout(), DisableMouseCapture, LeaveAlternateScreen);
        default_hook(info);
    }));

    let res = (|| -> io::Result<()> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
        let backend = CrosstermBackend::new(stdout);
        let mut terminal = Terminal::new(backend)?;
        let mut app = App::new(scan_root, options.scan_limits())?;
        run_main_loop(&mut terminal, &mut app)
    })();

    let _ = disable_raw_mode();
    let _ = execute!(
        io::stdout(),
        DisableMouseCapture,
        LeaveAlternateScreen,
        Show
    );

    if let Err(err) = res {
        eprintln!("AL1 Readout Fault: {err:?}");
        return Err(err);
    }
    Ok(())
}

fn run_main_loop<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
) -> io::Result<()> {
    loop {
        terminal.draw(|f| draw_ui(f, app))?;

        if event::poll(Duration::from_millis(150))? {
            match event::read()? {
                Event::Mouse(mouse) => {
                    if app.confirm.is_some() {
                        continue;
                    }
                    match mouse.kind {
                        MouseEventKind::Down(MouseButton::Right) => {
                            if app.context_menu.is_some() {
                                app.context_menu = None;
                            } else if let Some(idx) = app.row_at(mouse.row) {
                                app.list_state.select(Some(idx));
                                let node_path = app.flat[idx].node_path.clone();
                                app.open_context_menu(node_path, (mouse.column, mouse.row));
                            }
                        }
                        MouseEventKind::Down(MouseButton::Left) => {
                            if let Some(menu) = &app.context_menu {
                                // Click inside the menu activates that item;
                                // click elsewhere closes it.
                                let menu_area = menu_rect(menu, app.frame_size);
                                if mouse.row > menu_area.y
                                    && mouse.row < menu_area.y + menu_area.height.saturating_sub(1)
                                    && mouse.column >= menu_area.x
                                    && mouse.column < menu_area.x + menu_area.width
                                {
                                    let item_idx = (mouse.row - menu_area.y - 1) as usize;
                                    if let Some((_, action)) = menu.items.get(item_idx).cloned() {
                                        let node_path = menu.node_path.clone();
                                        app.run_menu_action(action, node_path);
                                    }
                                } else {
                                    app.context_menu = None;
                                }
                            } else if let Some(idx) = app.row_at(mouse.row) {
                                app.list_state.select(Some(idx));
                            }
                        }
                        _ => {}
                    }
                }
                Event::Key(key) => {
                    if key.kind != event::KeyEventKind::Press {
                        continue;
                    }

                    if let Some(_dialog) = &app.confirm {
                        match key.code {
                            KeyCode::Char('y') | KeyCode::Char('Y') | KeyCode::Enter => {
                                app.confirm_yes();
                            }
                            KeyCode::Char('n') | KeyCode::Char('N') | KeyCode::Esc => {
                                app.confirm_no();
                            }
                            _ => {}
                        }
                        continue;
                    }

                    if let Some(menu) = &mut app.context_menu {
                        match key.code {
                            KeyCode::Down | KeyCode::Char('j') => {
                                menu.selected = (menu.selected + 1).min(menu.items.len() - 1);
                            }
                            KeyCode::Up | KeyCode::Char('k') => {
                                menu.selected = menu.selected.saturating_sub(1);
                            }
                            KeyCode::Enter => {
                                let action = menu.items[menu.selected].1;
                                let node_path = menu.node_path.clone();
                                app.run_menu_action(action, node_path);
                            }
                            KeyCode::Esc => app.context_menu = None,
                            _ => {}
                        }
                        continue;
                    }

                    if app.filtering {
                        match key.code {
                            KeyCode::Enter | KeyCode::Esc => {
                                app.filtering = false;
                                app.rebuild_flat();
                            }
                            KeyCode::Backspace => {
                                app.filter.pop();
                                app.rebuild_flat();
                            }
                            KeyCode::Char(c) => {
                                app.filter.push(c);
                                app.rebuild_flat();
                            }
                            _ => {}
                        }
                        continue;
                    }

                    match key.code {
                        KeyCode::Char('q') => break,
                        KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                            break
                        }
                        KeyCode::Char('/') => app.filtering = true,
                        KeyCode::Esc => {
                            if !app.filter.is_empty() {
                                app.filter.clear();
                                app.rebuild_flat();
                            }
                        }
                        KeyCode::Down | KeyCode::Char('j') => {
                            let i = app.list_state.selected().unwrap_or(0);
                            if i + 1 < app.flat.len() {
                                app.list_state.select(Some(i + 1));
                            }
                        }
                        KeyCode::Up | KeyCode::Char('k') => {
                            let i = app.list_state.selected().unwrap_or(0);
                            app.list_state.select(Some(i.saturating_sub(1)));
                        }
                        KeyCode::Enter | KeyCode::Char(' ') => app.toggle_expand(),
                        KeyCode::Char('r') => {
                            if let Err(e) = app.rescan() {
                                app.flash(format!("Rescan failed: {e}"));
                            }
                        }
                        KeyCode::Char('y') => app.copy_selected(),
                        KeyCode::Char('Y') => app.copy_tree(),
                        KeyCode::Char('m') => {
                            if let Some(idx) = app.list_state.selected() {
                                let node_path = app.flat[idx].node_path.clone();
                                app.open_context_menu(
                                    node_path,
                                    (app.tree_area.x + 2, app.tree_area.y + 2),
                                );
                            }
                        }
                        _ => {}
                    }
                }
                _ => {}
            }
        }
    }
    Ok(())
}

fn draw_ui(f: &mut Frame, app: &mut App) {
    app.frame_size = f.size();
    let root = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(10),
            Constraint::Length(1),
        ])
        .split(f.size());

    draw_header(f, root[0], app);

    let body = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(45), Constraint::Percentage(55)])
        .split(root[1]);

    draw_tree(f, body[0], app);
    draw_detail(f, body[1], app);
    draw_status_bar(f, root[2], app);

    if let Some(menu) = &app.context_menu {
        draw_context_menu(f, menu, app.frame_size);
    }
    if let Some(dialog) = &app.confirm {
        draw_confirm(f, dialog, app.frame_size);
    }
}

/// Computes the popup rect for a context menu, anchored near the click
/// point but clamped so it never renders off-screen.
fn menu_rect(menu: &ContextMenu, bounds: Rect) -> Rect {
    let width = menu
        .items
        .iter()
        .map(|(label, _)| label.len() as u16)
        .max()
        .unwrap_or(10)
        + 4;
    let height = menu.items.len() as u16 + 2;

    let max_x = bounds.x + bounds.width.saturating_sub(width);
    let max_y = bounds.y + bounds.height.saturating_sub(height);
    let x = menu.anchor.0.min(max_x.max(bounds.x));
    let y = menu.anchor.1.min(max_y.max(bounds.y));

    Rect {
        x,
        y,
        width: width.min(bounds.width),
        height: height.min(bounds.height),
    }
}

fn draw_context_menu(f: &mut Frame, menu: &ContextMenu, bounds: Rect) {
    let area = menu_rect(menu, bounds);
    f.render_widget(Clear, area);

    let items: Vec<ListItem> = menu
        .items
        .iter()
        .enumerate()
        .map(|(i, (label, _))| {
            let style = if i == menu.selected {
                Style::default()
                    .bg(Color::DarkGray)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default()
            };
            ListItem::new(label.clone()).style(style)
        })
        .collect();

    let list = List::new(items).block(
        Block::default()
            .borders(Borders::ALL)
            .title(" Actions ")
            .border_style(Style::default().fg(Color::Cyan)),
    );
    f.render_widget(list, area);
}

fn draw_confirm(f: &mut Frame, dialog: &ConfirmDialog, bounds: Rect) {
    let width = bounds
        .width
        .saturating_sub(bounds.width / 4)
        .max(40)
        .min(bounds.width);
    let height = 9u16.min(bounds.height);
    let x = bounds.x + (bounds.width.saturating_sub(width)) / 2;
    let y = bounds.y + (bounds.height.saturating_sub(height)) / 2;
    let area = Rect {
        x,
        y,
        width,
        height,
    };

    f.render_widget(Clear, area);
    let mut lines: Vec<Line> = dialog.message.lines().map(Line::from).collect();
    lines.push(Line::from(""));
    lines.push(Line::from(vec![
        Span::styled(
            "[Y]",
            Style::default()
                .fg(Color::Green)
                .add_modifier(Modifier::BOLD),
        ),
        Span::raw("es    "),
        Span::styled(
            "[N]",
            Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
        ),
        Span::raw("o"),
    ]));

    let p = Paragraph::new(lines).wrap(Wrap { trim: false }).block(
        Block::default()
            .borders(Borders::ALL)
            .title(" Confirm — this will write to disk ")
            .border_style(Style::default().fg(Color::Yellow)),
    );
    f.render_widget(p, area);
}

fn draw_header(f: &mut Frame, area: Rect, app: &App) {
    let title = format!(
        " AL1 Readout — {} — {} nodes ",
        app.root_path.display(),
        app.tree.descendant_count()
    );
    let elapsed = app.last_scan.elapsed().as_secs();
    let text = Line::from(vec![Span::raw(format!(
        "last scan {}s ago{} | {}{}",
        elapsed,
        if app.prev_tree.is_some() {
            " (diffed)"
        } else {
            ""
        },
        app.summary.short_line(),
        if app.complete { "" } else { " | PARTIAL" }
    ))]);
    let p = Paragraph::new(text).block(Block::default().borders(Borders::ALL).title(title));
    f.render_widget(p, area);
}

fn draw_tree(f: &mut Frame, area: Rect, app: &mut App) {
    app.tree_area = area;
    let title = if app.filtering {
        format!(" Tree — filter: {}_ ", app.filter)
    } else if !app.filter.is_empty() {
        format!(
            " Tree — filter: \"{}\" ({} rows) ",
            app.filter,
            app.flat.len()
        )
    } else {
        " Tree ".to_string()
    };

    let items: Vec<ListItem> = app
        .flat
        .iter()
        .map(|row| {
            let node = app.node_at(&row.node_path);
            let indent = "  ".repeat(row.depth);
            let icon = if node.is_dir { "▸" } else { " " };
            let (marker, marker_color) = update_marker(node.update_state);
            let mut spans = vec![
                Span::raw(format!("{indent}{icon} ")),
                Span::styled(
                    format!("[{}]", node.tier.label()),
                    Style::default().fg(tier_color(node.tier)),
                ),
                Span::raw(" "),
                Span::raw(node.name.clone()),
            ];
            if !marker.is_empty() {
                spans.push(Span::raw(" "));
                spans.push(Span::styled(marker, Style::default().fg(marker_color)));
            }
            ListItem::new(Line::from(spans)).style(Style::default().fg(status_color(node.status)))
        })
        .collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title(title))
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("▶ ");

    f.render_stateful_widget(list, area, &mut app.list_state);
}

fn draw_detail(f: &mut Frame, area: Rect, app: &App) {
    let block = Block::default()
        .borders(Borders::ALL)
        .title(" Node Detail ");

    let Some(path) = app.selected_path() else {
        f.render_widget(Paragraph::new("Nothing selected").block(block), area);
        return;
    };
    let node = app.node_at(path);

    let mut lines: Vec<Line> = Vec::new();
    lines.push(Line::from(vec![
        Span::styled("Name: ", Style::default().add_modifier(Modifier::BOLD)),
        Span::raw(node.name.clone()),
    ]));
    lines.push(Line::from(vec![
        Span::styled("Path: ", Style::default().add_modifier(Modifier::BOLD)),
        Span::raw(if node.rel_path.is_empty() {
            ".".into()
        } else {
            node.rel_path.clone()
        }),
    ]));
    lines.push(Line::from(vec![
        Span::styled("Kind: ", Style::default().add_modifier(Modifier::BOLD)),
        Span::raw(if node.is_dir { "directory" } else { "file" }),
    ]));
    lines.push(Line::from(vec![
        Span::styled(
            "Tier (guess): ",
            Style::default().add_modifier(Modifier::BOLD),
        ),
        Span::styled(
            node.tier.label(),
            Style::default().fg(tier_color(node.tier)),
        ),
    ]));
    lines.push(Line::from(vec![
        Span::styled(
            "Install/Presence: ",
            Style::default().add_modifier(Modifier::BOLD),
        ),
        Span::styled(
            node.status.label(),
            Style::default().fg(status_color(node.status)),
        ),
    ]));
    lines.push(Line::from(vec![
        Span::styled(
            "Update status: ",
            Style::default().add_modifier(Modifier::BOLD),
        ),
        Span::raw(node.update_state.label()),
    ]));
    if !node.is_dir {
        lines.push(Line::from(vec![
            Span::styled("Size: ", Style::default().add_modifier(Modifier::BOLD)),
            Span::raw(human_size(node.size_bytes)),
        ]));
    }
    if let Some(mf) = &node.compat.manifest_file {
        lines.push(Line::from(vec![
            Span::styled(
                "Compat manifest: ",
                Style::default().add_modifier(Modifier::BOLD),
            ),
            Span::raw(mf.clone()),
        ]));
        if let Some(n) = &node.compat.package_name {
            lines.push(Line::from(format!("  name: {n}")));
        }
        if let Some(v) = &node.compat.package_version {
            lines.push(Line::from(format!("  version: {v}")));
        }
    }
    if !node.key_files.is_empty() {
        lines.push(Line::from(vec![Span::styled(
            "Key files: ",
            Style::default().add_modifier(Modifier::BOLD),
        )]));
        for k in &node.key_files {
            lines.push(Line::from(format!("  - {k}")));
        }
    }
    if let Some(note) = &node.repair_note {
        lines.push(Line::from(""));
        lines.push(Line::from(vec![Span::styled(
            "Repair suggestion:",
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )]));
        lines.push(Line::from(note.clone()));
    }
    if node.is_dir {
        lines.push(Line::from(""));
        lines.push(Line::from(format!("Children: {}", node.children.len())));
    }

    let p = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: false });
    f.render_widget(p, area);
}

fn draw_status_bar(f: &mut Frame, area: Rect, app: &mut App) {
    let text = if let Some(msg) = app.current_status() {
        msg
    } else if app.context_menu.is_some() {
        "↑↓/jk move  Enter select  click item  Esc close".to_string()
    } else if app.confirm.is_some() {
        "Y confirm  N cancel".to_string()
    } else {
        "/ filter  enter/space expand  right-click or m: menu  r rescan  y/Y copy  q quit"
            .to_string()
    };
    let bar = Paragraph::new(text).style(Style::default().fg(Color::DarkGray));
    f.render_widget(bar, area);
}

#[cfg(test)]
mod cli_tests {
    use super::*;

    fn args(values: &[&str]) -> Vec<String> {
        values.iter().map(|value| value.to_string()).collect()
    }

    #[test]
    fn parses_root_scope_dump_and_depth() {
        let parsed = CliOptions::parse(&args(&[
            "--root",
            "C:/project",
            "--scope",
            "src/L3",
            "--max-depth",
            "4",
            "--max-entries",
            "1000",
            "--max-seconds",
            "30",
            "--dump",
            "--summary",
            "--authority",
            "--resolve",
            "forge",
            "--impact",
            "forge",
            "--validate-promotion",
            "forge",
            "--evidence",
            "evidence.json",
        ]))
        .unwrap();

        assert_eq!(parsed.root, PathBuf::from("C:/project"));
        assert_eq!(parsed.scope, Some(PathBuf::from("src/L3")));
        assert_eq!(parsed.max_depth, 4);
        assert_eq!(parsed.max_entries, 1000);
        assert_eq!(parsed.max_seconds, 30);
        assert!(parsed.dump);
        assert!(parsed.summary);
        assert!(parsed.authority);
        assert_eq!(parsed.resolve.as_deref(), Some("forge"));
        assert_eq!(parsed.impact.as_deref(), Some("forge"));
        assert_eq!(parsed.validate_promotion.as_deref(), Some("forge"));
        assert_eq!(parsed.evidence, Some(PathBuf::from("evidence.json")));
        assert!(!parsed.help);
    }

    #[test]
    fn rejects_scope_escape_and_unknown_options() {
        assert!(CliOptions::parse(&args(&["--scope", "../outside"])).is_err());
        assert!(CliOptions::parse(&args(&["--unknown"])).is_err());
    }

    #[test]
    fn rejects_unpaired_promotion_options() {
        assert!(CliOptions::parse(&args(&["--validate-promotion", "forge"])).is_err());
        assert!(CliOptions::parse(&args(&["--evidence", "evidence.json"])).is_err());
    }

    #[test]
    fn rejects_invalid_depth() {
        assert!(CliOptions::parse(&args(&["--max-depth", "0"])).is_err());
        assert!(CliOptions::parse(&args(&["--max-depth", "129"])).is_err());
        assert!(CliOptions::parse(&args(&["--max-entries", "0"])).is_err());
        assert!(CliOptions::parse(&args(&["--max-seconds", "0"])).is_err());
    }
}

#[cfg(test)]
mod repair_tests {
    use super::*;

    #[test]
    fn repair_action_never_overwrites_existing_file() {
        let dir = std::env::temp_dir().join(format!("al1scan_repair_test_{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();

        // First application succeeds and creates the file.
        let msg1 = RepairAction::Gitkeep.apply(&dir, "whatever").unwrap();
        assert!(msg1.contains(".gitkeep"));
        assert!(dir.join(".gitkeep").exists());

        // Second application on the same target must fail, not overwrite.
        let result2 = RepairAction::Gitkeep.apply(&dir, "whatever");
        assert!(result2.is_err());

        // README stub only writes the file, never touches unrelated content.
        fs::write(dir.join("existing.txt"), "do not touch").unwrap();
        RepairAction::ReadmeStub.apply(&dir, "MyComponent").unwrap();
        assert!(dir.join("README.md").exists());
        assert_eq!(
            fs::read_to_string(dir.join("existing.txt")).unwrap(),
            "do not touch"
        );

        let _ = fs::remove_dir_all(&dir);
    }
}
