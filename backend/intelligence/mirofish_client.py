"""
Oybit — MiroFish Client
HTTP adapter that calls MiroFish's Flask API (port 5001) to run
swarm-intelligence simulations on draft content before publishing.

MiroFish API Flow:
  1. POST /api/graph/ontology/generate   → Upload seed, generate ontology
  2. POST /api/graph/build               → Build knowledge graph in Zep
  3. POST /api/simulation/create         → Create simulation from graph
  4. POST /api/simulation/prepare        → Generate agent personas + config
  5. POST /api/simulation/start          → Run the dual-platform simulation
  6. POST /api/report/generate           → Generate prediction report
  7. GET  /api/report/<report_id>        → Fetch the final report

Required ENV:
  MIROFISH_API_URL — MiroFish backend URL (default http://localhost:5001)
"""

import os
import io
import logging
import asyncio
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MIROFISH_URL = os.getenv("MIROFISH_API_URL", "http://localhost:5001")
POLL_INTERVAL = 2  # seconds between status polls
MAX_WAIT_SECONDS = 300  # 5 minutes max for any single stage


class MiroFishClient:
    """Thin async HTTP client for the MiroFish Flask backend."""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or MIROFISH_URL).rstrip("/")

    # ── Health Check ──────────────────────────────────
    async def is_available(self) -> bool:
        """Check if MiroFish backend is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self.base_url}/")
                return r.status_code < 500
        except Exception:
            return False

    # ── Step 1: Create Project + Ontology ─────────────
    async def create_project_and_ontology(
        self,
        seed_text: str,
        simulation_requirement: str,
        project_name: str = "Oybit Gate Check",
    ) -> dict:
        """
        Upload seed material as a .txt file and generate ontology.
        Returns: { project_id, ontology, analysis_summary }
        """
        # MiroFish expects a multipart file upload
        file_bytes = seed_text.encode("utf-8")

        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(
                f"{self.base_url}/api/graph/ontology/generate",
                data={
                    "simulation_requirement": simulation_requirement,
                    "project_name": project_name,
                },
                files={
                    "files": ("seed_material.txt", io.BytesIO(file_bytes), "text/plain"),
                },
            )
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Ontology generation failed: {body.get('error')}")

        return body["data"]

    # ── Step 2: Build Knowledge Graph ─────────────────
    async def build_graph(self, project_id: str) -> str:
        """
        Start graph build → poll until complete → return graph_id.
        """
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{self.base_url}/api/graph/build",
                json={"project_id": project_id},
            )
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Graph build failed to start: {body.get('error')}")

        task_id = body["data"]["task_id"]
        return await self._poll_task(task_id, stage_name="graph_build")

    # ── Step 3: Create Simulation ─────────────────────
    async def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> str:
        """Create a simulation record. Returns simulation_id."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{self.base_url}/api/simulation/create",
                json={
                    "project_id": project_id,
                    "graph_id": graph_id,
                    "enable_twitter": enable_twitter,
                    "enable_reddit": enable_reddit,
                },
            )
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Simulation create failed: {body.get('error')}")

        return body["data"]["simulation_id"]

    # ── Step 4: Prepare Simulation (generate agents) ──
    async def prepare_simulation(self, simulation_id: str) -> dict:
        """
        Prepare agent personas + config. Polls until ready.
        Returns prepare_info dict.
        """
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{self.base_url}/api/simulation/prepare",
                json={
                    "simulation_id": simulation_id,
                    "use_llm_for_profiles": True,
                    "parallel_profile_count": 5,
                },
            )
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Simulation prepare failed: {body.get('error')}")

        data = body["data"]
        if data.get("already_prepared"):
            return data.get("prepare_info", {})

        task_id = data.get("task_id")
        if task_id:
            await self._poll_prepare(simulation_id, task_id)

        return data

    # ── Step 5: Start Simulation ──────────────────────
    async def start_simulation(self, simulation_id: str) -> dict:
        """Start the OASIS dual-platform simulation."""
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{self.base_url}/api/simulation/start",
                json={"simulation_id": simulation_id},
            )
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Simulation start failed: {body.get('error')}")

        # Poll until simulation completes
        await self._poll_simulation_run(simulation_id)
        return body["data"]

    # ── Step 6: Generate Report ───────────────────────
    async def generate_report(self, simulation_id: str) -> str:
        """Generate a prediction report. Returns report_id."""
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{self.base_url}/api/report/generate",
                json={"simulation_id": simulation_id},
            )
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Report generation failed: {body.get('error')}")

        report_id = body["data"].get("report_id")
        if not report_id:
            raise RuntimeError("No report_id returned from MiroFish")

        # Poll until report is ready
        await self._poll_report(report_id)
        return report_id

    # ── Step 7: Fetch Report ──────────────────────────
    async def get_report(self, report_id: str) -> dict:
        """Fetch the completed prediction report."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self.base_url}/api/report/{report_id}")
            r.raise_for_status()
            body = r.json()

        if not body.get("success"):
            raise RuntimeError(f"Report fetch failed: {body.get('error')}")

        return body["data"]

    # ── Fetch Simulation Posts (agent reactions) ──────
    async def get_simulation_posts(self, simulation_id: str) -> list:
        """Get all posts made by agents during the simulation."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{self.base_url}/api/simulation/{simulation_id}/posts"
            )
            r.raise_for_status()
            body = r.json()

        return body.get("data", {}).get("posts", [])

    # ── Fetch Agent Stats ─────────────────────────────
    async def get_agent_stats(self, simulation_id: str) -> dict:
        """Get agent activity statistics from the simulation."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{self.base_url}/api/simulation/{simulation_id}/agent-stats"
            )
            r.raise_for_status()
            body = r.json()

        return body.get("data", {})

    # ── Interview an Agent ────────────────────────────
    async def interview_agent(
        self, simulation_id: str, agent_id: str, question: str
    ) -> str:
        """Chat with a specific agent post-simulation."""
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{self.base_url}/api/simulation/interview",
                json={
                    "simulation_id": simulation_id,
                    "agent_id": agent_id,
                    "prompt": question,
                },
            )
            r.raise_for_status()
            body = r.json()

        return body.get("data", {}).get("response", "")

    # ── List Simulations ──────────────────────────────
    async def list_simulations(self) -> list:
        """List all simulations."""
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{self.base_url}/api/simulation/list")
            r.raise_for_status()
            body = r.json()

        return body.get("data", [])

    # ══════════════════════════════════════════════════
    #  Internal Polling Helpers
    # ══════════════════════════════════════════════════

    async def _poll_task(self, task_id: str, stage_name: str = "task") -> str:
        """Poll a graph/build task until complete. Returns graph_id from result."""
        elapsed = 0
        while elapsed < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"{self.base_url}/api/graph/task/{task_id}")
                r.raise_for_status()
                body = r.json()

            data = body.get("data", {})
            status = data.get("status", "")
            progress = data.get("progress", 0)
            logger.info(f"MiroFish {stage_name}: {status} ({progress}%)")

            if status == "completed":
                result = data.get("result", {})
                return result.get("graph_id", "")
            elif status == "failed":
                raise RuntimeError(
                    f"MiroFish {stage_name} failed: {data.get('error', data.get('message'))}"
                )

        raise TimeoutError(f"MiroFish {stage_name} timed out after {MAX_WAIT_SECONDS}s")

    async def _poll_prepare(self, simulation_id: str, task_id: str):
        """Poll the simulation prepare task until ready."""
        await asyncio.sleep(3) # 3s grace delay to avoid 404 race on task not registered yet
        elapsed = 0
        while elapsed < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(
                    f"{self.base_url}/api/simulation/prepare/status",
                    json={"task_id": task_id, "simulation_id": simulation_id},
                )
                r.raise_for_status()
                body = r.json()

            data = body.get("data", {})
            status = data.get("status", "")
            progress = data.get("progress", 0)
            logger.info(f"MiroFish prepare: {status} ({progress}%)")

            if status in ("completed", "ready"):
                return
            elif status == "failed":
                raise RuntimeError(f"MiroFish prepare failed: {data.get('message')}")

        raise TimeoutError(f"MiroFish prepare timed out after {MAX_WAIT_SECONDS}s")

    async def _poll_simulation_run(self, simulation_id: str):
        """Poll simulation run status until completed."""
        elapsed = 0
        current_interval = POLL_INTERVAL
        while elapsed < MAX_WAIT_SECONDS:
            await asyncio.sleep(current_interval)
            elapsed += current_interval
            # Exponential backoff up to 30 seconds
            current_interval = min(current_interval * 1.5, 30.0)

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(
                    f"{self.base_url}/api/simulation/{simulation_id}/run-status"
                )
                r.raise_for_status()
                body = r.json()

            data = body.get("data", {})
            # SimulationState.to_simple_dict() in MiroFish returns it directly as `status` or nested.
            status = data.get("runner_status", data.get("status", ""))
            if isinstance(status, dict):
                status = status.get("value", str(status)) # In case it's serialized differently
            
            logger.info(f"MiroFish simulation run: status={status} (data={data})")

            if status in ("completed", "stopped"):
                return
            elif status == "failed":
                raise RuntimeError(f"MiroFish simulation run failed: {data.get('error')}")

        raise TimeoutError(f"MiroFish simulation timed out after {MAX_WAIT_SECONDS}s")

    async def _poll_report(self, report_id: str):
        """Poll report generation until complete."""
        elapsed = 0
        while elapsed < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(
                    f"{self.base_url}/api/report/{report_id}/progress"
                )
                r.raise_for_status()
                body = r.json()

            data = body.get("data", {})
            status = data.get("status", "")
            progress = data.get("progress", 0)
            logger.info(f"MiroFish report: {status} ({progress}%)")

            if status == "completed":
                return
            elif status == "failed":
                raise RuntimeError(f"MiroFish report failed: {data.get('error')}")

        raise TimeoutError(f"MiroFish report timed out after {MAX_WAIT_SECONDS}s")


# ══════════════════════════════════════════════════════
#  Convenience: Full Pipeline in One Call
# ══════════════════════════════════════════════════════

async def run_full_mirofish_gate(
    draft_text: str,
    persona_context: str,
    platform: str = "linkedin",
    project_name: str = "Oybit Gate Check",
) -> dict:
    """
    Run the complete MiroFish pipeline on a draft post:
      seed → ontology → graph → simulation → report → gate decision

    Returns:
        {
            "passed": bool,
            "report_id": str,
            "simulation_id": str,
            "sentiment_summary": str,
            "agent_reactions": list,
            "recommendation": str,
            "raw_report": dict,
        }
    """
    client = MiroFishClient()

    # Check availability
    if not await client.is_available():
        logger.warning("MiroFish is not available — falling back to auto-pass")
        return {
            "passed": True,
            "report_id": None,
            "simulation_id": None,
            "sentiment_summary": "MiroFish unavailable — auto-passed",
            "agent_reactions": [],
            "recommendation": "MiroFish service is offline. Post was auto-passed.",
            "raw_report": None,
        }

    # Build seed material: combine draft + persona + platform context
    seed_material = f"""
