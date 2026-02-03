"""
Nekazari Odoo ERP Module - Intelligence Module Integration

Handles integration with Nekazari Intelligence module for AI/ML predictions.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import httpx

from app.config import settings
from app.services.odoo_client import OdooClient
from app.services.database import get_tenant_odoo_info

logger = logging.getLogger(__name__)


class IntelligenceIntegration:
    """Service for Intelligence module integration."""

    def __init__(self, tenant_id: str):
        """
        Initialize Intelligence integration for a tenant.

        Args:
            tenant_id: Tenant ID
        """
        self.tenant_id = tenant_id
        self.intelligence_url = settings.INTELLIGENCE_API_URL

    async def _get_odoo_database(self) -> str:
        """Get Odoo database name for tenant."""
        info = await get_tenant_odoo_info(self.tenant_id)
        if not info:
            raise ValueError(f"No Odoo configured for tenant: {self.tenant_id}")
        return info.get("database", f"nkz_odoo_{self.tenant_id}")

    async def get_yield_prediction(
        self,
        parcel_id: str,
        crop_type: Optional[str] = None
    ) -> dict:
        """
        Get yield prediction from Intelligence module.

        Args:
            parcel_id: NGSI-LD parcel ID
            crop_type: Crop type (optional, will be fetched if not provided)

        Returns:
            Prediction data including expected yield and confidence
        """
        logger.info(f"Getting yield prediction for parcel: {parcel_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.intelligence_url}/api/intelligence/predict/yield",
                params={
                    "entity_id": parcel_id,
                    "crop_type": crop_type
                },
                headers={
                    "X-Tenant-ID": self.tenant_id
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Yield prediction failed: {response.status_code}")
                raise Exception(f"Yield prediction failed: {response.text}")

    async def get_energy_forecast(
        self,
        installation_id: str,
        days: int = 7
    ) -> dict:
        """
        Get energy production forecast from Intelligence module.

        Args:
            installation_id: NGSI-LD installation ID
            days: Number of days to forecast

        Returns:
            Forecast data including daily production predictions
        """
        logger.info(f"Getting energy forecast for installation: {installation_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.intelligence_url}/api/intelligence/predict/energy",
                params={
                    "entity_id": installation_id,
                    "days": days
                },
                headers={
                    "X-Tenant-ID": self.tenant_id
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Energy forecast failed: {response.status_code}")
                raise Exception(f"Energy forecast failed: {response.text}")

    async def sync_predictions_to_odoo(self):
        """
        Sync predictions from Intelligence module to Odoo reports.

        Creates or updates report records in Odoo with prediction data.
        """
        logger.info(f"Syncing predictions to Odoo for tenant: {self.tenant_id}")

        db_name = await self._get_odoo_database()
        odoo = OdooClient()

        # Get all parcels and installations
        # Then fetch predictions and create Odoo reports

        try:
            # Fetch parcels from Odoo
            parcels = await odoo.search_records(
                db_name,
                "product.template",
                [["x_ngsi_id", "like", "urn:ngsi-ld:AgriParcel"]],
                fields=["id", "name", "x_ngsi_id", "x_crop_type"]
            )

            for parcel in parcels:
                try:
                    prediction = await self.get_yield_prediction(
                        parcel["x_ngsi_id"],
                        parcel.get("x_crop_type")
                    )

                    # Create or update prediction record in Odoo
                    await self._update_odoo_prediction(
                        db_name,
                        odoo,
                        parcel["id"],
                        "yield",
                        prediction
                    )

                except Exception as e:
                    logger.warning(f"Failed to get prediction for {parcel['name']}: {e}")

            # Fetch energy installations
            installations = await odoo.search_records(
                db_name,
                "energy.installation",
                [["x_ngsi_id", "!=", False]],
                fields=["id", "name", "x_ngsi_id"]
            )

            for installation in installations:
                try:
                    forecast = await self.get_energy_forecast(
                        installation["x_ngsi_id"],
                        days=7
                    )

                    await self._update_odoo_prediction(
                        db_name,
                        odoo,
                        installation["id"],
                        "energy",
                        forecast
                    )

                except Exception as e:
                    logger.warning(f"Failed to get forecast for {installation['name']}: {e}")

            logger.info("Predictions synced to Odoo successfully")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Failed to sync predictions: {e}")
            raise

    async def _update_odoo_prediction(
        self,
        db_name: str,
        odoo: OdooClient,
        record_id: int,
        prediction_type: str,
        data: dict
    ):
        """
        Update or create prediction record in Odoo.

        This creates a custom record to store AI predictions.
        """
        # Check if prediction model exists (custom module may need to be installed)
        try:
            prediction_vals = {
                "name": f"{prediction_type.capitalize()} Prediction - {datetime.now().strftime('%Y-%m-%d')}",
                "prediction_type": prediction_type,
                "target_id": record_id,
                "prediction_date": datetime.now().strftime("%Y-%m-%d"),
                "prediction_data": str(data),
                "confidence": data.get("confidence", 0),
                "expected_value": data.get("expected_value") or data.get("total_kwh", 0)
            }

            # Look for existing prediction
            existing = await odoo.search_records(
                db_name,
                "x.prediction",
                [
                    ["target_id", "=", record_id],
                    ["prediction_type", "=", prediction_type],
                    ["prediction_date", "=", prediction_vals["prediction_date"]]
                ],
                fields=["id"],
                limit=1
            )

            if existing:
                await odoo.update_record(db_name, "x.prediction", existing[0]["id"], prediction_vals)
            else:
                await odoo.create_record(db_name, "x.prediction", prediction_vals)

        except Exception as e:
            # Prediction model might not exist, that's OK
            logger.debug(f"Could not save prediction to Odoo: {e}")

    async def request_analysis(
        self,
        entity_id: str,
        analysis_type: str,
        parameters: Optional[dict] = None
    ) -> dict:
        """
        Request an analysis from the Intelligence module.

        Args:
            entity_id: NGSI-LD entity ID
            analysis_type: Type of analysis (anomaly, trend, optimization)
            parameters: Additional parameters

        Returns:
            Analysis request ID and status
        """
        logger.info(f"Requesting {analysis_type} analysis for: {entity_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.intelligence_url}/api/intelligence/analyze",
                json={
                    "entity_id": entity_id,
                    "analysis_type": analysis_type,
                    "parameters": parameters or {},
                    "tenant_id": self.tenant_id
                },
                timeout=30.0
            )

            if response.status_code in [200, 202]:
                return response.json()
            else:
                logger.error(f"Analysis request failed: {response.status_code}")
                raise Exception(f"Analysis request failed: {response.text}")
