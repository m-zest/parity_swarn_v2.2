"""
Scope3Scout ESG Risk Simulation Wrapper

A FastAPI service that wraps MiroFish's multi-agent simulation engine
to provide a single-endpoint ESG risk assessment API for Scope3Scout.

Usage:
    uvicorn backend.esg_wrapper:app --host 0.0.0.0 --port 8001

Environment Variables:
    MIROFISH_BASE_URL          - MiroFish backend URL (default: http://localhost:5001)
    WRAPPER_PORT               - Port for this wrapper (default: 8001)
    USE_CACHE                  - Enable file-based result caching (default: true)
    CACHE_TTL_DAYS             - Cache time-to-live in days (default: 7)
    SIMULATION_TIMEOUT_SECONDS - Hard timeout for simulation (default: 600)
    LLM_API_KEY                - OpenAI-compatible API key (for report parsing)
    LLM_BASE_URL               - LLM API base URL
    LLM_MODEL_NAME             - LLM model name
"""

import asyncio
import hashlib
import io
import json
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env from project root
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

MIROFISH_BASE_URL = os.environ.get("MIROFISH_BASE_URL", "http://localhost:5001")
WRAPPER_PORT = int(os.environ.get("WRAPPER_PORT", "8001"))
USE_CACHE = os.environ.get("USE_CACHE", "true").lower() == "true"
CACHE_TTL_DAYS = int(os.environ.get("CACHE_TTL_DAYS", "7"))
SIMULATION_TIMEOUT_SECONDS = int(os.environ.get("SIMULATION_TIMEOUT_SECONDS", "600"))

LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

CACHE_DIR = Path(__file__).resolve().parent / "cache"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("esg_wrapper")

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class Violation(BaseModel):
    type: str = Field(..., description="Violation type (e.g., 'environmental', 'labor', 'governance')")
    severity: str = Field(..., description="Severity level: critical, high, medium, low")
    description: str = Field(..., description="Description of the violation")
    fine_amount_eur: float = Field(0, description="Fine amount in EUR")


class ESGRiskRequest(BaseModel):
    supplier_name: str = Field(..., description="Supplier company name")
    country: str = Field(..., description="Country of the supplier")
    violations: list[Violation] = Field(..., min_length=1, description="List of ESG violations")


class Prediction(BaseModel):
    agent_type: str = Field(..., description="Agent type: regulator, media, investor, NGO")
    prediction: str = Field(..., description="Prediction description")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability 0.0-1.0")
    timeline_days: int = Field(..., description="Estimated timeline in days")


class ESGRiskResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    predictions: list[Prediction] = Field(default_factory=list)
    recommended_action: str = Field("")
    financial_exposure_eur: float = Field(0)
    csrd_compliant: bool = Field(False)
    simulation_id: Optional[str] = Field(None, description="MiroFish simulation ID (if simulation ran)")
    source: str = Field("simulation", description="'simulation' or 'fallback'")
    cached: bool = Field(False, description="Whether this result was served from cache")


