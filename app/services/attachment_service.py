import os
import re
import unicodedata
from datetime import timedelta

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.errors import ConflictError
from app.models.attachment import ClaimAttachment
from app.models.claim import Claim
from app.services.audit_service import log_event
from app.services.claim_service import ensure_open
from app.timeutils import utcnow

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_FILES_PER_CLAIM = 5
# Customers can attach documents shortly after submitting, or while we wait for their follow-up.
UPLOAD_WINDOW = timedelta(hours=24)


class AttachmentRejected(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def sniff_content_type(head: bytes) -> str | None:
    """Trust the file's bytes, not the client-supplied MIME type."""
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def sanitize_filename(name: str | None) -> str:
    name = os.path.basename((name or "").replace("\\", "/"))
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[\x00-\x1f\x7f\"]", "", name).strip()
    return name[:255] or "attachment"


async def count_attachments(db: AsyncSession, claim_id) -> int:
    result = await db.execute(select(func.count(ClaimAttachment.id)).where(ClaimAttachment.claim_id == claim_id))
    return result.scalar() or 0


async def add_attachments(db: AsyncSession, claim: Claim, files: list[UploadFile]) -> list[ClaimAttachment]:
    ensure_open(claim)
    if claim.status != "follow_up" and utcnow() - claim.created_at > UPLOAD_WINDOW:
        raise ConflictError("Documents can only be added within 24 hours of submission or while information is requested.")
    if not files:
        raise AttachmentRejected("No files were provided.")
    if await count_attachments(db, claim.id) + len(files) > MAX_FILES_PER_CLAIM:
        raise AttachmentRejected(f"A claim can have at most {MAX_FILES_PER_CLAIM} attachments.")

    created = []
    for upload in files:
        data = await upload.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise AttachmentRejected(f'"{sanitize_filename(upload.filename)}" exceeds the 5 MB limit.', status_code=413)
        content_type = sniff_content_type(data[:16])
        if content_type is None:
            raise AttachmentRejected(f'"{sanitize_filename(upload.filename)}" is not a PDF, PNG, JPEG or WEBP file.', status_code=415)
        attachment = ClaimAttachment(
            claim_id=claim.id,
            filename=sanitize_filename(upload.filename),
            content_type=content_type,
            size_bytes=len(data),
            data=data,
        )
        db.add(attachment)
        created.append(attachment)

    await db.flush()
    await log_event(db, claim.id, "attachments_uploaded", {"files": [a.filename for a in created]}, "customer")
    await db.commit()
    return created


async def list_attachments(db: AsyncSession, claim_id) -> list[ClaimAttachment]:
    result = await db.execute(
        select(ClaimAttachment).where(ClaimAttachment.claim_id == claim_id).order_by(ClaimAttachment.created_at)
    )
    return list(result.scalars().all())


async def get_attachment_with_data(db: AsyncSession, claim_id, attachment_id) -> ClaimAttachment | None:
    result = await db.execute(
        select(ClaimAttachment)
        .options(undefer(ClaimAttachment.data))
        .where(ClaimAttachment.id == attachment_id, ClaimAttachment.claim_id == claim_id)
    )
    return result.scalar_one_or_none()
