use std::collections::{HashMap, HashSet};
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering};

use anyhow::{Context, Result, bail};
use chrono::Local;
use clap::Parser;
use futures::stream::{self, StreamExt};
use indicatif::{ProgressBar, ProgressStyle};
use rand::distributions::WeightedIndex;
use rand::prelude::*;
use serde::{Deserialize, Serialize};

const GEMINI_API_BASE: &str = "https://generativelanguage.googleapis.com/v1beta";

const DEFAULT_SYSTEM_PROMPT: &str = r#"Tulislah tugas atau pertanyaan seolah-olah ditanyakan orang biasa di forum atau Stack Overflow. Orang tersebut mungkin lelah atau frustrasi, tetapi tetap kompeten. Sampaikan masalah secara langsung tanpa penjelasan berlebihan. Jangan kekanak-kanakan dan jangan terdengar seperti robot. Gunakan gaya manusia yang santai dan tidak terlalu formal.
Contoh gaya santai yang baik: "bagaimana cara membalik matriks di NumPy?", "algoritma quicksort saya mengalami kesalahan off-by-one, ini kodenya", "mengapa fetch async saya mengembalikan undefined?"
Hindari gaya yang kasar, tidak jelas, atau dibuat-buat.
PENTING: tingkat kesulitan memengaruhi cara bertanya sekaligus kompleksitas masalah:
- Tingkat 1–3: pertanyaan dasar, kebingungan yang wajar, kalimat sederhana, dan masalah dengan jawaban yang jelas.
- Tingkat 4–5: masalah teknis nyata dari orang yang cukup kompeten. Nyatakan masalah secara langsung; mungkin ada ambiguitas atau beberapa pendekatan. Sebutkan hal yang sudah dicoba jika relevan.
- Tingkat 6–7: pertanyaan tingkat ahli dengan istilah teknis yang digunakan secara alami. Masalah memiliki ketegangan, trade-off, atau pilihan desain yang nyata. Jelaskan kompleksitasnya dengan bahasa santai tetapi lengkap.
- Tingkat 8–10: masalah sangat maju yang memiliki beberapa cara pandang, hasil yang tidak pasti, atau membutuhkan sintesis lintas bidang. Jelaskan apa yang sulit, apa yang belum pasti, dan hal yang perlu diseimbangkan. Anggap pembaca sebagai ahli sejawat.
Tulislah seperti seseorang mengirim pesan kepada teman yang memahami bidang tersebut. Gunakan tanda baca yang wajar. Inti tugas harus benar secara teknis.
Untuk tingkat 6 ke atas, sertakan konflik batasan, trade-off desain, atau pertanyaan terbuka yang benar-benar relevan. Jangan membuat kompleksitas palsu.
Hindari pengantar klise. Jangan menyertakan perintah, blok kode, atau versi perangkat lunak kecuali memang wajar untuk ditempelkan oleh penanya. Pertahankan tugas tetap ringkas tanpa menghilangkan kompleksitas yang penting.
SEMUA TUGAS WAJIB DITULIS DALAM BAHASA INDONESIA. Istilah teknis, nama bahasa pemrograman, pustaka, API, dan nama produk boleh tetap menggunakan nama aslinya bila diperlukan untuk ketepatan.
Keluarkan hanya teks tugas itu sendiri. Jangan menambahkan jawaban, penjelasan proses, judul tambahan, atau komentar di luar tugas."#;


#[derive(Debug, Clone)]
struct DomainDef {
    category: &'static str,
    name: &'static str, 
    subdomains: &'static [&'static str],
}