class HealthResponse(BaseModel):
    status: str
    mirofish_running: bool
    model: str
    cost_per_simulation: str
    cache_size: int


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class FileCache:
    """Simple file-based cache with TTL, keyed by supplier + violation hash."""

    def __init__(self, cache_dir: Path, ttl_days: int):
        self.cache_dir = cache_dir
        self.ttl = timedelta(days=ttl_days)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, request: ESGRiskRequest) -> str:
        payload = json.dumps(
            {
                "supplier_name": request.supplier_name.strip().lower(),
                "violations": [
                    {"type": v.type, "severity": v.severity, "description": v.description, "fine_amount_eur": v.fine_amount_eur}
                    for v in sorted(request.violations, key=lambda v: v.type)
                ],
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, request: ESGRiskRequest) -> Optional[dict]:
        if not USE_CACHE:
            return None
        key = self._key(request)
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            cached_at = datetime.fromisoformat(data["_cached_at"])
            if datetime.now(timezone.utc) - cached_at > self.ttl:
                path.unlink(missing_ok=True)
                return None
            data.pop("_cached_at", None)
            return data
        except Exception:
            path.unlink(missing_ok=True)
            return None

    def put(self, request: ESGRiskRequest, result: dict):
        if not USE_CACHE:
            return
        key = self._key(request)
        path = self.cache_dir / f"{key}.json"
        data = {**result, "_cached_at": datetime.now(timezone.utc).isoformat()}
        path.write_text(json.dumps(data, indent=2))

    def size(self) -> int:
        if not self.cache_dir.exists():
            return 0
        return len(list(self.cache_dir.glob("*.json")))

    def cleanup_expired(self):
        if not self.cache_dir.exists():
            return
        now = datetime.now(timezone.utc)
        for path in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                cached_at = datetime.fromisoformat(data["_cached_at"])
                if now - cached_at > self.ttl:
                    path.unlink()
            except Exception:
                path.unlink(missing_ok=True)


cache = FileCache(CACHE_DIR, CACHE_TTL_DAYS)

# ---------------------------------------------------------------------------
# Sequential Lock
# ---------------------------------------------------------------------------

simulation_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# App Lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"ESG Wrapper starting on port {WRAPPER_PORT}")
    logger.info(f"MiroFish backend: {MIROFISH_BASE_URL}")
    logger.info(f"Cache: {'enabled' if USE_CACHE else 'disabled'} (TTL: {CACHE_TTL_DAYS}d, entries: {cache.size()})")
    logger.info(f"Simulation timeout: {SIMULATION_TIMEOUT_SECONDS}s")
    logger.info(f"LLM model: {LLM_MODEL_NAME}")
    cache.cleanup_expired()
    yield
    logger.info("ESG Wrapper shutting down")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Scope3Scout ESG Risk API",
    description="ESG risk prediction powered by MiroFish multi-agent simulation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://scope3scout.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SIMULATION_REQUIREMENT = (
    "Predict regulatory enforcement risk, media coverage probability, "
    "and investor reaction to these ESG violations. "
    "Assess severity and timeline for each stakeholder group "
    "(regulators, media, investors, NGOs). "
    "Provide specific risk scores and actionable recommendations."
)


def build_violation_text(req: ESGRiskRequest) -> str:
    """Convert structured ESG input into a text document for MiroFish."""
    lines = [
        f"ESG Violation Report",
        f"Supplier: {req.supplier_name}",
        f"Country: {req.country}",
        f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        "Violations found:",
    ]
    for i, v in enumerate(req.violations, 1):
        lines.append(f"")
        lines.append(f"Violation {i}:")
        lines.append(f"  - Type: {v.type}")
        lines.append(f"  - Severity: {v.severity}")
        lines.append(f"  - Description: {v.description}")
        if v.fine_amount_eur > 0:
            lines.append(f"  - Fine: \u20ac{v.fine_amount_eur:,.2f}")
    return "\n".join(lines)


def compute_fallback(req: ESGRiskRequest) -> ESGRiskResponse:
    """Rule-based fallback when simulation fails or times out."""
    severity_scores = {"critical": 85, "high": 65, "medium": 40, "low": 20}
    max_severity = max(
        (v.severity.lower() for v in req.violations),
        key=lambda s: severity_scores.get(s, 20),
    )
    risk_score = severity_scores.get(max_severity, 40)
    total_fines = sum(v.fine_amount_eur for v in req.violations)

    predictions = []
    if max_severity in ("critical", "high"):
        predictions.append(Prediction(
            agent_type="regulator",
            prediction=f"Regulatory investigation likely in {req.country} due to {max_severity} severity violations",
            probability=0.8 if max_severity == "critical" else 0.5,
            timeline_days=30 if max_severity == "critical" else 90,
        ))
        predictions.append(Prediction(
            agent_type="media",
            prediction="Media coverage expected if violation becomes public",
            probability=0.7 if max_severity == "critical" else 0.4,
            timeline_days=7 if max_severity == "critical" else 30,
        ))
    predictions.append(Prediction(
        agent_type="investor",
        prediction="Investor concern proportional to financial exposure and ESG rating impact",
        probability=0.6 if total_fines > 100_000 else 0.3,
        timeline_days=60,
    ))

    return ESGRiskResponse(
        risk_score=risk_score,
        predictions=predictions,
        recommended_action=f"Immediate remediation required for {max_severity}-severity violations in {req.country}",
        financial_exposure_eur=total_fines * 3,
        csrd_compliant=max_severity in ("low", "medium"),
        source="fallback",
    )


