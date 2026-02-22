from pathlib import Path
import yaml


def load_config():
    ROOT_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = ROOT_DIR / "data"

    config = {
        # -------------------------
        # Core thresholds
        # -------------------------
        "confidence_threshold": 0.7,
        "high_value_threshold": 10_00_000,

        # -------------------------
        # Base paths
        # -------------------------
        "root_dir": ROOT_DIR,
        "data_dir": DATA_DIR,

        "invoices_dir": DATA_DIR / "invoices",
        "vendor_registry_path": DATA_DIR / "vendor_registry.json",
        "gst_rates_path": DATA_DIR / "gst_rates_schedule.csv",
        "hsn_sac_path": DATA_DIR / "hsn_sac_codes.json",
        "tds_sections_path": DATA_DIR / "tds_sections.json",
        "company_policy_path": DATA_DIR / "company_policy.yaml",
        "historical_decisions_path": DATA_DIR / "historical_decisions.jsonl",

        # -------------------------
        # External GST API
        # -------------------------
        "gst_api_base_url": "http://localhost:8080/api/gst",
        "gst_api_key": "test-api-key-12345",

        # -------------------------
        # Agentic AI feature flags
        # -------------------------
        "agentic": {
            "use_llm_resolver": True,   
            "use_mcp": True,             
            "use_sqlite_state": True     
        },

        # -------------------------
        # LLM (GROQ) config
        # -------------------------
        "groq": {
        "model": "llama-3.3-70b-versatile",
        "timeout": 30,
        "max_retries": 5
        },

        # -------------------------
        # SQLite state store
        # -------------------------
        "sqlite": {
            "db_path": DATA_DIR / "state.db"
        }
    }

    # -------------------------
    # Load company policy YAML
    # -------------------------
    try:
        with open(config["company_policy_path"], "r", encoding="utf-8") as f:
            config["company_policy"] = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Warning: Company policy file not found: {config['company_policy_path']}")
        config["company_policy"] = {}
    except yaml.YAMLError as e:
        print(f"Warning: Could not parse company policy YAML: {e}")
        config["company_policy"] = {}

    return config