static DOMAINS: &[DomainDef] = &[
    DomainDef { category: "math", name: "Algebra", subdomains: &["linear_equations", "polynomials", "inequalities", "matrices", "abstract_algebra"] },
    DomainDef { category: "math", name: "Calculus", subdomains: &["derivatives", "integrals", "limits", "series", "multivariable"] },
    DomainDef { category: "math", name: "Probability", subdomains: &["bayesian", "distributions", "combinatorics", "stochastic_processes", "markov_chains"] },
    DomainDef { category: "math", name: "Statistics", subdomains: &["hypothesis_testing", "regression", "anova", "descriptive", "bayesian_stats"] },
    DomainDef { category: "math", name: "Geometry", subdomains: &["euclidean", "analytic", "differential", "topology", "trigonometry"] },
    DomainDef { category: "math", name: "Number Theory", subdomains: &["primes", "modular_arithmetic", "diophantine", "cryptographic", "algebraic_nt"] },
    DomainDef { category: "math", name: "Discrete Math", subdomains: &["graph_theory", "combinatorics", "logic", "set_theory", "recurrence"] },
    DomainDef { category: "math", name: "Linear Algebra", subdomains: &["vector_spaces", "eigenvalues", "transformations", "inner_product", "decompositions"] },
    DomainDef { category: "coding", name: "Web Development", subdomains: &["html_css", "javascript", "react", "nodejs", "rest_apis", "databases", "authentication", "websockets"] },
    DomainDef { category: "coding", name: "C++", subdomains: &["templates", "stl", "memory_management", "concurrency", "meta_programming", "algorithms"] },
    DomainDef { category: "coding", name: "Java", subdomains: &["spring", "concurrency", "jvm", "design_patterns", "streams", "generics"] },
    DomainDef { category: "coding", name: "JavaScript", subdomains: &["async_await", "closures", "prototypes", "modules", "typescript", "dom", "node"] },
    DomainDef { category: "coding", name: "C", subdomains: &["pointers", "memory", "systems_programming", "ffi", "embedded", "algorithms"] },
    DomainDef { category: "coding", name: "Ruby", subdomains: &["metaprogramming", "rails", "blocks_procs", "concurrency", "gems", "dsls"] },
    DomainDef { category: "coding", name: "Lua", subdomains: &["coroutines", "metatable", "game_scripting", "embedded", "neovim", "love2d"] },
    DomainDef { category: "coding", name: "Rust", subdomains: &["ownership", "lifetimes", "traits", "async", "unsafe", "macros", "cargo"] },
    DomainDef { category: "coding", name: "C#", subdomains: &["linq", "async", "unity", "dotnet", "generics", "reflection", "entity_framework"] },
    DomainDef { category: "coding", name: "Python", subdomains: &["data_science", "ml", "web_frameworks", "scripting", "asyncio", "decorators"] },
    DomainDef { category: "coding", name: "Go", subdomains: &["goroutines", "channels", "interfaces", "modules", "networking", "microservices"] },
    DomainDef { category: "coding", name: "SQL", subdomains: &["queries", "optimization", "schema_design", "transactions", "window_functions", "nosql_comparison"] },
    DomainDef { category: "science", name: "Physics", subdomains: &["mechanics", "thermodynamics", "electromagnetism", "quantum", "relativity", "optics", "fluid_dynamics"] },
    DomainDef { category: "science", name: "Chemistry", subdomains: &["organic", "inorganic", "physical", "analytical", "biochemistry", "electrochemistry"] },
    DomainDef { category: "science", name: "Biology", subdomains: &["genetics", "ecology", "cell_biology", "evolution", "microbiology", "neuroscience", "immunology"] },
    DomainDef { category: "science", name: "Earth Science", subdomains: &["geology", "meteorology", "oceanography", "climate", "mineralogy", "volcanology"] },
    DomainDef { category: "science", name: "Astronomy", subdomains: &["stellar", "planetary", "cosmology", "astrophysics", "observational", "astrobiology"] },
    DomainDef { category: "cs", name: "Algorithms", subdomains: &["sorting", "searching", "dynamic_programming", "greedy", "divide_conquer", "graph_algorithms"] },
    DomainDef { category: "cs", name: "Data Structures", subdomains: &["trees", "graphs", "hash_tables", "heaps", "tries", "bloom_filters"] },
    DomainDef { category: "cs", name: "Operating Systems", subdomains: &["processes", "memory_management", "filesystems", "scheduling", "virtualization", "concurrency"] },
    DomainDef { category: "cs", name: "Networking", subdomains: &["tcp_ip", "dns", "http", "routing", "security", "wireless", "load_balancing"] },
    DomainDef { category: "cs", name: "Databases", subdomains: &["relational", "nosql", "indexing", "transactions", "distributed", "query_optimization"] },
    DomainDef { category: "cs", name: "Compilers", subdomains: &["lexing", "parsing", "ast", "code_gen", "optimization", "type_checking"] },
    DomainDef { category: "cs", name: "Distributed Systems", subdomains: &["consensus", "replication", "partitioning", "cap_theorem", "mapreduce", "eventual_consistency"] },
    DomainDef { category: "cs", name: "Machine Learning", subdomains: &["supervised", "unsupervised", "reinforcement", "neural_networks", "transformers", "evaluation"] },
    DomainDef { category: "cs", name: "Cybersecurity", subdomains: &["cryptography", "network_security", "web_security", "reverse_engineering", "forensics", "malware_analysis"] },
    DomainDef { category: "cs", name: "Software Engineering", subdomains: &["testing", "ci_cd", "design_patterns", "agile", "refactoring", "documentation"] },
    DomainDef { category: "creative", name: "Fiction", subdomains: &["short_story", "flash_fiction", "dialogue", "worldbuilding", "character_dev", "plot_twist"] },
    DomainDef { category: "creative", name: "Poetry", subdomains: &["sonnet", "free_verse", "haiku", "narrative", "spoken_word", "lyric"] },
    DomainDef { category: "creative", name: "Screenwriting", subdomains: &["dialogue", "scene", "monologue", "plot_structure", "character_arc", "formatting"] },
    DomainDef { category: "creative", name: "Journalism", subdomains: &["investigative", "feature", "opinion", "reporting", "interview", "editorial"] },
    DomainDef { category: "creative", name: "Songwriting", subdomains: &["lyrics", "melody_description", "concept", "hook", "verse_chorus", "story_song"] },
    DomainDef { category: "creative", name: "Game Narrative", subdomains: &["quest_design", "dialogue_trees", "lore", "cutscene", "branching_narrative", "environmental_storytelling"] },
    DomainDef { category: "creative", name: "Copywriting", subdomains: &["ad_copy", "slogans", "product_descriptions", "email_marketing", "social_media", "brand_voice"] },
    DomainDef { category: "creative", name: "Blogging", subdomains: &["how_to", "listicle", "opinion", "tutorial", "review", "personal_essay"] },
    DomainDef { category: "conversation", name: "Debate", subdomains: &["formal", "casual", "philosophical", "scientific", "political", "ethical"] },
    DomainDef { category: "conversation", name: "Advice", subdomains: &["career", "relationship", "academic", "financial", "health", "technical"] },
    DomainDef { category: "conversation", name: "Interview", subdomains: &["job", "podcast", "journalistic", "research", "behavioral", "technical_interview"] },
    DomainDef { category: "conversation", name: "Teaching", subdomains: &["socratic", "mentoring", "tutoring", "lecture_qa", "feedback", "study_guidance"] },
    DomainDef { category: "conversation", name: "Roleplay", subdomains: &["historical_figure", "professional", "customer_service", "therapy", "negotiation", "collaborative"] },
];

const DEFAULT_DISTRIBUTION: &[(&str, f64)] = &[
    ("math", 0.25),
    ("coding", 0.25),
    ("science", 0.15),
    ("cs", 0.15),
    ("creative", 0.10),
    ("conversation", 0.10),
];

const DEFAULT_DIFFICULTY: &[(u8, f64)] = &[
    (1, 0.05),
    (2, 0.05),
    (3, 0.10),
    (4, 0.15),
    (5, 0.20),
    (6, 0.15),
    (7, 0.10),
    (8, 0.08),
    (9, 0.07),
    (10, 0.05),
];

fn category_label(category: &str) -> &'static str {
    match category {
        "math" => "Matematika",
        "coding" => "Pemrograman",
        "science" => "Sains",
        "cs" => "Ilmu Komputer",
        "creative" => "Kreativitas dan Penulisan",
        "conversation" => "Percakapan",
        _ => "Lainnya",
    }
}