=== DRAFT POST FOR {platform.upper()} ===
{draft_text}

=== BRAND PERSONA CONTEXT ===
{persona_context}

=== TARGET PLATFORM ===
Platform: {platform}
Audience: Professional tech audience, potential investors, fellow developers
Goal: Build credibility, drive inbound, demonstrate technical competence
"""

    simulation_requirement = (
        f"Simulate how a {platform} audience of tech professionals, investors, "
        f"and developers would react to this post. Track sentiment, engagement "
        f"likelihood (would they repost/comment/ignore?), risk of backlash, "
        f"and overall reception quality."
    )

    # Run the full pipeline
    logger.info("MiroFish gate: starting full pipeline...")

    # Step 1: Create project + ontology
    project_data = await client.create_project_and_ontology(
        seed_text=seed_material,
        simulation_requirement=simulation_requirement,
        project_name=project_name,
    )
    project_id = project_data["project_id"]
    logger.info(f"MiroFish: project created → {project_id}")

    # Step 2: Build graph
    graph_id = await client.build_graph(project_id)
    logger.info(f"MiroFish: graph built → {graph_id}")

    # Step 3: Create simulation
    simulation_id = await client.create_simulation(
        project_id=project_id,
        graph_id=graph_id,
        enable_twitter=True,
        enable_reddit=False, # Twitter-only for gate checks
    )
    logger.info(f"MiroFish: simulation created → {simulation_id}")

    # Step 4: Prepare (generate agents)
    await client.prepare_simulation(simulation_id)
    logger.info("MiroFish: simulation prepared")

    # Step 5: Run simulation
    await client.start_simulation(simulation_id)
    logger.info("MiroFish: simulation completed")

    # Step 6: Generate report
    report_id = await client.generate_report(simulation_id)
    logger.info(f"MiroFish: report generated → {report_id}")

    # Step 7: Fetch report
    report = await client.get_report(report_id)

    # Parse gate decision from report
    gate_decision = _parse_gate_decision(report, report_id, simulation_id)
    
    # Save the run to the database
    try:
        from backend.db.session import SessionLocal
        from backend.db.models import MiroFishRun
        import json
        db = SessionLocal()
        run = MiroFishRun(
            simulation_id=simulation_id,
            project_id=project_id,
            status="completed",
            narratives=gate_decision.get("agent_reactions", []),
            metrics={"sentiment_summary": gate_decision.get("sentiment_summary")},
            raw_report=report
        )
        db.add(run)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to persist MiroFishRun to DB: {e}")

    return gate_decision


def _parse_gate_decision(report: dict, report_id: str, simulation_id: str) -> dict:
    """
    Extract a pass/fail gate decision from the MiroFish report.
    """
    content = report.get("content", "")
    sections = report.get("sections", [])

    # Simple heuristic: look for positive/negative signal words
    positive_signals = [
        "positive reception", "well-received", "high engagement",
        "strong interest", "resonates", "compelling", "credible",
        "authentic", "insightful", "would share", "would repost",
    ]
    negative_signals = [
        "negative reception", "backlash", "controversy", "cringe",
        "generic", "tone-deaf", "inauthentic", "spam", "clickbait",
        "ignored", "low engagement", "would scroll past",
    ]

    content_lower = content.lower() if content else ""
    pos_count = sum(1 for s in positive_signals if s in content_lower)
    neg_count = sum(1 for s in negative_signals if s in content_lower)

    # Decision logic
    if neg_count > pos_count:
        passed = False
        recommendation = "MiroFish simulation detected negative audience reception. Consider revising before publishing."
    elif pos_count > 0:
        passed = True
        recommendation = "MiroFish simulation indicates positive audience reception. Safe to publish."
    else:
        # Neutral — default to pass with caution
        passed = True
        recommendation = "MiroFish simulation returned neutral signals. Publishing with caution."

    sentiment = f"{pos_count} positive / {neg_count} negative signals detected"

    return {
        "passed": passed,
        "report_id": report_id,
        "simulation_id": simulation_id,
        "sentiment_summary": sentiment,
        "agent_reactions": sections[:5] if sections else [],
        "recommendation": recommendation,
        "raw_report": report,
    }