async def poll_task(client: httpx.AsyncClient, task_id: str, deadline: float) -> dict:
    """Poll a graph build task until completed or deadline."""
    while time.monotonic() < deadline:
        r = await client.get(f"{MIROFISH_BASE_URL}/api/graph/task/{task_id}", timeout=30)
        data = r.json()["data"]
        status = data.get("status", "")
        if status == "completed":
            return data
        if status == "failed":
            raise RuntimeError(f"Task failed: {data.get('error', 'Unknown')}")
        await asyncio.sleep(3)
    raise TimeoutError("Task polling exceeded deadline")


async def poll_prepare(client: httpx.AsyncClient, task_id: str, deadline: float) -> dict:
    """Poll simulation prepare status until ready."""
    while time.monotonic() < deadline:
        r = await client.post(
            f"{MIROFISH_BASE_URL}/api/simulation/prepare/status",
            json={"task_id": task_id},
            timeout=30,
        )
        data = r.json()["data"]
        status = data.get("status", "")
        if status in ("completed", "ready"):
            return data
        if status == "failed":
            raise RuntimeError(f"Prepare failed: {data.get('error', 'Unknown')}")
        await asyncio.sleep(3)
    raise TimeoutError("Prepare polling exceeded deadline")


async def poll_simulation(client: httpx.AsyncClient, sim_id: str, deadline: float) -> dict:
    """Poll simulation run status until finished."""
    while time.monotonic() < deadline:
        r = await client.get(
            f"{MIROFISH_BASE_URL}/api/simulation/{sim_id}/run-status",
            timeout=30,
        )
        data = r.json()["data"]
        runner = data.get("runner_status", "")
        if runner in ("completed", "stopped"):
            return data
        if runner == "failed":
            raise RuntimeError(f"Simulation failed")
        await asyncio.sleep(5)
    # Timeout — attempt to stop the simulation
    try:
        await client.post(
            f"{MIROFISH_BASE_URL}/api/simulation/stop",
            json={"simulation_id": sim_id},
            timeout=10,
        )
    except Exception:
        pass
    raise TimeoutError("Simulation exceeded timeout")


async def poll_report(client: httpx.AsyncClient, report_id: str, deadline: float) -> dict:
    """Poll report generation until completed."""
    while time.monotonic() < deadline:
        r = await client.get(f"{MIROFISH_BASE_URL}/api/report/{report_id}", timeout=30)
        data = r.json()["data"]
        if data.get("status") == "completed":
            return data
        if data.get("status") == "failed":
            raise RuntimeError("Report generation failed")
        await asyncio.sleep(3)
    raise TimeoutError("Report generation exceeded deadline")


def parse_report_with_llm(report_markdown: str, req: ESGRiskRequest) -> dict:
    """Use LLM to parse the simulation report into structured ESG risk output."""
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY required for report parsing")

    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    total_fines = sum(v.fine_amount_eur for v in req.violations)
    prompt = f"""You are an ESG risk analyst. Parse this MiroFish simulation report into structured risk data.

Supplier: {req.supplier_name}
Country: {req.country}
Total fines: EUR {total_fines:,.2f}
Violations: {', '.join(f'{v.type} ({v.severity})' for v in req.violations)}

SIMULATION REPORT:
{report_markdown[:8000]}

Return ONLY valid JSON with this exact structure:
{{
  "risk_score": <integer 0-100>,
  "predictions": [
    {{
      "agent_type": "<regulator|media|investor|NGO>",
      "prediction": "<specific prediction>",
      "probability": <float 0.0-1.0>,
      "timeline_days": <integer>
    }}
  ],
  "recommended_action": "<actionable recommendation>",
  "financial_exposure_eur": <number>,
  "csrd_compliant": <boolean>
}}

Rules:
- risk_score: Based on simulation consensus. Higher = more risk.
- predictions: 3-6 predictions covering regulator, media, investor, NGO perspectives.
- financial_exposure_eur: Estimated total financial impact (fines + remediation + reputation).
- csrd_compliant: false if any critical/high severity violations exist.
- Be specific and grounded in the simulation data, not generic."""

    response = client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return json.loads(content.strip())