fn domain_label(domain: &str) -> &'static str {
    match domain {
        "Algebra" => "Aljabar", "Calculus" => "Kalkulus", "Probability" => "Probabilitas",
        "Statistics" => "Statistika", "Geometry" => "Geometri", "Number Theory" => "Teori Bilangan",
        "Discrete Math" => "Matematika Diskret", "Linear Algebra" => "Aljabar Linear",
        "Web Development" => "Pengembangan Web", "C++" => "C++", "Java" => "Java",
        "JavaScript" => "JavaScript", "C" => "C", "Ruby" => "Ruby", "Lua" => "Lua",
        "Rust" => "Rust", "C#" => "C#", "Python" => "Python", "Go" => "Go", "SQL" => "SQL",
        "Physics" => "Fisika", "Chemistry" => "Kimia", "Biology" => "Biologi",
        "Earth Science" => "Ilmu Kebumian", "Astronomy" => "Astronomi",
        "Algorithms" => "Algoritma", "Data Structures" => "Struktur Data",
        "Operating Systems" => "Sistem Operasi", "Networking" => "Jaringan Komputer",
        "Databases" => "Basis Data", "Compilers" => "Kompiler",
        "Distributed Systems" => "Sistem Terdistribusi", "Machine Learning" => "Pembelajaran Mesin",
        "Cybersecurity" => "Keamanan Siber", "Software Engineering" => "Rekayasa Perangkat Lunak",
        "Fiction" => "Fiksi", "Poetry" => "Puisi", "Screenwriting" => "Penulisan Skenario",
        "Songwriting" => "Penulisan Lagu", "Game Narrative" => "Narasi Gim", "Copywriting" => "Penulisan Iklan",
        "Journalism" => "Jurnalisme", "Blogging" => "Blogging", "Debate" => "Debat",
        "Advice" => "Saran", "Interview" => "Wawancara", "Teaching" => "Pengajaran", "Roleplay" => "Permainan Peran",
        _ => "Topik Lainnya",
    }
}

fn humanize_subdomain(subdomain: &str) -> String {
    subdomain.replace('_', " ")
}

fn difficulty_label(d: u8) -> &'static str {
    match d {
        1 => "Sangat mudah",
        2 => "Mudah",
        3 => "Dasar",
        4 => "Menengah",
        5 => "Standar",
        6 => "Mahir",
        7 => "Profesional",
        8 => "Lanjutan",
        9 => "Ahli",
        10 => "Sangat ahli lintas bidang",
        _ => "Tidak diketahui",
    }
}

#[derive(Parser, Debug, Clone)]
#[command(name = "taskgen", version, about = "SFT task generator for distillation datasets by empero-org")]
struct Args {
    #[arg(long, env = "GEMINI_API_KEY")]
    api_key: Option<String>,

    #[arg(short, long, default_value = "gemini-3.5-flash-lite")]
    model: String,

    #[arg(long)]
    system_prompt: Option<String>,

    #[arg(short, long, default_value_t = 250)]
    count: usize,

    #[arg(long)]
    distribution: Option<String>,

    #[arg(long)]
    difficulty: Option<String>,

    #[arg(short, long, default_value_t = 0.9)]
    temperature: f64,

    #[arg(short, long, default_value_t = 5)]
    workers: usize,

    #[arg(short, long, default_value = "output.jsonl")]
    output: PathBuf,

    #[arg(long)]
    append: bool,

    #[arg(long)]
    proxies: Option<PathBuf>,

    #[arg(long)]
    rotating_proxy: bool,

    #[arg(long)]
    keyfile: Option<PathBuf>,

    #[arg(long)]
    dedup: bool,

    #[arg(long, default_value_t = 0.6)]
    dedup_threshold: f64,


    #[arg(long)]
    input_price: Option<f64>,

    #[arg(long)]
    output_price: Option<f64>,

    #[arg(long)]
    budget: Option<f64>,

}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct TaskEntry {
    prompt: String,
    domain: String,
    subdomain: String,
    difficulty: u8,
    #[serde(skip_serializing_if = "Option::is_none")]
    language: Option<String>,
    taskgen_model: String,
    temperature: f64,
}

