import asyncio
import httpx
import structlog
from tasks.celery_app import celery
from scrapers.gem import GEMScraper, generate_synthetic_orders

logger = structlog.get_logger(__name__)

API_BASE = "http://api:8000"


@celery.task(name="backend.tasks.scrape_tasks.scrape_gem_task", bind=True, max_retries=3)
def scrape_gem_task(self) -> dict:
    log = logger.bind(task="scrape_gem")
    log.info("task_start")

    async def _run():
        scraper = GEMScraper()
        all_records = []
        try:
            for page in range(1, 13):
                records = await scraper.scrape_orders(page=page)
                if not records:
                    break
                normalized = [scraper.normalize(r) for r in records]
                all_records.extend(normalized)
                if len(records) < 50:
                    break
        finally:
            await scraper.close()

        if not all_records:
            log.warning("no_records_scraped")
            return {"records": 0}

        async with httpx.AsyncClient(base_url=API_BASE, timeout=120) as client:
            resp = await client.post("/tenders/ingest", json=all_records)
            resp.raise_for_status()
            result = resp.json()

        log.info("task_complete", **result)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        log.error("task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(name="backend.tasks.scrape_tasks.scrape_cppp_task", bind=True, max_retries=3)
def scrape_cppp_task(self) -> dict:
    log = logger.bind(task="scrape_cppp")
    log.info("task_start")

    async def _run():
        from ..scrapers.cppp import CPPPScraper
        scraper = CPPPScraper()
        try:
            records = await scraper.scrape_tenders()
        finally:
            await scraper.close()

        if not records:
            log.warning("no_cppp_records")
            return {"records": 0}

        normalized = [scraper.normalize(r) for r in records]
        async with httpx.AsyncClient(base_url=API_BASE, timeout=120) as client:
            resp = await client.post("/tenders/ingest", json=normalized)
            resp.raise_for_status()
            result = resp.json()

        log.info("cppp_task_complete", **result)
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        log.error("cppp_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(name="backend.tasks.scrape_tasks.run_detection_task", bind=True)
def run_detection_task(self) -> dict:
    log = logger.bind(task="run_detection")
    log.info("detection_task_start")

    async def _run():
        async with httpx.AsyncClient(base_url=API_BASE, timeout=300) as client:
            resp = await client.post("/detection/run")
            resp.raise_for_status()
            result = resp.json()

        log.info("detection_pipeline_queued", task_id=result.get("task_id"))
        return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        log.error("detection_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery.task(name="backend.tasks.scrape_tasks.full_pipeline_task", bind=True)
def full_pipeline_task(self) -> dict:
    """GEM + CPPP scrape → detection → notify. Runs as a chain."""
    log = logger.bind(task="full_pipeline")
    log.info("pipeline_start")
    try:
        gem_result = scrape_gem_task.apply()
        cppp_result = scrape_cppp_task.apply()
        detect_result = run_detection_task.apply()
        log.info("pipeline_complete")
        return {
            "gem": gem_result.get() if gem_result else {},
            "cppp": cppp_result.get() if cppp_result else {},
            "detection": detect_result.get() if detect_result else {},
        }
    except Exception as exc:
        log.error("pipeline_failed", error=str(exc))
        raise