async def cleanup_project(client: httpx.AsyncClient, project_id: str):
    """Delete project to free disk space."""
    try:
        await client.delete(f"{MIROFISH_BASE_URL}/api/graph/project/{project_id}", timeout=15)
        logger.info(f"Cleaned up project {project_id}")
    except Exception as e:
        logger.warning(f"Cleanup failed for project {project_id}: {e}")


async def run_mirofish_pipeline(req: ESGRiskRequest) -> ESGRiskResponse:
    """Run the full MiroFish simulation pipeline and return structured results."""
    violation_text = build_violation_text(req)
    deadline = time.monotonic() + SIMULATION_TIMEOUT_SECONDS
    project_id = None

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Upload document + generate ontology
            logger.info(f"[{req.supplier_name}] Step 1: Generating ontology...")
            file_content = violation_text.encode("utf-8")
            r = await client.post(
                f"{MIROFISH_BASE_URL}/api/graph/ontology/generate",
                files={"files": ("esg_violation_report.txt", io.BytesIO(file_content), "text/plain")},
                data={
                    "simulation_requirement": SIMULATION_REQUIREMENT,
                    "project_name": f"ESG Risk: {req.supplier_name}",
                },
                timeout=120,
            )
            if r.status_code != 200 or not r.json().get("success"):
                raise RuntimeError(f"Ontology generation failed: {r.text[:500]}")
            ontology_data = r.json()["data"]
            project_id = ontology_data["project_id"]
            logger.info(f"[{req.supplier_name}] Ontology generated: {project_id}")

            # Step 2: Build knowledge graph
            logger.info(f"[{req.supplier_name}] Step 2: Building graph...")
            r = await client.post(
                f"{MIROFISH_BASE_URL}/api/graph/build",
                json={"project_id": project_id},
                timeout=30,
            )
            if r.status_code != 200 or not r.json().get("success"):
                raise RuntimeError(f"Graph build start failed: {r.text[:500]}")
            task_id = r.json()["data"]["task_id"]
            task_result = await poll_task(client, task_id, deadline)
            graph_id = task_result["result"]["graph_id"]
            logger.info(f"[{req.supplier_name}] Graph built: {task_result['result'].get('node_count', '?')} nodes")

            # Step 3: Create simulation
            logger.info(f"[{req.supplier_name}] Step 3: Creating simulation...")
            r = await client.post(
                f"{MIROFISH_BASE_URL}/api/simulation/create",
                json={
                    "project_id": project_id,
                    "graph_id": graph_id,
                    "enable_twitter": True,
                    "enable_reddit": False,
                },
                timeout=30,
            )
            if r.status_code != 200 or not r.json().get("success"):
                raise RuntimeError(f"Simulation create failed: {r.text[:500]}")
            sim_id = r.json()["data"]["simulation_id"]

            # Step 4: Prepare simulation
            logger.info(f"[{req.supplier_name}] Step 4: Preparing simulation...")
            r = await client.post(
                f"{MIROFISH_BASE_URL}/api/simulation/prepare",
                json={
                    "simulation_id": sim_id,
                    "use_llm_for_profiles": False,
                },
                timeout=30,
            )
            if r.status_code != 200 or not r.json().get("success"):
                raise RuntimeError(f"Simulation prepare failed: {r.text[:500]}")
            prep_task_id = r.json()["data"]["task_id"]
            await poll_prepare(client, prep_task_id, deadline)
            logger.info(f"[{req.supplier_name}] Simulation prepared")

            # Step 5: Run simulation
            logger.info(f"[{req.supplier_name}] Step 5: Running simulation (5 rounds, twitter only)...")
            r = await client.post(
                f"{MIROFISH_BASE_URL}/api/simulation/start",
                json={
                    "simulation_id": sim_id,
                    "platform": "twitter",
                    "max_rounds": 5,
                    "enable_graph_memory_update": False,
                },
                timeout=30,
            )
            if r.status_code != 200 or not r.json().get("success"):
                raise RuntimeError(f"Simulation start failed: {r.text[:500]}")
            await poll_simulation(client, sim_id, deadline)
            logger.info(f"[{req.supplier_name}] Simulation completed")

            # Step 6: Generate report
            logger.info(f"[{req.supplier_name}] Step 6: Generating report...")
            r = await client.post(
                f"{MIROFISH_BASE_URL}/api/report/generate",
                json={"simulation_id": sim_id},
                timeout=30,
            )
            if r.status_code != 200 or not r.json().get("success"):
                raise RuntimeError(f"Report generation start failed: {r.text[:500]}")
            report_id = r.json()["data"]["report_id"]
            report_data = await poll_report(client, report_id, deadline)
            report_markdown = report_data.get("markdown_content", "")
            logger.info(f"[{req.supplier_name}] Report generated ({len(report_markdown)} chars)")

            # Step 7: Parse report into structured output
            logger.info(f"[{req.supplier_name}] Step 7: Parsing report with LLM...")
            parsed = parse_report_with_llm(report_markdown, req)

            return ESGRiskResponse(
                risk_score=parsed.get("risk_score", 50),
                predictions=[Prediction(**p) for p in parsed.get("predictions", [])],
                recommended_action=parsed.get("recommended_action", ""),
                financial_exposure_eur=parsed.get("financial_exposure_eur", 0),
                csrd_compliant=parsed.get("csrd_compliant", False),
                simulation_id=sim_id,
                source="simulation",
            )

        finally:
            # Cleanup to prevent disk filling up
            if project_id:
                await cleanup_project(client, project_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    mirofish_ok = False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MIROFISH_BASE_URL}/health", timeout=5)
            mirofish_ok = r.status_code == 200
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        mirofish_running=mirofish_ok,
        model=LLM_MODEL_NAME,
        cost_per_simulation="$0.02",
        cache_size=cache.size(),
    )