#[derive(Debug, Serialize, Deserialize)]
struct ChatRequest {
    model: String,
    messages: Vec<ChatMessage>,
    temperature: f64,
    max_tokens: Option<u64>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ChatMessage {
    role: String,
    content: String,
}


struct AtomicStats {
    input_tokens: AtomicU64,
    output_tokens: AtomicU64,
    tasks: AtomicUsize,
    errors: AtomicUsize,
}

impl AtomicStats {
    fn new() -> Self {
        Self {
            input_tokens: AtomicU64::new(0),
            output_tokens: AtomicU64::new(0),
            tasks: AtomicUsize::new(0),
            errors: AtomicUsize::new(0),
        }
    }
}

struct RunStats {
    total_input_tokens: u64,
    total_output_tokens: u64,
    total_tasks: usize,
    errors: usize,
}

fn parse_distribution(input: &str) -> Result<HashMap<String, f64>> {
    let mut map = HashMap::new();
    for pair in input.split(',') {
        let pair = pair.trim();
        let (key, val) = pair.split_once('=').context(format!("invalid distribution pair: {}", pair))?;
        let key = key.trim().to_lowercase();
        let val: f64 = val.trim().parse().context(format!("invalid weight: {}", val))?;
        map.insert(key, val);
    }
    let total: f64 = map.values().sum();
    if (total - 1.0).abs() > 0.05 {
        bail!("distribution weights must sum to ~1.0, got {}", total);
    }
    let normalized: HashMap<String, f64> = map.into_iter().map(|(k, v)| (k, v / total)).collect();
    Ok(normalized)
}

fn parse_difficulty(input: &str) -> Result<HashMap<u8, f64>> {
    let mut map = HashMap::new();
    for pair in input.split(',') {
        let pair = pair.trim();
        let (key, val) = pair.split_once('=').context(format!("invalid difficulty pair: {}", pair))?;
        let key: String = key.trim().to_lowercase();
        let d: u8 = if key.starts_with('d') {
            key[1..].parse().context(format!("invalid difficulty level: {}", key))?
        } else {
            key.parse().context(format!("invalid difficulty level: {}", key))?
        };
        if !(1..=10).contains(&d) {
            bail!("difficulty must be 1-10, got {}", d);
        }
        let val: f64 = val.trim().parse().context(format!("invalid weight: {}", val))?;
        map.insert(d, val);
    }
    let total: f64 = map.values().sum();
    if (total - 1.0).abs() > 0.05 {
        bail!("difficulty weights must sum to ~1.0, got {}", total);
    }
    let normalized: HashMap<u8, f64> = map.into_iter().map(|(k, v)| (k, v / total)).collect();
    Ok(normalized)
}

fn parse_proxy_line(line: &str) -> Result<reqwest::Proxy> {
    let line = line.trim();
    let parts: Vec<&str> = line.split(':').collect();
    let proxy_url = match parts.len() {
        2 => format!("http://{}:{}", parts[0], parts[1]),
        4 => format!("http://{}:{}@{}:{}", parts[2], parts[3], parts[0], parts[1]),
        _ => bail!("invalid proxy format '{}', expected host:port or host:port:user:pass", line),
    };
    reqwest::Proxy::all(&proxy_url).context(format!("failed to create proxy from '{}'", line))
}

fn load_proxies(path: &PathBuf) -> Result<Vec<reqwest::Proxy>> {
    let file = File::open(path).context(format!("failed to open proxy file: {}", path.display()))?;
    let reader = BufReader::new(file);
    let mut proxies = Vec::new();
    for (i, line) in reader.lines().enumerate() {
        let line = line.context("failed to read proxy file")?;
        let line = line.trim().to_string();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        proxies.push(parse_proxy_line(&line).context(format!("proxy line {}", i + 1))?);
    }
    if proxies.is_empty() {
        bail!("proxy file is empty: {}", path.display());
    }
    Ok(proxies)
}

fn build_clients(proxies: &[reqwest::Proxy]) -> Vec<reqwest::Client> {
    proxies
        .iter()
        .map(|p| {
            reqwest::Client::builder()
                .proxy(p.clone())
                .build()
                .expect("failed to build client with proxy")
        })
        .collect()
}

fn word_trigrams(text: &str) -> HashSet<String> {
    let words: Vec<&str> = text.split_whitespace().collect();
    if words.len() < 3 {
        return words.iter().map(|w| w.to_string()).collect();
    }
    words.windows(3).map(|w| w.join(" ")).collect()
}

fn jaccard_similarity(a: &HashSet<String>, b: &HashSet<String>) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 1.0;
    }
    let intersection = a.intersection(b).count();
    let union = a.union(b).count();
    if union == 0 { return 0.0; }
    intersection as f64 / union as f64
}

fn load_api_keys(path: &PathBuf) -> Result<Vec<String>> {
    let file = File::open(path).context(format!("failed to open keyfile: {}", path.display()))?;
    let reader = BufReader::new(file);
    let mut keys = Vec::new();
    for line in reader.lines() {
        let line = line.context("failed to read keyfile")?;
        let line = line.trim().to_string();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        keys.push(line);
    }
    if keys.is_empty() {
        bail!("keyfile is empty: {}", path.display());
    }
    Ok(keys)
}

fn build_domain_pool(dist: &HashMap<String, f64>) -> Vec<(String, String, String, f64)> {
    let mut pool = Vec::new();
    for (cat, &weight) in dist {
        let domains_in_cat: Vec<&DomainDef> = DOMAINS.iter().filter(|d| d.category == cat).collect();
        if domains_in_cat.is_empty() {
            continue;
        }
        let per_domain = weight / domains_in_cat.len() as f64;
        for d in &domains_in_cat {
            for &sub in d.subdomains {
                pool.push((cat.to_string(), d.name.to_string(), sub.to_string(), per_domain / d.subdomains.len() as f64));
            }
        }
    }
    pool
}

fn sample_domain(rng: &mut impl Rng, pool: &[(String, String, String, f64)]) -> (String, String, String) {
    let weights: Vec<f64> = pool.iter().map(|(_, _, _, w)| *w).collect();
    let idx = WeightedIndex::new(&weights).unwrap();
    let i = idx.sample(rng);
    let (cat, name, sub, _) = &pool[i];
    (cat.clone(), name.clone(), sub.clone())
}

fn sample_difficulty(rng: &mut impl Rng, dist: &HashMap<u8, f64>) -> u8 {
    let levels: Vec<u8> = dist.keys().copied().collect();
    let weights: Vec<f64> = levels.iter().map(|l| dist[l]).collect();
    let idx = WeightedIndex::new(&weights).unwrap();
    levels[idx.sample(rng)]
}

enum ApiError {
    RateLimit(Option<u64>),
    Billing(String),
    Timeout,
    Other(anyhow::Error),
}

impl std::fmt::Display for ApiError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ApiError::RateLimit(s) => write!(f, "rate limited (retry after {:?}s)", s),
            ApiError::Billing(msg) => write!(f, "billing error: {}", msg),
            ApiError::Timeout => write!(f, "request timed out"),
            ApiError::Other(e) => write!(f, "{}", e),
        }
    }
}

fn is_billing_error(status: reqwest::StatusCode, body: &str) -> bool {
    if status.as_u16() == 402 {
        return true;
    }
    let lower = body.to_lowercase();
    lower.contains("insufficient_quota")
        || lower.contains("billing")
        || lower.contains("payment required")
        || lower.contains("exceeded your current quota")
        || lower.contains("account is not active")
        || lower.contains("insufficient_funds")
        || lower.contains("budget")
}

