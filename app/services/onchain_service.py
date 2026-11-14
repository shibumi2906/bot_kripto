from app.core.logger import logger
from app.core.schemas import OnChainMetricsOut


async def fetch_onchain_metrics(
    network: str = "ethereum",
    address: str | None = None,
) -> OnChainMetricsOut:
    if network != "ethereum":
        logger.warning(f"Unsupported network requested: {network}")
        return OnChainMetricsOut(active_addresses=0, tx_count=0)

    if not address:
        return OnChainMetricsOut(active_addresses=0, tx_count=0)

    logger.info(f"Returning fallback on-chain metrics for address {address}")
    return OnChainMetricsOut(active_addresses=1, tx_count=0)
