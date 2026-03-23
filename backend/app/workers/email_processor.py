import json
import logging

from sqlalchemy import select

from app.database import async_session
from app.models.email import Email, EmailStatus, EmailClassification
from app.models.ignore_rule import IgnoreRule
from app.models.po_draft import PODraft
from app.models.cache import VendorCache, ProductCache
from app.services.email_classifier import should_ignore, classify_email
from app.services.email_parser import parse_order_details
from app.services.vendor_matcher import match_vendor
from app.services.product_matcher import match_product
from app.services.tracking_parser import parse_tracking_info

logger = logging.getLogger(__name__)


async def process_pending_emails(ctx: dict):
    """Process emails in PROCESSING status: classify, parse, and create drafts."""
    async with async_session() as db:
        result = await db.execute(
            select(Email).where(Email.status == EmailStatus.PROCESSING).limit(20)
        )
        emails = result.scalars().all()

        if not emails:
            logger.debug("No pending emails to process")
            return

        logger.info(f"Found {len(emails)} emails to process")

        # Load ignore rules
        rules_result = await db.execute(select(IgnoreRule))
        rules = [{"field": r.field.value, "match_type": r.match_type.value, "value": r.value} for r in rules_result.scalars().all()]

        # Load vendor cache
        vendor_result = await db.execute(select(VendorCache))
        vendors = [{"odoo_id": v.odoo_id, "name": v.name, "email_domain": v.email_domain} for v in vendor_result.scalars().all()]
        vendor_domains = [v["email_domain"] for v in vendors if v["email_domain"]]

        # Load product cache
        product_result = await db.execute(select(ProductCache))
        products = [{"odoo_id": p.odoo_id, "name": p.name, "default_code": p.default_code, "description": p.description or ""} for p in product_result.scalars().all()]

        for email_record in emails:
            try:
                logger.info(f"Processing email {email_record.id}: {email_record.subject} (classification={email_record.classification.value})")

                # Step 1: Check ignore rules
                if should_ignore(email_record.sender, email_record.subject, rules):
                    email_record.status = EmailStatus.IGNORED
                    logger.info(f"  Email {email_record.id}: ignored by rule")
                    continue

                # Step 2: Classify (skip if user already classified via triage action)
                if email_record.classification == EmailClassification.UNCLASSIFIED:
                    classification = classify_email(
                        subject=email_record.subject,
                        body=email_record.body_text,
                        sender_domain=email_record.sender_domain,
                        known_vendor_domains=vendor_domains,
                    )
                    email_record.classification = EmailClassification(classification)
                    logger.info(f"  Email {email_record.id}: classified as {classification}")

                if email_record.classification == EmailClassification.UNCLASSIFIED:
                    email_record.status = EmailStatus.TRIAGE
                    logger.info(f"  Email {email_record.id}: sent to triage (unclassified)")
                    continue

                if email_record.classification == EmailClassification.SHIPPING_NOTICE:
                    tracking = parse_tracking_info(email_record.body_text)
                    email_record.status = EmailStatus.REVIEWED
                    logger.info(f"  Email {email_record.id}: shipping notice reviewed")
                    continue

                if email_record.classification == EmailClassification.BILL:
                    email_record.status = EmailStatus.TRIAGE
                    logger.info(f"  Email {email_record.id}: bill sent to triage")
                    continue

                # Step 3: Parse order details
                parsed = parse_order_details(email_record.body_text)
                logger.info(f"  Email {email_record.id}: parsed {len(parsed['line_items'])} line items, total={parsed['total_amount']}")

                # Step 4: Match vendor
                vendor_match = match_vendor(
                    sender=email_record.sender,
                    sender_domain=email_record.sender_domain,
                    vendors=vendors,
                )
                logger.info(f"  Email {email_record.id}: vendor={'matched: ' + vendor_match['name'] if vendor_match else 'no match'}")

                # Step 5: Match products
                matched_items = []
                for item in parsed["line_items"]:
                    product_match = match_product(
                        description=item["description"],
                        sku=item.get("sku"),
                        products=products,
                    )
                    matched_item = {**item}
                    if product_match:
                        matched_item["product_odoo_id"] = product_match["odoo_id"]
                        matched_item["product_name"] = product_match["name"]
                        matched_item["product_confidence"] = product_match["confidence"]
                        matched_item["alternatives"] = product_match.get("alternatives", [])
                    else:
                        matched_item["product_odoo_id"] = None
                        matched_item["product_name"] = None
                        matched_item["product_confidence"] = "low"
                        matched_item["alternatives"] = []
                    matched_items.append(matched_item)

                # Step 6: Create PO draft
                draft = PODraft(
                    email_id=email_record.id,
                    vendor_odoo_id=vendor_match["odoo_id"] if vendor_match else None,
                    vendor_name=vendor_match["name"] if vendor_match else email_record.sender,
                    vendor_confidence=vendor_match["confidence"] if vendor_match else "low",
                    line_items=json.dumps(matched_items),
                    total_amount=str(parsed["total_amount"]) if parsed["total_amount"] else None,
                    expected_date=parsed["expected_date"],
                    user_id=email_record.user_id,
                )
                db.add(draft)
                email_record.status = EmailStatus.REVIEWED
                logger.info(f"  Email {email_record.id}: PO draft created, status → reviewed")

            except Exception as e:
                logger.error(f"  Email {email_record.id}: processing failed: {e}", exc_info=True)
                email_record.status = EmailStatus.TRIAGE
                continue

        await db.commit()
        logger.info(f"Committed changes for {len(emails)} emails")