async fn api_request(
    client: &reqwest::Client,
    url: &str,
    api_key: &str,
    body: &ChatRequest,
) -> std::result::Result<(String, u64, u64), ApiError> {
    let system_text = body.messages.iter().find(|m| m.role == "system").map(|m| m.content.as_str()).unwrap_or("");
    let user_text = body.messages.iter().find(|m| m.role == "user").map(|m| m.content.as_str()).unwrap_or("");
    let gemini_body = serde_json::json!({
        "systemInstruction": { "parts": [{ "text": system_text }] },
        "contents": [{ "role": "user", "parts": [{ "text": user_text }] }],
        "generationConfig": {
            "temperature": body.temperature,
            "maxOutputTokens": body.max_tokens.unwrap_or(8192),
            "responseMimeType": "application/json"
        }
    });

    let resp = client
        .post(url)
        .header("x-goog-api-key", api_key)
        .header("Content-Type", "application/json")
        .json(&gemini_body)
        .send()
        .await;

    let resp = match resp {
        Ok(r) => r,
        Err(e) => {
            if e.is_timeout() { return Err(ApiError::Timeout); }
            return Err(ApiError::Other(e.into()));
        }
    };
    let status = resp.status();
    let retry_after = resp.headers().get("retry-after").and_then(|v| v.to_str().ok()).and_then(|v| v.parse::<u64>().ok());
    if status.as_u16() == 429 {
        return Err(ApiError::RateLimit(retry_after));
    }
    if !status.is_success() {
        let text = resp.text().await.unwrap_or_default();
        if is_billing_error(status, &text) { return Err(ApiError::Billing(text)); }
        return Err(ApiError::Other(anyhow::anyhow!("Gemini API error {}: {}", status, text)));
    }
    let value: serde_json::Value = resp.json().await
        .map_err(|e| ApiError::Other(anyhow::anyhow!("failed to parse Gemini response: {}", e)))?;
    let parts = value.get("candidates").and_then(|v| v.get(0)).and_then(|v| v.get("content")).and_then(|v| v.get("parts")).and_then(|v| v.as_array())
        .ok_or_else(|| ApiError::Other(anyhow::anyhow!("Gemini response has no candidate text: {}", value)))?;
    let text = parts.iter().filter_map(|p| p.get("text").and_then(|t| t.as_str())).collect::<Vec<_>>().join("").trim().to_string();
    let usage = value.get("usageMetadata");
    let input_tokens = usage.and_then(|u| u.get("promptTokenCount")).and_then(|n| n.as_u64()).unwrap_or(0);
    let output_tokens = usage.and_then(|u| u.get("candidatesTokenCount")).and_then(|n| n.as_u64()).unwrap_or(0);
    if text.is_empty() { return Err(ApiError::Other(anyhow::anyhow!("Gemini returned empty text: {}", value))); }
    Ok((text, input_tokens, output_tokens))
}

const MAX_RETRIES: u32 = 5;

fn clean_markdown(text: &str) -> String {
    let mut cleaned = text.trim().to_string();
    if cleaned.starts_with(char::from(96)) {
        if let Some(newline) = cleaned.find('\n') {
            cleaned = cleaned[newline + 1..].to_string();
        }
    }
    while cleaned.ends_with(char::from(96)) {
        cleaned.pop();
    }

    let mut lines = Vec::new();
    for line in cleaned.lines() {
        let mut line = line.trim().to_string();
        while line.starts_with('#') { line.remove(0); }
        line = line.trim_start().to_string();
        if line.starts_with("- ") || line.starts_with("* ") || line.starts_with("+ ") {
            line = line[2..].trim_start().to_string();
        } else {
            let prefix_len = line.chars().take_while(|c| c.is_ascii_digit()).count();
            if prefix_len > 0 {
                let rest = &line[prefix_len..];
                if rest.starts_with(". ") || rest.starts_with(") ") {
                    line = rest[2..].trim_start().to_string();
                }
            }
        }
        line = line.replace("**", "").replace(char::from(96), "");
        if !line.is_empty() { lines.push(line); }
    }
    lines.join("\n").trim().to_string()
}

async fn generate_batch(
    client: &reqwest::Client,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    tasks: &[(String, String, String, u8, Option<String>)],
    temperature: f64,
    cancel: &AtomicBool,
    consecutive_timeouts: &AtomicUsize,
    pb: &ProgressBar,
) -> std::result::Result<(Vec<String>, u64, u64), ApiError> {
    let mut task_descriptions = String::new();
    for (idx, (category, domain_name, subdomain, difficulty, _language)) in tasks.iter().enumerate() {
        let topic_display = format!("{}::{}", category_label(category), domain_label(domain_name));
        task_descriptions.push_str(&format!(
            "{}. Topik: {}; subtopik: {}; tingkat kesulitan: {}/10 ({}). Buat pertanyaan spesifik yang berfokus pada subtopik ini.\n",
            idx + 1, topic_display, humanize_subdomain(subdomain), difficulty, difficulty_label(*difficulty)
        ));
    }

    let user_msg = format!(
        "Buat tepat {} pertanyaan/tugas berbeda sesuai daftar berikut. Semua harus berbahasa Indonesia.\n\n{}\nKeluarkan hanya JSON valid berupa array yang berisi tepat {} string, dengan urutan yang sama. Setiap string hanya teks pertanyaan, tanpa jawaban, komentar, Markdown, bullet, nomor daftar, heading, atau code fence.",
        tasks.len(), task_descriptions, tasks.len()
    );
    let body = ChatRequest {
        model: model.to_string(),
        messages: vec![
            ChatMessage {
                role: "system".into(),
                content: format!("{}\n\nInstruksi wajib: teks pertanyaan harus polos tanpa Markdown. Ikuti jumlah dan urutan yang diminta.", system_prompt),
            },
            ChatMessage { role: "user".into(), content: user_msg },
        ],
        temperature,
        max_tokens: Some(8192),
    };
    let url = format!("{}/models/{}:generateContent", GEMINI_API_BASE, model);
    let mut retries = 0u32;
    loop {
        if cancel.load(Ordering::Relaxed) {
            return Err(ApiError::Other(anyhow::anyhow!("cancelled")));
        }
        match api_request(client, &url, api_key, &body).await {
            Ok((response_text, input_tokens, output_tokens)) => {
                consecutive_timeouts.store(0, Ordering::Relaxed);
                let parsed_text = response_text.trim();
                let json_text = if parsed_text.starts_with(char::from(96)) {
                    parsed_text.find('\n')
                        .map(|newline| &parsed_text[newline + 1..])
                        .unwrap_or(parsed_text)
                        .trim_end_matches(char::from(96)).trim()
                } else { parsed_text };
                let value: serde_json::Value = serde_json::from_str(json_text)
                    .map_err(|e| ApiError::Other(anyhow::anyhow!("invalid JSON batch: {}", e)))?;
                let array = value.as_array()
                    .ok_or_else(|| ApiError::Other(anyhow::anyhow!("batch response must be a JSON array")))?;
                let prompts: Vec<String> = array.iter()
                    .filter_map(|item| item.as_str())
                    .map(clean_markdown)
                    .collect();
                if prompts.len() != tasks.len() {
                    return Err(ApiError::Other(anyhow::anyhow!(
                        "model returned {} prompts for batch size {}; expected exactly {}",
                        prompts.len(), tasks.len(), tasks.len()
                    )));
                }
                return Ok((prompts, input_tokens, output_tokens));
            }
            Err(ApiError::RateLimit(retry_after)) => {
                retries += 1;
                if retries > MAX_RETRIES { return Err(ApiError::RateLimit(retry_after)); }
                let wait = retry_after.unwrap_or_else(|| 2u64.pow(retries).min(60));
                pb.suspend(|| eprintln!("[RATE] 429 hit, waiting {}s (retry {}/{})", wait, retries, MAX_RETRIES));
                tokio::time::sleep(tokio::time::Duration::from_secs(wait)).await;
            }
            Err(ApiError::Timeout) => {
                let count = consecutive_timeouts.fetch_add(1, Ordering::Relaxed) + 1;
                if count >= 5 {
                    pb.suspend(|| eprintln!("[FATAL] {} consecutive timeouts, shutting down gracefully...", count));
                    cancel.store(true, Ordering::Relaxed);
                    return Err(ApiError::Timeout);
                }
                retries += 1;
                if retries > MAX_RETRIES { return Err(ApiError::Timeout); }
                let wait = 2u64.pow(retries).min(30);
                pb.suspend(|| eprintln!("[TIMEOUT] request timed out, waiting {}s (retry {}/{}, {} consecutive)", wait, retries, MAX_RETRIES, count));
                tokio::time::sleep(tokio::time::Duration::from_secs(wait)).await;
            }
            Err(ApiError::Billing(msg)) => {
                pb.suspend(|| eprintln!("[FATAL] billing error, shutting down gracefully: {}", msg));
                cancel.store(true, Ordering::Relaxed);
                return Err(ApiError::Billing(msg));
            }
            Err(e) => return Err(e),
        }
    }
}