@app.post("/api/simulate-esg-risk", response_model=ESGRiskResponse)
async def simulate_esg_risk(req: ESGRiskRequest):
    """
    Run an ESG risk simulation for a supplier's violations.

    Orchestrates the full MiroFish pipeline:
    ontology → graph → simulation → report → structured risk output.

    Returns cached results if available. Falls back to rule-based scoring
    if the simulation fails or times out.
    """
    logger.info(f"ESG risk request: supplier={req.supplier_name}, violations={len(req.violations)}")

    # Check cache first
    cached = cache.get(req)
    if cached:
        logger.info(f"Cache hit for {req.supplier_name}")
        response = ESGRiskResponse(**cached)
        response.cached = True
        return response

    # Acquire sequential lock — only one simulation at a time
    if simulation_lock.locked():
        logger.warning(f"Simulation already running, using fallback for {req.supplier_name}")
        fallback = compute_fallback(req)
        fallback.recommended_action += " (Note: another simulation was in progress; this is a rule-based estimate)"
        return fallback

    async with simulation_lock:
        try:
            result = await asyncio.wait_for(
                run_mirofish_pipeline(req),
                timeout=SIMULATION_TIMEOUT_SECONDS,
            )
            # Cache the successful result
            cache.put(req, result.model_dump())
            logger.info(f"Simulation completed for {req.supplier_name}: risk_score={result.risk_score}")
            return result

        except TimeoutError:
            logger.error(f"Simulation timed out for {req.supplier_name}")
            fallback = compute_fallback(req)
            fallback.recommended_action += " (Note: simulation timed out; this is a rule-based estimate)"
            return fallback

        except Exception as e:
            logger.error(f"Simulation failed for {req.supplier_name}: {e}")
            fallback = compute_fallback(req)
            fallback.recommended_action += f" (Note: simulation failed; this is a rule-based estimate)"
            return fallback


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.esg_wrapper:app",
        host="0.0.0.0",
        port=WRAPPER_PORT,
        log_level="info",
        access_log=True,
    )