fn count_existing_tasks(path: &PathBuf) -> usize {
    if !path.exists() {
        return 0;
    }
    let file = File::open(path).ok();
    match file {
        Some(f) => BufReader::new(f).lines().filter_map(|l| l.ok()).filter(|l| !l.trim().is_empty()).count(),
        None => 0,
    }
}

fn generate_readme(
    args: &Args,
    stats: &RunStats,
    dist: &HashMap<String, f64>,
    diff_dist: &HashMap<u8, f64>,
) -> String {
    let input_cost = args.input_price.map(|p| p * stats.total_input_tokens as f64 / 1_000_000.0);
    let output_cost = args.output_price.map(|p| p * stats.total_output_tokens as f64 / 1_000_000.0);
    let total_cost = match (input_cost, output_cost) {
        (Some(i), Some(o)) => Some(i + o),
        _ => None,
    };

    let mut md = String::new();

    md.push_str("# Dataset TaskGen\n\n");
    md.push_str("> Generated with **taskgen** by [empero-org](https://github.com/empero-org)\n\n");

    md.push_str("## Parameter Generasi\n\n");
    md.push_str("| Parameter | Nilai |\n|---|---|\n");
    md.push_str(&format!("| Model | `{}` |\n", args.model));
    md.push_str(&format!("| Temperatur | `{}` |\n", args.temperature));
    md.push_str(&format!("| Total tugas | {} |\n", stats.total_tasks));
    md.push_str(&format!("| Worker paralel | {} |\n", args.workers));
    md.push_str("| Penyedia API | Google Gemini API (REST native) |\n");
    md.push_str("| Bahasa | Indonesia (`id`) saja |\n");
    md.push_str(&format!("| Waktu dibuat | {} |\n", Local::now().format("%Y-%m-%d %H:%M:%S")));
    if let Some(b) = args.budget {
        md.push_str(&format!("| Budget Cap | ${:.4} |\n", b));
    }
    md.push('\n');


    md.push_str("## Distribusi Kategori\n\n");
    md.push_str("| Kategori | Bobot |\n|---|---|\n");
    let mut sorted_cats: Vec<_> = dist.iter().collect();
    sorted_cats.sort_by(|a, b| b.1.partial_cmp(a.1).unwrap());
    for (cat, w) in &sorted_cats {
        md.push_str(&format!("| {} | {:.1}% |\n", category_label(cat), **w * 100.0));
    }
    md.push('\n');

    md.push_str("## Distribusi Tingkat Kesulitan\n\n");
    md.push_str("| Level | Keterangan | Bobot |\n|---|---|---|\n");
    for d in 1..=10u8 {
        if let Some(w) = diff_dist.get(&d) {
            md.push_str(&format!("| {} | {} | {:.1}% |\n", d, difficulty_label(d), w * 100.0));
        }
    }
    md.push('\n');

    md.push_str("## Penggunaan Token dan Biaya\n\n");
    md.push_str("| Metrik | Nilai |\n|---|---|\n");
    md.push_str(&format!("| Token input | {} |\n", stats.total_input_tokens));
    md.push_str(&format!("| Token output | {} |\n", stats.total_output_tokens));
    md.push_str(&format!("| Total token | {} |\n", stats.total_input_tokens + stats.total_output_tokens));
    md.push_str(&format!("| Error | {} |\n", stats.errors));
    if let Some(ic) = input_cost {
        md.push_str(&format!("| Input Cost | ${:.6} |\n", ic));
    }
    if let Some(oc) = output_cost {
        md.push_str(&format!("| Output Cost | ${:.6} |\n", oc));
    }
    if let Some(tc) = total_cost {
        md.push_str(&format!("| **Total Cost** | **${:.6}** |\n", tc));
    }
    if args.input_price.is_none() && args.output_price.is_none() {
        md.push_str("| Biaya | *Tidak dihitung; harga token belum dikonfigurasi* |\n");
    }
    md.push('\n');

    md.push_str("## Format Keluaran\n\n");
    md.push_str("Setiap baris file JSONL berisi:\n\n");
    md.push_str("```json\n");
    md.push_str("{\n");
    md.push_str("  \"prompt\": \"...\",\n");
    md.push_str("  \"domain\": \"math::Algebra\",\n");
    md.push_str("  \"subdomain\": \"polynomials\",\n");
    md.push_str("  \"difficulty\": 5,\n");
    md.push_str("  \"language\": \"id\",\n");
    md.push_str(&format!("  \"taskgen_model\": \"{}\",\n", args.model));
    md.push_str("  \"temperature\": 0.9\n");
    md.push_str("}\n");
    md.push_str("```\n\n");


    md.push_str("---\n\n");
    md.push_str("*Dibuat menggunakan [taskgen](https://github.com/empero-org/taskgen) oleh empero-org*\n");

    md
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    let api_keys: Arc<Vec<String>> = Arc::new(match &args.keyfile {
        Some(path) => {
            let keys = load_api_keys(path)?;
            println!("Loaded {} API keys (round-robin)", keys.len());
            keys
        }
        None => {
            let key = args.api_key.clone().context("API key Gemini diperlukan. Gunakan --api-key atau set GEMINI_API_KEY")?;
            vec![key]
        }
    });
    let key_counter = Arc::new(AtomicUsize::new(0));

    let dist: HashMap<String, f64> = match &args.distribution {
        Some(d) => parse_distribution(d)?,
        None => DEFAULT_DISTRIBUTION.iter().map(|(k, v)| (k.to_string(), *v)).collect(),
    };

    let diff_dist: HashMap<u8, f64> = match &args.difficulty {
        Some(d) => parse_difficulty(d)?,
        None => DEFAULT_DIFFICULTY.iter().map(|(k, v)| (*k, *v)).collect(),
    };

    let pool = build_domain_pool(&dist);
    if pool.is_empty() {
        bail!("no domains matched the given distribution. Kategori tersedia: math (matematika), coding (pemrograman), science (sains), cs (ilmu komputer), creative (kreativitas), conversation (percakapan)");
    }

    let system_prompt = args.system_prompt.as_deref().unwrap_or(DEFAULT_SYSTEM_PROMPT);

    let existing = if args.append { count_existing_tasks(&args.output) } else { 0 };
    if existing > 0 {
        println!("Appending to existing file with {} tasks", existing);
    }

    let file = if args.append && args.output.exists() {
        OpenOptions::new().append(true).open(&args.output)?
    } else {
        File::create(&args.output)?
    };

    let clients: Arc<Vec<reqwest::Client>> = Arc::new(match &args.proxies {
        Some(proxy_path) => {
            let proxies = load_proxies(proxy_path)?;
            let total = proxies.len();
            if args.rotating_proxy {
                let idx = thread_rng().gen_range(0..total);
                println!("Using rotating proxy (sticky): proxy #{}", idx + 1);
                vec![reqwest::Client::builder()
                    .proxy(proxies.into_iter().nth(idx).unwrap())
                    .build()?]
            } else {
                println!("Loaded {} proxies (round-robin)", total);
                build_clients(&proxies)
            }
        }
        None => vec![reqwest::Client::new()],
    });
    let proxy_counter = Arc::new(AtomicUsize::new(0));

    let file = Arc::new(std::sync::Mutex::new(file));
    let stats = Arc::new(AtomicStats::new());
    let cancel = Arc::new(AtomicBool::new(false));
    let consecutive_timeouts = Arc::new(AtomicUsize::new(0));

    let budget = args.budget;
    let input_price = args.input_price;
    let output_price = args.output_price;
    let count = args.count;
    let workers = args.workers;

    // Pre-sample tuples to preserve weighted distributions, then send at most 30 per API call.
    const BATCH_SIZE: usize = 30;
    let mut rng = thread_rng();
    let presampled: Vec<(String, String, String, u8, Option<String>)> = (0..count)
        .map(|_| {
            let (cat, name, sub) = sample_domain(&mut rng, &pool);
            let diff = sample_difficulty(&mut rng, &diff_dist);
            (cat, name, sub, diff, Some("id".to_string()))
        })
        .collect();
    let presampled = Arc::new(presampled);

    let pb = ProgressBar::new(count as u64);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({per_sec}) | {msg}")
            .unwrap()
            .progress_chars("##-"),
    );
    pb.set_message("starting...");

    stream::iter((0..count).step_by(BATCH_SIZE).collect::<Vec<_>>())
        .for_each_concurrent(workers, |start| {
            let clients = clients.clone();
            let proxy_counter = proxy_counter.clone();
            let file = file.clone();
            let stats = stats.clone();
            let cancel = cancel.clone();
            let consecutive_timeouts = consecutive_timeouts.clone();
            let api_keys = api_keys.clone();
            let key_counter = key_counter.clone();
            let model = args.model.clone();
            let system_prompt = system_prompt.to_string();
            let presampled = presampled.clone();
            let temperature = args.temperature;
            let pb = pb.clone();

            async move {
                let end = (start + BATCH_SIZE).min(presampled.len());
                let batch_len = end - start;
                if cancel.load(Ordering::Relaxed) {
                    pb.inc(batch_len as u64);
                    return;
                }

                if let (Some(b), Some(ip), Some(op)) = (budget, input_price, output_price) {
                    let in_tok = stats.input_tokens.load(Ordering::Relaxed) as f64;
                    let out_tok = stats.output_tokens.load(Ordering::Relaxed) as f64;
                    let cost = (ip * in_tok / 1_000_000.0) + (op * out_tok / 1_000_000.0);
                    if cost >= b {
                        cancel.store(true, Ordering::Relaxed);
                        pb.inc(batch_len as u64);
                        return;
                    }
                }

                let batch: Vec<(String, String, String, u8, Option<String>)> = presampled[start..end].to_vec();
                let client_idx = proxy_counter.fetch_add(1, Ordering::Relaxed) % clients.len();
                let client = &clients[client_idx];
                let key_idx = key_counter.fetch_add(1, Ordering::Relaxed) % api_keys.len();
                let api_key = &api_keys[key_idx];

                match generate_batch(
                    client, api_key, &model, &system_prompt, &batch, temperature,
                    &cancel, &consecutive_timeouts, &pb,
                ).await {
                    Ok((prompts, in_tok, out_tok)) => {
                        stats.input_tokens.fetch_add(in_tok, Ordering::Relaxed);
                        stats.output_tokens.fetch_add(out_tok, Ordering::Relaxed);

                        for (offset, prompt) in prompts.into_iter().enumerate() {
                            let (ref cat, ref domain_name, ref subdomain, difficulty, ref _lang) = batch[offset];
                            if prompt.trim().is_empty() {
                                stats.errors.fetch_add(1, Ordering::Relaxed);
                                continue;
                            }
                            let entry = TaskEntry {
                                prompt,
                                domain: format!("{}::{}", category_label(cat), domain_label(domain_name)),
                                subdomain: subdomain.clone(),
                                difficulty,
                                language: Some("id".to_string()),
                                taskgen_model: model.clone(),
                                temperature,
                            };
                            let line = serde_json::to_string(&entry).unwrap() + "\n";
                            let mut f = file.lock().unwrap();
                            if let Err(e) = f.write_all(line.as_bytes()).and_then(|_| f.flush()) {
                                stats.errors.fetch_add(1, Ordering::Relaxed);
                                pb.suspend(|| eprintln!("[ERROR] failed writing output: {}", e));
                            } else {
                                let done = stats.tasks.fetch_add(1, Ordering::Relaxed) + 1;
                                pb.set_message(format!("{} ok | {} err | {}k tok", done,
                                    stats.errors.load(Ordering::Relaxed),
                                    (stats.input_tokens.load(Ordering::Relaxed) + stats.output_tokens.load(Ordering::Relaxed)) / 1000));
                            }
                        }
                    }
                    Err(e) => {
                        stats.errors.fetch_add(batch_len, Ordering::Relaxed);
                        if !cancel.load(Ordering::Relaxed) {
                            pb.suspend(|| eprintln!("[ERROR] batch {}-{}: {}", start + 1, end, e));
                        }
                    }
                }
                pb.inc(batch_len as u64);
            }
        })
        .await;

    let was_cancelled = cancel.load(Ordering::Relaxed);
    if was_cancelled {
        pb.finish_with_message("stopped early — saving progress");
    } else {
        pb.finish_with_message("done");
    }

    let total_tasks = stats.tasks.load(Ordering::Relaxed);
    let total_errors = stats.errors.load(Ordering::Relaxed);
    let total_in = stats.input_tokens.load(Ordering::Relaxed);
    let total_out = stats.output_tokens.load(Ordering::Relaxed);

    if was_cancelled {
        println!("\nGraceful shutdown — saved {} tasks before exit", total_tasks);
    }
    println!("Generated {} tasks ({} errors)", total_tasks, total_errors);
    println!("Tokens: {} in / {} out", total_in, total_out);

    let stats = RunStats {
        total_input_tokens: total_in,
        total_output_tokens: total_out,
        total_tasks,
        errors: total_errors,
    };

    if args.dedup && args.output.exists() {
        println!("\nRunning deduplication (threshold: {:.2})...", args.dedup_threshold);

        let reader = BufReader::new(File::open(&args.output)?);
        let mut lines: Vec<String> = Vec::new();
        let mut entries: Vec<Option<TaskEntry>> = Vec::new();

        for line in reader.lines().flatten() {
            let entry = serde_json::from_str::<TaskEntry>(&line).ok();
            entries.push(entry);
            lines.push(line);
        }

        // pass 1: exact duplicates
        let mut seen: HashSet<String> = HashSet::new();
        let mut keep = vec![true; lines.len()];
        let mut exact_dupes = 0usize;

        for (i, entry) in entries.iter().enumerate() {
            if let Some(e) = entry {
                let normalized: String = e.prompt.to_lowercase().split_whitespace().collect();
                if !seen.insert(normalized) {
                    keep[i] = false;
                    exact_dupes += 1;
                }
            }
        }

        if exact_dupes > 0 {
            println!("Removed {} exact duplicates", exact_dupes);
        }

        // pass 2: semantic duplicates via word-trigram jaccard
        let kept_indices: Vec<usize> = (0..lines.len()).filter(|&i| keep[i]).collect();
        let trigrams: Vec<Option<HashSet<String>>> = kept_indices
            .iter()
            .map(|&i| {
                entries[i]
                    .as_ref()
                    .map(|e| word_trigrams(&e.prompt.to_lowercase()))
            })
            .collect();

        let mut semantic_dupes = 0usize;
        for j in 1..kept_indices.len() {
            if !keep[kept_indices[j]] {
                continue;
            }
            let trig_b = match &trigrams[j] {
                Some(t) => t,
                None => continue,
            };
            for k in 0..j {
                if !keep[kept_indices[k]] {
                    continue;
                }
                let trig_a = match &trigrams[k] {
                    Some(t) => t,
                    None => continue,
                };
                if jaccard_similarity(trig_a, trig_b) >= args.dedup_threshold {
                    keep[kept_indices[j]] = false;
                    semantic_dupes += 1;
                    break;
                }
            }
        }

        if semantic_dupes > 0 {
            println!("Removed {} semantic duplicates (similarity >= {:.2})", semantic_dupes, args.dedup_threshold);
        }

        let total_removed = exact_dupes + semantic_dupes;
        if total_removed > 0 {
            let mut f = File::create(&args.output)?;
            for (i, line) in lines.iter().enumerate() {
                if keep[i] {
                    f.write_all(line.as_bytes())?;
                    f.write_all(b"\n")?;
                }
            }
            let remaining = lines.len() - total_removed;
            println!("Deduplication complete: {} removed, {} remaining", total_removed, remaining);
        } else {
            println!("No duplicates found");
        }
    }

    // Dataset is Indonesian-only; no language-based file splitting is performed.
    let readme = generate_readme(&args, &stats, &dist, &diff_dist);
    let readme_path = args.output.parent().unwrap_or(std::path::Path::new(".")).join("README.md");
    let mut rf = File::create(&readme_path).context("failed to create README.md")?;
    rf.write_all(readme.as_bytes())?;
    println!("README.md written to {}", readme_path.display());

    Ok(())
}
